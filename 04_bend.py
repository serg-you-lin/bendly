"""
04_bend.py - come il programma calcola lo sviluppo di un pezzo piegato
=====================================================================

Prende UNA squadra a L e ne calcola la lunghezza di taglio. Spiegato per
chi sta in officina, non per chi scrive codice.


IL PROBLEMA (quello che gia' sai dalla pressa)
---------------------------------------------
Quando pieghi una lamiera la piega "tira" il materiale: se sommi le quote
del pezzo finito, viene piu' lungo del pezzo piano da tagliare. Quel "di
piu'", per ogni piega, si chiama ACCORCIAMENTO (sui TruBend:
"Biegeverkuerzung"; sui manuali inglesi: "bend deduction").

    lunghezza da tagliare  =  somma dei lati  -  somma degli accorciamenti

L'accorciamento di una piega dipende SOLO da tre cose - spessore, cava
della matrice (l'apertura a V), angolo - verificato su 20 pezzi veri di
officina. Non dalla forma del pezzo.


COME GLIELO DICI: LA CALIBRAZIONE
--------------------------------
Non devi impostare niente per partire: se non dici nulla, il programma usa
la calibrazione "default" (norma DIN 6935 + una tabella "spessore -> cava"
gia' dentro). Ti da subito un numero.

Una CALIBRAZIONE e' un file (calibrations/<nome>.json) con: la regola di
calcolo + la tabella che dice, per ogni spessore, che cava si usa. Ne
scegli una col nome:

  "default"          DIN 6935 + tabella cava standard (valori orientativi,
                     "DA SOSTITUIRE con quelli veri"). Per partire.
  "esempio_din_3cave" un'officina che lavora in DIN con 3 sole cave. E' il
                     modello di come si scrive la calibrazione di un cliente.
  "tipo_misurato"    accorciamenti VERI, misurati da programmi TruBend
                     reali. Dove un caso manca, ripiega su DIN.
  "inside_sum"       lavori in quote interne: passi le flange interne, lo
                     sviluppo e' la loro somma esatta (raggio 0, accorc. 0).
  "<tua_officina>"   il file della tua officina, quando ce l'hai.

La cava la sceglie la tabella, dallo spessore. Non la devi dare tu, a meno
che quel pezzo specifico sia stato piegato con una cava diversa dal solito
(allora la scrivi sulla piega: Bend(angle=90, cava=20)).

Il raggio di piega NON si passa: lo ricava la calibrazione dalla cava.
(Esiste Bend(radius=...) ma e' una scorciatoia accademica sconsigliata -
serve solo se conosci il raggio interno e non la cava. Vedi COME_FUNZIONA.md.)


NOTA SULLE QUOTE - qui i lati sono "a meta' spessore"
----------------------------------------------------
I numeri passati a `flanges` sono misurati a META' dello spessore, da
spigolo virtuale a spigolo virtuale. La tappa 6 del TUTORIAL mostra come
partire dalle quote ESTERNE del disegno.

NOTA SULL'ANGOLO
----------------
`angle=90` e' l'angolo di cui la lamiera RUOTA partendo da piatta, non
l'angolo fra i due lati finiti (l'angolo INCLUSO, quello che si legge sul
disegno). Per 90 gradi sono lo stesso numero, per coincidenza - per
qualunque altro angolo no: una piega con angolo incluso 120 ha angle=60
(180-120), non 120. Se hai l'incluso dal disegno, non fare il conto a
mano: `Bend.from_included(angle_included=120)` (MAP.md D49) - stesso
identico Bend, zero rischio di sbagliare il segno del conto.
"""

from pathlib import Path

from bendly import Bend, BentProfile

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# --- Il pezzo di prova: la squadra a L "L3" di officina 1 --------------
# Sul disegno: due lati da 115.5 (quota esterna), spessore 3, piega a 90
# gradi con cava 16. A meta' spessore i due lati diventano 114.0 ciascuno.
# Sviluppo VERO, letto da TruBend (L3.bnc): 115.5 + 115.5 - 5.222 = 225.78
FLANGES_MEZZERIA = [114.0, 114.0]
THICKNESS = 3.0
WIDTH = 50.0
SVILUPPO_VERO_TRUBEND = 225.78


def sviluppo(calibration) -> "FlatGeometry":
    return BentProfile(
        flanges=FLANGES_MEZZERIA,
        bends=[Bend(angle=90)],            # niente cava, niente raggio: decide la calibrazione
        thickness=THICKNESS, width=WIDTH,
        calibration=calibration,
        label=f"L_{calibration}",
    ).develop()


def stampa(nome, flat) -> None:
    b = flat.bends[0]
    tot = flat.meta["total_length"]
    print(f"  {nome:<18} sviluppo {tot:8.2f} mm   "
          f"(accorciamento {b.deduction:5.2f}, scarto dal vero {tot - SVILUPPO_VERO_TRUBEND:+.2f})")
    print(f"    {'':<16}   cava usata {b.cava} -> {b.source}"
          + ("   [RIPIEGO su DIN: nessun dato misurato]" if b.fallback else ""))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("SQUADRA A L - lati 114 + 114 (a meta' spessore), spessore 3, piega 90")
    print(f"Sviluppo VERO secondo TruBend (L3.bnc): {SVILUPPO_VERO_TRUBEND:.2f} mm")
    print(f"Somma dei lati: {sum(FLANGES_MEZZERIA):.2f} mm - da qui si tolgono gli accorciamenti")
    print()

    print("Lo stesso pezzo, con calibrazioni diverse (la cava viene dalla loro tabella):")
    print()
    for nome in ("default", "esempio_din_3cave", "tipo_misurato", "inside_sum"):
        stampa(nome, sviluppo(nome))
    print()

    # --- Bend.from_included() (MAP.md D49) — l'angolo che leggi sul disegno,
    # non quello di rotazione. Una piega con angolo INCLUSO 120 (una piega
    # "aperta", meno di una squadra) ha angle=60 (180-120) — se qualcuno
    # legge "120" sul disegno e lo passa diretto a Bend(angle=...), il
    # pezzo esce sbagliato, in silenzio. Confronto sui tre modi:
    print("Angolo incluso 120° (piega aperta, meno di una squadra) — tre modi di passarlo:")
    corretto_a_mano = BentProfile(
        flanges=[80.0, 80.0], bends=[Bend(angle=60)],   # 180-120 fatto a mano, giusto
        thickness=3, width=50, calibration="default",
    ).develop()
    corretto_from_included = BentProfile(
        flanges=[80.0, 80.0], bends=[Bend.from_included(120)],   # stesso Bend, zero conto a mano
        thickness=3, width=50, calibration="default",
    ).develop()
    sbagliato = BentProfile(
        flanges=[80.0, 80.0], bends=[Bend(angle=120)],   # errore comune: 120 passato diretto
        thickness=3, width=50, calibration="default",
    ).develop()
    print(f"  Bend(angle=60)                 -> sviluppo {corretto_a_mano.meta['total_length']:.2f} mm  (giusto, 180-120 a mano)")
    print(f"  Bend.from_included(120)        -> sviluppo {corretto_from_included.meta['total_length']:.2f} mm  (giusto, stesso numero, zero conto a mano)")
    print(f"  Bend(angle=120)  <- SBAGLIATO   -> sviluppo {sbagliato.meta['total_length']:.2f} mm  (120 passato diretto: pezzo sbagliato, in silenzio)")
    print()

    print("COSA SI VEDE")
    print("  - Non hai impostato NIENTE: 'default' ti da comunque un numero (DIN 6935).")
    print("  - 'tipo_misurato' azzecca il vero: sono accorciamenti misurati per")
    print("    spessore 3 + cava 16, presi dal .bnc.")
    print("  - le altre ci vanno vicino: sono stime (DIN 6935, o la vecchia scuola),")
    print("    non i numeri di quella pressa. Per il pezzo vero: calibra l'officina.")
    print("  - ogni riga dice quale cava ha usato e da dove viene il numero.")
    print()

    # --- un DXF, giusto per vederlo (serve forge installato a fianco) ---
    try:
        sviluppo("tipo_misurato").to_dxf(OUTPUT_DIR / "squadra_a_l.dxf")
        print(f"DXF di controllo (tipo_misurato) in {OUTPUT_DIR.resolve()}")
    except Exception as exc:
        print(f"(DXF non scritto: {exc})")


if __name__ == "__main__":
    main()
