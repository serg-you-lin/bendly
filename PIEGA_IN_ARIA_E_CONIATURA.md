# Piega in aria, sul fondo, coniatura

Modulo di riferimento. Nasce dal dubbio sul calcolo delle pieghe **non a
90°** (vedi `MAP.md` D34, `TODO.md`): prima di decidere quanto fidarsi
della formula fuori dai 90° bisogna sapere di che piega stiamo parlando,
perché "in aria" e "coniata" sono due mondi diversi e la formula della
fibra neutra (DIN 6935, quella che usa `unfold`) è tarata su uno solo.

I termini non sono puliti: ogni lingua e ogni costruttore raggruppa in
modo suo. Sotto, prima la sostanza, poi il glossario nelle quattro lingue
che contano.

---

## Le tre modalità, in sostanza

### 1. Piega in aria (*air bending*)

Il punzone spinge la lamiera dentro la V della matrice **ma non fino in
fondo**. La lamiera tocca la matrice **solo sui due spigoli** della V; sta
"per aria" sopra il fondo. L'angolo lo decide **quanto scende il punzone**:
più a fondo, più chiuso. Con lo stesso set di utensili fai qualsiasi
angolo, basta cambiare la quota di discesa.

- **Forza:** la più bassa delle tre.
- **Ritorno elastico (molla):** c'è, sensibile, va compensato scendendo un
  po' più del nominale.
- **Tolleranza angolo:** circa ±0,5° … ±0,75° (dipende da macchina e
  operatore).
- **Raggio interno:** **non** lo fa il punzone. Si forma come **percentuale
  dell'apertura della cava**: regola pratica ~15% per l'acciaio dolce
  (~20% per l'inox 304, ~12% per l'alluminio 5052). Cambi cava → cambi
  raggio → cambia l'allungamento nella piega → cambia l'accorciamento.
  È esattamente il motivo per cui `unfold` stima `r ≈ cava / 6` (≈ 16%).
- **Quando:** praticamente sempre, oggi. Officina 1 lavora così.

### 2. Sul fondo (*bottoming* / *bottom bending*)

Il punzone spinge la lamiera **fino a farla appoggiare sul fondo e sui
fianchi** della V, ma senza schiacciarla. L'angolo della matrice è ≈
l'angolo finale che vuoi: un set di utensili = un angolo.

- **Forza:** ~3–5 volte la piega in aria.
- **Ritorno elastico:** ridotto rispetto all'aria, ma ancora presente.
- **Tolleranza angolo:** circa ±0,5°.
- **Raggio interno:** lo impone in buona parte il fondo della matrice.

### 3. Coniatura (*coining*)

Il punzone schiaccia la lamiera contro la matrice con **pressione molto
alta**, tanto che il materiale viene "stampato" e prende **esattamente**
la forma di punzone e matrice, anche nella zona di piega (si assottiglia
un po' lì sotto).

- **Forza:** 5–30 volte la piega in aria a seconda della fonte (i giapponesi
  la danno come 5–8 volte il *bottoming*). Esempio dagli USA: acciaio dolce
  14 gauge a 90° ~1,5 t/pollice in aria, ~50 t/pollice coniato.
- **Ritorno elastico:** quasi nullo — è il pregio della coniatura.
- **Tolleranza angolo:** circa ±0,25°.
- **Raggio interno:** lo fa il **punzone**, non la cava.
- **Quando:** solo casi speciali che vogliono pochissima molla e alta
  ripetibilità. Costa in tonnellaggio e usura utensili.

> Nota terminologica: in inglese e in giapponese spesso **"air bending"
> raggruppa *partial bending* + *bottoming*** (tutto ciò che non è
> coniatura). In tedesco la famiglia è *Gesenkbiegen* / *Abkanten* e la
> divisione è *Freibiegen* vs *Prägebiegen* (il *bottoming* tedesco non ha
> un nome unico stabile: "auf Block biegen", "im Gesenk").

---

## Tabella di confronto

| | Piega in aria | Sul fondo | Coniatura |
|---|---|---|---|
| Contatto con la matrice | 2 spigoli | fondo + fianchi | fondo + fianchi, schiacciata |
| Forza (× aria) | 1 | 3–5 | 15–40 (5–30 secondo altre fonti) |
| Ritorno elastico | sensibile | ridotto | ~nullo |
| Tolleranza angolo | ±0,5°…±0,75° | ±0,5° | ±0,25° |
| Chi fa il raggio interno | l'apertura cava (~15% s.dolce) | il fondo matrice | il punzone |
| Angoli con un set utensili | tutti | uno | uno |
| Uso tipico | quasi tutto | serie con spessori grossi | casi di alta precisione |

---

## Perché ci riguarda

`unfold` calcola l'accorciamento con **una formula** (metodo della fibra
neutra, `unfold/rules/deduction.py`, `MAP.md` D33):

```
BD = 2·(r + s/2)·tan(β/2) − β·(r + K·s)
```

Questa formula, e la norma **DIN 6935** su cui è modellata, descrivono la
**piega in aria intorno ai 90°**:

- il raggio `r` è preso dalla cava (`r ≈ V/6`) — vero **solo in aria**: sul
  coniato il raggio lo impone il punzone e `r ≈ V/6` non vale;
- il fattore `K` (posizione della fibra neutra, tipicamente 0,3–0,4 in
  aria) è stimato dal solo rapporto `r/s` — tarato sull'acciaio, in aria;
- DIN 6935 copre il cold bending fino a ~12 mm.

Conseguenze per il non-90°:

- **Angoli aperti** (120–150° interni, cioè poca rotazione): siamo ancora
  in piena piega in aria, la formula dovrebbe reggere come regge a 90°.
- **Angoli chiusi** (< 90° interni, molta rotazione): il ritorno elastico
  cresce e diventa meno prevedibile; con le cave grandi (matrici a 80°
  come le EV/H W50–W60 di officina 1) non ci arrivi in aria e passi a
  coniare col punzone a punta — **regime diverso, formula meno
  affidabile per costruzione**. È l'alea di cui si parlava: non sappiamo
  di quanto sballa finché non misuriamo qualche pezzo.

Il campo `Biegeverkuerzung` nei `.bnc` di TruBend non è una misura fisica
pura: è DIN 6935 **più** le correzioni del database materiale Trumpf, che
sull'angolo si muovono in modi che non vediamo.

---

## Chi ci ha sbattuto la testa

- **Steve Benson** (ASMA LLC; *Precision Sheet Metal Technology Council*
  della FMA, USA). Scrive la rubrica *Bending Basics* su *The FABRICATOR*
  ogni mese dal 2015, e collabora alla rivista da oltre 30 anni. È la
  fonte della "regola del 20%" (raggio interno in aria = % dell'apertura
  cava) e di gran parte della pratica americana sul calcolo di
  `bend deduction` / `bend allowance` / K-factor / Y-factor.
- **Scuola tedesca (Umformtechnik).** La norma **DIN 6935**
  ("Kaltbiegen von Flacherzeugnissen aus Stahl") lega K-factor, raggio e
  spessore per il calcolo delle abwicklungen; è la base della formula di
  `unfold`. Trumpf ci ha costruito sopra il database materiale della
  TruBend. Manuali di riferimento: Kurt Lange, *Umformtechnik*.
- **Scuola giapponese (Amada e costruttori di stampi).** Molta della
  pratica fine su V-bending, selezione cava, ritorno elastico e le tre
  modalità viene dai die maker giapponesi (es. guide tecniche Conic,
  Ai-Link). Loro dividono in パーシャルベンディング / ボトミング /
  コイニング con tolleranze ±0,75° / ±0,5° / ±0,25°.

---

## Glossario nelle quattro lingue

| Italiano | Inglese | Deutsch | 日本語 |
|---|---|---|---|
| piega in aria | air bending / partial bending | Freibiegen / Luftbiegen | エアベンディング / パーシャルベンディング |
| piega sul fondo | bottoming / bottom bending | auf Block biegen / im Gesenk | ボトミング（底突き・底押し） |
| coniatura | coining | Prägen / Prägebiegen | コイニング |
| piegatura alla pressa (famiglia) | press brake bending | Gesenkbiegen / Abkanten | プレスブレーキ曲げ |
| piega a V | V-bending | V-Biegen | Ｖ曲げ |
| matrice (cava a V) | die (V-die) | Matrize / Gesenk | ダイ（Ｖ溝） |
| punzone | punch | Stempel / Oberwerkzeug / "Schwert" | パンチ |
| apertura cava | die opening / V-opening | Matrizenöffnung / V-Weite | Ｖ幅 |
| angolo di piega | bend angle | Biegewinkel | 曲げ角度 |
| raggio interno di piega | inside bend radius | Innenbiegeradius | 内側Ｒ (ir) |
| raggio minimo di piega | minimum bend radius (r ≈ 1…3·s) | Mindestbiegeradius | 最小曲げ半径 |
| ritorno elastico | springback | Rückfederung | スプリングバック |
| fibra neutra | neutral axis / neutral fiber | neutrale Faser | 中立軸 |
| fattore K | K-factor | k-Faktor | Ｋ係数 |
| accorciamento di piega | bend deduction | Biegeverkürzung | 減少量 / 伸び代 |
| sviluppo (lunghezza distesa) | flat pattern / developed length | Abwicklung / gestreckte Länge | 展開長 |
| bend allowance | bend allowance | Biegezugabe / Ausrundung | 曲げ代 |

---

## Fonti

- Steve Benson, *Bending Basics* / *The FABRICATOR* (FMA):
  - [Transitioning from bottom bending to air forming](https://www.thefabricator.com/thefabricator/blog/bending/transitioning-from-bottom-bending-to-air-forming-on-the-press-brake)
  - [Bending basics: dissecting bend deductions and die openings](https://www.thefabricator.com/thefabricator/article/bending/bending-basics-dissecting-bend-deductions-and-die-openings)
  - [How to calculate the air-formed radius of different bend angles](https://www.thefabricator.com/thefabricator/article/bending/how-to-calculate-the-air-formed-radius-of-different-bend-angles)
  - [Steve Benson — profilo autore](https://www.thefabricator.com/author/steve-benson)
- Confronto delle tre modalità (EN):
  - [Komaspec — Air bending vs bottom bending](https://www.komaspec.com/about-us/blog/the-difference-between-air-bending-and-bottom-bending-for-sheet-metal/)
  - [KAVDO — Air bending vs bottoming vs coining](https://www.kavdo.com/air-bending-vs-bottoming-vs-coining/)
- Scuola tedesca:
  - [Gesenkbiegen — Wikipedia (DE)](https://de.wikipedia.org/wiki/Gesenkbiegen)
  - [4ming — Freies Biegen (Umformtechnik-Handbuch)](https://4ming.de/de/forming-handbuch/freies-biegen/)
  - [industryarena.com — Biegenorm DIN 6935 (forum tecnico)](https://de.industryarena.com/forum/biegen-biegenorm-din-6935--16253.html)
- Scuola giapponese:
  - [Conic — Ｖ曲げ加工の種類](https://www.conic.co.jp/tech/brake/1_2.html)
  - [Ai-Link — 3種類の曲げ](https://www.ai-link.ne.jp/free/technical/ai_bending/Ai-bend.files/abc_01/3ways.htm)
