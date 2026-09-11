"""
unfold/core/bend.py
--------------------
Sviluppo piano di un profilo piegato (lamiera con una o più pieghe a
pressopiega) — flange rettilinee unite da pieghe, secondo le formule
standard di bend allowance / bend deduction.

Tre quantità utili per ogni piega (angolo, raggio interno R, spessore T):

    Bend Allowance (BA) — lunghezza dell'asse neutro nella piega:
        BA = (angle in radianti) * (R + K*T)

    Setback — distanza dal punto virtuale d'incontro delle facce (ESTERNE,
    INTERNE o di MEZZERIA, a seconda di dove si misura) al punto di tangenza
    del raggio. Stessa formula, cambia solo l'offset dal raggio interno:
        Outside     OSS = (R + T)     * tan(angle/2)
        Inside      ISS =  R          * tan(angle/2)
        Centerline  CSS = (R + T/2)   * tan(angle/2)

    Deduction — quanto sottrarre alla somma delle quote (nella STESSA
    convenzione del setback usato) per ottenere lo sviluppo piatto:
        Deduction = 2*Setback - BA
        L_totale  = somma(quote flange) - somma(Deduction di ogni piega)

CONVENZIONE ADOTTATA — quote a MEZZERIA (centerline), non esterne: `Bend
Profile.flanges` sono lunghezze misurate da mezzeria a mezzeria (CSS/CD, non
OSS/BD). Decisione permanente, non provvisoria: a differenza delle quote
esterne o interne, la mezzeria non ha "lati" — non può mai essere esterna a
una piega e interna a quella successiva. Su un profilo con pieghe in versi
alternati (Z, Omega) la quota esterna di una flangia centrale è
genuinamente ambigua (nessuna faccia è coerentemente esterna ad entrambe le
pieghe adiacenti — vedi MAP.md D1); a mezzeria l'ambiguità sparisce del
tutto, verificato numericamente su U/Z/Omega (zero errore in tutti e tre i
casi). È anche la convenzione più comoda per modellare i pezzi di test in
CAD: uno sketch primitivo (segmenti + angoli, NESSUN raggio disegnato — il
raggio dipende da matrice/punzone, è una scelta di produzione) più una
feature di lamiera dalla mezzeria, così lo stesso sketch si riusa a
spessori diversi senza rimodellare nulla. Resta il riferimento anche
quando in futuro si sapranno leggere le pieghe da un disegno in
prospettiva — non si ridiscute ad ogni nuova fonte di dati.

`BentProfile.develop()` non usa più queste formule direttamente:
l'accorciamento di ogni piega lo dà la `calibration` (obbligatoria), dalla
cava — vedi `unfold/rules/deduction.py` e `MAP.md` D33. I metodi
`Bend.centerline_setback()` / `outside_setback()` / `inside_setback()` /
`bend_allowance()` restano come utility pure e sono usati direttamente
dalle linee di piega di una `Cone` / `Cylinder` sfaccettata (lì non c'è
una cava, il raggio della faccetta è un dato).

ATTENZIONE alla convenzione di `Bend.angle`: è l'angolo di cui la lamiera
RUOTA rispetto a piatta (piatta = 0°), NON l'angolo incluso fra le due
flange finite. Per una squadra a 90° coincidono per coincidenza numerica
(180-90=90), ma per qualsiasi altro angolo no — una piega che lascia le
flange a un angolo incluso di 120° ha angle=60 (180-120), non 120. Se sul
disegno hai l'angolo incluso, passa (180 - angolo_incluso).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from ..model.geometry import FlatGeometry, swap_xy, _check_orientation

# Fattori K indicativi per materiale, rapporto raggio/spessore "standard"
# (R ≈ T) — dalla tabella di riferimento in COME_FUNZIONA.md. Usati SOLO
# dalle linee di piega di Cone/Cylinder sfaccettate (NON da BentProfile,
# che passa dalla calibrazione). Punto di partenza, non un valore misurato.
MATERIAL_K_FACTORS = {
    "mild_steel": 0.44,        # acciaio dolce / ferro, 0.43-0.45
    "stainless_steel": 0.39,   # inox, 0.38-0.40
    "aluminum": 0.41,          # alluminio, 0.40-0.42
}

_K_TIGHT_RADIUS = 0.31   # R/T < 1 — raggio molto stretto, 0.30-0.33 (COME_FUNZIONA.md)
_K_WIDE_RADIUS = 0.50    # R/T > 3 — raggio ampio, asse neutro al centro (COME_FUNZIONA.md)


def estimate_k_factor(material: str, radius: float, thickness: float) -> float:
    """
    Stima un K-factor di partenza da materiale + rapporto R/T, secondo la
    tabella qualitativa di COME_FUNZIONA.md. Le soglie numeriche per "molto
    stretto"/"ampio" (qui: R/T < 1 e R/T > 3) sono un'interpretazione
    ragionevole della tabella, non un valore da manuale — per un lavoro
    reale verifica/misura il K-factor della tua macchina e passalo
    esplicitamente a Bend(k_factor=...) invece di affidarti alla stima.
    """
    if thickness <= 0:
        raise ValueError("thickness deve essere maggiore di zero.")
    ratio = radius / thickness
    if ratio < 1.0:
        return _K_TIGHT_RADIUS
    if ratio > 3.0:
        return _K_WIDE_RADIUS
    return MATERIAL_K_FACTORS.get(material, MATERIAL_K_FACTORS["mild_steel"])


@dataclass
class Bend:
    """Una singola piega fra due flange consecutive.

    In un `BentProfile` serve solo `angle` (+ eventualmente `cava` per
    questa piega, se diversa da quella di tabella della calibrazione).
    L'accorciamento lo decide la `calibration` del profilo, dalla cava —
    vedi unfold/rules/deduction.py (MAP.md D33).

    `radius` / `k_factor`:
      - in un `BentProfile`: `radius` serve solo se conosci il raggio
        interno e non la cava (bombato, coniatura, stampo a raggio) — è
        un'eccezione, di norma il raggio lo dà la cava. `k_factor` è
        ignorato qui (il K lo decide la calibrazione).
      - sono invece la via normale per le linee di piega di una `Cone` /
        `Cylinder` sfaccettata, che chiamano i metodi di questa classe
        direttamente (lì non c'è una cava).
    """
    angle: float                      # gradi — vedi nota di convenzione in cima al file
    radius: Optional[float] = None    # raggio interno (R) — eccezione in BentProfile; via normale per Cone/Cylinder faceted
    k_factor: Optional[float] = None  # solo per Cone/Cylinder faceted (None -> stimato da material/radius/thickness)
    cava: Optional[float] = None      # apertura V matrice per questa piega — override della tabella di calibrazione

    def bend_allowance(self, thickness: float, k_factor: float) -> float:
        return math.radians(self.angle) * (self.radius + k_factor * thickness)

    def centerline_setback(self, thickness: float) -> float:
        """CSS — usato internamente da BentProfile (quote a mezzeria)."""
        return (self.radius + thickness / 2.0) * math.tan(math.radians(self.angle) / 2.0)

    def outside_setback(self, thickness: float) -> float:
        """OSS — utility indipendente, per confronti a quota esterna (non usata da BentProfile)."""
        return (self.radius + thickness) * math.tan(math.radians(self.angle) / 2.0)

    def inside_setback(self, thickness: float) -> float:
        """ISS — utility indipendente, per confronti a quota interna (non usata da BentProfile)."""
        return self.radius * math.tan(math.radians(self.angle) / 2.0)


@dataclass
class BendResult:
    """Esito del calcolo di UNA piega dentro `BentProfile.develop()` (o di
    una faccetta di `Cone`/`Cylinder` sfaccettati, MAP.md D45).

    Una per piega, interrogabile (skill 'interrogabilità per comprensione'):
    invece di spargere i numeri in liste parallele dentro `meta`, ogni piega
    porta il suo risultato e dice da dove viene.
    """
    angle:          float                   # gradi di rotazione da piatto
    cava:           Optional[float]          # apertura V usata (data o da tabella)
    deduction:      float                    # accorciamento a mezzeria tolto per questa piega (BentProfile) — 0 per Cone/Cylinder, lì niente si sottrae
    setback:        float                    # quanto ogni flangia adiacente perde: deduction/2 (BentProfile) — 0 per Cone/Cylinder
    rule:           str                      # "misurato" | "k_materiale" | "din6935" | "inside_sum" | "esplicito" (facet_k_factor dato a mano)
    source:         str                      # provenienza del numero, in chiaro
    fallback:       bool            = False  # True se c'erano misurati per lo spessore ma non per questa combinazione
    k_factor:       Optional[float]  = None  # il fattore K usato (None per "misurato" / "inside_sum")
    bend_allowance: float           = 0.0    # BentProfile: sempre 0 (linea di piega unica all'apice). Cone/Cylinder sfaccettati: il materiale AGGIUNTO da questa faccetta

    def to_dict(self) -> dict:
        return {
            "angle": self.angle,
            "cava": self.cava,
            "deduction": round(self.deduction, 4),
            "setback": round(self.setback, 4),
            "rule": self.rule,
            "source": self.source,
            "fallback": self.fallback,
            "k_factor": self.k_factor,
        }


@dataclass
class BentProfile:
    """
    Profilo piegato: N flange (quote a MEZZERIA) unite da N-1 pieghe.

    flanges:      lunghezze a mezzeria di spessore di ogni flangia, in
                  ordine — lo "sketch primitivo": nessun raggio, nessuno
                  spessore, solo segmenti e angoli (il raggio lo decide la
                  matrice/il punzone in produzione, non lo sketch)
    bends:        len(bends) == len(flanges) - 1
    thickness:    spessore lamiera (T) — libero di cambiare senza toccare
                  flanges/bends, è il punto di tutta la convenzione a
                  mezzeria (stesso sketch, spessori diversi)
    width:        larghezza del pezzo, perpendicolare alle pieghe
    material:     sceglie quale riga di `k_per_materiale` usare nella
                  calibrazione (es. "acciaio", "inox", "alluminio"). Se la
                  calibrazione non ha un K per quel materiale, si stima
                  DIN 6935. Default "acciaio".
    calibration:  Calibration | nome str. Porta i dati di calcolo (tabella
                  cave, K per materiale, valori misurati) — MAP.md D33.
                  Default "default" = K da manuale + tabella cave standard,
                  così `.develop()` funziona senza configurare niente.
                  Altri: "esempio_din_3cave", "inside_sum", o il nome di un
                  file in calibrations/ (la tua officina).
                  `flat.bends[i].source` dice sempre da dove viene il numero.
    orientation:  "horizontal" (default, lunghezza sviluppata su X) |
                  "vertical" (su Y)

    develop() ritorna un rettangolo (outer) più una linea per ogni piega,
    role="bending" — stesso schema che forge riconosce già per le linee di
    piega su un disegno letto da DXF.
    """
    flanges: List[float]
    bends: List[Bend]
    thickness: float
    width: float
    material: str = "acciaio"
    orientation: str = "horizontal"
    label: str = "bent_profile"
    calibration: object = "default"  # Calibration | nome str. Default: K da manuale + tabella cave standard.

    def _resolve_calibration(self):
        cal = self.calibration if self.calibration is not None else "default"
        if isinstance(cal, str):
            from ..rules.deduction import Calibration
            return Calibration.load(cal)
        return cal  # gia' un oggetto Calibration

    def develop(self) -> FlatGeometry:
        if len(self.flanges) < 2:
            raise ValueError("servono almeno 2 flange.")
        if len(self.bends) != len(self.flanges) - 1:
            raise ValueError(
                f"servono esattamente {len(self.flanges) - 1} pieghe per "
                f"{len(self.flanges)} flange, ricevute {len(self.bends)}."
            )
        for i, length in enumerate(self.flanges):
            if length <= 0:
                raise ValueError(f"flanges[{i}] deve essere maggiore di zero.")
        if self.thickness <= 0:
            raise ValueError("thickness deve essere maggiore di zero.")
        if self.width <= 0:
            raise ValueError("width deve essere maggiore di zero.")
        _check_orientation(self.orientation)

        calibration = self._resolve_calibration()

        results: List[BendResult] = []
        for i, bend in enumerate(self.bends):
            if not (0.0 < bend.angle < 180.0):
                raise ValueError(f"bends[{i}].angle deve essere fra 0 e 180 gradi (escluso).")
            if bend.radius is not None and bend.radius <= 0:
                raise ValueError(f"bends[{i}].radius deve essere maggiore di zero.")

            # L'accorciamento lo dà la calibrazione (MAP.md D33): valore
            # misurato per la combinazione, oppure la formula con K dal
            # materiale o stimato DIN 6935. Il raggio viene dalla cava (di
            # tabella o esplicita sul Bend), o da bend.radius se dato. La
            # linea di piega è UNA sola, all'apice (come nei DXF TruBend):
            # niente regione-arco, ogni flangia perde cd/2 per lato.
            # total = Σ flange - Σ cd.
            info = calibration.deduction_detail(
                self.thickness, bend.angle, bend.cava, bend.radius, self.material
            )
            cava_usata = (bend.cava if bend.cava is not None
                          else calibration.v_opening_for_thickness(self.thickness))
            results.append(BendResult(
                angle=bend.angle, cava=cava_usata, deduction=info.value,
                setback=info.value / 2.0, rule=info.rule, source=info.source,
                fallback=info.fallback, k_factor=info.k,
            ))

        cum = 0.0
        bend_positions: List[float] = []
        for i, length in enumerate(self.flanges):
            setback_before = results[i - 1].setback if i > 0 else 0.0
            setback_after = results[i].setback if i < len(self.bends) else 0.0
            flat = length - setback_before - setback_after
            if flat <= 0:
                raise ValueError(
                    f"flanges[{i}] ({length}) troppo corta per i raggi/angoli "
                    f"delle pieghe adiacenti."
                )
            cum += flat
            if i < len(self.bends):
                bend_positions.append(cum + results[i].bend_allowance / 2.0)
                cum += results[i].bend_allowance

        total_length = cum

        entities = [{
            "type": "polyline",
            "points": [
                (0.0, 0.0), (total_length, 0.0),
                (total_length, self.width), (0.0, self.width),
            ],
            "closed": True,
            "role": "outer",
        }]
        for pos in bend_positions:
            entities.append({
                "type": "line",
                "start": (pos, 0.0), "end": (pos, self.width),
                "role": "bending",
            })

        if self.orientation == "vertical":
            entities = swap_xy(entities)

        meta = {
            "flanges": list(self.flanges),
            "thickness": self.thickness,
            "width": self.width,
            "material": self.material,
            "total_length": total_length,
        }

        return FlatGeometry(entities=entities, label=self.label, meta=meta,
                            bends=results)


def resolve_calibration(calibration):
    """Nome stringa -> `Calibration` caricata, oggetto già risolto -> se
    stesso invariato. Stessa risoluzione di `BentProfile._resolve_calibration()`,
    riusata da `Cone`/`Cylinder` sfaccettati (MAP.md D45)."""
    cal = calibration if calibration is not None else "default"
    if isinstance(cal, str):
        from ..rules.deduction import Calibration
        return Calibration.load(cal)
    return cal


def resolve_facet_bend(
    calibration, thickness: float, angle_deg: float,
    explicit_radius: Optional[float], explicit_k: Optional[float],
    material: str,
):
    """
    Risolve raggio e K per UNA piega a faccette di `Cone`/`Cylinder` dalla
    `Calibration` dell'officina — stessa scaletta di `BentProfile`
    (misurato -> K per materiale -> stima DIN 6935, MAP.md D33), estesa
    qui alle faccette (MAP.md D45): un'officina usa la STESSA
    configurazione per sviluppare un profilo piegato e un cono/cilindro
    sfaccettato, sono pieghe fatte sulla stessa pressa.

    A differenza di `BentProfile`, qui non c'è una deduction da sottrarre
    a una flangia: il bend allowance si SOMMA fra due corde di faccette —
    si usa solo `info.k`/`info.radius` di `DeductionInfo`, mai `.value`.
    `explicit_radius`/`explicit_k` (`facet_bend_radius`/`facet_k_factor`)
    battono sempre la calibrazione, stesso principio di `Bend.radius` in
    `BentProfile` — ma qui esiste anche un override esplicito del K
    (`BentProfile` non ce l'ha: lì il K lo decide sempre la calibrazione).

    Ritorna `(radius, k, BendResult)` — il `BendResult` porta
    `bend_allowance` invece di `deduction`/`setback` (qui niente si
    sottrae, si aggiunge).
    """
    from ..rules.deduction import DEFAULT_UNKNOWN_RADIUS_MM, radius_from_v_opening

    cava = calibration.v_opening_for_thickness(thickness)
    info = calibration.deduction_detail(thickness, angle_deg, cava=cava,
                                        radius=explicit_radius, material=material)

    if explicit_radius is not None:
        radius = explicit_radius
    elif info.radius is not None:
        radius = info.radius
    else:
        # "misurato" ha vinto ma non porta un raggio derivabile (raro: la
        # combinazione esatta di questa faccetta risultava misurata) -
        # serve comunque un raggio per il bend allowance.
        radius = radius_from_v_opening(cava) if cava else DEFAULT_UNKNOWN_RADIUS_MM

    if explicit_k is not None:
        k, rule, source, fallback = explicit_k, "esplicito", f"k_factor {explicit_k:g} esplicito (facet_k_factor)", False
    else:
        k, rule, source, fallback = info.k, info.rule, info.source, info.fallback

    bend = Bend(angle=angle_deg, radius=radius, k_factor=k)
    bend_allowance = bend.bend_allowance(thickness, k)

    result = BendResult(
        angle=angle_deg, cava=cava, deduction=0.0, setback=0.0,
        rule=rule, source=source, fallback=fallback,
        k_factor=k, bend_allowance=bend_allowance,
    )
    return radius, k, result
