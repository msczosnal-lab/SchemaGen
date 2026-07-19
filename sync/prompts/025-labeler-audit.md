# Zadanie 025: Labeler — audyt całościowy + naprawa wiązania strona↔GT

**Status:** AKTYWNE
**Model:** Opus 4.8 na audyt (Faza A — szukanie nieznanych błędów w ~7 800 liniach), Sonnet 5 na wdrożenie (Faza C, po zatwierdzonej liście)
**Powód:** GT jest jedynym źródłem prawdy dla całej metryki. Błąd w labelerze fałszuje każdy SCORE wstecz.

## Zgłoszenie Filipa

> „Labeler pokazuje bboxy nie dla stron dla których powinien (zła strona i złe bboxy wczytane). Narzędzie do całościowego sprawdzenia — widzę błędy, ale ich nie wskażę. Do analizy cały labeler, bo były problemy z odzyskaniem danych."

Objaw potwierdzony: **desync page_id ↔ wczytany GT**. Zakres audytu szerszy niż ten jeden objaw.

## Historia, która mogła to spowodować (sprawdzić każdą)

1. **030** — migracja GT z SQLite do `gt/*.json`, cache odbudowywany (`rebuild_cache_from_gt`)
2. **Uszkodzenie bazy** (`malformed`) + `tools/recover_db.py` — dane odzyskiwane, możliwe niepełne/przemieszane rekordy
3. **Hard reset repo** — checkout mógł rozjechać `gt/` z `data/schemagen.db`
4. **022** — labeler v2, dwa tryby + prefill; nakładka na stary v1
5. `gt/_backup_2026-07-12/` — sprawdzić, czy nie jest wczytywany razem z `gt/*.json`

## Faza A — audyt (BEZ zmian w kodzie)

### A1. Integralność danych GT

Skrypt jednorazowy `tools/audit_gt.py` (read-only, `--json`):

- dla każdego `gt/*.json`: `page_id` w pliku == nazwa pliku?
- rozmiar obrazu w GT == faktyczny rozmiar PNG w `data/raw/`?
- bboxy mieszczą się w wymiarach strony? ile poza kadrem?
- duplikaty ID symboli/terminali w obrębie strony? ID współdzielone **między** stronami?
- cache SQLite `schematic_graph` == `gt/*.json`? (rozjazd = przyczyna „złej strony")
- `gt/_backup_2026-07-12/` — czy wpada w glob `gt/*.json` gdziekolwiek w kodzie?

Wynik → `sync/analysis/025-gt-integrity.md`. **To jest raport, nie naprawa.**

### A2. Ścieżka page_id przez cały stos

Prześledzić i udokumentować, gdzie `page_id` może się zgubić lub pomieszać:

`labeler/static/graph.js` (2 924 linie) · `labeler/static/app.js` (2 255) · `labeler/app.py` (581) · `backend/db.py` · `backend/gt_store.py`

Szukać konkretnie:

- **stan globalny w JS** — czy `currentPage` jest jedynym źródłem, czy istnieją równoległe zmienne/cache
- **wyścig fetch** — szybka zmiana strony: odpowiedź dla starej strony nadpisuje nową? (brak `AbortController` / brak sprawdzenia `page_id` w odpowiedzi)
- **cache przeglądarki** na `GET /api/graph/{page_id}` i `/api/pages/{page_id}/image`
- **fallback `_empty_graph`** (`app.py:419`) — czy pusty graf nie nadpisuje widoku poprzedniej strony
- **sanityzacja page_id** w `gt_store` — czy dwie różne strony nie mapują się na ten sam plik
- **`gt_loader.py`** — priorytet graph_v2 → fallback label_v1: czy przy niepełnym v2 nie miesza źródeł

### A3. Zapis — czy da się zapisać GT pod złym page_id

Najgroźniejszy scenariusz: użytkownik widzi stronę X, zapis idzie do Y → cicha korupcja GT.

- czy `POST /api/graph/{page_id}` waliduje, że `body.page_id` == ścieżka URL?
- guard `skipped_empty_overwrite` — czy działa też przy `allow_empty=True` z prefill (`app.py`, prefill zapisuje z `allow_empty=True`)
- czy `graph_prefill` / `runtime_draft` / `auto_draft` nie nadpisują ręcznego GT

## Faza B — raport i decyzja

`sync/analysis/025-labeler-audit.md`:

| Znalezisko | Ryzyko dla GT | Pewność | Koszt naprawy | Priorytet |
|---|---|---|---|---|

Reguła: **wszystko, co może cicho zapisać zły GT, ma priorytet nad błędami wyświetlania.** Zły widok użytkownik zauważy — zły zapis nie.

Filip zatwierdza listę przed Fazą C.

## Faza C — naprawa (Sonnet 5, po akceptacji)

Wymagane niezależnie od znalezisk:

1. **Kontrakt page_id** — odpowiedź `GET /api/graph/{id}` zawiera `page_id`; frontend odrzuca odpowiedź, jeśli nie zgadza się z aktualnie otwartą stroną
2. **`AbortController`** przy zmianie strony — anulowanie fetchów w locie
3. **Walidacja po stronie zapisu** — `POST /api/graph/{id}` odrzuca body z niezgodnym `page_id` (400)
4. **`Cache-Control: no-store`** na endpointach GT
5. **Testy regresji** w `labeler/tests/`: szybka zmiana strony A→B (odpowiedź A po B nie wchodzi), zapis z niezgodnym page_id = 400, pusty graf nie nadpisuje niepustego

## Niezmienniki (nie łamać — `CLAUDE.md`)

- `gt/<page_id>.json` = źródło prawdy; SQLite = cache odbudowywalny
- Zapis GT atomowo (tmp + `os.replace`), nigdy w miejscu
- Pusty graf nie nadpisuje niepustego (`skipped_empty_overwrite`)
- **Przed Fazą C: `git tag gt-pre-025` + kopia `gt/` poza repo.** Audyt narzędzia, które psuje dane, nie może zacząć od zepsucia danych.

## Walidacja

```powershell
python -m tools.audit_gt --json
pytest labeler/tests backend/tests -q
python scripts/diff_gt_runtime.py --page p028
```

Kryterium: audyt bez znalezisk krytycznych; `diff_gt_runtime` na 6 stronach **bez zmiany SCORE** — naprawa labelera nie może ruszyć metryki. Jeśli ruszyła, znaczy że GT było wcześniej złe i wszystkie baseline'y wymagają przeliczenia.

## [RYZYKO] Nierozstrzygnięte

`p040` — Filip zgłasza, że oznaczył; w `gt/` widocznym z tej sesji **nie ma pliku p040** (jest w `config/val-pages.yaml`, ale bez GT). Albo niezsynchronizowane, albo zapis poszedł gdzie indziej — **to może być ten sam błąd co „zła strona"**. Sprawdzić jako pierwsze w A1: to najświeższy zapis, więc najlepszy trop.
