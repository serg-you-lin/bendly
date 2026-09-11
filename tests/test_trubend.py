"""
Sanita' del lettore .bnc. Gira solo se ci sono i file reali (non su GitHub).
"""

import glob
import os
import unittest

DATI = "data_4_cloude"
_ha_dati = os.path.isdir(DATI) and bool(glob.glob(f"{DATI}/**/*.bnc", recursive=True))


@unittest.skipUnless(_ha_dati, "file .bnc non presenti (ok su CI)")
class TestLettoreBnc(unittest.TestCase):

    def test_legge_campi_essenziali(self):
        from unfold.adapters.trubend import leggi_bnc
        for path in glob.glob(f"{DATI}/**/*.bnc", recursive=True):
            with self.subTest(file=os.path.basename(path)):
                r = leggi_bnc(path)
                self.assertEqual(r.materiale, "St37")
                self.assertGreater(r.spessore, 0)
                self.assertGreater(r.sviluppo, 0)
                self.assertTrue(r.pieghe)
                self.assertIsNotNone(r.matrice)
                self.assertGreater(r.matrice.apertura_v, 0)

    def test_accorciamento_piu_quote_esterne_da_lo_sviluppo(self):
        # verifica la relazione interna al .bnc: per una L,
        #   quota_esterna_a + quota_esterna_b - accorciamento = sviluppo
        from unfold.adapters.trubend import leggi_bnc
        r = leggi_bnc(f"{DATI}/L/L3.bnc")
        acc = r.pieghe[0].accorciamento_esterno
        # L3: a = b = 114 a mezzeria, spessore 3 -> quota esterna 115.5
        self.assertAlmostEqual(115.5 + 115.5 - acc, r.sviluppo, delta=0.05)


if __name__ == "__main__":
    unittest.main()
