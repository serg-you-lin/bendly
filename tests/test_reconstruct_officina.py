"""
tests/test_reconstruct_officina.py
----------------------------------
Verifica a GIRO CHIUSO della Fase 1 (vedi MAP.md D21, D22 / TODO.md).

  pezzo reale (DXF piatto + .bnc)
    -> reconstruct.section_from_part()   -> Section a mezzeria
    -> Section.to_bent_profile(calibration="tipo_misurato").develop()
    -> la lunghezza sviluppo deve tornare quella del .bnc entro 0.01 mm.

Con la calibrazione tipo_misurato l'accorciamento è il valore MISURATO
esatto (preso dai .bnc): il giro deve chiudere alla precisione
dell'arrotondamento, non a 0.1 mm come per i golden din6935.

Si controllano anche i singoli segmenti a mezzeria: la ricostruzione deve
dare lo sketch primitivo nominale ([114, 114], [40, 40, 60, 30, 70], ...).
Su Z e omega le pieghe sono di verso opposto (cerniera) e a mezzeria
l'ambiguità di ± spessore·tan(angolo/2) non c'è — è il senso della
convenzione a mezzeria.

L'omega da 10 mm è fatta con una pre-piega (5 colpi per 4 pieghe
geometriche): il numero di colpi non cambia il pezzo né lo sviluppo, la
pre-piega viene scartata e il giro chiude come gli altri.

Include anche i 6 golden non-90° aperti (`La114ab{120,150}b114s{1,3,10}`,
MAP.md "angolo incluso vero", 11 set 2026): l'angolo vero viene dal
Sollwinkel del `.bnc`, non più assunto 90/270 dal solo layer DXF. Le forme
a più pieghe non a 90° (Z, omega) restano fuori (`is_reconstructable_name`).

Gira solo con i dati reali di officina 1 (data_4_cloude/, non su GitHub).
"""

import unittest

TOLL_MM = 0.01

# segmenti nominali dello sketch primitivo, per forma (solo dove tutte le
# pieghe sono nello stesso verso o comunque la cerniera è a mezzeria)
_SEGMENTS = {
    "L": [114.0, 114.0],
    "U": [60.0, 110.0, 60.0],
    "Z": [60.0, 100.0, 50.0],
    "O": [40.0, 40.0, 60.0, 30.0, 70.0],
}

try:
    from reconstruct import (
        DATA_DIR, section_from_part, part_pairs, is_reconstructable_name,
    )
    _PAIRS = []
    for _shape in ("L", "U", "Z", "O"):
        _PAIRS += part_pairs(DATA_DIR / _shape)
    _PAIRS = [(b, d) for b, d in _PAIRS if is_reconstructable_name(d.stem)]
except Exception:  # noqa: BLE001 — senza dati/ezdxf la classe si salta
    _PAIRS = []


@unittest.skipUnless(_PAIRS, "dati reali di officina 1 non presenti (ok su CI)")
class TestReconstructOfficina1(unittest.TestCase):
    pass


def _make_test(bnc_path, dxf_path):
    def test(self):
        try:
            rec = section_from_part(bnc_path, dxf_path)
        except ValueError as exc:
            self.skipTest(str(exc))
            return

        flat = rec.section.to_bent_profile(
            width=50, calibration="tipo_misurato", cava=rec.v_opening,
        ).develop()

        got = flat.meta["total_length"]
        print(f"{dxf_path.name}: sviluppo {got:.3f} vs .bnc {rec.developed_length:.3f}")
        self.assertAlmostEqual(got, rec.developed_length, delta=TOLL_MM)

        expected = _SEGMENTS.get(rec.section.shape)
        if expected is not None:
            self.assertEqual(len(rec.section.segments), len(expected))
            for seg, exp in zip(rec.section.segments, expected):
                self.assertAlmostEqual(seg, exp, delta=TOLL_MM)

    test.__name__ = f"test_{dxf_path.stem}"
    return test


for _bnc, _dxf in _PAIRS:
    setattr(TestReconstructOfficina1, f"test_{_dxf.stem}", _make_test(_bnc, _dxf))


if __name__ == "__main__":
    unittest.main()
