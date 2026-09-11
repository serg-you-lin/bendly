# unfold

> **Stato: alpha.** Le Fasi 1–3 sono fatte (forme avvolte, profili piegati a
> pressopiega, il layer umano con quote esterno-esterno e la vista in sezione
> quotata). Le Fasi 4–5 (scatole / pieghe su più assi, info di piega dentro i
> DXF TruBend) sono parcheggiate. L'API in `unfold.__all__` è stabile; vedi
> `docs/API.md` e `docs/ARCHITECTURE.md`.
>
> **Tutti i diritti riservati — nessuna licenza concessa.** Questo repo è
> pubblico per essere letto e valutato, non è open source. Vuoi usarlo?
> Chiedi — apri una issue o scrivimi.

Motore matematico puro per gli sviluppi piani di pezzi in lamiera: **forme
avvolte** (cono, cilindro) e **profili piegati a pressopiega** (una squadra a L,
una staffa a U, una Z, un'omega…).

`.develop()` **non ha dipendenze**: fa trigonometria e ritorna un
`FlatGeometry` — dati Python puri (una lista di entità geometriche in uno schema
neutro + i valori calcolati). Niente DXF, niente forge. Solo `.to_dxf()` tocca
[dxf-forge](../dxf-forge), e solo se lo chiami tu.

```python
from unfold import Cone, Cylinder

flat = Cone(top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5).develop()
flat.to_dxf("cone.dxf")

flat = Cylinder(diameter=1016, height=3895, thickness=5).develop()
flat.to_dxf("cylinder.dxf")
```

## Installazione

```
pip install -e .
```

`.develop()` funziona subito, senza altro. Per `.to_dxf()` serve anche
[dxf-forge](../dxf-forge) installato a fianco (non è su PyPI):

```
pip install -e ../dxf-forge
```

## Le convenzioni che contano

- **Il motore calcola a mezzeria** (centro spessore), mai a quote esterne o
  interne. È la decisione fondativa (`MAP.md` D1): una flangia incastrata fra
  due pieghe di verso opposto — l'anima di una Z o di un'omega — non ha una
  faccia "esterna" coerente, quindi l'ambiguità si toglie alla radice invece di
  ridurla soltanto. `BentProfile.flanges` e `Section.segments` sono lunghezze a
  mezzeria, da apice virtuale ad apice virtuale.
- **I diametri di `Cone` / `Cylinder` sono ESTERNI.** Lo sviluppo è calcolato
  sulla fibra media (`D_medio = D_esterno − thickness`), `MAP.md` D19.
- **Lo sviluppo è lineare**: Σ segmenti − Σ accorciamenti. L'accorciamento per
  piega è una costante pura di (spessore, cava, angolo) — nessun effetto di
  forma, dimostrato su 20 pezzi reali di officina (`MAP.md` D2).
- Se lavori a quote **esterno-esterno**, come un carpentiere che legge un
  disegno, usa il **layer umano** (`develop_from_external_flanges`,
  `Section.from_external_flanges`): traduce lui a mezzeria (`MAP.md` D28/D30), e
  l'offset esterno↔mezzeria **non** dipende dal raggio di piega.

## Esempi

### Un profilo piegato a pressopiega

L'accorciamento di ogni piega esce da **una formula sola** (metodo della fibra
neutra), che vuole un raggio interno `r` e un fattore `K`. Li porta la
**calibrazione** — un file con la tabella spessore→cava (da cui `r ≈ cava/6`),
eventualmente il `K` per materiale, eventualmente accorciamenti già **misurati**
(`MAP.md` D33). Non imposti niente per partire: senza `calibration` usa
`"default"`, che non indovina la cava di nessuno — `r` ripiega su un raggio
fisso dichiarato (1 mm) e il `K` lo stima DIN 6935 da `r/s` (`MAP.md` D36).
`flat.bends[i].source` dice sempre da dove viene ogni numero, mai una stima
travestita da dato reale.

```python
from unfold import Bend, BentProfile

flat = BentProfile(
    flanges=[50, 80, 50],                       # lunghezze a mezzeria
    bends=[Bend(angle=90), Bend(angle=90)],     # solo l'angolo
    thickness=2, width=300,
    material="acciaio",                         # sceglie la riga in k_per_materiale della calibrazione
    calibration="tipo_misurato",                # o omesso -> "default"; o "din6935", "esempio_din_3cave", "inside_sum"
).develop()

print(flat.meta["total_length"])
for b in flat.bends:                            # una BendResult per piega
    print(b.angle, b.deduction, b.source)       # quanto, e da dove viene

flat.to_dxf("squadra.dxf")                       # rettangolo + una linea per piega, role="bending"
```

`K`, in ordine: un accorciamento **misurato** per quella combinazione
(spessore, cava, angolo) → il `K` per materiale della calibrazione → la stima
DIN 6935. La cava viene dalla tabella; passa `cava=` su un `Bend` solo per una
piega fatta con una cava fuori standard. `Bend(radius=...)` è per quando conosci
il raggio interno e non la cava (bombato, coniatura).

`Bend.angle` è l'angolo di cui la lamiera **ruota** rispetto a piatta
(piatta = 0°), non l'angolo incluso fra le flange finite. Per una squadra a 90°
coincidono per coincidenza; per ogni altro angolo passa `180 − angolo_incluso`.

### Il layer umano — quote esterno-esterno

```python
from unfold import Bend, develop_from_external_flanges

flat = develop_from_external_flanges(
    external_flanges=[100, 110],                 # lette sull'esterno del pezzo
    bends=[Bend(angle=90)],
    thickness=3, width=300,
    calibration="tipo_misurato",
)
```

### La vista in sezione quotata

`Section` porta il **verso** della piega (su/giù, `angles` nella naming scheme
90/270). Dà sia lo sviluppo piatto sia il disegno del pezzo *piegato*.

```python
from unfold import Section

sec = Section.from_external_flanges(
    shape="Z", external_flanges=[80, 40, 80], angles=[90, 270], thickness=3,
)

for q in sec.flange_quotes():
    # display_kind dice "esterno" o, per l'anima ambigua di una Z, "mezzeria"
    print(q.display_length, q.display_kind)

flat = sec.to_bent_profile(width=300, calibration="din6935").develop()
```

### L'export a livelli — un solo DXF, impilato in verticale

```python
from unfold import Section, export_part

sec = Section.from_external_flanges(
    shape="L", external_flanges=[100, 110], angles=[90], thickness=3,
)
export_part(sec, width=300, path="pezzo.dxf",
            calibration="din6935", include_section=True, include_header=True)
```

Taglio (sempre) → vista in sezione quotata (opzionale) → header (opzionale),
impilati dall'alto in basso, allineati a sinistra (`MAP.md` D32).

## Qual è il setup giusto per te

La formula generica è il prodotto: deve funzionare bene senza i dati di
nessuna officina. Una calibrazione è un bonus opzionale, mai un requisito.
Ogni scelta di setup si controlla contro questi quattro casi (`MAP.md`
D36/D39) — una calibrazione dichiara da sé quale dei quattro è col campo
`tipo_cliente`, verificato contro il suo contenuto reale da
`tipo_cliente_coerente()`:

| `tipo_cliente` | Sei... | Dai a `unfold`... | Calibrazione |
|---|---|---|---|
| `zero_config` | uno sconosciuto che l'ha appena scaricato, non legge nulla | niente | `default` (o omessa) — raggio fisso 1 mm, `K` stimato DIN |
| `cava_propria` | un'officina con le tue cave ma senza CAM | solo la tabella spessore→cava (5 minuti, mai una misura) | copia `calibrations/esempio_din_3cave.json`, ci metti le tue cave vere |
| `somma_interna` | un'officina che vuole solo la somma delle quote interne, niente K-factor | niente, solo questa preferenza | `calibrations/inside_sum.json` |
| `misurato` | un'officina con CAM, che vuole avvicinarsi il più possibile per preventivare | cave + accorciamenti misurati (ore di lavoro vere, non gratis) | come `calibrations/tipo_misurato.json` — misurato dove c'è, stimato altrove |

## Il contratto neutro con forge

`FlatGeometry.entities` è nello stesso schema accettato da
`forge.load_geometry()` — è il contratto neutro fra i due progetti. `unfold` non
importa mai forge per il calcolo; forge serve solo a `to_dxf()`. Se non vuoi
passare da `to_dxf()`, consuma `.entities` / `.meta` / `.bends` direttamente.

## Documentazione

- **`TUTORIAL.md`** — un ordine consigliato per attraversare gli script di
  esplorazione numerati e (ri)imparare la libreria, con una domanda a cui
  rispondere ad ogni tappa.
- **`SCRIPTS.md`** — l'indice degli script numerati (`00_*` … `10_*`): script →
  area API → cosa mostra.
- **`MAP.md`** — il decision log: cosa è stato deciso e soprattutto perché
  (`D1`, `D2`, …), in ordine cronologico.
- **`COME_FUNZIONA.md`**, **`SECTIONS.md`** — documenti di dominio (bend
  allowance, DIN 6935, K-factor; cos'è una sezione e perché il verso vive lì).
- **`TODO.md`** — cosa manca ancora, in ordine di priorità.
- **`tests/`** — la specifica eseguibile: valori golden da pezzi reali di
  officina (`data_4_cloude/`, non versionati), rigenerati solo dagli script
  dedicati `tests/generate_*.py`.

## Licenza

Tutti i diritti riservati — vedi [`LICENSE`](LICENSE). Copyright (c)
2026 Federico Sidraschi. Codice consultabile per lettura; nessuna
licenza concessa per usarlo, copiarlo, modificarlo o distribuirlo.
