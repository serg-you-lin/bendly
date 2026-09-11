"""
test_section.py
-----------------
Fase 3.3/3.4 (MAP.md D31): `Section.from_external_flanges()`,
`flange_faces()` e `flange_quotes()` — la vista in sezione col riconoscimento
della faccia esterna coerente (MAP.md D1).
"""

import math
import unittest

try:
    import forge  # noqa: F401
    FORGE_AVAILABLE = True
except ImportError:
    FORGE_AVAILABLE = False

from unfold import Section
from unfold.rules.deduction import external_flanges_to_centerline


class TestFromExternalFlanges(unittest.TestCase):

    def test_uguale_al_giro_manuale(self):
        external = [100.0, 110.0]
        angles = [90.0]
        thickness = 3.0

        section = Section.from_external_flanges("L", external, angles, thickness)

        self.assertEqual(
            section.segments,
            external_flanges_to_centerline(external, [90.0], thickness),
        )
        self.assertEqual(section.angles, angles)


class TestFlangeFaces(unittest.TestCase):
    """MAP.md D1: una flangia ha una faccia esterna coerente solo se le due
    pieghe adiacenti girano nello stesso verso."""

    def test_L_entrambe_le_flange_hanno_una_faccia(self):
        section = Section.default("L", segments=[50.0, 60.0], angles=[90.0], thickness=2.0)
        faces = section.flange_faces()
        self.assertEqual(len(faces), 2)
        self.assertIsNotNone(faces[0].face)
        self.assertIsNotNone(faces[1].face)

    def test_U_tutte_e_tre_le_flange_hanno_una_faccia(self):
        # stesso verso su entrambe le pieghe (90/90): base + due sponde.
        section = Section.default("U", segments=[40.0, 60.0, 40.0],
                                  angles=[90.0, 90.0], thickness=2.0)
        for ff in section.flange_faces():
            self.assertIsNotNone(ff.face, f"flangia {ff.index} dovrebbe avere una faccia")

    def test_Z_la_flangia_centrale_e_ambigua(self):
        # versi opposti (90/270): l'anima della Z non ha faccia coerente.
        section = Section.default("Z", segments=[40.0, 60.0, 40.0],
                                  angles=[90.0, 270.0], thickness=2.0)
        faces = section.flange_faces()
        self.assertIsNotNone(faces[0].face)
        self.assertIsNone(faces[1].face, "l'anima della Z non ha una faccia esterna coerente")
        self.assertIsNotNone(faces[2].face)


class TestFlangeQuotes(unittest.TestCase):

    def test_lunghezza_geometrica_torna_uguale_alla_quota_mostrata(self):
        """Verifica indipendente (regola del gioco): la distanza fra i due
        punti estesi all'apice virtuale deve tornare uguale a
        `display_length`, calcolata invece per via algebrica
        (`centerline_to_external_flange`/D28) — stesso numero, due strade."""
        for shape, segments, angles in [
            ("L", [50.0, 60.0], [90.0]),
            ("U", [40.0, 60.0, 40.0], [90.0, 90.0]),
            ("Z", [40.0, 60.0, 40.0], [90.0, 270.0]),
        ]:
            for thickness in (1.0, 3.0, 10.0):
                with self.subTest(shape=shape, thickness=thickness):
                    section = Section.default(shape, segments, angles, thickness)
                    for q in section.flange_quotes():
                        geo_length = math.hypot(q.p1[0] - q.p0[0], q.p1[1] - q.p0[1])
                        self.assertAlmostEqual(geo_length, q.display_length, places=9)

    def test_quota_esterna_torna_uguale_alla_quota_data_in_ingresso(self):
        """Round trip: da una Section costruita con quote esterne, le
        quote lette da `flange_quotes()` sulle flange con faccia coerente
        tornano uguali a quelle date in ingresso."""
        external = [40.0, 60.0, 40.0]
        angles = [90.0, 90.0]   # U: tutte e tre le flange hanno una faccia
        section = Section.from_external_flanges("U", external, angles, thickness=2.0)

        quotes = section.flange_quotes()
        for given, q in zip(external, quotes):
            self.assertEqual(q.display_kind, "esterno")
            self.assertAlmostEqual(q.display_length, given, places=9)

    def test_flangia_ambigua_e_dichiarata_a_mezzeria(self):
        section = Section.default("Z", [40.0, 60.0, 40.0], [90.0, 270.0], thickness=3.0)
        quotes = section.flange_quotes()
        self.assertEqual(quotes[1].display_kind, "mezzeria")
        self.assertIsNone(quotes[1].face)
        self.assertAlmostEqual(quotes[1].display_length, 60.0, places=9)

    def test_e_in_unfold_all(self):
        import unfold
        self.assertIn("FlangeFace", unfold.__all__)
        self.assertIn("FlangeQuote", unfold.__all__)


@unittest.skipUnless(FORGE_AVAILABLE, "forge non installato — pip install -e ../dxf-forge")
class TestSectionToDxf(unittest.TestCase):

    def test_scrive_un_file_con_le_quote(self):
        import tempfile
        from pathlib import Path

        section = Section.default("L", [50.0, 60.0], [90.0], thickness=2.0)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "section.dxf"
            section.to_dxf(out)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
