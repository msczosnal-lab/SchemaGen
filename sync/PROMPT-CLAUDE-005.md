# Prompt startowy — Claude BUILD M0 (prompt 005)

> **Filip:** skopiuj cały blok poniżej do nowej sesji [claude.ai/code](https://claude.ai/code).  
> Na PC ZW: najpierw `Start-GitSync.cmd Claude` (pull).

---

```
SchemaGen — Builder. Nowa sesja. Aktywne zadanie: prompt 005 (BUILD M0).

Przeczytaj w kolejności:
1. sync/KOLEJNE-ZADANIE.md
2. sync/filip-to-zw.md (wpis BUILD M0 na górze)
3. docs/claude-cowork-instructions.md
4. sync/prompts/005-train-symbols.md

KRYTYCZNE — podział implementacja vs trening:
- PC ZW (Twój): TYLKO implementacja kodu + pytest (testy jednostkowe, mock/fixture).
- PC Filip (RTX 2080): pełny trening GPU — dataset w data/schemagen.db i PNG w data/raw/ NIE są w gicie (.gitignore). Na ZW ich nie ma — NIE uruchamiaj pełnego train_symbols z epokami.
- W zw-to-filip.md napisz instrukcję dla Filipa: jak odpalić export + train lokalnie (komendy PowerShell).

Implementuj:
- train/dataset_export.py (SQLite → YOLO train/val + PNG)
- train/train_symbols.py (ultralytics YOLOv8n, batch≤8)
- fix labeler/export.py — kopiowanie PNG przy eksporcie
- train/tests/test_dataset_export.py

Po kodzie:
1. pytest backend/tests labeler/tests train/tests
2. python -m backend.cli validate schema/fixtures/page1_expected.json
3. sync/zw-to-filip.md — pliki, testy, komendy dla Filipa (NIE wklejaj best.pt — Filip trenuje u siebie)
4. sync/commit-message.txt = [Claude] train: dataset export + YOLO train code M0 (prompt 005)

Zacznij od podsumowania planu, potem implementuj. Nie rób 008a w tej sesji.
```

Skrót (gdy sesja zna repo): `kolejne zadanie — tylko 005, bez treningu GPU na ZW`
