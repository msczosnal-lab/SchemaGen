# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-06-28)

| Prompt | Status |
|--------|--------|
| **crop-review GT (T/R/C)** | ✅ DONE (Cursor) — import draft, batch terminale, review bbox/conn |
| **010-labeler-bbox-first-palette** | ✅ DONE |
| **symbols_atomic_v2** | ✅ mAP50≈0.92 |
| **004-graph-builder** | ✅ DONE — p040 draft: 14 conn |

**Strona referencyjna:** `22_A_153_PL_Adamed_AGV_SA2_20250706_p040` (draft runtime w SQLite)

---

## Aktywne zadanie — Filip

| Pole | Wartosc |
|------|---------|
| **Review crop** | labeler tryby **T** (terminale), **R** (bbox), **C** (połączenia) na p040 |
| **Akceptacja** | ✓ OK / ✕ usuń → Zapisz stronę |

```powershell
python -m labeler.app   # Ctrl+F5
python scripts/diff_gt_runtime.py --page p040
python scripts/preview_schema.py --page p040
```

---

## Aktywne zadanie — Claude

| Pole | Wartosc |
|------|---------|
| **Backlog** | tolerancja wire→bbox, progi Hough, poprawki po review Filipa |

---

## Aktywne zadanie — Cursor

| Pole | Wartosc |
|------|---------|
| **DONE** | `preview_schema.py`, `diff_gt_runtime.py`, crop-review labeler |

---

## Stan archiwum (2026-06-27)

| Prompt | Status |
|--------|--------|
| **010-labeler-bbox-first-palette** | ✅ DONE |
| **005–006, 001 recognize, train_cycle** | ✅ DONE |
| **symbols_atomic_v2** | ✅ mAP50≈0.92, aktywny w registry |
| **002-ocr-engine** | ✅ DONE — smoke OK (~75%) |
| **002-labeler-lines-colors** | ✅ DONE (Claude) |
| **003-line-tracer** | ✅ DONE — progi Hough: backlog |
| **004-graph-builder** | ✅ DONE (Claude) — smoke na **p040** |
| **008a QET atlas** | ⛔ NIE UŻYWAĆ |

**Strona referencyjna GT linii + walidacja e2e:**  
`22_A_153_PL_Adamed_AGV_SA2_20250706_p040` (Filip, 2026-06-27)

---

## Aktywne zadanie — Claude

| Pole | Wartosc |
|------|---------|
| **Backlog** | tolerancja wire→bbox, progi Hough, poprawki po review Filipa |

**Nie ruszaj:** atlas QET, trening GPU.

---

## Aktywne zadanie — Filip

| Pole | Wartosc |
|------|---------|
| **Review crop** | tryby T/R/C na p040 |

---

## Aktywne zadanie — Cursor

| Pole | Wartosc |
|------|---------|
| **DONE** | crop-review + import draft + preview/diff |

---

## (archiwum) Poprzednie zadania

## Aktywne zadanie — Claude

| Pole | Wartosc |
|------|---------|
| **Cel** | Poprawki po smoke **p040** (gdy Filip/Cursor zgłoszą `## Poprawka`) |
| **Backlog** | tolerancja końców wire→bbox, progi Hough, terminale w Connection |
| **Start** | czekaj na wynik smoke / diff GT vs runtime |

**Nie ruszaj:** atlas QET, trening GPU, labeler (GT linii DONE na p040).

---

## Aktywne zadanie — Filip

| Pole | Wartosc |
|------|---------|
| **GT linii** | ✅ DONE — **p040** |
| **Smoke pipeline** | `recognize_file` na p040 → ocena connections od–do |
| **Review autolabel** | bbox p051+ (incognito) |
| **train_cycle** | dopiero po poprawionym GT bbox |

```powershell
python -c "from backend.recognize.pipeline import recognize_file; m=recognize_file('data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p040.png'); print(len(m.components),'sym', len(m.graphic_lines),'linii', len(m.connections),'conn')"
```

### Cykl YOLO (gdy GT bbox poprawione)

```powershell
python scripts/train_cycle.py
```

---

## Aktywne zadanie — Cursor

| Pole | Wartosc |
|------|---------|
| **Cel** | `scripts/preview_schema.py` — overlay bbox + linie + connections na **p040** |
| **Cel** | diff GT labeler vs `recognize_file` (graphic_lines, connections) |

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
