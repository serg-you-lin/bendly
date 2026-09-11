"""
tests/reconstruct.py
--------------------
Strumento INTERNO (non API pubblica, mai in bendly.__all__).

Da un pezzo reale TruBend — DXF piatto + file .bnc — ricostruisce lo
sketch primitivo a mezzeria (una Section, stesso formato della Fase 0),
senza che nessuno dichiari quale centerline è stata usata.

Chi ha già .bnc + DXF piatto ha già lo sviluppo e usa quello: questo serve
solo a noi, per generare i golden test di officina 1 e, più avanti, per
capire e sviluppare le scatole.

Come:
  - dal DXF piatto: contorno chiuso + linee di piega (layer Bend / MBend)
    -> lunghezze PIATTE di ogni flangia + verso di ogni piega. Il layer dà
    il verso: Bend = piega "in su" -> 90 nello schema nomi; MBend = piega
    "in giù" -> 270 (verificato sui nomi dei file: Za...b100bc270... ha la
    seconda piega su MBend).
  - dal .bnc: lo spessore, e per ogni piega l'accorciamento (riferito a
    quote ESTERNE) -> lo si porta a mezzeria con external_to_centerline_deduction().
  - flangia a mezzeria = flangia piatta + accorciamento a mezzeria / 2 per
    ogni piega adiacente.

Se il .bnc ha più colpi che pieghe geometriche (un angolo tirato in due
volte, pre-piega + finitura — tipico dell'omega spessa), le pre-pieghe si
scartano: il numero di colpi non cambia il pezzo finito né lo sviluppo.

NON usa read_section(): quello legge un disegno in SEZIONE (dove lo
spessore si vede). Un DXF piatto è il pezzo già disteso, lo spessore non
si vede.

Limite noto (Z / omega): la flangia centrale "cerniera" fra due pieghe di
verso opposto è ambigua di ± spessore·tan(angolo/2) se la si vuole
esprimere come quota ESTERNA — nessuna faccia è coerentemente esterna a
entrambe le pieghe adiacenti (vedi MAP.md D1). A mezzeria l'ambiguità
sparisce del tutto e la lunghezza sviluppo TOTALE resta comunque esatta:
è esattamente il motivo per cui il core lavora a mezzeria.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import ezdxf

from bendly.rules.deduction import external_to_centerline_deduction
from bendly.model.section import SECTION_INNER_RADIUS_MM, Section
from bendly.adapters.trubend import leggi_bnc

# layer della linea di piega nei DXF TruBend -> angolo nello schema nomi
# (piatto = 180, piega in su = 90, piega in giù = 270).
_BEND_LAYER_ANGLE = {"BEND": 90.0, "MBEND": 270.0}

# suffisso del nome file DXF -> apertura V della matrice, per accoppiare
# ogni .bnc al suo DXF piatto (stesse combinazioni della tabella CAVA in
# tests/test_golden_officina.py).
_CAVA_SUFFIX = {"EV1": 6.0, "EV2": 8.0, "EV5": 16.0,
                "EW50": 50.0, "EW60": 60.0, "EV60": 60.0}

DATA_DIR = Path(__file__).resolve().parent.parent / "data_4_cloude"

# token angolo nello schema nomi: due lettere minuscole consecutive (ab, bc,
# cd, ...) seguite dai gradi. Nei nomi tersi (L12, O2) non c'è nessun token
# -> pezzo a sole pieghe di 90° (90 = su, 270 = giù nello schema).
_ANGLE_TOKEN = re.compile(r"(?<![A-Za-z])[a-z]{2}(\d+)")


def is_ninety_degree_name(stem: str) -> bool:
    """True se il nome file descrive un pezzo con SOLO pieghe a 90°.

    I golden storici di officina 1 sono tutti a 90°.
    """
    return all(g in ("90", "270") for g in _ANGLE_TOKEN.findall(stem))


def is_reconstructable_name(stem: str) -> bool:
    """True se `section_from_part` sa ricostruire questo pezzo OGGI
    (MAP.md, "angolo incluso vero" — 11 set 2026).

    Tutti i 90° (`is_ninety_degree_name`), più i pezzi a UNA sola piega
    geometrica **aperta** (incluso >= 90°, ancora piena piega in aria,
    `PIEGA_IN_ARIA_E_CONIATURA.md`): l'angolo vero viene dal Sollwinkel del
    `.bnc`, senza ambiguità di pre-piega o di verso da risolvere
    (verificato su `La114ab{120,150}b114s{1,3,10}`).

    Restano fuori, apposta: le pieghe **chiuse** a una piega sola
    (`La114ab{50,70}...`, incluso < 90°) — lì il `Biegeverkuerzung` non è
    affidabile per costruzione, è coniatura non piega in aria (verificato:
    lo sviluppo non torna, sviluppo reale mm più corto); e le forme a più
    pieghe non a 90° (Z, omega) — la seconda piega di una Z non va in
    appoggio (dopo la prima il pezzo non è più piatto) e il `.bnc` non ha
    un `Biegeverkuerzung` misurato per lei, non è un buco di lettura
    nostro (vedi `tests/generate_calibration.py`, `TODO.md`).
    """
    if is_ninety_degree_name(stem):
        return True
    tokens = _ANGLE_TOKEN.findall(stem)
    return len(tokens) == 1 and float(tokens[0]) >= 90.0


@dataclass
class PartReconstruction:
    """Esito di section_from_part()."""
    section: Section
    thickness: float
    v_opening: Optional[float]                       # apertura V matrice (dal .bnc)
    developed_length: Optional[float]                # lunghezza sviluppo dal .bnc
    flat_flanges: List[float] = field(default_factory=list)
    centerline_deductions: List[float] = field(default_factory=list)


# --------------------------------------------------------------------------
# 1.1 — dal DXF piatto: flange piatte + verso delle pieghe
# --------------------------------------------------------------------------

def _outline_points(entity) -> List[Tuple[float, float]]:
    if entity.dxftype() == "LWPOLYLINE":
        return [(p[0], p[1]) for p in entity.get_points("xy")]
    return [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]


def flat_flanges_from_dxf(dxf_path) -> Tuple[List[float], List[str]]:
    """Contorno + linee di piega -> (flange_piatte, versi).

    Le flange piatte sono le distanze fra una linea di piega e la
    successiva lungo l'asse lungo dello sviluppo, più i due tratti alle
    estremità. I versi ("BEND" | "MBEND") seguono l'ordine in cui le
    pieghe si incontrano percorrendo quell'asse. Il DXF dà SOLO il verso
    (su/giù) — la grandezza vera dell'angolo si legge dal `.bnc` gemello
    (`section_from_part`, TODO.md "angolo incluso vero").
    """
    msp = ezdxf.readfile(str(dxf_path)).modelspace()

    outline = next((e for e in msp
                    if e.dxftype() in ("POLYLINE", "LWPOLYLINE")), None)
    if outline is None:
        raise ValueError(f"{Path(dxf_path).name}: nessun contorno (polilinea) nel DXF")

    pts = _outline_points(outline)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    horizontal = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    lo, hi = (min(xs), max(xs)) if horizontal else (min(ys), max(ys))

    bends: List[Tuple[float, str]] = []
    for e in msp:
        if e.dxftype() != "LINE":
            continue
        layer = str(e.dxf.layer).upper()
        if layer not in _BEND_LAYER_ANGLE:
            continue
        pos = e.dxf.start.x if horizontal else e.dxf.start.y
        bends.append((pos, layer))
    bends.sort()

    cuts = [lo] + [p for p, _ in bends] + [hi]
    flanges = [round(cuts[i + 1] - cuts[i], 4) for i in range(len(cuts) - 1)]
    directions = [d for _, d in bends]
    return flanges, directions


# --------------------------------------------------------------------------
# 1.2 — da piatto a mezzeria: la Section del pezzo reale
# --------------------------------------------------------------------------

def section_from_part(bnc_path, dxf_path) -> PartReconstruction:
    """Ricostruisce la Section a mezzeria da un pezzo reale (.bnc + DXF piatto)."""
    bnc = leggi_bnc(bnc_path)
    flat, directions = flat_flanges_from_dxf(dxf_path)

    # stima grezza SOLO per scartare le pre-pieghe quando il .bnc ha più
    # colpi che pieghe geometriche (angolo tirato in due volte, tipico
    # dell'omega spessa): assume 90/270 dal solo verso. L'angolo vero di
    # ogni piega arriva sotto, dal Sollwinkel del passo giusto — per le
    # pieghe standard a 90° coincide (verificato), per le altre no, ma lì
    # il conteggio colpi==pieghe non fa mai scattare questo filtro.
    naive_rotations = [abs(180.0 - _BEND_LAYER_ANGLE[d]) for d in directions]

    # I colpi di piega nel .bnc possono essere PIÙ delle pieghe geometriche:
    # un angolo tirato in due volte (pre-piega + finitura, tipico dell'omega
    # spessa) conta comunque per UNA piega. Non cambia né il pezzo finito né
    # lo sviluppo. Si tiene il colpo di finitura di ogni corner — quello
    # all'angolo geometrico finale — scartando le pre-pieghe (angolo diverso).
    steps = list(bnc.pieghe)
    if len(steps) > len(directions):
        steps = [p for p in steps
                 if any(abs((p.angolo or 90.0) - r) < 1.0 for r in naive_rotations)]

    if len(steps) != len(directions):
        raise ValueError(
            f"{Path(dxf_path).name}: {len(directions)} linee di piega nel DXF, "
            f"{len(bnc.pieghe)} colpi nel .bnc, non riconducibili a "
            f"{len(directions)} pieghe"
        )

    thickness = float(bnc.spessore)

    # angolo VERO (schema nomi, piatto=180) per ogni piega: il verso dal
    # layer DXF, la grandezza dal Sollwinkel del .bnc (verificato su
    # La114ab120b114s1.bnc: Sollwinkel 120.0 == token "ab120" del nome file).
    # Per le pieghe "in giù" (MBend) il Sollwinkel è la stessa grandezza
    # "quanto sono aperti i lembi" letta senza segno: 360 - Sollwinkel la
    # riporta nella fascia 181-360 dello schema nomi (D7), coerente col caso
    # a 90° già noto (Sollwinkel 90 -> 270).
    angles: List[float] = []
    rotations: List[float] = []
    for piega, direction in zip(steps, directions):
        sollwinkel = piega.angolo if piega.angolo is not None else _BEND_LAYER_ANGLE[direction]
        angles.append(sollwinkel if direction == "BEND" else 360.0 - sollwinkel)
        rotations.append(abs(180.0 - sollwinkel))

    # accorciamento a mezzeria per ogni piega (il .bnc lo dà a quote esterne)
    cd: List[float] = []
    for piega, rotation in zip(steps, rotations):
        cd.append(external_to_centerline_deduction(piega.accorciamento_esterno, thickness, rotation))

    # flangia a mezzeria = flangia piatta + cd/2 per ogni piega adiacente.
    # 1.4 — sulla flangia centrale di una Z/omega si sommano i cd/2 di due
    # pieghe di verso opposto: a mezzeria è esatto (verificato: [60,100,50]
    # sulla Z), ma la stessa flangia come quota ESTERNA sarebbe ambigua di
    # ± spessore·tan(angolo/2). Lo sviluppo totale non ne risente.
    segments: List[float] = []
    for j, f in enumerate(flat):
        s = f
        if j >= 1:
            s += cd[j - 1] / 2.0
        if j <= len(flat) - 2:
            s += cd[j] / 2.0
        segments.append(round(s, 4))

    shape = Path(dxf_path).name[0].upper()
    section = Section(shape=shape, segments=segments, angles=list(angles),
                      thickness=thickness, inner_radius=SECTION_INNER_RADIUS_MM)

    return PartReconstruction(
        section=section,
        thickness=thickness,
        v_opening=(bnc.matrice.apertura_v if bnc.matrice else None),
        developed_length=bnc.sviluppo,
        flat_flanges=flat,
        centerline_deductions=[round(x, 4) for x in cd],
    )


# --------------------------------------------------------------------------
# accoppiamento .bnc <-> DXF piatto
# --------------------------------------------------------------------------

def part_pairs(shape_dir) -> List[Tuple[Path, Path]]:
    """Per una cartella data_4_cloude/<FORMA>/ accoppia ogni .bnc col suo
    DXF piatto.

    1) accoppiamento diretto: .bnc e .dxf con lo STESSO nome (schema nuovo,
       es. ``L12.bnc`` <-> ``L12.dxf``, ``Za60ab50b100bc250c50s3.bnc`` <->
       ``.dxf``).
    2) per i golden storici, dove il .bnc ha un nome diverso dal DXF
       verboso (``L1.bnc`` <-> ``La114ab90b114s1-EV1.dxf``): si accoppia
       per (spessore, apertura V della matrice) sui DXF ancora liberi.
    """
    shape_dir = Path(shape_dir)
    dxf_files = sorted(shape_dir.glob("*.dxf"))
    dxf_by_stem = {p.stem: p for p in dxf_files}
    pairs: List[Tuple[Path, Path]] = []
    usati: set = set()

    resto = []
    for bnc_path in sorted(shape_dir.glob("*.bnc")):
        gemello = dxf_by_stem.get(bnc_path.stem)
        if gemello is not None:
            pairs.append((bnc_path, gemello))
            usati.add(gemello.stem)
        else:
            resto.append(bnc_path)

    for bnc_path in resto:
        bnc = leggi_bnc(bnc_path)
        v = bnc.matrice.apertura_v if bnc.matrice else None
        want_t = f"s{int(round(bnc.spessore))}-"
        for dxf_path in dxf_files:
            if dxf_path.stem in usati or want_t not in dxf_path.stem:
                continue
            suffix = dxf_path.stem.split("-")[-1]
            if _CAVA_SUFFIX.get(suffix) == v:
                pairs.append((bnc_path, dxf_path))
                usati.add(dxf_path.stem)
                break
    return pairs


# --------------------------------------------------------------------------
# esplorazione: python tests/reconstruct.py
# --------------------------------------------------------------------------

def main() -> None:
    for shape in ("L", "U", "Z", "O"):
        shape_dir = DATA_DIR / shape
        if not shape_dir.is_dir():
            continue
        for bnc_path, dxf_path in part_pairs(shape_dir):
            try:
                rec = section_from_part(bnc_path, dxf_path)
            except ValueError as exc:
                print(f"{dxf_path.name}\n    salto: {exc}")
                continue
            segs = ", ".join(f"{s:g}" for s in rec.section.segments)
            angs = ", ".join(f"{a:g}" for a in rec.section.angles)
            print(f"{dxf_path.name}")
            print(f"    piatte     : {[f'{x:g}' for x in rec.flat_flanges]}")
            print(f"    mezzeria   : [{segs}]  angoli [{angs}]  s{rec.thickness:g}")
            print(f"    section    : {rec.section.name()}")
            print(f"    sviluppo   : .bnc {rec.developed_length:g}")


if __name__ == "__main__":
    main()
