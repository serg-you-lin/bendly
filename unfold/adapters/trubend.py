"""
unfold/adapters/trubend.py
---------------------------
Lettore dei file .bnc di TruBend / TruTops (formato testo "Flux").

Un .bnc NON contiene un calcolo: contiene il RISULTATO che TruBend ha già
calcolato. Questo modulo lo legge e basta. Ne tira fuori i pochi numeri che
servono a calibrare un profilo officina:

  - materiale, spessore, dimensioni dello sviluppo piatto
  - utensili usati (punzone / matrice, con apertura V e raggio)
  - per ogni piega: angolo e "Biegeverkuerzung" (accorciamento, riferito a
    quote esterne)

Struttura del formato (per chi un domani deve leggere un CAM diverso):
il file è a blocchi BEGIN_<NOME> ... ENDE_<NOME>. Dentro ogni blocco:
  ZA,MM,<n>                     -> seguono n righe di intestazione colonna
  MM,AT,1,<attr>,...,'<nome>'   -> definisce una colonna, in ordine
  ZA,DA,<m>                     -> seguono m righe di dati
  DA,<val>,<val>,...            -> una riga di dati, i valori in ordine
                                  mappano sulle colonne MM qui sopra
Le righe che iniziano con "* " sono continuazioni della riga precedente.
I campi sono separati da virgola; le stringhe sono fra apici singoli.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# --------------------------------------------------------------------------
# lettura grezza del formato a blocchi
# --------------------------------------------------------------------------

def _righe_unite(testo: str) -> List[str]:
    out: List[str] = []
    for riga in testo.splitlines():
        if riga[:2] in ("* ", "*\t") or riga.startswith("*  "):
            out[-1] += riga.lstrip("* ").rstrip()
        else:
            out.append(riga.rstrip())
    return out


def _spezza_campi(riga: str) -> List[str]:
    """Spezza una riga DA,... rispettando gli apici singoli."""
    campi = re.findall(r"'[^']*'|[^,]+", riga)
    puliti = []
    for c in campi:
        c = c.strip()
        if c.startswith("'") and c.endswith("'"):
            puliti.append(c[1:-1])
        else:
            puliti.append(c)
    return puliti


def _valore(x: str):
    try:
        return float(x) if ("." in x or "e" in x.lower()) else int(x)
    except ValueError:
        return x


def leggi_blocchi(percorso: str | Path) -> Dict[str, List[dict]]:
    """Ritorna {NOME_BLOCCO: [ {nome_colonna: valore, ...}, ... ]}."""
    righe = _righe_unite(Path(percorso).read_text(encoding="latin-1"))
    blocchi: Dict[str, List[dict]] = {}
    i = 0
    while i < len(righe):
        r = righe[i]
        m = re.match(r"BEGIN_(\w+)", r)
        if not m:
            i += 1
            continue
        nome = m.group(1)
        i += 1
        colonne: List[str] = []
        dati: List[dict] = []
        while i < len(righe) and not righe[i].startswith(f"ENDE_{nome}"):
            r = righe[i]
            if r.startswith("MM,AT"):
                cm = re.search(r"'([^']+)'", r)
                if cm:
                    colonne.append(cm.group(1))
            elif r.startswith("DA,"):
                campi = _spezza_campi(r)[1:]  # salta 'DA'
                riga_dati = {}
                for k, v in zip(colonne, campi):
                    riga_dati[k] = _valore(v)
                # tieni anche i campi grezzi in coda (colonne non nominate)
                riga_dati["_campi"] = [_valore(c) for c in campi]
                dati.append(riga_dati)
            i += 1
        blocchi.setdefault(nome, []).extend(dati)
    return blocchi


# --------------------------------------------------------------------------
# estrazione dei dati che ci servono
# --------------------------------------------------------------------------

@dataclass
class Utensile:
    nome: str
    tipo: str            # "punzone" | "matrice" | "?"
    raggio: Optional[float]
    apertura_v: Optional[float]
    angolo: Optional[float]


@dataclass
class PiegaBnc:
    numero: int
    angolo: Optional[float]              # Sollwinkel (gradi di rotazione)
    accorciamento_esterno: Optional[float]  # Biegeverkuerzung (quote esterne)


@dataclass
class LetturaBnc:
    percorso: str
    nome: str
    materiale: Optional[str]
    spessore: Optional[float]
    sviluppo_x: Optional[float]
    sviluppo_y: Optional[float]
    n_pieghe: Optional[int]
    utensili: List[Utensile] = field(default_factory=list)
    pieghe: List[PiegaBnc] = field(default_factory=list)

    @property
    def matrice(self) -> Optional[Utensile]:
        for u in self.utensili:
            if u.tipo == "matrice":
                return u
        return None

    @property
    def sviluppo(self) -> Optional[float]:
        vals = [v for v in (self.sviluppo_x, self.sviluppo_y) if v]
        return max(vals) if vals else None


def _classifica_utensile(nome: str) -> str:
    n = nome.upper()
    if n.startswith("OW") or "PUNZ" in n:
        return "punzone"
    if n.startswith("EV") or n.startswith("EW") or "MATR" in n or "/H" in n or "W" in n[:4]:
        return "matrice"
    return "?"


def _apertura_da_nome(nome: str) -> Optional[float]:
    # l'apertura V della matrice sta sempre dopo la lettera W:
    #   "EV005/H W16/30 R1.6" -> 16 ; "EV/H W50/80 R5" -> 50 ; "EV001 W6/30 R0.6" -> 6
    m = re.search(r"\bW\s?(\d+(?:\.\d+)?)", nome)
    return float(m.group(1)) if m else None


def leggi_bnc(percorso: str | Path) -> LetturaBnc:
    percorso = str(percorso)
    b = leggi_blocchi(percorso)

    parte = (b.get("BIEGETEILSTAMM") or [{}])[0]
    lettura = LetturaBnc(
        percorso=percorso,
        nome=parte.get("Bezeichnung") or Path(percorso).stem,
        materiale=parte.get("Material"),
        spessore=_num(parte.get("Blechdicke")),
        sviluppo_x=_num(parte.get("UmschreibendesRechteckX")),
        sviluppo_y=_num(parte.get("UmschreibendesRechteckY")),
        n_pieghe=_int(parte.get("AnzahlBiegeschritte")),
    )

    for w in b.get("WERKZEUGSTAMM", []):
        nome = w.get("Werkzeugbezeichnung") or ""
        if not nome:
            continue
        lettura.utensili.append(Utensile(
            nome=nome,
            tipo=_classifica_utensile(nome),
            raggio=_num(w.get("Radius")),
            apertura_v=_apertura_da_nome(nome),
            angolo=_num(w.get("Winkel")),
        ))

    # angoli di piega dal blocco TEIL_BIEGEN (una riga Press### per piega)
    angoli = [_num(p.get("Sollwinkel")) for p in b.get("TEIL_BIEGEN", [])]
    # accorciamento dal blocco BIEGESCHRITTDATEN, colonna 'Biegeverkuerzung'
    passi = b.get("BIEGESCHRITTDATEN", [])
    for idx, passo in enumerate(passi):
        acc = _num(passo.get("Biegeverkuerzung"))
        if acc is None:
            # fallback: cerca un numero negativo "isolato" nei campi grezzi
            for v in passo.get("_campi", []):
                if isinstance(v, float) and -60 < v < -0.1:
                    acc = v
                    break
        num = _int(passo.get("Biegenummer")) or (idx + 1)
        ang = angoli[idx] if idx < len(angoli) else None
        lettura.pieghe.append(PiegaBnc(
            numero=num,
            angolo=ang,
            accorciamento_esterno=abs(acc) if acc is not None else None,
        ))

    return lettura


def _num(x) -> Optional[float]:
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _int(x) -> Optional[int]:
    v = _num(x)
    return int(v) if v is not None else None
