# SchemaGen — roadmap offline (RTX 2080)

## Fazy

| Faza | Cel | Status |
|------|-----|--------|
| 0 | Szkielet, archiwum EPLAN, labeler stub | ✅ |
| 1 | Labeler canvas (Cowork) + pierwsze dane uzytkownika | OPEN |
| 2 | Trening YOLO + recognize ONNX | OPEN |
| 3 | Walidacja + diff ground truth | ✅ struktura |
| 4 | Generowanie SVG z blokow | ✅ MVP 3 bloki |
| 5 | Next.js localhost | placeholder |

## Moduly (MVP = finalne uproszczone)

1. **LABEL** — labeler → LabelRecord → YOLO + SchemaModel GT
2. **TRAIN** — YOLOv8n → ONNX → registry.json
3. **READ** — PDF → ONNX+OCR+CV → SchemaModel
4. **CHECK** — reguly JSON + diff GT
5. **BUILD** — config XML → bloki → SVG

## GPU

RTX 2080 (8 GB) = max cap runtime aplikacji. Agenci dev (Cursor, Claude) = chmura, osobno.

## Archiwum

Kod EPLAN: `archive/eplan-era-2026-06.zip`
