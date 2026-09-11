"""
00_cone_cylinder.py
-------------------
Equivalente di dxf-forge/cono.py con la nuova API: modifica i valori qui
sotto ed esegui. Sostituisce due file DXF separati (cono + cilindro) invece
di un unico disegno combinato — un file per parte, come nell'uso reale.

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from unfold import Cone, Cylinder

# =============================================================================
# PARAMETRI DI INPUT — diametri ESTERNI, in millimetri
# =============================================================================

TOP_DIAMETER = 200
BOTTOM_DIAMETER = 150
CONE_HEIGHT = 100

CYLINDER_DIAMETER = 150
CYLINDER_HEIGHT = 25

THICKNESS = 2

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cone_flat = Cone(
        top_diameter=TOP_DIAMETER,
        bottom_diameter=BOTTOM_DIAMETER,
        height=CONE_HEIGHT,
        thickness=THICKNESS,
        label="sviluppo_cono",
    ).develop()
    cone_flat.to_dxf(OUTPUT_DIR / "sviluppo_cono.dxf")

    cylinder_flat = Cylinder(
        diameter=CYLINDER_DIAMETER,
        height=CYLINDER_HEIGHT,
        thickness=THICKNESS,
        label="sviluppo_cilindro",
        margin=2.0
        
    ).develop()
    cylinder_flat.to_dxf(OUTPUT_DIR / "sviluppo_cilindro.dxf")

    print("Cono:", cone_flat.meta)
    print("Cilindro:", cylinder_flat.meta)


if __name__ == "__main__":
    main()