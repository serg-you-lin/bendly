"""
Round-trip test for the drawing interpreter.

Build a section from known parameters, throw away everything but its
outline, and check `read_section` recovers:
  - is_sheet_metal / is_bent
  - the thickness
  - the centerline segments (apex to apex)
  - the bend angles (naming scheme)

A section reads the same from either end, so segments/angles are compared
up to that reversal (see `_canonical`).
"""

import math
import unittest

from bendly.model.geometry import polar_point
from bendly.model.section import Section
from bendly.rules.read_section import SheetThicknessTable, read_section

SHAPES = {
    "L": ([114.0, 114.0], [90.0]),
    "U": ([60.0, 110.0, 60.0], [90.0, 90.0]),
    "Z": ([60.0, 100.0, 50.0], [90.0, 270.0]),
    "O": ([40.0, 40.0, 60.0, 30.0, 70.0], [90.0, 270.0, 270.0, 90.0]),
}
THICKNESSES = [1.0, 3.0, 10.0]


def _canonical(segments, angles):
    fwd = (list(segments), list(angles))
    rev = (list(reversed(segments)),
           [round((360.0 - a) % 360.0, 4) for a in reversed(angles)])
    return min(fwd, rev, key=lambda pair: (pair[0], pair[1]))


class TestReadSection(unittest.TestCase):

    def test_roundtrip_golden_shapes(self):
        for shape, (segments, angles) in SHAPES.items():
            for thickness in THICKNESSES:
                d = Section.default(shape, segments, angles, thickness)
                reading = read_section(d.section().entities)
                with self.subTest(section=d.name()):
                    self.assertTrue(reading.is_sheet_metal, reading.notes)
                    self.assertTrue(reading.is_bent, reading.notes)
                    self.assertAlmostEqual(reading.thickness, thickness, delta=1e-3)

                    exp_seg, exp_ang = _canonical(segments, angles)
                    self.assertEqual(len(reading.centerline_segments), len(exp_seg))
                    for got, want in zip(reading.centerline_segments, exp_seg):
                        self.assertAlmostEqual(got, want, delta=0.05)
                    self.assertEqual(
                        [round(a) % 360 for a in reading.angles],
                        [round(a) % 360 for a in exp_ang],
                    )

    def test_flat_blank_is_sheet_but_not_bent(self):
        # a plain rectangle 200 x 3: constant-distance faces, no arcs
        rect = [
            {"type": "line", "start": (0, 0), "end": (200, 0)},
            {"type": "line", "start": (200, 0), "end": (200, 3)},
            {"type": "line", "start": (200, 3), "end": (0, 3)},
            {"type": "line", "start": (0, 3), "end": (0, 0)},
        ]
        reading = read_section(rect)
        self.assertTrue(reading.is_sheet_metal)
        self.assertFalse(reading.is_bent)
        self.assertAlmostEqual(reading.thickness, 3.0, delta=1e-3)

    def test_unknown_thickness_is_not_sheet_metal(self):
        rect = [
            {"type": "line", "start": (0, 0), "end": (200, 0)},
            {"type": "line", "start": (200, 0), "end": (200, 3.7)},
            {"type": "line", "start": (200, 3.7), "end": (0, 3.7)},
            {"type": "line", "start": (0, 3.7), "end": (0, 0)},
        ]
        table = SheetThicknessTable(thicknesses_mm=[1.0, 2.0, 3.0, 4.0],
                                    tolerance_mm=0.2)
        reading = read_section(rect, table=table)
        self.assertFalse(reading.is_sheet_metal)

    def test_angle_sign_survives_down_bend(self):
        # Z has one up (90) and one down (270) bend
        d = Section.default("Z", [60.0, 100.0, 50.0], [90.0, 270.0], 3.0)
        reading = read_section(d.section().entities)
        self.assertIn(270.0, [round(a) % 360 for a in reading.angles])
        self.assertIn(90.0, [round(a) % 360 for a in reading.angles])

    def test_two_concentric_circles_are_bent_sheet_metal(self):
        # MAP.md D42 - top view of a tube: two full circles, same center,
        # radii differing by exactly the thickness. Signal 1+2+3 must all
        # fire even though there is no straight cap anywhere.
        outer_r, thickness = 75.0, 3.0
        circles = [
            {"type": "circle", "center": (0.0, 0.0), "radius": outer_r},
            {"type": "circle", "center": (0.0, 0.0), "radius": outer_r - thickness},
        ]
        reading = read_section(circles)
        self.assertTrue(reading.is_sheet_metal, reading.notes)
        self.assertTrue(reading.is_bent, reading.notes)
        self.assertAlmostEqual(reading.thickness, thickness, delta=1e-3)

    def test_two_concentric_circles_centerline_not_recovered_yet(self):
        # Detection works (test above); the flange-chain recovery is a
        # separate, not-yet-built piece (D42 step 3) - it must degrade to
        # an explicit note, not crash and not fabricate segments/angles.
        circles = [
            {"type": "circle", "center": (0.0, 0.0), "radius": 75.0},
            {"type": "circle", "center": (0.0, 0.0), "radius": 72.0},
        ]
        reading = read_section(circles)
        self.assertEqual(reading.centerline_segments, [])
        self.assertEqual(reading.angles, [])
        self.assertTrue(any("centerline not recovered" in n for n in reading.notes))

    def test_single_circle_is_too_few_edges(self):
        reading = read_section([{"type": "circle", "center": (0.0, 0.0), "radius": 75.0}])
        self.assertFalse(reading.is_sheet_metal)
        self.assertFalse(reading.is_bent)

    def test_bare_calandra_arc_is_pure_arc_not_bentprofile(self):
        # MAP.md D42/D43 - a rolled "sella": R300 (centerline), 60deg,
        # thickness 3. cap -> outer arc -> cap -> inner arc, no straight
        # flange anywhere - Cylinder/Cone territory, not BentProfile.
        r_cl, half_angle, thickness = 300.0, 30.0, 3.0
        r_out, r_in = r_cl + thickness / 2.0, r_cl - thickness / 2.0
        entities = [
            {"type": "arc", "center": (0.0, 0.0), "radius": r_out,
             "start_angle": -half_angle, "end_angle": half_angle, "ccw": True},
            {"type": "line", "start": polar_point(r_out, half_angle),
             "end": polar_point(r_in, half_angle)},
            {"type": "arc", "center": (0.0, 0.0), "radius": r_in,
             "start_angle": half_angle, "end_angle": -half_angle, "ccw": False},
            {"type": "line", "start": polar_point(r_in, -half_angle),
             "end": polar_point(r_out, -half_angle)},
        ]
        table = SheetThicknessTable(thicknesses_mm=[1.0, 2.0, 3.0, 4.0], tolerance_mm=0.2)
        reading = read_section(entities, table=table)
        self.assertTrue(reading.is_sheet_metal, reading.notes)
        self.assertTrue(reading.is_bent, reading.notes)
        self.assertAlmostEqual(reading.thickness, thickness, delta=1e-3)
        self.assertEqual(reading.centerline_segments, [])
        self.assertEqual(reading.angles, [])
        self.assertAlmostEqual(reading.pure_arc_radius, r_cl, delta=1e-3)
        self.assertAlmostEqual(reading.pure_arc_angle_deg, 2 * half_angle, delta=1e-3)


if __name__ == "__main__":
    unittest.main()
