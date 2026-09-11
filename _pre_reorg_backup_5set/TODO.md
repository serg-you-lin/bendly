# TODO

## Imparato — confronto con YouCanNotUnfold (sessione 4 set 2026)

YouCanNotUnfold (Alex Neufeld, plugin FreeCAD, ora nel Sheet Metal
Workbench) fa il lavoro OPPOSTO al nostro: parte da un **solido 3D già
modellato** e lo appiattisce (srotola). Noi partiamo da quote + angoli e
**costruiamo** il piatto. Non è un concorrente diretto.

Cosa fa lei e noi no:
- srotola un 3D vero in automatico (riconosce facce, pieghe cilindriche,
  spessore, direzione su/giù, fori/asole anche a cavallo di una piega);
- geometrie ramificate (pezzi a T/croce, pieghe su più assi) — usa un
  grafo delle facce tangenti + albero minimo (networkx);
- estrazione sketch 2D dal piatto + export DXF/SVG (da noi lo fa forge);
- K-factor in stile ANSI oltre al DIN.

Cosa facciamo noi e lei no:
- generazione parametrica senza CAD (dai solo le quote);
- le 3 regole per officina (din6935 / misurati / inside_sum) — lei ha
  solo bend allowance con K-factor, una filosofia sola;
- DIN 6935 completa (fibra neutra mobile), non K-factor tabellato;
- lettore `.bnc` TruBend nativo;
- coni / cilindri / cono sfaccettato (lei non fa coni);
- profili officina in JSON, tracciabilità piega per piega;
- zero dipendenze pesanti (niente FreeCAD/OpenCASCADE).

Il "plus" confermato: **andare contro i numeri dell'officina** (match
delle quote del cliente, anche con `inside_sum`) — nessun unfolder
generico lo fa. Se in futuro servisse srotolare STEP 3D complessi,
YouCanNotUnfold è il riferimento da guardare (idea grafo facce + MST).

## Domande aperte da questa sessione (da verificare col codice / dati)

- [ ] **Ricostruire lo sketch primitivo a mezzeria dai soli `.bnc`** (senza
      che Federico dica quale centerline ha usato). Per L/U è pura
      geometria: il `.bnc` ha quote esterne + spessore + angolo +
      accorciamento → mezzeria = esterno − (sp/2)·tan(angolo/2). Da fare:
      una funzione `trubend` → parametri `BentProfile`. Per Z/omega resta
      l'ambiguità nota della flangia-cerniera (± sp·tan(angolo/2)): serve
      sapere da che faccia TruBend ha quotato. La lunghezza sviluppo
      totale è sempre esatta.
- [ ] **Scatola da `.bnc`:** il `.bnc` è di fatto il programma di piega —
      contiene posizione, angolo, verso e accorciamento di OGNI piega,
      quindi possiamo LEGGERE com'è fatta (4 pieghe, 2 per asse, base
      X×Y). Ma `BentProfile` oggi NON la sa RICOSTRUIRE: modella solo una
      catena di pieghe parallele su un asse. Leggere ≠ modellare.
- [ ] **Pieghe su più assi (scatole / vassoi):** fattibile. Il caso
      scatola è il più semplice: pieghe che partono a raggiera da una
      faccia-base, nessuna flangia condivisa, sviluppo separabile lato per
      lato — non serve nemmeno il grafo/MST. Fase 1 possibile: topologia
      "a stella" (base + sponde), niente angoli condivisi. I casi duri
      (spigolo piegato due volte, angoli non-90) restano fuori.
- [ ] **Layer umano / API su esterno-esterno + vista in sezione quotata.**
      Il core resta a mezzeria (deciso, non si tocca: niente ambiguità).
      Ma per un carpentiere le quote a mezzeria sono fuorvianti — lui
      legge esterno-esterno. Il layer umano è un TRADUTTORE: prende quote
      esterne, converte a mezzeria, gira il core, riconverte in esterne
      per la stampa. Oltre allo sviluppo deve generare la **vista in
      sezione del pezzo piegato con le quote di riferimento marcate** —
      senza quella, i numeri esterno-esterno sono ambigui quanto la
      mezzeria. Le Z sono il caso che fa i capricci (la flangia centrale
      non ha una faccia "esterna" coerente — vedi `appunti.md`): lì la
      vista in sezione non è un optional, è ciò che rende usabile
      l'esterno-esterno.

## Fatto (sessione 3 set 2026)

- `unfold/trubend.py` — lettore file `.bnc` TruBend (spessore, sviluppo,
  matrice+V, accorciamento per piega)
- `unfold/deduction.py` — le 3 regole: `din6935`, `misurati`, `inside_sum`
- `profiles/default.json` (DIN + tabella cave generica) e
  `profiles/officina_1.json` (misurato, generato dai `.bnc`)
- `BentProfile(..., profilo=)` — unico punto di calcolo dello sviluppo
- golden test: `tests/test_deduction.py` (DIN da manuale) +
  `tests/test_golden_officina.py` (riproduce i DXF reali entro 0.1 mm) —
  75 test verdi
- `.gitignore` aggiornato: dati cliente fuori da GitHub
- `COME_FUNZIONA.md` — bozza da rileggere/correggere

## Domani — le dime (spessori 1, 3, 10)

- [ ] Decidere cos'è una "dima" nel repo: forma + parametri + formato.
      È la formalizzazione dei pezzi di test? o serve a tarare l'interprete
      di disegno? (Federico: "servono a dedurre i disegni che passiamo
      allo script" — chiarire)
- [ ] Fare le dime L / U / Z / omega per spessore 1, 3, 10 (le
      combinazioni per cui abbiamo già i DXF TruBend)
- [ ] Decidere come costruirle: in forge? a mano? da `BentProfile`?
- [ ] Match: ogni dima → sviluppo dal tool (profilo `officina_1`) vs DXF
      reale, deve tornare entro 0.1 mm
- [ ] Rivedere `deduction.py` / `bend.py` INSIEME, riga per riga, finché
      Federico li sente suoi. Valutare se togliere l'ereditarietà dei
      profili (forse è troppo per adesso)

## Da chiarire con Federico prima di codare

- [ ] Carpentiere (tizio 1): i numeri che dà sono quote INTERNE o a
      mezzeria? `inside_sum` oggi dà 136 su una U 50/70/20; sommando le
      interne "a crudo" farebbe 140
- [ ] Tabella cava→spessore VERA dell'officina 1 (Federico la porta)

## Dati che Federico porta

- [ ] Programmi TruBend (solo export, no piega fisica) per spessori
      1.5, 2, 4, 5, 6, 8, 12, 15, 20 — una L a 90° ciascuno, con la cava
      che usa davvero per quello spessore
- [ ] Non-90°: ~4 angoli (2 chiusi es. 30/60, 2 aperti es. 120/150),
      una L ciascuno, a 3 spessori (es. 2, 8, 20)
- [ ] Opzionale: 1 omega a un angolo non-90, per confermare la geometria

## Più avanti (non domani)

- [ ] Cono: confronto sviluppo `Cone(...)` vs DXF TruBend
      (`conodM450dm250h100s2.DXF`)
- [ ] API per far uscire i pattern "possibile lamiera"
- [ ] Cosa estrarre dai forge result (forge splitta/detecta, non
      interpreta)
- [ ] Allineamento viste — va calcolato ESTERNAMENTE a forge ma non credo faccai parte nemmeno di qusesto layer di unfolding hce imho vive una vita per i cazzi suoi.
- [ ] Reverse engineering pieghe da un DXF esistente (già in `appunti.md`)
- [ ] I dxf che escono d atrue bend anno qualche info nelle linee di piegatura, capire cos'è e se possimao allinearci o comunque creare un pattern nostro. Se reimporto un dxf uscito da TB in TB stesso, il sfw capisce già le linne di piegatura a che angolazione sono piegate, se su o giù.
