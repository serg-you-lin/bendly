"""
test_export_part.py
---------------------
Fase 3 (MAP.md D32): `export_part()` — export a livelli impilati in
verticale (taglio + vista in sezione opzionale + header opzionale), mai
affiancati, allineati a sinistra.
"""

import tempfile
import unittest
from pathlib import Path

try:
    import forge  # noqa: F401
    FORGE_AVAILABLE = True
except ImportError:
    FORGE_AVAILABLE = False

from unfold import Section, export_part


@unittest.skipUnless(FORGE_AVAILABLE, "forge non installato — pip install -e ../dxf-forge")
class TestExportPart(unittest.TestCase):

    def _section(self) -> Section:
        return Section.default("L", [50.0, 60.0], [90.0], thickness=2.0)

    def test_e_in_unfold_all(self):
        import unfold
        self.assertIn("export_part", unfold.__all__)

    def test_le_quattro_combinazioni_scrivono_file(self):
        section = self._section()
        with tempfile.TemporaryDirectory() as tmp:
            for include_section in (False, True):
                for include_header in (False, True):
                    out = Path(tmp) / f"part_{include_section}_{include_header}.dxf"
                    export_part(section, width=80.0, path=out, calibration="default",
                                include_section=include_section, include_header=include_header)
                    self.assertTrue(out.exists())

    def test_impilamento_verticale_senza_sovrapposizioni_allineato_a_sinistra(self):
        import ezdxf
        import ezdxf.bbox as ezbbox

        section = self._section()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "part.dxf"
            export_part(section, width=80.0, path=out, calibration="default",
                        include_section=True, include_header=True, margin=20.0)

            doc = ezdxf.readfile(out)
            msp = doc.modelspace()

            def layer_bbox(*, exclude=None, only=None):
                entities = [
                    e for e in msp
                    if (only is None or e.dxf.layer in only)
                    and (exclude is None or e.dxf.layer not in exclude)
                ]
                box = ezbbox.extents(entities)
                return box.extmin, box.extmax

            cut_min, cut_max = layer_bbox(exclude={"SectionView", "Notes", "Quotes"})
            sec_min, sec_max = layer_bbox(only={"SectionView"})
            notes_min, notes_max = layer_bbox(only={"Notes"})

            # ordine verticale taglio -> sezione -> header, senza sovrapposizioni
            self.assertLess(sec_max.y, cut_min.y)
            self.assertLess(notes_max.y, sec_min.y)

            # allineati a sinistra sullo stesso x0 del taglio
            self.assertAlmostEqual(sec_min.x, cut_min.x, places=3)
            self.assertAlmostEqual(notes_min.x, cut_min.x, places=3)

    def test_senza_sezione_lo_header_si_piazza_sotto_al_taglio(self):
        import ezdxf
        import ezdxf.bbox as ezbbox

        section = self._section()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "part.dxf"
            export_part(section, width=80.0, path=out, calibration="default",
                        include_section=False, include_header=True)

            doc = ezdxf.readfile(out)
            msp = doc.modelspace()

            cut_entities = [e for e in msp if e.dxf.layer not in ("SectionView", "Notes", "Quotes")]
            notes_entities = [e for e in msp if e.dxf.layer == "Notes"]
            self.assertGreater(len(notes_entities), 0)

            cut_box = ezbbox.extents(cut_entities)
            notes_box = ezbbox.extents(notes_entities)
            self.assertLess(notes_box.extmax.y, cut_box.extmin.y)
            self.assertAlmostEqual(notes_box.extmin.x, cut_box.extmin.x, places=3)


if __name__ == "__main__":
    unittest.main()
