# TUTORIAL — percorso per imparare (o rimparare) `unfold`

Non è un altro posto per le stesse informazioni (quelle restano dove sono:
`MAP.md` le decisioni, `TODO.md` il lavoro aperto, `SCRIPTS.md` l'indice
degli script) — è solo un ORDINE consigliato per attraversarle, con una
domanda a cui rispondere ad ogni tappa. Ogni tappa è uno script già
scritto: si apre, si fa girare (bottone Run di VS Code, o `python
NN_nome.py` dalla radice del repo), si legge l'output, si guarda il DXF se
c'è. Nessuno di questi script è "prodotto finito" — sono la palestra
(vedi `SCRIPTS.md`), quindi va benissimo modificare i numeri dentro e
rifarli girare per vedere cosa cambia.

## 0. Il modello mentale, prima di tutto

Leggi `README.md` (inglese) o `README_IT.md` (italiano, stesso contenuto):
ora copre tutta l'API — `Cone`/`Cylinder`, `Bend`/`BentProfile`, `Section`,
il layer umano, `export_part`. Restano da scrivere `docs/API.md` e
`docs/ARCHITECTURE.md` (vedi `MAP.md` D16). Quello che conta restare in
testa:

- `unfold` calcola, non disegna: ogni `.develop()` ritorna un
  `FlatGeometry` — dati Python puri (entità + numeri), zero dipendenze.
  Solo `.to_dxf()` tocca forge, e solo se lo chiami tu.
- Il motore calcola sempre a **mezzeria** (centro spessore), mai a quote
  esterne o interne — è la decisione fondativa, `MAP.md` D1. Tienila a
  mente: spiega perché serve un "layer umano" sopra per chi lavora a
  quote esterne (le tappe 6+ sotto).
- Il pacchetto è a strati: `model/` (dati puri) → `core/` (motore) →
  `rules/` (regole di calibrazione) → `human_layer.py` (li incolla per
  chi non vuole vedere la mezzeria) → `io/` (unico punto che sa di forge).
  Non serve saperlo a memoria per usare la libreria, ma spiega perché un
  import viene da un posto piuttosto che un altro.

## 1. Forme avvolte: `Cone`, `Cylinder`

- `00_cone_cylinder.py` — lo sviluppo liscio di un cono e un cilindro.
  Guarda i DXF in `output/`. Nota i diametri: sono ESTERNI in ingresso,
  lo sviluppo è calcolato sul diametro medio.
- `01_faceted.py` — la stessa cosa ma sfaccettata (per chi non ha la
  calandra): N facce piane + linee di piega.
- `02_compare_cone.py` — liscio vs sfaccettato, stesso cono, confronto
  numerico fianco a fianco.
- `03_margin_orientation.py` — i due parametri di layout: `orientation`
  (quale asse è il lato lungo del foglio) e `margin` (saldatura tolta in
  parti uguali).

**Cosa dovresti saper rispondere alla fine**: perché i diametri sono
esterni e cosa cambia se il tuo cliente li dà interni.

## 2. Profili piegati a pressopiega: `Bend`, `BentProfile`

L'idea, tutta qui: un pezzo piegato è **lati + angoli**. Il piano da
tagliare è più corto perché ogni piega "mangia" materiale (l'**accorciamento**).
Quanto mangia dipende solo da spessore, cava, angolo (`MAP.md` D2).

C'è **una formula sola** (`COME_FUNZIONA.md`, "La formula"). Le servono il
raggio interno `r` e il fattore `K` (dove sta la fibra neutra). Li porta la
**calibrazione**, un file con: la tabella "spessore → cava" (da cui
`r ≈ cava/6`), eventualmente il `K` per materiale, eventualmente gli
accorciamenti già **misurati** (`MAP.md` D33). Punti da tenere a mente:

- **Non devi impostare niente per partire**: se non dici nulla, la
  calibrazione è `"default"` — non indovina nessuna cava (tabella tutta a
  `null`, `MAP.md` D36), usa un raggio fisso dichiarato (1 mm) e il `K` lo
  stima DIN 6935 dal rapporto raggio/spessore. `flat.bends[i].source` dice
  sempre da dove viene il numero — mai un valore travestito da reale.
- **La cava, se la dai, la sceglie la tabella** per spessore (`r ≈
  cava/6`, più preciso del raggio fisso). La passi sulla piega
  (`Bend(angle=90, cava=20)`) solo se quel pezzo è stato piegato con una
  cava fuori standard.
- **Il raggio in ordine di bontà**: esplicito (`Bend(radius=...)`, per
  bombato/coniatura) → dalla tua cava → fisso 1 mm dichiarato se non sai
  né l'uno né l'altra.
- **Il `K` in ordine di bontà**: misurato per quella combinazione → il tuo
  `k_per_materiale` → stima DIN 6935.

Quattro casi ricorrono sempre, e ogni default del progetto si controlla
contro tutti e quattro (`MAP.md` D36, dettaglio in `COME_FUNZIONA.md`):
uno sconosciuto che non configura niente (→ `default`), una carpenteria
che dà solo le sue cave vere senza misurare nulla (→ tabella cave propria),
una che vuole solo la somma delle quote interne (→ `inside_sum`), una con
CAM che vuole avvicinarsi il più possibile per preventivare (→ `misurati`).

Script:

- `04_bend.py` — una squadra a L sviluppata con quattro calibrazioni
  (`default`, `esempio_din_3cave`, `tipo_misurato`, `inside_sum`) fianco a
  fianco, confrontate con lo sviluppo vero del `.bnc`. Guarda per ogni riga
  cosa ha usato (misurato / stima DIN) e con che cava.
- `05_compare_calibrations.py` — la stessa idea su tutti e 20 i pezzi di
  test reali: sviluppo REALE (TruBend) vs `default` (stima) vs
  `tipo_misurato` (misurato).

Se un numero non torna, `COME_FUNZIONA.md` ha il dettaglio (la formula, la
stima DIN 6935, come si scrive una calibrazione cliente) — leggilo quando
ti serve il PERCHÉ, non prima.

**Cosa dovresti saper rispondere alla fine**: la formula e da dove vengono
`r` e `K`; la scaletta del `K` (misurato → per materiale → DIN); perché lo
sviluppo è sempre "somma lati meno accorciamenti" (`MAP.md` D2)
indipendentemente dalla forma.

## 3. Il pezzo piegato visto come sezione: `Section`

Prima di andare oltre, guarda `SECTIONS.md` e `unfold/model/section.py`
(la docstring in cima, non tutto il file): `Section` è il modello che
porta il VERSO di ogni piega (su/giù, non solo l'angolo) — cosa che
`BentProfile` deliberatamente non sa (`MAP.md` D1/D23). `tests/
generate_section.py` mostra i pezzi golden (L/U/Z/O) con cui è stato
verificato tutto il resto: aprine uno per vedere `segments`/`angles` veri.

**Cosa dovresti saper rispondere alla fine**: perché il verso vive in
`Section` e non in `Bend`, e cosa cambia fra un angolo "90" e uno "270"
nella naming scheme.

## 4. Il layer umano: quote ESTERNO-ESTERNO invece che a mezzeria

Qui si comincia a lavorare come farebbe un carpentiere: quote lette
sull'esterno del pezzo, non a mezzeria.

- `06_external_quotes.py` — il traduttore `external_flanges_to_centerline()`
  / `centerline_to_external_flange()` su una L, andata e ritorno. Il
  punto chiave (dimostrato in `MAP.md` D28): l'offset esterno↔mezzeria
  NON dipende dal raggio di piega.
- `07_compare_calibrations_external.py` — la stessa L, stesse tre
  calibrazioni della tappa 2, ma partendo da quote esterne.
- `08_human_layer.py` — `develop_from_external_flanges()`: la stessa cosa
  di 06+07 ma in una funzione sola, senza mai vedere la mezzeria da fuori.

**Cosa dovresti saper rispondere alla fine**: perché l'offset esterno↔mezzeria
non dipende dal raggio (prova a rifare il conto a mano su un foglio, è due
righe di trigonometria).

## 5. La vista in sezione, quotata

- `09_section_view.py` — `Section.from_external_flanges()` +
  `flange_quotes()` + `to_dxf()`: il disegno del pezzo PIEGATO (non
  sviluppato) con una quota per flangia. Guarda i DUE casi: la L (tutte
  le quote sono "esterno") e la Z (la flangia centrale esce dichiarata
  "a mezzeria" — apri il DXF e leggi il testo della quota).

Il punto da capire bene qui è geometrico, non di codice: una flangia ha
una faccia esterna coerente solo se le due pieghe adiacenti girano nello
STESSO verso (`MAP.md` D1/D31) — vero per L/U, falso per l'anima di una Z
o di un'omega. Prova a costruire tu una `Section` per un'omega
(4 flange, 3 pieghe: su-giù-giù-su) e a chiamare `flange_faces()`: indovina
prima quali flange risultano ambigue, poi controlla.

**Cosa dovresti saper rispondere alla fine**: perché non è mai un'ambiguità
silenziosa — cosa dice esplicitamente la quota quando la faccia esterna
non c'è.

## 6. L'export finito: un solo file, a livelli

- `10_export_part.py` — `export_part()`: taglio (sempre) + vista in
  sezione quotata (opzionale) + header (opzionale), impilati in verticale
  in un unico DXF. Apri `10_export_full.dxf` e guarda come sono disposti
  i tre blocchi, uno sotto l'altro, allineati a sinistra.

**Cosa dovresti saper rispondere alla fine**: perché la vista in sezione,
qui dentro, non passa da `forge.heal_and_detect()` come il taglio (`MAP.md`
D32) — cosa succederebbe se lo facesse.

## Da qui in poi: i riferimenti, non un percorso lineare

- **`MAP.md`** — tutte le decisioni con il perché, in ordine cronologico
  (D1, D2, ...). Non va letto tutto: quando una tappa sopra cita una
  decisione, è quella da leggere, non l'intero file.
- **`TODO.md`** — cosa manca ancora, in ordine di priorità.
- **`SCRIPTS.md`** — l'indice di tutti gli script (tabella script → area
  API → cosa mostra), utile come mappa quando questo percorso finisce e
  serve solo un ripasso mirato.
- **`tests/`** — la specifica eseguibile. Se un pezzo di questo percorso
  non torna, il test corrispondente (stesso nome dell'area, es.
  `tests/test_section.py` per la tappa 5) mostra esattamente cosa deve
  valere, con `assertAlmostEqual` invece di parole.

Un'ultima cosa, non tecnica: ogni tappa sopra chiude con un numero o un
comportamento che deve tornare (`MAP.md`, "regola del gioco") — se
cambi un input e il risultato non ti convince, è lì che vale la pena
fermarsi, non andare avanti.
