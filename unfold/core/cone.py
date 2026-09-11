"""
unfold/core/cone.py
--------------------
Sviluppo piano del tronco di cono (settore anulare). Stessa matematica di
`cono.py` (dxf-forge), riscritta come motore parametrico puro — zero
dipendenze, zero DXF: `develop()` ritorna dati, non un file.

Convenzione: i diametri sono ESTERNI. Lo sviluppo è calcolato sulla fibra
media (D_medio = D_esterno - thickness), come nello script originale.

Orientamento canonico: il settore è costruito simmetrico rispetto all'asse
X, con la bisettrice verso +X — nessuna trasformazione. orientation="vertical"
(default) lo ruota di 90° (bisettrice verso +Y). orientation="horizontal"
tiene la costruzione canonica.

Margine di saldatura (margin): quantità TOTALE, tolta in parti uguali dai due
bordi radiali del settore (metà per lato) — es. margin=2 accorcia lo
sviluppo di 1 mm per lato. È convertito in una riduzione d'angolo usando il
raggio esterno come riferimento (arco ≈ raggio × angolo in radianti): per un
raggio esterno molto più grande del margine — il caso normale — l'errore
introdotto da questa approssimazione è trascurabile.

Sviluppo sfaccettato (faceted=True): invece di un settore curvo da calandra,
approssima il cono con N facce PIANE trapezoidali unite da pieghe a
pressopiega — la stessa idea di un cono/tronco "a spicchi". I due raggi
sviluppati (r_outer/r_inner) restano IDENTICI a quelli della versione
liscia: si dimostra che il lato obliquo di ogni faccetta trapezoidale ha
sempre lunghezza pari alla generatrice, quindi r_outer - r_inner = slant
vale in entrambi i casi. Cambia solo il passo angolare fra i vertici, scelto
in modo che la corda dritta a ciascun raggio (non l'arco) coincida con il
lato reale del poligono inscritto nella circonferenza vera (non in quella
sviluppata) a quel diametro.

Raggio e K delle pieghe sfaccettate (MAP.md D45): dalla `calibration`
dell'officina, stessa scaletta di `BentProfile` (misurato -> K per
materiale -> stima DIN 6935) — un giunto sfaccettato è una piega vera,
fatta sulla stessa pressa. `facet_bend_radius`/`facet_k_factor` restano
override espliciti, come `Bend.radius`/`Bend.cava` in `BentProfile`.
`develop()` popola `flat.bends` (una `BendResult` per faccetta, tutte
identiche per un poligono regolare) — stessa cosa che fa `BentProfile`
per dire all'operatore come impostare la macchina.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from ..model.geometry import FlatGeometry, polar_point, swap_xy, _check_orientation
from .bend import resolve_calibration, resolve_facet_bend

_TOL = 1e-9

# Quanto le linee di piega del cono sfaccettato si fermano prima del vero
# raggio interno/esterno — vedi commento in _develop_faceted().
_BEND_LINE_INSET = 0.5


def _sector_entities(r_inner: float, r_outer: float, angle: float, role: str = None) -> list:
    """Settore anulare simmetrico rispetto a X, ampiezza angolare `angle` (gradi)."""
    a0, a1 = -angle / 2.0, angle / 2.0
    p_inner_1, p_outer_1 = polar_point(r_inner, a0), polar_point(r_outer, a0)
    p_inner_2, p_outer_2 = polar_point(r_inner, a1), polar_point(r_outer, a1)

    def _tag(d: dict) -> dict:
        if role is not None:
            d["role"] = role
        return d

    return [
        _tag({
            "type": "arc", "center": (0.0, 0.0), "radius": r_outer,
            "start_angle": a0, "end_angle": a1, "ccw": True,
        }),
        _tag({"type": "line", "start": p_outer_2, "end": p_inner_2}),
        _tag({
            "type": "arc", "center": (0.0, 0.0), "radius": r_inner,
            "start_angle": a1, "end_angle": a0, "ccw": False,
        }),
        _tag({"type": "line", "start": p_inner_1, "end": p_outer_1}),
    ]


def _faceted_sector_outline(r_inner: float, r_outer: float, vertex_angles: list, role: str) -> list:
    """
    Perimetro del settore sfaccettato fra i vertici dati: N corde esterne, un
    lato radiale, N corde interne (in verso opposto per richiudere il loop),
    l'altro lato radiale. Tutte con lo stesso `role` (bordo di taglio).
    """
    n = len(vertex_angles) - 1
    entities = []
    for i in range(n):
        entities.append({
            "type": "line",
            "start": polar_point(r_outer, vertex_angles[i]),
            "end": polar_point(r_outer, vertex_angles[i + 1]),
            "role": role,
        })
    entities.append({
        "type": "line",
        "start": polar_point(r_outer, vertex_angles[-1]),
        "end": polar_point(r_inner, vertex_angles[-1]),
        "role": role,
    })
    for i in range(n, 0, -1):
        entities.append({
            "type": "line",
            "start": polar_point(r_inner, vertex_angles[i]),
            "end": polar_point(r_inner, vertex_angles[i - 1]),
            "role": role,
        })
    entities.append({
        "type": "line",
        "start": polar_point(r_inner, vertex_angles[0]),
        "end": polar_point(r_outer, vertex_angles[0]),
        "role": role,
    })
    return entities


@dataclass
class Cone:
    top_diameter: float
    bottom_diameter: float
    height: float
    thickness: float = 0.0
    margin: float = 0.0
    orientation: str = "vertical"
    faceted: bool = False
    n_facets: int = 8
    facet_bend_radius: Optional[float] = None   # esplicito -> batte la calibrazione
    facet_k_factor: Optional[float] = None      # esplicito -> batte la calibrazione
    material: str = "acciaio"
    calibration: object = "default"             # Calibration | nome str, come BentProfile (MAP.md D45)
    label: str = "cone"

    def develop(self) -> FlatGeometry:
        """Calcola il settore anulare (liscio o sfaccettato) e ritorna un FlatGeometry."""
        for name, value in (
            ("top_diameter", self.top_diameter),
            ("bottom_diameter", self.bottom_diameter),
            ("height", self.height),
        ):
            if value <= 0:
                raise ValueError(f"{name} deve essere maggiore di zero.")
        if self.thickness < 0:
            raise ValueError("thickness non può essere negativo.")
        if self.margin < 0:
            raise ValueError("margin non può essere negativo.")
        _check_orientation(self.orientation)
        if self.faceted and self.n_facets < 3:
            raise ValueError("n_facets deve essere almeno 3.")

        top_mean = self.top_diameter - self.thickness
        bottom_mean = self.bottom_diameter - self.thickness

        if top_mean <= 0:
            raise ValueError("thickness deve essere minore di top_diameter.")
        if bottom_mean <= 0:
            raise ValueError("thickness deve essere minore di bottom_diameter.")
        if abs(top_mean - bottom_mean) < _TOL:
            raise ValueError(
                "top_diameter e bottom_diameter coincidono sulla fibra media: "
                "usa Cylinder, non Cone."
            )

        big_d = max(top_mean, bottom_mean)
        small_d = min(top_mean, bottom_mean)
        big_r, small_r = big_d / 2.0, small_d / 2.0
        delta_r = big_r - small_r

        # Generatrice reale del tronco di cono — è anche la lunghezza del
        # lato obliquo di ogni faccetta nella versione sfaccettata (vedi
        # dimostrazione nel docstring del modulo).
        slant = math.hypot(self.height, delta_r)

        # Raggi dello sviluppo piano — identici per liscio e sfaccettato.
        r_outer = slant * big_r / delta_r
        r_inner = slant * small_r / delta_r

        bends = []
        if self.faceted:
            entities, reference_entities, extra_meta, bends = self._develop_faceted(
                r_inner, r_outer, big_r, small_r,
            )
        else:
            entities, reference_entities, extra_meta = self._develop_smooth(r_inner, r_outer, big_r)

        if self.orientation == "vertical":
            entities = swap_xy(entities)
            reference_entities = swap_xy(reference_entities)

        meta = {
            "top_diameter": self.top_diameter,
            "bottom_diameter": self.bottom_diameter,
            "height": self.height,
            "thickness": self.thickness,
            "margin": self.margin,
            "top_diameter_mean": top_mean,
            "bottom_diameter_mean": bottom_mean,
            "slant_height": slant,
            "outer_radius": r_outer,
            "inner_radius": r_inner,
            **extra_meta,
        }

        return FlatGeometry(
            entities=entities, label=self.label, meta=meta,
            reference_entities=reference_entities, bends=bends,
        )

    # ------------------------------------------------------------------

    def _develop_smooth(self, r_inner: float, r_outer: float, big_r: float):
        full_angle = 360.0 * big_r / r_outer

        half_margin_angle = math.degrees(self.margin / 2.0 / r_outer) if self.margin > 0 else 0.0
        cut_angle = full_angle - 2.0 * half_margin_angle
        if cut_angle <= 0:
            raise ValueError("margin troppo grande rispetto allo sviluppo del cono.")

        entities = _sector_entities(r_inner, r_outer, cut_angle, role="outer")

        reference_entities = []
        if self.margin > 0:
            reference_entities = _sector_entities(r_inner, r_outer, full_angle)

        return entities, reference_entities, {"sector_angle_deg": cut_angle}

    def _develop_faceted(self, r_inner: float, r_outer: float, big_r: float, small_r: float):
        n = self.n_facets

        # Passo angolare tale che la corda dritta a r_outer coincida col
        # lato del poligono a N lati inscritto nella circonferenza VERA di
        # raggio big_r (non nella circonferenza sviluppata r_outer).
        angular_step_rad = 2.0 * math.asin(big_r * math.sin(math.pi / n) / r_outer)
        angular_step = math.degrees(angular_step_rad)
        full_span = n * angular_step

        if self.facet_bend_radius is not None and self.facet_bend_radius <= 0:
            raise ValueError("facet_bend_radius deve essere maggiore di zero.")
        calibration = resolve_calibration(self.calibration)
        bend_radius, k, bend_result = resolve_facet_bend(
            calibration, self.thickness, angular_step,
            self.facet_bend_radius, self.facet_k_factor, self.material,
        )
        bend_allowance = bend_result.bend_allowance
        # Tutte le N-1 faccette sono identiche (poligono regolare, stesso
        # angolo ovunque) - un solo BendResult calcolato, ripetuto.
        bends = [bend_result for _ in range(n - 1)]

        vertex_angles_full = [-full_span / 2.0 + i * angular_step for i in range(n + 1)]

        vertex_angles = list(vertex_angles_full)
        if self.margin > 0:
            half_margin_angle = math.degrees(self.margin / 2.0 / r_outer)
            vertex_angles[0] += half_margin_angle
            vertex_angles[-1] -= half_margin_angle
            if vertex_angles[0] >= vertex_angles[1] or vertex_angles[-1] <= vertex_angles[-2]:
                raise ValueError(
                    "margin troppo grande rispetto alla faccetta estrema del cono sfaccettato."
                )

        entities = _faceted_sector_outline(r_inner, r_outer, vertex_angles, role="outer")
        # Le linee di piega si fermano un filo prima del vero raggio interno/
        # esterno (_BEND_LINE_INSET): se toccassero esattamente lo stesso
        # nodo dei vertici del contorno, il grafo di forge le userebbe per
        # richiudere ogni singola faccetta come loop a sé — 1 parte diventa
        # N parti. Stesso principio per cui in BentProfile/Cylinder le linee
        # di piega non toccano mai gli angoli del rettangolo.
        for angle in vertex_angles[1:-1]:
            entities.append({
                "type": "line",
                "start": polar_point(r_inner + _BEND_LINE_INSET, angle),
                "end": polar_point(r_outer - _BEND_LINE_INSET, angle),
                "role": "bending",
            })

        reference_entities = []
        if self.margin > 0:
            reference_entities = _faceted_sector_outline(r_inner, r_outer, vertex_angles_full, role=None)
            for e in reference_entities:
                e.pop("role", None)

        extra_meta = {
            "n_facets": n,
            "facet_angle_deg": angular_step,
            "facet_bend_radius": bend_radius,
            "facet_k_factor": k,
            "facet_bend_allowance": bend_allowance,
            "outer_facet_width": 2.0 * big_r * math.sin(math.pi / n),
            "inner_facet_width": 2.0 * small_r * math.sin(math.pi / n),
        }
        return entities, reference_entities, extra_meta, bends
