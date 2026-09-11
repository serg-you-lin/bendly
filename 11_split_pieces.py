"""
11_split_pieces.py
--------------------
MAP.md D46: cono/cilindro sviluppati in PIÙ PEZZI UGUALI saldati insieme
(`split`/`sector_angle`) — il pezzo intero è troppo grande per una
lavorazione sola, tipicamente due metà. Non è la stessa cosa di una
mezzaluna a settore libero (una sella): quella è `12_selle.py`.

Tre pezzi, liscio E sfaccettato per ciascuno:
  1. Cilindro diviso in due metà — margine di saldatura sui due bordi di
     CIASCUNA metà, stesso parametro `margin` di sempre (zero codice
     nuovo per quello, era già generico).
  2. Cono diviso in due — qui "pieno" non è 360 a scelta: è il valore che
     la geometria del cono impone (`meta["full_angle_deg"]`).
  3. Bonus sullo sfaccettato: lo stesso pezzo esportato CON e SENZA la
     vista in sezione — un pezzo sfaccettato è, geometricamente, un
     profilo a N flange/N-1 pieghe (la stessa forma di una L), quindi si
     può "vedere in sezione" quotata come si fa per una L
     (09_section_view.py), costruendo una `Section` dai numeri che
     Cylinder ha già calcolato. NON passa da `export_part()`: quello
     ricalcolerebbe lo sviluppo con la formula a deduzione di
     `BentProfile`, diversa da quella ad addizione delle faccette (MAP.md
     D45/D48 — verificato, ~2mm di differenza reale, non arrotondamento).
     Il taglio nel file "con sezione" resta quello vero calcolato da
     `Cylinder`, la sezione è solo impilata sopra con `write_part_dxf()`.

Il liscio (calandra) non ha un equivalente "vista in sezione": è una
curva continua, non una catena di flange dritte — quel concetto si
applica solo allo sfaccettato.

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from bendly import Cone, Cylinder
from bendly.io.dxf import write_part_dxf
from bendly.model.section import Section

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def faceted_piece_as_section(flat, thickness: float, shape_name: str) -> Section:
    """Un pezzo sfaccettato APERTO (N faccette, N-1 pieghe) è la stessa
    forma di un profilo piegato a N flange — costruisce la Section
    equivalente dai numeri che Cone/Cylinder hanno già calcolato: corda,
    angolo di piega (convertito dalla convenzione Bend.angle a quella di
    Section.angles, 180 - rotazione), raggio VERO usato (dalla
    calibrazione, non il raggio simbolico 1mm di Section.default())."""
    n = flat.meta["n_facets"]
    chord = flat.meta["facet_width"]
    naming_angle = 180.0 - flat.bends[0].angle
    radius = flat.meta["facet_bend_radius"]
    return Section(
        shape=shape_name, segments=[chord] * n, angles=[naming_angle] * (n - 1),
        thickness=thickness, inner_radius=radius,
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # === 1. Cilindro diviso in due metà =====================================
    cyl_full = Cylinder(diameter=600, height=800, thickness=3).develop()
    cyl_half_smooth = Cylinder(
        diameter=600, height=800, thickness=3, split=2, margin=3, label="cyl_half_smooth",
    ).develop()
    cyl_half_smooth.to_dxf(OUTPUT_DIR / "11_cylinder_half_smooth.dxf", show_margin_reference=True)

    cyl_half_faceted = Cylinder(
        diameter=600, height=800, thickness=3, faceted=True, n_facets=12,
        split=2, margin=3, label="cyl_half_faceted",
    ).develop()
    cyl_half_faceted.to_dxf(OUTPUT_DIR / "11_cylinder_half_faceted_no_section.dxf")

    print("--- 1. Cilindro diviso in due metà ---")
    print(f"  liscio:      width intero={cyl_full.meta['width']:.2f}  "
          f"metà={cyl_half_smooth.meta['width']:.2f} (atteso: metà)")
    print(f"  sfaccettato: {cyl_half_faceted.meta['n_facets']} facce "
          f"(di {cyl_half_faceted.meta['n_facets_full']} piene)  "
          f"{len(cyl_half_faceted.bends)} pieghe da {cyl_half_faceted.bends[0].angle:.2f}°")

    # === 2. Cono diviso in due ===============================================
    cone_full = Cone(top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5).develop()
    cone_half_smooth = Cone(
        top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5,
        split=2, margin=5, label="cone_half_smooth",
    ).develop()
    cone_half_smooth.to_dxf(OUTPUT_DIR / "11_cone_half_smooth.dxf", show_margin_reference=True)

    cone_half_faceted = Cone(
        top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5,
        faceted=True, n_facets=10, split=2, label="cone_half_faceted",
    ).develop()
    cone_half_faceted.to_dxf(OUTPUT_DIR / "11_cone_half_faceted_no_section.dxf")

    print("\n--- 2. Cono diviso in due ---")
    print(f"  sviluppo naturale: full_angle_deg={cone_full.meta['full_angle_deg']:.2f}°")
    print(f"  liscio, metà: sector_angle_deg={cone_half_smooth.meta['sector_angle_deg']:.2f}° "
          f"(atteso: metà di full_angle_deg)")
    print(f"  sfaccettato, metà: {cone_half_faceted.meta['n_facets']} facce (atteso: 5)")

    # === 3. Sfaccettato: lo stesso pezzo, CON e SENZA vista in sezione ======
    # "senza" e' gia' stato scritto sopra (cyl_half_faceted.to_dxf(), plain).
    # "con": impila taglio VERO + sezione + header con write_part_dxf().
    half_as_section = faceted_piece_as_section(cyl_half_faceted, 3.0, "half_cylinder_12")
    write_part_dxf(
        cyl_half_faceted, OUTPUT_DIR / "11_cylinder_half_faceted_with_section.dxf",
        section_flat=half_as_section.section(), quotes=half_as_section.flange_quotes(),
        thickness=3.0, include_header=True,
    )

    print("\n--- 3. Sfaccettato con/senza vista in sezione ---")
    print("  senza: 11_cylinder_half_faceted_no_section.dxf   (solo il taglio + header)")
    print("  con:   11_cylinder_half_faceted_with_section.dxf (taglio + sezione quotata + header)")
    for q in half_as_section.flange_quotes():
        print(f"    flangia {q.index}: {q.display_length:.3f}  [{q.display_kind}]")

    print("\nFile in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
