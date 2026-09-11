"""
tests/generate_calibration.py
-------------------------------
Legge una cartella di file .bnc di TruBend e ne ricava la lista "misurati"
per una calibrazione a dati misurati (`tipo_cliente: "misurato"`, vedi
bendly/rules/deduction.py e calibrations/tipo_misurato.json).

Generazione da zero (stampa su stdout, si redirige a mano):

    python tests/generate_calibration.py data_4_cloude "tipo_misurato" > calibrations/tipo_misurato.json

Aggiornamento di una calibrazione che esiste già (MERGE in place): si
tiene tutto quello che c'è nel file — nome, descrizione, k_per_materiale,
cava_per_spessore — e si rinfresca solo la lista "misurati" dai .bnc:

    python tests/generate_calibration.py data_4_cloude --merge calibrations/tipo_misurato.json

Non inventa niente: prende spessore, apertura V della matrice, angolo
(Sollwinkel) e accorciamento (Biegeverkuerzung) così come TruBend li ha
scritti nel file. Qualunque angolo, non solo 90° (TODO.md "angolo incluso
vero"): l'angolo VERO viene dal Sollwinkel, non assunto. Scarta i
duplicati (stessa terna spessore/cava/angolo): il primo .bnc in ordine di
nome vince.
"""

import glob
import json
import sys
from pathlib import Path

from bendly.adapters.trubend import leggi_bnc
from reconstruct import _ANGLE_TOKEN

_DEFAULT = Path(__file__).resolve().parent.parent / "calibrations" / "default.json"


def misurati_da_bnc(cartella: str) -> list:
    """Righe 'misurati' da tutti i .bnc sotto `cartella`.

    Angolo: quello che si confronta con `Bend.angle` nel motore (rotazione
    da piatta, NON il Sollwinkel/angolo incluso) — vedi `bendly/core/bend.py`
    e `bendly/rules/deduction.py`. `rotazione = |180 - Sollwinkel|`,
    indipendente dal verso (il motore è cieco al verso, MAP.md D23).

    Un .bnc con UNA sola piega REGISTRATA: qualunque angolo — ma solo se il
    nome del file promette anche lui una sola piega (`_ANGLE_TOKEN`, schema
    D7): un pezzo Z/omega ne promette di più nel nome, e se il .bnc ne
    registra comunque una sola si scarta il file intero (trovato 11 set
    2026 su `Za60ab50b100bc250c50s10.bnc`: `TEIL_BIEGEN`/
    `BIEGESCHRITTDATEN` hanno un solo `Biegenummer`, non due). Causa
    (Federico): la seconda piega di una Z non va in appoggio — dopo la
    prima il pezzo non è più piatto, quella flangia non passa dal ciclo
    automatico di posizionamento della pressa, quindi non ha un
    `Biegeverkuerzung` misurato pulito alla fonte, non è un dato perso da
    noi. Serve un'altra via per quel numero (es. misura a mano sul pezzo
    finito), non altro scavo nei `.bnc`.

    Un .bnc con PIÙ pieghe registrate: solo 90° — coi dati di oggi i colpi
    extra sono pre-pieghe (l'omega spessa: un angolo tirato in due volte,
    MAP.md D22) che qui, senza il DXF gemello per riconoscerle, sono
    indistinguibili da una piega vera; scartarle richiede
    `reconstruct.section_from_part` (che il DXF ce l'ha) — non ancora
    fatto per i pezzi non-90 a più pieghe (Z, omega). Vedi TODO.md.
    """
    visti = {}
    for percorso in sorted(glob.glob(f"{cartella}/**/*.bnc", recursive=True)):
        r = leggi_bnc(percorso)
        v = r.matrice.apertura_v if r.matrice else None
        pieghe_attese = max(1, len(_ANGLE_TOKEN.findall(Path(percorso).stem)))
        if len(r.pieghe) < pieghe_attese:
            continue  # export incompleto: il nome ne promette di più
        multi_piega = len(r.pieghe) > 1
        for pg in r.pieghe:
            if pg.angolo is None or pg.accorciamento_esterno is None:
                continue
            rotazione = round(abs(180.0 - pg.angolo), 4)
            if multi_piega and abs(rotazione - 90.0) > 1e-6:
                continue
            chiave = (r.spessore, v, rotazione)
            if chiave in visti:
                continue
            visti[chiave] = {
                "spessore": r.spessore,
                "cava": v,
                "angolo": rotazione,
                "accorciamento_esterno": round(pg.accorciamento_esterno, 4),
                "fonte": percorso.replace("\\", "/"),
            }
    return [visti[k] for k in sorted(visti, key=lambda t: (t[0], t[1] or 0, t[2]))]


def main() -> None:
    args = sys.argv[1:]
    cartella = args[0] if args else "data_4_cloude"

    if len(args) >= 3 and args[1] == "--merge":
        percorso = Path(args[2])
        profilo = json.loads(percorso.read_text(encoding="utf-8"))
        profilo["misurati"] = misurati_da_bnc(cartella)
        percorso.write_text(
            json.dumps(profilo, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        n = len(profilo["misurati"])
        print(f"{percorso}: {n} righe 'misurati' aggiornate dai .bnc di {cartella}/")
        return

    nome = args[1] if len(args) > 1 else "officina"

    # tabella cava standard: copiata dentro la calibrazione, non ereditata.
    # Una calibrazione = un file completo (vedi MAP.md D5).
    cava_default = json.loads(_DEFAULT.read_text(encoding="utf-8"))["cava_per_spessore"]

    profilo = {
        "nome": nome,
        "descrizione": f"{nome}. Accorciamenti di piega MISURATI dai file .bnc TruBend "
                       "(campo 'misurati'). Dove manca la combinazione, la formula col K "
                       "stimato DIN 6935. Aggiungere 'k_per_materiale' dal database "
                       "materiale della pressa per migliorare i casi non misurati.",
        "cava_per_spessore": cava_default,
        "misurati": misurati_da_bnc(cartella),
    }
    print(json.dumps(profilo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
