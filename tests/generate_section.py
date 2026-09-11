"""
tests/generate_section.py
---------------------------
Generate the golden-set sections (L / U / Z / O) into data_4_cloude/sections/.

One section per shape x thickness (1, 3, 10), with a fixed 1 mm inner
radius. The radius does NOT enter the flat-length calculation: it only
serves the recognition pattern "this is bent sheet metal". Geometrically
impossible combinations (a segment shorter than its neighbouring radii)
are skipped and reported.

Each section is written in two formats:
  - .dxf  : via forge (to look at it / feed the drawing interpreter)
  - .json : neutral entities + parameters (for tests, via
            forge.load_geometry, without going through a DXF file)

Usage:
    python tests/generate_section.py
"""

from __future__ import annotations

import json
from pathlib import Path

from unfold.model.section import Section

# same centerline segments and angles as the real TruBend DXF in
# data_4_cloude/<SHAPE>/ and as the FORME dict in
# tests/test_golden_officina.py
SHAPES = {
    "L": ([114.0, 114.0], [90.0]),
    "U": ([60.0, 110.0, 60.0], [90.0, 90.0]),
    "Z": ([60.0, 100.0, 50.0], [90.0, 270.0]),
    "O": ([40.0, 40.0, 60.0, 30.0, 70.0], [90.0, 270.0, 270.0, 90.0]),
}
THICKNESSES = [1.0, 3.0, 10.0]
OUT = Path("data_4_cloude/sections")


def _round(entities):
    def r(v):
        if isinstance(v, (list, tuple)):
            return [r(x) for x in v]
        if isinstance(v, float):
            return round(v, 4)
        return v
    return [{k: r(val) for k, val in e.items()} for e in entities]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    written, skipped = 0, 0
    for shape, (segments, angles) in SHAPES.items():
        for thickness in THICKNESSES:
            s = Section.default(shape, segments, angles, thickness)
            try:
                flat = s.section()
            except ValueError as exc:
                print(f"  skip {s.name()}: {exc}")
                skipped += 1
                continue

            payload = {**flat.meta, "name": s.name(),
                       "entities": _round(flat.entities)}
            (OUT / f"{s.name()}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            try:
                flat.to_dxf(str(OUT / f"{s.name()}.dxf"), annotate=False)
            except Exception as exc:  # forge missing, or heal failed
                print(f"  {s.name()}: JSON ok, DXF no ({exc})")

            print(f"  {s.name()}  (inner radius {s.inner_radius:g})")
            written += 1

    print(f"\n{written} sections written to {OUT}/  ({skipped} skipped)")


if __name__ == "__main__":
    main()
