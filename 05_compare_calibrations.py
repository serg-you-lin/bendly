"""
05_compare_calibrations.py
---------------------------
Per ogni pezzo di test in data_4_cloude/ stampa, fianco a fianco:
  - la lunghezza dello sviluppo REALE (DXF prodotto da TruBend)
  - quella della calibrazione "default"     (DIN 6935 + cava da tabella)
  - quella della calibrazione "tipo_misurato" (valori misurati dai .bnc)

Il calcolo passa TUTTO da un punto solo: BentProfile(...).develop() con
calibration= . Nessuna matematica in questo script.
"""

import glob
import os
import re
from pathlib import Path

import ezdxf
from ezdxf import bbox

from bendly import Bend, BentProfile, Calibration

# --- CONFIG ---
# i DXF reali di officina 1 (non versionati, vedi .gitignore). Il path è
# ancorato alla radice del repo, così lo script gira anche da un'altra CWD.
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data_4_cloude"

FORME = {
    "L": [114.0, 114.0],
    "U": [60.0, 110.0, 60.0],
    "Z": [60.0, 100.0, 50.0],
    "O": [40.0, 40.0, 60.0, 30.0, 70.0],
}
CAVA = {"EV1": 6, "EV2": 8, "EV5": 16, "EW50": 50, "EW60": 60, "EV60": 60}


def golden_len(path: str) -> float:
    b = bbox.extents(ezdxf.readfile(path).modelspace())
    return max(b.size.x, b.size.y)


def parse_nome(fname: str):
    base = os.path.splitext(os.path.basename(fname))[0]
    forma = base[0]
    spess = float(re.search(r"s(\d+)-", base).group(1))
    suff = base.split("-")[-1]
    cava = next((v for k, v in CAVA.items() if k == suff), None)
    return forma, spess, cava


def sviluppo(calibration, forma, spess, cava) -> float:
    segmenti = FORME[forma]
    bends = [Bend(angle=90, cava=cava) for _ in range(len(segmenti) - 1)]
    flat = BentProfile(flanges=segmenti, bends=bends, thickness=spess,
                       width=50, calibration=calibration).develop()
    return flat.meta["total_length"]


def main() -> None:
    default = Calibration.load("default")
    misurato = Calibration.load("tipo_misurato")

    print(f"{'file':44} {'sp':>3} {'cava':>4} "
          f"{'REALE':>9} {'default':>9} {'Δ':>7}  {'tipo_misurato':>13} {'Δ':>7}")
    print("-" * 100)
    for path in sorted(glob.glob(str(DATA_DIR / "[LUZO]" / "*.dxf"))):
        forma, spess, cava = parse_nome(path)
        if forma not in FORME:
            continue
        reale = golden_len(path)
        d = sviluppo(default, forma, spess, cava)
        m = sviluppo(misurato, forma, spess, cava)
        print(f"{os.path.basename(path):44} {spess:3.0f} {str(cava):>4} "
              f"{reale:9.2f} {d:9.2f} {d - reale:+7.2f}  {m:13.2f} {m - reale:+7.2f}")


if __name__ == "__main__":
    main()
