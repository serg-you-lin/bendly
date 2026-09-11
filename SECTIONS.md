# Le sezioni

Una **sezione** (`Section`, prima si chiamava "dima") e' il disegno in
**sezione** di un pezzo di lamiera piegata, generato dai parametri invece
che disegnato a mano.

## A cosa serve

1. **Pattern di riconoscimento** per l'interprete di disegno: guardando
   una vista, capire se e' *lamiera piegata* (da sviluppare) o un
   *contorno da tagliare*.
2. **Formalizzare i pezzi di test** golden: la geometria di L/U/Z/O sta
   in codice, non come numeri sparsi nei test.
3. **Portare il verso della piega** (su/giu): e' l'unico posto dove vive
   — il motore (`BentProfile`) e' cieco al verso apposta (vedi `MAP.md`
   D1/D23). `Section.to_bent_profile()` e' il ponte che lo butta via
   entrando nel motore.

## Cosa contiene una sezione

**Solo il profilo reale** — il contorno pieno a spessore. **Niente linea
di mezzeria disegnata**: la mezzeria si ricava offsettando le due facce
esterne di meta' spessore verso l'interno.

## Come si riconosce "e' lamiera piegata"

Segnale triplo (`bendly/rules/read_section.py`, `read_section`):

- le facce sono sempre **parallele a distanza costante** -> spessore candidato;
- quello spessore e' una **lamiera che esiste davvero** (`sheet_thicknesses.json`);
- gli spigoli curvi sono **coppie di archi concentrici** con raggi che
  differiscono **esattamente dello spessore** (es. interno 1, esterno 4
  -> differenza 3 = spessore) -> allora e' *piegata*, non un contorno
  piatto ne' un profilo da tagliare.

`read_section` fa anche l'inverso di `Section`: dalla sola sezione
ricava spessore, segmenti a mezzeria (apice-apice) e angoli (schema
naming). Una sezione si legge uguale da un capo o dall'altro: segmenti e
angoli escono in una forma canonica (fissa) fra le due letture speculari.

## Il raggio e' inventato

Il raggio della sezione **non entra nel calcolo dello sviluppo** — quello
lo decide la calibrazione officina dalla cava. Il raggio serve solo al
pattern.

Le sezioni hanno **un solo raggio in entrata**: `inner_radius`, che per le
sezioni di prova e' **1 mm fisso**, uguale per ogni spessore (raggio
minimo simbolico). Il raggio a mezzeria non e' un dato: si deriva
(`inner_radius + spessore/2`) e varia con lo spessore.

## Parametri (schema di naming)

`FORMA` + coppie `segmento`/`angolo` + `s<spessore>`.

Esempio: `Ua60ab90b110bc90c60s3`
- `U` forma
- `a60` segmento a = 60 mm (a **mezzeria**, da apice virtuale ad apice virtuale)
- `ab90` angolo fra a e b = 90 (schema naming: piatto = 180, su = 90, giu = 270)
- ... `b110`, `bc90`, `c60`
- `s3` spessore 3 mm

Il raggio non entra nel nome: le sezioni di prova sono tutte a raggio
interno 1 mm.

I segmenti sono gli stessi numeri che si passano a `BentProfile.flanges`
e che stanno in `tests/test_golden_officina.py` (`FORME`).

## Come si generano

```
python tests/generate_section.py
```

Scrive in `data_4_cloude/sections/` (rigenerabile, non versionato) sia
`.dxf` (via forge, per guardarle) sia `.json` (entita' neutre + parametri,
per i test con `forge.load_geometry` senza passare da un file). Una
sezione per forma x spessore (1, 3, 10): 12 in totale, meno quelle
geometricamente impossibili.

Il motore e' `bendly/section.py` (`Section`). Combinazioni impossibili
(segmento piu' corto dei raggi adiacenti) vengono saltate e riportate. Con
raggio interno 1 mm le 12 sezioni del set golden si generano tutte.

## Test

`tests/test_read_section.py` — giro chiuso: `Section` -> sezione -> buttata
via tutto tranne il contorno -> `read_section` ricava spessore,
segmenti e angoli; devono tornare i parametri di partenza. Non serve forge
ne' i dati cliente, gira sempre.
