"""
Fase 3.2 (layer umano) — `develop_from_external_flanges()` deve dare
ESATTAMENTE lo stesso risultato del giro manuale già verificato in
`test_deduction.py::TestExternalToCenterlineFlange` (converti con
`external_flanges_to_centerline()`, poi `BentProfile.develop()`): è solo
un involucro comodo, non un calcolo nuovo.
"""

import unittest

from unfold import Bend, BentProfile, develop_from_external_flanges
from unfold.rules.deduction import external_flanges_to_centerline


class TestDevelopFromExternalFlanges(unittest.TestCase):

    def test_uguale_al_giro_a_mano_con_raggio_esplicito(self):
        # via accademica: raggio esplicito (MAP.md D33). Il wrapper deve dare
        # lo stesso numero del giro fatto a mano.
        external_flanges = [100.0, 110.0]
        bends = [Bend(angle=90.0, radius=2.0)]
        thickness = 3.0

        atteso = BentProfile(
            flanges=external_flanges_to_centerline(external_flanges, [90.0], thickness),
            bends=[Bend(angle=90.0, radius=2.0)],
            thickness=thickness, width=50, calibration="din6935",
        ).develop()

        flat = develop_from_external_flanges(
            external_flanges, bends, thickness=thickness, width=50,
            calibration="din6935",
        )
        self.assertAlmostEqual(flat.meta["total_length"], atteso.meta["total_length"], places=9)

    def test_uguale_al_giro_manuale_modo_calibrazione(self):
        # stessa L 100x110s3 degli script 06/07 — calibrazione tipo_misurato
        external_flanges = [100.0, 110.0]
        bend_angles = [90.0]
        thickness = 3.0

        atteso = BentProfile(
            flanges=external_flanges_to_centerline(external_flanges, bend_angles, thickness),
            bends=[Bend(angle=a) for a in bend_angles],
            thickness=thickness, width=50, calibration="tipo_misurato",
        ).develop()

        flat = develop_from_external_flanges(
            external_flanges, [Bend(angle=a) for a in bend_angles],
            thickness=thickness, width=50, calibration="tipo_misurato",
        )
        self.assertAlmostEqual(flat.meta["total_length"], atteso.meta["total_length"], places=9)
        self.assertEqual(flat.bends[0].rule, "misurato")

    def test_e_in_unfold_all(self):
        import unfold
        self.assertIn("develop_from_external_flanges", unfold.__all__)


if __name__ == "__main__":
    unittest.main()
