# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

---

## Stan (2026-06-14)

| Prompt | Status |
|--------|--------|
| **001-labeler-canvas** | DONE |
| **003-labeler-bbox-hierarchy** | DONE |
| **007-sources-analysis** | **AKTYWNE** — wspólna praca Filip + Claude |
| **002-labeler-lines-colors** | WSTRZYMANE — po 007 lub równolegle jeśli Filip wskaże |

---

## Aktywne zadanie

| Pole | Wartosc |
|------|---------|
| **Prompt** | [`sync/prompts/007-sources-analysis.md`](prompts/007-sources-analysis.md) |
| **Inbox źródeł** | [`sync/sources-inbox.md`](sources-inbox.md) — **Filip uzupełnia linki** |
| **Deliverable** | `docs/knowledge-sources-analysis.md` |
| **Typ** | Research / analiza (bez kodu) |
| **Model** | Sonnet lub Opus, effort **High** |

### Kroki

1. Przeczytaj `docs/claude-cowork-instructions.md`
2. Przeczytaj `sync/filip-to-zw.md`
3. Filip uzupełnia `sync/sources-inbox.md` (wideo, PDF, atlas…)
4. Wykonaj **007-sources-analysis.md** → napisz `docs/knowledge-sources-analysis.md`
5. Iteruj z Filipem — dopisuj źródła, aktualizuj analizę
6. Wpis w `sync/zw-to-filip.md`
7. `sync/commit-message.txt` = `[Claude] docs: knowledge sources analysis (prompt 007)`

### Czego NIE robic w 007

- Implementacja labelera / recognize / importu atlasu
- Cloud API w runtime
- Rozpakowywanie EPLAN do kodu produkcyjnego

---

## Kontekst decyzji (Filip)

- Rozważa **podręcznik / wideo / bazę symboli** zamiast samych opisów ze schematu
- SchemaGen = **hybrid**: geometria + tagi ze schematu WRT01, typy/opisy z bazy referencyjnej
- 3 strony oznaczone (p013–p015), 77 stron w scope

---

## Kolejnosc promptow

| # | Prompt | Status |
|---|--------|--------|
| 1 | 003-labeler-bbox-hierarchy | DONE |
| 2 | **007-sources-analysis** | **AKTYWNE** |
| 3 | 002-labeler-lines-colors | wstrzymane |
| 4 | 001-symbol-detector | po danych + ewent. atlasie |

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]`. Nie nadpisuj jesli jest `[Cursor]` i niepusty.
