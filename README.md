# bendly

> **Status: alpha.** Phases 1–3 are done (wrapped shapes, press-brake bent
> profiles, the human layer with external-to-external quotes and the dimensioned
> section view). Phases 4–5 (boxes / multi-axis bends, bend info inside TruBend
> DXFs) are parked. The API in `bendly.__all__` is stable; see `docs/API.md`
> and `docs/ARCHITECTURE.md`.
>
> **All rights reserved — no license is granted.** This repo is public so it
> can be read and evaluated; it is not open source. Want to use it? Ask —
> open an issue or reach out.

Pure math engine for flat patterns of sheet-metal parts: **wrapped shapes**
(cone, cylinder) and **press-brake bent profiles** (an L bracket, a U channel, a
Z, an omega…).

`.develop()` has **no dependencies**: it does trigonometry and returns a
`FlatGeometry` — plain Python data (a list of geometric entities in a neutral
schema + computed values). No DXF, no forge. Only `.to_dxf()` touches
[dxf-forge](../dxf-forge), and only if you call it.

```python
from bendly import Cone, Cylinder

flat = Cone(top_diameter=1600, bottom_diameter=1016, height=1000, thickness=5).develop()
flat.to_dxf("cone.dxf")

flat = Cylinder(diameter=1016, height=3895, thickness=5).develop()
flat.to_dxf("cylinder.dxf")
```

## Install

```
pip install -e .
```

`.develop()` works immediately, with nothing else. For `.to_dxf()` you also need
[dxf-forge](../dxf-forge) installed alongside (it is not on PyPI):

```
pip install -e ../dxf-forge
```

## The conventions that matter

- **The engine calculates at the centerline** (mid-thickness), never at outside
  or inside dimensions. This is the founding decision (`MAP.md` D1): a flange
  trapped between two bends of opposite direction — the web of a Z or an omega —
  has no coherent "outside" face, so the ambiguity is removed at the root rather
  than merely reduced. `BentProfile.flanges` and `Section.segments` are
  centerline lengths, from virtual apex to virtual apex.
- **Diameters for `Cone` / `Cylinder` are OUTSIDE.** The pattern is computed on
  the mean fibre (`D_mean = D_outside − thickness`), `MAP.md` D19.
- **The flat pattern is linear**: Σ segments − Σ deductions. The deduction per
  bend is a pure constant of (thickness, V-opening, angle) — no shape effect,
  proven on 20 real shop parts (`MAP.md` D2).
- If you work in **outside-to-outside** dimensions, like a metal worker reading a
  drawing, use the **human layer** (`develop_from_external_flanges`,
  `Section.from_external_flanges`): it translates to the centerline for you
  (`MAP.md` D28/D30), and the offset outside↔centerline does **not** depend on
  the bend radius.

## Examples

### A press-brake bent profile

A bent part is flanges + angles. The deduction per bend comes from **one
formula** (neutral-fibre method), which needs an inside radius `r` and a
k-factor `K`. Both are supplied by a **calibration** — a file with a
thickness→V-opening table (so `r ≈ V/6`), optionally a per-material `K`, and
optionally already-**measured** deductions (`MAP.md` D33). You set nothing to
start: with no `calibration` it uses `"default"`, which doesn't guess anyone's
die — `r` falls back to a fixed, declared 1mm radius and `K` is estimated by
DIN 6935 from `r/s` (`MAP.md` D36). `flat.bends[i].source` always says where
each number came from, never a guess dressed up as real data.

```python
from bendly import Bend, BentProfile

flat = BentProfile(
    flanges=[50, 80, 50],                       # centerline lengths
    bends=[Bend(angle=90), Bend(angle=90)],     # just the angle
    thickness=2, width=300,
    material="acciaio",                         # picks the row in the calibration's k_per_materiale
    calibration="tipo_misurato",                # or omit -> "default"; or "din6935", "esempio_din_3cave", "inside_sum"
).develop()

print(flat.meta["total_length"])
for b in flat.bends:                            # one BendResult per bend
    print(b.angle, b.deduction, b.source)       # how much, and where it came from

flat.to_dxf("bracket.dxf")                       # rectangle + one line per bend, role="bending"
```

`K`, best to worst: a **measured** deduction for that (thickness, V-opening,
angle) → the calibration's per-material `K` → the DIN 6935 estimate. The
V-opening comes from the calibration's table; pass `cava=` on a `Bend` only for a
bend formed with a non-standard die. `Bend(radius=...)` is for when you know the
inside radius and not the V-opening (bump forming, coining).

`Bend.angle` is the angle the sheet **rotates** from flat (flat = 0°), not the
included angle between the finished flanges. For a 90° square they coincide by
coincidence; otherwise pass `180 − included_angle`.

### The human layer — outside-to-outside quotes

```python
from bendly import Bend, develop_from_external_flanges

flat = develop_from_external_flanges(
    external_flanges=[100, 110],                 # read on the outside of the part
    bends=[Bend(angle=90)],
    thickness=3, width=300,
    calibration="tipo_misurato",
)
```

### The dimensioned section view

`Section` carries the bend **direction** (up/down, `angles` in the 90/270 naming
scheme). It gives you both the flat pattern and the drawing of the *bent* part.

```python
from bendly import Section

sec = Section.from_external_flanges(
    shape="Z", external_flanges=[80, 40, 80], angles=[90, 270], thickness=3,
)

for q in sec.flange_quotes():
    # display_kind is "esterno" or, for the ambiguous web of a Z, "mezzeria"
    print(q.display_length, q.display_kind)

flat = sec.to_bent_profile(width=300, calibration="din6935").develop()
```

### The layered export — one DXF, stacked vertically

```python
from bendly import Section, export_part

sec = Section.from_external_flanges(
    shape="L", external_flanges=[100, 110], angles=[90], thickness=3,
)
export_part(sec, width=300, path="part.dxf",
            calibration="din6935", include_section=True, include_header=True)
```

Cut (always) → dimensioned section view (optional) → header (optional), stacked
top to bottom, left-aligned (`MAP.md` D32).

## Which setup fits you

The generic formula is the product: it must work well without anyone's shop
data. A calibration file is an optional bonus, never a requirement. Check any
setup choice against these four cases (`MAP.md` D36/D39) — a calibration
self-declares which one it is via `tipo_cliente`, checked against its actual
content by `tipo_cliente_coerente()`:

| `tipo_cliente` | You are... | You give `bendly`... | Calibration |
|---|---|---|---|
| `zero_config` | a stranger who just downloaded this, no reading | nothing | `default` (or omit it) — fixed 1mm radius, DIN-estimated `K` |
| `cava_propria` | a shop with your own dies but no CAM | only a thickness→die table (5 minutes, never a measurement) | copy `calibrations/esempio_din_3cave.json`, fill in your real dies |
| `somma_interna` | a shop that only wants raw interior-quote sums, no K-factor talk | nothing, just that preference | `calibrations/inside_sum.json` |
| `misurato` | a shop with CAM, quoting as close to real as possible | dies + measured deductions (real hours of work, not free) | like `calibrations/tipo_misurato.json` — measured where you have it, estimated elsewhere |

## The neutral contract with forge

`FlatGeometry.entities` is in the same schema `forge.load_geometry()` accepts —
it is the neutral contract between the two projects. `bendly` never imports forge
for the calculation; forge is only needed by `to_dxf()`. If you do not want to go
through `to_dxf()`, consume `.entities` / `.meta` / `.bends` directly.

## Documentation

- **`TUTORIAL.md`** — a suggested order for going through the numbered
  exploration scripts to (re)learn the library, one question to answer at each
  stop.
- **`SCRIPTS.md`** — the index of the numbered scripts (`00_*` … `10_*`): script
  → API area → what it shows.
- **`MAP.md`** — the decision log: what was decided and, above all, why
  (`D1`, `D2`, …), in chronological order.
- **`COME_FUNZIONA.md`**, **`SECTIONS.md`** — domain documents (bend allowance,
  DIN 6935, K-factor; what a section is and why direction lives there).
- **`TODO.md`** — what is still missing, by priority.
- **`tests/`** — the executable specification: golden values from real shop parts
  (`data_4_cloude/`, not versioned), regenerated only by the dedicated
  `tests/generate_*.py` scripts.

## License

All rights reserved — see [`LICENSE`](LICENSE). Copyright (c) 2026
Federico Sidraschi. Source-available for reading; no license is
granted to use, copy, modify, or distribute it.
