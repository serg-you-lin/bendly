"""
09_section_view.py
--------------------
Fase 3.3/3.4 (MAP.md D31): vista in sezione del pezzo PIEGATO (non
sviluppato), con una quota per flangia — esterna dove la flangia ha una
faccia esterna coerente, a mezzeria con nota esplicita altrimenti (MAP.md
D1: capita solo sull'anima di una Z/omega, fra due pieghe di verso
opposto).

Due esempi:
  - la L 100x110s3 di 06/07/08: entrambe le flange hanno una faccia
    esterna coerente (un'unica piega), quote tutte "esterno";
  - una Z: la flangia centrale (fra due pieghe di verso opposto) non ha
    faccia coerente, la sua quota esce "a mezzeria" col testo che lo dice.

Richiede forge installato a fianco: pip install -e ../dxf-forge
"""

from pathlib import Path

from unfold import Section

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def show(section: Section, label: str) -> None:
    print(f"\n{label} — {section.name()}")
    for q in section.flange_quotes():
        faccia = f" (faccia {q.face})" if q.face else ""
        print(f"  flangia {q.index}: {q.display_length:.3f}  [{q.display_kind}]{faccia}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- L 100x110s3, quote esterne, un'unica piega: nessuna ambiguità ---
    l_section = Section.from_external_flanges(
        "L", external_flanges=[100.0, 110.0], angles=[90.0], thickness=3.0,
    )
    show(l_section, "L 100x110s3")
    l_section.to_dxf(OUTPUT_DIR / "09_section_L.dxf")

    # --- Z, quote esterne, due pieghe di verso opposto: anima ambigua ---
    z_section = Section.from_external_flanges(
        "Z", external_flanges=[80.0, 40.0, 80.0], angles=[90.0, 270.0], thickness=3.0,
    )
    show(z_section, "Z 80x40x80s3")
    z_section.to_dxf(OUTPUT_DIR / "09_section_Z.dxf")

    print("\nFile in", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
