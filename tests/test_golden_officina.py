"""
Golden test "officina 1".

NON prova la correttezza della fisica della piega (i numeri li abbiamo
messi noi nel profilo, dai .bnc): prova che la CATENA GEOMETRICA sia
giusta — somma dei segmenti, posizione delle linee di piega, versi
alternati di Z/omega — dato l'accorciamento corretto.

Gira solo se ci sono i dati reali di officina 1 (cartella data_4_cloude/,
non su GitHub). Senza, si salta.
"""

import glob
import os
import re
import unittest

TOLLERANZA_MM = 0.1

DATI = "data_4_cloude"
CALIBRAZIONE = os.path.join("calibrations", "tipo_misurato.json")

FORME = {
    "L": [114.0, 114.0],
    "U": [60.0, 110.0, 60.0],
    "Z": [60.0, 100.0, 50.0],
    "O": [40.0, 40.0, 60.0, 30.0, 70.0],
}
CAVA = {"EV1": 6, "EV2": 8, "EV5": 16, "EW50": 50, "EW60": 60, "EV60": 60}

_ha_dati = os.path.isdir(DATI) and os.path.isfile(CALIBRAZIONE)


@unittest.skipUnless(_ha_dati, "dati reali di officina 1 non presenti (ok su CI)")
class TestGoldenOfficina1(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import ezdxf  # noqa
        from reconstruct import is_ninety_degree_name
        from bendly import Calibration
        cls.calibration = Calibration.load("tipo_misurato")
        cls.files = [
            f for f in sorted(glob.glob(f"{DATI}/[LUZO]/*.dxf"))
            if is_ninety_degree_name(os.path.splitext(os.path.basename(f))[0])
        ]
        assert cls.files, "nessun DXF di test trovato"

    def _caso(self, path):
        base = os.path.splitext(os.path.basename(path))[0]
        forma = base[0]
        # se c'è il .bnc con lo stesso nome (schema nuovo: L12, O2, ...),
        # spessore e apertura V si prendono da lì, sono autorevoli.
        twin = os.path.join(os.path.dirname(path), base + ".bnc")
        if os.path.isfile(twin):
            from bendly.adapters.trubend import leggi_bnc
            b = leggi_bnc(twin)
            cava = b.matrice.apertura_v if b.matrice else None
            return forma, float(b.spessore), cava
        # schema verboso storico: ...s<spessore>-<matrice>
        spess = float(re.search(r"s(\d+)-", base).group(1))
        cava = CAVA.get(base.split("-")[-1])
        return forma, spess, cava

    def test_lunghezza_sviluppo(self):
        import ezdxf
        from ezdxf import bbox
        from bendly import Bend, BentProfile

        for path in self.files:
            forma, spess, cava = self._caso(path)
            if forma not in FORME:
                continue
            with self.subTest(file=os.path.basename(path)):
                b = bbox.extents(ezdxf.readfile(path).modelspace())
                reale = max(b.size.x, b.size.y)
                segmenti = FORME[forma]
                bends = [Bend(angle=90, cava=cava) for _ in range(len(segmenti) - 1)]
                flat = BentProfile(flanges=segmenti, bends=bends, thickness=spess,
                                   width=50, calibration=self.calibration).develop()
                self.assertAlmostEqual(flat.meta["total_length"], reale,
                                       delta=TOLLERANZA_MM)

    def test_posizioni_linee_di_piega(self):
        import ezdxf
        from bendly import Bend, BentProfile

        for path in self.files:
            forma, spess, cava = self._caso(path)
            if forma not in FORME or len(FORME[forma]) < 3:
                continue  # solo i multi-piega
            with self.subTest(file=os.path.basename(path)):
                doc = ezdxf.readfile(path)
                msp = doc.modelspace()
                poly = [e for e in msp if e.dxftype() == "POLYLINE"][0]
                ys = [v.dxf.location.y for v in poly.vertices]
                xs = [v.dxf.location.x for v in poly.vertices]
                vert = (max(ys) - min(ys)) > (max(xs) - min(xs))
                o = min(ys) if vert else min(xs)
                reali = sorted(
                    (l.dxf.start.y if vert else l.dxf.start.x) - o
                    for l in msp if l.dxftype() == "LINE"
                )
                segmenti = FORME[forma]
                bends = [Bend(angle=90, cava=cava) for _ in range(len(segmenti) - 1)]
                flat = BentProfile(flanges=segmenti, bends=bends, thickness=spess,
                                   width=50, calibration=self.calibration).develop()
                nostre = sorted(
                    e["start"][0] for e in flat.entities if e.get("role") == "bending"
                )
                self.assertEqual(len(nostre), len(reali))
                for n, r in zip(nostre, reali):
                    self.assertAlmostEqual(n, r, delta=TOLLERANZA_MM)


if __name__ == "__main__":
    unittest.main()
