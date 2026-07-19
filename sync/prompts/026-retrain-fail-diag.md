# Zadanie 026: symbols_tiled_v1-3 — mAP50 = 0.0001, diagnoza eksportu

**Status:** BLOKUJĄCE (przed jakimkolwiek kolejnym treningiem)
**Model:** Opus 4.8 (diagnoza), potem Sonnet 5 na fix eksportu
**Nie uruchamiać ponownie treningu przed zamknięciem kroku 1.** 150 epok = godziny; przyczyna jest w danych, nie w hiperparametrach.

## Fakty

```
map50: 0.00010287     # praktycznie zero
epochs: 150, batch: 4, imgsz: 1536, model: yolov8n.pt
preview_batch --conf 0.18: 30 stron → 2 detekcje (obie `zlaczka`)
Ultralytics 8.4.67 ... CPU (Intel Core i7-9700KF)
```

mAP 0.0001 po 150 epokach to **nie** niedouczenie i nie zła klasa modelu. To etykiety, które nie pokrywają się z obrazem. Sieć nie ma czego dopasować.

## Hipoteza główna — rozjazd skali GT ↔ obraz

Poszlaki, wszystkie zbieżne:

1. `tiled_export` przełączony w 023 na `load_all_training_records()` (GT v2) — **zmiana świeża, nigdy nie zwalidowana wizualnie**. Poprzedni v1-2 uczył się poprawnie na starej ścieżce.
2. loop 032 it5: `zlaczka GT x=5558 vs RT x=442, IoU=0` — rozjazd współrzędnych ~12,6× był już obserwowany i **nigdy nie wyjaśniony**, tylko obejściem („brak bezpiecznej zmiany").
3. W repo istnieją `scripts/reingest_highdpi.py` i `scripts/scale_annotations.py` — historia zmian DPI. GT v2 mógł zostać zapisany w innej rozdzielczości niż PNG w `data/raw/`.
4. Filip niezależnie zgłasza: **labeler pokazuje złe bboxy**. To prawdopodobnie ten sam błąd widziany z drugiej strony — patrz 025.

**Jedna przyczyna, dwa objawy.** Jeśli GT ma współrzędne w innej skali niż obraz: labeler rysuje ramki obok symboli, a YOLO trenuje na szumie.

## Krok 1 — weryfikacja wizualna (minuty, nie godziny)

```powershell
python scripts/visualize_yolo_dataset.py --data data/labeled_tiled/data.yaml --limit 20
```

Patrzeć na kafelki: czy ramki leżą **na** symbolach.

- Ramki obok / poza kadrem / w rogu → **eksport zepsuty**, przejdź do kroku 2
- Ramki poprawne → hipoteza obalona, sprawdzać `data.yaml` (mapowanie klas, ścieżki train/val), a nie skalę

Dodatkowo: `python scripts/class_report.py --min-count 5` i porównać liczności klas z tym, co realnie wylądowało w `data/labeled_tiled/labels/`. Rozjazd liczb = filtr `--min-visible 0.35` odrzucił prawie wszystko (drugi możliwy sprawca: przy złej skali bboxy wypadają poza kafelek i `min-visible` je wycina — dałoby dokładnie taki obraz: prawie puste labelki, mAP≈0).

## Krok 2 — źródło rozjazdu

Porównać dla p028 (i p034 z it5):

| Wielkość | Skąd |
|---|---|
| Rozmiar obrazu w GT v2 | `gt/*.json` pole page width/height |
| Faktyczny rozmiar PNG | `data/raw/*.png` |
| bbox w GT v2 | `gt/*.json` |
| bbox po `load_all_training_records()` | wyjście funkcji |
| bbox znormalizowany w `labels/*.txt` | `data/labeled_tiled/` |

Rozjazd pokaże się na jednym z tych przejść. Nie zgadywać — wypisać wszystkie pięć.

Wynik → `sync/analysis/026-tiled-export-diag.md`.

## Krok 3 — fix + test regresji

Po naprawie: test w `backend/tests/` (lub `train/tests/`), który dla znanej strony sprawdza, że bbox z GT v2 po eksporcie ląduje w tym samym miejscu obrazu co przed. Bez tego testu ten błąd wróci przy następnej zmianie źródła GT.

## [RYZYKO] Trening szedł na CPU

Log eksportu: `torch-2.5.1+cu121 CPU (Intel Core i7-9700KF)`. Jeśli **trening** też szedł na CPU, to przy 150 epokach × 1536 px `batch 4` mogło zostać ukończone byle jak lub torch nie widzi RTX 2080. Sprawdzić:

```powershell
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

To nie tłumaczy mAP≈0 (na CPU model też by się nauczył, tylko wolniej), ale trzeba to zamknąć przed kolejnym cyklem — inaczej każda iteracja kosztuje wielokrotnie za dużo.

## Stan modelu produkcyjnego

`symbols_tiled_v1-3` **nie wchodzi** do `data/models/registry.json`. Aktywny pozostaje **`symbols_tiled_v1-2`, conf 0.18**. Nie podmieniać do czasu mAP porównywalnego z v1-2.
