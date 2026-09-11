# Come funziona lo sviluppo delle pieghe

> Scritta da Claude, da rileggere con occhio di officina. Spiega come il
> tool decide la lunghezza di uno sviluppo e perché ci si può fidare.
> Modello rivisto il 6 set 2026 (`MAP.md` D33, una formula sola) e l'11 set
> 2026 (`MAP.md` D36): la formula generica è il prodotto, non i dati
> misurati di un'officina — vedi "Cosa c'è di default" più sotto.

## Il problema

Quando pieghi una lamiera, la piega "consuma" materiale: la somma delle
quote del pezzo finito è più lunga dello sviluppo piano da tagliare. La
differenza, per ogni piega, si chiama **accorciamento** (tedesco
*Biegeverkürzung*, inglese *bend deduction*).

Verificato sui 20 pezzi reali di officina 1 (L, U, Z, omega): l'accorcia-
mento di una piega dipende **solo da spessore, cava, angolo** — non dalla
forma, dalla lunghezza delle flange, dal numero di pieghe. Entro 5
centesimi di millesimo. Quindi:

```
lunghezza sviluppo = somma dei segmenti  −  somma degli accorciamenti
```

I segmenti sono misurati a **mezzeria** dello spessore, da spigolo virtuale
a spigolo virtuale (`MAP.md` D1).

## La formula (una sola)

L'accorciamento di **una** piega è:

```
BD = 2·(r + s/2)·tan(β/2)  −  β·(r + K·s)          β in radianti
```

| simbolo | cos'è |
|---|---|
| `s` | spessore lamiera |
| `β` | angolo di piega = di quanto ruota la lamiera da piatta (90° per una squadra) |
| `r` | raggio interno di piega |
| `K` | **fattore K**: dove sta la fibra neutra, da 0 (faccia interna) a 0.5 (mezzeria). È lo stesso K dei manuali e del database materiale di TruBend. |

Non ci sono altre formule. `din6935`, "modo manuale", "somma interni": erano
nomi diversi per **da dove prendi `r` e `K`**, non calcoli diversi.

## Da dove vengono `r` e `K`

### Il raggio `r` — in ordine di bontà

1. **Dalla cava della matrice**: `r ≈ cava / 6` (regola della piega in
   aria). La cava viene dalla tabella `spessore → cava` della calibrazione
   — quella VERA della tua officina, se gliel'hai data.
2. Per una piega fatta con una cava fuori standard: la scrivi tu,
   `Bend(angle=90, cava=20)`.
3. Se conosci il raggio interno e non la cava (bombato, coniatura, stampo a
   raggio): `Bend(angle=90, radius=8)`.
4. **Se non sai né la cava né il raggio** (spessore assente dalla tabella,
   o presente con `null`): un **raggio fisso dichiarato, 1 mm**
   (`DEFAULT_UNKNOWN_RADIUS_MM`, `MAP.md` D36) — mai `raggio = spessore`
   né un'altra stima scalata dallo spessore, che sembrerebbe informata ma
   sarebbe inventata. È la situazione di partenza di chi usa `default`
   senza aver toccato niente (caso **A** più sotto): un numero grezzo ma
   onesto, sempre scritto in chiaro nel risultato ("raggio 1 fisso,
   nessuna cava nota per...").

### Il fattore `K` — in ordine di bontà

1. **Misurato.** Se la calibrazione ha l'accorciamento **misurato** per
   quella combinazione (spessore + cava + angolo), il tool usa quel numero
   diretto — niente formula. È la verità: la tua pressa, il tuo materiale,
   il tuo utensile. Viene dai file `.bnc` di TruBend.
2. **Il tuo K per materiale.** Se la calibrazione ha una tabella
   `k_per_materiale` (`acciaio` 0.40, `inox` 0.38, `alluminio` 0.41…), usa
   il K del materiale del pezzo. È quello che TruBend tiene nel database
   materiale.
3. **Stima DIN 6935.** Se non c'è nessuno dei due, il K lo stima la norma
   DIN 6935 dal solo rapporto raggio/spessore:
   `K = (0.65 + 0.5·log₁₀(r/s)) / 2`, limitato tra 0 e 0.5.
   DIN 6935 è **cieca al materiale** — è una semplificazione tarata
   sull'acciaio. Buona per farsi un'idea, meno per inox/alluminio.

Ogni piega, nel risultato, dice quale delle tre strade ha preso
(`flat.bends[i].source`, in chiaro). Niente scatola nera.

### `inside_sum` — a parte

Moltissime carpenterie non calcolano: sommano le quote **interne** e via
(in Italia è la prassi dominante — vedi il disegno cliente in
`data_4_cloude/Sviluppo_somma_interni.pdf`: staffa 8 mm, una piega,
sviluppo dichiarato `142 + 262 = 404`).

`inside_sum` non è una regola di accorciamento: è la dichiarazione che
lavori **tutto in quote interne**. Le flange che passi sono le quote
interne (spigolo interno a spigolo interno); lo sviluppo è la loro
**somma esatta**, raggio 0, accorciamento 0, linea di piega allo spigolo
interno. Su pieghe dello stesso verso (L, U, omega) non è interpretabile:
è quel numero lì. Sulle pieghe su-giù (Z) la "quota interna" della flangia
in mezzo è ambigua come tutto il resto — lì serve la vista in sezione.

## La calibrazione (il file)

Una **calibrazione** è un file `calibrations/<nome>.json`. Porta le scelte
di un'officina: la tabella cave, e — se ce l'hai — il K per materiale e gli
accorciamenti misurati. Tutti i campi tranne la tabella cave sono
opzionali.

```json
{
  "nome": "officina di Tizio",
  "cava_per_spessore": { "1": 8, "2": 12, "3": 16, "4": 20, "5": 25 },
  "k_per_materiale":   { "acciaio": 0.40, "inox": 0.38, "alluminio": 0.41 },
  "misurati": [
    { "spessore": 3, "cava": 16, "angolo": 90, "accorciamento_esterno": 5.222, "fonte": "L3.bnc" }
  ]
}
```

Ogni calibrazione è un file **completo**, senza ereditarietà da un'altra
(`MAP.md` D5). `BentProfile(..., material="inox")` sceglie quale riga di
`k_per_materiale` usare (default `"acciaio"`).

## Cosa c'è di default, e i quattro casi (`MAP.md` D36)

**Il default è `calibrations/default.json`.** Se in `BentProfile` non
passi `calibration`, usa quello. Non indovina **nessuna** cava: la tabella
`cava_per_spessore` elenca gli spessori comuni tutti a `null` — un elenco
di taglie da riempire, non un valore inventato spacciato per vero.

Quindi il default = **raggio fisso dichiarato (1 mm) + K stimato DIN 6935**
(dal rapporto raggio/spessore): un numero subito, dichiarato grezzo, mai
travestito da dato reale. Ogni piega scrive nel `source` da dove viene.

Ogni scelta di calibrazione si controlla contro questi quattro casi —
sono sempre gli stessi, non se ne inventano altri per ogni feature. Il
nome standard di ognuno è il campo `tipo_cliente` della calibrazione
(niente più lettere A/B/C/D, MAP.md D39):

| `tipo_cliente` | Chi è | Cosa dà a `bendly` | Calibrazione |
|---|---|---|---|
| `zero_config` | sconosciuto, scarica e usa, non legge nulla | niente | `default` (o omessa) — raggio fisso 1 mm, K stima DIN |
| `cava_propria` | carpenteria vicina, ha le sue cave ma non il CAM | solo `cava_per_spessore` reale (5 minuti, mai una misura) | copia di `esempio_din_3cave.json` — raggio dalla cava vera, K stima DIN |
| `somma_interna` | vuole solo la somma delle quote interne, zero K-factor | niente, solo la sua convenzione | `inside_sum.json` — bypassa raggio e K |
| `misurato` | ha il CAM, vuole avvicinarsi per preventivare | cava + accorciamenti **misurati** (ore di lavoro dedicato, non gratis) | come `tipo_misurato.json` — misurato dove c'è, stima altrove |

Una scelta che serve bene `misurato` ma appesantisce gli altri tre è
quasi sempre la scelta sbagliata: la formula generica (`zero_config`/
`cava_propria`) deve reggere da sola, i dati misurati di un'officina sono
un bonus, mai un requisito.

**Il `tipo_cliente` non è un'etichetta decorativa**: `tipo_cliente_coerente(calibration)`
controlla che il contenuto del file mantenga la promessa (es. `zero_config`
non può avere cave vere, `misurato` non può avere `misurati` vuoto) e un
test gira su ogni file in `calibrations/` a ogni `pytest`. Nasce da un bug
vero: `default.json` (`zero_config`) copiava in silenzio le cave reali
della calibrazione a dati misurati (`misurato`) — il controllo prende
esattamente quella classe di errore.

`04_bend.py` sviluppa lo stesso pezzo con più calibrazioni, fianco a fianco.

## Dove stanno i numeri veri (file CAM)

Un `.bnc` di TruBend **non contiene un calcolo, contiene il risultato**.
Dentro `L3.bnc`:

```
quote esterne del pezzo:  115.50 + 115.50
accorciamento (Biegeverkürzung):  −5.222
lunghezza sviluppo:  225.78

115.50 + 115.50 − 5.222 = 225.78
```

Il `−5.222` viene dal database materiale di TruBend (che include il K del
materiale), non dal file. Per un CAM diverso: ogni CAM esporta un DXF
piatto, e la lunghezza sviluppo è il rettangolo che lo contiene — quello si
legge sempre uguale. Il lettore del formato nativo (`.bnc`…) serve solo ad
avere l'accorciamento spezzato piega per piega.
`bendly/adapters/trubend.py` è il lettore per TruBend.

## Quanto ci si può fidare (onesto)

- **Combinazione misurata** → esatta (è il numero della pressa).
- **K per materiale** → buono: è lo stesso principio del database TruBend.
  Un provino di verifica su un nuovo spessore/materiale resta consigliato.
- **Stima DIN 6935, cava nota** (nessun K dato) → un'idea ragionevole.
  Sull'acciaio ci va vicino (sui dati di officina 1: ~0.05 mm sull'1 mm,
  ~0.4 mm sul 3 mm, fino a qualche mm sugli spessori grossi, 15-20 mm).
- **Stima DIN 6935, raggio fisso** (nessuna cava nota, caso A) → la più
  grezza delle tre: onesta e dichiarata, ma senza la cava vera l'errore
  non è misurato. Basta la cava (caso B) per togliersi di mezzo questa
  fascia d'errore.
- **Angoli diversi da 90°, aperti** (120-150°, poca rotazione: ancora
  piena piega in aria) → la formula tiene, verificato entro 0.005-0.3 mm
  su un numero ancora piccolo di provini.
- **Angoli diversi da 90°, chiusi** (<~90° di incluso) → **non affidabile
  per costruzione**, non è un buco di dati: sotto una certa apertura la
  matrice non ci arriva in aria e si passa a coniare, un processo fisico
  diverso (raggio dal punzone, non dalla cava — vedi
  `PIEGA_IN_ARIA_E_CONIATURA.md`). Un interprete che legge solo un
  disegno non può sapere se una piega verrà coniata: la formula assume
  aria (il caso dominante) e lo dichiara.
- **Scarto fisico** (ritorno elastico, lotto, usura utensili): ±0.2–0.5 mm
  sul pezzo reale, con qualunque metodo. Si corregge in macchina
  sull'angolo. Non è compito del tool.

## Come si usa (codice)

```python
from bendly import Bend, BentProfile

flat = BentProfile(
    flanges=[60, 110, 60],                   # segmenti a mezzeria (dallo sketch)
    bends=[Bend(angle=90), Bend(angle=90)],   # solo l'angolo
    thickness=3, width=50,
    material="acciaio",                       # sceglie il K in k_per_materiale
    calibration="tipo_misurato",              # o omesso -> "default"
).develop()

flat.meta["total_length"]                     # la lunghezza sviluppo
for b in flat.bends:                          # una riga per piega
    print(b.deduction, b.source)              # quanto, e da dove viene
flat.to_dxf("pezzo.dxf")                      # richiede forge installato a fianco
```

La cava viene dalla tabella della calibrazione; la passi (`Bend(cava=20)`)
solo per una piega fatta con una cava fuori standard.

## Generare una calibrazione dai file .bnc

```
python tests/generate_calibration.py data_4_cloude "tipo_misurato" > calibrations/tipo_misurato.json
```

Riempie `cava_per_spessore` e `misurati` da una cartella di `.bnc`. Il
`k_per_materiale` lo aggiungi a mano (dal database materiale della pressa).

## I test

- `tests/test_deduction.py` → la formula e la stima DIN 6935 danno i numeri
  attesi; la conversione quote esterne↔mezzeria è indipendente dal raggio.
- `tests/test_golden_officina.py` → con `tipo_misurato`, il tool riproduce
  ogni DXF reale (lunghezza + posizione pieghe) entro tolleranza. Gira solo
  se i dati del cliente sono presenti.
- `tests/test_trubend.py` → il lettore `.bnc` legge i campi giusti.
