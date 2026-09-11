"""
02_compare_cone.py
------------------
Genera lo STESSO cono in entrambi i modi — sviluppo liscio da calandra e
sviluppo sfaccettato — con parametri identici, per confrontarli fianco a
fianco (apri i due DXF in AutoCAD, o guarda i numeri stampati qui sotto).

Modifica i parametri qui sotto per riprodurre il caso che ti sembra "molto
diverso" e rilancia.

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from bendly import Cone

# =============================================================================
# PARAMETRI DI INPUT — diametri ESTERNI, in millimetri
# =============================================================================

TOP_DIAMETER = 450
BOTTOM_DIAMETER = 250
HEIGHT = 100
THICKNESS = 2

N_FACETS = 16
FACET_BEND_RADIUS = 1   # None -> usa THICKNESS, come di default in Cone

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    smooth = Cone(
        top_diameter=TOP_DIAMETER, bottom_diameter=BOTTOM_DIAMETER,
        height=HEIGHT, thickness=THICKNESS, label="cono_liscio",
    ).develop()
    smooth.to_dxf(OUTPUT_DIR / "confronto_cono_liscio.dxf")

    faceted = Cone(
        top_diameter=TOP_DIAMETER, bottom_diameter=BOTTOM_DIAMETER,
        height=HEIGHT, thickness=THICKNESS, faceted=True, n_facets=N_FACETS,
        facet_bend_radius=FACET_BEND_RADIUS, label="cono_sfaccettato",
    ).develop()
    faceted.to_dxf(OUTPUT_DIR / "confronto_cono_sfaccettato.dxf")

    result_smooth = smooth.to_forge_result()
    result_faceted = faceted.to_forge_result()
    area_smooth = result_smooth.parts[0].outer.area
    area_faceted = result_faceted.parts[0].outer.area
    bbox_smooth = result_smooth.parts[0].outer.bbox
    bbox_faceted = result_faceted.parts[0].outer.bbox

    facet_span = faceted.meta["n_facets"] * faceted.meta["facet_angle_deg"]
    smooth_span = smooth.meta["sector_angle_deg"]

    print("=" * 70)
    print(f"Parametri: top={TOP_DIAMETER}  bottom={BOTTOM_DIAMETER}  "
          f"height={HEIGHT}  thickness={THICKNESS}  n_facets={N_FACETS}")
    print("=" * 70)
    print()
    print(f"{'':25s}{'liscio':>15s}{'sfaccettato':>18s}{'diff %':>10s}")
    print(f"{'angolo/span totale':25s}{smooth_span:15.3f}{facet_span:18.3f}"
          f"{100 * (facet_span - smooth_span) / smooth_span:10.2f}")
    print(f"{'area (mm2)':25s}{area_smooth:15.2f}{area_faceted:18.2f}"
          f"{100 * (area_faceted - area_smooth) / area_smooth:10.2f}")
    print(f"{'bbox larghezza (mm)':25s}{bbox_smooth[2]-bbox_smooth[0]:15.2f}"
          f"{bbox_faceted[2]-bbox_faceted[0]:18.2f}"
          f"{100 * ((bbox_faceted[2]-bbox_faceted[0]) - (bbox_smooth[2]-bbox_smooth[0])) / (bbox_smooth[2]-bbox_smooth[0]):10.2f}")
    print()
    print("Dettaglio sfaccettato:")
    print("  corda esterna     :", faceted.meta["outer_facet_width"])
    print("  corda interna     :", faceted.meta["inner_facet_width"])
    print("  angolo per faccetta:", faceted.meta["facet_angle_deg"])
    print("  raggio piega usato :", faceted.meta["facet_bend_radius"])
    print("  K-factor usato     :", faceted.meta["facet_k_factor"])
    print("  bend allowance/piega:", faceted.meta["facet_bend_allowance"])
    print()
    print("File generati in", OUTPUT_DIR.resolve())
    print("  confronto_cono_liscio.dxf")
    print("  confronto_cono_sfaccettato.dxf")


if __name__ == "__main__":
    main()
