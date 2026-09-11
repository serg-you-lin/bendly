"""
unfold/human_layer.py
-----------------------
Il layer umano (Fase 3, MAP.md D28/D30): un carpentiere dà le quote
ESTERNO-ESTERNO del pezzo, come le leggerebbe su un disegno — non le quote
a MEZZERIA che vuole `BentProfile`. Questo modulo è la SOLA API pubblica
che fa la conversione da sola: prende quote esterne, converte, chiama il
motore, ritorna un `FlatGeometry` — chi lo usa non deve mai vedere la
mezzeria.

Non sta né in model/ né in core/ né in rules/: incolla core (`BentProfile`)
e rules (`external_flanges_to_centerline`) insieme — esattamente il ruolo
che avrebbe un `pipeline/`. È un file solo perché per ora sono un paio di
funzioni, non un'intera fase orchestrata (MAP.md D26: niente `pipeline/`
finché non serve davvero un'orchestrazione multi-fase).

`export_part()` (Fase 3, D32) fa lo stesso mestiere per l'export finito:
incolla `Section` (taglio + vista in sezione, la stessa forma vista in
due modi, D31) e `io.dxf.write_part_dxf` (che sa impilare i livelli in
DXF) — chi chiama non deve mai occuparsi di bbox o offset.
"""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from .core.bend import Bend, BentProfile
from .model.geometry import FlatGeometry
from .rules.deduction import external_flanges_to_centerline

if TYPE_CHECKING:
    from .model.section import Section


def develop_from_external_flanges(
    external_flanges: List[float],
    bends: List[Bend],
    thickness: float,
    width: float,
    calibration: Optional[object] = None,
    material: str = "acciaio",
    orientation: str = "horizontal",
    label: str = "bent_profile",
) -> FlatGeometry:
    """
    Come `BentProfile.develop()`, ma `external_flanges` sono quote
    ESTERNO-ESTERNO (l'apice virtuale delle facce esterne, come la quota
    che dà un carpentiere) invece che a mezzeria.

    Converte con `external_flanges_to_centerline()` — indipendente dal
    raggio, MAP.md D28 — e poi chiama `BentProfile`: il core resta cieco
    alle quote esterne e non cambia.

    bends: la stessa lista che passeresti a `BentProfile` — un `Bend` per
    piega, con `angle` obbligatorio (+ `cava` per piega solo se diversa da
    quella di tabella). `calibration`: se None -> "default" (MAP.md D33).
    """
    bend_angles = [b.angle for b in bends]
    centerline_flanges = external_flanges_to_centerline(external_flanges, bend_angles, thickness)
    return BentProfile(
        flanges=centerline_flanges, bends=bends, thickness=thickness, width=width,
        material=material, orientation=orientation, label=label, calibration=calibration,
    ).develop()


def export_part(
    section: "Section",
    width: float,
    path: str,
    calibration: Optional[object] = None,
    include_section: bool = False,
    include_header: bool = False,
    tolerance: float = 0.05,
    margin: float = 20.0,
):
    """
    Esporta un pezzo su un UNICO file DXF a livelli (Fase 3, MAP.md D32):
    taglio (sempre) + vista in sezione quotata (`include_section`) +
    header (`include_header`), impilati in verticale — mai affiancati,
    stesso ordine per qualunque combinazione: taglio, poi sezione se
    c'è, poi header se c'è, ognuno sotto al precedente.

    `section` porta le quote/il verso (Fase 3.3, D31: `Section` sa fare
    sia il taglio che la vista in sezione, sono la stessa forma vista in
    due modi); `width`/`calibration` servono solo a sviluppare il taglio
    (`section.to_bent_profile()`) — la vista in sezione non li usa.
    """
    flat = section.to_bent_profile(width, calibration=calibration).develop()
    section_flat = section.section() if include_section else None
    quotes = section.flange_quotes() if include_section else None

    from .io.dxf import write_part_dxf
    return write_part_dxf(
        flat, path,
        section_flat=section_flat, quotes=quotes, thickness=section.thickness,
        include_header=include_header, tolerance=tolerance, margin=margin,
    )
