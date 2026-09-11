"""
03_margin_orientation.py
------------------------
Prova dei due nuovi parametri di Cone/Cylinder:

- orientation: quale asse dello sviluppo è il lato lungo.
  Cylinder: "vertical" (default, canonico: circonferenza su X) | "horizontal" (swap: lunghezza assiale su X).
  Cone:     "vertical" (default) | "horizontal".
- margin: margine di saldatura TOTALE, tolto in parti uguali dai due lati
  (margin=2 -> pezzo 1 mm più corto per lato).
    Cylinder: toglie sui due bordi dello sviluppo/circonferenza (cucitura
              longitudinale del rotolo) — non sopra/sotto lungo l'altezza.
    Cone:     toglie sui due bordi radiali (riduce l'angolo del settore).
  Con margin>0 e to_dxf(show_margin_reference=True) (default False, opt-in),
  in output compare anche il contorno del foglio pieno prima del margine,
  tratteggiato su un layer separato ("MarginReference") — solo riferimento,
  mai geometria di taglio.

Genera 4 file per il cilindro (orizzontale/verticale x con/senza margine) e
2 per il cono (con/senza margine, verticale), così puoi aprirli e
confrontarli in AutoCAD.

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from unfold import Cone, Cylinder

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Cilindro: verticale (default) vs orizzontale, senza margine -----
    Cylinder(
        diameter=150, height=25, thickness=2, label="cyl_vertical",
    ).develop().to_dxf(OUTPUT_DIR / "cyl_vertical.dxf")

    Cylinder(
        diameter=150, height=25, thickness=2, orientation="horizontal",
        label="cyl_horizontal",
    ).develop().to_dxf(OUTPUT_DIR / "cyl_horizontal.dxf")

    # --- Cilindro: con 6 mm di margine totale (destra/sinistra sulla
    # circonferenza), riferimento esplicitamente acceso — show_margin_reference
    # è opt-in, default False.
    cyl_margin = Cylinder(
        diameter=150, height=25, thickness=2, margin=6, label="cyl_margin",
    ).develop()
    cyl_margin.to_dxf(OUTPUT_DIR / "cyl_margin.dxf", show_margin_reference=True)

    # --- Cono: verticale (default), senza e con margine --------------------
    Cone(
        top_diameter=200, bottom_diameter=150, height=100, thickness=2,
        label="cone_no_margin",
    ).develop().to_dxf(OUTPUT_DIR / "cone_no_margin.dxf")

    cone_margin = Cone(
        top_diameter=200, bottom_diameter=150, height=100, thickness=2,
        margin=10, label="cone_margin",
    ).develop()
    cone_margin.to_dxf(OUTPUT_DIR / "cone_margin.dxf", show_margin_reference=True)

    cyl_no_margin = Cylinder(diameter=150, height=25, thickness=2).develop()
    cone_no_margin = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2).develop()

    print("Cilindro senza margine — width:", cyl_no_margin.meta["width"], "width_cut:", cyl_no_margin.meta["width_cut"])
    print("Cilindro con margine=6 — width:", cyl_margin.meta["width"], "(piena) width_cut:", cyl_margin.meta["width_cut"], "(atteso: width - 6)")
    print("Cono senza margine — angolo settore:", cone_no_margin.meta["sector_angle_deg"])
    print("Cono con margine=10 — angolo settore:", cone_margin.meta["sector_angle_deg"], "(atteso: più piccolo)")
    print()
    print("File in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
