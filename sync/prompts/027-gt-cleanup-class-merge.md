# Zadanie 027: GT cleanup — przegląd bboxów + scalenie klas

**Status:** AKTYWNE — blokuje następny trening
**Model:** Sonnet 5 (migracja narzędzia), decyzje taksonomiczne — Filip
**Zależność:** 026 zamknięte (tor modelu zamrożony na `symbols_tiled_v1-2`)

## Zasada przyjęta przez Filipa

> Lepiej mniej **prawdziwych** bboxów niż dużo mieszających się. Kilka wzorców na klasę, nie dziesiątki osobnych ramek generujących szum.

Zgodne z tym, jak uczy się detektor: spójność wewnątrz klasy waży więcej niż liczność. Klasa z 30 spójnymi przykładami uczy się lepiej niż z 80, z których 30 to inny element.

**Ale:** czyszczenie **nie zastępuje** doznaczania. Dziś jest 480 bbox, po czyszczeniu będzie mniej. Kolejność jest jednak właśnie taka — najpierw kanon, potem masa. Doznaczanie 1 500 bboxów w niespójnej taksonomii to 1 500 bboxów do późniejszego przeglądu.

## Narzędzie — już istnieje

| Skrypt | Rola |
|---|---|
| `scripts/element_review.py` | przeglądarka **wszystkich** oznaczonych elementów: klik = usuń, `<select>` = retag, filtr per klasa, „przejrzane" w localStorage |
| `scripts/visualize_class_crops.py` | wycinki pogrupowane per klasa — ocena spójności |
| `scripts/apply_reassign.py` | stosuje `reassignments.json` (`new_tag="__DELETE__"` = usuń) |
| `scripts/apply_delete.py` | PRZESTARZAŁE — wchłonięte przez `apply_reassign` |

Nie budować nowego. Trzeba je **naprawić**.

## [BŁĄD] Narzędzie pisze do złego źródła prawdy

```
element_review.py  → train.dataset_export.load_labeled_records()   # label v1 (SQLite)
apply_reassign.py  → backend.db.load_annotation / save_annotation  # label v1 (SQLite)
```

Oba **omijają `gt/*.json`** — źródło prawdy od 030. Skutki, oba poważne:

1. **Przeglądasz co innego, niż trenujesz.** `tiled_export` po 023 czyta GT v2 (`load_all_training_records()`), a `element_review` pokazuje v1. Ocena spójności dotyczy zbioru, który nie jest tym, na czym uczy się model.
2. **Praca ginie.** `apply_reassign` zapisuje do cache SQLite. Labeler przy starcie woła `rebuild_cache_from_gt()` → nadpisuje cache z `gt/*.json`. Godziny czyszczenia znikają bez komunikatu.

**Nie uruchamiać `apply_reassign --apply` przed migracją.** Dry-run bezpieczny.

Prawdopodobnie ten sam korzeń, co zgłoszenie „labeler pokazuje bboxy nie dla tych stron" (025): dwie współistniejące przestrzenie danych, v1 i v2, i różne miejsca sięgają do różnych.

## Krok 1 — migracja narzędzia na GT v2

1. `element_review.py` czyta przez `labeler/gt_loader.py` (graph_v2 priorytet) albo `load_all_training_records()` — **ta sama ścieżka, co `tiled_export`**. Jedno źródło, wspólna funkcja.
2. `apply_reassign.py` zapisuje przez `backend.db.save_schematic_graph` / `gt_store` — atomowo, z guardem `skipped_empty_overwrite`. Nigdy bezpośrednio do cache.
3. Zachować `--apply` / dry-run i backup przed zapisem (już jest — nie usuwać).
4. Test: retag + delete na stronie testowej → `gt/<page>.json` zmieniony, cache zgodny po `rebuild_cache_from_gt()`.

**Przed pierwszym `--apply`: `git tag gt-pre-027` + kopia `gt/` poza repo.**

## Krok 2 — kanon klas (Filip, decyzja domenowa)

Wejście: `python scripts/visualize_class_crops.py --per-class 80`

Do rozstrzygnięcia — potwierdzone duplikaty EN/PL:

| Podejrzana para/grupa | Liczności |
|---|---|
| `zlaczka` ↔ `terminal_block` | 10 + 10 |
| `relay` ↔ `przekaznik_polaryzowany` | 114 + 9 |
| `styki` / `styki_nc` / `styk_nc` / `styki_przekaznika` / `styk_stycznika` | 5 / 5 / 15 / 16 / 14 |

Grupa styków — pięć etykiet, 55 bboxów razem, podział niejasny. Rozstrzygnąć **łącznie**, patrząc na crops, nie na nazwy.

Wynik → `config/class-aliases.yaml`, nazwy kanoniczne **polskie** (spójnie z GT v2).

Reguła przy wątpliwości: jeśli dwa crops wyglądają dla ciebie tak samo, dla sieci tym bardziej. Scalać.

## Krok 3 — alias w eksporcie

Mapa aliasów stosowana w `dataset_export` **i** `tiled_export` przez **jedną wspólną funkcję**. Nie duplikować — rozjazd tych dwóch ścieżek był przyczyną 023.

Kontrola: suma bbox po scaleniu bez usuwania = **480**. Scalenie zmienia przypisanie klas, nie tworzy i nie gubi etykiet. Inna liczba = błąd migracji.

## Krok 4 — przegląd i czyszczenie (Filip)

Per klasa w `element_review.py`: usunąć to, co nie pasuje do wzorca klasy. Zapisać w `sync/analysis/027-gt-cleanup.md`: przed/po per klasa + krótka definicja wzorca każdej klasy.

Te definicje są ważniejsze niż same liczby — bez nich następne doznaczanie odtworzy ten sam szum.

## Kryterium zamknięcia

1. `class_report.py` bez nazw angielskich
2. Każda klasa produkcyjna ma spisany wzorzec w `027-gt-cleanup.md`
3. `apply_reassign --apply` zapisuje do `gt/*.json`; test regresji to potwierdza
4. `diff_gt_runtime.py` na 6 stronach — **SCORE się zmieni** (GT się zmieniło) → przeliczyć i zapisać nowy baseline, stary 21.50 unieważniony

Punkt 4 jest oczekiwany, nie regresją. Ale musi być zapisany świadomie, inaczej kolejne porównania będą fałszywe.

## Poza zakresem

- Trening (zamrożony do czasu doznaczania — 026)
- Zmiana `val-pages.yaml`
- ContextResolver
