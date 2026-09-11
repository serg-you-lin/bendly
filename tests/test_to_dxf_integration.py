"""
test_to_dxf_integration.py
----------------------------
Verifica l'integrazione con forge — FlatGeometry.to_dxf() end-to-end. Salta
automaticamente se forge non è installato a fianco (vedi README).
"""

import unittest

try:
    import forge  # noqa: F401
    FORGE_AVAILABLE = True
except ImportError:
    FORGE_AVAILABLE = False

from unfold import Bend, BentProfile, Cone, Cylinder


@unittest.skipUnless(FORGE_AVAILABLE, "forge non installato — pip install -e ../dxf-forge")
class TestToDxfIntegration(unittest.TestCase):

    def test_cone_to_forge_result(self):
        flat = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2).develop()
        result = flat.to_forge_result()
        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.cluster_count, 1)

    def test_cylinder_to_forge_result(self):
        flat = Cylinder(diameter=150, height=500, thickness=2).develop()
        result = flat.to_forge_result()
        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.cluster_count, 1)

    def test_bent_profile_to_forge_result_detects_bending_line(self):
        flat = BentProfile(
            flanges=[50, 80], bends=[Bend(angle=90, radius=3)],
            thickness=2, width=200,
        ).develop()
        result = flat.to_forge_result()
        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.cluster_count, 1)
        self.assertEqual(len(result.clusters[0].bending_lines), 1)

    def test_faceted_cylinder_detects_seven_bending_lines(self):
        flat = Cylinder(diameter=150, height=500, thickness=2, faceted=True, n_facets=8).develop()
        result = flat.to_forge_result()
        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.cluster_count, 1)
        self.assertEqual(len(result.clusters[0].bending_lines), 7)

    def test_faceted_cone_detects_seven_bending_lines(self):
        flat = Cone(
            top_diameter=200, bottom_diameter=150, height=100, thickness=2,
            faceted=True, n_facets=8,
        ).develop()
        result = flat.to_forge_result()
        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.cluster_count, 1)
        self.assertEqual(len(result.clusters[0].bending_lines), 7)

    def test_cone_to_dxf_writes_file_with_notes(self, tmp_path=None):
        import tempfile
        from pathlib import Path

        flat = Cone(top_diameter=200, bottom_diameter=150, height=100, thickness=2).develop()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cone.dxf"
            doc_out = flat.to_dxf(out)
            self.assertTrue(out.exists())
            texts = list(doc_out.modelspace().query("TEXT"))
            self.assertTrue(any(t.dxf.layer == "Notes" for t in texts))


if __name__ == "__main__":
    unittest.main()
