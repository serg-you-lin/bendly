"""
06_external_quotes.py
-----------------------
Layer umano (Fase 3.1, MAP.md D28) — un carpentiere dà le quote
ESTERNO-ESTERNO del pezzo, come le leggerebbe su un disegno, non le quote a
MEZZERIA che vuole `BentProfile.flanges`. `external_flanges_to_centerline()`
traduce; il core (`BentProfile`) non cambia — vede sempre e solo mezzeria.

Genera una squadra a L 100x110 (quote esterne) a spessore 3mm, calibrazione
"default" (DIN 6935): niente raggio da dare a mano, lo decide la
calibrazione dalla cava, esattamente come nell'uso normale di BentProfile.

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from bendly import Bend, BentProfile
from bendly.rules.deduction import external_flanges_to_centerline, centerline_to_external_flange

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# --- CONFIG ---
EXTERNAL_FLANGES = [100.0, 110.0]   # quote esterno-esterno, come le dà un carpentiere
BEND_ANGLES = [90.0]                # un angolo per piega (convenzione Bend.angle, non l'incluso)
THICKNESS = 3.0
WIDTH = 50.0
CALIBRATION = "default"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    centerline_flanges = external_flanges_to_centerline(
        EXTERNAL_FLANGES, BEND_ANGLES, THICKNESS,
    )

    l_bracket = BentProfile(
        flanges=centerline_flanges,
        bends=[Bend(angle=a) for a in BEND_ANGLES],
        thickness=THICKNESS,
        width=WIDTH,
        calibration=CALIBRATION,
        label="L_100x110_esterno",
    ).develop()
    l_bracket.to_dxf(OUTPUT_DIR / "L_100x110_esterno.dxf")

    # andata e ritorno: riconvertendo la mezzeria si devono ritrovare le
    # quote esterne di partenza (stessa verifica del test automatico)
    ricostruite = [
        centerline_to_external_flange(
            length, THICKNESS,
            angle_before=BEND_ANGLES[i - 1] if i > 0 else None,
            angle_after=BEND_ANGLES[i] if i < len(BEND_ANGLES) else None,
        )
        for i, length in enumerate(centerline_flanges)
    ]

    print(f"Quote esterne date:          {EXTERNAL_FLANGES}")
    print(f"Quote a mezzeria calcolate:  {[round(f, 3) for f in centerline_flanges]}")
    print(f"Quote esterne ricostruite:   {[round(f, 3) for f in ricostruite]}")
    print(f"Lunghezza sviluppo:          {l_bracket.meta['total_length']:.3f}")
    for i, b in enumerate(l_bracket.bends):
        print(f"  piega {i}: accorciamento {b.deduction:.3f}, regola {b.rule} — {b.source}")
    print("File in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
