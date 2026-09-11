"""
unfold/io/dxf.py
-----------------
Export di un FlatGeometry (unfold.model.geometry) su file DXF, via forge.
Unico modulo di `unfold` che importa forge — e lo fa lazy: se forge non è
installato, il resto del pacchetto (calcolo dello sviluppo) funziona
comunque; solo queste due funzioni sollevano ImportError.

`FlatGeometry.to_forge_result()`/`.to_dxf()` sono deleghe sottili a queste
due funzioni: da fuori si continua a chiamare `flat.to_dxf(...)`, il corpo
vive qui per tenere lo strato `model` pulito da forge.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..model.geometry import FlatGeometry
    from ..model.section import FlangeQuote, Section


def to_forge_result(flat: "FlatGeometry", tolerance: float = 0.05):
    """
    Traduce `flat` in un ForgeResult passando da forge.load_geometry() +
    forge.heal_and_detect() — stesso contratto di qualsiasi altra sorgente
    forge (DXF, PDF, ...).
    """
    try:
        import forge
    except ImportError as exc:
        raise ImportError(
            "FlatGeometry.to_forge_result()/.to_dxf() richiedono il "
            "pacchetto 'forge' installato a fianco "
            "(pip install -e <percorso a dxf-forge>)."
        ) from exc

    doc = forge.load_geometry(
        flat.entities, tolerance=tolerance, source_path=flat.label,
    )
    result = forge.heal_and_detect(doc, label=flat.label)
    if not result.is_valid:
        raise ValueError(
            f"FlatGeometry '{flat.label}' non valido dopo heal(): "
            + " ".join(result.errors)
        )
    return result


def to_dxf(
    flat: "FlatGeometry",
    path: str,
    tolerance: float = 0.05,
    annotate: bool = True,
    show_margin_reference: bool = False,
):
    """
    Scrive `flat` su file DXF via forge.to_dxf() — layer/colori coerenti
    col resto dell'output forge.

    annotate:               blocco di testo con i valori di `flat.meta`,
                             layer "Notes" — riferimento in officina, non
                             fa parte della geometria di taglio
    show_margin_reference:   default False (opt-in). Se True e c'è un
                             margine di saldatura, disegna il contorno
                             completo del foglio pieno (prima del margine)
                             tratteggiato sul layer "MarginReference" —
                             solo riferimento, mai geometria di taglio
    """
    import forge

    result = to_forge_result(flat, tolerance=tolerance)
    doc_out = forge.to_dxf(result)

    if annotate and flat.meta:
        _write_meta_block(doc_out, result, flat.label, flat.meta)

    if show_margin_reference and flat.reference_entities:
        _write_reference_lines(doc_out, flat.reference_entities)

    doc_out.saveas(path)
    return doc_out


def write_section_dxf(
    section: "Section",
    quotes: List["FlangeQuote"],
    path: str,
    tolerance: float = 0.05,
    quote_clearance: float = 8.0,
    annotate: bool = True,
):
    """
    Esporta la vista in sezione (Fase 3.3/3.4, MAP.md D31): il contorno
    reale del pezzo PIEGATO (`section.section()`) più una quota per
    flangia — chiamata da `Section.to_dxf()`, non pensata per essere usata
    da sola.

    Ogni quota in `quotes` (`Section.flange_quotes()`) diventa una
    DIMENSION `ezdxf` vera (frecce + linee di richiamo), non solo testo:
    se la flangia ha una faccia esterna coerente, la quota è disegnata
    fuori dal pezzo sul lato di quella faccia col testo "... (esterno)";
    se non ce l'ha (l'anima di una Z/omega, MAP.md D1), resta sulla
    mezzeria col testo che lo dice esplicitamente — è la 3.4: non è mai
    ambiguo da che faccia è presa una quota, perché quando non lo è si
    vede scritto.
    """
    import forge

    flat = section.section()
    result = to_forge_result(flat, tolerance=tolerance)
    doc_out = forge.to_dxf(result)

    _write_flange_quotes(doc_out, quotes, section.thickness, quote_clearance)

    if annotate and flat.meta:
        _write_meta_block(doc_out, result, flat.label, flat.meta)

    doc_out.saveas(path)
    return doc_out


def write_part_dxf(
    flat: "FlatGeometry",
    path: str,
    section_flat: Optional["FlatGeometry"] = None,
    quotes: Optional[List["FlangeQuote"]] = None,
    thickness: Optional[float] = None,
    include_header: bool = False,
    tolerance: float = 0.05,
    quote_clearance: float = 8.0,
    margin: float = 20.0,
):
    """
    Esporta un pezzo su un unico file a LIVELLI impilati in VERTICALE
    (Fase 3, MAP.md D32) — mai affiancati, un solo asse di offset (Y) da
    gestire per qualunque combinazione di livelli:

      1. taglio          (`flat`, sempre — via forge, come `to_dxf()`)
      2. vista in sezione (se `section_flat` è dato — SOLO riferimento:
                           linee/archi disegnati diretti, non passa da
                           forge/heal_and_detect, per non farla scambiare
                           per una seconda parte da tagliare)
      3. header           (se `include_header`: il blocco note di `flat.meta`)

    Ogni livello incluso si piazza sotto al precedente di
    `bbox_height + margin`; tutti allineati a sinistra sullo stesso x0
    del taglio — chiamata da `human_layer.export_part()`, non pensata per
    essere usata da sola.
    """
    import forge

    result = to_forge_result(flat, tolerance=tolerance)
    doc_out = forge.to_dxf(result)

    cut_bbox = result.clusters[0].outer.bbox if result.clusters else (0.0, 0.0, 0.0, 0.0)
    x0 = cut_bbox[0]
    y_cursor = cut_bbox[1] - margin

    if section_flat is not None:
        sec_bbox = _entities_bbox(section_flat.entities)
        dx = x0 - sec_bbox[0]
        dy = y_cursor - sec_bbox[3]
        _write_section_view_entities(doc_out, section_flat.entities, dx, dy)
        if quotes:
            if thickness is None:
                raise ValueError("thickness richiesto per disegnare le quote della sezione")
            shifted = [
                replace(q, p0=(q.p0[0] + dx, q.p0[1] + dy), p1=(q.p1[0] + dx, q.p1[1] + dy))
                for q in quotes
            ]
            _write_flange_quotes(doc_out, shifted, thickness, quote_clearance)
        y_cursor = (sec_bbox[1] + dy) - margin

    if include_header and flat.meta:
        _write_text_lines(doc_out, _meta_lines(flat.label, flat.meta), x0, y_cursor)

    doc_out.saveas(path)
    return doc_out


def _entities_bbox(entities: List[Dict[str, Any]]):
    """Bbox degli entity grezzi (linee/archi, schema `FlatGeometry.entities`)
    senza passare da forge. Per gli archi usa il cerchio completo
    (centro±raggio) invece del solo arco spazzato — conservativo (mai
    sottostima), sufficiente per non sovrapporsi nello stacking."""
    xs: List[float] = []
    ys: List[float] = []
    for e in entities:
        if e.get("type") == "line":
            for p in (e["start"], e["end"]):
                xs.append(p[0])
                ys.append(p[1])
        elif e.get("type") == "arc":
            cx, cy = e["center"]
            r = e["radius"]
            xs += [cx - r, cx + r]
            ys += [cy - r, cy + r]
    if not xs:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))


def _write_section_view_entities(doc_out, entities: List[Dict[str, Any]], dx: float, dy: float,
                                 layer: str = "SectionView") -> None:
    """Disegna la vista in sezione come linee/archi diretti, traslati di
    (dx, dy) — SOLO riferimento, non passa da forge/heal_and_detect: se lo
    facesse, verrebbe rilevata come una seconda parte da tagliare, che non
    è (stesso principio di `_write_reference_lines`, qui su un layer
    pieno invece che tratteggiato perché non è un fantasma del foglio ma
    un disegno vero da leggere)."""
    msp = doc_out.modelspace()
    if layer not in doc_out.layers:
        # verde SCURO, deliberatamente diverso dal verde di OuterContour
        # (color 3, la sagoma da tagliare): la vista in sezione è solo
        # riferimento, non va scambiata per la parte vera.
        section_layer = doc_out.layers.new(layer, dxfattribs={"color": 3})
        section_layer.rgb = (0, 100, 0)

    attribs = {"layer": layer}
    for entity in entities:
        kind = entity.get("type")
        if kind == "line":
            msp.add_line(
                (entity["start"][0] + dx, entity["start"][1] + dy),
                (entity["end"][0] + dx, entity["end"][1] + dy),
                dxfattribs=attribs,
            )
        elif kind == "arc":
            ccw = entity.get("ccw", True)
            start, end = entity["start_angle"], entity["end_angle"]
            if not ccw:
                start, end = end, start
            cx, cy = entity["center"]
            msp.add_arc(
                center=(cx + dx, cy + dy), radius=entity["radius"],
                start_angle=start, end_angle=end, dxfattribs=attribs,
            )


def _write_flange_quotes(doc_out, quotes: List["FlangeQuote"], thickness: float, clearance: float) -> None:
    msp = doc_out.modelspace()
    if "Quotes" not in doc_out.layers:
        doc_out.layers.new("Quotes", dxfattribs={"color": 5})

    for q in quotes:
        p0, p1 = q.p0, q.p1
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        length = math.hypot(dx, dy)
        if length < 1e-9:
            continue

        if q.display_kind == "esterno":
            # p0/p1 sono già sulla faccia esterna: basta un margine di
            # rispetto per non sovrapporre la linea di quota al pezzo.
            nx, ny = -dy / length, dx / length      # normale a sinistra di p0->p1
            sign = 1.0 if q.face == "left" else -1.0
            distance = sign * clearance
            text = f"{q.display_length:.2f} (esterno)"
        else:
            # p0/p1 sono sulla mezzeria: sposta la quota fuori dal
            # materiale (spessore/2) più il margine, da un lato qualunque
            # — non è una faccia, il testo lo dice.
            distance = thickness / 2.0 + clearance
            text = f"{q.display_length:.2f} (a mezzeria — nessuna faccia esterna coerente)"

        dim = msp.add_aligned_dim(
            p1=p0, p2=p1, distance=distance, text=text,
            dxfattribs={"layer": "Quotes"},
        )
        dim.render()


# ---------------------------------------------------------------------------
# Annotazione — solo testo/linee di riferimento, mai geometria di taglio
# ---------------------------------------------------------------------------

def _meta_lines(label: str, meta: Dict[str, Any]) -> List[str]:
    return [label.upper() or "SVILUPPO"] + [
        f"{key} = {value:.3f}" if isinstance(value, float) else f"{key} = {value}"
        for key, value in meta.items()
    ]


def _write_text_lines(doc_out, lines: List[str], x0: float, y0: float, layer: str = "Notes") -> None:
    msp = doc_out.modelspace()
    if layer not in doc_out.layers:
        doc_out.layers.new(layer)

    for i, text in enumerate(lines):
        entity = msp.add_text(
            text,
            dxfattribs={
                "height": 5.0 if i == 0 else 3.5,
                "layer": layer,
            },
        )
        entity.set_placement((x0, y0 - i * 8.0))


def _write_meta_block(doc_out, result, label: str, meta: Dict[str, Any]) -> None:
    bbox = result.clusters[0].outer.bbox if result.clusters else (0.0, 0.0, 0.0, 0.0)
    x0 = bbox[2] + 30.0
    y0 = bbox[3]
    _write_text_lines(doc_out, _meta_lines(label, meta), x0, y0)


def _write_reference_lines(doc_out, reference_entities: List[Dict[str, Any]]) -> None:
    """
    Disegna il contorno PIENO (prima del margine) — non solo due lati
    sciolti: linee, polilinee e archi, così il contorno tratteggiato si
    richiude/collega intorno alla geometria di taglio reale, invece di
    lasciare due segmenti staccati.
    """
    msp = doc_out.modelspace()
    layer = "MarginReference"

    if "DASHED" not in doc_out.linetypes:
        doc_out.linetypes.new("DASHED", dxfattribs={
            "description": "Dashed __ __ __", "pattern": "A,.5,-.25",
        })
    if layer not in doc_out.layers:
        doc_out.layers.new(layer, dxfattribs={"color": 8, "linetype": "DASHED"})

    attribs = {"layer": layer, "linetype": "DASHED", "color": 8}

    for entity in reference_entities:
        kind = entity.get("type")
        if kind == "line":
            msp.add_line(entity["start"], entity["end"], dxfattribs=attribs)
        elif kind == "polyline":
            msp.add_lwpolyline(
                entity["points"], close=bool(entity.get("closed", False)),
                dxfattribs=attribs,
            )
        elif kind == "circle":
            msp.add_circle(entity["center"], entity["radius"], dxfattribs=attribs)
        elif kind == "arc":
            ccw = entity.get("ccw", True)
            start, end = entity["start_angle"], entity["end_angle"]
            if not ccw:
                start, end = end, start
            msp.add_arc(
                center=entity["center"], radius=entity["radius"],
                start_angle=start, end_angle=end, dxfattribs=attribs,
            )
