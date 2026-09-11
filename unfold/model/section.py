"""
unfold/model/section.py
------------------------
A "section" is the SECTION drawing of a bent sheet-metal part, built from
parameters: shape, centerline segments, angles, thickness, radius.

What it is for:
  1. it is the recognition pattern for the drawing interpreter — "this
     view is bent sheet metal, not an outline to cut";
  2. it formalizes the golden test pieces instead of scattering numbers
     around the tests;
  3. it is the human-facing model that carries bend DIRECTION (up/down —
     `angles` follow the naming scheme, 90 vs 270). `BentProfile`, the
     engine underneath, is direction-blind on purpose (see MAP.md D1/D23):
     length and bend-line position never depend on up/down. `Section` is
     where direction lives; `to_bent_profile()` is the bridge that throws
     it away on the way into the engine.

A section contains ONLY the real profile (the solid outline at thickness):
no centerline is drawn. The centerline is recovered by offsetting the two
outer faces inward by half the thickness.

The section takes a SINGLE radius as input: `inner_radius`. For the test
sections it is a fixed 1 mm (SECTION_INNER_RADIUS_MM), the same for every
thickness — a symbolic minimum bend radius, used only by the pattern. The
centerline radius is not an input: it is derived (`inner_radius +
thickness / 2`) and varies with thickness.

The "is bent sheet metal" pattern is recognized from three signals:
  - the faces are everywhere parallel at a constant distance = thickness;
  - the rounded corners are concentric arc pairs whose radii differ by
    exactly the thickness;
  - that thickness is a sheet that actually exists (see
    sheet_thicknesses.json).

Conventions (consistent with unfold/core/bend.py and the naming scheme):
  - `segments`: CENTERLINE lengths, from virtual apex to virtual apex —
    the same numbers passed to BentProfile.flanges.
  - `angles`: interior angle as in the naming scheme (flat = 180, a bend
    "up" of 90 -> 90, a bend "down" -> 270). The signed rotation relative
    to going straight is: turn = 180 - angle.
  - the RADIUS is invented: it does NOT enter the flat-length calculation
    (the shop calibration decides that from the die). It only serves the
    pattern.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .geometry import FlatGeometry

# Inner radius of the test sections: a fixed 1 mm, the same for every
# thickness. A symbolic minimum bend radius; it does not touch the
# flat-length calculation.
SECTION_INNER_RADIUS_MM = 1.0

_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _fmt(x: float) -> str:
    return f"{x:g}"


def _turn_deg(angle_name: float) -> float:
    """Signed rotation relative to going straight (>0 = to the left)."""
    return 180.0 - angle_name


def _unit(angle_deg: float):
    r = math.radians(angle_deg)
    return math.cos(r), math.sin(r)


@dataclass
class FlangeFace:
    """Per una flangia: la faccia ESTERNA (convessa) se è coerente da un
    capo all'altro, altrimenti None — vedi `Section.flange_faces()`.
    `p0`/`p1` sono i due punti di tangenza (NON estesi all'apice virtuale)
    della faccia scelta, o della mezzeria se `face` è None.
    """
    index: int
    centerline_length: float
    face: Optional[str]          # "left" | "right" | None
    p0: Tuple[float, float]
    p1: Tuple[float, float]


@dataclass
class FlangeQuote:
    """La quota da disegnare per una flangia nella vista in sezione
    (Fase 3.3/3.4, MAP.md D1/D28/D31): esterna se la flangia ha una faccia
    esterna coerente, a mezzeria — dichiarato esplicitamente in
    `display_kind` — altrimenti. `p0`/`p1` sono già estesi fino
    all'apice virtuale (esterno o a mezzeria a seconda del caso), pronti
    da passare a una quota DXF.
    """
    index: int
    centerline_length: float
    display_length: float
    display_kind: str            # "esterno" | "mezzeria"
    face: Optional[str]          # "left" | "right" | None
    p0: Tuple[float, float]
    p1: Tuple[float, float]


@dataclass
class Section:
    shape: str                 # "L" | "U" | "Z" | "O" | ...
    segments: List[float]      # centerline lengths, apex to apex
    angles: List[float]        # interior, naming scheme; len == len(segments) - 1
    thickness: float
    inner_radius: float        # minimum bend radius; invented, pattern only

    def __post_init__(self):
        if len(self.angles) != len(self.segments) - 1:
            raise ValueError(
                f"need {len(self.segments) - 1} angles for "
                f"{len(self.segments)} segments, got {len(self.angles)}."
            )

    @classmethod
    def default(cls, shape, segments, angles, thickness) -> "Section":
        """Test section: a fixed 1 mm inner radius, for every thickness."""
        return cls(shape, segments, angles, thickness,
                   inner_radius=SECTION_INNER_RADIUS_MM)

    @classmethod
    def from_external_flanges(
        cls, shape: str, external_flanges: List[float], angles: List[float],
        thickness: float, inner_radius: float = SECTION_INNER_RADIUS_MM,
    ) -> "Section":
        """Costruisce una `Section` da quote ESTERNO-ESTERNO (come le dà
        un carpentiere) invece che a mezzeria — l'inverso di
        `to_bent_profile()` (Fase 3.3, MAP.md D31). `angles` restano nella
        naming scheme (90/270): servono per il verso, disegnato da
        `section()`, e per ricavare l'angolo di piega (`abs(180-a)`) che
        `external_flanges_to_centerline()` (D28) vuole.
        """
        from ..rules.deduction import external_flanges_to_centerline
        magnitudes = [abs(180.0 - a) for a in angles]
        segments = external_flanges_to_centerline(external_flanges, magnitudes, thickness)
        return cls(shape, segments, angles, thickness, inner_radius=inner_radius)

    @property
    def centerline_radius(self) -> float:
        """Derived, not an input: inner radius + half the thickness."""
        return self.inner_radius + self.thickness / 2.0

    # -- file name, shared naming scheme ----------------------------------

    def name(self) -> str:
        parts = [self.shape]
        for i, seg in enumerate(self.segments):
            letter = _LETTERS[i]
            parts.append(f"{letter}{_fmt(seg)}")
            if i < len(self.angles):
                parts.append(f"{letter}{_LETTERS[i + 1]}{_fmt(self.angles[i])}")
        parts.append(f"s{_fmt(self.thickness)}")
        return "".join(parts)

    # -- bridge to the engine ---------------------------------------------

    def to_bent_profile(self, width: float, calibration=None,
                        cava: Optional[float] = None):
        """Builds the `BentProfile` (direction-blind engine) that develops
        this section.

        Turns each interior `angle` (naming scheme) into a
        `Bend(angle=|180-angle|)`: BentProfile only sees the rotation from
        flat, never up/down (see MAP.md D23 — direction lives here, in
        `Section`, not in `Bend`). `calibration` (a `Calibration` object or
        a profile name) is passed straight through and is required — a
        `Section` carries no bend radius, so there is no manual mode here;
        `cava` is used for every bend if given.
        """
        from ..core.bend import Bend, BentProfile
        bends = [Bend(angle=abs(180.0 - a), cava=cava) for a in self.angles]
        return BentProfile(
            flanges=self.segments, bends=bends, thickness=self.thickness,
            width=width, calibration=calibration,
        )

    # -- geometry -------------------------------------------------------

    def _centerline_primitives(self):
        """Centerline path as a list of primitives:
        ("line", (x0, y0), (x1, y1), heading_deg)
        ("arc", (cx, cy), radius, a0_deg, a1_deg, ccw)
        """
        n = len(self.segments)
        r_cl = self.centerline_radius
        setback = [
            r_cl * math.tan(math.radians(abs(_turn_deg(a))) / 2.0)
            for a in self.angles
        ]

        prims = []
        pos = (0.0, 0.0)
        heading = 0.0
        for j in range(n):
            sb_before = setback[j - 1] if j >= 1 else 0.0
            sb_after = setback[j] if j <= n - 2 else 0.0
            straight = self.segments[j] - sb_before - sb_after
            if straight <= 1e-6:
                raise ValueError(
                    f"segment {j} ({self.segments[j]:g}) too short for the "
                    f"centerline radius {r_cl:g}: no straight part left."
                )
            ux, uy = _unit(heading)
            p1 = (pos[0] + ux * straight, pos[1] + uy * straight)
            prims.append(("line", pos, p1, heading))
            pos = p1

            if j <= n - 2:
                turn = _turn_deg(self.angles[j])
                ccw = turn > 0
                normal = heading + (90.0 if ccw else -90.0)
                nx, ny = _unit(normal)
                center = (pos[0] + nx * r_cl, pos[1] + ny * r_cl)
                a0 = math.degrees(
                    math.atan2(pos[1] - center[1], pos[0] - center[0])
                )
                a1 = a0 + turn
                prims.append(("arc", center, r_cl, a0, a1, ccw))
                ar = math.radians(a1)
                pos = (
                    center[0] + r_cl * math.cos(ar),
                    center[1] + r_cl * math.sin(ar),
                )
                heading += turn
        return prims

    def _offset_chains(self):
        """Le due catene offset a ±spessore/2 dalla mezzeria (traslazione
        esatta per i tratti dritti, stesso centro/angoli a raggio diverso
        per gli archi — un offset a distanza costante di un percorso
        tangente-continuo lo è altrettanto). Ogni voce corrisponde 1:1 al
        primitivo di `_centerline_primitives()` alla stessa posizione, così
        `right[k]`/`left[k]` sono l'offset di `prims[k]`.

        A ogni piega, la faccia ESTERNA (convessa) sta sulla catena
        "left" se la piega gira in senso antiorario (ccw), "right" se in
        senso orario — vedi `flange_faces()`.
        """
        prims = self._centerline_primitives()
        h = self.thickness / 2.0

        left, right = [], []
        for p in prims:
            if p[0] == "line":
                _, q0, q1, hd = p
                nx, ny = _unit(hd + 90.0)
                left.append(
                    ("line", (q0[0] + nx * h, q0[1] + ny * h),
                     (q1[0] + nx * h, q1[1] + ny * h))
                )
                right.append(
                    ("line", (q0[0] - nx * h, q0[1] - ny * h),
                     (q1[0] - nx * h, q1[1] - ny * h))
                )
            else:
                _, c, r, a0, a1, ccw = p
                r_left = (r - h) if ccw else (r + h)
                r_right = (r + h) if ccw else (r - h)
                left.append(("arc", c, r_left, a0, a1, ccw))
                right.append(("arc", c, r_right, a0, a1, ccw))
        return right, left, prims

    def flange_faces(self) -> List[FlangeFace]:
        """Per ogni flangia, la faccia esterna se è coerente da un capo
        all'altro (MAP.md D1): capita solo quando le due pieghe adiacenti
        girano nello stesso verso (stesso `ccw`) — vero per L/U, falso per
        l'anima di una Z o le anime di un'omega, dove le due pieghe
        adiacenti vedono come "esterna" due facce opposte. `p0`/`p1` sono
        i punti di tangenza sulla faccia scelta (o sulla mezzeria se
        `face` è None) — non ancora estesi all'apice virtuale, vedi
        `flange_quotes()` per quello.
        """
        right, left, prims = self._offset_chains()
        n = len(self.segments)

        def outer_chain(bend_k: int) -> str:
            _, _, _, _, _, ccw = prims[2 * bend_k + 1]
            return "left" if ccw else "right"

        faces: List[FlangeFace] = []
        for j in range(n):
            before = j - 1 if j >= 1 else None
            after = j if j <= n - 2 else None
            if before is None and after is None:
                face = "right"      # unica flangia, nessuna piega: la scelta non conta
            elif before is None:
                face = outer_chain(after)
            elif after is None:
                face = outer_chain(before)
            else:
                fb, fa = outer_chain(before), outer_chain(after)
                face = fb if fb == fa else None

            chain = right if face == "right" else left if face == "left" else None
            if chain is not None:
                p0, p1 = chain[2 * j][1], chain[2 * j][2]
            else:
                cl_line = prims[2 * j]
                p0, p1 = cl_line[1], cl_line[2]

            faces.append(FlangeFace(
                index=j, centerline_length=self.segments[j],
                face=face, p0=p0, p1=p1,
            ))
        return faces

    def flange_quotes(self) -> List[FlangeQuote]:
        """La quota da mostrare per ogni flangia nella vista in sezione
        (Fase 3.3/3.4, MAP.md D31): esterna se `flange_faces()` trova una
        faccia coerente, a mezzeria — con `display_kind` che lo dice
        esplicitamente — altrimenti. `p0`/`p1` sono estesi dal punto di
        tangenza fino all'apice virtuale (esterno o a mezzeria a seconda
        del caso: la stessa matematica di `external_to_centerline_flange`,
        D28, applicata punto per punto invece che alla lunghezza totale —
        `hypot(p1-p0)` torna infatti identico a `display_length`, verificato
        in `tests/test_section.py`).
        """
        from ..rules.deduction import centerline_to_external_flange
        magnitudes = [abs(180.0 - a) for a in self.angles]
        r_cl = self.centerline_radius
        css = [r_cl * math.tan(math.radians(m) / 2.0) for m in magnitudes]
        h = self.thickness / 2.0

        quotes: List[FlangeQuote] = []
        for ff in self.flange_faces():
            j = ff.index
            angle_before = magnitudes[j - 1] if j >= 1 else None
            angle_after = magnitudes[j] if j <= len(magnitudes) - 1 else None

            dx, dy = ff.p1[0] - ff.p0[0], ff.p1[1] - ff.p0[1]
            length = math.hypot(dx, dy)
            ux, uy = (dx / length, dy / length) if length > 1e-9 else (1.0, 0.0)

            if ff.face is not None:
                display_length = centerline_to_external_flange(
                    ff.centerline_length, self.thickness, angle_before, angle_after)
                kind = "esterno"
                extra_before = (css[j - 1] + h * math.tan(math.radians(angle_before) / 2.0)
                                if angle_before is not None else 0.0)
                extra_after = (css[j] + h * math.tan(math.radians(angle_after) / 2.0)
                               if angle_after is not None else 0.0)
            else:
                display_length = ff.centerline_length
                kind = "mezzeria"
                extra_before = css[j - 1] if angle_before is not None else 0.0
                extra_after = css[j] if angle_after is not None else 0.0

            p0 = (ff.p0[0] - ux * extra_before, ff.p0[1] - uy * extra_before)
            p1 = (ff.p1[0] + ux * extra_after, ff.p1[1] + uy * extra_after)

            quotes.append(FlangeQuote(
                index=j, centerline_length=ff.centerline_length,
                display_length=display_length, display_kind=kind,
                face=ff.face, p0=p0, p1=p1,
            ))
        return quotes

    def to_dxf(self, path: str, tolerance: float = 0.05, quote_clearance: float = 8.0) -> None:
        """Vista in sezione del pezzo PIEGATO (non sviluppato), con le
        quote di riferimento marcate — quota esterna dove la flangia ha una
        faccia esterna coerente, a mezzeria con nota esplicita altrimenti
        (Fase 3.3/3.4, MAP.md D31). Esce in DXF via forge/ezdxf.
        """
        from ..io.dxf import write_section_dxf
        return write_section_dxf(self, self.flange_quotes(), path,
                                 tolerance=tolerance, quote_clearance=quote_clearance)

    def section(self) -> FlatGeometry:
        """Solid section outline, as one closed loop (no centerline)."""
        right, left, prims = self._offset_chains()

        entities = [_edge_to_entity(e) for e in right]
        entities.append(_cap(_edge_end(right[-1]), _edge_end(left[-1])))
        entities += [_edge_to_entity(e) for e in left]
        entities.append(_cap(_edge_start(left[0]), _edge_start(right[0])))

        meta = {
            "shape": self.shape,
            "centerline_segments": list(self.segments),
            "angles": list(self.angles),
            "thickness": self.thickness,
            "inner_radius": self.inner_radius,
            "centerline_radius": round(self.centerline_radius, 6),
            "note": "inner radius = minimum bend radius; not used in the flat-length calculation",
        }
        return FlatGeometry(entities=entities, label=self.name(), meta=meta)


# --------------------------------------------------------------------------

def _edge_start(edge):
    if edge[0] == "line":
        return edge[1]
    _, c, r, a0, _a1, _ccw = edge
    ar = math.radians(a0)
    return (c[0] + r * math.cos(ar), c[1] + r * math.sin(ar))


def _edge_end(edge):
    if edge[0] == "line":
        return edge[2]
    _, c, r, _a0, a1, _ccw = edge
    ar = math.radians(a1)
    return (c[0] + r * math.cos(ar), c[1] + r * math.sin(ar))


def _cap(a, b):
    return {"type": "line", "start": a, "end": b, "role": "outer"}


def _edge_to_entity(edge):
    if edge[0] == "line":
        return {"type": "line", "start": edge[1], "end": edge[2], "role": "outer"}
    _, c, r, a0, a1, ccw = edge
    return {
        "type": "arc", "center": c, "radius": r,
        "start_angle": a0 % 360.0, "end_angle": a1 % 360.0,
        "ccw": ccw, "role": "outer",
    }
