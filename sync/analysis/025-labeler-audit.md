# 025 — audyt labelera (Faza A + B)

**Data:** 2026-07-19 · **Model:** Opus 4.8 · **Zakres:** `labeler/`, `backend/db.py`, `backend/gt_store.py`, `backend/paths.py`
**Bez zmian w kodzie produkcyjnym.** Dodany wyłącznie `tools/audit_gt.py` (read-only).

---

## Wniosek jednozdaniowy

**6 plików w `gt/` jest zdrowych — ale to nie jest całe GT.** Uruchomienie audytu na PC Filipa pokazało
**197 stron w cache SQLite bez pliku w `gt/`**, w tym `p040`. Baza jest w `.gitignore` i już raz padła.
Drugi wątek: mechanizm, który przy szybkiej zmianie strony zapisuje graf strony A pod page_id strony B.

> **Aktualizacja 2026-07-19, po uruchomieniu A1 na PC Filipa.** Pierwsza wersja tego raportu powstała
> na klonie ZW, gdzie baza była pusta (po rollbacku hot journala) — stąd wniosek „dane GT są zdrowe".
> Był prawdziwy dla `gt/`, ale niepełny: nie widziałem 197 wierszy cache. Sekcja F0 poniżej jest nowa
> i przejmuje priorytet nad F1.

---

## F0 [BŁĄD, KRYTYCZNY] — 197 stron GT istnieje wyłącznie w cache SQLite

**Wynik A1 na PC Filipa:** 197 × `cache_orphan` — wiersze w `schematic_graph`, dla których **nie ma
pliku `gt/<page_id>.json`**. Trzy dokumenty:

| Dokument | Zakres stron w cache | Plików w `gt/` |
|---|---|---|
| `22_A_153_PL_Adamed_AGV_SA2_20250706` | p020–p199 (≈160 stron) | **6** (p028–p034) |
| `25_A_229_PL5_19012026` | p004–p023 (17 stron) | **0** |
| `SchematWRT01` | p013–p052 (16 stron) | **0** |

To odwraca niezmiennik z `CLAUDE.md`. Miało być: `gt/` = źródło prawdy, SQLite = cache odbudowywalny.
Faktycznie: **dla 197 stron SQLite jest jedynym nośnikiem**, a `gt/` ma 3% zawartości. Baza:

* jest w `.gitignore` (`data/schemagen*`) — **zero wersjonowania, zero kopii w repo**,
* już raz padła na `malformed` (stąd `tools/recover_db.py`),
* działa w trybie DELETE zamiast WAL (F4) — czyli w tym samym trybie, w którym padła.

**Prawdopodobna przyczyna:** migracja 030 (`tools/export_gt_to_json.py`) eksportuje wszystkie wiersze
bezwarunkowo, więc albo została puszczona na bazie mającej wtedy tylko 6 wierszy (a reszta wróciła
później przez `recover_db.py`), albo nie została puszczona ponownie po odzyskaniu bazy.
`gt/_backup_2026-07-12/` też ma tylko 6 plików — backup powstał już po stracie.

### F0b — co dokładnie siedzi w tych 197 stronach (wynik `rescue --dry-run`)

**196 z 197 stron ma `0 linii`.** Jedyny wyjątek to `p040` (19 sym./17 linii). To rozstrzyga charakter
danych: **to nie jest ręczne GT v2**, bo ręczna praca w labelerze v2 zawsze rodzi linie. To bboxy.

Znaczniki czasu układają się w trzy rozłączne grupy:

| Grupa | `updated_at` | Strony | Zawartość | Interpretacja |
|---|---|---|---|---|
| **A** | `2026-07-11T16:33:51.222736` — **identyczny co do mikrosekundy** dla ~180 stron | p020–p199, cały `25_A_229_PL5`, cały `SchematWRT01` | 1–163 sym., **0 linii** | Jedna operacja wsadowa, nie zapisy z labelera. Najpewniej `migrate_label_v1_to_graph.py` albo `recover_db.py` — konwersja starych adnotacji v1 |
| **B** | `2026-07-11T19:12:00` | `p027` | 90 sym., 0 linii | Osobny zapis. p027 to strona referencyjna („strzałki 7/8 + terminale — komplet", `KOLEJNE-ZADANIE.md`). **Wartościowa** |
| **C** | `2026-07-19T11:11:14`–`11:11:48` | p032, p035–p042 | patrz niżej | **Dzisiaj, 9 stron w 34 sekundy** |

### [BŁĄD] Grupa C wygląda na F1 złapane na gorącym uczynku

W grupie C cztery kolejne strony mają **dokładnie po 108 symboli**: p035, p036, p037, p038.
`gt/…_p034.json` — strona zapisana wcześniej — ma **też dokładnie 108 symboli i 0 linii**.

Pięć kolejnych stron schematu nie ma przypadkiem tej samej liczby symboli. To wygląda na zawartość
p034 rozlaną na p035–p038 przy przewijaniu stron — czyli **dokładnie mechanizm F1**, w oknie 34 sekund,
z odstępami 1–5 s między zapisami (tempo przewijania, nie tempo oznaczania).

Jeśli to się potwierdzi, część grupy C **nie jest danymi do odzyskania, tylko śmieciem wyprodukowanym
przez błąd** — i wpuszczenie jej do `gt/` zepsułoby GT zamiast je naprawić.

**Rozstrzyga to `tools/gt_dup_scan.py`** (nowy, read-only): liczy podpis SHA1 z posortowanej listy
bboxów każdej strony i pokazuje grupy stron o **identycznej zawartości**. Skanuje `gt/`, cache SQLite
i katalogi `gt/_rescue_*` naraz.

### POTWIERDZONE — F1 udowodnione na danych (2026-07-19)

```
--- sygnatura 2c7d6ccd1f9a · 108 symboli · 5 stron
      [cache] …_p034   108 sym./0 linii   2026-07-19T11:11:22.546049
      [gt/  ] …_p034   108 sym./0 linii
      [cache] …_p035   108 sym./0 linii   2026-07-19T11:11:24.937245   (+2.4 s)
      [cache] …_p036   108 sym./0 linii   2026-07-19T11:11:29.238465   (+4.3 s)
      [cache] …_p037   108 sym./0 linii   2026-07-19T11:11:31.239659   (+2.0 s)
      [cache] …_p038   108 sym./0 linii   2026-07-19T11:11:32.089477   (+0.85 s)
```

**Identyczne bboxy co do dziesiątej części piksela na pięciu różnych stronach schematu.**
To nie jest zbieg okoliczności — to zawartość p034 zapisana pod czterema kolejnymi page_id
przy przewijaniu, w odstępach 0.85–4.3 s. F1 przestaje być hipotezą z lektury kodu:
**jest udokumentowanym zdarzeniem z dzisiaj, 11:11:22–11:11:32.**

Druga grupa (`p079`/`p080`, **2 symbole**, znacznik z migracji wsadowej `16:33:51`) to
najprawdopodobniej **nie** F1 — przy dwóch bboxach kolizja podpisu jest możliwa przypadkiem
(np. ta sama ramka rysunkowa), a znacznik czasu wskazuje na migrację, nie na labeler.
Domyślny próg `--dup-min-symbols 5` ją pomija.

**`p040` nie wystąpił w żadnej grupie.** Jego 19 sym./17 linii to zawartość unikalna — czyli
**prawdziwa praca Filipa**, nie artefakt. Odzyskiwalna w całości.

**Co zostało utracone:** nic. p035–p038 nie miały wcześniej GT (brak w `gt/`, brak w
`val-pages` z plikiem), więc kopie nadpisały pustkę. Gdyby wyścig trafił w stronę z danymi,
strata byłaby niewykrywalna po fakcie — porównanie `gt/` z `gt/_backup_2026-07-12/` pokazuje,
że 6 głównych stron jest nietkniętych.

### F0c — to jest też najpewniej przyczyna porażki retrain z prompta 026

`026-retrain-fail-diag` zamknięto ustaleniem: **„480 bbox / 20 klas, train = 1 strona"**. Tymczasem
w cache leżą bboxy z ~190 stron, których eksport treningowy **nie widzi**: po 023 `tiled_export`
czyta `load_all_training_records()` → GT v2 → `gt/*.json` → **6 plików**. Wiersze w `schematic_graph`
nie są przez tę ścieżkę widziane, a `dataset_export` łączy v1 z tabeli `annotations` (nie `schematic_graph`).

Czyli migracja 030 nie tylko wyprowadziła GT poza źródło prawdy — **wycięła też ~190 stron
z datasetu treningowego**. „Tor modelu zamrożony na `symbols_tiled_v1-2`" może być odmrażalny
natychmiast po odzyskaniu grupy A. To jest osobny, duży zysk i warto go zweryfikować przed
kolejnym podejściem do treningu.

### To jest odpowiedź na p040

`22_A_153_PL_Adamed_AGV_SA2_20250706_p040` **jest na liście sierot**. Filip pamiętał dobrze — p040
został oznaczony, zapis poszedł do bazy, do `gt/` nigdy nie trafił. Nie zginął. Leży w pliku,
który nie jest w gicie.

**Działanie natychmiastowe (zrobione 2026-07-19):**

```powershell
copy data\schemagen.db data\schemagen.db.bak-025
python -m tools.audit_gt --md sync\analysis\025-gt-integrity.md
python -m tools.rescue_gt_from_cache --dry-run    # 197 stron, gt/_rescue_2026-07-19/
```

`tools/rescue_gt_from_cache.py` domyślnie zrzuca sieroty do `gt/_rescue_<data>/` — podkatalogu,
którego aplikacja nie czyta — żeby nic nie wjechało do źródła prawdy bez przejrzenia. `--promote`
przenosi do `gt/` i **nigdy nie nadpisuje istniejących plików**.

**[RYZYKO] Nie puszczać `--promote` na całości** — patrz F0b poniżej. Część grupy C to prawdopodobnie
produkt błędu F1, nie dane.

**[RYZYKO] Dopóki to nie jest zrobione, nie uruchamiać:** `scripts/apply_reassign.py --apply`
(już oznaczony jako [BŁĄD] w `KOLEJNE-ZADANIE.md`), `tools/recover_db.py`, ani niczego, co woła
`rebuild_cache_from_gt()` w wariancie z kasowaniem sierot (punkt F3a Fazy C — **musi poczekać na F0**).

---

### F0d — wpływ promocji na metrykę (SPROSTOWANE)

Odzysk wykonany: **193 strony** w `gt/_rescue_2026-07-19/`, 4 kopie odsiane, 6 pominiętych
(źródło prawdy wygrywa).

> **Korekta.** Wcześniejsza wersja tej sekcji ostrzegała, że promocja wywróci baseline 21.50,
> bo ewaluatory policzą 199 stron zamiast 6. **To było błędne** — napisane bez sprawdzenia,
> jak dobierany jest zestaw stron. Weryfikacja:
>
> | Narzędzie | Skąd bierze strony |
> |---|---|
> | `scripts/eval_val_pages.py` | `config/val-pages.yaml` (jawna lista 9 stron) albo `--page`/`--pages` |
> | `tools/baseline_eval_gt.py` | `PAGES = ["p028","p029","p030","p033"]` — na sztywno w kodzie |
> | `scripts/diff_gt_runtime.py` | `--page` (jedna strona, wymagane) |
>
> **Żadne z nich nie iteruje po `gt/*.json`.** Dołożenie 193 plików nie zmieni baseline 21.50.

Realny, mniejszy skutek: `val-pages.yaml` wymienia 9 stron, z których 5 nie miało GT. Po promocji
GT dostaną **p025, p040, p045, p050** (p035 odpadł jako kopia). `eval_val_pages` bez argumentów
zacznie liczyć te strony, więc **val-pages mean 30.77 się zmieni** — trzy z nich mają 0 linii, więc
w dół. To jedyna liczba do przeliczenia po promocji, i dotyczy zestawu walidacyjnego, nie baseline GT.

**`config/gt-eval.yaml` w ogóle nie istnieje i nikt go nie czyta.** Notatka w `KOLEJNE-ZADANIE.md`
(„Wykluczenie p031 ze średniej GT → `config/gt-eval.yaml`") opisuje mechanizm, który nigdy nie
powstał. To osobny dług, nie blokada promocji: **p031 (SCORE 0.00) nadal wchodzi do średniej z 6 stron
i zaniża 21.50 o ok. 3.6 pkt.** Warto zamknąć przy okazji, ale nie wstrzymuje F0.

---

### F0e — stan końcowy F0 (2026-07-19, zamknięte)

| Metryka | Przed | Po |
|---|---|---|
| Plików `gt/*.json` (źródło prawdy, w gicie) | **6** | **199** |
| Stron GT wyłącznie w niewersjonowanej bazie | **197** | **0** |
| Kopie z wyścigu F1 w danych | 4 | 0 (odsiane) |
| `p040` | „zaginiony" | odzyskany, 19 sym./17 linii |

Cache SQLite zgodny ze źródłem prawdy (199 = 199), zweryfikowane `tools/prune_cache_orphans.py`.

**[BŁĄD w moim narzędziu — naprawiony]** `audit_gt` przez pewien czas raportował 4 nieistniejące
sieroty. Przyczyna: czytał bazę przez `immutable=1`, co każe SQLite **zignorować dziennik i WAL** —
narzędzie pokazywało migawkę sprzed checkpointu. Dowód:

```
po DELETE w bazie WAL:   mode=ro -> ['a','b']   immutable=1 -> "no such table"
```

Naprawione: `mode=ro` w pierwszej kolejności, `immutable=1` tylko awaryjnie i z jawnym
znaleziskiem `db_read_stale`. Wniosek na przyszłość: **narzędzie diagnostyczne, które dla wygody
omija mechanizmy spójności bazy, produkuje fałszywe alarmy w dokładnie tym obszarze, który ma badać.**

### F0f — `bbox_out_of_frame`: nie jest błędem migracji

Osiem stron z jednym bboxem poza kadrem. Sprawdzone — **wszystkie osiem to klasa `urzadzenie`**,
duże bboxy kontenerowe (1500–3500 px) przeciągnięte ręcznie poza krawędź:

| Strona | bbox | przekroczenie |
|---|---|---|
| p022 | `[-2, 3151, 1647, 4351]` | x1 = −2 |
| p047 | `[0, 3261, 2717, 5169]` | y2 o 491 |
| p057 | `[1427, 3356, 4825, 5099]` | y2 o 421 |
| p058 | `[1394, 3357, 4944, 5150]` | y2 o 472 |
| p065 | `[4248, 2427, 6624, 4424]` | x2 o 7 |
| p149 / p157 | `[5099, ~725, 6638, 2048]` | x2 o 21 |
| p177 | `[370, 2731, 3394, 4892]` | y2 o 214 |

Wcześniej opisałem to jako „systematyczny artefakt migracji v1" — **nietrafnie**. To ręczne
zaznaczenia obszaru urządzenia z przeciągnięciem poza brzeg. `urzadzenie` jest w
`yolo_runtime_exclude_classes`, więc do treningu i tak nie wchodzi. **Priorytet: P3.**
Jedyny warunek: gdyby `urzadzenie` kiedyś weszło do YOLO, eksport musi przycinać bboxy do kadru.

---

## F1 [BŁĄD, KRYTYCZNY] — wyścig `selectPage` zapisuje graf pod cudzym page_id

**Uwaga:** F1 jest niezależny od F0 i nadal aktualny — ale kolejność naprawy to F0 → F1.
**Status: potwierdzone empirycznie** — patrz sekcja dowodowa w F0b.

---

## F1 [BŁĄD, KRYTYCZNY] — wyścig `selectPage` zapisuje graf pod cudzym page_id

**Plik:** `labeler/static/graph.js:2282` (`selectPage`), `:1485` (`flushAutoSave`), `:1649` (`buildPayload`)

`selectPage()` jest `async`, nie ma żadnego guardu re-entrancji, a wołane jest z `onclick` listy stron
(`:2046`, `:2058`) i ze strzałek klawiatury (`:2811`, `:2815`) — **bez `await`**.

Kolejność w środku:

```js
async function selectPage(pageId) {
  if (currentPageId && pageId !== currentPageId) await flushAutoSave({ force: true }); // (1)
  currentPageId = pageId;                                    // (2) natychmiast
  bgImage = await new Promise(...);                          // (3) ~setki ms dla PNG 6617x4678
  const data = await fetchJson(`/api/graph/${pageId}...`);   // (4)
  applyGraph(data);                                          // (5)
}
```

Scenariusz (dwa naciśnięcia strzałki w odstępie < czas ładowania PNG):

| Krok | Stan |
|---|---|
| wywołanie #1 `selectPage(B)` | zapis A ✅ → `currentPageId = B` → czeka na obraz B |
| wywołanie #2 `selectPage(C)` startuje w tym czasie | `flushAutoSave({force:true})` → `buildPayload()` |
| `buildPayload()` (`:1652`) | `page_id: currentPageId` = **B** |
| ale `graph.symbols` / `graph.lines` | wciąż **zawartość strony A** (`applyGraph` dla B jeszcze nie poszło) |
| `POST /api/graph/B` | body.page_id = B == URL → **walidacja przechodzi** |

**Wynik: `gt/…_B.json` zostaje nadpisany symbolami, liniami i `image_width/height` strony A.**

Cztery rzeczy czynią to gorszym, niż wygląda:

1. **`force: true`** w `flushAutoSave` — zapis leci nawet gdy `dirty === false`.
   **Samo przewijanie stron strzałkami przepisuje GT stron, których użytkownik nie dotknął.**
2. **Walidacja `page_id` na serwerze (`labeler/app.py:465`) jest w tym scenariuszu martwa** —
   frontend bierze `page_id` z `currentPageId`, a nie z danych, które faktycznie wczytał
   (`graph.page_id`, ustawiane w `applyGraph:1611`). Body zawsze zgadza się z URL-em, także wtedy,
   gdy treść pochodzi z innej strony.
3. **Guard `skipped_empty_overwrite` nie chroni** — nadpisujący graf nie jest pusty, tylko cudzy.
4. **`image_width/height` z `bgImage.naturalWidth`** (`:1653`) — jeśli late-resolve obrazu A nadpisze
   `bgImage`, do GT strony B trafia rozmiar obrazu A. Przy różnych rozmiarach stron = rozjazd skali
   całej strony (u nas wszystkie 6617×4678, więc na razie niewidoczne — mina na przyszłość).

To samo dotyczy `beforeunload` (`:2890`) — `keepalive` fetch z `buildPayload()`.

**Objaw dla użytkownika:** „widzę stronę B, a bboxy są z A". Widoczna połowa objawu to `applyGraph`
z opóźnionej odpowiedzi (`:2311` — brak sprawdzenia `data.page_id === currentPageId`, brak
`AbortController`). Niewidoczna połowa to zapis.

---

## F2 [BŁĄD] — niespójne rozwiązywanie `page_id` między endpointami

**Plik:** `labeler/app.py:445/454` vs `labeler/auto_draft.py:87`, `backend/paths.py:33`

| Endpoint | `resolve_page_id`? | Efekt dla `p028` |
|---|---|---|
| `GET/POST /api/graph/{id}` | **nie** | `gt/p028.json` — nowy, osobny plik |
| `POST /api/graph/{id}/auto-draft` | **tak** | `gt/22_A_153_…_p028.json` |
| `POST /api/graph/{id}/prefill` | nie | `gt/p028.json` |

Każde narzędzie/skrypt/curl używający skrótu `p028` na endpointach graph tworzy **drugi, równoległy GT**
tej samej strony. `GET` go potem zwraca zamiast prawdziwego. Dziś w `gt/` takich plików nie ma, ale
nic tego nie blokuje.

Dodatkowo `_DEFAULT_PAGE_PREFIX` (`paths.py:30`) na sztywno wskazuje Adamed AGV SA2 — po wejściu
drugiego projektu `p040` zmapuje się na cudzą stronę. **[RYZYKO] na później, nie teraz.**

---

## F3 [BŁĄD] — cache SQLite ma pierwszeństwo przed źródłem prawdy i nigdy nie kasuje sierot

**Plik:** `backend/db.py:161` (`load_schematic_graph`), `:190` (`rebuild_cache_from_gt`)

* `load_schematic_graph` czyta **najpierw cache**, do pliku sięga dopiero przy cache-miss.
* `rebuild_cache_from_gt` robi wyłącznie `INSERT … ON CONFLICT UPDATE` — **nie usuwa** wpisów,
  których nie ma już w `gt/`.

Konsekwencja: strona usunięta lub przemianowana w `gt/` **zostaje w cache na zawsze** i to cache jest
tym, co labeler pokaże i co pójdzie do metryki. Po `git checkout` / hard-resecie `gt/` cache nadal
serwuje starą treść aż do restartu aplikacji. To pasuje do historii „po odzyskiwaniu bazy widzę stare/złe dane".

Drugi rozjazd w tym samym miejscu: `save_schematic_graph` zapisuje **plik** pod
`sanitize_page_id(page_id)`, a **cache** pod surowym `page_id` (`db.py:156` vs `:157`).
Dla dzisiejszych ID identyczne; dla ID ze spacją/ukośnikiem — dwa różne klucze.

---

## F4 [RYZYKO] — `PRAGMA journal_mode=WAL` nie działa i nikt się o tym nie dowie

**Plik:** `backend/db.py:27-32`

```python
try:
    conn.execute("PRAGMA journal_mode=WAL")
    ...
except sqlite3.DatabaseError:
    pass          # <- połknięte
```

Stan faktyczny w repo (zmierzony): `journal_mode = delete`, brak `-wal`, **leży hot journal
`data/schemagen.db-journal` (4616 B) z 2026-07-12** — ślad nieczystego zamknięcia. `PRAGMA journal_mode`
zwraca aktualny tryb jako wiersz; jeśli przełączenie się nie uda, SQLite **nie rzuca wyjątku**, tylko
zwraca stary tryb. Ten `except` niczego nie łapie, bo nie ma czego łapać.

To jest ten sam tryb pracy, w którym baza wcześniej padła (`malformed` → `tools/recover_db.py`).
Naprawa jest jednolinijkowa: sprawdzić zwrócony wiersz i zalogować, gdy `!= 'wal'`.

Osobno: obecna baza **nie ma nawet tabeli `schematic_graph`** (są `pages`, `annotations`,
`model_versions`, `tag_usage`). `init_db()` + `rebuild_cache_from_gt()` na starcie to odtworzy — czyli
niezmiennik „SQLite = cache odbudowywalny" **zadziałał zgodnie z projektem**. Dane nie zginęły.

---

## F5 [RYZYKO] — brak `Cache-Control` na endpointach GT

`GET /api/graph/{id}` i `GET /api/pages/{id}/image` nie ustawiają nagłówków. Dziś ratuje to
`?t=Date.now()` w `graph.js` (`:2306`, `:2310`), ale ochrona jest po stronie klienta i znika przy
każdym innym konsumencie (curl, skrypt, `beforeunload`).

---

## F6 [RYZYKO] — `GET /api/graph/{id}` na braku GT zwraca 200 z pustym grafem

**Plik:** `labeler/app.py:445-451`, `_empty_graph:419`

Frontend nie odróżnia „strona nieoznaczona" od „GT puste". W połączeniu z F1 pusty graf potrafi
wjechać na ekran w miejsce dobrej strony. Sam w sobie nie kasuje danych (guard działa), ale zaciemnia
diagnozę. Kandydat na 404 albo na jawne `"exists": false` w odpowiedzi.

---

## F7 [drobne]

* `labeler/app.py:492` — `upsert_page(page_id, f"{page_id}.png")` bez sprawdzenia, czy PNG istnieje:
  dowolny POST tworzy wpis strony-widmo na liście.
* `labeler/app.py:70` — `/legacy` (stary labeler v1) serwowany bez `no-cache`, w przeciwieństwie do `/`.
* `labeler/app.py:547` — `post_graph_auto_draft` robi `upsert_page(page_id, …)` surowym argumentem,
  podczas gdy zapis poszedł pod `resolve_page_id(page_id)` → wpis strony pod skrótem.

---

## Czego **nie** znaleziono (sprawdzone, czysto)

> Poniższe dotyczy **6 plików obecnych w `gt/`**. Nie mówi nic o 197 stronach z F0 — te nie były
> jeszcze sprawdzone pod kątem integralności (audyt widzi tylko ich liczniki, nie zawartość).

| Hipoteza z promptu | Wynik |
|---|---|
| `gt/_backup_2026-07-12/` wpada w glob `gt/*.json` | **Nie.** `Path.glob("*.json")` nie schodzi do podkatalogów. |
| `page_id` w pliku ≠ nazwa pliku | **0 przypadków** (6/6 zgodnych) |
| Duplikaty ID symboli / terminali / linii w stronie | **0** |
| Linie wskazujące na nieistniejący symbol | **0** |
| Bboxy poza kadrem strony | **0** |
| Utrata danych vs backup z 12.07 | **0** — `gt/` bit w bit zgodne z `gt/_backup_2026-07-12/` |
| Zapis GT nieatomowy | Nie — `gt_store.write_gt_json` = tmp w tym samym katalogu + `os.replace` + `fsync`. Poprawne. |
| Walidacja `page_id` body vs URL na POST | **Istnieje** (`app.py:465`) — ale nieskuteczna wobec F1, patrz wyżej |
| Prefill nadpisuje ręczne GT | Nie — `prefill_graph:109` rzuca `FileExistsError` → 409, a `runPrefill` nie wysyła `force` |
| Auto-draft nadpisuje ręczne GT | Nie — `save_auto_draft:88` sprawdza istniejący niepusty → `skipped_existing` → 409 |

**p031 (SCORE 0.00) i p034 (5.29) to nie korupcja:** p031 ma 1 symbol / 0 linii, p034 108 symboli / 0 linii.
Strony są po prostu niedokończone. Wykluczenie p031 ze średniej (`config/gt-eval.yaml`) jest zasadne.

---

## p040 — ROZSTRZYGNIĘTE (patrz F0)

**p040 jest w cache SQLite, nie ma go w `gt/`.** Praca nie zginęła — nigdy nie została wyeksportowana
do źródła prawdy. Poniższa sekcja to zapis rozumowania z klonu ZW (baza pusta), zostawiona dla historii.

### ~~Trop rozstrzygnięty częściowo~~ (nieaktualne)

* `git log --all --diff-filter=A -- 'gt/*p040*'` → **pusto. Plik nigdy nie wszedł do repo.**
* `data/raw/` na klonie ZW nie zawiera **żadnych PNG** — tylko `IEC60617.pdf`. Klon ZW nie może
  odtworzyć widoku labelera ani zweryfikować skali GT wobec obrazów.
* Wersje `gt/` = wersje backupu z 12.07 → nic nie zostało skasowane po drodze.

**Wniosek:** to nie jest kasowanie. Albo praca nad p040 nie została zapisana na dysk, albo została
zapisana na klonie Filipa i nie trafiła do commita/push. **[DO SPRAWDZENIA PRZEZ FILIPA]** na jego PC:

```powershell
dir gt\*p040*
git status --short gt/
git stash list
```

Jeśli plik tam jest — to zwykły brak commita. Jeśli go nie ma, a Filip pamięta zapis — wtedy F1 jest
też odpowiedzią na p040 (zapis poszedł pod page_id sąsiedniej strony).

---

## Tabela decyzyjna — Faza B

| # | Znalezisko | Ryzyko dla GT | Pewność | Koszt | Priorytet |
|---|---|---|---|---|---|
| **F0** | 197 stron GT tylko w niewersjonowanej bazie SQLite (w tym p040) | **Utrata całości pracy przy jednej awarii bazy** | **Wysoka** — zmierzone na PC Filipa | XS (skrypt gotowy) | **P0 — dziś** |
| **F1** | Wyścig `selectPage` → zapis grafu pod cudzym page_id (+ `force:true` przy braku zmian) | **Cicha korupcja GT** | **Wysoka** — kod czytany wprost, brak jakiegokolwiek guardu | S (~40 linii JS) | **P0** |
| **F3** | Cache SQLite wygrywa nad `gt/`; sieroty nigdy nie znikają | Serwowanie nieaktualnego GT do labelera i metryki | Wysoka | S | **P0** |
| **F2** | Niespójny `resolve_page_id` → możliwy drugi GT tej samej strony | Rozszczepienie źródła prawdy | Wysoka | S | **P1** |
| **F4** | WAL nie działa, błąd połknięty; hot journal w repo | Powtórka `malformed` | Wysoka (zmierzone) | XS | **P1** |
| **F5** | Brak `Cache-Control` na GT | Stary GT z cache przeglądarki | Średnia | XS | P2 |
| **F6** | 200 + pusty graf zamiast 404 | Mylące, nie niszczy | Wysoka | XS | P2 |
| **F7** | Drobne (`upsert_page`, `/legacy`, auto-draft) | Kosmetyka listy stron | Wysoka | XS | P3 |

Reguła z promptu (cichy zapis > błąd widoku) daje: **F0, potem F1 i F3.**

**F0 wywraca kryterium walidacji z promptu.** „`diff_gt_runtime` bez zmiany SCORE" zakładało, że GT
jest kompletne. Nie jest — baseline 21.50 liczony jest z 6 stron, podczas gdy oznaczonych może być
znacznie więcej. Po odzyskaniu sierot **baseline wymaga przeliczenia z definicji**, niezależnie od
tego, czy naprawa labelera cokolwiek ruszy. To nie jest regresja, tylko pierwszy pomiar na pełnych danych.

---

## Rekomendowany zakres Fazy C (do zatwierdzenia)

Przed czymkolwiek: `git tag gt-pre-025` + kopia `gt/` poza repo.

1. **F1a** — `buildPayload()` bierze `page_id` z `graph.page_id` (to, co faktycznie wczytano), nie z
   `currentPageId`. Wtedy serwerowe 400 z `app.py:465` zaczyna łapać ten błąd zamiast go przepuszczać.
2. **F1b** — token generacji w `selectPage` (`const gen = ++pageGen`) + `AbortController`; po każdym
   `await` sprawdzenie `if (gen !== pageGen) return;`. Dotyczy obrazu i fetchu grafu.
3. **F1c** — `applyGraph` odrzuca dane, gdy `data.page_id && data.page_id !== currentPageId`.
4. **F1d** — `saveGraph` przerywa, gdy `graph.page_id !== currentPageId` (pas i szelki wobec 1–3).
5. **F3a** — `rebuild_cache_from_gt()` kasuje wpisy cache spoza `gt/` (`DELETE … WHERE page_id NOT IN`).
6. **F3b** — `load_schematic_graph` czyta plik jako źródło prawdy, cache tylko gdy pliku nie ma
   (albo: cache z `mtime` pliku). Do decyzji — wariant „plik zawsze wygrywa" jest prostszy i zgodny
   z `CLAUDE.md`.
7. **F2** — `resolve_page_id` na **wszystkich** endpointach `/api/graph/*` albo na żadnym. Rekomendacja: na wszystkich.
8. **F4** — sprawdzić wynik `PRAGMA journal_mode` i ostrzec, gdy `!= wal`; usunąć martwy `except`.
9. **F5/F6** — `no-store` na endpointach GT; `"exists": bool` w odpowiedzi `GET /api/graph/{id}`.
10. **Testy regresji** (`labeler/tests/`): POST z niezgodnym `page_id` → 400; pusty graf nie nadpisuje
    niepustego; `rebuild_cache_from_gt` usuwa sierotę; `resolve_page_id` spójny na GET/POST/prefill/auto-draft.
    Wyścig A→B — test jednostkowy `buildPayload` po zmianie `currentPageId` bez `applyGraph`.

**Kryterium z promptu:** po naprawie `diff_gt_runtime` na 6 stronach **bez zmiany SCORE**.
Ponieważ audyt nie wykrył uszkodzeń w danych GT (F1 jest mechanizmem, nie zrealizowaną szkodą na
tych 6 stronach — pliki zgodne z backupem z 12.07), **SCORE nie powinien drgnąć**. Jeśli drgnie,
znaczy że zmiana w `load_schematic_graph` (F3b) odsłoniła rozjazd cache↔plik i baseline 21.50
wymaga przeliczenia.

---

## Załączniki

* `tools/audit_gt.py` — audyt read-only, `--json` / `--md`
* `sync/analysis/025-gt-integrity.md` — wynik A1 (wygenerowany)
