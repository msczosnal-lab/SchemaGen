# Komendy: publikacja zmian + wizualizacja bboxów + ścieżka do treningu

> Stan: na PC ZW (daemon OFF) gotowe poprawki w drzewie roboczym, **niezacommitowane**
> (bash w Cowork nie może zdjąć `.git/index.lock` ani commitować — robi to Windows).

## A. PC ZW — opublikuj zmiany (raz)

```powershell
cd C:\Users\ZW\Desktop\prywatne\automatyzacja\KodKlon\SchemaGen

# 1. Zdejmij zalegający lock (jeśli jest)
if (Test-Path .git\index.lock) { Remove-Item .git\index.lock -Force }

# 2. Commit + push (GitSync sam doda/commit/push)
.\Start-GitSync.cmd Claude
```

Co wejdzie: `.gitattributes` (EOL=LF — koniec „rozsypania"), fix importu w
`scripts/preview_detection.py`, idempotencja `scripts/scale_annotations.py`,
nowy `scripts/visualize_bboxes.py`, + normalizacja EOL kilku plików.

## B. PC Filip — pobranie (daemon nasłuchuje, zwykle sam; ręcznie:)

```powershell
cd <repo>\SchemaGen
git pull
```

## C. PC Filip — wizualizacja bboxów GT w aktualnych koordynatach

```powershell
# Render stron z nałożonymi bboxami z bazy (zielone OK, CZERWONE = poza obrazem)
python scripts/visualize_bboxes.py

# Pojedyncza strona:
python scripts/visualize_bboxes.py --page SchematWRT01_p013
```

Wynik w `data/output/bbox_overlay/`:
- `index.html` — galeria + tabele tagów per strona (otwórz w przeglądarce)
- `<page>.png` — strona z bboxami
- `report.json` — liczba bbox/overflow + **rozkład tagów** (wejście do klas SSN)

Weryfikacja: jeśli w `index.html` są czerwone ramki / `overflow > 0` → skalowanie
danej strony jest złe.

## D. Skalowanie — TYLKO jeśli wizualizacja pokaże overflow

Cursor już przeskalował bazę. Nie uruchamiaj ślepo `--apply`. Najpierw dry-run:

```powershell
python scripts/scale_annotations.py                 # dry-run (nic nie zapisuje)
python scripts/scale_annotations.py --apply         # zapis dopiero gdy dry-run OK
# konkretny współczynnik dla jednego PDF (np. 200->400 DPI):
python scripts/scale_annotations.py --apply --factor 2.0
```

Po fixie idempotencji ponowny `--apply` nie przeskaluje już raz poprawionych stron
(marker `data/.annotation_dpi`). Jeśli pojedyncza strona dalej zła — podaj jej numer.

## E. [BŁĄD] Zanim trenujesz SSN — przeczytaj

Trening teraz **będzie jednoklasowy** (`element`). Typ, który oznaczasz, siedzi w
polu `tag`, a nie w klasie YOLO — `config/symbol-classes.yaml` ma tylko `element`,
a `labeler/export.py` mapuje każdy bbox na `class_id=0`. 1500 bboxów = 1500 sztuk
jednej klasy. Strzałek/styków/złączek model nie rozróżni, choćby dane były idealne.

Dlatego kolejność jest:
1. Wizualizacja (C) → potwierdź geometrię.
2. `report.json` → rozkład tagów → ustalmy 3 klasy priorytetowe
   (strzałka potencjału / styki / złączka) + `inny`.
3. Wpięcie `tag` → `class_name` w eksporcie + realne klasy w `symbol-classes.yaml`.
4. Dopiero wtedy `dataset_export` + trening (imgsz 1280, augmentacja bez odbić —
   patrz `sync/RAPORT-YOLO-trening.md`).

Pełna diagnoza: `sync/RAPORT-YOLO-trening.md`.
