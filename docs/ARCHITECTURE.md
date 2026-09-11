# ARCHITECTURE — come è fatto `bendly`, e come si incastra col resto

Questo file spiega il flusso e i confini fra i pezzi (forge, framer,
bendly, pippo) — non ripete l'API (quella è `docs/API.md`, da scrivere)
e non ripete le decisioni (quelle sono `MAP.md`). Se riapri il codice fra
un mese e non si capisce più niente, il punto di partenza è questo file,
non il codice.

---

## I quattro pezzi, in una frase ciascuno

- **forge** — motore 2D generico: legge un file CAD (DXF/PDF), lo ripara
  (`heal`), trova i contorni chiusi e li raggruppa in cluster con
  gerarchia esterno/interno (`detect`). Non sa cosa sia la lamiera, i
  fori, le pieghe — vede solo geometria e ruoli generici (`outer`,
  `inner`, `hole`, ...).
- **framer** — repo sorella, già in sviluppo. Capisce in un disegno
  dov'è la cornice e il cartiglio (altrimenti `heal` la vede come un
  `outer` normale e falsa tutto quello che viene dopo), estrae le
  informazioni semantiche del cartiglio e le passa a pippo.
- **bendly** (questo repo) — sa cosa sia la lamiera piegata. Due lavori:
  **calcolare** uno sviluppo da parametri (`Cone`, `Cylinder`,
  `BentProfile`) e **leggere** un contorno per capire se è lamiera
  piegata e con che misure (`read_section`).
- **pippo** — non ancora scritto, vive fuori da questo repo.
  L'interprete di disegno: prende un file CAD intero, usa framer per
  togliere la cornice dal conto e forge per trovare i cluster, e per
  ciascuno decide cosa fare — fra cui chiedere a
  `bendly.read_section()` "in questo cluster c'è lamiera piegata?".
  Il nome è deciso l'11 set 2026 (prima non ne avevamo uno, e infatti
  confondeva).

```
file CAD (DXF/PDF)
      |
      v
  forge.load_dxf() / load_pdf()
      |
      v
  framer  -- toglie cornice/cartiglio dal conto, PRIMA di heal --
      |     (framer legge il disegno grezzo: una cornice ha una firma
      |     sua — un rettangolo enorme rispetto al resto, spesso su un
      |     layer/blocco a parte — che va riconosciuta prima che heal la
      |     tratti come un outer normale, non dopo su un risultato che
      |     l'ha già mischiata dentro. Se framer sbagliasse questo
      |     ordine, andrebbe deciso lì, non qui)
      |
      v
  forge.heal_and_detect()  ->  ForgeResult { clusters: [...] }
      |                             ognuno con .outer (ForgeContour,
      |                             .segments ordinati) e .inners
      v
   PIPPO   -- per ogni cluster che sembra una vista di lamiera --
      |
      v
  bendly.read_section(...)  ->  SectionReading
      |                             is_sheet_metal, is_bent, thickness,
      |                             centerline_segments/angles OPPURE
      |                             pure_arc_radius/pure_arc_angle_deg
      v
   PIPPO decide: costruisce un BentProfile/Cylinder/Cone con quei
   numeri, o scarta il cluster (non è lamiera), o segnala "non capito"
   (reading.notes)
```

**Pippo è una pipeline o un oggetto?** Una pipeline, per come è disegnato
sopra — un flusso file→forge→pippo→bendly, non uno stato che vive a
lungo. Ma "pipeline" non vuol dire "funzione unica": dentro, cammina i
cluster e per ciascuno costruisce un piccolo referto (candidato lamiera,
scartato, non capito) — quello sì può essere un oggetto per cluster,
accumulato in un risultato finale interrogabile (stesso principio di
`SectionReading`: un oggetto tipizzato, non un dict sparso). Non è ancora
deciso per davvero — pippo non esiste — ma se dovessi scommettere è
questa la forma: pipeline all'esterno, oggetti-risultato all'interno.

---

## Cosa riceve pippo da bendly, oggi

`read_section()` ritorna un `SectionReading` — un dataclass
interrogabile, non un dict sparso (vedi `python-code-style`: i risultati
sono oggetti tipizzati). Pippo lo legge così, in ordine:

| campo | pippo lo usa per |
|---|---|
| `is_sheet_metal` | **il cancello**: se `False`, questo cluster non è lamiera, pippo passa oltre. |
| `is_bent` | `True` = profilo piegato o arco calandrato; `False` = lamiera piatta (taglio, non piega). |
| `thickness` | lo spessore riconosciuto (o `None` se il segnale non c'è). |
| `centerline_segments` + `angles` | **solo se è un profilo a flange dritte** (L/U/Z/omega) — stesso formato che `BentProfile(segments=..., angles=..., thickness=...)` già accetta. Vuoti se non è questo il caso. |
| `pure_arc_radius` + `pure_arc_angle_deg` | **solo se è un arco puro senza flange** (sella calandrata, MAP.md D42) — pippo li passa a `Cylinder(sector_angle=...)`/`Cone`, non a `BentProfile`. `None` se non è questo il caso. |
| `notes` | perché il riconoscimento non è riuscito del tutto (spessore fuori tabella, centerline non ricostruita, ...) — diagnostica per un umano o per pippo che decide di scartare/segnalare. |

Regola pratica per pippo: **mai più di uno fra i due gruppi di misure
valorizzato insieme** — o è un profilo a flange (primo gruppo), o è un
arco puro (secondo gruppo), o nessuno dei due (`notes` dice perché).

## Cosa manda pippo a bendly, oggi

`read_section(entities: List[dict], ...)` prende in ingresso una
lista di dict grezzi (`{"type": "line", ...}`) — lo stesso schema che
`Cone`/`Cylinder`/`BentProfile` producono generando, e che
`forge.load_geometry()` accetta come "geometria da un generatore"
(MAP.md D43). `bendly` non importa forge da nessuna parte tranne
`io/dxf.py`, lettura compresa — provato il contrario per una notte
intera (D43), tornato indietro: non perché non funzionasse (167/167
verdi anche lì), ma perché decidere QUEL contratto oggi vorrebbe dire
indovinare cosa vorrà pippo, che non esiste ancora. Se pippo arriverà con
già in mano `cluster.outer.segments` di forge (probabile, se usa
`heal_and_detect()` per i cluster) e fargli ricostruire dict grezzi da
lì sarà uno spreco visibile, si riapre la domanda allora — con pippo
vero davanti, non immaginato.

---

## Layer di `bendly`, dipendenza in una direzione sola

```
core/        matematica di piega pura (Bend, K-factor, DIN 6935)
             ZERO dipendenze — non importa forge, non importa niente
             sopra di lui
model/       Section, FlatGeometry — struttura dati di dominio,
             ancora senza forge
rules/       deduction.py + read_section.py — entrambi puri, zero forge
io/          dxf.py — UNICO posto che importa forge, per scrivere
human_layer  API pubblica di comodo (quote esterne, export a livelli)
```

Ogni layer può dipendere solo da quelli sopra di lui in questa lista,
mai il contrario. `core/` non sa che forge esiste, punto — qualunque
codice nuovo che gli farebbe importare forge è nel posto sbagliato.

## Cosa espone `bendly`, per chi ci costruisce sopra

Non solo una pipeline chiusa (`develop_from_external_flanges()`,
`export_part()`) — anche i pezzi sciolti, per chi vuole comporli da sé
(stesso spirito di `ezdxf`/`shapely`: oggetti tipizzati in mano al
chiamante, non solo funzioni-scatola-nera). Già veri oggi, non solo
un'intenzione — `Cone` stesso li usa così internamente, non solo un
esterno ipotetico:

- `Bend` — una piega sola, riusabile senza `BentProfile` attorno
  (`Cone`/`Cylinder` sfaccettati già lo fanno per le proprie pieghe).
- `Calibration`, `k_din6935`, `deduction_din6935` — la matematica del
  K-factor da sola, per chi vuole solo quella.
- `Section`, `FlangeFace`, `FlangeQuote` — il layer a quote umane, senza
  passare per forza da `develop_from_external_flanges()`.
- `read_section()` → `SectionReading` — leggere un contorno senza
  costruire nessuna forma.
- `FlatGeometry` — entities/meta grezzi, per chi vuole la propria
  pipeline forge invece di `to_dxf()`.

Quello che mette in ritardo un "chi ci costruisce sopra" oggi non è
l'architettura (gli oggetti giusti ci sono già) — è che non c'è ancora
`docs/API.md`, la scheda per-oggetto (segnatura/prende/ritorna/solleva)
che fa risparmiare la lettura del sorgente. `MAP.md` D16, ancora aperta.

---

## Cosa non è ancora pulito (onesto, non nascosto)

- Il contratto di ingresso di `read_section()` (dict vs segmenti
  forge nativi) — deciso quando pippo esiste, non prima: decidere ora su
  un consumatore immaginario è il modo in cui è nata (e si è ritrattata)
  tutta la parentesi forge di MAP.md D43.
- Dove framer entra nel flusso rispetto a `heal()` (sopra, nel
  diagramma) — framer è una repo a sé, non ancora vista da qui: quando
  esiste per davvero questo file va corretto sui fatti, non tenuto come
  unica verità.
- `pippo` è un nome, non un repo — stesso discorso.
- `docs/API.md` non esiste ancora — `MAP.md` D16.
