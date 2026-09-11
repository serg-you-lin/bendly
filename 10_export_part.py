"""
10_export_part.py
-------------------
Fase 3 (MAP.md D32): `export_part()` — un unico file DXF a livelli
impilati in verticale: taglio (sempre) + vista in sezione quotata
(opzionale) + header (opzionale), mai affiancati, allineati a sinistra.

Stessa L 100x110s3 di 06/07/08/09, calibrazione tipo_misurato. Due file:
solo il taglio, e il combo completo (taglio + sezione + header) da aprire
e guardare per vedere lo stacking.

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from unfold import Section, export_part

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    section = Section.from_external_flanges(
        "L", external_flanges=[100.0, 110.0], angles=[90.0], thickness=3.0,
    )

    export_part(section, width=50.0, path=OUTPUT_DIR / "10_export_cut_only.dxf",
                calibration="tipo_misurato")

    export_part(section, width=50.0, path=OUTPUT_DIR / "10_export_full.dxf",
                calibration="tipo_misurato", include_section=True, include_header=True)

    print("File in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
