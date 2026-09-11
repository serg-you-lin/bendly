"""
01_faceted.py
-------------
Prova dello sviluppo SFACCETTATO (faceted=True) — invece del settore/
rettangolo da calandra, un cono o cilindro approssimato con N faccette
piane (8 di default) unite da pieghe a pressopiega, per chi non ha la
calandra. Le API di sempre (senza faceted) restano identiche.

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from bendly import Cone, Cylinder

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Cilindro sfaccettato, 8 facce (default) --------------------------
    cyl_faceted = Cylinder(
        diameter=150, height=500, thickness=2, faceted=True,
        label="cilindro_sfaccettato",
    ).develop()
    cyl_faceted.to_dxf(OUTPUT_DIR / "cilindro_sfaccettato.dxf")

    # --- Stesso cilindro, 12 faccette invece di 8 --------------------------
    cyl_faceted_12 = Cylinder(
        diameter=150, height=500, thickness=2, faceted=True, n_facets=12,
        label="cilindro_sfaccettato_12",
    ).develop()
    cyl_faceted_12.to_dxf(OUTPUT_DIR / "cilindro_sfaccettato_12.dxf")

    # --- Cono sfaccettato, 8 facce (default) -------------------------------
    cone_faceted = Cone(
        top_diameter=200, bottom_diameter=150, height=100, thickness=2,
        faceted=True, label="cono_sfaccettato",
    ).develop()
    cone_faceted.to_dxf(OUTPUT_DIR / "cono_sfaccettato.dxf")

    # --- Confronto: stesso cono, sviluppo liscio da calandra ----------------
    cone_smooth = Cone(
        top_diameter=200, bottom_diameter=150, height=100, thickness=2,
        label="cono_liscio",
    ).develop()
    cone_smooth.to_dxf(OUTPUT_DIR / "cono_liscio.dxf")

    print("Cilindro sfaccettato (8) — larghezza faccetta:", cyl_faceted.meta["facet_width"])
    print("  sviluppo totale (8 facce + 7 pieghe):", cyl_faceted.meta["width"])
    print()
    print("Cono sfaccettato (8) — corda esterna:", cone_faceted.meta["outer_facet_width"])
    print("  corda interna:", cone_faceted.meta["inner_facet_width"])
    print("  angolo per faccetta:", cone_faceted.meta["facet_angle_deg"])
    print("  K-factor usato:", cone_faceted.meta["facet_k_factor"])
    print()
    print("Cono liscio — angolo settore:", cone_smooth.meta["sector_angle_deg"])
    print()
    print("File in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
