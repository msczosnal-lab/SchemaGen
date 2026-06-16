# Raport: dlaczego YOLO słabo rozpoznaje elementy schematów

Data: 2026-06-16 · Zakres: pipeline treningu `train/` + `config/` + `labeler/export.py` + `data/models/`

## Wniosek nadrzędny

[BŁĄD] **Typ elementu, który oznaczasz, NIE trafia do klasy YOLO — ląduje w polu tekstowym `tag`.** Każdy bbox w systemie ma na sztywno `class_name = "element"`, a wybór z palety zapisuje się do `tag`. Trening czyta wyłącznie `class_name` → wszystkie ~1500 bboxów to dla sieci **jedna klasa**. Stąd masz mnóstwo etykiet, a model i tak uczy się tylko „czy tu jest jakiś element vs tło". Rozróżnienia strzałka/styk/złączka nie da się osiągnąć — informacja o typie istnieje w danych, ale pipeline jej nie używa.

To nie jest kwestia „za mało danych" — 1500 bboxów by wystarczyło. To błąd przepływu etykiety: **`tag` → nigdzie**, `class_name` → zawsze `element`.

Dowody twarde (z kodu):
- `labeler/static/app.js:7` → `const DEFAULT_CLASS = "element"`; linie 161, 956 → bbox tworzony zawsze z `class_name: "element"`.
- `labeler/static/app.js:593` → wybór z palety: `bboxes[idx].tag = trimmed;` (zapis do **`tag`**, nie do klasy). `isAssigned` (l. 280) sprawdza `tag`, nie `class_name`.
- `config/symbol-classes.yaml` → `classes: [element]` (1 klasa); `config/element-catalog.yaml` → 68/68 wpisów `yolo_class: element`.
- `labeler/export.py::yolo_label_lines` (l. 89) → `cls_id = cmap.get(b.class_name, 0)`; mapa ma tylko `element` → **każdy** bbox dostaje `0` (a nawet gdyby `class_name` był typem, `.get(..., 0)` i tak zwróci 0 dla typu spoza mapy).
- Archiwum legacy (`data/archive/.../annotations/*.label.json`): 406 bboxów, **wszystkie** `class_name="element"`, typ wpisany w `tag` jako długi opis (np. „Symbol rozłącznika bezpiecznikowego"). Potwierdza wzorzec.
- `data/models/symbols_v1_train_summary.json` → **mAP50 = 0.085**; `symbols_v2` → **mAP50 = 0.106** (30 epok).

mAP50 ≈ 0.09–0.11 nawet dla **jednej** klasy to wynik bardzo zły (próg użyteczności orientacyjnie >0.5). Czyli nakładają się dwa problemy: zła definicja zadania (typ w `tag`, nie w klasie) **oraz** zły trening (rozmiar/augmentacja).

> Uwaga o liczbie bboxów: w repo widać tylko **406** zarchiwizowanych (`data/archive/wrt01-legacy-2026-06-15/`). Żywe **~1500** siedzi w `data/schemagen.db`, który jest w `.gitignore` (`data/schemagen.db`) i **nie jest synchronizowany** do tego repo — dlatego nie policzę ich rozkładu po typach stąd. Wniosek architektoniczny jest jednak niezależny od liczby: dopóki typ jest w `tag`, każda liczba bboxów = 1 klasa.

---

## Przyczyny — ranking wg wpływu

### 1. [BŁĄD] Jedna klasa zamiast wielu — przyczyna #1
Opisana wyżej. Skutek: nie ma czego oceniać per-typ; model uczy się tylko „obiekt vs tło".
Twoje oczekiwanie (strzałka potencjału / styki / złączka jako osobne klasy) wymaga, żeby `class_name` bboxa mapował się na **osobny `class_id`**, a `data.yaml::names` miał te klasy.

### 2. [BŁĄD] Dramatycznie za mały zbiór obrazów
- Trening v1/v2: **~394 bboxy na 9 stronach** (`sync/filip-to-zw.md`, BUILD M0).
- YOLO liczy się w **obrazach**, nie bboxach. 9 obrazów to dla detektora margines szumu — i to przy 1-klasie. Przy podziale na ~kilkanaście klas część typów dostanie 1–3 przykłady → nie nauczą się wcale.
- Dodatkowo WRT01 zresetowano do zera (`2026-06-15 Reset WRT01`), więc aktualny GT jest jeszcze mniejszy.
Orientacyjnie: minimum sensowne to ~50–100 obrazów i ≥150–300 instancji **na klasę** dla klas priorytetowych.

### 3. [RYZYKO] Rozdzielczość treningu za mała dla gęstych, drobnych symboli
- `data/runs/*_train_summary.json` → realny trening szedł na **imgsz 640**.
- Strona p015 = **152 bboxy/stronę**; strzałka potencjału / styk to kilka–kilkanaście px na skanie 400 DPI. Przy 640 px symbole są praktycznie nie do odróżnienia.
- [BŁĄD] Niespójność źródła prawdy: `train/configs/symbols.yaml` mówi `imgsz: 640, batch: 8`, a `config/runtime.yaml` mówi `imgsz: 1280, batch: 4`, i `train_symbols.py` bierze wartość z `runtime_config` — łatwo wytrenować na innym rozmiarze niż się myśli. Summary pokazuje 640 → trenowano wg starego configu.

### 4. [RYZYKO] Domyślna augmentacja ultralytics psuje schematy
Trening nie wyłącza augmentacji → działają domyślne: `fliplr=0.5`, `mosaic=1.0`, `hsv_*`, `scale`, `translate`, ewentualnie obroty.
- **Odbicia/obroty niszczą semantykę kierunkową**: w katalogu masz `strzałka_potencjału_wejściowa` vs `wyjściowa`, styki NO/NC, „coming/leaving arrow". Lustro/obrót zamienia jedno w drugie → uczysz sieć sprzecznych etykiet.
- **HSV/jaskrawość**: schemat to grafika kreskowa (prawie B/W) — augmentacja koloru nic nie wnosi, a mosaic dodatkowo skleja drobne symbole z sąsiadami.

### 5. [RYZYKO] Podział train/val niewiarygodny przy 9 stronach
`dataset_export.split_train_val`: przy `n<=1` ta sama strona idzie do train i val (przeciek = zawyżone metryki). Przy 9 stronach val = ~2 strony → mAP skacze losowo i nie jest reprezentatywne. Stąd „v2 lepsze od v1" (0.106 vs 0.085) może być szumem podziału, nie postępem.

### 6. [RYZYKO] Próg `conf` i ocena
`yolo_conf_threshold: 0.15` w runtime — bardzo nisko (dużo fałszywych trafień). To maskuje słaby model przy demie i utrudnia ocenę. To skutek, nie przyczyna — ale zaciemnia diagnozę.

---

## Co zrobić — plan naprawczy (kolejność = priorytet)

### Krok 1 — Włącz wieloklasowość (bez tego reszta nie ma sensu)
Zacznij od **3 klas priorytetowych**, których masz najwięcej bboxów: `strzałka_potencjału` (na start scal wejściową+wyjściową LUB trzymaj osobno — patrz niżej), `styki`, `złączka`. Resztę można na razie zmapować do `inny`/pominąć.

1. `config/symbol-classes.yaml` → realna lista klas, np.:
   ```yaml
   classes:
     - strzalka_potencjalu
     - styki
     - zlaczka
   ```
2. `config/element-catalog.yaml` → ustaw `yolo_class` per wpis (mapowanie wariantów na klasę docelową). Wyjątki wg Twojego założenia: `obiekt` (ramka) i `listwa_złączek` (kontener zacisków) — **trzymaj poza tym etapem**, dodasz później jako osobne klasy „kontenerowe".
3. Zweryfikuj, że `data.yaml::names` po `dataset_export` ma >1 klasy i że pliki `labels/*.txt` mają różne `class_id` (nie same zera).

[RYZYKO] Kierunkowość: jeśli wejściowa/wyjściowa różnią się tylko zwrotem strzałki — albo (a) jedna klasa `strzalka_potencjalu` + kierunek licz geometrią po detekcji, albo (b) dwie klasy, ale **wtedy `fliplr=0, flipud=0`** obowiązkowo.

### Krok 2 — Popraw konfigurację treningu
W `train/train_symbols.py::yolo.train(...)` dołóż jawnie (i ujednolić z `runtime.yaml`):
```python
yolo.train(
    data=yaml_path, epochs=150, imgsz=1280, batch=4, device=0,
    patience=40, cos_lr=True,
    fliplr=0.0, flipud=0.0, degrees=0.0, shear=0.0, perspective=0.0,
    hsv_h=0.0, hsv_s=0.0, hsv_v=0.2,
    mosaic=0.0, mixup=0.0, scale=0.2, translate=0.05,
    rect=True,
)
```
Uzasadnienie: schematy są drobne i kierunkowe → wyłączamy odbicia/obroty/kolor/mosaic; imgsz 1280 (lub więcej, jeśli VRAM pozwoli przy batch 2) dla drobnych symboli; więcej epok bo mały zbiór; `patience` większy. [BŁĄD do usunięcia] rozbieżność `symbols.yaml` 640 vs `runtime.yaml` 1280 — zostaw jedno źródło prawdy.

### Krok 3 — Więcej danych (równolegle, najważniejsze długoterminowo)
- Doznacz strony pod **różnorodność i liczność klas priorytetowych** (cel: ≥150–300 instancji/klasę, ≥50 stron).
- Rozważ **tiling/SAHI** przy inferencji i treningu: tnij stronę na kafelki ~1024 px z zakładką — drobne symbole stają się duże względem kafelka. To zwykle największy skok mAP na gęstych schematach.

### Krok 4 — Wiarygodna ocena
- Stały, ręcznie wybrany `val` (np. 2–3 całe strony **nie** występujące w train), nie auto-split z przeciekiem.
- Patrz na **mAP50 per-klasa + confusion matrix**, nie tylko globalne mAP. Próg `conf` do oceny ustaw ~0.25, nie 0.15.

---

## Szybki test hipotezy (zanim doznaczysz cokolwiek)
Na obecnych ~9 stronach: przemapuj katalog na 3 klasy, wyłącz szkodliwą augmentację, imgsz 1280, 150 epok. Jeśli mAP50 per-klasa dla strzałek/styków wyraźnie przebije obecne 0.10 — potwierdza, że #1 (jedna klasa) i #3/#4 (imgsz/augmentacja) były głównymi hamulcami, a dalej skaluje się już tylko danymi (#2).

## Odpowiedź wprost na Twoje pytanie
„Bboxów jest dużo, więc czemu słabo?" — bo **liczba bboxów nie przekłada się na liczbę klas**: pipeline kasuje typ każdego bboxa do `element`. Masz dużo etykiet, ale wszystkie tej samej, jednej klasy, na 9 obrazach, w za małej rozdzielczości, z augmentacją łamiącą kierunkowość. Najpierw napraw definicję klas (Krok 1) — to odblokowuje cały sens treningu.
