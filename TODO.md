# TODO — cosa manca, in ordine

Unico posto per il lavoro aperto. Le decisioni e il perché stanno in
`MAP.md`; qui non si ripetono, si rimanda con "vedi `MAP.md` D...".

## Fatto stanotte, non ancora in cima al file (MAP.md D45)

- [x] `Cone`/`Cylinder(faceted=True)` usano la `Calibration` dell'officina
  per raggio/K dei giunti (come `BentProfile`), non più una tabella per
  materiale a parte. `flat.bends` popolato anche lì (una `BendResult`
  per giunto). Cambia il default del raggio quando `facet_bend_radius`
  non è dato (prima `= thickness`, ora dalla calibrazione — 1mm fisso
  per chi usa `"default"`, MAP.md D36). 6 test nuovi, 173/173 verdi.
  `MATERIAL_K_FACTORS`/`estimate_k_factor` orfani dal percorso di
  default, ancora pubblici — da decidere se tenerli o ritirarli.

## Priorità di fondo (MAP.md D36/D39)

La formula generica è il prodotto; i dati misurati di un'officina sono un
bonus/banco di prova, mai un blocco. Ogni scelta di setup/default si
controlla contro questi quattro casi, sempre gli stessi — nome standard
`tipo_cliente` (campo verificato da codice, `tipo_cliente_coerente()`):

| `tipo_cliente` | Chi è | Cosa gli si chiede |
|---|---|---|
| `zero_config` | sconosciuto, scarica e basta, non legge nulla | niente — zero config, `calibration="default"` |
| `cava_propria` | carpenteria vicina, mi contatta, niente CAM | solo la tabella spessore→cava (5 minuti, mai una misura) |
| `somma_interna` | vuole solo somma quote interne, zero K-factor | niente — `calibrations/inside_sum.json` |
| `misurato` | ha il CAM, vuole avvicinarsi per preventivare | cava + tutti i dati misurati che il CAM tira fuori, **quando li ha** — mai un prerequisito per gli altri tre |

Una scelta che serve bene `misurato` ma appesantisce o blocca gli altri
tre è quasi sempre la scelta sbagliata. Niente viene più parcheggiato "in
attesa di altri `.bnc`": o si trova una via generica, o si dichiara il
limite e si va avanti (vedi MAP.md D36).

## Fatto (fasi 1-3.5)

1. ✅ Pulizie di impostazione, `MAP.md`, script numerati + `SCRIPTS.md`.
2. ✅ Fase 1 — `section_from_part`, giro chiuso su L/U/Z/omega entro 0.01 mm.
3. ✅ Fase 2 — motore a strati, `BendResult` interrogabile, rinomine EN.
4. ✅ Fase 3 — layer umano: quote esterne↔mezzeria, vista in sezione
   quotata, `export_part()` a livelli.
5. ✅ Fase 3.5 (D36) — priorità capovolta formula-generica-prima;
   `default.json` non indovina più cave (tutta a `null`); raggio fisso
   dichiarato (`DEFAULT_UNKNOWN_RADIUS_MM = 1.0`) quando cava e raggio
   sono entrambi ignoti.

## Prossimo

- [x] `COME_FUNZIONA.md` / `TUTORIAL.md` / `README.md` / `README_IT.md` —
  riallineati a D36 (raggio fisso dichiarato per il caso A, tabella dei
  4 casi A/B/C/D).
- [x] `docs/ARCHITECTURE.md` — scritto (11 set 2026): il flusso
  forge→pippo→unfold, cosa riceve/manda pippo da/a `read_section()`,
  i layer e la regola di dipendenza, cosa non è ancora pulito.
- [x] `docs/API.md` — scritto (11 set 2026), D16 chiusa: una scheda per
  ognuno dei 24 nomi di `unfold.__all__`, ogni esempio verificato
  girando davvero (non solo letto dal sorgente).

## Dati che arrivano quando arrivano — mai un blocco

- [ ] **`cava_per_spessore` VERA in `tipo_misurato.json`**: `CAVE_officina_1.txt`
  ha più V per lo stesso spessore (0,5 → V4/V6/V8; 4 → V20/V24; 6 →
  V30/V40; 8 → V40/V50; 10 → V50/V60; 12 → V60/V70; 15 → V70/V90). Serve
  che Federico dica la "standard" per ciascuno. Migliora solo il caso D
  su officina 1, non morde i test (ogni provino ha la sua combinazione
  esatta fra i `misurati`).
- [ ] **K per materiale (inox/allu)**: niente più placeholder (erano
  sbagliati, sotto ogni range pubblicato — tolti, MAP.md D37). Nessuna
  fonte generica di settore è affidabile per questo (verificato, D37): si
  scende alla stima DIN generica finché Federico non porta gli `.fx` con
  materiale cambiato. Non blocca nulla.
- [ ] **Prossimo giro di provini**, solo se/quando Federico li porta:
  spessori grossi (8–20 mm, dove la formula sbaglia di più) e non-90°
  aperti (120°/150°) a s2/s5/s8.

## Angolo non a 90° — fatto per gli aperti a una piega (MAP.md D38)

- [x] **1. Angolo incluso vero nel giro dei golden**, dal `Sollwinkel` del
  `.bnc` gemello — il layer DXF resta solo per il verso su/giù.
- [x] **2. Sei golden non-90° aperti**, `La114ab{120,150}b114s{1,3,10}`,
  nel giro golden + `tipo_misurato.json` (`misurati`). Chiuso entro 0.005 mm.
- [x] **3. Match misurato sull'angolo** — verificato: `rule="misurato"`
  su tutti e 6, non il fallback DIN.
- [ ] **4. Z/omega non a 90°.** Restano fuori. Causa capita (Federico,
  11 set): la seconda piega di una Z non va in appoggio — dopo la prima
  piega il pezzo non è più piatto, quella flangia non si posiziona più
  contro il riscontro nel ciclo automatico, quindi TruBend non la misura
  come un colpo normale e il `.bnc` non ha un `Biegeverkuerzung` pulito
  per lei (confermato su `Za60ab50b100bc250c50s10`: un solo `Biegenummer`
  registrato invece di due). Non è un dato mancante da noi, è un dato che
  non esiste alla fonte in forma misurata automatica. Serve un'altra via
  per quel numero (es. misura a mano sul pezzo finito) — non altro scavo
  nei `.bnc`.

## Piega chiusa / coniatura — limite dichiarato, non un buco da tappare

Un interprete che legge solo un disegno non può sapere se una piega verrà
coniata o piegata in aria — è una scelta di processo dell'officina,
invisibile nella vista. La risposta corretta è **assumere aria** (il caso
dominante, vedi `PIEGA_IN_ARIA_E_CONIATURA.md`) e dichiararlo, non
inseguire dati di coniatura all'infinito.

- [x] Confermato con dati veri (11 set, `La114ab{50,70}b114s{1,3,10}`):
  trattati come piega in aria, lo sviluppo ricostruito sbaglia di 2–5 mm.
  `reconstruct.is_reconstructable_name()` li esclude di proposito dai
  golden — non è un buco, è il limite dichiarato.
- [ ] Se Federico porta un punzone di coniatura + angolo di montaggio,
  quei golden si chiavano a parte (spessore, angolo, punzone) — bonus,
  non prerequisito.
- [ ] `Za60ab{50,70}...s{1,3,10}`: stessa famiglia (chiusi), dopo Z aperti.

## Lettura disegno → Cone/Cylinder/BentProfile (MAP.md D42)

`read_section()` (la "dima": rileva spessore da facce parallele/
archi concentrici) resta l'unico rilevatore — instrada verso una classe
esistente o l'altra, nessuna classe geometrica nuova. Ordine consigliato,
ogni pezzo piccolo e verificabile da solo:

- [x] **1. `Cylinder`: angolo di settore opzionale** (default 360°) —
  `width = radians(angle) × raggio_medio` invece di sempre `π×diametro`,
  stessa famiglia di formula del settore di `Cone`. Sblocca lo sviluppo
  di una sella calandrata (R300, 60°) senza nessuna lettura di disegno,
  solo passando l'angolo a mano — primo pezzo utile da solo. Fatto:
  parametro `sector_angle` (default 360, invariato per chi non lo tocca),
  `faceted=True` + settore parziale rifiutato esplicito (non deciso). 5
  test nuovi, 163/163 verdi.
- [x] **2. `read_section()`: gestire `type: "circle"`** — oggi le
  entity `circle` (es. le due circonferenze concentriche di un tubo
  visto dall'alto) sono scartate in silenzio dal filtro `type in
  ("line", "arc")`. Fatto: `_Edge` legge `circle` come giro chiuso
  (lunghezza = 2πr diretta, non passa dal calcolo sweep che a 360°
  darebbe 0 per il modulo), spessore e `is_bent` lo vedono. La
  ricostruzione della centerline resta esplicitamente non fatta per
  questo caso (si degrada a nota, non crasha) — è il punto 3. 3 test
  nuovi, 166/166 verdi.
- [x] ~~3. percorso per profilo ad arco puro~~ e ~~4. `BentProfile.from_section_reading()`~~
  — non più su questa base: `read_section()` stesso passa a forge
  nativo (MAP.md D43). Si fanno lì, una volta sola, non due (vedi sotto).

## `read_section()` su forge — provato e ritrattato per intero (MAP.md D43, CHIUSA)

`rules/read_section.py` ha importato forge per una notte (prima gli interni
`forge.core.topology.*`, poi la superficie pubblica
`load_geometry`+`heal_and_detect`, entrambe verificate funzionanti) ed è
tornato al loop-walker fatto a mano — non perché rotto, ma perché non
c'è ancora un consumatore vero (`pippo`) per cui decidere quel
contratto. `unfold` oggi importa forge SOLO in `io/dxf.py`, come sempre.
Restano dal giro di stanotte: il rilevamento delle coppie di cerchi e
l'instradamento dell'arco puro (sella) verso `Cylinder`/`Cone`, portati
sul loop-walker originale — 167/167 verdi. Storico delle fasi valutate:

- [x] **0. Decisione + `pyproject.toml`** — dipendenza `forge` ora
  richiesta (non più opzionale), descrizione riscritta.
- [x] **1. `read_section()` su `forge/core/topology/graph.py` +
  `loop_finder.py`** — sostituisce `_Edge`/`_split_into_sides`/
  `_order_chain` fatti a mano. Assorbe qui il caso "profilo ad arco puro
  → `Cylinder`/`Cone`" (ex punto 3 sopra) direttamente sulla base nuova.
  Fatto: `forge.load_geometry()` costruisce il `ForgeDocument`,
  `build_node_graph()`+`LoopFinder()` camminano il loop chiuso già
  ordinato. **Ritrattato lo stesso giorno** (vedi sotto): tornato al
  loop-walker fatto a mano, `unfold` non importa più forge da
  `rules/read_section.py`. Sopravvive il risultato buono: caso arco puro
  (sella, cap→arco→cap, zero flange) riconosciuto, `centerline_segments`/
  `angles` vuoti per quel caso, campi `pure_arc_radius`/
  `pure_arc_angle_deg` su `SectionReading` — portati sul walker
  originale. 1 test nuovo (sella R300/60°/s3), **167/167 verdi**.
- [x] ~~2. `Cone`/`Cylinder`/`BentProfile.develop()` costruiscono `Edge`~~,
  ~~3. `io/dxf.py` via `to_forge_result()`~~, ~~4. test → `Edge`~~ —
  **ritrattate (MAP.md D43), non si fanno.** `forge.load_geometry()` è
  già il modo con cui forge vuole ricevere geometria da un generatore
  (il suo stesso docstring usa un settore di cono come esempio) —
  costruire `Edge` a mano rifarebbe peggio quello che fa già lui.
  `FlatGeometry` non è ridondante con `ForgeDocument`: porta `meta`
  (i numeri leggibili da un piegatore) e `reference_entities` (il
  margine tratteggiato), roba di dominio `unfold` che `ForgeDocument`
  non ha. D43 resta chiusa alla fase 0-1 sopra.

## `BentProfile` da un disegno letto — resta da fare, indipendente da D43

`BentProfile.from_section_reading(reading: SectionReading, calibration=...)`
per il caso a flange dritte vere (L/U/Z lette da un disegno) — non
dipende in nessun modo dalla questione Edge/dict sopra, prende in
ingresso `read_section()`'s `centerline_segments`/`angles`/
`thickness`, stesso formato di oggi.

## Parcheggiato — Fase 4/5

- [ ] Scatole / pieghe su più assi (modello "a stella" — logica nuova
  per l'incrocio delle flange agli spigoli; usa la stessa formula
  generica già in `bend.py`/`deduction.py`, `calibration="default"`,
  zero dati misurati richiesti per partire — vedi MAP.md
  "formula generica prima" D36/D39).
- [ ] Info di piega (angolo ≠ 90°) nei DXF TruBend — dove sta quando si
  reimporta.

## Futuribili — qui dentro unfold, non un altro progetto (11 set 2026)

Deciso da Federico: senza un pippo anche rudimentale, `unfold` come
generatore+lettore è già in uno stato completo per quello che è (173
test verdi, calibrazione unificata D45, `docs/API.md`/`ARCHITECTURE.md`
scritti) — non è bloccato in attesa di pippo, pippo è un consumatore a
parte. Questi tre restano lavoro VERO di `unfold`, non rimandati a un
altro repo, perché modificano/estendono la geometria che `unfold` stesso
genera — diverso dal caso "foro nella posizione che dice il cliente"
(quello sì resta di forge/pippo a valle, vedi sotto):

- [ ] **Smussi/raggi ai 4 angoli dello sviluppo** — già prassi
  d'officina, `unfold` oggi genera sempre spigoli vivi. Sostituisce il
  vecchio bullet "raggio sugli spigoli del contorno esterno" (era
  segnato "non deciso" — ora deciso: qui). Conseguenza diretta: la
  **larghezza netta** della flangia vista dall'alto (quella che si
  taglia davvero) non è più semplicemente `width` una volta smussati gli
  angoli — va esposta in `meta` accanto a `width`, non lasciata implicita.
- [ ] **Convertitore da profilo strutturale standard (angolare/U) a
  `Section`** — quando un angolare o un U a catalogo nella misura giusta
  non si trova/non si compra, l'officina lo piega da lamiera invece —
  stessa forma (L/U) che `unfold` già sa sviluppare. Serve una tabella
  dati VERA (dimensioni standard angolari/profilati UNI/EN) prima di
  scrivere il convertitore — non va inventata a memoria (stesso principio
  di "verificare prima di asserire" già in altre note). Nome di lavoro:
  `Section.from_structural_profile(...)`, un'altra via d'ingresso come
  `from_external_flanges()`.
- [ ] **Posizione di ogni flangia nello sviluppo PIATTO** (non nella
  vista in sezione) — oggi `BentProfile.develop()` calcola internamente
  le posizioni delle linee di piega ma non le espone in `meta` come
  range per-flangia. Senza quello, pippo (o chiunque) non sa DOVE su un
  cut file piazzare una feature con `forge.inject()` — questo è il pezzo
  che manca perché `unfold` continui a dire "le coordinate", non "la
  feature" (vedi sotto).

## Fuori scope (di un altro layer, non "non deciso")

- [ ] Fori/altre feature sul pezzo, in posizione decisa dal disegno
  cliente — resta compito di `forge`/pippo a valle
  (`forge.inject()` esiste già per questo). Principio che li separa dai
  tre sopra: uno smusso d'angolo è `unfold` che completa la SUA propria
  geometria generata; un foro a una coordinata del cliente è pippo che
  aggiunge qualcosa che `unfold` non ha motivo di conoscere.
- [ ] Traduttore quote INTERNE ↔ mezzeria — proposto e ritirato da
  Federico stesso, resta qui solo perché banale da aggiungere se serve.
- [x] ~~Reverse engineering pieghe da un DXF cliente senza `.bnc`~~ —
  non più fuori scope, diventato un piano concreto: vedi sezione
  "Lettura disegno → Cone/Cylinder/BentProfile" sopra (MAP.md D42).
- [ ] Cosa esportare per il generatore di file di taglio a valle
  (`develop_from_external_flanges()` e i dati di `flange_quotes()` sono i
  candidati, non `to_dxf()` — vedi MAP.md D30/D31). Non ancora discusso
  nel dettaglio.
