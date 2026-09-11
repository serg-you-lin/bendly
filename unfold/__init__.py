"""
unfold
------
Motore matematico puro per sviluppi piani di forme sviluppabili: forme
avvolte (cono, cilindro) e profili piegati a pressopiega (BentProfile).
Zero dipendenze per il calcolo — la lettura di un disegno
(`read_section`) compresa: MAP.md D43 ha provato e ritrattato
un'integrazione nativa con forge, non ancora giustificata finché "pippo"
(il futuro interprete di disegno, `docs/ARCHITECTURE.md`) non esiste
davvero. `.develop()` ritorna sempre un FlatGeometry — dati puri, nessun
import di forge.

    from unfold import Cone, Cylinder, Bend, BentProfile

    flat = Cone(top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5).develop()
    flat.to_dxf("cone.dxf")   # richiede forge installato a fianco

    flat = Cylinder(diameter=1016, height=3895, thickness=5).develop()
    flat.to_dxf("cylinder.dxf")

    flat = BentProfile(
        flanges=[50, 80, 50],
        bends=[Bend(angle=90), Bend(angle=90)],
        thickness=2, width=300,
        calibration="default",        # decide l'accorciamento dalla cava (spessore->cava)
    ).develop()
    flat.to_dxf("bent_profile.dxf")   # rettangolo + linee di piega (role="bending")

`FlatGeometry.entities` è nello stesso schema accettato da
`forge.load_geometry()` — è il contratto neutro fra i due progetti.
"""

from importlib.metadata import version, PackageNotFoundError

# La versione vive SOLO in pyproject.toml: qui si legge a runtime dai
# metadati del pacchetto installato. In sviluppo senza install (`pip
# install -e .` non ancora dato) si ripiega su un segnaposto.
try:
    __version__ = version("unfold")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"

from .model.geometry import FlatGeometry, polar_point
from .core.cone import Cone
from .core.cylinder import Cylinder
from .core.bend import Bend, BendResult, BentProfile, estimate_k_factor, MATERIAL_K_FACTORS
from .rules.deduction import (
    Calibration, DeductionInfo, bend_deduction, k_din6935, deduction_din6935,
    TIPI_CLIENTE, tipo_cliente_coerente,
)
from .model.section import Section, FlangeFace, FlangeQuote
from .rules.read_section import SectionReading, SheetThicknessTable, read_section
from .human_layer import develop_from_external_flanges, export_part

__all__ = [
    "Cone", "Cylinder", "FlatGeometry", "polar_point",
    "Bend", "BendResult", "BentProfile", "estimate_k_factor", "MATERIAL_K_FACTORS",
    "Calibration", "DeductionInfo", "bend_deduction", "k_din6935", "deduction_din6935",
    "TIPI_CLIENTE", "tipo_cliente_coerente",
    "Section", "FlangeFace", "FlangeQuote", "read_section", "SectionReading", "SheetThicknessTable",
    "develop_from_external_flanges", "export_part",
]
