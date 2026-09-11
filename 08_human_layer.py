"""
08_human_layer.py
-------------------
Fase 3.2 (MAP.md D30) — l'API pubblica del layer umano:
`develop_from_external_flanges()`. Stessa L 100x110s3 di
`06_external_quotes.py`/`07_compare_calibrations_external.py`, ma qui non
si vede la conversione a mezzeria: si danno le quote esterne e i `Bend`,
esce direttamente il `FlatGeometry`.

Richiede forge installato a fianco per il DXF: pip install -e ../dxf-forge
"""

from pathlib import Path

from bendly import Bend, develop_from_external_flanges

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# --- CONFIG ---
EXTERNAL_FLANGES = [100.0, 110.0]   # quote esterno-esterno
BENDS = [Bend(angle=90.0)]          # cava non data -> la decide la calibrazione
THICKNESS = 3.0
WIDTH = 50.0
CALIBRATION = "tipo_misurato"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    flat = develop_from_external_flanges(
        EXTERNAL_FLANGES, BENDS, thickness=THICKNESS, width=WIDTH,
        calibration=CALIBRATION, label="L_100x110s3_human_layer",
    )
    flat.to_dxf(OUTPUT_DIR / "L_100x110s3_human_layer.dxf")

    print(f"Quote esterne: {EXTERNAL_FLANGES}  (calibrazione {CALIBRATION!r})")
    print(f"Lunghezza sviluppo: {flat.meta['total_length']:.3f}")
    for b in flat.bends:
        print(f"  piega: accorciamento {b.deduction:.3f}, regola {b.rule} — {b.source}")
    print("File in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
