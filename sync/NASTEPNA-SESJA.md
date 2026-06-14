# NASTĘPNA SESJA — start tutaj (2026-06-15)

> Handoff po sesji 2026-06-14 (wieczór). Szczegóły planu: [`sync/PLAN-TYMCZASOWY.md`](PLAN-TYMCZASOWY.md).

---

## Stan (2026-06-14 wieczór)

| Pole | Wartość |
|------|---------|
| **BUILD M0** | ✅ trening + ONNX + inferencja (CPU) u Filipa |
| **Model** | mAP50 ≈ 0.085, 1 klasa `element`, 9 stron train |
| **Venv GPU** | **`.venv311`** (Py 3.11, torch cu121) — nie `.venv` |
| **ONNX inferencja** | CPU OK; CUDA onnxruntime wymaga CUDA 12 DLL (opcjonalnie) |
| **Testy repo** | `pytest backend/tests labeler/tests train/tests` |

Lokalnie u Filipa (poza gitem): `best.pt`, `symbols_v1.onnx`, `registry.json` z `active=symbols_v1`.

---

## Pierwsze kroki

### Filip / Cursor
1. Przeczytaj `sync/PLAN-TYMCZASOWY.md`.
2. Decyzja: **008a atlas QET** u Claude vs więcej bboxów w labelerze.
3. Opcjonalnie: porównaj `.pt` vs ONNX na p013 (`ultralytics predict` vs `OnnxSymbolDetector`).

### Claude (ZW) — po „kolejne zadanie”
- **Priorytet:** [`sync/prompts/008-symbol-atlas-extract.md`](prompts/008-symbol-atlas-extract.md) (faza QET)
- Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md)
- Instrukcje: [`sync/filip-to-zw.md`](filip-to-zw.md) (wpis BUILD M0 DONE)

---

## Zamknięte dziś (Filip + Cursor)

- Diagnoza problemów Claude (006 przed treningiem, złe venv).
- Odbudowa `.venv311` + trening 30 epok + export ONNX.
- Smoke test: 5 detekcji na p013 @ conf=0.05.

---

## Mapa sync

| Plik | Rola |
|------|------|
| **`sync/PLAN-TYMCZASOWY.md`** | Plan i kontekst (tymczasowy) |
| **`sync/NASTEPNA-SESJA.md`** | Ten plik — start sesji |
| `sync/KOLEJNE-ZADANIE.md` | Aktywny prompt Claude |
| `sync/filip-to-zw.md` | Cursor → Claude |
| `sync/zw-to-filip.md` | Claude → Filip |
