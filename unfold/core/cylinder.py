"""
unfold/core/cylinder.py
------------------------
Sviluppo piano del cilindro (rettangolo). Stessa matematica di `cono.py`
(dxf-forge), riscritta come motore parametrico puro.

Convenzione: il diametro è ESTERNO. Lo sviluppo è calcolato sulla fibra
media (D_medio = D_esterno - thickness), come nello script originale.

Orientamento canonico interno: X = circonferenza (o sviluppo sfaccettato),
Y = lunghezza assiale del cilindro. orientation="vertical" (default) tiene
questa costruzione così com'è. orientation="horizontal" ruota il tutto di
90° (X e Y scambiati) — utile quando è la lunghezza assiale, non la
circonferenza, il lato lungo del foglio (es. un tubo lungo con diametro
piccolo).

Margine di saldatura (margin): quantità TOTALE, tolta in parti uguali dai due
bordi lungo lo sviluppo/circonferenza (destra e sinistra, non sopra/sotto
lungo l'altezza) — es. margin=2 accorcia il pezzo di 1 mm per lato. È il
margine per la cucitura longitudinale del rotolo (i due bordi del foglio
piano che si affacciano quando lo arrotoli a formare il cilindro), non per
la saldatura di testa fra due tronchi di cilindro consecutivi — stessa
convenzione di `cone.py`, dove margin riduce l'angolo del settore invece
della generatrice. Con faceted=True taglia nelle due faccette estreme
(prima e ultima), le altre restano intatte.

Sviluppo sfaccettato (faceted=True): invece del rettangolo per la calandra,
approssima il cilindro con un prisma a N facce piane (poligono regolare
inscritto nel diametro medio) unite da pieghe a pressopiega. La lunghezza
di ogni faccetta è la corda del poligono; l'angolo di ogni piega è
l'angolo esterno del poligono regolare, 360/N.

Settore parziale (sector_angle, default 360 = giro intero): un cilindro non
è sempre un tubo chiuso — una lamiera calandrata su un raggio ma tagliata
prima di richiudere il giro (es. una "sella", MAP.md D42) è lo stesso
identico sviluppo, solo con un angolo minore di 360. Lo sviluppo liscio
diventa `width = raggio_medio × sector_angle (radianti)`, che con
sector_angle=360 torna esattamente `π × diametro_medio` (giro intero) —
stessa formula del settore anulare di `Cone`, qui applicata al raggio
singolo del cilindro.

`split` (MAP.md D46): scorciatoia per il caso "il tubo è troppo
grande/lungo per farlo da un pezzo solo, lo facciamo in N pezzi uguali
saldati insieme" — `split=2` sviluppa 1/2 del giro (`sector_angle=180`
equivalente, ma senza dover calcolare l'angolo a mano). Alternativo a
`sector_angle` esplicito, non combinabile (uno dei due, mai entrambi
diversi dal default). `margin` continua a valere com'è, tolto ai due
bordi di QUESTO pezzo — è la giunzione a saldatura fra i pezzi, non
cambia parametro passando da un pezzo intero a un pezzo diviso.

Sfaccettato + settore parziale (MAP.md D46): supportato quando
`sector_angle`/`split` tagliano esattamente su un confine di faccetta —
`n_facets` resta il conteggio del prisma INTERO (360°), la porzione
sviluppata ne prende una frazione proporzionale (`n_facets × angolo/360`,
deve tornare un intero: es. `n_facets=8, split=2` -> 4 faccette in
questo pezzo). Un taglio che cade a metà di una faccetta solleva errore
esplicito invece di un risultato silenziosamente sbagliato.

Raggio e K delle pieghe sfaccettate (MAP.md D45): dalla `calibration`
dell'officina, stessa scaletta di `BentProfile` (misurato -> K per
materiale -> stima DIN 6935) — un giunto sfaccettato è una piega vera,
fatta sulla stessa pressa. `facet_bend_radius`/`facet_k_factor` restano
override espliciti, come `Bend.radius`/`Bend.cava` in `BentProfile`.
`develop()` popola `flat.bends` (una `BendResult` per faccetta, tutte
identiche per un poligono regolare).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from ..model.geometry import FlatGeometry, swap_xy, _check_orientation
from .bend import resolve_calibration, resolve_facet_bend


@dataclass
class Cylinder:
    diameter: float
    height: float
    thickness: float = 0.0
    margin: float = 0.0
    sector_angle: float = 360.0
    split: int = 1                              # scorciatoia per sector_angle=360/split (MAP.md D46)
    orientation: str = "vertical"
    faceted: bool = False
    n_facets: int = 8
    facet_bend_radius: Optional[float] = None   # esplicito -> batte la calibrazione
    facet_k_factor: Optional[float] = None      # esplicito -> batte la calibrazione
    material: str = "acciaio"
    calibration: object = "default"             # Calibration | nome str, come BentProfile (MAP.md D45)
    label: str = "cylinder"

    def develop(self) -> FlatGeometry:
        """Calcola il rettangolo di sviluppo (liscio o sfaccettato) e ritorna un FlatGeometry."""
        for name, value in (("diameter", self.diameter), ("height", self.height)):
            if value <= 0:
                raise ValueError(f"{name} deve essere maggiore di zero.")
        if self.thickness < 0:
            raise ValueError("thickness non può essere negativo.")
        if self.margin < 0:
            raise ValueError("margin non può essere negativo.")
        if not (0.0 < self.sector_angle <= 360.0):
            raise ValueError("sector_angle deve essere maggiore di zero e al massimo 360.")
        if self.split < 1:
            raise ValueError("split deve essere almeno 1.")
        if self.split != 1 and self.sector_angle != 360.0:
            raise ValueError(
                "sector_angle e split sono due modi di dire la stessa cosa — "
                "usane solo uno (sector_angle esplicito, o split per una "
                "frazione uguale del giro)."
            )
        _check_orientation(self.orientation)
        if self.faceted and self.n_facets < 3:
            raise ValueError("n_facets deve essere almeno 3.")

        effective_angle = self.sector_angle if self.split == 1 else 360.0 / self.split

        diameter_mean = self.diameter - self.thickness
        if diameter_mean <= 0:
            raise ValueError("thickness deve essere minore di diameter.")

        bends = []
        if self.faceted:
            width, bend_lines, extra_meta, bends = self._faceted_width_and_bends(
                diameter_mean / 2.0, effective_angle,
            )
        else:
            width = math.radians(effective_angle) * (diameter_mean / 2.0)
            bend_lines, extra_meta = [], {}

        half_margin = self.margin / 2.0
        cut_width = width - self.margin
        if cut_width <= 0:
            raise ValueError("margin troppo grande rispetto allo sviluppo del cilindro.")
        if bend_lines and (half_margin >= bend_lines[0] or half_margin >= width - bend_lines[-1]):
            raise ValueError(
                "margin troppo grande rispetto alla faccetta estrema del cilindro sfaccettato."
            )
        x0 = half_margin

        # Canonico: X = circonferenza/sviluppo sfaccettato (accorciata a
        # destra e sinistra dal margine), Y = lunghezza assiale (invariata).
        entities = [{
            "type": "polyline",
            "points": [
                (x0, 0.0), (x0 + cut_width, 0.0),
                (x0 + cut_width, self.height), (x0, self.height),
            ],
            "closed": True,
            "role": "outer",
        }]
        for pos in bend_lines:
            entities.append({
                "type": "line", "start": (pos, 0.0), "end": (pos, self.height), "role": "bending",
            })

        reference_entities = []
        if self.margin > 0:
            reference_entities = [{
                "type": "polyline",
                "points": [
                    (0.0, 0.0), (width, 0.0),
                    (width, self.height), (0.0, self.height),
                ],
                "closed": True,
            }]

        if self.orientation == "horizontal":
            entities = swap_xy(entities)
            reference_entities = swap_xy(reference_entities)

        meta = {
            "diameter": self.diameter,
            "height": self.height,
            "thickness": self.thickness,
            "margin": self.margin,
            "sector_angle_deg": effective_angle,
            "split": self.split,
            "diameter_mean": diameter_mean,
            "width": width,
            "width_cut": cut_width,
            **extra_meta,
        }

        return FlatGeometry(
            entities=entities, label=self.label, meta=meta,
            reference_entities=reference_entities, bends=bends,
        )

    # ------------------------------------------------------------------

    def _faceted_width_and_bends(self, r_mean: float, effective_angle: float):
        n_full = self.n_facets
        exterior_angle = 360.0 / n_full
        chord = 2.0 * r_mean * math.sin(math.pi / n_full)

        # Quante faccette di QUESTO pezzo (MAP.md D46) — n_full resta il
        # conteggio del prisma INTERO (360°), qui se ne prende una
        # frazione proporzionale. Corda/angolo di piega non cambiano: sono
        # proprietà del poligono intero, identiche per ogni faccetta.
        if effective_angle == 360.0:
            n = n_full
        else:
            raw_n = n_full * effective_angle / 360.0
            n = round(raw_n)
            if n < 1 or abs(raw_n - n) > 1e-6:
                raise ValueError(
                    f"sector_angle/split (effettivo {effective_angle:g}°) non taglia "
                    f"n_facets={n_full} su un confine di faccetta esatto "
                    f"({raw_n:g} faccette) — scegli una combinazione che torni intera."
                )

        if self.facet_bend_radius is not None and self.facet_bend_radius <= 0:
            raise ValueError("facet_bend_radius deve essere maggiore di zero.")
        calibration = resolve_calibration(self.calibration)
        bend_radius, k, bend_result = resolve_facet_bend(
            calibration, self.thickness, exterior_angle,
            self.facet_bend_radius, self.facet_k_factor, self.material,
        )
        bend_allowance = bend_result.bend_allowance
        # Tutte le N-1 faccette sono identiche (poligono regolare) - un
        # solo BendResult calcolato, ripetuto.
        bends = [bend_result for _ in range(max(n - 1, 0))]

        cum = 0.0
        bend_positions = []
        for i in range(n):
            cum += chord
            if i < n - 1:
                bend_positions.append(cum + bend_allowance / 2.0)
                cum += bend_allowance

        extra_meta = {
            "n_facets": n,
            "n_facets_full": n_full,
            "facet_width": chord,
            "facet_bend_radius": bend_radius,
            "facet_k_factor": k,
            "facet_bend_allowance": bend_allowance,
        }
        return cum, bend_positions, extra_meta, bends
