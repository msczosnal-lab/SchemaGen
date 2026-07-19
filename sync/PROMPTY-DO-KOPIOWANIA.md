# Prompty do wklejania agentom (stan 2026-07-19)

Kolejność ma znaczenie: **027 → 025 → 024**. 027 zmienia przestrzeń klas, więc metryki liczone przed nim są nieporównywalne z tym, co będzie po.

Trening: **zamrożony** na `symbols_tiled_v1-2` (conf 0.18) do czasu doznaczenia stron. `symbols_tiled_v1-3` (mAP 0.0001) nie wchodzi do `registry.json`.

---

## 1. Prompt 027 — eksport po `type` (Cursor, Sonnet 5) — ZACZNIJ TU

```
SchemaGen. Zadanie 027 v2 — poprawka eksportu klas.

Przeczytaj: sync/prompts/027-gt-cleanup-class-merge.md (cała treść, to źródło prawdy dla tego zadania).

Skrót problemu: GT v2 ma pola `type` (kanoniczny typ) i `tag` (oznaczenie z rysunku).
Eksport klasyfikuje po `tag` (backend/class_map.py:188), przez co:
- tag="6" (numer złączki) tworzy klasę "6", wycinaną przez --min-count 5 → bbox znika z treningu
- tag="przekaźnik" mapuje się przez paletę na id "relay" → stąd angielskie nazwy klas
W 382 z 421 symboli type != tag. zlaczka ma w GT 136 wystąpień, a w datasecie 10.

Zrób krok 1 i 2 z promptu:
1. Klasa symbolu = `type` (ścieżka GT v2), `tag` nie trafia do YOLO.
   Fallback tag_to_class() zostaje dla starych rekordów label v1 bez `type`.
   Normalizuj `type` do ASCII — w GT są duplikaty na diakrytykach
   (custom_urządzenie vs custom_urzadzenie, custom_terminale_urządzenia vs terminale_urzadzenia).
2. Re-export + pomiar, wynik zapisz w sync/analysis/027-export-type-fix.md (przed/po per klasa).

Nie rób kroku 3 (scalenia klas) — czeka na decyzję Filipa po obejrzeniu crops.

Walidacja: pytest backend/tests labeler/tests -q; class_report --min-count 5;
visualize_yolo_dataset.py --root data/labeled_tiled --limit 20.
Test regresji obowiązkowo: symbol type="zlaczka" tag="6" eksportuje się jako klasa zlaczka.

Niezmienniki z CLAUDE.md obowiązują (gt/*.json = źródło prawdy, zapis atomowy, guard empty).
Commit: sync/commit-message.txt jedna linia [Cursor] ...
```

**Kryterium odbioru:** `zlaczka` ~100+, zero klas numerycznych, zero nazw angielskich, suma bbox **wyższa** niż 480.

---

## 2. Prompt 025 — audyt labelera (Opus 4.8) — może iść równolegle

```
SchemaGen. Zadanie 025 — audyt labelera.

Przeczytaj: sync/prompts/025-labeler-audit.md oraz CLAUDE.md (niezmienniki GT).

Zgłoszenie: labeler pokazuje bboxy nie dla tej strony, dla której powinien
(zła strona, złe bboxy). Filip nie wskaże konkretnych przypadków — do audytu cały labeler,
bo w historii były problemy z odzyskiwaniem danych (uszkodzona baza SQLite,
migracja 030 GT→JSON, hard reset repo).

Wykonaj FAZĘ A (audyt, BEZ zmian w kodzie) i FAZĘ B (raport):
- A1 integralność GT: tools/audit_gt.py (read-only, --json) wg specyfikacji w prompcie
- A2 ścieżka page_id przez graph.js (2924 linie), app.js (2255), labeler/app.py, backend/db.py, gt_store.py
- A3 czy da się zapisać GT pod złym page_id (to najgroźniejszy scenariusz)
- B: sync/analysis/025-labeler-audit.md — tabela znalezisk z priorytetem

Zasada priorytetu: wszystko, co może CICHO zapisać zły GT, jest ważniejsze niż błędy wyświetlania.
Zły widok użytkownik zauważy — zły zapis nie.

Pierwszy trop: p040 jest w config/val-pages.yaml, Filip twierdzi że go oznaczył,
ale nie ma pliku gt/*p040.json. To najświeższy zapis, więc najlepszy ślad.

NIE wchodź w fazę C (naprawa) bez akceptacji listy przez Filipa.
```

**Kryterium odbioru:** raport z priorytetami, zero zmian w kodzie.

---

## 3. Prompt 024 — connections (Opus 4.8) — DOPIERO PO 027

```
SchemaGen. Zadanie 024 — connections: remap fail + precyzja.

Przeczytaj: sync/prompts/024-conn-remap-precision.md
oraz sync/analysis/023-p028-conn-baseline.md.

Kontekst: 023 naprawił topologię emisji (gwiazda → łańcuch), p028 conn 4/42 → 10/42.
To był mniejszy kubeł błędu. Zostaje 118 remap-fail i precyzja ~0.05 (207 RT vs 42 GT).

Kolejność sztywna:
1. Metryka P/R/F1 dla connections w diff_metrics.py + --json. WAG SCORE NIE ZMIENIAĆ.
   Baseline P/R/F1 dla 6 stron → sync/analysis/024-conn-pr-baseline.md
2. Breakdown 118 remap-fail na 4 kategorie (spec w prompcie). Kategoria 4
   (klasy kontekstowe poza YOLO) to sufit nienaprawialny bez ContextResolver — policz ją JAWNIE.
   Jeśli dominuje, zatrzymaj się i zaproponuj ContextResolver jako 028 zamiast obchodzić problem.
3. Implementacja dopiero wg masy błędu z kroku 2.

Kryterium: F1 w górę (nie sam match — match rośnie też przez nadprodukcję krawędzi),
poprawa na ≥2 stronach POZA p028 (023 dał zysk wyłącznie na p028 — nie powtarzać przeuczenia),
val-pages mean bez regresji.

Uwaga: 027 zmieniło przestrzeń klas, więc baseline 21.50 jest nieaktualny.
Zmierz aktualny stan przed jakąkolwiek zmianą.

Wątek do sprawdzenia przy okazji: loop 032 it5 zanotował zlaczka GT x=5558 vs RT x=442, IoU=0.
Eksport GT jest zdrowy (sprawdzone), więc rozjazd dotyczy ścieżki runtime.
```

**Kryterium odbioru:** F1 w górę na ≥3 stronach, nowy baseline zapisany.

---

## Co robi Filip (nie agent)

1. **Backup przed czymkolwiek:** `git tag gt-pre-027` (zrobione) + kopia `gt/` poza repo.
2. **Po 027:** obejrzeć `visualize_class_crops.py --per-class 80` i rozstrzygnąć:
   - `zlaczka` (136) vs `zlacze` (38) vs `listwa_zlaczek` (4)
   - `styki` (3) / `styki_przekaznika` (4) / `styk_nc` (6)
   - `custom_urzadzenie` vs `urzadzenie`
3. **Czyszczenie GT** w `element_review.py` — usuwanie bboxów niepasujących do wzorca klasy.
   Przy każdej klasie zapisać jednym zdaniem, co do niej należy → `sync/analysis/027-gt-cleanup.md`.
   Te definicje są trwalszym wynikiem niż liczby.
4. **Doznaczanie stron** — cel ~15–20. Strony z `contactor` i `custom_urzadzenie` muszą trafić
   do **train**, nie val (dziś obie klasy istnieją wyłącznie po stronie walidacyjnej).
5. **Trening** dopiero po punkcie 4.
