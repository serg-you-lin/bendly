"""
Test della REGOLA di base (DIN 6935) e del meccanismo delle calibrazioni.
Nessun dato di officina qui dentro: questo verifica che la formula sia
giusta, non che riproduca una macchina specifica.
"""

import math
import unittest
from pathlib import Path

from bendly.rules.deduction import (
    Calibration,
    bend_deduction,
    deduction_din6935,
    bend_allowance_din6935,
    external_to_centerline_deduction,
    radius_from_v_opening,
    k_din6935,
    external_to_centerline_flange,
    centerline_to_external_flange,
    external_flanges_to_centerline,
    tipo_cliente_coerente,
)
from bendly.core.bend import Bend, BentProfile, estimate_k_factor


class TestDIN6935(unittest.TestCase):

    def test_k_din_a_rapporto_uno(self):
        # r/s = 1  ->  k' = 0.65 + 0.5*log10(1) = 0.65  ->  K = k'/2 = 0.325
        self.assertAlmostEqual(k_din6935(3.0, 3.0), 0.325, places=9)

    def test_k_din_clampato_zero_mezzo(self):
        self.assertEqual(k_din6935(0.001, 100.0), 0.0)   # r/s piccolissimo
        self.assertEqual(k_din6935(1000.0, 1.0), 0.5)    # r/s enorme -> mezzeria

    def test_bend_allowance_formula(self):
        r, s, a = 2.0, 3.0, 90.0
        k = k_din6935(r, s)
        atteso = math.radians(a) * (r + k * s)
        self.assertAlmostEqual(bend_allowance_din6935(r, s, a), atteso, places=9)

    def test_bend_deduction_e_la_formula_generale(self):
        # deduction_din6935 = bend_deduction con K stimato DIN
        r, s, a = 2.5, 3.0, 90.0
        self.assertAlmostEqual(
            deduction_din6935(r, s, a, "mezzeria"),
            bend_deduction(r, s, a, k_din6935(r, s), "mezzeria"),
            places=12,
        )

    def test_accorciamento_esterno_meno_mezzeria_e_s_tan(self):
        # la differenza fra accorciamento a quota esterna e a mezzeria e'
        # esattamente s * tan(angolo/2)
        r, s, a = 4.0, 5.0, 90.0
        est = deduction_din6935(r, s, a, "esterno")
        mez = deduction_din6935(r, s, a, "mezzeria")
        self.assertAlmostEqual(est - mez, s * math.tan(math.radians(a) / 2.0), places=9)

    def test_esterno_a_mezzeria_inversa(self):
        self.assertAlmostEqual(external_to_centerline_deduction(5.222, 3.0, 90.0), 5.222 - 3.0, places=9)

    def test_raggio_da_cava_e_v_su_sei(self):
        self.assertAlmostEqual(radius_from_v_opening(12.0), 2.0, places=9)

    def test_din6935_esempio_manuale_lamiera_2mm(self):
        # esempio calcolabile a mano: r = 2, s = 2, 90 gradi
        #   k = 0.65 ; asse neutro a r + k/2*s = 2 + 0.65 = 2.65
        #   BA  = pi/2 * 2.65               = 4.1626...
        #   OSS = (2 + 2) * tan(45)         = 4.0
        #   accorciamento esterno = 2*4.0 - 4.1626 = 3.8374...
        atteso = 2 * 4.0 - (math.pi / 2) * 2.65
        self.assertAlmostEqual(deduction_din6935(2.0, 2.0, 90.0, "esterno"),
                               atteso, places=6)


class TestCalibrazioni(unittest.TestCase):

    def test_default_stima_din6935(self):
        p = Calibration.load("default")
        # 3 mm, cava 16 -> nessun K di officina -> stima DIN 6935 da r/s
        cd = p.centerline_deduction(3.0, 90.0, cava=16.0)
        atteso = deduction_din6935(16.0 / 6.0, 3.0, 90.0, "mezzeria")
        self.assertAlmostEqual(cd, atteso, places=9)
        info = p.deduction_detail(3.0, 90.0, cava=16.0)
        self.assertEqual(info.rule, "din6935")
        self.assertAlmostEqual(info.k, k_din6935(16.0 / 6.0, 3.0), places=9)

    def test_k_per_materiale_batte_la_stima_din(self):
        # una calibrazione col TUO K per materiale -> usa quello, non DIN
        p = Calibration({"nome": "prova", "k_per_materiale": {"inox": 0.38}})
        info = p.deduction_detail(3.0, 90.0, cava=16.0, material="inox")
        self.assertEqual(info.rule, "k_materiale")
        self.assertEqual(info.k, 0.38)
        self.assertAlmostEqual(
            info.value, bend_deduction(16.0 / 6.0, 3.0, 90.0, 0.38, "mezzeria"), places=9)
        # materiale non in tabella -> ripiega su DIN
        self.assertEqual(p.deduction_detail(3.0, 90.0, cava=16.0, material="ottone").rule, "din6935")

    def test_default_cava_da_tabella_se_data(self):
        # esempio_din_3cave HA valori veri di cava (default oggi non ne ha
        # nessuno, MAP.md D36: tutta la tabella a null)
        p = Calibration.load("esempio_din_3cave")
        con_tabella = p.centerline_deduction(3.0, 90.0)          # cava dedotta (V20)
        con_cava = p.centerline_deduction(3.0, 90.0, cava=20.0)  # cava esplicita
        self.assertAlmostEqual(con_tabella, con_cava, places=9)

    def test_default_senza_cava_nota_usa_raggio_fisso(self):
        # MAP.md D36: default.json ha tutti gli spessori a null -> nessuna
        # cava indovinata, raggio fisso dichiarato (1 mm), mai spessore.
        p = Calibration.load("default")
        info = p.deduction_detail(3.0, 90.0)
        self.assertEqual(info.rule, "din6935")
        self.assertIn("raggio 1", info.source)
        atteso = deduction_din6935(1.0, 3.0, 90.0, "mezzeria")
        self.assertAlmostEqual(info.value, atteso, places=9)

    def test_din6935_e_la_pura_norma(self):
        p = Calibration.load("din6935")   # nome nudo, nessun file
        info = p.deduction_detail(3.0, 90.0, cava=16.0)
        self.assertEqual(info.rule, "din6935")
        self.assertAlmostEqual(
            info.value, deduction_din6935(16.0 / 6.0, 3.0, 90.0, "mezzeria"), places=9)

    def test_tipo_misurato_usa_il_misurato_dove_c_e(self):
        p = Calibration.load("tipo_misurato")
        # 3 mm / cava 16 / 90 -> misurato 5.222 esterno -> 5.222 - 3 a mezzeria
        info = p.deduction_detail(3.0, 90.0, cava=16.0)
        self.assertEqual(info.rule, "misurato")
        self.assertAlmostEqual(info.value, 5.222 - 3.0, places=6)

    def test_tipo_misurato_ripiega_su_din_dove_manca(self):
        p = Calibration.load("tipo_misurato")   # niente k_per_materiale
        d = Calibration.load("din6935")
        # 7 mm non e' fra i misurati -> stessa stima DIN della pura norma
        self.assertAlmostEqual(
            p.centerline_deduction(7.0, 90.0, cava=40.0),
            d.centerline_deduction(7.0, 90.0, cava=40.0),
            places=9,
        )
        self.assertTrue(p.deduction_detail(3.0, 90.0, cava=99.0).fallback)  # c'e' misurato a 3mm

    def test_tipo_misurato_niente_interpolazione(self):
        # cava non esatta -> NON deve usare il misurato di una cava vicina
        p = Calibration.load("tipo_misurato")
        d = Calibration.load("din6935")
        self.assertAlmostEqual(
            p.centerline_deduction(3.0, 90.0, cava=20.0),   # cava 20, non 16
            d.centerline_deduction(3.0, 90.0, cava=20.0),
            places=9,
        )

    def test_inside_sum(self):
        # inside_sum = lavori in quote interne: accorciamento 0, lo sviluppo
        # è la somma cruda delle flange (MAP.md D35)
        p = Calibration.load("inside_sum")
        info = p.deduction_detail(3.0, 90.0, cava=16.0)
        self.assertEqual(info.rule, "inside_sum")
        self.assertEqual(info.value, 0.0)
        # indipendente da spessore / angolo / cava: sempre 0
        self.assertEqual(p.deduction_detail(8.0, 135.0, cava=40.0).value, 0.0)

    def test_inside_sum_sviluppo_e_somma_cruda_delle_flange(self):
        # riproduce il disegno cliente Sviluppo_somma_interni.pdf:
        # staffa 8 mm, una piega a 90°, sviluppo dichiarato 142 + 262 = 404
        from bendly import Bend, BentProfile
        flat = BentProfile(
            flanges=[142.0, 262.0], bends=[Bend(angle=90.0)],
            thickness=8.0, width=100.0, calibration="inside_sum",
        ).develop()
        self.assertAlmostEqual(flat.meta["total_length"], 404.0, places=9)
        b = flat.bends[0]
        self.assertEqual(b.deduction, 0.0)
        self.assertEqual(b.rule, "inside_sum")
        # linea di piega allo spigolo interno: 142 dal bordo
        bend_lines = [e for e in flat.entities if e.get("role") == "bending"]
        self.assertAlmostEqual(bend_lines[0]["start"][0], 142.0, places=9)


class TestExternalToCenterlineFlange(unittest.TestCase):
    """
    Fase 3.1 (layer umano) — traduttore quote esterno-esterno <-> mezzeria
    per la lunghezza di UNA flangia. Diverso da external_to_centerline_deduction() sopra,
    che converte l'accorciamento TOTALE, non la lunghezza della flangia.
    """

    def test_offset_e_meta_tan_indipendente_dal_raggio(self):
        # (T/2)*tan(angolo/2) -- lo stesso offset qualunque sia il raggio
        # (si elide nella differenza OSS - CSS, vedi il commento nel codice)
        t, a = 3.0, 90.0
        atteso = (t / 2.0) * math.tan(math.radians(a) / 2.0)
        centerline = external_to_centerline_flange(100.0, t, angle_after=a)
        self.assertAlmostEqual(100.0 - centerline, atteso, places=9)

    def test_nessuna_piega_adiacente_non_cambia_nulla(self):
        self.assertAlmostEqual(
            external_to_centerline_flange(100.0, 3.0), 100.0, places=9
        )

    def test_due_pieghe_adiacenti_sottraggono_due_volte(self):
        # una flangia centrale (es. l'anima di una U) ha una piega per lato
        t = 3.0
        centerline = external_to_centerline_flange(
            110.0, t, angle_before=90.0, angle_after=90.0
        )
        offset = (t / 2.0) * math.tan(math.radians(90.0) / 2.0)
        self.assertAlmostEqual(110.0 - centerline, 2 * offset, places=9)

    def test_andata_e_ritorno_tornano_uguali(self):
        centerline = external_to_centerline_flange(100.0, 3.0, angle_after=90.0)
        esterno = centerline_to_external_flange(centerline, 3.0, angle_after=90.0)
        self.assertAlmostEqual(esterno, 100.0, places=9)

    def test_lista_flange_stessa_struttura_di_bentprofile(self):
        # 3 flange, 2 pieghe -- stessa struttura di BentProfile(flanges=, bends=)
        centerline = external_flanges_to_centerline(
            [60.0, 110.0, 60.0], [90.0, 90.0], thickness=3.0
        )
        self.assertEqual(len(centerline), 3)
        # la flangia centrale (fra le due pieghe) perde due volte l'offset
        offset = (3.0 / 2.0) * math.tan(math.radians(90.0) / 2.0)
        self.assertAlmostEqual(centerline[0], 60.0 - offset, places=9)
        self.assertAlmostEqual(centerline[1], 110.0 - 2 * offset, places=9)
        self.assertAlmostEqual(centerline[2], 60.0 - offset, places=9)

    def test_bilancia_bentprofile_a_qualunque_raggio(self):
        """
        Verifica di fase (regola del gioco: un numero che deve tornare).

        Sviluppo di una L data in quote ESTERNO-ESTERNO, per due strade
        indipendenti che devono dare lo STESSO numero:

          1. formula bend-deduction DIN 6935 diretta sulle quote esterne
             (riferimento "esterno");
          2. converti le quote esterne a mezzeria con
             `external_flanges_to_centerline()`, poi lascia calcolare
             BentProfile.develop() (DIN 6935 a mezzeria, stesso raggio).

        Ripetuto su due raggi diversi: la conversione esterno<->mezzeria e'
        indipendente da R (dimostrato algebricamente: il termine in R si
        elide, MAP.md D28), quindi le due strade devono tornare identiche.
        """
        from bendly.rules.deduction import deduction_din6935

        thickness = 3.0
        angle = 90.0
        external_a, external_b = 100.0, 110.0

        for radius in (1.6, 5.0):
            bd = deduction_din6935(radius, thickness, angle, "esterno")
            atteso = (external_a + external_b) - bd

            centerline = external_flanges_to_centerline(
                [external_a, external_b], [angle], thickness
            )
            flat = BentProfile(
                flanges=centerline, bends=[Bend(angle=angle, radius=radius)],
                thickness=thickness, width=50, calibration="din6935",
            ).develop()

            self.assertAlmostEqual(flat.meta["total_length"], atteso, places=9)


class TestTipoCliente(unittest.TestCase):
    """Ogni calibrazione in calibrations/ che dichiara 'tipo_cliente'
    mantiene la promessa (MAP.md D39) — così un file che si dice
    'zero_config' non può più contenere di nascosto le cave di
    qualcun altro (il bug reale che ha fatto nascere il controllo)."""

    def test_tutte_le_calibrazioni_del_repo_sono_coerenti(self):
        cartella = Path(Calibration.CALIBRATIONS_FOLDER)
        file_json = sorted(cartella.glob("*.json"))
        self.assertTrue(file_json, "nessuna calibrazione trovata in calibrations/")
        for percorso in file_json:
            cal = Calibration.load(percorso.stem)
            with self.subTest(file=percorso.name):
                self.assertEqual(tipo_cliente_coerente(cal), [])

    def test_zero_config_con_cava_vera_e_incoerente(self):
        cal = Calibration({
            "nome": "prova", "tipo_cliente": "zero_config",
            "cava_per_spessore": {"3": 16},
        })
        problemi = tipo_cliente_coerente(cal)
        self.assertEqual(len(problemi), 1)
        self.assertIn("zero_config", problemi[0])

    def test_tipo_sconosciuto_e_incoerente(self):
        cal = Calibration({"nome": "prova", "tipo_cliente": "livello_4"})
        self.assertEqual(len(tipo_cliente_coerente(cal)), 1)

    def test_nessun_tipo_dichiarato_non_e_un_errore(self):
        cal = Calibration({"nome": "prova"})
        self.assertEqual(tipo_cliente_coerente(cal), [])


if __name__ == "__main__":
    unittest.main()
