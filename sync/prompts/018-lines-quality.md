# Zadanie 018: Jakość linii (LineTracer + paleta)

**Status:** DONE — wdrożone 2026-07-04 (Claude)  
**pytest:** 226 passed (PC Filip)

## Kontekst

Główna przyczyna **0 connections na p027** (H7 potwierdzone w pełnej skali):

- Szyna listwy = segmenty tuszu **67–76 px** między kółkami węzłów (przerwy **21–22 px**).
- Runtime Hough na stronie ~6617 px: `min_line_length=132` (>76!) i `max_line_gap=10` (<21!) → **szyna w 100% niewidoczna**.
- Sito **NIE** jest blokerem (H3/H6 odrzucone — szyna biegnie przez środki bboxów).

Objaw „czerwony/zielony losowy" to **kolory overlayu** (`preview_schema`: zielony=wire, czerwony=Connection), nie tusz (§7b). Na stronach Adamed nie ma czerwonego/zielonego tuszu.

**Strony referencyjne:** p027 (szyna listwy y≈2945), p040 (bez regresji connections), p035 (kontrola szumu).

**Następny prompt:** [`018-terminals-strategy.md`](018-terminals-strategy.md) — zależy od jakości linii z tego zadania.

## Reguły (nie zmieniać bez zgody Cursor)

- `GraphicLine` ≠ `Connection` — **nie ruszać** `net_builder.py`, kroków 4/5 w `graph_builder.py`
- Kontrakt `SchemaModel` (`backend/models/schema.py`) nietknięty
- Sito (`apply_sieve`) **zawsze włączone** — bez flagi off; **nie zmieniać** `EDGE_OVERLAP_MIN` ani logiki `_is_box_edge`
- Bez cloud API w `backend/recognize/`
- `derive_mostek_terminals` — nietknięte

## 1. Hough pod kółka węzłów

Plik: [`backend/recognize/line_tracer.py`](../../backend/recognize/line_tracer.py)

Przerwy 21–22 px to systematyczna cecha notacji (kółko węzła), nie szum.

**Wariant C eksperymentu** (findings §1): `min_len≈66`, `gap≈25` na skali pełnej strony → szyna 1535 px, 171 segmentów (bez eksplozji szumu vs 336 przy min_len=40).

Wybierz **jedną** strategię (lub hybrydę z configiem):

| Opcja | Opis |
|-------|------|
| **A — dwuprzebiegowy Hough** | Przebieg 1: obecne progi (`hough_min_len_frac` 0.02). Przebieg 2: niższe progi tylko dla linii osiowych — start kalibracji `min_len≈0.01*max(W,H)`, `gap≈0.004*max(W,H)`; scal wyniki + dedup |
| **B — morfologia CLOSE** | `cv2.morphologyEx(CLOSE)` kernelem 1×25 / 25×1 przed Houghem na masce osiowej (poziomej/pionowej) |

Nowe klucze w [`config/runtime.yaml`](../../config/runtime.yaml) (np. `hough_bus_min_len_frac`, `hough_bus_gap_frac` lub `hough_second_pass: true`) + loadery w `backend/runtime_config.py`.

Zachowaj jawne override int w `LineTracer` (testy).

## 2. `_merge_collinear` — skalowany `gap_tol`

Plik: [`backend/recognize/line_tracer.py`](../../backend/recognize/line_tracer.py) (~linia 96)

Dziś: stała `gap_tol=12` px — za mało na przerwy 21–22 px między segmentami szyny.

```python
gap_tol = max(12.0, hough_gap * 2.5)  # hough_gap = efektywny max_line_gap z auto_line_params
```

Wywołanie `_merge_collinear(segments, gap_tol=...)` — przekaż gap z `_params()` / rozmiaru strony.

## 3. Paleta kolorów + `match_color`

Pliki: [`config/semantic-colors.yaml`](../../config/semantic-colors.yaml), [`backend/colors/palette.py`](../../backend/colors/palette.py)

Realny tusz niebieski **#134088 / #105090** nie łapie się do `motor_device` (#0066CC) → linie z pustą `semantic_group`.

- Kalibracja niebieskiego (rozszerz `motor_device` stroke lub nowa grupa wire z tymi hexami)
- **Rozdziel** stroke `enclosure` vs `pe_wire` (dziś oba `#00AA44` — remis po kolejności dict)
- Tie-break `match_color` po roli/stylu, nie kolejności w dict
- Hint dla grup wielorolowych: `enclosure` → rola `frame`, nie domyślne `wire`
- **NIE dodawać** grupy czerwieni — brak takiego tuszu na stronach

## 4. Overlay i diagnostyka

| Plik | Zadanie |
|------|---------|
| [`scripts/preview_lines.py`](../../scripts/preview_lines.py) | Usuń martwy klucz `"bus"` w `ROLE_COLORS_BGR`; rozjaśnij kolory wire vs frame (dziś dwie prawie identyczne zielenie) |
| [`scripts/diag_lines.py`](../../scripts/diag_lines.py) | **NOWY** read-only: histogram `detected_color` per rola / `semantic_group` na stronę; CLI `--page` |

## 5. Opcjonalnie: `arrow_supplement`

Plik: [`backend/recognize/arrow_supplement.py`](../../backend/recognize/arrow_supplement.py)

~3 linie: `need` — supplement gdy brak detekcji klasy z conf ≥ progu (np. 0.5), nie `c not in have` (jedna słaba detekcja nie wyłącza całej klasy). Komentarz przy `roi_top_frac`: odcina **dolne** `(1-frac)*H` strony (ROI = górne 93%).

## Testy

- Rozszerz [`backend/tests/test_line_tracer.py`](../../backend/tests/test_line_tracer.py): skalowany `gap_tol` w merge; ewentualnie drugi przebieg Hough (mock/small image)
- Rozszerz testy palety jeśli zmienia się tie-break
- **Wszystkie istniejące testy** `backend/tests`, `labeler/tests`, `train/tests` — bez regresji

## Kryteria akceptacji

| Kryterium | Sprawdzenie |
|-----------|-------------|
| Szyna p027 | Pozioma linia y≈2945 jako `wire` ciągła ≥90% szerokości rzędu 58 złączek — `preview_lines.py` |
| p040 bez regresji | `python scripts/eval_val_pages.py --page p040` — connections jak przed zmianą |
| Kontrola szumu p035 | Liczba segmentów nie rośnie >2× |
| Niebieski tusz | Linie `#134088`/`#105090` mają niepustą `semantic_group` |
| Overlay | wire vs frame wizualnie odróżnialne w `preview_lines` |
| pytest | ≥213 passed |

## Smoke (Filip / główny PC)

```powershell
python scripts/preview_lines.py --page data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p027.png
python scripts/diag_lines.py --page p027
python scripts/eval_val_pages.py --page p040
python -m pytest backend/tests labeler/tests train/tests -q
```

## Po ukończeniu

`sync/commit-message.txt` = `[Claude] recognize: line tracer quality + palette (prompt 018-lines)`

## Poprawka (runda N)

*(Cursor)*
