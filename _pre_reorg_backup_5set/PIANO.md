# PIANO — dove siamo e dove andiamo (agg. 4 set 2026)

Questo è il file su cui Federico si basa. Gli appunti grezzi in maiuscolo
delle sessioni precedenti sono stati recepiti e sciolti qui dentro come
decisioni chiuse.

## Regole del gioco (non si cambiano in corsa)

- Prima si concorda il modello a parole, poi si scrive il codice.
- Ogni fase è piccola e si chiude con **una verifica numerica** (un numero
  che deve tornare).
- Il core (calcolo dello sviluppo **a mezzeria**) è già deciso: non si
  tocca. Tutto il nuovo lavoro gli sta intorno.
- Una cosa alla volta. Se un concetto non è chiaro, ci si ferma lì.
- Il codice nuovo è in **inglese** (funzioni, classi, test), come su
  forge. I documenti (questo, `TODO.md`, `DIME.md`, `appunti.md`,
  `COME_FUNZIONA.md`) restano in italiano.

---

## Impostazione del progetto sulle skill — quando

Da adesso il progetto si allinea alle skill di Federico (layout a strati
`adapters/core/model/rules/io`, script numerati alla radice, `docs/API.md`
+ `docs/ARCHITECTURE.md` + `MAP.md`, README doppio IT/EN).

**Il refactor grosso NON si fa adesso.** Spostare tanti moduli in fretta è
proprio ciò che ha fatto sentire `unfold` non suo a Federico. Il refactor
a strati si fa **dopo la Fase 2**, quando si sposta roba già capita.

Adesso solo tre pulizie piccole e a basso rischio:

1. ✅ versione letta da `pyproject.toml` a runtime (`importlib.metadata`)
   in `unfold/__init__.py` → `unfold.__version__`. 79 test verdi.
2. ✅ creato `MAP.md` — decision log (D1–D20) che raccoglie le decisioni
   già chiuse, così non si ri-decidono ogni sessione;
3. ✅ script di esplorazione rinominati in serie numerata `00_*.py`…`05_*.py`
   alla radice del repo + tabella in `SCRIPTS.md`. I due generatori
   (`generate_section.py`, `genera_profilo.py`) restano in `scripts/` per ora.

---

## FATTO — Fase 0 e primo pezzo di interprete (4 set 2026)

`unfold/section.py` (`Section`, si chiamava `Dima` fino alle rinomine D23)
+ `scripts/generate_section.py` + `unfold/interpret.py` +
`sheet_thicknesses.json` + `SECTIONS.md` + `tests/test_interpret.py`.

Decisioni chiuse:

- **una sezione = solo il profilo pieno**, nessuna linea di mezzeria
  disegnata: la mezzeria si deduce offsettando le due facce di sp/2 verso
  l'interno;
- le sezioni generate hanno **un solo raggio in entrata**, `inner_radius`
  = 1 mm fisso per ogni spessore (raggio minimo simbolico). Il raggio a
  mezzeria si deriva (`inner_radius + sp/2`) e non entra nel nome. Non
  tocca il calcolo dello sviluppo: serve solo al pattern di
  riconoscimento. In futuro, su una vista reale il raggio può essere
  qualsiasi — serve solo a capire se è lamiera piegata;
- **"è lamiera piegata" = segnale triplo**: facce parallele a distanza
  costante (= sp) + quello sp presente in `sheet_thicknesses.json` +
  archi concentrici con differenza raggi == sp;
- **le sezioni NON hanno utilità matematica.** Il triplo check basta a sé.
  Le sezioni servono all'occhio e per costruire il viewer per l'occhio
  umano. Sono sezioni parametriche, non una verità di calcolo;
- 12 sezioni generate (L/U/Z/O × sp 1/3/10) in `data_4_cloude/sections/`,
  `.dxf` + `.json`, **non versionate** (sono solo prove, rigenerabili).
  Un file per sezione va bene;
- `interpret_section()` fa l'inverso di `Section`: dalla sola sezione
  ricava spessore + segmenti a mezzeria + angoli. Giro chiuso verde su
  tutte e 12 (segmenti entro 0.05 mm). 79 test verdi;
- la sezione fatta a mano `La114ab90b114s3` è stata rigenerata, backup in
  `.fatta-a-mano.bak`.

---

## FASE 1 — Da DXF piatto + `.bnc` ai numeri della sezione — ✅ FATTA (4 set 2026)

`tests/reconstruct.py` (`section_from_part(bnc, dxf)`) +
`tests/test_reconstruct_officina.py`. Giro chiuso verde su tutti e 20 i
provini (L / U / Z / omega × spessori 1, 3, 10), tutti entro 0.01 mm (in
pratica ~0.005 mm, solo l'arrotondamento del `.bnc` a 2 decimali).
L'omega da 10 mm è fatta con una pre-piega (5 colpi per 4 pieghe): il
numero di colpi non cambia il pezzo né lo sviluppo, la pre-piega viene
scartata e il giro chiude come gli altri.

Novità utile emersa: il **verso** della piega si legge dal layer del DXF
piatto — `Bend` = su (90), `MBend` = giù (270). Così la Section si
ricostruisce completa dal solo DXF; il `.bnc` serve solo per l'accorciamento
e per la lunghezza di controllo. (Vedi `MAP.md` D21, D22.)

Il testo qui sotto resta come traccia di cosa è stato fatto.

---

**Cos'è e cosa NON è.** È uno **strumento interno**, non API pubblica.
Chi ha già un `.bnc` e un DXF piatto ha già lo sviluppo: non lo ripassa
nel codice, usa quelli. Questo strumento serve solo a noi, per:

- generare i **golden test per officina 1** (ricostruzione ↔ `.bnc`);
- più avanti, capire e sviluppare le **scatole**.

Sta in `scripts/` o in `tests/generate_*.py`, mai in `unfold.__all__`.

**Obiettivo tecnico.** Dato un pezzo reale TruBend (file `.bnc` + DXF
piatto), ricostruire lo sketch primitivo a mezzeria senza che nessuno
dica quale centerline è stata usata.

> Nota: NON si usa `interpret_section()` qui. Quello legge un disegno in
> **sezione** (dove si vede lo spessore). Un DXF piatto è il pezzo già
> disteso, lo spessore non si vede: è tutta un'altra funzione.

Cosa abbiamo, cosa manca:

- `trubend.py` legge già: spessore, lunghezza sviluppo (bounding box),
  matrice + V, e per ogni piega angolo + accorciamento (riferito a quote
  esterne). **Non** legge le quote delle singole flange.
- Il DXF piatto ha il contorno + le **linee di piega** (forge le tira
  fuori gratis).

Passi:

- **1.1** Dal DXF: contorno + posizioni delle linee di piega → lunghezze
  **piatte** di ogni flangia (distanze fra una linea di piega e l'altra,
  più le due estremità).
- **1.2** Da piatto a mezzeria: `flangia_mezzeria = flangia_piatta +
  accorciamento/2` per ogni piega adiacente. Ritorna una sezione, stesso
  formato della Fase 0. È un test in più, non una feature.
- **1.3** **Verifica a giro chiuso:** sezione ricostruita →
  `Section.to_bent_profile(calibration="officina_1").develop()` → la
  lunghezza sviluppo deve tornare quella del `.bnc` **entro 0.01 mm**. Con
  la calibrazione `officina_1` l'accorciamento è il valore misurato
  esatto: deve tornare alla precisione dell'arrotondamento, sennò i dati
  non servono a niente. (Il margine di 0.1 mm vale solo per i golden
  `din6935`, che è formula.) Test automatico: parte dalla L, poi la U se i
  dati ci sono.
- **1.4** Limite noto, scritto **nel** codice (non nascosto): su Z/omega
  la flangia centrale ha l'ambiguità di ± `sp·tan(angolo/2)`. La
  lunghezza sviluppo totale resta sempre esatta.

**Verifica Fase 1:** `section_from_part(bnc, dxf)` + test verde sulla L a
0.01 mm.

---

## FASE 2 — Leggere il motore insieme, riga per riga

**Questa è la fase che preoccupa di più Federico.** Non è una lezione e
non c'è codice nuovo. Si legge `bend.py` e `deduction.py` insieme,
ancorati a **una L con numeri veri**, un concetto per volta. Se un pezzo
non torna, ci si ferma lì e si torna indietro.

- **2.1** ✅ Lettura guidata di `BentProfile.develop()` sulla L: sketch a
  mezzeria → togli `accorciamento/2` per lato → somma.
- **2.2** ✅ Ereditarietà dei profili JSON tolta: un profilo = un file
  completo (`officina_1.json` ha la sua copia della tabella cava). Vedi
  `MAP.md` D5.
- **2.4** ✅ `BendResult` — ogni piega di `develop()` è un oggetto
  interrogabile: dice l'accorciamento, la regola usata e da dove viene il
  numero, con `fallback=True` quando ripiega su DIN 6935. Vedi `MAP.md`
  D24.
- **2.3** ✅ Federico ha rispiegato la catena a parole sue (segmenti a
  mezzeria → accorciamento dal profilo/DIN 6935 → somma), letta anche
  insieme la formula DIN 6935 riga per riga.
- **2.5** ✅ Pacchetto di rinomine `profiles`→`calibrations`,
  `Dima`→`Section` (`MAP.md` D23).

**Verifica Fase 2:** ✅ Federico ha rispiegato la catena del calcolo senza
guardare il codice.

**Obiettivo di questa fase:** sentire il motore suo. Dopo questa, il
refactor a strati sulle skill diventa facile.

---

## FASE 3 — Il layer umano (esterno-esterno + vista in sezione) — PARCHEGGIATA

Lasciata qui per ora. Si riprende dopo che la L gira a giro chiuso **e**
Federico sente il motore suo.

**Obiettivo:** un carpentiere dà quote **esterno-esterno** e riceve lo
sviluppo + il disegno del pezzo piegato quotato.

- **3.1** Traduttore `quote_esterne ↔ quote_mezzeria` (una funzione, due
  versi). Il core non cambia.
- **3.2** API pubblica su esterno-esterno:
  `sviluppo_da_quote_esterne(forma, quote, angoli, spessore, calibration)`.
- **3.3** **Vista in sezione:** disegno del pezzo PIEGATO (non
  sviluppato) con le quote di riferimento marcate — quale faccia, quale
  quota. Esce in DXF via forge.
- **3.4** Z/omega: nella vista in sezione si dice esplicitamente da che
  faccia è presa ogni quota. Qui la vista **non è un optional**.

**Verifica Fase 3:** dando le quote esterne di una L e di una U il
risultato torna uguale a partire dalla sezione a mezzeria.

---

## FASE 4 — Scatole / pieghe su più assi — PARCHEGGIATA

Idem: non adesso.

- **4.1** Da `.bnc`: lista completa delle pieghe (posizione, asse, verso,
  angolo) — quasi tutto già in `trubend.py`.
- **4.2** Modello "a stella": una faccia-base + sponde che partono a
  raggiera, nessuna flangia condivisa → sviluppo lato per lato.
- **4.3** Verifica su una scatola `.bnc` reale.
- **Fuori scope per ora:** spigolo piegato due volte, angoli condivisi.

---

## FASE 5 — Info di piega dentro i DXF TruBend — PARCHEGGIATA

Se si reimporta in TruBend un DXF uscito da TruBend, il software capisce
già a che angolo è piegata ogni linea e se su o giù. L'informazione è da
qualche parte nelle linee di piega (layer `Bend` / `Mbend`).

- **5.1** Indagare (quando c'è un DXF reimportabile sotto mano): angolo e
  verso stanno nel nome del layer, in xdata, o altrove. Capire se ci si
  può allineare o se conviene un pattern nostro.

---

## Ordine prossimo

1. ✅ Le tre pulizie di impostazione (versione via `importlib`, `MAP.md`,
   script numerati + `SCRIPTS.md`).
2. ✅ **Fase 1** — `section_from_part`, giro chiuso su L / U / Z entro 0.01 mm.
3. ✅ **Fase 2** — lettura guidata del motore (`bend.py` + `deduction.py`)
   ancorata a una L con numeri veri, formula DIN 6935 inclusa. Federico
   sente il motore suo. Rinomine D23 fatte.
4. Il refactor a strati sulle skill (D16), poi Fase 3 (layer umano).

Fasi 4, 5 restano parcheggiate oltre.
