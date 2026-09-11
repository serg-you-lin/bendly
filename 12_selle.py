"""
12_selle.py
------------
MAP.md D42: una mezzaluna — un settore LIBERO di cilindro, non una
frazione esatta del giro come in `11_split_pieces.py`. Una sella
calandrata tagliata a un angolo scelto perché lì taglia il pezzo, non
perché divide il tubo in N pezzi uguali (`split` non c'entra qui:
`sector_angle` è un valore a mano).

Due pezzi, liscio E sfaccettato:
  1. Sella calandra (liscia) — R300 di mezzeria, arco 60°. Non ha un
     equivalente "vista in sezione": è una curva continua, non una
     catena di flange dritte — quel concetto esiste solo per lo
     sfaccettato.
  2. Stessa sella, sfaccettata (per chi non ha la calandra) — esportata
     CON e SENZA la vista in sezione quotata, stesso principio di
     `11_split_pieces.py`: un pezzo sfaccettato aperto è, geometricamente,
     un profilo a N flange/N-1 pieghe, si vede in sezione come una L
     costruendo una `Section` dai numeri che Cylinder ha già calcolato.
     Il file "con sezione" impila il taglio VERO (da `Cylinder.develop()`)
     con `write_part_dxf()` — non passa da `export_part()` (ricalcolerebbe
     lo sviluppo con la formula sbagliata, MAP.md D45/D48).

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from bendly import Cylinder
from bendly.io.dxf import write_part_dxf
from bendly.model.section import Section

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Sella R300 di mezzeria, arco 60°, spessore 3 — stessi numeri in tutto lo
# script, solo liscio vs sfaccettato cambia.
DIAMETER = 606.0   # diametro esterno -> raggio medio = (606-3)/2 = 301.5 ~ R300
HEIGHT = 400.0
THICKNESS = 3.0
SECTOR_ANGLE = 60.0


def faceted_piece_as_section(flat, thickness: float, shape_name: str) -> Section:
    """Vedi 11_split_pieces.py — stesso helper, stesso principio: un pezzo
    sfaccettato aperto è la stessa forma di un profilo a N flange."""
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

    # === 1. Sella calandra (liscia) ==========================================
    sella_smooth = Cylinder(
        diameter=DIAMETER, height=HEIGHT, thickness=THICKNESS,
        sector_angle=SECTOR_ANGLE, label="sella_calandra",
    ).develop()
    sella_smooth.to_dxf(OUTPUT_DIR / "12_sella_calandra.dxf")

    print("--- 1. Sella calandra (liscia), R~300, 60° ---")
    print(f"  sector_angle_deg={sella_smooth.meta['sector_angle_deg']:.1f}°  "
          f"width={sella_smooth.meta['width']:.2f}")
    print("  nessuna vista in sezione per il liscio: è una curva, non flange dritte.")

    # === 2. Stessa sella, sfaccettata, CON e SENZA vista in sezione =========
    # 60° su n_facets=30 piene -> 5 faccette in questo pezzo (30*60/360=5).
    sella_faceted = Cylinder(
        diameter=DIAMETER, height=HEIGHT, thickness=THICKNESS,
        sector_angle=SECTOR_ANGLE, faceted=True, n_facets=30, label="sella_sfaccettata",
    ).develop()
    sella_faceted.to_dxf(OUTPUT_DIR / "12_sella_sfaccettata_no_section.dxf")

    sella_as_section = faceted_piece_as_section(sella_faceted, THICKNESS, "sella_R300_60_faceted")
    write_part_dxf(
        sella_faceted, OUTPUT_DIR / "12_sella_sfaccettata_with_section.dxf",
        section_flat=sella_as_section.section(), quotes=sella_as_section.flange_quotes(),
        thickness=THICKNESS, include_header=True,
    )

    print("\n--- 2. Stessa sella, sfaccettata (30 facce piene -> 5 in questo pezzo) ---")
    print(f"  n_facets={sella_faceted.meta['n_facets']} (di {sella_faceted.meta['n_facets_full']} piene)  "
          f"{len(sella_faceted.bends)} pieghe da {sella_faceted.bends[0].angle:.2f}°")
    print("  senza: 12_sella_sfaccettata_no_section.dxf   (solo il taglio + header)")
    print("  con:   12_sella_sfaccettata_with_section.dxf (taglio + sezione quotata + header)")
    for q in sella_as_section.flange_quotes():
        print(f"    flangia {q.index}: {q.display_length:.3f}  [{q.display_kind}]")

    print("\nFile in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
