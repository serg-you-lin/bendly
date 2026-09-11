"""
unfold/rules/deduction.py
--------------------------
Quanto si accorcia una piega ("accorciamento" / bend deduction) e le
CALIBRAZIONI che portano i dati di un'officina.

C'è UNA formula sola (metodo della fibra neutra, MAP.md D33):

    BD = 2·(r + s/2)·tan(β/2)  −  β·(r + K·s)          β in radianti

    r = raggio interno · s = spessore · β = angolo di piega (rotazione da
    piatta) · K = fattore K in [0, 0.5] (posizione della fibra neutra:
    0 = faccia interna, 0.5 = mezzeria) — lo stesso K dei manuali e del
    database materiale di TruBend.

Da dove vengono r e K:
  - r: dalla cava (r ≈ cava/6), o esplicito.
  - K, in ordine: valore MISURATO per (spessore, cava, angolo) → K per
    materiale dalla calibrazione → stima DIN 6935 dal solo r/s.

Convenzione: le funzioni ritornano l'accorciamento a MEZZERIA (centerline),
quello che consuma `BentProfile`. Il valore letto sulla pressa è riferito
alle quote ESTERNE: `external_to_centerline_deduction()` converte.

`angolo` = di quanto ruota la lamiera da piatta (90 per una squadra), come
in bend.py — NON l'angolo incluso.

Nota di naming (MAP.md D29): le CHIAVI dei file JSON in calibrations/
(`cava_per_spessore`, `misurati`, `k_per_materiale`, `metodo`, `spessore`,
`cava`, `angolo`, ...) restano in italiano: sono un formato dati, non
identificatori Python.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------
# La formula (metodo della fibra neutra) + la stima DIN 6935 del fattore K
# --------------------------------------------------------------------------

def bend_deduction(radius: float, thickness: float, angle_deg: float, k: float,
                   reference: str = "mezzeria") -> float:
    """Accorciamento di piega, formula della fibra neutra.

    k = fattore K in [0, 0.5]: distanza della fibra neutra dalla faccia
        interna / spessore.
    reference: "mezzeria" (default, per BentProfile) | "esterno" (quello
        che si legge sulla pressa).
    """
    a = math.radians(angle_deg)
    offset = thickness / 2.0 if reference == "mezzeria" else thickness
    setback = (radius + offset) * math.tan(a / 2.0)
    bend_allowance = a * (radius + k * thickness)
    return 2.0 * setback - bend_allowance


def k_din6935(radius: float, thickness: float) -> float:
    """Stima DIN 6935 del fattore K (in [0, 0.5]), dal SOLO rapporto
    raggio/spessore. DIN definisce k' = 0.65 + 0.5·log10(r/s) in [0, 1]
    (k' = 1 per r/s > 5); qui K = k'/2. Cieca al materiale — tarata
    sull'acciaio."""
    if radius <= 0 or thickness <= 0:
        return 0.5
    k_din = 0.65 + 0.5 * math.log10(radius / thickness)
    return max(0.0, min(0.5, k_din / 2.0))


def bend_allowance_din6935(radius: float, thickness: float, angle_deg: float) -> float:
    """Lunghezza dell'asse neutro dentro la piega, con K stimato DIN 6935."""
    return math.radians(angle_deg) * (radius + k_din6935(radius, thickness) * thickness)


def deduction_din6935(radius: float, thickness: float, angle_deg: float,
                      reference: str = "mezzeria") -> float:
    """Accorciamento di piega con K stimato DIN 6935 (scorciatoia di
    `bend_deduction(..., k_din6935(radius, thickness))`)."""
    return bend_deduction(radius, thickness, angle_deg,
                          k_din6935(radius, thickness), reference)


def external_to_centerline_deduction(external_deduction: float, thickness: float,
                                     angle_deg: float) -> float:
    """Converte un accorciamento riferito alle quote esterne (come nei .bnc
    TruBend) in accorciamento a mezzeria."""
    return external_deduction - thickness * math.tan(math.radians(angle_deg) / 2.0)


def radius_from_v_opening(v_opening: float) -> float:
    """Stima del raggio interno di piega in aria da una cava a V.
    Regola classica: r ≈ V / 6."""
    return v_opening / 6.0


# Raggio usato quando non c'è né un raggio esplicito né una cava nota per lo
# spessore (MAP.md D36). NON è una stima scalata dallo spessore (mai
# `r = spessore`: sembra informata ma è arbitraria e si muove in silenzio con
# lo spessore) — è una costante fissa, uguale per ogni spessore, sempre
# dichiarata in chiaro nel `source` del risultato.
DEFAULT_UNKNOWN_RADIUS_MM = 1.0


# --------------------------------------------------------------------------
# Quote esterne <-> mezzeria per la LUNGHEZZA di una flangia (Fase 3 -
# layer umano). Diverso da external_to_centerline_deduction() sopra: quella
# converte l'accorciamento TOTALE di una piega, questa converte la
# lunghezza di UNA flangia. Stessa idea, un'altra grandezza.
#
# La differenza fra l'apice virtuale ESTERNO (dove si incontrerebbero le
# due facce esterne estese, se non ci fosse il raggio) e l'apice virtuale a
# MEZZERIA è INDIPENDENTE dal raggio: OSS - CSS = (R+T)*tan(a/2) -
# (R+T/2)*tan(a/2) = (T/2)*tan(a/2). Il termine in R si elide sempre -
# è un puro effetto di offset (T/2 fra faccia esterna e mezzeria), non
# dipende da quanto è arrotondato lo spigolo.
# --------------------------------------------------------------------------

def external_to_centerline_flange(
    external_length: float,
    thickness: float,
    angle_before: Optional[float] = None,
    angle_after: Optional[float] = None,
) -> float:
    """Converte la lunghezza ESTERNO-ESTERNO di una flangia (apice virtuale
    delle facce esterne, come la quota che dà un carpentiere) nella
    lunghezza a MEZZERIA che consuma `BentProfile.flanges`.

    angle_before/angle_after: l'angolo (convenzione Bend.angle, NON
    l'angolo incluso) della piega adiacente su ciascun lato; None se quel
    lato è un'estremità del pezzo (nessuna piega lì).
    """
    length = external_length
    for angle in (angle_before, angle_after):
        if angle is not None:
            length -= (thickness / 2.0) * math.tan(math.radians(angle) / 2.0)
    return length


def centerline_to_external_flange(
    centerline_length: float,
    thickness: float,
    angle_before: Optional[float] = None,
    angle_after: Optional[float] = None,
) -> float:
    """Inversa di `external_to_centerline_flange`: da mezzeria a esterno-esterno."""
    length = centerline_length
    for angle in (angle_before, angle_after):
        if angle is not None:
            length += (thickness / 2.0) * math.tan(math.radians(angle) / 2.0)
    return length


def external_flanges_to_centerline(
    external_flanges: list[float],
    bend_angles: list[float],
    thickness: float,
) -> list[float]:
    """Converte l'intero elenco di flange (come lo si passerebbe a
    `BentProfile.flanges`) da quote esterno-esterno a quote a mezzeria.

    bend_angles: un angolo per piega, len(bend_angles) == len(external_flanges) - 1
    (stessa struttura di BentProfile: N flange, N-1 pieghe).
    """
    if len(bend_angles) != len(external_flanges) - 1:
        raise ValueError(
            f"servono esattamente {len(external_flanges) - 1} angoli di piega per "
            f"{len(external_flanges)} flange, ricevuti {len(bend_angles)}."
        )
    result = []
    for i, length in enumerate(external_flanges):
        angle_before = bend_angles[i - 1] if i > 0 else None
        angle_after = bend_angles[i] if i < len(bend_angles) else None
        result.append(external_to_centerline_flange(length, thickness, angle_before, angle_after))
    return result


# --------------------------------------------------------------------------
# Calibrazioni officina
# --------------------------------------------------------------------------

# Nomi di calibrazione che funzionano SENZA un file in calibrations/.
#   "inside_sum" — lavori in quote INTERNE: passi le flange interne, lo
#                  sviluppo è la loro somma esatta (raggio 0, accorciamento 0).
#   "din6935"    — la pura stima della norma: nessuna tabella cave, nessun K
#                  di officina; devi passare cava= o radius= sulla piega.
BARE_CALIBRATIONS = {
    "inside_sum": {"nome": "inside_sum", "metodo": "inside_sum"},
    "din6935": {"nome": "din6935"},
}


@dataclass
class DeductionInfo:
    """Accorciamento di piega + da dove viene il numero.

    Interrogabile apposta (skill 'interrogabilità per comprensione'):
      rule   — come è stato ottenuto: "misurato" | "k_materiale" | "din6935"
               | "inside_sum".
      source — la provenienza in chiaro.
      k      — il fattore K usato (None per "misurato" e "inside_sum").
      fallback — True quando c'erano dati misurati per lo spessore ma non
               per QUESTA combinazione, e si è dovuto stimare.
      radius — il raggio interno RISOLTO (esplicito, o da cava) usato per
               calcolare `value`. `None` per "misurato" (un accorciamento
               misurato non deriva da un raggio: è un dato diretto), `0.0`
               per "inside_sum" (raggio 0 per definizione del metodo).
               Serve a chi ha bisogno del raggio stesso, non solo
               dell'accorciamento — es. le pieghe sfaccettate di
               Cone/Cylinder, che sommano un bend allowance invece di
               sottrarre una deduction (MAP.md D45).
    """
    value: float                       # accorciamento a mezzeria (mm)
    rule: str
    source: str
    k: Optional[float] = None
    fallback: bool = False
    radius: Optional[float] = None


# I quattro casi di riferimento per cui si controlla ogni scelta di default
# (MAP.md D36, TODO.md). Campo facoltativo `tipo_cliente` di una
# calibrazione: la dichiarazione di quale caso è, verificabile da codice
# con `tipo_cliente_coerente()` — non un'etichetta decorativa.
#
#   zero_config    — A: nessun dato dato all'utente, raggio fisso dichiarato.
#   cava_propria   — B: solo la tabella spessore->cava, K stimato DIN.
#   somma_interna  — C: bypassa raggio/K, somma le quote interne (metodo
#                    "inside_sum").
#   misurato       — D: accorciamenti misurati dal CAM/pressa.
TIPI_CLIENTE = ("zero_config", "cava_propria", "somma_interna", "misurato")


class Calibration:
    """Una calibrazione = i dati di calcolo di un'officina.

    Un file JSON in calibrations/, **completo** (nessuna ereditarietà fra
    calibrazioni, MAP.md D5). Campi (tutti opzionali tranne, di fatto, la
    tabella cave):

      tipo_cliente       uno di TIPI_CLIENTE sopra — quale dei 4 casi di
                         riferimento è questa calibrazione (MAP.md D36/D39).
      cava_per_spessore  { "<spessore>": <cava>, ... }  — la via per il raggio
      k_per_materiale    { "acciaio": 0.40, "inox": 0.38, ... }  — il tuo K
      misurati           [ {spessore, cava, angolo, accorciamento_esterno, fonte}, ... ]
      metodo             "inside_sum" — lavori in quote INTERNE: le flange
                         passate sono quote interne, lo sviluppo è la loro
                         somma esatta (raggio 0, accorciamento 0)

    Vedi COME_FUNZIONA.md.
    """

    def __init__(self, data: dict):
        self.data = data

    @property
    def tipo_cliente(self) -> Optional[str]:
        return self.data.get("tipo_cliente")

    # --- caricamento --------------------------------------------------------

    CALIBRATIONS_FOLDER = Path(__file__).resolve().parent.parent.parent / "calibrations"

    @classmethod
    def load(cls, name: str, folder: str | Path | None = None) -> "Calibration":
        folder = Path(folder) if folder is not None else cls.CALIBRATIONS_FOLDER
        path = Path(folder) / f"{name}.json"
        if not path.is_file() and name in BARE_CALIBRATIONS:
            return cls(dict(BARE_CALIBRATIONS[name]))
        return cls(json.loads(path.read_text(encoding="utf-8")))

    # --- lookup ---------------------------------------------------------

    def _field(self, key: str, default=None):
        return self.data.get(key, default)

    def v_opening_for_thickness(self, thickness: float) -> Optional[float]:
        """Cava per uno spessore. `None` = non la conosciamo (spessore
        assente dalla tabella, o presente con valore `null` — "so che questo
        spessore esiste, non so la tua cava per lui", D36)."""
        table = self._field("cava_per_spessore", {}) or {}
        key = str(thickness)
        if key in table and table[key] is not None:
            return float(table[key])
        known = {s: v for s, v in table.items() if v is not None}
        if not known:
            return None
        closest = min(known, key=lambda s: abs(float(s) - thickness))
        return float(known[closest])

    def k_for_material(self, material: str) -> Optional[float]:
        table = self._field("k_per_materiale", {}) or {}
        if material in table:
            return float(table[material])
        return None

    def _measured_row(self, thickness: float, cava: Optional[float],
                      angle_deg: float) -> Optional[dict]:
        """Cerca la riga MISURATA per (spessore, cava, angolo) esatti.
        Nessuna interpolazione: match esatto o niente."""
        for m in self._field("misurati", []) or []:
            if abs(m["spessore"] - thickness) > 1e-6:
                continue
            if cava is not None and abs(m.get("cava", cava) - cava) > 1e-6:
                continue
            if abs(m.get("angolo", 90) - angle_deg) > 1e-6:
                continue
            return m
        return None

    def _has_measured_for_thickness(self, thickness: float) -> bool:
        return any(abs(m["spessore"] - thickness) <= 1e-6
                   for m in self._field("misurati", []) or [])

    # --- API principale -------------------------------------------------

    def bend_allowance_din(self, thickness: float, angle_deg: float,
                           cava: Optional[float] = None) -> float:
        """Bend allowance stimata DIN 6935 — solo per posizionare la linea di
        piega nello sviluppo, non entra nel totale."""
        if cava is None:
            cava = self.v_opening_for_thickness(thickness)
        r = radius_from_v_opening(cava) if cava else DEFAULT_UNKNOWN_RADIUS_MM
        return bend_allowance_din6935(r, thickness, angle_deg)

    def centerline_deduction(self, thickness: float, angle_deg: float,
                             cava: Optional[float] = None,
                             radius: Optional[float] = None,
                             material: str = "acciaio") -> float:
        """Accorciamento di piega (a mezzeria) — solo il numero. Per la
        provenienza usa `deduction_detail()`."""
        return self.deduction_detail(thickness, angle_deg, cava, radius, material).value

    def deduction_detail(self, thickness: float, angle_deg: float,
                         cava: Optional[float] = None,
                         radius: Optional[float] = None,
                         material: str = "acciaio") -> DeductionInfo:
        """Accorciamento di piega (a mezzeria) + provenienza. Vedi la
        docstring del modulo per la formula e la scaletta di K."""
        # -- scorciatoia: somma quote interne, niente formula --------------
        # "inside_sum" non è una regola di accorciamento: è la dichiarazione
        # che stai lavorando TUTTO in quote interne. Le flange che passi sono
        # le quote interne (spigolo interno a spigolo interno), lo sviluppo è
        # la loro somma esatta, raggio 0, nessun accorciamento. È il metodo
        # "non voglio la tua matematica" di moltissime carpenterie (MAP.md
        # D35): su pieghe dello stesso verso non è interpretabile.
        if self._field("metodo") == "inside_sum":
            return DeductionInfo(
                0.0, "inside_sum",
                "somma quote interne: sviluppo = somma delle flange (interne), "
                "raggio 0, nessun accorciamento",
                radius=0.0,
            )

        # via normale: la cava viene dalla tabella spessore->cava
        if cava is None:
            cava = self.v_opening_for_thickness(thickness)

        # -- 1. valore MISURATO per questa combinazione -------------------
        row = self._measured_row(thickness, cava, angle_deg)
        if row is not None:
            v = external_to_centerline_deduction(
                row["accorciamento_esterno"], thickness, angle_deg)
            return DeductionInfo(v, "misurato",
                                 row.get("fonte") or "valore misurato (.bnc)")

        # -- il raggio: esplicito, dalla cava, o fisso dichiarato (D36) ----
        if radius is not None:
            r = radius
            r_src = f"raggio {r:g} esplicito"
        elif cava:
            r = radius_from_v_opening(cava)
            r_src = f"raggio {r:g} da cava {cava:g}"
        elif self._field("cava_per_spessore") is not None:
            # la calibrazione HA una tabella cave, solo non copre questo
            # spessore (assente, o presente con valore null): zero-config
            # deve funzionare comunque (MAP.md D33/D36), niente errore —
            # raggio fisso dichiarato, mai una stima scalata dallo spessore.
            r = DEFAULT_UNKNOWN_RADIUS_MM
            r_src = f"raggio {r:g} fisso (nessuna cava nota per {thickness:g} mm)"
        else:
            # nessuna tabella cave affatto: scelta esplicita di calibrazioni
            # "nude" come din6935 — lì l'utente deve dare cava=/radius= per
            # ogni piega, niente da indovinare.
            nome = self._field("nome", "?")
            raise ValueError(
                f"calibrazione '{nome}': nessuna tabella cave (manca "
                f"'cava_per_spessore') e nessun raggio per lo spessore "
                f"{thickness:g}. Passa cava=/radius= sulla piega, o usa una "
                f"calibrazione con tabella cave (es. 'default')."
            )

        fallback = self._has_measured_for_thickness(thickness)

        # -- 2. il TUO K per materiale ----------------------------------
        k_mat = self.k_for_material(material)
        if k_mat is not None:
            v = bend_deduction(r, thickness, angle_deg, k_mat, "mezzeria")
            src = f"K {k_mat:g} ({material}, calibrazione '{self._field('nome', '?')}') · {r_src}"
            return DeductionInfo(v, "k_materiale", src, k=k_mat, fallback=fallback, radius=r)

        # -- 3. stima DIN 6935 dal solo r/s ---------------------------
        k = k_din6935(r, thickness)
        v = bend_deduction(r, thickness, angle_deg, k, "mezzeria")
        src = f"K {k:.3f} (stima DIN 6935 da r/s) · {r_src}"
        return DeductionInfo(v, "din6935", src, k=k, fallback=fallback, radius=r)


# --------------------------------------------------------------------------
# Coerenza fra tipo_cliente dichiarato e contenuto reale della calibrazione
# --------------------------------------------------------------------------

def tipo_cliente_coerente(calibration: Calibration) -> list[str]:
    """Controlla che una calibrazione mantenga la promessa del suo
    `tipo_cliente` (MAP.md D39). Ritorna la lista dei problemi trovati
    (vuota = coerente). Non fa niente se `tipo_cliente` non è dichiarato —
    è un controllo opzionale, per chi lo dichiara.

    Nasce da un bug vero: `default.json` (`zero_config`) copiava la
    tabella cave reale della calibrazione a dati misurati (`misurato`)
    spacciandola per generica. Il controllo prende esattamente quella
    classe di errori.
    """
    tipo = calibration.tipo_cliente
    if tipo is None:
        return []
    if tipo not in TIPI_CLIENTE:
        return [f"tipo_cliente '{tipo}' non è uno dei valori noti {TIPI_CLIENTE}"]

    problemi: list[str] = []
    cave = calibration._field("cava_per_spessore") or {}
    cave_note = {k: v for k, v in cave.items() if v is not None}
    misurati = calibration._field("misurati") or []
    metodo = calibration._field("metodo")

    if tipo == "zero_config":
        if cave_note:
            problemi.append(
                f"zero_config ma 'cava_per_spessore' ha valori reali "
                f"({len(cave_note)}) — un cliente a zero config non dovrebbe "
                f"ereditare cave di nessuno; usa cava_propria se ce le hai."
            )
        if misurati:
            problemi.append("zero_config ma 'misurati' non è vuoto — usa 'misurato'.")
    elif tipo == "cava_propria":
        if not cave_note:
            problemi.append("cava_propria ma 'cava_per_spessore' non ha nessun valore reale.")
        if misurati:
            problemi.append("cava_propria ma 'misurati' non è vuoto — usa 'misurato'.")
    elif tipo == "somma_interna":
        if metodo != "inside_sum":
            problemi.append("somma_interna ma 'metodo' non è 'inside_sum'.")
    elif tipo == "misurato":
        if not misurati:
            problemi.append("misurato ma 'misurati' è vuoto.")
        if not cave_note:
            # MAP.md D40: chi ha un CAM/pressa quasi certamente sa anche
            # quale cava usa per spessore — non costa niente chiederglielo.
            # Senza, ogni combinazione non misurata (spessore/cava/angolo
            # nuovi) ripiega sul raggio fisso di zero_config invece che su
            # una cava vera: un fallback inutilmente più grezzo di quanto
            # potrebbe essere per QUESTO utente.
            problemi.append(
                "misurato ma 'cava_per_spessore' non ha nessun valore reale "
                "— il fallback per le combinazioni non misurate userebbe il "
                "raggio fisso (zero_config) invece della cava vera; "
                "aggiungila, chi ha un CAM la conosce comunque."
            )

    return problemi
