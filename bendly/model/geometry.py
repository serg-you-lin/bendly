"""
bendly/model/geometry.py
-------------------------
FlatGeometry — il contratto neutro tra il motore matematico di Unfold e
qualsiasi consumatore a valle. Puri dati Python (dataclass + dict), zero
import di forge: ogni entità in `.entities` è nello stesso schema accettato
da `forge.load_geometry()` — {"type": "line"|"arc"|"circle"|"polyline", ...,
"role": ...} — così Unfold non deve conoscere alcun tipo interno di forge, e
forge non deve conoscere nulla di Unfold.

forge entra in gioco SOLO in `bendly/io/dxf.py` (`to_forge_result()`/
`to_dxf()`), con import lazy: se forge non è installato, `Cone(...).develop()`
funziona comunque e i dati grezzi restano leggibili/utilizzabili da
`.entities`/`.meta` — solo il salvataggio DXF richiede forge installato a
fianco (`pip install -e <percorso a dxf-forge>`). `FlatGeometry.to_dxf()`/
`.to_forge_result()` restano metodi comodi da chiamare, ma il loro corpo
vive in `bendly/io/dxf.py`: questo modulo non importa mai forge, nemmeno
lazy — lo strato `model` resta pulito, lo strato `io` fa da ponte.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

VALID_ORIENTATIONS = frozenset({"horizontal", "vertical"})


def polar_point(
    radius: float,
    angle_deg: float,
    origin: Tuple[float, float] = (0.0, 0.0),
) -> Tuple[float, float]:
    """Punto a coordinate polari (angolo in gradi)."""
    rad = math.radians(angle_deg)
    return (origin[0] + radius * math.cos(rad), origin[1] + radius * math.sin(rad))


def _check_orientation(orientation: str) -> None:
    if orientation not in VALID_ORIENTATIONS:
        raise ValueError(
            f"orientation deve essere 'horizontal' o 'vertical', ricevuto {orientation!r}."
        )


def swap_xy(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Riflette la geometria lungo la diagonale y=x (scambia gli assi X/Y) — il
    modo più semplice per ruotare di 90° uno sviluppo canonico senza dover
    ritraslare in seguito per tenerlo in quadrante positivo (una vera
    rotazione attorno all'origine porterebbe metà coordinate in negativo).

    È una riflessione, non una rotazione pura: inverte il verso di
    percorrenza degli archi (ccw <-> cw) e mappa l'angolo polare
    theta -> 90 - theta. Per un rettangolo o un settore simmetrico rispetto
    a un asse — gli unici casi che Cone/Cylinder producono — il risultato è
    geometricamente identico a una rotazione di 90° a fini di orientamento.
    """
    swapped: List[Dict[str, Any]] = []
    for entity in entities:
        e = dict(entity)
        kind = e.get("type")
        if kind == "line":
            e["start"] = (e["start"][1], e["start"][0])
            e["end"] = (e["end"][1], e["end"][0])
        elif kind == "polyline":
            e["points"] = [(p[1], p[0]) for p in e["points"]]
        elif kind == "circle":
            e["center"] = (e["center"][1], e["center"][0])
        elif kind == "arc":
            e["center"] = (e["center"][1], e["center"][0])
            e["start_angle"] = 90.0 - e["start_angle"]
            e["end_angle"] = 90.0 - e["end_angle"]
            e["ccw"] = not e.get("ccw", True)
        swapped.append(e)
    return swapped


@dataclass
class FlatGeometry:
    """
    Sviluppo piano di una forma sviluppabile — output di Cone.develop() /
    Cylinder.develop().

    entities:           geometria di taglio, schema di forge.load_geometry()
    label:               nome della parte
    meta:                 valori calcolati (diametri medi, generatrice, ...)
    reference_entities:    geometria SOLO di riferimento (es. i due bordi del
                           foglio pieno prima del margine di saldatura) — mai
                           passata a forge.load_geometry(), disegnata solo in
                           to_dxf() su un layer separato, tratteggiato
    bends:                 una BendResult per piega (solo da
                           BentProfile.develop()); dice per ogni piega
                           l'accorciamento usato e da dove viene
    """
    entities: List[Dict[str, Any]]
    label: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)
    reference_entities: List[Dict[str, Any]] = field(default_factory=list)
    # una BendResult per piega — popolata solo da BentProfile.develop(),
    # vuota per Cone / Cylinder (vedi bendly/core/bend.py)
    bends: List[Any] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Integrazione con forge — deleghe sottili a bendly/io/dxf.py, che è
    # l'unico modulo a importare forge (lazy). Questo file resta pulito.
    # ------------------------------------------------------------------

    def to_forge_result(self, tolerance: float = 0.05):
        """
        Traduce questo sviluppo in un ForgeResult passando da
        forge.load_geometry() + forge.heal_and_detect() — stesso contratto
        di qualsiasi altra sorgente forge (DXF, PDF, ...).
        """
        from ..io.dxf import to_forge_result
        return to_forge_result(self, tolerance=tolerance)

    def to_dxf(
        self,
        path: str,
        tolerance: float = 0.05,
        annotate: bool = True,
        show_margin_reference: bool = False,
    ):
        """
        Scrive lo sviluppo su file DXF via forge.to_dxf() — layer/colori
        coerenti col resto dell'output forge.

        annotate:               blocco di testo con i valori di `.meta`,
                                 layer "Notes" — riferimento in officina, non
                                 fa parte della geometria di taglio
        show_margin_reference:   default False (opt-in). Se True e c'è un
                                 margine di saldatura, disegna il contorno
                                 completo del foglio pieno (prima del
                                 margine) tratteggiato sul layer
                                 "MarginReference" — solo riferimento, mai
                                 geometria di taglio
        """
        from ..io.dxf import to_dxf
        return to_dxf(
            self, path, tolerance=tolerance, annotate=annotate,
            show_margin_reference=show_margin_reference,
        )
