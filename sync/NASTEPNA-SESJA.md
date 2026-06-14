# NASTĘPNA SESJA — start tutaj (2026-06-15)

> Etap 1: **detekcja elementów** + labeler bbox-first. Handoff: [`sync/KOLEJNE-ZADANIE.md`](KOLEJNE-ZADANIE.md).

---

## Stan

| Pole | Wartość |
|------|---------|
| **BUILD M0** | ✅ trening + ONNX u Filipa (mAP50 ≈ 0.085, 9 stron) |
| **008a QET** | ✅ kod; kurator TAK/NIE **wstrzymany** |
| **Aktywny prompt Claude** | **010** — bbox-first + `symbol-palette.yaml` |
| **Venv GPU** | `.venv311` (Py 3.11, torch cu121) |

---

## Filip

1. Oznaczaj bboxy na kolejnych schematach (`data/raw/`, `sync/sources/`).
2. Hasła krótkie (typ urządzenia); po 010 — wybór z palety po narysowaniu bboxa.
3. Re-train YOLO gdy baza urośnie (500+ bboxów / 20+ stron).

## Claude (ZW)

- Prompt: [`sync/prompts/010-labeler-bbox-first-palette.md`](prompts/010-labeler-bbox-first-palette.md)
- Start: [`sync/PROMPT-CLAUDE-010.md`](PROMPT-CLAUDE-010.md) lub „kolejne zadanie”

---

## Mapa sync

| Plik | Rola |
|------|------|
| `sync/KOLEJNE-ZADANIE.md` | Aktywny prompt |
| `sync/filip-to-zw.md` | Cursor → Claude |
| `sync/PROMPT-CLAUDE-010.md` | Wklejka startowa sesji |
