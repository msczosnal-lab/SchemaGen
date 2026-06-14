# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

---

## Stan (2026-06-14 wieczór)

| Prompt | Status |
|--------|--------|
| **005-train-symbols** | ✅ kod w repo; trening + ONNX u Filipa DONE (mAP50≈0.085) |
| **006-export-onnx** | ✅ zaimplementowany |
| **001-symbol-detector** | ✅ zaimplementowany; smoke OK (CPU) |
| **008-symbol-atlas-extract (QET)** | **PRIORYTET #1 — następny kod u Claude** |
| **002-labeler-lines-colors** | OPEN |
| **003-line-tracer / 004-graph-builder** | OPEN — po atlasie + danych |
| **009-bbox-symbol-id** | po 008a |

---

## Aktywne zadanie — PRIORYTET

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/008-symbol-atlas-extract.md`](prompts/008-symbol-atlas-extract.md) |
| **Deliverable (Claude ZW)** | `config/symbol-reference.yaml`, moduł ekstrakcji QET, cropy atlasu, testy |
| **Deliverable (Filip)** | Biblioteka QET lokalnie (`data/atlas/qet/`), review cropów |
| **Typ** | Implementacja + pytest (bez cloud API) |
| **Model** | Sonnet, effort **High** |

### Podział maszyn

| PC | Co robisz |
|----|-----------|
| **ZW (Claude)** | Kod 008a + pytest. **Bez** pełnego treningu YOLO. |
| **Filip (RTX 2080)** | QET lokalnie, ewent. re-train po nowych klasach/danych |

### Kroki Claude (ZW)

1. `sync/filip-to-zw.md` + `008-symbol-atlas-extract.md`
2. Implementacja fazy **008a tylko QET**
3. `pytest backend/tests labeler/tests`
4. `sync/zw-to-filip.md` — pliki + instrukcja dla Filipa (ścieżka QET, licencja GPL)
5. `sync/commit-message.txt` = `[Claude] atlas: QET extract → symbol-reference.yaml (prompt 008a)`

### Czego NIE robic

- Pełny trening YOLO na PC ZW
- 003/004 pipeline w tej samej sesji (chyba że Filip każe)
- Cloud API
- **006/001 ponownie** — DONE; nie dotykaj bez review Cursor

---

## BUILD M0 — zamknięty u Filipa

Trening GPU, export ONNX i smoke inferencji wykonane lokalnie. Szczegóły: [`sync/PLAN-TYMCZASOWY.md`](PLAN-TYMCZASOWY.md).

**Venv:** `.venv311` (Py 3.11 + torch cu121). **Nie** `.venv` (Py 3.14 CPU).

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
