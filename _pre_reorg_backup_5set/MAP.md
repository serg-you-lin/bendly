# MAP — decision log di `unfold`

La **memoria delle decisioni**: cosa è stato deciso e soprattutto *perché*.
Non è documentazione (quella andrà in `docs/`), non è un log di sessione
(quello è il git log, quando il repo sarà su git).

**Regola: una decisione chiusa non si re-decide da capo.** Se va rimessa in
discussione si dice esplicitamente "stiamo riaprendo la decisione N".

---

## Stato corrente (agg. 4 set 2026)

- **Repo git:** non ancora inizializzato. `.gitignore` già scritto (esclude
  i dati cliente). Da valutare come pulizia futura.
- **Test:** 101 passati + 67 subtest (`python -m pytest -q`).
- **API pubblica** (`unfold.__all__`):
  `Cone`, `Cylinder`, `FlatGeometry`, `polar_point`, `Bend`, `BendResult`,
  `BentProfile`, `estimate_k_factor`, `MATERIAL_K_FACTORS`, `Calibration`,
  `DeductionInfo`, `deduction_din6935`, `Section`, `interpret_section`,
  `SectionReading`, `SheetThicknessTable`, più `__version__`.
- **Contratto neutro con forge:** `FlatGeometry.entities` è nello stesso
  schema di `forge.load_geometry()`. `unfold` non importa mai forge per il
  calcolo; forge serve solo a `to_dxf()`.

### Cosa manca, in ordine (vedi `PIANO.md`)

1. ✅ Pulizie di impostazione: versione via `importlib` · `MAP.md`
   (questo file) · script di esplorazione numerati `00_*`…`05_*` alla
   radice + `SCRIPTS.md`.
2. ✅ Fase 1 — `tests/reconstruct.py` (`dima_da_pezzo(bnc, dxf)`, strumento
   interno) + `tests/test_reconstruct_officina.py`: giro chiuso su tutti e
   20 i provini L / U / Z / omega × spessori, entro 0.01 mm.
3. ✅ Fase 2 — lettura guidata del motore. Letto `develop()` sulla L,
   Federico ha rispiegato la catena (verifica passata); tolta
   l'ereditarietà dei profili (D5); aggiunto `BendResult` con il segnale
   "no data → din6935" (D24); letta insieme la formula DIN 6935
   (`_k_din6935` / `bend_allowance_din6935` / `deduction_din6935`); fatte
   le rinomine (D23).
4. Fasi 3, 4, 5 — parcheggiate. Poi il refactor a strati sulle skill (D16).

---

## Decisioni

### D1 — Il core calcola a MEZZERIA, non a quote esterne ✅

`BentProfile.flanges` sono lunghezze misurate da mezzeria a mezzeria
(centerline set-back `CSS = (R + sp/2)·tan(angolo/2)`), non quote esterne.
Motivo: la flangia incastrata fra due pieghe di verso opposto (l'anima di
una Z, le anime di un'omega) non ha una faccia "esterna" coerente — le due
pieghe adiacenti vedono come esterna due facce opposte. A quota esterna
`BentProfile` sbagliava di `sp·tan(angolo/2)` per flangia ambigua (−2 mm su
una Z a 90°/sp2, −4 mm su un'omega). La mezzeria non ha lati: l'ambiguità
sparisce alla radice, non si riduce soltanto. Verificato con uno script di
geometria indipendente: differenza U / Z / omega = 0.0000. Combacia anche
con come Federico modella i pezzi in CAD (sketch a mezzeria + feature
lamiera, spessore libero di cambiare). Implementato in `unfold/bend.py`
(`Bend.centerline_setback()`); `outside_setback()` / `inside_setback()`
restano disponibili come utilità.

### D2 — Lo sviluppo è lineare: Σ segmenti − Σ accorciamenti ✅

Dimostrato sui 20 DXF reali di officina 1 (L, U, Z, omega × 3 spessori):
l'accorciamento per piega è una **costante pura** di (spessore, apertura
cava, angolo), identica tra le forme entro 0.00005 mm. NON dipende dalla
lunghezza delle flange, dal numero di pieghe o dalla forma. Quindi nessun
effetto di forma, nessuna regione-arco da modellare: somma e sottrazione.

### D3 — Tre regole di piega, il k-factor fisso non è una regola a sé ✅ (parziale)

Le regole per calcolare l'accorciamento sono tre: **din6935** (la norma,
calcolo da manuale, default per chiunque), **misurati** (i numeri veri di
un'officina dai suoi `.bnc`; dove manca la combinazione, ripiega su
din6935), **inside_sum / somma_interni** (somma le quote interne, raggio 0,
nessuna correzione — la prassi radicata di moltissime carpenterie). Motivo
di fondo (da `appunti.md`): per l'adozione reale conta di più matchare le
quote del cliente che avere ragione in teoria. Lo standalone "k-factor
fisso" che c'era in `bend.py` NON si tiene come regola separata: din6935 lo
generalizza (fibra neutra mobile) ed è un suo caso particolare. Stato:
`din6935` implementata in `unfold/deduction.py`; le altre due da completare.

### D4 — Configurazione = un file profilo JSON per officina ✅

Un **profilo** (`profiles/<nome>.json`) porta le scelte di calcolo di
un'officina; si cambia profilo, non il motore. `profiles/default.json`:
regola din6935 + tabella "spessore → cava" (cava ≈ 8 × spessore), va su
git. `profiles/officina_1.json`: regola misurati, valori dai `.bnc`,
fallback din6935, **NON va su git**. Il default corrente è `officina_1`
(scelta di Federico) ma è una riga di config, non è cablato, e il fallback
interno è sempre din6935.

### D5 — Niente ereditarietà fra profili: un profilo = un file completo ✅

Prima `officina_1.json` ereditava la tabella cava da `default.json`
(`"eredita": "default"`). Tolto (Fase 2, set 2026): per sapere cosa fa un
profilo dovevi aprire due file e fonderli a mente. Ora ogni profilo porta
tutto — regola, `cava_per_spessore`, eventuali `misurati`. `officina_1.json`
ha la sua copia della tabella cava standard. Costo accettato: se la tabella
standard cambia, si aggiorna in più file (succede di rado). Rimossi da
`unfold/deduction.py` `genitore` / il walk di `_campo`; `scripts/genera_profilo.py`
ora copia la tabella di `default` dentro il profilo generato. Federico:
"appiattisci, così non ci pensiamo più".

### D6 — Il cognome di Federico non si scrive MAI ✅ (permanente)

Né in chat né in file, path, nomi di profilo o commenti. La sua officina è
**"officina 1"** (`officina_1`). Vale anche a ritroso: se lo si trova in
file scritti da noi, si toglie.

### D7 — Schema di naming dei pezzi di test / dime ✅

`FORMA` + coppie `segmento`/`angolo` + `s<spessore>`. Esempio
`Ua60ab90b110bc90c60s3`. I segmenti sono misure **a mezzeria**, da apice
virtuale ad apice virtuale; sono gli stessi numeri passati a
`BentProfile.flanges`. Angoli: piatto = 180, su = 90, giù = 270. Nessun
raggio nel nome (dipende da matrice/punzone, è produzione, non sketch).
L'omega sfrutta la simmetria (3 segmenti + 2 angoli invece di 5 + 4).
La quota esterno-esterno `H` NON entra nel nome: è derivata dallo sketch.

### D8 — Una dima = solo il profilo pieno, niente mezzeria disegnata ✅

La dima contiene solo il contorno a spessore. La mezzeria si deduce
offsettando le due facce di sp/2 verso l'interno. Motore in
`unfold/dima.py` (`Dima`).

### D9 — Le dime non hanno utilità matematica ✅

Il segnale triplo (D10) basta a riconoscere la lamiera piegata. Le dime
servono all'occhio e per costruire il viewer per l'occhio umano; sono
parametriche. Vivono in `data_4_cloude/dime/` (`.dxf` + `.json`), **non
versionate**, rigenerabili con `python scripts/generate_dima.py`. Un file
per dima.

### D10 — "È lamiera piegata" = segnale triplo ✅

Facce parallele a distanza costante (= spessore candidato) + quello
spessore presente in `sheet_thicknesses.json` (lamiera che esiste davvero)
+ spigoli curvi come coppie di archi concentrici con differenza raggi
esattamente == spessore. Implementato in `unfold/interpret.py`
(`interpret_section`), che fa anche l'inverso di `Dima` (dalla sola sezione
ricava spessore, segmenti a mezzeria, angoli, in forma canonica fra le due
letture speculari). Giro chiuso verde sulle 12 dime, segmenti entro
0.05 mm.

### D11 — `inner_radius` = 1 mm fisso per le dime di prova ✅

Uguale per ogni spessore (raggio minimo simbolico). Il raggio a mezzeria si
deriva (`inner_radius + sp/2`). Il raggio **non entra** nel calcolo dello
sviluppo — quello lo decide il profilo officina dalla cava; serve solo al
pattern di riconoscimento. Su una vista reale il raggio può essere
qualsiasi.

### D12 — `dima_da_pezzo(bnc, dxf)` (Fase 1) NON è API pubblica ✅ (fatto)

Chi ha già un `.bnc` e un DXF piatto ha già lo sviluppo: non lo ripassa nel
codice, usa quelli. Lo strumento serve solo a noi: generare i golden test
per officina 1 e, più avanti, capire/sviluppare le scatole. Vive in
`tests/reconstruct.py`, mai in `unfold.__all__`. NON usa `interpret_section`
(quello legge sezioni, un DXF piatto è il pezzo già disteso). Verifica a
giro chiuso in `tests/test_reconstruct_officina.py`.

### D21 — Il verso della piega si legge dal layer del DXF piatto ✅

Nei DXF TruBend piatti la linea di piega sta sul layer `Bend` (piega "in
su", 90 nello schema nomi) o `MBend` (piega "in giù", 270). Verificato sui
nomi dei file: `Za60ab90b100bc270c50...` ha la prima piega su `Bend`, la
seconda su `MBend`; l'omega `Oa...ab90b...bc270...cd270...de90...` fa
`Bend, MBend, MBend, Bend`. Così `dima_da_pezzo` ricostruisce la Dima
completa (segmenti **e** verso) dal solo DXF piatto; il `.bnc` serve solo
per l'accorciamento e per la lunghezza sviluppo di controllo.

### D22 — Fase 1 copre la piega a un asse; il numero di colpi è irrilevante ✅

Fase 1 lavora sulla geometria del pezzo finito: quante volte la pressa ha
colpito per formare un angolo non conta. L'omega da 10 mm di officina 1 è
fatta con una pre-piega (`.bnc`: 5 colpi, il primo a 120°, per 4 pieghe
geometriche); `dima_da_pezzo` scarta la pre-piega (angolo diverso da quello
geometrico finale) e il giro chiude come per gli altri (202.995 vs 203.0).
Tutti e 20 i provini L / U / Z / omega × spessori chiudono entro 0.01 mm.
Restano fuori da Fase 1 (→ Fase 4) solo scatole e pieghe su più assi.

### D13 — Tolleranza dei golden: 0.01 mm per `officina_1`, 0.1 mm per `din6935` ✅

Col profilo `officina_1` l'accorciamento è il valore misurato esatto preso
dai `.bnc`, quindi il giro chiuso deve tornare alla precisione
dell'arrotondamento — "sennò i dati a che pro li abbiamo presi". Il margine
di 0.1 mm vale solo per i golden `din6935`, che è una formula con errore
residuo dichiarato onesto.

### D14 — Non rigenerare un golden per far passare un test ✅ (permanente)

Se un golden fallisce, prima si prova che il codice è corretto, poi
eventualmente si rigenera il fixture. Mai il contrario. Quando una
decisione cambia legittimamente l'output, si rigenerano i golden uno per
uno con verifica del diff a mano.

### D15 — Codice nuovo in inglese, documenti in italiano ✅ (da set 2026)

Nomi di funzioni, classi, variabili, file di test in inglese, come su
forge. Il codice italiano esistente (`Profilo`, `deduction.py`,
`accorciamento_mezzeria`, `BentProfile`...) resta com'è finché non si
tocca. I documenti (`PIANO.md`, `TODO.md`, `DIME.md`, `appunti.md`,
`COME_FUNZIONA.md`, questo file) restano in italiano.

### D16 — Impostazione sulle skill: il refactor grosso dopo la Fase 2 ✅ (deciso 4 set 2026)

Il layout a strati (`adapters/`, `core/`, `model/`, `rules/`, `io/`), gli
script numerati alla radice, `docs/API.md` + `docs/ARCHITECTURE.md` +
README doppio: tutto sì, ma **dopo** la Fase 2, quando si sposta roba già
capita. Spostare tanti moduli in fretta è ciò che ha fatto sentire
`unfold` non suo a Federico. Adesso solo tre pulizie piccole (D17 + `MAP.md`
+ script numerati).

### D17 — La versione vive solo in `pyproject.toml` ✅ (4 set 2026)

`unfold/__init__.py` la legge a runtime con
`importlib.metadata.version("unfold")`, ripiego `"0.0.0+dev"` se il
pacchetto non è installato. Nessun numero duplicato nel codice.

### D18 — I dati cliente fuori da GitHub ✅

`.bnc`, DXF TruBend e tutto `data_4_cloude/` sono dati veri di officina 1:
`.gitignore` li esclude. Perfetti per la sua officina, non una verità
universale.

### D19 — Cono / cilindro: diametri esterni, sviluppo sulla fibra media ✅

I diametri passati a `Cone` / `Cylinder` sono **esterni**. Lo sviluppo è
calcolato su `D_medio = D_esterno − thickness`.

### D20 — Golden solo su coppie matrice/spessore in range ✅

Regola della piega ad aria: l'apertura V della matrice sta tra 6 e 10 volte
lo spessore. I provini fuori range (es. L da 10 mm fatta con V16 → V/T =
1.6, fisicamente irrealizzabile) TruBend li calcola comunque ma il numero
non rappresenta una piega reale: restano come riferimento "perché non
torna", non come dato di calibrazione.

### D24 — Il calcolo di ogni piega è un oggetto interrogabile: `BendResult` ✅

`BentProfile.develop()` non spargeva più i risultati per-piega in liste
parallele dentro `meta` (`k_factors`, `bend_allowances`,
`centerline_setbacks`, `centerline_deductions`): da quelle liste non si
vedeva quale numero veniva da dove. Ora ogni piega è una `BendResult`
(`unfold/bend.py`) in `flat.bends`: `angle`, `cava` usata, `deduction` (a
mezzeria), `setback`, `rule` (`misurati` / `din6935` / `inside_sum` /
`manuale`), `source` (in chiaro: `data_4_cloude/L/L3.bnc`, oppure
`DIN 6935 (raggio ... da cava ...)`), `fallback` (True quando chiedeva
`misurati` e ha ripiegato su DIN — il segnale "no data → din6935" che
Federico voleva vedere ogni volta). Sotto, `Profilo.deduction_detail()`
ritorna un `DeductionInfo`; `accorciamento_mezzeria()` resta come scorciatoia
al solo numero. Principio generale salvato nella skill `stile-codice-python`
("interrogabilità per comprensione"). `meta` tiene solo i valori di profilo
(`flanges`, `thickness`, `width`, `material`, `total_length`).

### D23 — Pacchetto di rinomine, da fare in blocco ✅ (fatto 4 set 2026)

Emerse in Fase 2, decise a parole, applicate in blocco a fine Fase 2. In
inglese (D15):

| prima | dopo | perché |
|---|---|---|
| `profiles/` + classe `Profilo` | `calibrations/` + `Calibration` | "profilo" era ambiguo con `BentProfile` (il pezzo piegato) |
| `Dima` / `dima.py` / `data_4_cloude/dime/` | `Section` / `section.py` / `data_4_cloude/sections/` | una dima è la **sezione** di un pezzo piegato; `Dima` ha già un campo `.shape`, quindi `Shape` come nome di classe è escluso |
| (il giro a mano in `tests/reconstruct.py`) | metodo `Section.to_bent_profile()` | rendere esplicito il ponte forma→motore |

Applicato anche a cascata, per non lasciare metà nome vecchio e metà
nuovo: il parametro `BentProfile(profilo=...)` → `BentProfile(calibration=...)`;
`DIMA_INNER_RADIUS_MM` → `SECTION_INNER_RADIUS_MM`; `tests/reconstruct.py`
(`dima_da_pezzo` → `section_from_part`, `PartReconstruction.dima` →
`.section`); `05_compare_profiles.py` → `05_compare_calibrations.py`;
`scripts/generate_dima.py` → `scripts/generate_section.py`; `DIME.md` →
`SECTIONS.md`. Non toccati (fuori dallo scopo della decisione): i nomi dei
metodi già in italiano su `Calibration`
(`accorciamento_mezzeria`, `cava_per_spessore`, `carica`...) — quelli sono
"codice italiano esistente" (D15), si toccano quando serve, non per
inerzia della rinomina.

Nota architetturale confermata: il **verso** della piega (su/giù) vive in
`Section` (angoli 90/270), NON in `Bend`. Il motore (`BentProfile.develop()`)
è cieco al verso e resta così — lunghezza e posizione piega non ne
dipendono (D1). L'API umana di Fase 3 parla `Section`; da lì esce sia lo
sviluppo (via `BentProfile`, verso buttato) sia il disegno in sezione (via
`Section.section()`, verso usato). Passare la forma L/U/Z e dedurre il
verso è stato scartato: l'omega è su-giù-giù-su, non "alternata", e un
catalogo forma→pattern si rompe al primo pezzo fuori catalogo.

### D25 — `Cylinder.margin` taglia la circonferenza, non l'altezza ✅ (5 set 2026)

Prima versione: `margin` toglieva materiale sopra/sotto (lunghezza assiale),
pensato per la saldatura di testa fra due tronchi impilati. Federico lo
usa invece per la cucitura longitudinale del rotolo — i due bordi del
foglio piano che si affacciano quando lo arrotoli — quindi va tolto dallo
sviluppo/circonferenza, un mm per lato, non dall'altezza. Cambiato per
allinearlo a `Cone`, dove `margin` riduceva già l'angolo del settore (stessa
direzione fisica). Con `faceted=True` il taglio cade nelle due faccette
estreme (prima e ultima); se il margine è più grande della faccetta di
bordo, `develop()` solleva `ValueError` invece di produrre una geometria
inconsistente (stessa cautela già presente in `Cone._develop_faceted`).
`meta["height_cut"]` è sparito, sostituito da `meta["width_cut"]`
(`meta["width"]` resta la circonferenza PIENA, prima del margine — utile
insieme a `reference_entities`/`show_margin_reference=True` per disegnare il
foglio pieno tratteggiato accanto al taglio reale).

Nella stessa occasione, il default di `orientation` su `Cylinder` è passato
da `"horizontal"` a `"vertical"` (costruzione canonica, nessuno swap):
`"horizontal"` faceva sempre swap X/Y indipendentemente da quale dimensione
(altezza o circonferenza) fosse effettivamente più grande — per un cilindro
corto e largo (es. anello D150 × H25) il risultato era un foglio stretto e
altissimo, l'opposto di "orizzontale". Resta un parametro esplicito, non un
calcolo automatico basato sull'aspect ratio: chi lo chiama sa se vuole
l'altezza o la circonferenza sull'asse X.

---

## QUESTIONI CHIUSE (storico)

- *Le quote si misurano esterne, interne o a mezzeria?* → mezzeria (D1).
- *Il k-factor fisso è una delle regole di piega?* → no, din6935 lo
  generalizza (D3).
- *Dove vivono le dime, cartella committata o no?* → `data_4_cloude/dime/`,
  non versionate, sono solo prove (D9).
- *Una dima serve al calcolo dello sviluppo?* → no, il triplo check basta;
  servono all'occhio e al viewer umano (D9).
- *Il raggio entra nel nome della dima / nel calcolo?* → no e no (D11).
- *`dima_da_pezzo` è una funzione del prodotto?* → no, strumento interno
  per fixture (D12).
- *Come si sa il verso di una piega da un DXF piatto?* → dal layer
  `Bend` / `MBend` (D21).
- *Che tolleranza per i golden di officina 1?* → 0.01 mm (D13); la Fase 1
  chiude su tutti i casi validi a ~0.005 mm (solo l'arrotondamento del
  `.bnc` a 2 decimali).
- *Si fa subito il refactor a strati sulle skill?* → no, dopo la Fase 2
  (D16).

---

## Appunti Federico (grezzi, da sciogliere in decisioni)

- **Carpentiere (officina cliente): le quote che dà sono interne o a
  mezzeria?** `inside_sum` oggi dà 136 su una U 50/70/20; sommando le
  interne "a crudo" farebbe 140. Da chiarire con lui prima di fissare i
  default di `inside_sum`.
- **Tabella cava → spessore VERA di officina 1** — Federico la porta.
- **Reverse engineering delle pieghe da un DXF esistente** — fatto per il
  caso "DXF piatto TruBend + `.bnc`" in `tests/reconstruct.py` (Fase 1).
  Resta aperto il caso "DXF già fatto da un cliente, senza `.bnc`": capire
  quale convenzione di sviluppo ha usato chi l'ha disegnato.
- **Info di piega nei DXF TruBend** (Fase 5): il verso di ogni piega è nel
  layer `Bend` / `MBend` (D21). Manca l'angolo quando non è 90° —
  reimportando in TruBend un suo DXF il software lo riconosce lo stesso:
  indagare dove sta (xdata?) quando c'è un DXF reimportabile con angoli
  diversi da 90.
- **Allineamento viste**: va calcolato ESTERNAMENTE a forge; probabilmente
  non fa parte nemmeno di questo layer di unfolding, vive di vita propria.
- **`COME_FUNZIONA.md`** è una bozza scritta da Claude, con qualche
  disallineamento rispetto al codice attuale (nomi delle regole, firma di
  `Bend`): da rileggere e correggere, poi confluirà in
  `docs/ARCHITECTURE.md`.
