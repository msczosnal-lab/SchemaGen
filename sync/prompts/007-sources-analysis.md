# Zadanie 007: ocena i analiza źródeł wiedzy o schematach

**Status:** DONE — akceptacja Filip 2026-06-14 (commit `dd8eceb`)  
**Typ:** research / analiza (nie implementacja kodu)  
**Model:** Sonnet lub Opus, effort **High** (dokładność terminologii)  
**Deliverable:** [`docs/knowledge-sources-analysis.md`](../docs/knowledge-sources-analysis.md)

## Kontekst

Filip rozważa **hybrid**: schemat WRT01 (bboxy, linie, tagi) + **zewnętrzna baza wiedzy** (poradnik wideo, atlas symboli, normy) zamiast przepisywania encyklopedycznych opisów w każdym bboxie.

SchemaGen dziś:
- **Labeler** — bbox + opis → `config/element-catalog.yaml` (prawie pusty)
- **Rozpoznawanie** — YOLO + OCR + LineTracer (stuby) — czyta **PNG schematu**
- **Generowanie** — `blocks/*.json` (szablony obwodów, nie atlas symboli)
- **Pivot offline** — brak cloud API w `backend/recognize/`, `train/`, `labeler/`

Pytanie biznesowe: **czy i jak** zewnętrzne źródła skrócą oznaczanie i poprawią jakość modelu?

## Wejście od Filipa

1. Przeczytaj [`sync/sources-inbox.md`](../sources-inbox.md) — linki i pliki od Filipa
2. Jeśli inbox pusty — poproś Filipa o uzupełnienie (min. 1 źródło, np. poradnik wideo)
3. Opcjonalnie przejrzyj istniejące oznaczenia: `data/labeled/*.label.json`, bboxy w DB (SchematWRT01_p013–p015)
4. Kontekst: [`docs/project-context.txt`](../../docs/project-context.txt), [`docs/labeling-guide.md`](../../docs/labeling-guide.md)

## Zadanie — wykonaj analizę

Napisz **`docs/knowledge-sources-analysis.md`** według struktury poniżej. Pracuj **iteracyjnie z Filipem** — po każdej rundzie dopisuj źródła i aktualizuj dokument.

### 1. Inwentaryzacja źródeł

Dla każdego źródła z inbox:

| Pole | Opis |
|------|------|
| Nazwa, typ, URL/ścieżka | |
| Język, standard (IEC/PN/producent) | |
| Format użyteczności | tekst / obraz symboli / wideo / interaktywne |
| Dostęp offline | da się pobrać / zarchiwizować lokalnie? |
| Zgodność z WRT01 | ten sam język symboli i tagów? (szacunek 1–5) |

### 2. Mapowanie na potrzeby SchemaGen

Rozdziel wyraźnie, co źródło daje dla:

| Potrzeba | Ze schematu (must) | Ze źródła referencyjnego (nice) |
|----------|-------------------|--------------------------------|
| Pozycja bbox | ✓ | |
| Tag instancji (`-11`, `-K1`) | OCR / labeler | |
| Typ urządzenia (fuse, contactor…) | YOLO / dopasowanie | atlas symboli |
| Opis / definicja | ręcznie dziś | podręcznik → katalog |
| Połączenia elektryczne | LineTracer + graf | reguły walidacji |
| Bloki funkcjonalne (RUPS1…) | tylko projekt | częściowo teoria |

### 3. Macierz oceny (każde źródło)

Oceń 1–5 + krótkie uzasadnienie:

- **Przydatność dla oznaczającego** (Filip mniej pisze)
- **Przydatność dla treningu YOLO** (obrazy symboli, syntetyka)
- **Przydatność dla walidacji** (reguły „co powinno być obok czego”)
- **Koszt integracji** (niski / średni / wysoki)
- **Ryzyko** (inny standard, licencja, halucynacje przy streszczeniu wideo)

### 4. Propozycja integracji technicznej

Zaproponuj **konkretny format** lokalny (bez cloud w runtime), np.:

```yaml
# config/symbol-reference.yaml (propozycja — nie implementuj bez akceptacji Cursor)
symbols:
  - id: disconnector_fuse
    iec_ref: "…"
    aliases: ["rozłącznik bezpiecznikowy"]
    default_description: "…"
    # opcjonalnie: path do crop PNG atlasu
```

Opisz relację do istniejących plików:
- `config/element-catalog.yaml` — instancje z labelera
- `config/symbol-classes.yaml` — klasa YOLO `element`
- `blocks/` — szablony obwodów, nie pojedyncze symbole
- `archive/eplan-era-2026-06.zip` — czy warto ekstrakcji symboli (offline, jednorazowo)

### 5. Rekomendacja dla Filipa

Jednoznaczna sekcja **„Co robimy”**:

1. **Kontynuować bboxy na WRT01?** (tak/nie, ile stron)
2. **Które źródło priorytetem #1?**
3. **Skrócony workflow labelera** — np. tylko tag `-11`, opis z bazy
4. **Co odkładamy** — np. pełne ręczne rysowanie linii vs auto-tracer
5. **Następny prompt implementacyjny** — propozycja dla Cursor (np. import atlasu, dopasowanie bbox→typ)

### 6. Ekstrakcja z wideo (jeśli Filip poda poradnik)

Dla materiału wideo **nie** zakładaj, że program obejrzy plik w runtime. Zamiast tego:

- Streszczenie **ręczne / z transkryptu** — lista symboli omawianych w filmie
- Tabela: **symbol wizualny → nazwa PL → przykład tagu → występuje na WRT01? (tak/nie/nie wiemy)**
- Timestampy rozdziałów (jeśli dostępne) — dla Filipa jako ściąga

## Deliverable — struktura pliku

Plik `docs/knowledge-sources-analysis.md` musi mieć:

```markdown
# Analiza źródeł wiedzy — schematy elektryczne
Data, autor (Claude + Filip), wersja

## Streszczenie wykonawcze (≤15 linii)

## Źródła (tabela)

## Ocena szczegółowa (per źródło)

## Mapowanie na SchemaGen

## Proponowany format bazy symboli

## Rekomendacje i następne kroki

## Otwarte pytania do Filipa
```

## Zakazy

- **Nie implementuj kodu** w tym zadaniu (wyjątek: ewentualny szkic YAML w dokumencie jako propozycja)
- **Nie** dodawaj cloud API / zewnętrznych serwisów do runtime
- **Nie** rozpakowuj `archive/eplan-era-2026-06.zip` do runtime — tylko opisz, czy warto i co wyciągnąć
- **Nie** zmieniaj `backend/models/` ani labelera

## Po ukończeniu (runda 1)

1. Commit pliku `docs/knowledge-sources-analysis.md` (+ ewentualnie uzupełniony `sync/sources-inbox.md` jeśli Filip dodał źródła)
2. Wpis w `sync/zw-to-filip.md` — link do analizy, 3 bullet rekomendacji
3. `sync/commit-message.txt` = `[Claude] docs: knowledge sources analysis (prompt 007)`

**Kolejne rundy:** Filip dopisuje źródła → aktualizujesz ten sam dokument (wersja + data), krótki wpis w `zw-to-filip.md`.

## Test akceptacji

- [ ] Plik `docs/knowledge-sources-analysis.md` istnieje i ma wszystkie sekcje
- [ ] Każde źródło z `sync/sources-inbox.md` ma ocenę
- [ ] Jest jasna rekomendacja: schemat vs baza vs hybrid
- [ ] Propozycja formatu lokalnego (YAML/JSON) jest zgodna z offline pivot

## Poprawka (runda N)

*(Cursor dopisuje feedback po review)*
