Lo sviluppo delle lamiere (ovvero il calcolo dello sviluppo piatto o blank development) è il processo geometrico e matematico utilizzato per determinare le dimensioni esatte di una lamiera piana prima che venga piegata tramite pressopiega.Il fattore cruciale in questo calcolo è che, durante la piegatura, le fibre esterne della lamiera si tendono (trazione) e quelle interne si comprimono (compressione). Esiste una linea immaginaria che non subisce variazioni di lunghezza, chiamata asse neutro.Ecco i metodi principali e le formule utilizzate per calcolare lo sviluppo lineare:1. Il Metodo del Fattore K (K-Factor)Il Fattore K è il rapporto che definisce la posizione dell'asse neutro rispetto allo spessore della lamiera.Formula del fattore K: K = t / T (dove t è la distanza dall'interno della piega all'asse neutro, e T è lo spessore della lamiera).Di solito il valore varia tra 0.3 e 0.5 in base al materiale e al raggio di piegatura.Formula dello Sviluppo Piatto (L):\(L=A+B+BA\)Dove:A e B: Le lunghezze dei tratti rettilinei (flange) misurate fino all'inizio del raggio di piega.BA (Bend Allowance): La tolleranza di piegatura (la lunghezza dell'asse neutro nella curva).Calcolo della Bend Allowance (BA):\(BA=\frac{\pi \cdot \alpha }{180}\cdot (R+K\cdot T)\)α = Angolo di piegatura (in gradi)R = Raggio interno di piegaturaT = Spessore della lamieraK = Fattore K2. Il Metodo della Deduzione di Piegatura (Bend Deduction / BD)È il metodo più pratico e utilizzato dai programmatori di macchine CNC perché si basa sulle quote esterne totali del pezzo piegato.Formula dello Sviluppo Piatto (L):\(L=L1+L2-BD\)Dove:L1 e L2: Le quote esterne totali delle flange (misurate fino al punto di intersezione virtuale delle facce esterne).BD (Bend Deduction): La quantità di materiale che viene "sottratta" per compensare l'allungamento.Calcolo della Bend Deduction (BD):\(BD=2\cdot OSS-BA\)OSS (Outside Set Back) = \(=(R + T) \cdot \tan(\alpha / 2)\)Tabella di orientamento rapido per il Fattore KMaterialeRapporto Raggio/Spessore (R/T)Fattore K indicativoAcciaio Dolce / FerroAccoppiamento standard (R ≈ T)0.43 - 0.45Acciaio InoxAccoppiamento standard (R ≈ T)0.38 - 0.40AlluminioAccoppiamento standard (R ≈ T)0.40 - 0.42TuttiRaggio molto stretto (R < T)0.30 - 0.33TuttiRaggio ampio (R >> T)0.50 (asse neutro al centro)Se hai un pezzo specifico da sviluppare, posso aiutarti a fare il calcolo esatto. Per procedere, potresti fornirmi:Lo spessore della lamiera (T)Il materiale (es. ferro, inox, alluminio)Le misure delle quote (interne o esterne?)L'angolo di piega (es. 90°) e il raggio interno (R)

---

# TODO — metodo di sviluppo "carpenteria vecchia scuola" (somma quote interne, R=0)

Da fare, non ancora implementato. Segnalato da Federico: nella stragrande
maggioranza delle carpenterie a cui questo progetto può puntare come clienti,
lo sviluppo NON si calcola con Bend Deduction/K-factor — si sommano le quote
INTERNE delle flange, punto, senza nessuna correzione per raggio o
allungamento (raggio di piega considerato 0, e comunque ignorato anche
quando non lo è — stessa matrice da decenni, nessuno la rimette in
discussione). È una prassi tecnicamente imprecisa ma radicatissima: i
carpentieri la difendono a oltranza, arrivano a ricontrollare a calcolatrice
a mano, e un solo errore rispetto alle LORO quote costa la fiducia nello
strumento in modo permanente. Conclusione pratica di Federico: lo strumento
deve poter riprodurre ANCHE questo metodo, non solo quello corretto — non è
negoziabile per l'adozione reale sul campo, indipendentemente da cosa sia
"giusto" in teoria.

Analisi già fatta in questa sessione (vedi `scripts/example_compare_inside_sum.py`,
funzione `inside_sum()`): per una piega di angolo A, la quota interna di una
flangia si ottiene da quella esterna con

    quota_interna = quota_esterna - T * tan(A/2)      (per ogni piega adiacente)

— una riduzione che dipende SOLO da spessore e angolo, mai dal raggio. Sommare
le quote interne così, senza altro, equivale a un bend allowance IMPLICITO
pari a zero (altra formulazione: outside setback meno bend allowance, con
outside setback nullo perché a raggio zero OSS=0). Verificato coi numeri:
a raggio "standard" l'errore è quasi nullo per puro caso geometrico (~0.2mm
su una staffa a due pieghe) — probabilmente è proprio per questo che la
prassi non è mai stata messa in discussione sui casi tipici — ma con raggio
vicino a zero lo scarto rispetto al calcolo corretto è sistematico e cresce
con il numero di pieghe (~1mm per piega a T=2, K=0.31, 90°).

Idea di implementazione (da decidere quando ci si mette mano): un parametro
tipo `BentProfile(method="bend_deduction" | "inside_sum")`, dove
`"inside_sum"` riproduce esattamente questa prassi (nessun BA/OSS/BD, sola
sottrazione geometrica esatta di T*tan(angolo/2) per lato) — non un'opzione
"meno precisa" nascosta, ma un metodo alternativo di pari dignità nell'API,
perché per l'adozione reale conta di più matchare le quote del cliente che
avere ragione in teoria.

Il dubbio ancora aperto di Federico, da verificare sul campo prima di
decidere i default: nei loro sviluppi TruBend a lavoro, il DXF viene sempre
più corto rispetto alla tavola del cliente — ma non sa ancora che metodo di
sviluppo usi il cliente per la sua tavola, va controllato caso per caso
prima di trarre conclusioni.

---

# TODO — reverse engineering delle pieghe da un DXF esistente (forge + bend.py)

Da fare, non ancora implementato. Idea di Federico, collegata al punto sopra:
usare forge per leggere un DXF già fatto (di un cliente, o l'output TruBend)
ed estrarne le pieghe, poi `bend.py` per ricostruire le quote — invece di
indovinare a occhio che convenzione di sviluppo ha usato chi ha disegnato
quel DXF.

È fattibile, ed è la stessa matematica di `BentProfile` fatta al contrario:

1. `forge.load_dxf(path)` → `forge.heal_and_detect(doc)` → `result.parts[0]`
   dà già GRATIS, da un DXF vero: `part.bending_lines` (posizione di ogni
   piega) e `part.outer` (contorno pieno). Non serve scrivere niente di
   nuovo in forge per questo pezzo — c'è già.
2. Dalle posizioni delle linee di piega, ordinate lungo l'asse dello
   sviluppo, si ricavano le distanze fra una piega e l'altra (e le due
   estremità) — sono le lunghezze PIATTE (tangenti) di ogni flangia, lo
   stesso dato che `BentProfile` oggi consuma internamente ma non espone.
3. Con un'ipotesi di raggio/angolo/K per ciascuna piega (letta da
   un'annotazione nel DXF se c'è, o assunta), si ricostruiscono le quote
   ESTERNE del pezzo finito piegato — è l'inverso della catena OSS/BD di
   `BentProfile`: invece di `flangia_esterna → sottrai OSS → lunghezza
   piatta`, si fa `lunghezza piatta (da forge) → aggiungi OSS → flangia
   esterna ricostruita`.
4. Usarlo per il problema aperto sopra: prendi la tavola del cliente,
   ricostruisci le quote finite assumendo prima Bend Deduction poi
   inside_sum-a-raggio-zero, confronta con le quote dichiarate sulla tavola
   — quella che torna ti dice empiricamente quale convenzione ha usato il
   cliente, invece di indovinare.

Nome di lavoro provvisorio: qualcosa come `BentProfile.from_flat_segments(...)`
o una funzione a parte in `bend.py` — da decidere quando ci si mette mano.

---

# BUG/LIMITE noto — quota esterna ambigua sulle flange fra pieghe di verso opposto (Z, Omega)

Scoperto verificando numericamente (non a mente) la domanda di Federico sul
disegno della Z. Confermato con uno script indipendente che costruisce la
geometria vera (coordinate reali, non la formula di `bend.py`) e confronta
col risultato di `BentProfile`.

**Per L e U (pieghe sempre nello stesso verso): nessun errore, verificato di
nuovo, `BentProfile` torna esatto.**

**Per Z e Omega (pieghe in verso alternato): la flangia incastrata fra due
pieghe di verso opposto non ha un'unica "quota esterna" ben definita** — le
due pieghe adiacenti vedono come "esterna" due facce OPPOSTE della stessa
lamiera, quindi non esiste una faccia coerente da cui misurare quella
flangia sola. Se si è comunque costretti a sceglierne una (come fa chiunque
quoti un disegno da un solo punto di vista), `BentProfile` sbaglia — perché
la sua formula (`L_i - OSS_prima - OSS_dopo`) assuma sempre "esterno" da
entrambi i lati.

L'errore è piccolo, PREVEDIBILE e limitato — non esplode:

    errore = T · tan(angolo/2)     per ogni flangia ambigua

Verificato numericamente con T=2, pieghe a 90° (tan(45°)=1, quindi errore=T
esatto per flangia ambigua):
- Z (1 flangia ambigua, l'anima): **-2.0 mm** sullo sviluppo totale
- Omega (2 flange ambigue, le due anime): **-4.0 mm** sullo sviluppo totale

Non è un errore ovunque — solo sulle flange "di cerniera" fra due pieghe di
verso opposto. Le flange di estremità e le flange fra pieghe dello stesso
verso (anche dentro una Omega) restano esatte.

**RISOLTO (in teoria, non ancora in codice) — la mezzeria elimina l'ambiguità
del tutto.** Proposta di Federico, verificata numericamente: misurare a/b/c
sempre a MEZZERIA di spessore (non esterno, non interno) invece che a quota
esterna. La mezzeria non ha "lati" — non può mai essere esterna a una piega
e interna a quella dopo, quindi la scelta arbitraria che causava l'errore
sparisce alla radice, non solo si riduce.

Verificato con lo stesso script indipendente, sostituendo OSS con
CSS = (R + sp/2)·tan(angolo/2) (centerline set-back) ovunque:

    U:     differenza = 0.0000
    Z:     differenza = 0.0000
    Omega: differenza = 0.0000

Zero errore su tutti e tre, nessuna eccezione — a differenza della quota
esterna che dava -2mm (Z) e -4mm (Omega). La mezzeria vince anche perché
combacia con come Federico vuole modellare i pezzi di test in CAD (sketch
primitivo a mezzeria + feature lamiera, spessore libero di cambiare senza
rimodellare — vedi sezione sotto).

**Da fare in `bend.py` per chiudere il cerchio:** sostituire OSS con CSS
nella formula di `BentProfile` (oggi usa `bend.outside_setback()`, serve un
`bend.centerline_setback()` analogo con `R + thickness/2` al posto di
`R + thickness`). Cambia anche il significato di `flanges=[...]`: non più
quote esterne, ma quote a mezzeria — è un cambio di contratto dell'API,
non solo un fix interno, quindi le funzioni/test/script che già usano
`BentProfile` con quote esterne vanno rivisti quando si fa.

---

# Convenzione di naming per i pezzi di test (STEP + golden test)

Decisa da Federico. Ogni pezzo di test si descrive con uno sketch primitivo
a mezzeria — solo segmenti (a, b, c, …) e angoli (α, β, …), NESSUN raggio
disegnato (il raggio dipende da matrice/punzone, è una scelta di produzione,
non fa parte dello sketch) — e si modella in CAD come feature di lamiera
dalla mezzeria, così lo stesso sketch si riusa a spessori diversi (es. 2mm
= 1mm per parte, 5mm = 2.5mm per parte) senza rimodellare nulla.

Nome del file/test, esempio: `U1001201009090sp3` = forma U, a=100, b=120,
c=100, α=90°, β=90°, spessore=3. Generalizza a Z con più segmenti/angoli
nello stesso schema (vedi l'artifact "Spigolo Virtuale" per la versione
illustrata di L/U/Z/Omega con questa convenzione).

**Omega — sfruttare la simmetria nel nome.** Per un'Omega simmetrica (piedi
e anime uguali a specchio, caso normale) bastano 3 segmenti e 2 angoli
invece di 5 e 4: `a` (piede) = `e`, `b` (anima) = `d`, e per gli angoli
`α` (piede→anima, le due pieghe agli estremi) = `δ`, `β` (anima→piano, le
due pieghe centrali) = `γ` — verificato geometricamente (per riflessione
speculare le due pieghe di estremità hanno la stessa ampiezza, idem le due
centrali). Esempio: `OMEGA0501001109090sp3` = a=e=50, b=d=100, c=110,
α=β=90°, sp=3 — γ e δ non compaiono, si ricavano da α e β.

**H (quota del pezzo finito, esterno-esterno — vedi §01 dell'artifact) NON
entra nel nome.** È derivata dallo sketch primitivo (per l'Omega:
H = b + sp = d + sp), non un dato indipendente — lo sketch primitivo la
determina già da solo, includerla nel nome sarebbe ridondante.

Il test ricostruisce i punti della lamiera a partire da questi stessi
numeri (stessa mezzeria) — non dallo STEP: lo STEP serve solo a generare
l'output "ufficiale" di TruBend/CAD da confrontare, i parametri per
`BentProfile` si scrivono a mano dagli stessi numeri usati per costruire
lo STEP (vedi sezione golden test più sopra — nessun parsing di STEP

---

# TODO — dati golden reali (`data_4_cloude/`) e regola matrice/spessore

Federico ha generato una prima batch di dati reali TruBend in
`data_4_cloude/` (L, U, Z, O, cono — 3 spessori ciascuno, `tooling.json` coi
dati di matrici/punzoni Trumpf estratti dai cataloghi). Prima batch fatta
con un solo utensile fisso (matrice EV005/H, V16, + punzone OW210/S) per
tutti gli spessori, di proposito: rispecchia la prassi di molte carpenterie
("una matrice/punzone per tutto").

**Scoperta di questa sessione — perché conviene solo su alcuni spessori:**
confrontando `BentProfile` (R=1.6, K da tabella) con le lunghezze reali
estratte dai DXF (bounding box via `ezdxf`) sul provino L
(a=b=114, 90°, EV005/OW210S, acciaio dolce):

| spessore | nostro modello | reale TruBend | delta |
|---|---|---|---|
| 1mm  | 227.00 | 226.31 | +0.70 |
| 3mm  | 225.77 | 225.78 | −0.004 (praticamente esatto) |
| 10mm | 222.18 | 218.75 | +3.43 |

L'errore cresce con quanto ci si allontana dal range di spessore per cui
la matrice V16 è dimensionalmente corretta. Regola pratica della piegatura
ad aria: l'apertura V della matrice dovrebbe stare tra 6 e 10 volte lo
spessore. Per V16 → spessore ideale ≈2mm, range accettabile ≈1.6-2.7mm:
il 3mm ci sta (match quasi perfetto), l'1mm è leggermente sotto range,
il 10mm è enormemente fuori range (V/T=1.6 — il materiale non ci sta
fisicamente nella gola, la matrice si romperebbe prima di arrivare a 90°).
Conclusione: il provino da 10mm fatto con EV005/OW210S NON è un dato
fisicamente valido da usare per calibrare — TruBend calcola comunque un
numero anche con un abbinamento matrice/spessore irrealizzabile in
officina, ma quel numero non rappresenta una piega reale.

**Piano concordato con Federico:** rifare (o integrare) i provini usando
per ogni spessore la matrice davvero adatta (regola V≈6-10×T), usando
quelle come riferimento "golden" da lì in avanti. Matrici già in
`tooling.json` per orientarsi sulle fasce:

| matrice | V | spessore indicativo (V/6 – V/10) |
|---|---|---|
| EV001/S | 6  | ≈0.6 – 1.0mm |
| EV002   | 8  | ≈0.8 – 1.3mm |
| EV004/H | 12 | ≈1.2 – 2.0mm |
| EV005/H | 16 | ≈1.6 – 2.7mm |
| EV_W50/80/H | 50 | ≈5.0 – 8.3mm |
| EV_W60/80   | 60 | ≈6.0 – 10.0mm |

Per lo spessore 10mm quindi la matrice giusta è EV_W50/80 o EV_W60/80, non
EV005. Il punzone OW308-T (R8, angolo 0°, "Custom") è un caso a parte: non
è un punzone da piega ad aria (punta a 28° come OW210), ha angolo 0° quindi
si comporta più da punzone "a fondo"/coining — raggio imposto
meccanicamente dal punzone stesso, non stimato da V/6, e verosimilmente
K-factor più alto per la maggior compressione del materiale in piega
(spiegherebbe uno sviluppo più lungo nonostante il raggio maggiore, visto
da Federico ma senza DXF salvato per verificarlo).

**Stato al momento della sospensione:** Federico porta i nuovi provini
(matrice corretta per spessore) il giorno dopo — non prima. Fino ad allora:
NON sono ancora stati scritti test automatici (pytest) contro i dati
reali — i confronti fatti finora sono stati script/snippet interattivi
usati solo per diagnosticare il problema, non salvati come test ripetibili
nel repo. Da fare quando arrivano i DXF nuovi:
1. Ricostruire la tabella di confronto SOLO sulle coppie matrice/spessore
   in range (quelle fuori range restano come riferimento "perché non torna",
   non come dato di calibrazione).
2. Solo allora decidere se formalizzare un test golden vero e proprio in
   `tests/` (lettura DXF + confronto `BentProfile`, tolleranza da
   concordare) — non farlo prima, per non costruire test su dati che
   Federico ha già segnalato come non rappresentativi.
necessario).