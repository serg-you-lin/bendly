"""
07_compare_calibrations_external.py
-------------------------------------
La STESSA L 100x110 (quote ESTERNE, spessore 3mm) sviluppata con tre
calibrazioni diverse: `tipo_misurato` (misurati, dal .bnc reale), `default`
(DIN 6935), `inside_sum` (somma quote interne, raggio 0 — prassi da
vecchia scuola, MAP.md D3).

La conversione esterno -> mezzeria (D28, `06_external_quotes.py`) è la
STESSA per `tipo_misurato` e `default`: è pura geometria, non dipende da come
la calibrazione calcola l'accorciamento. `inside_sum` è a parte (MAP.md
D35): lavora in quote INTERNE, quindi qui si convertono le quote esterne
in interne e si sommano — niente passaggio per la mezzeria.

Richiede forge installato a fianco per il DXF: pip install -e ../dxf-forge
"""

from pathlib import Path

from unfold import Bend, BentProfile
from unfold.rules.deduction import (
    external_flanges_to_centerline,
    external_to_centerline_flange,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# --- CONFIG ---
EXTERNAL_FLANGES = [100.0, 110.0]   # quote esterno-esterno
BEND_ANGLES = [90.0]
THICKNESS = 3.0
WIDTH = 50.0
CALIBRATIONS = ["tipo_misurato", "default", "inside_sum"]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # tipo_misurato / default lavorano a mezzeria; inside_sum in quote interne
    centerline_flanges = external_flanges_to_centerline(
        EXTERNAL_FLANGES, BEND_ANGLES, THICKNESS,
    )
    # interne = mezzeria - (s/2)·tan(β/2) per piega adiacente: una seconda
    # applicazione dello stesso offset geometrico
    inside_flanges = external_flanges_to_centerline(
        centerline_flanges, BEND_ANGLES, THICKNESS,
    )
    print(f"L {EXTERNAL_FLANGES[0]:g}x{EXTERNAL_FLANGES[1]:g}s{THICKNESS:g} — quote esterne")
    print(f"Quote a mezzeria (tipo_misurato / default): "
          f"{[round(f, 3) for f in centerline_flanges]}")
    print(f"Quote interne (inside_sum): {[round(f, 3) for f in inside_flanges]}")
    print()

    for name in CALIBRATIONS:
        flat = BentProfile(
            flanges=inside_flanges if name == "inside_sum" else centerline_flanges,
            bends=[Bend(angle=a) for a in BEND_ANGLES],
            thickness=THICKNESS,
            width=WIDTH,
            calibration=name,
            label=f"L_100x110s3_{name}",
        ).develop()
        flat.to_dxf(OUTPUT_DIR / f"L_100x110s3_{name}.dxf")

        print(f"{name}:")
        print(f"  lunghezza sviluppo: {flat.meta['total_length']:.3f}")
        for b in flat.bends:
            nota = " (fallback su DIN, nessun dato misurato)" if b.fallback else ""
            print(f"  piega: accorciamento {b.deduction:.3f}, regola {b.rule}{nota} — {b.source}")
        print()

    print("File in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
