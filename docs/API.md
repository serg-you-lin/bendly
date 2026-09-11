# API — una scheda per ogni nome pubblico di `unfold`

Copre ogni nome in `unfold.__all__` (24 nomi). Non ripete il *perché*
(quello è `MAP.md`) né il flusso generale (quello è
`docs/ARCHITECTURE.md`) — qui solo: cosa prende, cosa ritorna, cosa
solleva, un esempio copiabile.

Organizzato per layer (stesso ordine di `docs/ARCHITECTURE.md`):
generatori (`core`) → calibrazione/accorciamento (`rules`) → lettura di
un disegno (`rules`) → modello a quote umane (`model`) → dati grezzi
dello sviluppo (`model`) → pipeline di comodo (`human_layer`).

---

## Generatori — `unfold.core`

### `Cone`

```python
Cone(
    top_diameter: float, bottom_diameter: float, height: float,
    thickness: float = 0.0, margin: float = 0.0,
    sector_angle: float | None = None,       # tetto sullo sviluppo naturale (MAP.md D46)
    split: int = 1,                          # scorciatoia: sector_angle = full_angle/split
    orientation: str = "vertical",           # "vertical" | "horizontal"
    faceted: bool = False, n_facets: int = 8,
    facet_bend_radius: float | None = None,  # esplicito -> batte la calibration
    facet_k_factor: float | None = None,     # esplicito -> batte la calibration
    material: str = "acciaio",
    calibration: "Calibration | str" = "default",   # MAP.md D45
    label: str = "cone",
)
```

Tronco di cono (o cono intero se un diametro è ~0) come settore anulare
sviluppato — a calandra (`faceted=False`, un arco vero) o a spicchi
piani uniti da pieghe (`faceted=True`). Sfaccettato: raggio e K di ogni
giunto vengono dalla `calibration` dell'officina — stessa scaletta di
`BentProfile` (MAP.md D45), un giunto sfaccettato è una piega vera.
`sector_angle`/`split` (MAP.md D46, mai insieme): sviluppa solo una
porzione dello sviluppo naturale — tipicamente per farlo in pezzi
uguali saldati (`split=2` = due metà). A differenza di `Cylinder`, qui
"pieno" non è 360 ma un valore fissato dalla geometria del cono
(`meta["full_angle_deg"]`).

- **`.develop() -> FlatGeometry`** — calcola e ritorna lo sviluppo, con
  `flat.bends: list[BendResult]` popolato se `faceted=True` (una per
  giunto, `n_facets - 1`, tutte identiche per un poligono regolare —
  `bend_allowance` valorizzato, `deduction`/`setback` a 0: qui si
  aggiunge materiale, non se ne sottrae). **Mutates**: niente, `Cone` è
  immutabile in pratica (dataclass, ma `.develop()` non tocca `self`).
  **Raises**: `ValueError` se un diametro/altezza è ≤0, `thickness` ≥ un
  diametro, `top_diameter` == `bottom_diameter` sulla fibra media (usa
  `Cylinder`), `orientation` non valida, `n_facets < 3`.
- `meta` del risultato: `top_diameter_mean`, `bottom_diameter_mean`,
  `slant_height`, `outer_radius`, `inner_radius`, `sector_angle_deg`
  (liscio) o `n_facets`/`facet_angle_deg`/`facet_bend_radius`/
  `facet_k_factor`/`facet_bend_allowance`/... (sfaccettato).

```python
from unfold import Cone
flat = Cone(top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5).develop()
flat.to_dxf("cone.dxf")   # richiede forge installato a fianco
```

### `Cylinder`

```python
Cylinder(
    diameter: float, height: float,
    thickness: float = 0.0, margin: float = 0.0,
    sector_angle: float = 360.0,             # < 360 = settore parziale (sella calandrata)
    split: int = 1,                          # scorciatoia: sector_angle = 360/split (MAP.md D46)
    orientation: str = "vertical",
    faceted: bool = False, n_facets: int = 8,
    facet_bend_radius: float | None = None,  # esplicito -> batte la calibration
    facet_k_factor: float | None = None,     # esplicito -> batte la calibration
    material: str = "acciaio",
    calibration: "Calibration | str" = "default",   # MAP.md D45
    label: str = "cylinder",
)
```

Cilindro (tubo) sviluppato come rettangolo — a calandra o a prisma
sfaccettato. `sector_angle` (MAP.md D42): meno di 360° sviluppa solo un
settore del giro (es. una sella calandrata, o — con `faceted=True`,
supportato da MAP.md D46 — una metà da saldare, `split=2`). Sfaccettato:
raggio e K dalla `calibration` dell'officina (MAP.md D45), stesso
principio di `Cone`.

- **`.develop() -> FlatGeometry`**, con `flat.bends` popolato se
  `faceted=True` (vedi `Cone`). **Mutates**: niente. **Raises**:
  `ValueError` — stessa famiglia di `Cone` più `sector_angle` fuori
  `(0, 360]`, o `sector_angle != 360` con `faceted=True`.
- `meta`: `diameter_mean`, `width`, `width_cut`, `sector_angle_deg`, +
  campi sfaccettato se `faceted=True`.

```python
from unfold import Cylinder
flat = Cylinder(diameter=1016, height=3895, thickness=5).develop()
sella = Cylinder(diameter=603, height=400, thickness=3, sector_angle=60).develop()
```

### `Bend`

```python
Bend(
    angle: float,                    # gradi — rotazione da piatto, NON l'angolo incluso
    radius: float | None = None,     # raggio interno; eccezione in BentProfile
    k_factor: float | None = None,   # solo per Cone/Cylinder sfaccettati
    cava: float | None = None,       # override della cava di tabella, in BentProfile
)
```

Una piega sola. Dentro `BentProfile` serve solo `angle` (+ `cava` se
diversa da quella di tabella) — l'accorciamento lo decide la
`Calibration` del profilo. `radius`/`k_factor` sono invece la via
normale per le pieghe di un `Cone`/`Cylinder` sfaccettato, che li usano
direttamente (lì non c'è una cava).

| metodo | ritorna | usa |
|---|---|---|
| `.bend_allowance(thickness, k_factor) -> float` | lunghezza dell'asse neutro nella piega | `radius` |
| `.centerline_setback(thickness) -> float` | setback a mezzeria (CSS) | `radius` |
| `.outside_setback(thickness) -> float` | setback esterno (OSS) | `radius` |
| `.inside_setback(thickness) -> float` | setback interno (ISS) | `radius` |

Tutti e quattro sollevano `TypeError` se chiamati con `radius=None`
(nessun controllo esplicito — è aritmetica su `None`, non un `raise`
scritto a mano).

```python
from unfold import Bend
b = Bend(angle=90, radius=4.0, k_factor=0.42)
allowance = b.bend_allowance(thickness=3.0, k_factor=0.42)
```

### `BentProfile`

```python
BentProfile(
    flanges: list[float],            # lunghezze A MEZZERIA, apice a apice
    bends: list[Bend],                # len(bends) == len(flanges) - 1
    thickness: float,
    width: float,
    material: str = "acciaio",
    orientation: str = "horizontal",  # "horizontal" | "vertical"
    label: str = "bent_profile",
    calibration: "Calibration | str" = "default",
)
```

Il motore: N flange a mezzeria unite da N-1 pieghe. `calibration`
decide l'accorciamento di ogni piega dalla cava (MAP.md D33) —
`"default"` funziona senza configurare niente.

- **`.develop() -> FlatGeometry`** — con `flat.bends: list[BendResult]`
  popolato (uno per piega). **Mutates**: niente. **Raises**:
  `ValueError` — meno di 2 flange, `len(bends) != len(flanges)-1`, una
  flangia ≤0, `thickness`/`width` ≤0, `orientation` non valida, un
  `bend.angle` fuori `(0, 180)`, un `bend.radius` ≤0 se dato, o una
  flangia troppo corta per i raggi/angoli delle pieghe adiacenti (il
  setback mangia più della flangia).

```python
from unfold import Bend, BentProfile
flat = BentProfile(
    flanges=[50, 80, 50],
    bends=[Bend(angle=90), Bend(angle=90)],
    thickness=2, width=300,
    calibration="default",
).develop()
flat.to_dxf("bent_profile.dxf")
for r in flat.bends:
    print(r.angle, r.rule, r.source)   # rule: misurato | k_materiale | din6935 | inside_sum
```

### `estimate_k_factor`

```python
estimate_k_factor(material: str, radius: float, thickness: float) -> float
```

Stima un K-factor di partenza da materiale + rapporto R/T (tabella
qualitativa, `COME_FUNZIONA.md`). **Orfana da MAP.md D45**: fino ad
allora era la via di default delle pieghe sfaccettate di `Cone`/
`Cylinder`; ora quelle passano dalla `calibration` dell'officina
(`k_din6935`, non questa tabella). Resta pubblica e chiamabile a mano
per chi vuole proprio questa stima per materiale, ma nessun codice di
`unfold` la chiama più di default. **Raises**: `ValueError` se
`thickness <= 0`.

### `MATERIAL_K_FACTORS`

```python
MATERIAL_K_FACTORS: dict[str, float]
# {"mild_steel": 0.44, "stainless_steel": 0.39, "aluminum": 0.41}
```

Costante, punto di partenza per `estimate_k_factor` — stessa nota:
orfana dal percorso di default di `unfold` (D45), resta pubblica.

---

## Calibrazione e accorciamento — `unfold.rules.deduction`

### `Calibration`

```python
Calibration(data: dict)
Calibration.load(name: str, folder: str | Path | None = None) -> Calibration
```

I dati di calcolo di un'officina (tabella cave, K per materiale, righe
misurate) — un file JSON completo in `calibrations/`, nessuna
ereditarietà fra calibrazioni. `.load("din6935")`/`.load("inside_sum")`
funzionano anche senza un file (`BARE_CALIBRATIONS`). **Raises**
(`.load`): `FileNotFoundError` se il nome non è né un file né una
calibrazione nuda.

| metodo | ritorna |
|---|---|
| `.tipo_cliente` (property) | `str \| None` — uno di `TIPI_CLIENTE` |
| `.v_opening_for_thickness(thickness) -> float \| None` | cava per uno spessore (interpolata al più vicino se manca l'esatta) |
| `.k_for_material(material) -> float \| None` | il K di questa officina per quel materiale |
| `.centerline_deduction(thickness, angle_deg, cava=None, radius=None, material="acciaio") -> float` | solo il numero |
| `.deduction_detail(...) -> DeductionInfo` | il numero + provenienza |

**Raises** (`.deduction_detail`/`.centerline_deduction`): `ValueError`
se la calibrazione non ha tabella cave e non è dato né `cava` né
`radius` per lo spessore richiesto.

```python
from unfold import Calibration
cal = Calibration.load("default")
info = cal.deduction_detail(thickness=3.0, angle_deg=90.0)
print(info.rule, info.source, info.value)
```

### `DeductionInfo`, `bend_deduction`, `k_din6935`, `deduction_din6935`

```python
bend_deduction(radius: float, thickness: float, angle_deg: float, k: float,
               reference: str = "mezzeria") -> float          # "mezzeria" | "esterno"
k_din6935(radius: float, thickness: float) -> float           # stima K in [0, 0.5]
deduction_din6935(radius: float, thickness: float, angle_deg: float,
                  reference: str = "mezzeria") -> float        # bend_deduction + k_din6935
```

La formula della fibra neutra da sola, senza nessuna calibrazione —
per chi vuole solo la matematica. `DeductionInfo` è il tipo che
ritorna `Calibration.deduction_detail()`, vedi la tabella in fondo.
Nessuno di questi tre solleva eccezioni proprie (aritmetica pura;
`radius`/`thickness` ≤0 non sono validati qui).

### `TIPI_CLIENTE`, `tipo_cliente_coerente`

```python
TIPI_CLIENTE: tuple[str, ...]
# ("zero_config", "cava_propria", "somma_interna", "misurato")

tipo_cliente_coerente(calibration: Calibration) -> list[str]
```

I quattro casi di riferimento (MAP.md D36/D39) e il controllo che una
calibrazione mantenga la promessa del `tipo_cliente` dichiarato —
ritorna la lista dei problemi trovati (vuota = coerente, o se
`tipo_cliente` non è dichiarato: controllo opt-in).

```python
from unfold import Calibration, tipo_cliente_coerente
problemi = tipo_cliente_coerente(Calibration.load("tipo_misurato"))
assert not problemi, problemi
```

---

## Leggere un disegno — `unfold.rules.read_section`

### `read_section`

```python
read_section(
    entities: list[dict],                          # stesso schema di FlatGeometry.entities
    table: SheetThicknessTable | None = None,       # None -> sheet_thicknesses.json
    join_tol: float = 1e-4,
) -> SectionReading
```

Legge un contorno (linee/archi/cerchi) e decide se è lamiera piegata —
l'inverso di `Section`: da un contorno a spessore/segmenti/angoli
invece che il contrario. Zero dipendenze da forge (MAP.md D43/D44 —
provata e ritrattata un'integrazione nativa con forge). Non solleva
mai: un contorno non riconosciuto torna con `is_sheet_metal=False` e/o
`notes` che spiega perché, mai un'eccezione.

```python
from unfold import read_section
reading = read_section(my_entities)
if reading.is_sheet_metal and reading.centerline_segments:
    # profilo a flange dritte -> BentProfile
    ...
elif reading.is_sheet_metal and reading.pure_arc_radius is not None:
    # arco puro, es. sella calandrata -> Cylinder(sector_angle=...)
    ...
```

`SectionReading`/`SheetThicknessTable`: vedi le tabelle in fondo.

---

## Modello a quote umane — `unfold.model.section`

### `Section`

```python
Section(shape: str, segments: list[float], angles: list[float],
        thickness: float, inner_radius: float)
Section.default(shape, segments, angles, thickness) -> Section          # inner_radius = 1mm fisso
Section.from_external_flanges(shape, external_flanges: list[float],
                              angles: list[float], thickness: float,
                              inner_radius: float = 1.0) -> Section
```

Il disegno in SEZIONE di un pezzo piegato (a differenza di
`BentProfile`, che è cieco al verso): `angles` porta su/giù (schema
naming, piatto=180). `Section.default` prende segmenti a mezzeria
(come `BentProfile.flanges`); `.from_external_flanges` prende quote
ESTERNO-ESTERNO (come le dà un carpentiere) e converte da sola.
**Raises** (costruttore): `ValueError` se
`len(angles) != len(segments) - 1`.

| metodo/property | ritorna |
|---|---|
| `.centerline_radius` (property) | `inner_radius + thickness/2` |
| `.name() -> str` | nome nello schema di naming dei golden (`La114ab90b114s3`) |
| `.to_bent_profile(width, calibration=None, cava=None) -> BentProfile` | il motore sotto, cieco al verso |
| `.flange_faces() -> list[FlangeFace]` | per ogni flangia, la faccia esterna se coerente |
| `.flange_quotes() -> list[FlangeQuote]` | la quota da disegnare per ogni flangia |
| `.section() -> FlatGeometry` | il contorno pieno del pezzo piegato, un loop chiuso |
| `.to_dxf(path, tolerance=0.05, quote_clearance=8.0)` | scrive la vista in sezione quotata su file (richiede forge) |

`.section()`/`._centerline_primitives()` sollevano `ValueError` se una
flangia è troppo corta per il raggio/angolo delle pieghe adiacenti
(stesso controllo di `BentProfile.develop()`, prima ancora di arrivare
alla calibrazione).

```python
from unfold.model.section import Section
sec = Section.from_external_flanges("L", [100, 110], [90], thickness=3)
sec.to_dxf("sezione_L.dxf")
```

`FlangeFace`/`FlangeQuote`: vedi le tabelle in fondo.

---

## Dati grezzi dello sviluppo — `unfold.model.geometry`

### `FlatGeometry`

```python
FlatGeometry(
    entities: list[dict], label: str = "", meta: dict = {},
    reference_entities: list[dict] = [], bends: list["BendResult"] = [],
)
```

Il contratto neutro fra `unfold` e chiunque a valle — output di ogni
`.develop()`/`.section()`. `entities` è nello stesso schema di
`forge.load_geometry()`, zero import di forge in questo modulo.

| metodo | ritorna | richiede |
|---|---|---|
| `.to_forge_result(tolerance=0.05)` | `ForgeResult` di forge | forge installato |
| `.to_dxf(path, tolerance=0.05, annotate=True, show_margin_reference=False)` | scrive un file DXF (con `annotate=True`, il blocco note include anche `.bends`, MAP.md D47) | forge installato |

**Raises**: `ImportError` da entrambi i metodi se forge non è
installato (messaggio esplicito, `pip install -e <path a dxf-forge>`).

### `polar_point`

```python
polar_point(radius: float, angle_deg: float,
            origin: tuple[float, float] = (0.0, 0.0)) -> tuple[float, float]
```

Punto a coordinate polari (angolo in gradi). Pura aritmetica, nessuna
eccezione propria.

---

## Pipeline di comodo — `unfold.human_layer`

### `develop_from_external_flanges`

```python
develop_from_external_flanges(
    external_flanges: list[float], bends: list[Bend],
    thickness: float, width: float,
    calibration: object | None = None,   # None -> "default"
    material: str = "acciaio",
    orientation: str = "horizontal",
    label: str = "bent_profile",
) -> FlatGeometry
```

Come `BentProfile(...).develop()`, ma `external_flanges` sono quote
ESTERNO-ESTERNO — la SOLA API pubblica che fa la conversione da sola:
chi la chiama non vede mai la mezzeria. Stesse eccezioni di
`BentProfile.develop()` (la conversione stessa non solleva).

```python
from unfold import Bend, develop_from_external_flanges
flat = develop_from_external_flanges(
    external_flanges=[100, 110], bends=[Bend(angle=90)],
    thickness=3, width=300,
)
```

### `export_part`

```python
export_part(
    section: Section, width: float, path: str,
    calibration: object | None = None,
    include_section: bool = False, include_header: bool = False,
    tolerance: float = 0.05, margin: float = 20.0,
)
```

Esporta un pezzo su un unico file DXF a livelli impilati in verticale:
taglio (sempre) + vista in sezione quotata (`include_section=True`) +
header con i valori di `meta` **e gli angoli di piega** (`flat.bends`,
una riga sola se sono tutti uguali — MAP.md D47) se `include_header=True`.
**Mutates**: scrive `path` su disco. **Raises**: richiede forge
installato (via `io.dxf.write_part_dxf`); propaga le eccezioni di
`section.to_bent_profile(width, calibration).develop()`.

```python
from unfold.model.section import Section
from unfold import export_part
sec = Section.from_external_flanges("L", [100, 110], [90], thickness=3)
export_part(sec, width=300, path="pezzo.dxf", include_section=True, include_header=True)
```

---

## Tipi di risultato, campo per campo

Non si costruiscono a mano (tranne per test) — sono quello che torna
indietro dalle chiamate sopra. Tutti dataclass interrogabili, niente
dict sparsi.

### `BendResult` — una riga di `BentProfile.develop().bends`, o di `Cone`/`Cylinder(faceted=True).develop().bends` (MAP.md D45)

| campo | tipo | significato |
|---|---|---|
| `angle` | `float` | gradi di rotazione da piatto |
| `cava` | `float \| None` | apertura V usata (data o da tabella) |
| `deduction` | `float` | accorciamento a mezzeria tolto per questa piega — **`BentProfile` solo**, sempre `0.0` per `Cone`/`Cylinder` |
| `setback` | `float` | `deduction / 2` — **`BentProfile` solo**, sempre `0.0` per `Cone`/`Cylinder` |
| `rule` | `str` | `"misurato"` \| `"k_materiale"` \| `"din6935"` \| `"inside_sum"` \| `"esplicito"` (`facet_k_factor` dato a mano, solo `Cone`/`Cylinder`) |
| `source` | `str` | provenienza del numero, in chiaro |
| `fallback` | `bool` | `True` se c'erano misurati per lo spessore ma non per questa combinazione |
| `k_factor` | `float \| None` | il K usato (`None` per `misurato`/`inside_sum`) |
| `bend_allowance` | `float` | materiale AGGIUNTO da questa piega — **`Cone`/`Cylinder` solo**, sempre `0.0` per `BentProfile` (lì la linea di piega è unica all'apice) |

`.to_dict()` per serializzare (usato da chi scrive metadati DXF).

### `DeductionInfo` — ritorno di `Calibration.deduction_detail()`

| campo | tipo | significato |
|---|---|---|
| `value` | `float` | accorciamento a mezzeria (mm) |
| `rule` | `str` | stesso vocabolario di `BendResult.rule` |
| `source` | `str` | provenienza in chiaro |
| `k` | `float \| None` | K usato |
| `fallback` | `bool` | vedi sopra |
| `radius` | `float \| None` | raggio RISOLTO usato per `value` — `None` per `"misurato"` (un accorciamento misurato non deriva da un raggio), `0.0` per `"inside_sum"` (MAP.md D45) |

### `SectionReading` — ritorno di `read_section()`

| campo | tipo | significato |
|---|---|---|
| `is_sheet_metal` | `bool` | il cancello: spessore riconosciuto ed esistente in tabella |
| `is_bent` | `bool` | piegato/calandrato vs lamiera piatta |
| `thickness` | `float \| None` | spessore riconosciuto |
| `centerline_segments` | `list[float]` | **solo profilo a flange dritte** — vuoto altrimenti |
| `angles` | `list[float]` | idem, schema naming |
| `pure_arc_radius` | `float \| None` | **solo arco puro senza flange** (sella) — `None` altrimenti |
| `pure_arc_angle_deg` | `float \| None` | idem |
| `notes` | `list[str]` | perché il riconoscimento non è (del tutto) riuscito |

Mai più di uno fra i due gruppi di misure valorizzato insieme — vedi
`docs/ARCHITECTURE.md`.

### `SheetThicknessTable`

```python
SheetThicknessTable(thicknesses_mm: list[float], tolerance_mm: float = 0.2)
SheetThicknessTable.load(path: str | Path | None = None) -> SheetThicknessTable  # None -> sheet_thicknesses.json
```

`.contains(thickness: float) -> bool` — entro `tolerance_mm` da un
valore della lista.

### `FlangeFace` / `FlangeQuote` — righe di `Section.flange_faces()`/`.flange_quotes()`

| campo | tipo | in `FlangeFace` | in `FlangeQuote` |
|---|---|---|---|
| `index` | `int` | ✓ | ✓ |
| `centerline_length` | `float` | ✓ | ✓ |
| `display_length` | `float` | — | ✓ — quota da mostrare |
| `display_kind` | `str` | — | ✓ `"esterno"` \| `"mezzeria"` |
| `face` | `str \| None` | ✓ `"left"` \| `"right"` \| `None` | ✓ |
| `p0`, `p1` | `tuple[float,float]` | ✓ punti di tangenza | ✓ estesi all'apice virtuale |

`face=None` (in entrambi) = nessuna faccia esterna coerente su questa
flangia — succede sull'anima di una Z/omega (MAP.md D1), mai su L/U.

---

## Il flusso completo, in ordine

```python
from unfold import Bend, BentProfile, Calibration, read_section
from unfold.model.section import Section

# 1. Generare uno sviluppo da parametri, zero disegno coinvolto
flat = BentProfile(
    flanges=[100, 110], bends=[Bend(angle=90)],
    thickness=3, width=300, calibration="default",
).develop()
flat.to_dxf("sviluppo.dxf")           # richiede forge

# 2. Le quote come le dà un carpentiere (esterno-esterno), non a mezzeria
sec = Section.from_external_flanges("L", [100, 110], [90], thickness=3)
sec.to_dxf("sezione_quotata.dxf")     # vista in sezione con le quote marcate

# 3. Leggere un contorno esistente (round-trip sullo stesso pezzo)
reading = read_section(sec.section().entities)
assert reading.is_sheet_metal and reading.is_bent
assert reading.centerline_segments and reading.thickness == 3

# 4. Dalla lettura, ricostruire e sviluppare
rebuilt = Section.default("L", reading.centerline_segments, reading.angles, reading.thickness)
flat2 = rebuilt.to_bent_profile(width=300, calibration="default").develop()
```
