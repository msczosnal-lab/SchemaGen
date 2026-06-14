# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

---

## Stan (2026-06-14, wieczór)

| Prompt | Status |
|--------|--------|
| **001-labeler-canvas** | DONE |
| **003-labeler-bbox-hierarchy** | DONE |
| **007-sources-analysis** | **DONE — akceptacja Filipa** |
| **008-symbol-atlas-extract** (faza 1 / QET) | **AKTYWNE** |
| **002-labeler-lines-colors** | OPEN — równolegle lub po 008a |
| **009-bbox-symbol-id** | po 008a |

---

## Aktywne zadanie

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/008-symbol-atlas-extract.md`](prompts/008-symbol-atlas-extract.md) |
| **Deliverable** | `config/symbol-reference.yaml`, `data/atlas/crops/`, `backend/atlas/` |
| **Typ** | Implementacja offline (parser QET `.elmt`) |
| **Model** | Sonnet, effort **High** |

### Kroki

1. Przeczytaj `docs/knowledge-sources-analysis.md` (v4, zaakceptowane)
2. Przeczytaj `sync/filip-to-zw.md` — **Filip: tylko PDF schematu, bez EPLAN WRT01**
3. Sklonuj QET → `data/atlas/qet/` (gitignore)
4. Wykonaj **008a** wg promptu
5. `pytest backend/tests labeler/tests`
6. Wpis w `sync/zw-to-filip.md`
7. `sync/commit-message.txt` = `[Claude] atlas: QET extract → symbol-reference.yaml (prompt 008a)`

### Czego NIE robic w 008a

- IEC 60617 PDF (008b)
- PDF producenta (008c — Filip uzupełni ścieżkę później)
- EPLAN lokalny / `.edz`
- UI labelera (009)
- Cloud API

---

## Kontekst decyzji (Filip, 2026-06-14)

- **Akceptacja** analizy 007: atlas warstwowy + Siemens-first
- **WRT01:** tylko **PDF** (77 str., p013–p015 oznaczone)
- **Drugi PDF:** elementy innych producentów — ścieżka w `sync/sources-inbox.md` (Filip dopisze)
- **Brak** projektu EPLAN / Data Portal dla WRT01
- Bbox-y na WRT01: **kontynuować** (p013–p015, potem 3–5 stron różnorodnych)

---

## Kolejnosc promptow

| # | Prompt | Status |
|---|--------|--------|
| 1 | 007-sources-analysis | DONE ✓ |
| 2 | **008-symbol-atlas-extract (a)** | **AKTYWNE** |
| 3 | 002-labeler-lines-colors | OPEN |
| 4 | 009-bbox-symbol-id | po 008a |
| 5 | 008b IEC PDF / 008c PDF producenta | po 008a |
| 6 | 001-symbol-detector | po danych bbox + atlas MVP |

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]`. Nie nadpisuj jesli jest `[Cursor]` i niepusty.
