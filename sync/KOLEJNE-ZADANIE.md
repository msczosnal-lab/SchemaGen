# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.  
> **Gotowy prompt do wklejenia:** [`sync/PROMPT-CLAUDE-005.md`](PROMPT-CLAUDE-005.md)

---

## Stan (2026-06-14 — BUILD M0)

| Prompt | Status |
|--------|--------|
| **005-train-symbols (BUILD M0)** | **PRIORYTET #1 — kod u Claude, trening u Filipa** |
| **008-symbol-atlas-extract (QET)** | OPEN — po 005 |
| **002-labeler-lines-colors** | OPEN |
| **009-bbox-symbol-id** | po 008a |

---

## Aktywne zadanie — PRIORYTET

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/005-train-symbols.md`](prompts/005-train-symbols.md) |
| **Deliverable (Claude ZW)** | `train/dataset_export.py`, `train/train_symbols.py`, testy, fix `labeler/export.py` |
| **Deliverable (Filip RTX 2080)** | `python -m train.dataset_export` + `train_symbols` → `best.pt` |
| **Typ** | Implementacja kodu (ZW) + trening GPU (Filip) |
| **Model** | Sonnet, effort **High** |

### Podział maszyn — OBOWIĄZKOWO

| PC | Co robisz |
|----|-----------|
| **ZW (Claude)** | Kod + pytest. **Bez pełnego treningu** — brak `data/schemagen.db` i PNG w gicie |
| **Filip (RTX 2080)** | Po pull committa Claude: export + train lokalnie |

### Kroki Claude (ZW)

1. `sync/filip-to-zw.md` + `005-train-symbols.md`
2. Implementacja wg promptu
3. `pytest backend/tests labeler/tests train/tests`
4. `sync/zw-to-filip.md` — **sekcja komend dla Filipa (PowerShell)**
5. `sync/commit-message.txt` = `[Claude] train: dataset export + YOLO train code M0 (prompt 005)`

### Kroki Filip (po commicie Claude)

```powershell
cd C:\Users\Filip\Desktop\Cursor\SchemaGen
pip install -e ".[gpu]"
.venv\Scripts\python.exe -m train.dataset_export
.venv\Scripts\python.exe -m train.train_symbols --epochs 30 --batch 8
```

### Czego NIE robic

- Pełny trening YOLO na PC ZW
- Atlas 008a w tej samej sesji (chyba że 005 done + Filip każe)
- Cloud API

---

## Dataset (tylko u Filipa — nie w gicie)

9 stron, ~394 bboxy w `data/schemagen.db`. Eksport batch = część 005.

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]`.
