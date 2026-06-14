# SchemaGen — offline rozpoznawanie schematow (RTX 2080)

Pivot z EPLAN API na lokalny pipeline: YOLO + OCR + OpenCV → SchemaModel JSON → walidacja → SVG.

Archiwum ery EPLAN: `archive/eplan-era-2026-06.zip`

## Szybki start

```powershell
.\scripts\dev.ps1
```

## Moduly MVP

| Modul | Polecenie |
|-------|-----------|
| LABEL | `python -m labeler.app` → :8765 |
| TRAIN | `python -m train.train_symbols` |
| READ | `python -m backend.cli recognize input.pdf -o out.json` |
| CHECK | `python -m backend.cli validate out.json` |
| BUILD | `python -m backend.cli generate -o out.svg` |

## Agenci

- **Cursor** — szkielet, prompty, review, akceptacja
- **Claude Cowork** — implementacja z `sync/prompts/`
- **Uzytkownik** — oznaczanie danych, kierunek

Dokumentacja: `docs/ROADMAP.md`, `docs/claude-cowork-instructions.md`
