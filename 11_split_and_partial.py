"""
11_split_and_partial.py
-------------------------
MAP.md D46: cono/cilindro sviluppati in pezzi uguali (`split`/`sector_angle`)
— tipicamente due metà saldate insieme quando il pezzo è troppo grande per
una lavorazione sola, liscio o sfaccettato. E il caso "mezzaluna" di MAP.md
D42 (`sector_angle` libero, non necessariamente una frazione esatta del
giro): una lamiera calandrata su un raggio ma tagliata prima di richiudersi
— una sella, non un tubo.

Quattro pezzi:
  1. Cilindro liscio diviso in due metà (split=2) — margine di saldatura sui
     due bordi di CIASCUNA metà, stesso parametro `margin` di sempre.
  2. Cilindro SFACCETTATO diviso in due (split=2) — prima di stanotte non si
     poteva fare (MAP.md D42 lo lasciava esplicitamente "non deciso").
     `flat.bends` porta una BendResult per giunto, come per BentProfile.
  3. Cono liscio e sfaccettato divisi in due — stessa idea, ma qui "pieno"
     non è 360 a scelta: è il valore che la geometria del cono impone
     (`meta["full_angle_deg"]`).
  4. Una mezzaluna: settore libero (non un `split`) di un cilindro liscio,
     es. una sella R300/60°.

Bonus, alla fine: la metà sfaccettata del punto 2 è — geometricamente — la
STESSA cosa di un profilo piegato a N flange (N facce, N-1 pieghe): la si
può quindi "vedere in sezione", quotata, esattamente come si fa per una L
(09_section_view.py) — costruendo una `Section` dai numeri che il cilindro
stesso ha già calcolato (corda, angolo di piega, raggio VERO usato).

Il file finale impila TAGLIO VERO + sezione + header, come fa
`export_part()` per una L — ma non passa da `export_part()`: quello
ricalcola lo sviluppo con `Section.to_bent_profile().develop()`, che usa
la formula a DEDUZIONE di `BentProfile` (accorciamento sottratto da una
flangia apice-apice) — non la stessa formula ad ADDIZIONE delle faccette
(bend allowance sommato fra corde, MAP.md D45). Provato: i due total
length NON coincidono (differenza reale, ~2mm su questo pezzo, non un
arrotondamento) — sono due geometrie diverse che condividono solo lo
stesso K/raggio, non la stessa formula. Il taglio giusto resta quello che
`Cylinder.develop()` ha già calcolato; `write_part_dxf()` (lo strato sotto
`export_part()`) lo impila con la sezione senza doverlo ricalcolare.

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from unfold import Cone, Cylinder
from unfold.io.dxf import write_part_dxf
from unfold.model.section import Section

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # === 1. Cilindro liscio diviso in due metà =============================
    full_smooth = Cylinder(diameter=600, height=800, thickness=3).develop()
    half_smooth = Cylinder(
        diameter=600, height=800, thickness=3, split=2, margin=3, label="cyl_half_smooth",
    ).develop()
    half_smooth.to_dxf(OUTPUT_DIR / "11_cylinder_half_smooth.dxf", show_margin_reference=True)

    print("--- 1. Cilindro liscio, split=2 ---")
    print(f"  intero:  width={full_smooth.meta['width']:.2f}")
    print(f"  metà:    width={half_smooth.meta['width']:.2f} "
          f"(atteso: metà dell'intero) width_cut={half_smooth.meta['width_cut']:.2f} (con 3mm di margine)")

    # === 2. Cilindro SFACCETTATO diviso in due metà =========================
    full_faceted = Cylinder(
        diameter=600, height=800, thickness=3, faceted=True, n_facets=12,
    ).develop()
    half_faceted = Cylinder(
        diameter=600, height=800, thickness=3, faceted=True, n_facets=12,
        split=2, margin=3, label="cyl_half_faceted",
    ).develop()
    half_faceted.to_dxf(OUTPUT_DIR / "11_cylinder_half_faceted.dxf", show_margin_reference=True)

    print("\n--- 2. Cilindro sfaccettato (12 facce), split=2 ---")
    print(f"  intero:  {full_faceted.meta['n_facets']} facce, {len(full_faceted.bends)} pieghe")
    print(f"  metà:    {half_faceted.meta['n_facets']} facce (atteso: metà, 6), "
          f"{len(half_faceted.bends)} pieghe")
    print(f"  faccetta e raggio di piega identici fra intero e metà "
          f"(proprietà del poligono, non di quanto ne prendi):")
    print(f"    facet_width  intero={full_faceted.meta['facet_width']:.3f}  "
          f"metà={half_faceted.meta['facet_width']:.3f}")
    print(f"    facet_bend_radius intero={full_faceted.meta['facet_bend_radius']:.3f}  "
          f"metà={half_faceted.meta['facet_bend_radius']:.3f}")
    for b in half_faceted.bends:
        print(f"    piega: angolo={b.angle:.2f}°  regola={b.rule}  {b.source}")

    # === 3. Cono liscio e sfaccettato divisi in due =========================
    cone_full = Cone(top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5).develop()
    cone_half = Cone(
        top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5,
        split=2, margin=5, label="cone_half_smooth",
    ).develop()
    cone_half.to_dxf(OUTPUT_DIR / "11_cone_half_smooth.dxf", show_margin_reference=True)

    cone_half_faceted = Cone(
        top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5,
        faceted=True, n_facets=10, split=2, label="cone_half_faceted",
    ).develop()
    cone_half_faceted.to_dxf(OUTPUT_DIR / "11_cone_half_faceted.dxf")

    print("\n--- 3. Cono liscio e sfaccettato, split=2 ---")
    print(f"  sviluppo naturale del cono: full_angle_deg={cone_full.meta['full_angle_deg']:.2f}°")
    print(f"  metà liscia: sector_angle_deg={cone_half.meta['sector_angle_deg']:.2f}° "
          f"(atteso: metà di full_angle_deg)")
    print(f"  metà sfaccettata (10 facce piene): "
          f"{cone_half_faceted.meta['n_facets']} facce (atteso: 5)")

    # === 4. Mezzaluna: settore libero, non un N-esimo del giro ==============
    # Sella calandrata: raggio medio 300, arco 60°, spessore 3 — MAP.md D42.
    # Non è "1/split del giro": è un angolo scelto perché lì taglia il
    # pezzo, non perché divide il tubo in pezzi uguali.
    sella = Cylinder(
        diameter=606.0, height=400, thickness=3.0, sector_angle=60.0, label="sella_R300_60",
    ).develop()
    sella.to_dxf(OUTPUT_DIR / "11_mezzaluna_sella.dxf")

    print("\n--- 4. Mezzaluna (sella calandrata R300, 60°) ---")
    print(f"  sector_angle_deg={sella.meta['sector_angle_deg']:.1f}°  width={sella.meta['width']:.2f}")

    # Stessa mezzaluna, ma SFACCETTATA (per chi non ha la calandra) — MAP.md
    # D46: 60° deve tagliare n_facets su un confine esatto. n_facets=30 sul
    # giro intero -> 30*60/360 = 5 faccette in questo pezzo, un profilo
    # riconoscibile ad arco invece di una sola faccetta piatta.
    sella_faceted = Cylinder(
        diameter=606.0, height=400, thickness=3.0,
        sector_angle=60.0, faceted=True, n_facets=30, label="sella_R300_60_sfaccettata",
    ).develop()
    sella_faceted.to_dxf(OUTPUT_DIR / "11_mezzaluna_sella_sfaccettata.dxf")

    print("\n--- 4b. Stessa mezzaluna, sfaccettata (30 facce piene -> 5 in questo pezzo) ---")
    print(f"  n_facets={sella_faceted.meta['n_facets']} (di {sella_faceted.meta['n_facets_full']} piene)  "
          f"{len(sella_faceted.bends)} pieghe da {sella_faceted.bends[0].angle:.2f}°")
    print(f"  facet_width={sella_faceted.meta['facet_width']:.3f}  "
          f"facet_bend_radius={sella_faceted.meta['facet_bend_radius']:.3f}")

    # === Bonus: vedere in sezione QUALUNQUE pezzo sfaccettato ===============
    # Un pezzo sfaccettato APERTO (metà cilindro, mezzaluna, cono, non
    # importa il nome) è, geometricamente, un profilo a N flange/N-1
    # pieghe — la stessa forma di una L/U/Z. Non serve che sia una delle
    # "shape" con un nome (L/U/Z/O): basta costruire una Section con i
    # numeri che Cone/Cylinder hanno già calcolato:
    #   - segments: facet_width (o chord), ripetuto per ogni faccetta
    #   - angles: nella naming scheme (piatto=180), non in convenzione
    #     Bend.angle (rotazione da piatto) — la conversione è 180 - rotazione
    #   - inner_radius: il raggio VERO usato per le pieghe (dalla
    #     calibrazione), non il raggio simbolico 1mm di Section.default()
    def faceted_piece_as_section(flat, thickness: float, shape_name: str) -> Section:
        n = flat.meta["n_facets"]
        chord = flat.meta["facet_width"]
        rotation = flat.bends[0].angle
        naming_angle = 180.0 - rotation
        radius = flat.meta["facet_bend_radius"]
        return Section(
            shape=shape_name, segments=[chord] * n, angles=[naming_angle] * (n - 1),
            thickness=thickness, inner_radius=radius,
        )

    half_as_section = faceted_piece_as_section(half_faceted, 3.0, "half_cylinder_12")
    sella_as_section = faceted_piece_as_section(sella_faceted, 3.0, "sella_R300_60_faceted")

    # Un file solo per pezzo: TAGLIO VERO (quello che Cylinder ha già
    # calcolato) + sezione + header, impilati — write_part_dxf() invece di
    # export_part() apposta (vedi docstring in cima: export_part
    # ricalcolerebbe lo sviluppo con la formula sbagliata per un pezzo
    # sfaccettato).
    for label, flat, sec, fname in (
        ("metà cilindro", half_faceted, half_as_section, "11_half_faceted_full.dxf"),
        ("mezzaluna", sella_faceted, sella_as_section, "11_mezzaluna_sfaccettata_full.dxf"),
    ):
        write_part_dxf(
            flat, OUTPUT_DIR / fname,
            section_flat=sec.section(), quotes=sec.flange_quotes(), thickness=3.0,
            include_header=True,
        )
        print(f"\n--- Bonus: la {label} sfaccettata — taglio + sezione + header in un file solo ---")
        n = len(sec.segments)
        print(f"  {n} flange da {sec.segments[0]:.3f}mm, {n - 1} pieghe da "
              f"{sec.angles[0]:.1f}° (naming scheme), raggio {sec.inner_radius:.3f}mm")
        for q in sec.flange_quotes():
            print(f"  flangia {q.index}: {q.display_length:.3f}  [{q.display_kind}]")

    print("\nFile in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
