# KOLEJNE ZADANIE — wczytaj ten plik po wiadomosci od Filipa

> **Filip pisze:** „kolejne zadanie” → czytasz ten plik + `sync/filip-to-zw.md` + aktywny prompt.

**Wizja:** [`docs/schematic-interpretation.md`](../docs/schematic-interpretation.md) — trzy filary + relacje.

---

## Stan (2026-06-25)

| Prompt | Status |
|--------|--------|
| **010-labeler-bbox-first-palette** | ✅ DONE |
| **005–006, 001 recognize, train_cycle** | ✅ DONE |
| **symbols_atomic_v2** | ✅ mAP50≈0.92, aktywny w registry |
| **002-ocr-engine** | ✅ DONE — smoke OK (~75%, mały/pionowy tekst akceptowane) |
| **002-labeler-lines-colors** | ✅ DONE (Claude) |
| **003-line-tracer** | ✅ DONE — smoke OK (progi Hough: backlog) |
| **004-graph-builder** | 🟢 **AKTYWNE dla Claude** → [`PROMPT-CLAUDE-004.md`](PROMPT-CLAUDE-004.md) |
| **008a QET atlas** | ⛔ NIE UŻYWAĆ |

---

## Aktywne zadanie — Claude (PRIORYTET)

| Pole | Wartosc |
|------|---------|
| **Cel** | **GraphBuilder.build()** — SchemaModel z 3 filarów |
| **Start** | [`sync/PROMPT-CLAUDE-004.md`](PROMPT-CLAUDE-004.md) |
| **Spec** | `sync/prompts/004-graph-builder.md` |

**Nie ruszaj:** atlas QET, trening GPU, preview scripts.

---

## Aktywne zadanie — Filip

| Pole | Wartosc |
|------|---------|
| **Claude** | Wklej `PROMPT-CLAUDE-004.md` → GraphBuilder |
| **Labeler L** | GT wire/bus na 2–3 stronach (p030) — pod walidację connections |
| **Review autolabel** | bbox p051+ (incognito) |
| **train_cycle** | dopiero po poprawionym GT bbox |

### Cykl YOLO (gdy GT poprawione)

```powershell
python scripts/train_cycle.py
```

---

## Commit

Jedna linia w `sync/commit-message.txt`, autor `[Claude]` lub `[Cursor]`.
