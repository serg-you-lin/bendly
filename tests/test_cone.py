import math
import unittest

from bendly import Cone


class TestConeMath(unittest.TestCase):
    """
    Verifica la matematica dello sviluppo contro calcoli indipendenti — non
    contro forge (develop() non ne ha bisogno).
    """

    def test_sector_angle_and_radii(self):
        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
        ).develop()
        m = flat.meta

        top_mean, bottom_mean = 198.0, 148.0
        big_r, small_r = top_mean / 2.0, bottom_mean / 2.0
        delta_r = big_r - small_r
        slant = math.hypot(100, delta_r)
        outer_radius = slant * big_r / delta_r
        angle = 360.0 * big_r / outer_radius

        self.assertAlmostEqual(m["slant_height"], slant, places=6)
        self.assertAlmostEqual(m["outer_radius"], outer_radius, places=6)
        self.assertAlmostEqual(m["sector_angle_deg"], angle, places=6)

    def test_entities_form_a_closed_loop(self):
        flat = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2).develop()
        self.assertEqual(len(flat.entities), 4)
        kinds = [e["type"] for e in flat.entities]
        self.assertEqual(kinds, ["arc", "line", "arc", "line"])

    def test_equal_diameters_raises(self):
        with self.assertRaises(ValueError):
            Cone(top_diameter=100, bottom_diameter=100, height=50).develop()

    def test_thickness_too_large_raises(self):
        with self.assertRaises(ValueError):
            Cone(top_diameter=10, bottom_diameter=20, height=50, thickness=15).develop()

    def test_non_positive_dimension_raises(self):
        with self.assertRaises(ValueError):
            Cone(top_diameter=0, bottom_diameter=100, height=50).develop()

    def test_default_orientation_is_vertical_transformed(self):
        # orientation="vertical" (default): il settore canonico (bisettrice
        # su +X) viene ruotato — l'angolo iniziale dell'arco esterno non
        # coincide più con quello canonico -angle/2.
        flat = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2).develop()
        angle = flat.meta["sector_angle_deg"]
        self.assertNotAlmostEqual(flat.entities[0]["start_angle"], -angle / 2.0)

    def test_horizontal_orientation_is_canonical_no_transform(self):
        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            orientation="horizontal",
        ).develop()
        angle = flat.meta["sector_angle_deg"]
        outer_arc = flat.entities[0]
        self.assertAlmostEqual(outer_arc["center"][0], 0.0)
        self.assertAlmostEqual(outer_arc["start_angle"], -angle / 2.0)

    def test_invalid_orientation_raises(self):
        with self.assertRaises(ValueError):
            Cone(top_diameter=200, bottom_diameter=150, height=100, orientation="up").develop()

    def test_margin_reduces_sector_angle(self):
        no_margin = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2).develop()
        with_margin = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2, margin=10,
        ).develop()
        self.assertLess(with_margin.meta["sector_angle_deg"], no_margin.meta["sector_angle_deg"])

    def test_margin_produces_full_untrimmed_sector_outline(self):
        # Il riferimento è il contorno PIENO del settore (arco+linea+arco+
        # linea, come quello tagliato) non due linee sciolte — così si
        # richiude/collega intorno alla geometria di taglio reale.
        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2, margin=10,
        ).develop()
        self.assertEqual(len(flat.reference_entities), 4)
        self.assertEqual(
            [e["type"] for e in flat.reference_entities], ["arc", "line", "arc", "line"]
        )
        self.assertAlmostEqual(flat.reference_entities[0]["radius"], flat.meta["outer_radius"], places=6)
        self.assertAlmostEqual(flat.reference_entities[2]["radius"], flat.meta["inner_radius"], places=6)

    def test_no_margin_means_no_reference_lines(self):
        flat = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2).develop()
        self.assertEqual(flat.reference_entities, [])


class TestConeFaceted(unittest.TestCase):

    def test_bending_line_length_is_slant_height_minus_insets(self):
        # Dimostrazione nel modulo: il lato obliquo di ogni faccetta (raggio
        # interno -> esterno alla stessa angolazione) ha sempre lunghezza
        # pari alla generatrice, indipendentemente da N. Le linee di piega
        # si fermano un filo prima dei due raggi veri (vedi
        # cone.py::_BEND_LINE_INSET) per non condividere nodo coi vertici
        # del contorno — altrimenti forge spezza ogni faccetta in una parte
        # a sé (bug osservato e corretto: 8 parti invece di 1).
        from bendly.core.cone import _BEND_LINE_INSET

        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8, orientation="horizontal",
        ).develop()
        bend_lines = [e for e in flat.entities if e.get("role") == "bending"]
        self.assertEqual(len(bend_lines), 7)
        expected_length = flat.meta["slant_height"] - 2 * _BEND_LINE_INSET
        for line in bend_lines:
            (x1, y1), (x2, y2) = line["start"], line["end"]
            length = math.hypot(x2 - x1, y2 - y1)
            self.assertAlmostEqual(length, expected_length, places=6)

    def test_outer_facet_width_matches_inscribed_polygon_chord(self):
        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8,
        ).develop()
        top_mean, bottom_mean = 198.0, 148.0
        big_r = max(top_mean, bottom_mean) / 2.0
        expected = 2.0 * big_r * math.sin(math.pi / 8)
        self.assertAlmostEqual(flat.meta["outer_facet_width"], expected, places=6)

    def test_default_bend_radius_comes_from_calibration(self):
        # MAP.md D45: senza facet_bend_radius esplicito, il raggio viene
        # dalla calibration (default "default", D33/D36) — non piu' una
        # stima scalata dallo spessore mai dichiarata.
        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True,
        ).develop()
        self.assertAlmostEqual(flat.meta["facet_bend_radius"], 1.0)

    def test_explicit_facet_bend_radius_still_wins(self):
        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, facet_bend_radius=3.0,
        ).develop()
        self.assertAlmostEqual(flat.meta["facet_bend_radius"], 3.0)

    def test_faceted_bends_populated_one_per_joint(self):
        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8,
        ).develop()
        self.assertEqual(len(flat.bends), 7)
        self.assertEqual(flat.bends[0].rule, "din6935")
        self.assertGreater(flat.bends[0].bend_allowance, 0.0)

    def test_default_n_facets_is_eight(self):
        flat = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2, faceted=True).develop()
        self.assertEqual(flat.meta["n_facets"], 8)

    def test_facet_span_converges_to_smooth_sector_angle(self):
        smooth = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2).develop()
        coarse = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8,
        ).develop()
        fine = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=300,
        ).develop()

        fine_span = fine.meta["n_facets"] * fine.meta["facet_angle_deg"]
        coarse_span = coarse.meta["n_facets"] * coarse.meta["facet_angle_deg"]
        smooth_span = smooth.meta["sector_angle_deg"]

        self.assertLess(abs(fine_span - smooth_span), abs(coarse_span - smooth_span))
        self.assertLess(abs(fine_span - smooth_span), 0.01)

    def test_n_facets_below_three_raises(self):
        with self.assertRaises(ValueError):
            Cone(
                top_diameter=200, bottom_diameter=150, height=100,
                faceted=True, n_facets=2,
            ).develop()

    def test_margin_trims_only_end_facets(self):
        from bendly.core.cone import _BEND_LINE_INSET

        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8, margin=10, orientation="horizontal",
        ).develop()
        bend_lines = [e for e in flat.entities if e.get("role") == "bending"]
        self.assertEqual(len(bend_lines), 7)
        expected_length = flat.meta["slant_height"] - 2 * _BEND_LINE_INSET
        for line in bend_lines:
            (x1, y1), (x2, y2) = line["start"], line["end"]
            self.assertAlmostEqual(math.hypot(x2 - x1, y2 - y1), expected_length, places=6)

    def test_smooth_is_still_the_default(self):
        flat = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2).develop()
        self.assertNotIn("n_facets", flat.meta)


class TestConeSplit(unittest.TestCase):
    """MAP.md D46 — sviluppo parziale (sector_angle/split), tipicamente
    per farlo in più pezzi saldati insieme."""

    def _full_angle(self):
        return Cone(top_diameter=200, bottom_diameter=150, height=100).develop().meta["full_angle_deg"]

    def test_split_in_half_matches_explicit_sector_angle(self):
        full_angle = self._full_angle()
        via_split = Cone(top_diameter=200, bottom_diameter=150, height=100, split=2).develop()
        via_angle = Cone(
            top_diameter=200, bottom_diameter=150, height=100, sector_angle=full_angle / 2.0,
        ).develop()
        self.assertAlmostEqual(via_split.meta["sector_angle_deg"], via_angle.meta["sector_angle_deg"])

    def test_sector_angle_above_natural_raises(self):
        full_angle = self._full_angle()
        with self.assertRaises(ValueError):
            Cone(
                top_diameter=200, bottom_diameter=150, height=100, sector_angle=full_angle + 1.0,
            ).develop()

    def test_split_and_sector_angle_together_raises(self):
        with self.assertRaises(ValueError):
            Cone(
                top_diameter=200, bottom_diameter=150, height=100,
                sector_angle=10.0, split=2,
            ).develop()

    def test_faceted_split_in_half_gives_half_the_facets(self):
        full = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8,
        ).develop()
        half = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8, split=2,
        ).develop()
        self.assertEqual(half.meta["n_facets"], 4)
        self.assertEqual(half.meta["n_facets_full"], 8)
        self.assertEqual(len(half.bends), 3)
        # Corda/angolo di piega sono proprietà del poligono INTERO,
        # identiche fra il pezzo intero e la metà.
        self.assertAlmostEqual(half.meta["outer_facet_width"], full.meta["outer_facet_width"])
        self.assertAlmostEqual(half.meta["facet_bend_radius"], full.meta["facet_bend_radius"])

    def test_margin_on_faceted_half_still_works(self):
        # Stesso parametro margin che accorcia il cono intero (MAP.md D46).
        no_margin = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8, split=2,
        ).develop()
        with_margin = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8, split=2, margin=2,
        ).develop()
        self.assertEqual(len(with_margin.entities), len(no_margin.entities))

    def test_split_not_on_a_facet_boundary_raises(self):
        with self.assertRaises(ValueError):
            Cone(
                top_diameter=200, bottom_diameter=150, height=100, thickness=2,
                faceted=True, n_facets=8, split=3,
            ).develop()


if __name__ == "__main__":
    unittest.main()
