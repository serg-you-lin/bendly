import math
import os
import unittest

from unfold import Bend, BentProfile, Calibration, estimate_k_factor, MATERIAL_K_FACTORS


class TestBendFormulas(unittest.TestCase):

    def test_bend_allowance_matches_manual_formula(self):
        bend = Bend(angle=90, radius=3)
        ba = bend.bend_allowance(thickness=2, k_factor=0.44)
        expected = math.radians(90) * (3 + 0.44 * 2)
        self.assertAlmostEqual(ba, expected, places=9)

    def test_outside_setback_matches_manual_formula(self):
        bend = Bend(angle=90, radius=3)
        oss = bend.outside_setback(thickness=2)
        expected = (3 + 2) * math.tan(math.radians(90) / 2.0)
        self.assertAlmostEqual(oss, expected, places=9)

    def test_inside_setback_matches_manual_formula(self):
        bend = Bend(angle=90, radius=3)
        iss = bend.inside_setback(thickness=2)
        expected = 3 * math.tan(math.radians(90) / 2.0)
        self.assertAlmostEqual(iss, expected, places=9)

    def test_centerline_setback_matches_manual_formula(self):
        bend = Bend(angle=90, radius=3)
        css = bend.centerline_setback(thickness=2)
        expected = (3 + 1) * math.tan(math.radians(90) / 2.0)
        self.assertAlmostEqual(css, expected, places=9)

    def test_centerline_setback_is_average_of_outside_and_inside(self):
        bend = Bend(angle=63, radius=4.5)
        css = bend.centerline_setback(thickness=3)
        oss = bend.outside_setback(thickness=3)
        iss = bend.inside_setback(thickness=3)
        self.assertAlmostEqual(css, (oss + iss) / 2.0, places=9)


class TestBendFromIncluded(unittest.TestCase):
    """MAP.md D49 — Bend.from_included(), costruttore dall'angolo incluso
    (quello che si legge su un disegno tecnico)."""

    def test_ninety_degrees_coincides_by_numeric_coincidence(self):
        # 180-90=90: coincidono SOLO per la squadra, non in generale (vedi
        # test sotto) — non e' la regola, e' un caso particolare.
        b = Bend.from_included(90, radius=3)
        self.assertAlmostEqual(b.angle, 90.0)

    def test_wider_included_angle_gives_smaller_rotation(self):
        # Una piega piu' aperta (120 incluso, meno piegata di una squadra)
        # ruota MENO da piatto, non di piu' — esattamente il punto dove chi
        # legge un disegno tecnico sbaglierebbe passando 120 diretto a
        # Bend(angle=...).
        b = Bend.from_included(120, radius=3)
        self.assertAlmostEqual(b.angle, 60.0)

    def test_narrower_included_angle_gives_larger_rotation(self):
        b = Bend.from_included(60, radius=3)
        self.assertAlmostEqual(b.angle, 120.0)

    def test_matches_manual_conversion(self):
        for included in (30, 45, 75, 100, 150):
            b = Bend.from_included(included, radius=2, k_factor=0.4, cava=16)
            self.assertAlmostEqual(b.angle, 180.0 - included)
            self.assertEqual(b.radius, 2)
            self.assertEqual(b.k_factor, 0.4)
            self.assertEqual(b.cava, 16)

    def test_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            Bend.from_included(0)
        with self.assertRaises(ValueError):
            Bend.from_included(180)
        with self.assertRaises(ValueError):
            Bend.from_included(-10)
        with self.assertRaises(ValueError):
            Bend.from_included(200)

    def test_develops_the_same_as_manual_angle_in_a_bentprofile(self):
        # Giro chiuso: from_included(120) dentro un BentProfile vero deve
        # sviluppare esattamente come Bend(angle=60) a mano.
        via_included = BentProfile(
            flanges=[50, 50], bends=[Bend.from_included(120, radius=3)],
            thickness=2, width=100, calibration="default",
        ).develop()
        via_manual = BentProfile(
            flanges=[50, 50], bends=[Bend(angle=60, radius=3)],
            thickness=2, width=100, calibration="default",
        ).develop()
        self.assertAlmostEqual(via_included.meta["total_length"], via_manual.meta["total_length"])

    def test_estimate_k_factor_standard_ratio_uses_material_table(self):
        # R/T ~ 1 (standard) -> valore di tabella per il materiale
        self.assertAlmostEqual(estimate_k_factor("mild_steel", radius=2, thickness=2), 0.44)
        self.assertAlmostEqual(estimate_k_factor("stainless_steel", radius=2, thickness=2), 0.39)
        self.assertAlmostEqual(estimate_k_factor("aluminum", radius=2, thickness=2), 0.41)

    def test_estimate_k_factor_tight_and_wide_radius(self):
        self.assertAlmostEqual(estimate_k_factor("mild_steel", radius=0.5, thickness=2), 0.31)
        self.assertAlmostEqual(estimate_k_factor("mild_steel", radius=10, thickness=2), 0.50)


class TestBentProfileSingleBend(unittest.TestCase):
    """
    Caso semplice: 2 flange, 1 piega — lo sviluppo è Σ flange − accorciamento,
    con l'accorciamento deciso dalla calibrazione (MAP.md D33).
    """

    def setUp(self):
        self.thickness = 2.0
        self.cava = 16.0
        self.cal = Calibration.load("default")
        self.flat = BentProfile(
            flanges=[50.0, 80.0], bends=[Bend(angle=90, cava=self.cava)],
            thickness=self.thickness, width=300, calibration=self.cal,
        ).develop()

    def test_total_length_is_sum_of_flanges_minus_deduction(self):
        cd = self.cal.centerline_deduction(self.thickness, 90, cava=self.cava)
        self.assertAlmostEqual(self.flat.meta["total_length"], 50.0 + 80.0 - cd, places=6)

    def test_outer_rectangle_matches_total_length(self):
        outer = self.flat.entities[0]
        xs = [p[0] for p in outer["points"]]
        self.assertAlmostEqual(max(xs) - min(xs), self.flat.meta["total_length"], places=6)

    def test_one_bending_line_between_the_two_flanges(self):
        bend_lines = [e for e in self.flat.entities if e.get("role") == "bending"]
        self.assertEqual(len(bend_lines), 1)
        x = bend_lines[0]["start"][0]
        self.assertGreater(x, 0.0)
        self.assertLess(x, self.flat.meta["total_length"])


class TestBentProfileMultiBend(unittest.TestCase):
    """3 flange, 2 pieghe — verifica che la catena si sommi correttamente."""

    def test_three_flanges_two_bends(self):
        cal = Calibration.load("default")
        flat = BentProfile(
            flanges=[50.0, 80.0, 50.0],
            bends=[Bend(angle=90, cava=12), Bend(angle=90, cava=12)],
            thickness=2.0, width=200, calibration=cal,
        ).develop()

        cd = cal.centerline_deduction(2.0, 90, cava=12)
        expected_total = 50.0 + 80.0 + 50.0 - 2 * cd

        self.assertAlmostEqual(flat.meta["total_length"], expected_total, places=6)
        bend_lines = [e for e in flat.entities if e.get("role") == "bending"]
        self.assertEqual(len(bend_lines), 2)
        positions = sorted(e["start"][0] for e in bend_lines)
        self.assertLess(positions[0], positions[1])


class TestBendResult(unittest.TestCase):
    """`develop()` popola `flat.bends` con una BendResult per piega, che dice
    da dove viene l'accorciamento (D5 / skill interrogabilità)."""

    def test_default_reports_din6935_from_cava(self):
        flat = BentProfile(
            flanges=[50, 80], bends=[Bend(angle=90, cava=16)],
            thickness=2, width=200, calibration="default",
        ).develop()
        self.assertEqual(len(flat.bends), 1)
        b = flat.bends[0]
        self.assertEqual(b.rule, "din6935")
        self.assertFalse(b.fallback)
        self.assertIn("da cava 16", b.source)
        self.assertIsNotNone(b.k_factor)

    def test_k_per_materiale_calibration(self):
        cal = Calibration({"nome": "prova", "cava_per_spessore": {"2": 16},
                           "k_per_materiale": {"inox": 0.38}})
        flat = BentProfile(
            flanges=[50, 80], bends=[Bend(angle=90)],
            thickness=2, width=200, calibration=cal, material="inox",
        ).develop()
        b = flat.bends[0]
        self.assertEqual(b.rule, "k_materiale")
        self.assertEqual(b.k_factor, 0.38)

    def test_explicit_radius_coexists_with_calibration(self):
        # MAP.md D33: raggio esplicito + calibrazione convivono; il raggio
        # va nella formula al posto della cava, la provenienza lo dice.
        flat = BentProfile(
            flanges=[50, 80], bends=[Bend(angle=90, radius=3)],
            thickness=2, width=200, calibration="din6935",
        ).develop()
        b = flat.bends[0]
        self.assertEqual(b.rule, "din6935")
        self.assertIn("raggio 3 esplicito", b.source)

    @unittest.skipUnless(
        os.path.isfile(os.path.join("calibrations", "tipo_misurato.json")),
        "calibrazione tipo_misurato non presente",
    )
    def test_profilo_reports_misurato_vs_fallback(self):
        cal = Calibration.load("tipo_misurato")
        flat = BentProfile(
            flanges=[60, 100, 60],
            bends=[Bend(angle=90, cava=16), Bend(angle=90, cava=40)],
            thickness=3, width=50, calibration=cal,
        ).develop()

        got = flat.bends[0]                      # 3 mm / V16 -> misurato (L3.bnc)
        self.assertEqual(got.rule, "misurato")
        self.assertFalse(got.fallback)
        self.assertIn(".bnc", got.source)

        fell_back = flat.bends[1]                # 3 mm / V40 -> nessun misurato per questa combinazione
        self.assertEqual(fell_back.rule, "din6935")
        self.assertTrue(fell_back.fallback)
        self.assertIn("DIN 6935", fell_back.source)


class TestBentProfileValidation(unittest.TestCase):

    def test_mismatched_bends_count_raises(self):
        with self.assertRaises(ValueError):
            BentProfile(
                flanges=[50, 80, 50], bends=[Bend(90, 2)],
                thickness=2, width=200,
            ).develop()

    def test_too_few_flanges_raises(self):
        with self.assertRaises(ValueError):
            BentProfile(flanges=[50], bends=[], thickness=2, width=200).develop()

    def test_non_positive_flange_raises(self):
        with self.assertRaises(ValueError):
            BentProfile(
                flanges=[0, 80], bends=[Bend(90, 2)], thickness=2, width=200,
            ).develop()

    def test_flange_too_short_for_setback_raises(self):
        with self.assertRaises(ValueError):
            BentProfile(
                flanges=[1, 80], bends=[Bend(90, radius=50)], thickness=2, width=200,
            ).develop()

    def test_bend_angle_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            BentProfile(
                flanges=[50, 80], bends=[Bend(angle=180, radius=2)],
                thickness=2, width=200,
            ).develop()

    def test_defaults_to_default_calibration(self):
        # Nessuna calibrazione data -> "default": .develop() funziona senza
        # configurare niente (MAP.md D33). "default" non indovina nessuna
        # cava (tutta a null, MAP.md D36): raggio fisso dichiarato, mai una
        # stima scalata dallo spessore.
        flat = BentProfile(
            flanges=[50, 80], bends=[Bend(angle=90)],
            thickness=2, width=200,
        ).develop()
        b = flat.bends[0]
        self.assertEqual(b.rule, "din6935")     # default = stima DIN dal r/s
        self.assertIn("raggio 1", b.source)
        self.assertIn("nessuna cava nota", b.source)


if __name__ == "__main__":
    unittest.main()
