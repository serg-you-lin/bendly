# SCRIPTS — script di esplorazione dell'API

Script standalone alla **radice del repo** (numerati), uno per area
dell'API pubblica di `unfold`. Girano senza argomenti
(`python 00_cone_cylinder.py`) e scrivono in `output/` (ignorata da git).
Sono la palestra per capire e collaudare l'API, non codice di libreria.

Quelli che generano il DXF richiedono forge installato a fianco
(`pip install -e ../dxf-forge`); il resto gira liscio.

| script | area API | cosa mostra |
|---|---|---|
| `00_cone_cylinder.py` | `Cone`, `Cylinder` | sviluppo liscio da calandra di un cono e di un cilindro → due DXF |
| `01_faceted.py` | `Cone(faceted=…)`, `Cylinder(faceted=…)` | sviluppo sfaccettato (N facce piane + pieghe) per chi non ha la calandra; 8 vs 12 facce |
| `02_compare_cone.py` | `Cone` liscio vs `Cone(faceted=…)` | stesso cono nei due modi, confronto numerico (angolo, area, bbox) fianco a fianco |
| `03_margin_orientation.py` | `Cone`/`Cylinder` — `orientation`, `margin` | i due parametri di layout: quale asse è il lato lungo, margine di saldatura tolto in parti uguali; `show_margin_reference=True` |
| `04_bend.py` | `Bend`, `BentProfile` | lo stesso pezzo (squadra a L "L3" di officina 1) sviluppato con quattro calibrazioni (`default` / `esempio_din_3cave` / `tipo_misurato` / `inside_sum`) fianco a fianco, confrontate con lo sviluppo vero del `.bnc`. Ogni riga dice cosa ha usato (misurato / stima DIN) e con che cava. Docstring lunga, per un piegatore: la formula, da dove vengono `r` e `K`, la scaletta del `K`, perché non serve impostare niente per partire (`MAP.md` D33) |
| `05_compare_calibrations.py` | `BentProfile(calibration=…)`, `Calibration` | per ogni DXF reale in `data_4_cloude/`: lunghezza sviluppo REALE (TruBend) vs calibrazione `default` (DIN 6935) vs calibrazione `tipo_misurato` (misurati). Richiede i dati cliente presenti. |
| `06_external_quotes.py` | `external_flanges_to_centerline()`, `centerline_to_external_flange()` | layer umano (Fase 3.1, MAP.md D28): quote esterno-esterno di una L → quote a mezzeria → `BentProfile` → DXF, e ritorno per verifica |
| `07_compare_calibrations_external.py` | come sopra + `BentProfile(calibration=…)` | la stessa L 100×110s3 (quote esterne) con tre calibrazioni — `tipo_misurato` (misurati), `default` (DIN 6935), `inside_sum` — tre DXF a confronto |
| `08_human_layer.py` | `develop_from_external_flanges()` | l'API pubblica di Fase 3.2 (MAP.md D30): stessa L 100×110s3, ma senza vedere la mezzeria — quote esterne + `Bend` dentro, `FlatGeometry` fuori |
| `09_section_view.py` | `Section.from_external_flanges()`, `flange_quotes()`, `to_dxf()` | vista in sezione del pezzo PIEGATO con le quote marcate (Fase 3.3/3.4, MAP.md D31): L 100×110s3 (quote tutte esterne) e una Z (l'anima esce dichiarata "a mezzeria", nessuna faccia esterna coerente) |
| `10_export_part.py` | `export_part()` | export a livelli impilati in verticale (MAP.md D32): stessa L 100×110s3, un file solo taglio e uno taglio+sezione quotata+header, per vedere lo stacking |

## Generatori — non sono script di esplorazione

Vivono in `tests/` perché producono artefatti (fixture / calibrazioni), non
esplorano l'API — spostati lì dal vecchio `scripts/` nel refactor a strati
(`MAP.md` D26).

| script | cosa produce |
|---|---|
| `tests/generate_section.py` | le 12 sezioni golden (L/U/Z/O × sp 1/3/10) in `data_4_cloude/sections/`, `.dxf` + `.json` |
| `tests/generate_calibration.py` | la lista "misurati" per una calibrazione a dati misurati, letta da una cartella di `.bnc`: `python tests/generate_calibration.py data_4_cloude "tipo_misurato" > calibrations/tipo_misurato.json` |
| `tests/reconstruct.py` | strumento interno Fase 1: da DXF piatto + `.bnc` ricostruisce la Section a mezzeria del pezzo reale (`section_from_part`). `python tests/reconstruct.py` stampa la ricostruzione di tutti i provini di `data_4_cloude/`. La verifica a giro chiuso è in `tests/test_reconstruct_officina.py`. |
