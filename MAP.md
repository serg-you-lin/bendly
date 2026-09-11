# MAP — decision log di `unfold`

La **memoria delle decisioni**: cosa è stato deciso e soprattutto *perché*.
Non è documentazione (quella andrà in `docs/`), non è un log di sessione
(quello è il git log, quando il repo sarà su git).

**Regola: una decisione chiusa non si re-decide da capo.** Se va rimessa in
discussione si dice esplicitamente "stiamo riaprendo la decisione N".

---

## Regole del gioco (non si cambiano in corsa)

- Prima si concorda il modello a parole, poi si scrive il codice.
- Ogni fase è piccola e si chiude con **una verifica numerica** (un numero
  che deve tornare).
- Il core (calcolo dello sviluppo **a mezzeria**) è già deciso: non si
  tocca. Tutto il nuovo lavoro gli sta intorno.
- Una cosa alla volta. Se un concetto non è chiaro, ci si ferma lì.
- Il codice nuovo è in **inglese** (funzioni, classi, test), come su
  forge (D15). I documenti (`TODO.md`, `COME_FUNZIONA.md`, `SECTIONS.md`)
  restano in italiano. **Eccezione (D36, 11 set 2026):** le decisioni
  chiuse qui sotto e "Closed questions" sono in inglese e il più brevi
  possibile — è lo storico, si legge come un changelog, non un verbale.
  Il resto di questo file (regole del gioco, stato corrente, appunti di
  Federico) resta in italiano.

---

## Dove sta cosa (5 set 2026 — riordino)

Un posto solo per tipo di informazione, per non fare più confusione fra
piano/todo/map:

- **`MAP.md`** (questo file) — le decisioni chiuse e il perché, le regole
  del gioco sopra, lo stato corrente qui sotto, le note grezze di Federico
  in fondo. L'unico posto per "cosa abbiamo deciso".
- **`TODO.md`** — l'unico posto per "cosa manca", in ordine: la roadmap
  delle fasi aperte + il lavoro concreto a breve termine.
- **`COME_FUNZIONA.md`**, **`SECTIONS.md`**, **`PIEGA_IN_ARIA_E_CONIATURA.md`**
  — documenti di dominio (spiegano un concetto), non fanno parte di questo
  riordino. `PIEGA_IN_ARIA_E_CONIATURA.md` (9 set 2026): differenza fra
  piega in aria / sul fondo / coniatura, glosario IT/EN/DE/JA e perché la
  formula DIN 6935 vale per l'aria a ~90° — serve al ragionamento sul
  non-90° (D34).
- **`TUTORIAL.md`** (aggiunto 5 set 2026) — non è un'informazione nuova,
  è solo un ORDINE consigliato per attraversare gli script numerati +
  `SCRIPTS.md`/`MAP.md`/`TODO.md`/documenti di dominio già esistenti, per
  chi deve (ri)imparare la libreria da capo.
- **`PIANO.md`** e **`appunti.md`** sono stati ritirati: il loro contenuto
  ancora valido è confluito qui e in `TODO.md`; il resto era storia già
  chiusa da una decisione (es. il bug quota-esterna-ambigua → D1, la
  convenzione di naming → D7, la regola matrice/spessore → D20). Copia di
  cortesia in `_pre_reorg_backup_5set/` (il repo non ha ancora git).

---

## Stato corrente (agg. 11 set 2026)

- **Repo git:** inizializzato l'11 set 2026, primo commit fatto (era in
  giro non tracciato fino ad ora). Trovato e chiuso PRIMA del commit un
  buco reale nel `.gitignore`: il pattern `calibrations/officina_*.json`
  non beccava più `tipo_misurato.json` dopo il rename D40 — dati veri
  misurati che stavano per finire tracciati. Nessun repo GitHub remoto
  ancora — decisione di Federico, non ancora presa.
- **Test:** 173 passati + 132 subtest, **tutti verdi** (`python -m pytest -q`,
  D41 — chiuso il disallineamento con `forge`).
- **Documentazione:** `README.md` (EN) + `README_IT.md` (IT),
  `COME_FUNZIONA.md`, `TUTORIAL.md` allineati a D36 (raggio fisso
  dichiarato, `default.json` senza cave indovinate, i quattro casi
  A/B/C/D). `docs/API.md` e `docs/ARCHITECTURE.md` ancora da scrivere
  (D16).
- **API pubblica** (`unfold.__all__`):
  `Cone`, `Cylinder`, `FlatGeometry`, `polar_point`, `Bend`, `BendResult`,
  `BentProfile`, `estimate_k_factor`, `MATERIAL_K_FACTORS`, `Calibration`,
  `DeductionInfo`, `bend_deduction`, `k_din6935`, `deduction_din6935`,
  `Section`, `FlangeFace`, `FlangeQuote`, `read_section` (D44, ex
  `interpret_section`),
  `SectionReading`, `SheetThicknessTable`, `develop_from_external_flanges`,
  `export_part`, più `__version__`.
- **Contratto con forge — invariato (D43 provata e ritrattata per intero,
  11 set 2026):** `unfold` non importa mai forge per il calcolo o per la
  lettura di un disegno — solo `io/dxf.py` lo fa, per scrivere, come
  sempre. `rules/interpret.py` ha importato forge per una notte intera
  (fase 1 di D43) e poi è tornato al loop-walker fatto a mano — non
  perché quella versione fosse rotta (167/167 verdi anche lì), ma perché
  non c'era ancora un consumatore vero (`pippo`, non ancora scritto) per
  cui decidere quel contratto. Vedi `docs/ARCHITECTURE.md`.
- **Priorità di fondo (D36, 11 set 2026):** la formula generica è il
  prodotto; i dati misurati di una singola officina sono un bonus/banco di
  prova, mai un blocco. Ogni scelta di default si controlla contro i
  quattro casi A/B/C/D (vedi `TODO.md`).

### Cosa manca, in ordine (vedi `TODO.md`)

1. ✅ Pulizie di impostazione: versione via `importlib` · `MAP.md`
   (questo file) · script di esplorazione numerati `00_*`…`05_*` alla
   radice + `SCRIPTS.md`.
2. ✅ Fase 1 — ricostruzione dai `.bnc`/DXF reali, giro chiuso su tutti e
   20 i provini L / U / Z / omega × spessori, entro 0.01 mm.
3. ✅ Fase 2 — lettura guidata del motore, `BendResult` interrogabile,
   rinomine in inglese.
4. ✅ Fase 3 — layer umano (quote esterne, vista in sezione, export a
   livelli).
5. ✅ Fase 3.5 — priorità capovolta: formula generica prima della
   calibrazione per officina (D36).
6. Fase 4/5 — scatole, pieghe su più assi, info di piega nei DXF —
   parcheggiate.

---

## Decisions

### D1 — Core computes at CENTERLINE, not outer quotes ✅

`BentProfile.flanges` are centerline-to-centerline lengths. A flange shared
between two opposite-direction bends (a Z web, an omega web) has no
consistent "outer" face — the two adjacent bends see opposite faces as
outer, so an outer-quote model was off by `s·tan(angle/2)` per ambiguous
flange (−2mm on a 90°/2mm Z, −4mm on an omega). Centerline removes the
ambiguity at the root (verified against an independent geometry script,
diff 0.0000) and matches how Federico models parts in CAD.

### D2 — Development is linear: Σ segments − Σ deductions ✅

Proven on 20 real officina_1 DXFs (L/U/Z/omega × 3 thicknesses): bend
deduction is a pure constant of (thickness, V-opening, angle), identical
across shapes within 0.00005mm. No shape effect, no arc region to model —
plain sum and subtraction.

### D3 — SUPERSEDED by D33

Originally: three separate bend-deduction "rules" (din6935 / misurati /
inside_sum). D33 replaced this with one formula and a two-input ladder
(r, K) — those were never different calculations, just different sources
for r and K.

### D4 — Configuration = one calibration file per shop. Partially SUPERSEDED by D33/D36

Originally introduced "profiles" (later renamed `calibrations`, D23) and a
"manual mode vs calibration mode" split with no default. D33 removed
manual mode; D36 gave `default` a real zero-config path. Still valid: one
shop = one self-contained file (D5).

### D5 — No inheritance between calibration files ✅

A calibration used to inherit its die table from `default`
(`"eredita": "default"`); dropped — reading one file meant opening two and
merging them mentally. Every calibration now carries everything it needs.
Federico: "flatten it, so we stop thinking about it."

### D6 — Federico's surname is never used as a scattered reference ✅ (permanent, refined 5 Sep 2026)

Not to address him in chat, not in folder/module/config names or code
comments. His shop is `officina_1`. Exception: legitimate, isolated
authorship (e.g. `pyproject.toml`'s `authors` field) — package paternity,
not "labelling" code with his name.

### D7 — Naming scheme for test pieces / sections ✅

`SHAPE` + `segment`/`angle` pairs + `s<thickness>` (e.g.
`Ua60ab90b110bc90c60s3`). Segments are centerline lengths, the same
numbers passed to `BentProfile.flanges`. Angles: flat=180, up=90, down=270.
No radius in the name (die/punch-dependent, a production detail).

### D8 — A section fixture holds only the full-thickness outline ✅

No drawn centerline — it's derived by offsetting both faces inward by
half the thickness.

### D9 — Section fixtures have no mathematical role ✅

The triple signal (D10) is enough to recognize bent sheet metal; fixtures
exist only for the eye and the viewer. Not versioned, regenerable.

### D10 — "This is bent sheet metal" = a triple signal ✅

Parallel faces at a constant distance (= candidate thickness) that also
appears in the known-thickness table, plus rounded corners as
concentric-arc pairs whose radius difference exactly equals that
thickness. Implemented in `interpret_section`, which also runs the
reverse direction (section → thickness/segments/angles). Verified on 12
fixtures, segments within 0.05mm.

### D11 — Fixed 1mm symbolic inner radius for TEST FIXTURES only ✅

Same for every thickness, used purely so the recognition pattern (D10) has
a radius to look for — it never enters the real bend-deduction formula.
Not to be confused with D36's fixed fallback radius, a different constant
for a different purpose.

### D12 — The internal reconstruction tool is NOT public API ✅

Anyone with a real `.bnc` + flat DXF already has the development — no need
to recompute it. Exists only to build our own golden tests, never in
`unfold.__all__`.

### D21 — Bend direction is read from the flat DXF's layer ✅

`Bend` layer = upward (90 in the naming scheme), `MBend` = downward (270).
Lets reconstruction recover both segments and direction from the flat DXF
alone; the `.bnc` is only needed for the deduction and reference length.

### D22 — Phase 1 covers single-axis bending; press-stroke count is irrelevant ✅

Reconstruction works on the finished geometry; a pre-bend stroke (a
different angle than the final one) is discarded. All 20 real test pieces
close within 0.01mm. Boxes / multi-axis bending stay out of scope
(→ Phase 4).

### D13 — Golden tolerance: 0.01mm for `officina_1`, 0.1mm for `din6935` ✅

`officina_1` goldens use the exact measured deduction, so the round trip
must land at rounding precision. The 0.1mm margin is only for `din6935`
goldens, a formula with an honestly-declared residual error.

### D14 — Never regenerate a golden just to make a test pass ✅ (permanent)

Prove the code is right first; only then regenerate the fixture, one at a
time, diff checked by hand.

### D15 — New code in English, documents in Italian ✅ (from Sep 2026)

Function/class/variable/test names in English, like `forge`. Existing
Italian code stays as-is until touched. Documents stay Italian.
**Narrowed by D36**: this log's closed decisions and "Closed questions"
are the one exception, English and short.

### D16 — Big layered refactor deferred until after Phase 2 ✅ (4 Sep 2026)

Moving many modules quickly is what made `unfold` stop feeling like
Federico's own project. Done later (D26), together with the double
README (`README.md`/`README_IT.md`, 6 Sep 2026). `docs/API.md`/
`docs/ARCHITECTURE.md` still to write.

### D17 — Version lives only in `pyproject.toml` ✅ (4 Sep 2026)

Read at runtime via `importlib.metadata.version("unfold")`, falls back to
`"0.0.0+dev"` if not installed. No duplicated version number in code.

### D18 — Customer data stays out of GitHub ✅

`.bnc`, TruBend DXFs, all of `data_4_cloude/` are officina_1's real data,
excluded via `.gitignore` — right for that shop, not a universal truth.

### D19 — Cone/Cylinder: outer diameters in, development on the mean fiber ✅

Diameters passed to `Cone`/`Cylinder` are outer; development uses
`D_mean = D_outer − thickness`.

### D20 — Goldens only within realistic die/thickness ranges ✅

Air-bending rule of thumb: V-opening ≈ 6–10× thickness. Out-of-range
samples (e.g. a 10mm L bent with V16, physically unrealistic) are kept as
"doesn't match, and shouldn't" references, not calibration data.
`tooling.json` carries the real die set; die OW308-T (0° punch angle)
behaves like coining, not air bending — its radius comes from the punch,
not V/6 (ties into `PIEGA_IN_ARIA_E_CONIATURA.md`, D34).

### D24 — Each bend's calculation is a queryable object: `BendResult` ✅

Replaced scattered parallel lists (`k_factors`, `bend_allowances`, …) with
one `BendResult` per bend in `flat.bends`, carrying `angle`, `cava`,
`deduction`, `setback`, `rule`, `source` (plain text — a `.bnc` path, or
"DIN 6935 …"), `fallback`. General principle saved in the
`python-code-style` skill ("queryable for understanding"). *The rule
values shown here (`misurati`/`din6935`/`inside_sum`/`manuale`) are the
pre-D33 names — D33 renamed them (`misurato`/`k_materiale`/`din6935`/
`inside_sum`, no more `manuale`).*

### D23 — Batch rename package ✅ (4 Sep 2026)

`profiles`/`Profilo` → `calibrations`/`Calibration`; `Dima` → `Section` (a
fixture is the *section* of a bent part). Full before/after list: git
log. Confirmed architecture note: bend **direction** (up/down) lives in
`Section`, not in `Bend` — the core engine stays blind to it (D1).

### D26 — Layered structure applied: `model/core/rules/adapters/io` ✅ (5 Sep 2026)

`model/` = pure dataclasses (`FlatGeometry`, `Section`); `core/` = the
calculation engine, zero I/O (`Cone`, `Cylinder`, `Bend`, `BentProfile`);
`rules/` = domain rules/thresholds (`deduction.py`, `interpret.py`);
`adapters/` = the one module that knows an external CAM format
(`trubend.py`); `io/` = the one module that imports `forge` (`dxf.py`).
Public API unchanged, clean break, no compatibility aliases. 102 tests
green, unchanged from pre-refactor.

### D25 — `Cylinder.margin` cuts the circumference, not the height ✅ (5 Sep 2026)

Federico uses `margin` for the roll's longitudinal seam (the two edges
that meet when you roll the flat sheet), not an axial cut — aligned with
`Cone.margin`. `Cylinder.orientation` default also switched
`"horizontal"` → `"vertical"`: the old default silently swapped X/Y
regardless of which dimension was actually larger.

### D30 — Human-layer public API: `develop_from_external_flanges()` ✅ (5 Sep 2026, Phase 3.2)

Same as `BentProfile.develop()` but flanges are outer-to-outer quotes, not
centerline — glues `external_flanges_to_centerline()` (rules) to
`BentProfile` (core). Doesn't fit any of the 5 existing layers, a
deliberate one-file "human layer" (`unfold/human_layer.py`) rather than a
full `pipeline/` package for one function. In `unfold.__all__`: meant to
be called from outside `unfold` (e.g. a downstream cutting/nesting
generator).

### D31 — Section view with quotes ✅ (5 Sep 2026, Phase 3.3+3.4)

A flange has a coherent "outer face" only when its two adjacent bends turn
the same way (L, U) — not when they turn opposite ways (a Z/omega web,
same ambiguity as D1). `Section.flange_faces()`/`flange_quotes()` compute
this per flange and return the outer quote when coherent, the centerline
quote with an explicit `display_kind` flag otherwise — never a
silently-wrong number. `Section.to_dxf()` stays an internal
verification/demo tool only, not the integration point for downstream
consumers (that's the data: `flange_quotes()`/`flange_faces()`).

### D32 — Layered DXF export, stacked vertically: `export_part()` ✅ (5 Sep 2026)

One DXF with selectable layers (cut only / +header / +section view / all
three), always stacked vertically and left-aligned — avoids a full
page-layout problem. The section view is drawn as raw lines/arcs, never
through `forge.heal_and_detect()` — otherwise it would be detected as a
second cuttable part, which it isn't.

### D29 — Reopens D23: renamed the remaining Italian method names on `Calibration` ✅ (5 Sep 2026)

D23 had deliberately left `Calibration`'s Italian method names alone;
done now, one pass, no behavior change. Deliberately NOT touched: the
JSON **keys** inside `calibrations/*.json` — a data format on disk, not
Python identifiers; nor `adapters/trubend.py`'s Italian dataclasses, for
when that module is next touched anyway.

### D28 — Outer↔centerline translator for ONE flange's length ✅ (5 Sep 2026, Phase 3.1)

Different from `external_to_centerline_deduction()` (a whole bend's total
deduction): converts a single flange's outer-to-outer length, the way a
carpenter reads a drawing, to the centerline length `BentProfile.flanges`
wants. Proven algebraically that the outer↔centerline offset is
radius-independent — always `(thickness/2)·tan(angle/2)` per adjacent
bend (the radius term cancels).

### D27 — No geometry package shared across projects, for now ✅ (5 Sep 2026)

Considered a `geometry` package shared between `forge`/`snapmark`/
`unfold`, decided against: one more project to version and install, and a
shared library risks bending to compromises that suit none of the three
if their needs diverge. Revisit only if real duplication becomes painful.

### D33 — ONE formula for bend deduction; calibration supplies r and K; no more "manual mode" ✅ (6 Sep 2026)

After D32, deduction had two silently-competing user-facing "modes"
(manual radius+K, calibration+rule enum) — wrong the moment both were
given. Settled model: **one formula** (neutral-fiber method,
`BD = 2·(r + s/2)·tan(β/2) − β·(r + K·s)`), fed by two independently
sourced ladders:

- **r**: from the calibration's die table (`r ≈ cava/6`), an explicit
  per-bend `Bend(cava=...)`, or an explicit `Bend(radius=...)` override
  when the radius is known directly (crowned, coined) — an exception, not
  a mode.
- **K**: (1) a measured value for that exact (thickness, cava, angle) if
  the calibration has one — ground truth from a real `.bnc`; (2) the
  calibration's `k_per_materiale` for the given material — what TruBend
  itself keeps in its material database; (3) a DIN 6935 estimate from r/s
  alone, material-blind, steel-tuned.
- `inside_sum` stays a separate escape hatch: `BD = s·tan(β/2)`, r and K
  ignored entirely — the "I don't want your math" shortcut many shops
  actually use.
- `calibration` defaults to `"default"` — `BentProfile(...).develop()`
  works with zero configuration, always declared in `BendResult.source`,
  never silent.

`BendResult.rule` ∈ {`misurato`, `k_materiale`, `din6935`, `inside_sum`}.
Named presets: `default` (zero-config), `din6935` (pure norm, caller
supplies cava per bend), `esempio_din_3cave` (die-table-only template),
`inside_sum`, `officina_1` (real measured rows). 131 tests green at the
time; on officina_1 data `default`'s DIN estimate was within ~0.1mm at
1mm stock, ~0.45mm at 3mm, worse at 10mm — `officina_1` (measured) exact
everywhere.

### D34 — 9 Sep 2026 TruBend samples: officina_1 `misurati` from 5 to 19 rows ✅

New real samples across the full 0.5–20mm thickness range (still S235;
inox/aluminium held back for a later `.fx` re-export), plus the real die
table (`CAVE_officina_1.txt`) and tooling geometry. Confirmed: deduction
stays a pure (thickness, cava, angle) constant across shapes; **the
V-opening genuinely matters** — same thickness, different die, 0.3–1mm
shift (sp4: V20→6.869 vs V24→7.132; sp8: V40→14.043 vs V60→15.043).
`default`'s DIN estimate error across the range: ~0.1–0.4mm up to 3mm,
~1mm mid-range, **−3.2mm at 20mm/V90**. Added merge-in-place to
`tests/generate_calibration.py` (refreshes only `misurati`, keeps the
rest of the file). Two unrelated test-discovery regressions from the new
file-naming scheme fixed.

Left open at the time (folded into D36's persona framing and `TODO.md`):
non-90° samples not yet in the golden set; inox/aluminium
`k_per_materiale` still placeholder; `officina_1.json`'s die table not
yet reconciled against `CAVE_officina_1.txt`'s multiple V-options per
thickness; 10 pre-existing `to_dxf` test failures from unrelated `forge`
API drift (`ForgeResult.part_count`), left as-is.

### D35 — `inside_sum` = raw interior-quote sum, zero deduction ✅ (10 Sep 2026)

A real customer drawing (8mm steel bracket) declares its flat length as
the exact sum of the two **interior** dimensions, radius 0, no correction
— "at least in Italy this is standard practice, full stop" (Federico).
The previous `inside_sum` was a *deduction rule* applied to centerline
flanges, giving the wrong number to anyone actually holding interior
quotes. Redefined: `inside_sum` means working entirely in interior
quotes — the flanges passed in already are interior-to-interior, and the
development is their exact sum. The one calibration where
`BentProfile.flanges` are interior quotes, not centerline.

Tried and rejected in the same pass: loading the `PARAMETRI DI PIEGA_*`
manufacturer tables as a data source or middle rung. On the 10 points
with measured+table+formula, the table was less accurate against real
officina_1 values than the formula (median error 0.65mm vs 0.24mm).
Deduction stays a two-rung ladder: measured → formula.

### D36 — Generic formula is the product; shop calibration is a bonus, never a gate; declared fixed radius replaces silent guessing ✅ (11 Sep 2026)

Engineering effort had drifted toward treating officina_1's measured
`.bnc` data as *the* path to reliability, roadmap organized around
"waiting for more samples from Federico". Corrected hard: `unfold`'s
purpose is a layer for a future generic interpreter — reads any drawing
via `forge`, produces a laser-cuttable development — that must work for
**any** shop, cold, with zero shop-specific data, because no future shop
will spend a day measuring bends just to make this tool trust them; a
tool that only works well for officina_1 isn't worth building.

Decided:

- The generic formula (neutral-fiber method — the one every CAD uses)
  **is** the product. Shop-measured data (`misurati`) is downgraded from
  "the path to reliability" to a validation/improvement dataset for the
  generic formula, plus an optional per-shop override — never a blocking
  dependency. Roadmap items stop being parked on "waiting for the next
  `.bnc` drop" (see `TODO.md`).
- Four reference personas to check every setup/default decision against:
  **A** unknown user, zero config, zero questions asked; **B** nearby
  shop, gives *only* a thickness→die table, never measures anything;
  **C** shop that wants raw interior-sum only, refuses to hear about
  K-factor; **D** shop with CAM, willing to spend real hours producing
  measured data for quoting accuracy. A choice that only serves D and
  burdens A/B/C is usually the wrong one here.
- Fixed a real bug found while working this: `default.json`'s die table
  was a byte-for-byte, unlabeled copy of officina_1's own (itself still
  unverified against `CAVE_officina_1.txt`). Case A was silently
  inheriting one shop's guesses disguised as "generic". `default.json`
  now lists common thicknesses mapped to `null` — an honest "I don't
  know your die, fill it in" template, not an invented one.
- Closed a gap: a 6 Sep rule ("never derive a missing physical quantity
  by scaling another one — `r = thickness` was explicitly rejected") had
  only ever been recorded in an assistant memory file, never in this
  log, so the code kept silently violating it (`bend_allowance_din()`'s
  fallback was `r = thickness`). Formalized here instead:
  **`DEFAULT_UNKNOWN_RADIUS_MM = 1.0`**, a fixed constant (never scaled
  from thickness), used only when neither an explicit radius nor a known
  die exists for that thickness, always declared in `BendResult.source`.
  Distinct from D11's 1mm, a symbolic radius for test-fixture pattern
  recognition that never enters a real deduction.
- A calibration with no die table at all (the bare `din6935` preset)
  keeps raising an error demanding `cava=`/`radius=` per bend — a
  deliberate strict mode, untouched by the fallback above.
- `unfold/rules/deduction.py`, `calibrations/default.json`,
  `tests/test_deduction.py`, `tests/test_bend.py`. 139 tests green (same
  10 pre-existing `forge`-drift reds as D34, untouched).
- Documentation policy narrowed for this file only (amends D15): from
  here on this log's closed decisions and "Closed questions" are English
  and short — everything else (`TODO.md`, `COME_FUNZIONA.md`, chat)
  stays Italian.

Open, deliberately not solved here (see `TODO.md`): `default.json`'s
thickness list is itself an unvalidated guess at "common sizes"; the K
ladder's middle rung (`k_per_materiale`) still has no source beyond
officina_1's own unverified placeholders.

### D37 — No trustworthy generic K-factor-by-material source exists; removed officina_1's invented inox/aluminium placeholders ✅ (11 Sep 2026)

Checked whether a published, citable K-factor-by-material table could
populate the calibration ladder's middle rung generically (for cases A/B,
who have no press database) instead of leaving it empty. Searched
published sources (thefabricator.com/Steve Benson — already this
project's trusted reference for air-bending practice, plus several vendor
technical pages) for mild steel / stainless / aluminium K-factor ranges.

Found: no single authoritative table exists. Every source gives a wide,
partly contradictory range — stainless steel alone is cited anywhere from
0.30 to 0.50 depending on source and bend regime (air vs. bottoming,
tight vs. large radius); aluminium and mild steel ranges overlap
similarly (~0.33–0.45). This matches what D35 already found for steel
specifically: a generic manufacturer table was *less* accurate than the
material-blind DIN r/s estimate on real measured data. A real,
trustworthy material K comes only from actual measurement on a real
press — which is exactly what a shop's own material database (TruBend's
`.fx` export) is, and exactly why it's shop-specific, not withheld out of
caution.

Consequence: `k_per_materiale`'s middle rung stays legitimately empty for
anyone without real press data — that's the honest state of the art, not
a gap `unfold` is missing something to fill. Found a related bug while
checking: `officina_1.json`'s inox (0.2) / aluminium (0.15) placeholders
were *below every published range found* (0.3–0.5) — not a rough
estimate, an actively wrong number, worse than falling back to DIN.
Removed; falls back to the DIN r/s estimate now, same as any
unconfigured material. `k_per_materiale` returns when Federico's `.fx`
re-export (D34) gives real values.

### D38 — Real included angle from the `.bnc`'s Sollwinkel; 6 open non-90° L goldens closed ✅ (11 Sep 2026)

TODO.md items 1–3. `tests/reconstruct.py` always assumed 90°/270° from the
flat DXF's `Bend`/`MBend` layer (direction only). Now: direction still
from that layer, magnitude from the paired `.bnc`'s `Sollwinkel` per bend
(`unfold/adapters/trubend.py` already parsed it, just wasn't used).
Verified on a real file before trusting it: `La114ab120b114s1.bnc`'s
Sollwinkel reads exactly `120.0`, matching the `ab120` filename token.

Two real bugs found and fixed on the way:

- **Angle-convention mismatch.** `Calibration._measured_row()` matches
  against `Bend.angle` (rotation from flat, flat=0° — what the core
  formula uses), not the Sollwinkel/naming-scheme value (included angle,
  flat=180°). `tests/generate_calibration.py` was about to store
  Sollwinkel directly into `misurati.angolo` — wrong for anything but 90°
  (only case where the two conventions coincide). Fixed: stores
  `|180 − Sollwinkel|`.
- **Pre-bend contamination risk.** Naively trusting every `.bnc` row's
  Sollwinkel would have pulled pre-bend strokes into `misurati` as if
  they were real finishing bends (confirmed on `O10.bnc`: 5 recorded
  strokes for 4 geometric bends, first one a 120° pre-bend of corner 1 —
  exactly the pattern D22 already knew about, just never seen from this
  angle). `misurati_da_bnc()` now only trusts a multi-stroke `.bnc` for
  its 90° rows (pre-bends essentially never land exactly on 90°); a
  single-stroke `.bnc` is trusted for any angle, but only when the
  filename doesn't promise more bends than it recorded — found a real
  case of that too: `Za60ab50b100bc250c50s10.bnc`'s name promises 2 bends
  but `TEIL_BIEGEN`/`BIEGESCHRITTDATEN` only ever recorded one
  (`Biegenummer` never reaches 2). Cause (Federico): the Z's second bend
  doesn't sit against the back gauge — after the first bend the part
  isn't flat any more, so that flange never goes through the machine's
  normal automatic-positioning cycle and gets no clean measured
  `Biegeverkuerzung` at all, not a parsing gap. Both Z files affected are
  excluded; not a bug to chase further, a different data source is
  needed for that number (e.g. measuring the finished part by hand).

**Closed** (`reconstruct.is_reconstructable_name()`, TODO.md items 1–3):
the 6 `La114ab{120,150}b114s{1,3,10}` samples — all **open** angles
(included ≥ 90°, still plain air bending) — are now real goldens in
`officina_1.json` (`misurati`, angle-matched, `rule="misurato"`, not a
DIN fallback) and in `test_reconstruct_officina.py`'s loop. Round trip
within 0.005mm (well under the 0.01mm bar, D13); reconstructed centerline
segments land on the nominal 114mm sketch within 0.0003mm.

**Deliberately still out**, same file naming, same session — not a
regression, a documented limit: `La114ab{50,70}...` (**closed** angles,
included < 90°) reconstruct to the wrong nominal length (off by
2–5mm) when treated as plain air bending — confirms D34/
`PIEGA_IN_ARIA_E_CONIATURA.md`: that regime is coining, a different
process, and `Biegeverkuerzung` there isn't the number this formula
expects. `is_reconstructable_name()` excludes them on purpose. Z/omega at
non-90° stay out too (multi-bend, plus the export-completeness problem
above). 145 tests green (same 10 pre-existing `forge`-drift reds,
untouched).

### D39 — `tipo_cliente`: the four reference personas become a checked field, not a letter ✅ (11 Sep 2026)

Federico: every calibration needs a self-declared pointer to which of the
four reference personas (D36) it is, in standard naming, not the A/B/C/D
shorthand this log had been using. Named them `zero_config` /
`cava_propria` / `somma_interna` / `misurato` (`TIPI_CLIENTE`,
`unfold/rules/deduction.py`), added to all 4 shipped calibration files.

Made it more than a label: `tipo_cliente_coerente(calibration)` checks
the file's actual content against what its `tipo_cliente` promises
(`zero_config` can't carry real dies or measured rows; `cava_propria`
must have at least one; `somma_interna` must set `metodo: "inside_sum"`;
`misurato` must have measured rows) — optional (skipped when a
calibration doesn't declare `tipo_cliente` at all), but a test now runs
it over every file in `calibrations/` on every `pytest`. Built to catch
exactly the bug D36 found by hand: `default.json` silently carrying
officina_1's real dies while claiming to be generic. Both new names in
`unfold.__all__` (`TIPI_CLIENTE`, `tipo_cliente_coerente`). 149 tests
green (same 10 pre-existing `forge`-drift reds, untouched).

### D40 — `officina_1` renamed to `tipo_misurato`; the `misurato` tier should carry its own die table too ✅ (11 Sep 2026)

Federico: `officina_1` must not appear in the codebase as if it were the
canonical example of the `misurato` tier — it's one real shop's name, not
a standard. Renamed the calibration file and every code/test/script
reference: `calibrations/officina_1.json` → `calibrations/tipo_misurato.json`,
`Calibration.load("officina_1")` / `calibration="officina_1"` →
`"tipo_misurato"` everywhere (04/05/07/08/10 scripts, `tests/test_bend.py`,
`test_deduction.py`, `test_golden_officina.py`, `test_human_layer.py`,
`test_reconstruct_officina.py`, `tests/generate_calibration.py`). Content
unchanged (still officina_1's real measured rows — that's legitimate
ground truth, D36 already reframed it as a validation dataset, not a
branding problem). Left alone on purpose: mentions of "officina 1" as
*provenance* of real test data (`data_4_cloude/`, D18's already-established
gitignored real-data zone, docstrings explaining where a golden DXF came
from) — that's a fact about the data's origin, not the calibration's
public name, and D18 already keeps the raw files out of git.

Checked whether the other three tiers need a dedicated example file too:
no — `esempio_din_3cave.json` already *is* the `cava_propria` template,
`default.json` and `inside_sum.json` already cover `zero_config` and
`somma_interna`. Nothing new to create there.

Separate, real question raised in the same message: should a `misurato`
calibration be required to also carry a real `cava_per_spessore`? Yes —
anyone with a CAM/press almost certainly already knows their own dies
too, so asking costs nothing, and without it every (thickness, cava,
angle) combination outside the measured rows falls all the way to
`zero_config`'s crude fixed-radius fallback instead of a real cava.
`tipo_cliente_coerente()` now flags a `misurato` calibration with no real
`cava_per_spessore` value as incoherent (soft check, same mechanism as
D39 — never blocks `develop()`, only caught by the test that runs it over
every file in `calibrations/`). 149 tests green, unchanged.

### D41 — Forge API drift fixed: `ForgeResult.parts`/`.part_count` → `.clusters`/`.cluster_count` ✅ (11 Sep 2026)

The 10 tests left red since before D34 (`forge` in motion, `unfold` not
touched) had one single cause: forge renamed its part model (`Part` →
`ForgeCluster`) and `ForgeResult.parts`/`.part_count` along with it, as
part of Federico's work making forge's entity roles extensible for
subclassing consumers. `unfold/io/dxf.py` is the only module that reads
`ForgeResult` (D26) — two call sites (`export_part`'s cut-position lookup,
`_write_meta_block`'s note placement), both `result.parts[0].outer.bbox`
→ `result.clusters[0].outer.bbox`. `tests/test_to_dxf_integration.py`'s
assertions renamed the same way. Nothing else in forge's public surface
moved (`load_geometry`, `heal_and_detect`, `to_dxf` unchanged). **All 159
tests green, zero red** — first time this session the suite has been
fully clean.

---

### D42 — Drawing-reading architecture: `interpret_section()` is the one router, no new geometry classes

Question raised by Federico: with `Cone`/`Cylinder`/`BentProfile` (manual
values) and `interpret_section()` (the "dima" detector — reads a section
outline, decides if it's bent sheet metal, recovers thickness/centerline)
already existing, can the three generator classes take drawing data
straight from what the detector already finds, without new classes?

**Yes for `BentProfile`, no as-is for `Cone`/`Cylinder` — same detector,
two different landing classes, decided by shape:**

- `interpret_section()`'s signal (parallel faces / concentric-arc pairs
  differing by exactly the thickness) is generic — it already fires
  correctly for a tube's top view (two full concentric circles, radii
  differing by wall thickness) and for a calandrata "sella" in section
  (two concentric *partial* arcs, e.g. R300 over 60°, closed by two
  thickness-wide cap edges) — not just for a bent L/U/Z profile. Same
  code, no changes needed for detection itself.
- Where the detector's chain-recovery (`_recover_centerline`) finds an
  **open profile with real straight flanges** framing each bend →
  destination is `BentProfile` (`Section.from_external_flanges`-style
  constructor, the parked `from_flat_segments` idea in `TODO.md`).
- Where it finds a **closed or partial arc with no straight flange**
  (full tube, or a sella's pure curve) → destination is `Cylinder`/`Cone`,
  **not** `BentProfile`. Verified in `section.py`: `BentProfile`'s
  `_centerline_primitives()` computes `straight = segment - setback_before
  - setback_after` per flange and raises ("too short") whenever that's
  <= 0 — the model hard-requires non-zero straight length on both sides
  of every bend. A pure roll (no flat flange before/after the curve) has
  none, so it structurally cannot go through `BentProfile`; forcing it
  through breaks, it isn't a data problem.
- `Cylinder.develop()` today always develops the full 360°
  (`width = π × diameter_mean`). It needs one generalization — an
  optional sector angle, defaulting to 360° — so a partial roll (the
  sella case) becomes `width = radians(angle) × mean_radius`, same
  formula family `Cone`'s annular sector already uses. Still `Cylinder`,
  no new class.

**Two concrete gaps in `interpret_section()` to close before any of this
reads a real drawing** (not yet done, tracked in `TODO.md`):
1. it filters entities to `type in ("line", "arc")` — a full circle in
   the `FlatGeometry` entity schema is `type: "circle"`, a different tag,
   and is silently dropped today (needs explicit circle handling, e.g.
   treat as a 360° arc).
2. the cap/chain recovery assumes at least one straight-flange segment
   in the walked chain; a pure-arc profile (cap → arc → cap, zero
   flanges) needs its own short-circuit path that hands the recovered
   radius/angle straight to `Cylinder`/`Cone`'s sector math, instead of
   trying to force it through the flange-based `segments`/`angles` shape
   `BentProfile` expects.

Real motivating case from the shop: "selle" (saddle brackets) — rolled
sheet with slots (asole) cut in, e.g. R300 over a 60° arc. The slots are
a feature layered on top of the shape, out of scope for this decision.

---

### D43 — `unfold` moves onto `ForgeDocument`/`Edge` natively; reopens the "no forge in calculation" boundary (Stato corrente, line 76-78)

Reopening, explicitly: the standing rule "`unfold` never imports forge
for the calculation, only `io/dxf.py` does, optionally" is superseded.
Reason: building D42 surfaced real, unnecessary duplication —
`interpret.py`'s hand-rolled `_Edge`/`_split_into_sides`/`_order_chain`
reimplement in miniature, for one narrow case (2 caps + 2 face chains),
what forge's own topology engine (`forge/core/topology/graph.py`,
`loop_finder.py`) already does in general. The D41 test breakage
(`ForgeResult.parts` → `.clusters`) was also a symptom of the same
seam: a translation boundary between two geometry schemas that drifts
when either side changes. And the forward direction of this project
(read a real drawing, D42) needs exactly forge's strength — genuine
loop-finding on noisy real geometry — not a bespoke reader that only
handles the shapes we thought to test.

**The split that stays true regardless — pure math is not what's
moving.** `core/bend.py` (`Bend`, `bend_allowance`, `estimate_k_factor`,
`k_din6935`) takes and returns plain floats/lists — no geometry object
of any kind. That layer stays dependency-free; nothing about this
decision touches it. What moves is the **geometry representation and
reading layer**: `FlatGeometry`'s entities today are plain dicts
(`{"type": "line", ...}`), a schema `unfold` invented to stay
forge-neutral. Going forward that layer speaks forge's own domain
object directly — `ForgeDocument`/`Edge`
(`forge/model/document.py`/`forge/core/topology/edge.py`) — not a
lookalike.

**Why now, not "slim library + adapter later" when `unfold` plugs into
a bigger interpreter**: Federico's own framing settles it — if
`ForgeDocument` is meant to be the shared arena a CAD-reading agent
operates in, a second incompatible schema on unfold's side is pure
translation cost paid at every call, with a proven failure mode (D41)
and no offsetting benefit. The "keep the library dependency-free"
instinct is sound in general, but it already only ever applied to the
math (see above) — the geometry-representation layer was never truly
independent, it was already declared "same schema as `forge.load_geometry()`"
(line 76-78), just duplicated by hand instead of imported.

**Cost, stated plainly:** forge becomes a hard dependency of `unfold`
core, not an optional one for `to_dxf()` only — `unfold`'s pitch of
"zero dependencies for the calculation" (`pyproject.toml` description)
goes away. Checked what that actually pulls in: forge's own
dependencies are `ezdxf>=1.1`, `shapely>=2.0`, `numpy>=1.24` — a
standard, stable 2D-geometry stack, not heavy (no compiled ML/graphics
toolchains). forge itself stays an unpublished local sibling package
(`pip install -e ../dxf-forge`), same install story as today, just
required instead of optional.

**Phased migration (each phase closes with the test suite green before
the next starts — this is a multi-session migration, not one phase):**

0. ✅ This decision + `pyproject.toml` updated (dependency comment,
   description no longer claims zero dependencies).
1. ✅ `interpret_section()` rebuilt on forge's `Edge`/`graph.py`/
   `loop_finder.py` instead of `_Edge`/`_split_into_sides`/
   `_order_chain` — folds in D42's step 3 (pure-arc routing) directly
   on the new foundation instead of building it twice. `forge.load_geometry()`
   builds the `ForgeDocument` (same dict schema `io/dxf.py` already fed
   it the other way); `build_node_graph()` + `LoopFinder()` return the
   closed loop already ordered, so splitting it into the two face
   chains is index slicing between the two end-cap positions, not a
   hand-rolled walk. A bare calandra arc (cap→arc→cap, zero flange —
   the sella case) is recognized directly: `SectionReading` gained
   `pure_arc_radius`/`pure_arc_angle_deg`, left `centerline_segments`/
   `angles` empty for that shape instead of forcing it into
   `BentProfile`'s. `unfold` now imports forge starting at
   `rules/interpret.py` (`unfold/__init__.py` docstring updated to
   match). 167/167 tests green.
2. ~~`Cone`/`Cylinder`/`BentProfile.develop()` build forge `Edge`
   objects; `FlatGeometry` retired.~~ **Retracted (11 Sep 2026, before
   writing any code for it)** — re-read
   `forge/adapters/geometry/loader.py` while starting this phase:
   `forge.load_geometry()` (already used by `io/dxf.py`) is not a
   workaround, it is forge's own documented, intended entry point for
   "geometry computed elsewhere" — its own docstring example is a cone
   sector. Hand-building `Edge`/`LineSeg`/`ArcSeg` in the generators
   would redo, worse, exactly what `load_geometry()` already does
   (node rounding, role assignment, degrees→radians) — the same
   duplication class this decision exists to remove, just inverted.
   `FlatGeometry` is also not redundant with `ForgeDocument`: it carries
   `meta` (the officina-readable numbers — radius, K, sector angle) and
   `reference_entities` (the dashed welding-margin outline) — domain
   data `ForgeDocument`/`heal_and_detect()` has no slot for and no
   reason to compute. Dict-emitting generators + `FlatGeometry` were
   never the problem; kept as they are.
3. ~~`io/dxf.py` drops `to_forge_result()`.~~ **Retracted with step 2** —
   `to_forge_result()` is the correct minimal use of `load_geometry()` +
   `heal_and_detect()`, and `heal_and_detect()` does real work beyond
   translation (gap-closing, role detection, clustering) regardless of
   whether the input started as a dict or a hand-built `Edge`.
4. ~~Tests: raw dicts → `Edge`.~~ **Retracted** — depended on 2-3.

**Naming, 11 Sep 2026**: the not-yet-built drawing interpreter (reads a
whole CAD file, uses forge to find clusters, decides per-cluster what to
do — including calling `unfold.interpret_section()` to check for sheet
metal) now has a name, "pippo" — it had none before, which was part of
why these conversations kept getting confusing. Lives outside this repo.
See `docs/ARCHITECTURE.md` for the flow and the forge → pippo → unfold
boundary.

**Update, same day — phase 0-1 retracted too.** Once phases 2-4 fell,
Federico asked the question that closes this decision: forge itself
already exposes its useful pieces publicly for exactly this reason
(`forge.__all__`: `load_geometry`, `heal_and_detect`,
`ForgeResult`/`ForgeCluster`/`ForgeContour` — confirmed working end to
end on both the flanged-profile and the two-circles case, verified with
real calls, not just reading the source). So phase 1's problem — reading
via `forge.core.topology.*` internals instead of forge's stable surface
— had a real, working fix available. But building *either* version of
that contract now means guessing what `pippo` (the actual future
consumer, not yet written) will need. That guess is exactly what phases
2-4 already got wrong once tonight. Decided: **`interpret_section()`
goes back to zero forge dependency**, keeping the two real improvements
from tonight (circle-pair detection, bare-arc routing to Cylinder/Cone)
ported onto the original hand-rolled walker — see `docs/ARCHITECTURE.md`
for the forge → pippo → unfold contract this revisits once `pippo`
exists. `unfold`'s "forge only in `io/dxf.py`" boundary (line 76-78) is
unchanged from before this decision ever opened. 167/167 tests green.

D43 leaves exactly one artifact behind: `docs/ARCHITECTURE.md`, and the
name "pippo" for the not-yet-built drawing interpreter this was all
in service of.

---

### D44 — `interpret_section` renamed to `read_section` (11 Sep 2026)

Federico's call: "interpret" was doing three different jobs under one
word — forge's own public `interpret_annotations`, this function, and
"pippo" colloquially being "l'interprete di disegno" — and that overlap
was actively confusing, on top of everything else tonight. Renamed
throughout: `unfold/rules/interpret.py` → `read_section.py`,
`interpret_section()` → `read_section()`, test file and every doc
mention updated to match (`TODO.md`, `docs/ARCHITECTURE.md`,
`SECTIONS.md`, `unfold/__init__.py`, `unfold/rules/__init__.py`). Picked
`read_section` over the other options on the table (`find_section`,
`get_section`) because it matches the return type already in place,
`SectionReading` — `read_section() -> SectionReading` reads as one
sentence. Earlier decisions above (D42/D43) keep the old name in their
own prose — they describe what was true when written, not corrected
after the fact; the code and every current doc use the new name.
Historical entries elsewhere in this file that still say
`interpret_section` are exactly that: history, not stale docs.

---

### D45 — Faceted `Cone`/`Cylinder` bends use the shop's `Calibration` too, not a separate material table (11 Sep 2026)

Federico's call: a facet joint on a faceted cone/cylinder is a real
press-brake bend, made on the same machine as every `BentProfile` bend
— an officina of any `tipo_cliente` (zero_config, cava_propria,
misurato, MAP.md D36/D39) should get consistent math whether it develops
a bent profile or a faceted cone/cylinder, one configuration for both.
Explicitly out of scope, his call: `tipo_cliente == somma_interna`
("inside_sum") doesn't need to work well here — those customers already
handle their own edge cases by experience.

**What changed**: `Cone`/`Cylinder` gained a `calibration: object =
"default"` field, same contract as `BentProfile`. `facet_bend_radius`/
`facet_k_factor` stay explicit overrides on top of it (same pattern as
`Bend.radius` in `BentProfile`) — new here: `facet_k_factor` alone now
reports `rule="esplicito"` on the resulting `BendResult`, honest about
not coming from the calibration ladder (`BentProfile` has no equivalent
since it never let K be overridden directly).

**The geometric mismatch, resolved without merging the two formulas**:
`BentProfile` computes a *deduction* to subtract from an apex-to-apex
flange; a facet joint *adds* a `bend_allowance` between two facet
chords — different geometry, can't share one formula. New shared helper
`core/bend.py::resolve_facet_bend()` pulls radius+K from the calibration
(`Calibration.deduction_detail()`, using only `.k`/`.radius`, never
`.value`) and separately calls `Bend.bend_allowance()` for the faceted
math. `DeductionInfo` gained a `radius` field (the resolved radius —
`None` for `"misurato"`, since a measured accorciamento is a direct
value with no radius behind it; `0.0` for `"inside_sum"`) so this
resolution didn't need to duplicate `deduction_detail()`'s own cava→radius
lookup.

**Second part of the ask**: `flat.bends` (a `BendResult` per bend,
already how `BentProfile` tells the operator how to set the machine —
angle, cava, rule, source) was empty for `Cone`/`Cylinder` before this.
Now populated for the faceted case too — one `BendResult` per facet
joint (`n_facets - 1`), all identical for a regular polygon, reporting
`bend_allowance` instead of `deduction`/`setback` (nothing is subtracted
here, see above).

**Real, visible consequence**: the *default* facet radius (no
`facet_bend_radius` given) changes. It used to be `= thickness` — an
undeclared, thickness-scaled guess, exactly what D36 already forbids for
`BentProfile` ("niente quantità inventate per scala"). It is now
whatever the calibration resolves to — for `"default"` (no cava known
for any thickness), that is the same fixed `DEFAULT_UNKNOWN_RADIUS_MM =
1.0` `BentProfile` already falls back to, not scaled by thickness
either. Existing callers relying on the old `= thickness` default get a
different number now; `facet_bend_radius=` still overrides explicitly
for anyone who wants the old value back on purpose. 6 new tests (default
radius from calibration, explicit override still wins, `bends`
populated, explicit K reports `"esplicito"` — both `Cone` and
`Cylinder`), **173/173 green**.

`MATERIAL_K_FACTORS`/`estimate_k_factor()` (`core/bend.py`) are no
longer used by any code path in `unfold` — `Cone`/`Cylinder` faceted now
go through the calibration ladder, which already ends at `k_din6935()`
(a different, DIN-based estimate), not `estimate_k_factor()`'s
material-bucket table. Both stay public (still in `unfold.__all__`,
still importable, still documented in `docs/API.md`) for anyone who
wants that specific rough-material estimate standalone — orphaned from
`unfold`'s own default path, not deleted. Left as is, not raised with
Federico yet — worth a explicit "keep or retire" call, not assumed.

---

### D46 — `Cone`/`Cylinder` developable in equal pieces (`split`), faceted included (11 Sep 2026)

Federico's call: especially when a cone/cylinder is made from bent
(faceted) sheet rather than rolled, it is often built as 2 (or more)
equal pieces welded together — too big for one press-brake run in one
piece. Those pieces need the same shortening parameter the full
development already has for its weld seam (`margin`) — not a new,
separate parameter.

**`Cylinder`** already had `sector_angle` (D42) for an arbitrary partial
development (e.g. a sella's 60°) — that alone already covers "split in
half" (`sector_angle=180`), just requires the caller to do the angle
math. Added `split: int = 1` as a convenience — `split=2` means
`sector_angle=360/split` — mutually exclusive with an explicit
`sector_angle` (both non-default raises, no silent precedence). The gap
`faceted=True` + partial `sector_angle` left explicitly open in D42
("not yet decided") is closed here: `n_facets` now means the count for
the FULL 360° prism; a partial piece takes `n_facets × angle/360` of
them, required to land on a whole facet (raises a clear error
otherwise, same "explicit over silently wrong" rule as everywhere else
tonight). Chord/bend-angle are properties of the full polygon, unchanged
by how much of it this piece covers — verified equal between a full
`Cylinder` and its `split=2` half in a new test.

**`Cone`** had no partial-development concept at all before this — its
"full" angle is fixed by geometry (`full_angle_deg`, now reported in
`meta`), not a free value like the cylinder's 360°. Added
`sector_angle: Optional[float] | None = None` (a cap on that natural
value, must be `<= full_angle_deg`) and the same `split` convenience
(`split=2` → `full_angle/2`), same mutual-exclusion rule. Faceted+partial
resolves proportionally against the smooth `full_angle` (the faceted
model's own natural span differs from it by the same small
approximation the existing convergence test already documents) — same
"must land on a whole facet" requirement.

Found and fixed one real bug while wiring this: `Cone`'s faceted
`outer_facet_width`/`inner_facet_width` were computed from `n` (this
piece's facet count) instead of `n_full` (the whole polygon's) — chord
width is a property of the full inscribed polygon, not of how many of
its facets a given piece happens to cover; using the reduced count would
have reported the wrong chord width for any non-full piece. Caught by
building the split feature itself, before it shipped with the bug — not
found by a pre-existing test.

`margin` needed zero new code for any of this — it already trims a
fixed amount off whatever span gets built (`width`/`vertex_angles`),
regardless of where that span came from. That was the actual ask
("stessi parametri di accorciamento che prendono ora gli sviluppi
completi") and it is satisfied by construction, not by adding anything.
11 new tests (6 `Cylinder`, 5 `Cone` — matching `sector_angle`, mutual
exclusion, faceted facet-count halving, margin still working, indivisible
split raising), **184/184 green**.

---

### D47 — bend angles in the DXF header (11 Sep 2026)

Federico's ask, after seeing `flat.bends` printed to the console in
tonight's scripts: it should be in the DXF header too — an operator
reading the drawing needs the bend angles, not just someone reading
Python output. `flat.bends` (`BendResult`, populated for `BentProfile`
and, since D45, for faceted `Cone`/`Cylinder` too) was computed but never
reached either header path (`to_dxf(annotate=True)`'s note block,
`export_part(include_header=True)`'s header level, D32) — both only ever
read `flat.meta`.

`_meta_lines()` now takes `bends` too and appends one line per bend
(angle, rule, cava) via a new `_bend_lines()` — collapsed to a single
`"N pieghe x angle gradi (rule)"` line when every bend is identical (the
regular-polygon case, most of the time for faceted `Cone`/`Cylinder`),
listed individually (`"piega 1: ...", "piega 2: ...`) when they differ
(the general `BentProfile` case). Verified on both: a 5-facet faceted arc
(4 identical bends → one line) and a `BentProfile` with two different
angles (two distinct lines) — read back from the actual generated DXF
text entities, not just printed. 184/184 unaffected (no test asserted on
the old header text).

---

### D48 — real trap found: `export_part()` on a facet-derived `Section` silently gives the wrong cut length

Federico noticed the sella section-view DXF from script 11 had no
development in it, and asked since when a "DXF without a development"
was a thing — it never was: `Section.to_dxf()` has always drawn the
folded section alone (same as `09_section_view.py`), the script had just
called it directly instead of stacking it with the real cut.

Checking how to stack them properly (development + section + header, the
`export_part()` picture) surfaced a real correctness trap, caught before
it shipped as advice: `export_part()`/`Section.to_bent_profile().develop()`
recomputes the development using `BentProfile`'s DEDUCTION formula
(subtract accorciamento from an apex-to-apex flange) — not the ADDITION
formula the faceted `Cone`/`Cylinder` math actually uses (`bend_allowance`
summed between exact facet chords, D45's whole reason for
`resolve_facet_bend()` bypassing `deduction_detail()`'s `.value`).
Verified numerically on the faceted sella: feeding the same chord/angle
data through `Section.to_bent_profile("default").develop()` gives
`total_length` off by ~2mm from the real one — not rounding, a different
formula for a different geometry, silently wrong if used.

Fix: don't rebuild the development at all for a faceted piece — combine
the ALREADY-CORRECT `flat` (from `Cylinder`/`Cone.develop()`) with the
`Section`'s folded view via `write_part_dxf()` directly (the layer
underneath `export_part()`, `unfold.io.dxf.write_part_dxf` — not
re-exported in `unfold.__all__`, imported explicitly where needed).
Script 11 rewritten to do this; both bonus files now correctly stack
the real cut + section + header (verified: `OuterContour`+`Bending` from
the real development, `SectionView`+`Quotes`+`Notes` layered on top,
read back from the generated DXF). 186/186 unaffected.

---

### D49 — `Bend.from_included()`: construct from the drawing's included angle (11 Sep 2026)

From an outside review Federico asked for my read on (`Parere_di_DeepSeek.md`,
gitignored — a personal note, not project documentation): `Bend.angle`
being the rotation-from-flat (not the included angle a technical drawing
quotes) is a real "silent bug" trap — correct only by numeric coincidence
at 90°, wrong everywhere else, and nothing stopped someone from passing
the drawing's angle straight into `angle`. Agreed with the suggestion,
implemented it.

`Bend.from_included(angle_included, radius=None, k_factor=None,
cava=None) -> Bend` — same object, built from `angle = 180 -
angle_included` instead of asking for that arithmetic by hand.
**Raises** `ValueError` if `angle_included` is not in `(0, 180)` (the
same valid range as `angle`, checked at the friendlier boundary instead
of letting a bad value surface later as a confusing `angle` error).
Documented in the module's own angle-convention warning (top of
`core/bend.py`), `docs/API.md`, `TUTORIAL.md` (tappa 2), and demonstrated
in `04_bend.py` with the exact failure mode made visible: the same 120°
included angle developed three ways — by hand (`Bend(angle=60)`),
`from_included(120)`, and the common mistake `Bend(angle=120)` — the
first two match, the third gives a measurably different, silently wrong,
development length. 6 new tests, **192/192 green**.

## Closed questions (history)

- *Outer, interior, or centerline quotes?* → core at centerline (D1);
  `inside_sum` works entirely in interior quotes (D35).
- *Does a carpentry customer give interior or centerline quotes?* →
  interior, raw sum (D35).
- *Is the fixed k-factor a bend rule of its own?* → no, din6935
  generalizes it (D3, content superseded by D33).
- *How is a bend's deduction chosen — radius or calibration?* → always
  the calibration ladder; "manual mode" no longer exists, an explicit
  radius is one rung of it (D33); `default` needs zero setup (D36).
- *Do test fixtures matter for the calculation?* → no, the triple signal
  is enough (D9/D10).
- *Does the radius enter a fixture's name or the calculation?* → no and
  no (D11 — unrelated to D36's fallback radius).
- *Is the internal reconstruction tool part of the public product?* →
  no, an internal fixture-generation tool (D12).
- *How is bend direction read from a flat DXF?* → from the `Bend`/
  `MBend` layer (D21).
- *Golden tolerance for officina_1?* → 0.01mm (D13); Phase 1 lands
  within ~0.005mm on all valid cases.
- *Layered refactor right away?* → no, after Phase 2 (D16).

---

## Appunti Federico (grezzi, da sciogliere in decisioni)

- **Nomi progetto (11 set 2026, idea grezza, non decisa)**: "pippo" come
  nome del progetto/repo dell'interprete di disegno (non solo un nome
  interno di comodo) — piace perché è simpatico, chi arriva non se
  l'aspetta, dà l'idea di parlare con un collega. Forse questo repo
  (`unfold`) diventa "bendly". Non deciso, non rinominato: resta qui
  finché non si torna sopra con la testa fresca.
- **`misurati` non ha il campo `materiale`, e sembra sbagliato (6 set 2026).**
  Un accorciamento misurato da un `.bnc` è specifico del materiale di quel
  job (viene dal database materiale di TruBend). Oggi `_measured_row` lo
  userebbe per qualunque materiale. Va aggiunto `materiale` alla riga e al
  match — ma solo quando si rimette mano al modello: per ora officina 1
  misura solo acciaio, quindi non morde.
- **Lo schema della calibrazione ha troppi campi (Federico, 6 set 2026):**
  `cava_per_spessore` + `k_per_materiale` + `misurati` (5 campi per riga) +
  `metodo`. Da rivedere se si può ridurre. Non ora.
- **Tabella cava → spessore VERA di officina 1** — `CAVE_officina_1.txt`
  c'è (D34), ma ha più V per lo stesso spessore: serve che Federico dica
  la "standard" per ognuno. Vedi `TODO.md`.
- **Reverse engineering delle pieghe da un DXF esistente** — fatto per il
  caso "DXF piatto TruBend + `.bnc`" (Fase 1). Resta aperto il caso "DXF
  già fatto da un cliente, senza `.bnc`": capire quale convenzione di
  sviluppo ha usato chi l'ha disegnato.
- **Info di piega nei DXF TruBend** (Fase 5): il verso di ogni piega è nel
  layer `Bend` / `MBend` (D21). Manca l'angolo quando non è 90° —
  indagare dove sta (xdata?) quando c'è un DXF reimportabile con angoli
  diversi da 90.
- **Allineamento viste**: va calcolato ESTERNAMENTE a forge; probabilmente
  non fa parte nemmeno di questo layer di unfolding, vive di vita propria.
- **`COME_FUNZIONA.md`** è una bozza scritta da Claude, riallineata a D36
  l'11 set 2026 — poi confluirà in `docs/ARCHITECTURE.md`.
