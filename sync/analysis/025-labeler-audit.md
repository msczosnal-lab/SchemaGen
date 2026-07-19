# 025 — audyt labelera (Faza A + B)

**Data:** 2026-07-19 · **Model:** Opus 4.8 · **Zakres:** `labeler/`, `backend/db.py`, `backend/gt_store.py`, `backend/paths.py`
**Bez zmian w kodzie produkcyjnym.** Dodany wyłącznie `tools/audit_gt.py` (read-only).

---

## Wniosek jednozdaniowy

**Dane GT są zdrowe. Narzędzie, które je zapisuje — nie.** Znaleziono mechanizm, który przy szybkiej
zmianie strony **zapisuje graf strony A pod page_id strony B**, i robi to nawet gdy użytkownik niczego
nie edytował. To dokładnie objaw zgłoszony przez Filipa i jest to cicha korupcja GT, nie błąd wyświetlania.

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

## p040 — trop rozstrzygnięty częściowo

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
| **F1** | Wyścig `selectPage` → zapis grafu pod cudzym page_id (+ `force:true` przy braku zmian) | **Cicha korupcja GT** | **Wysoka** — kod czytany wprost, brak jakiegokolwiek guardu | S (~40 linii JS) | **P0** |
| **F3** | Cache SQLite wygrywa nad `gt/`; sieroty nigdy nie znikają | Serwowanie nieaktualnego GT do labelera i metryki | Wysoka | S | **P0** |
| **F2** | Niespójny `resolve_page_id` → możliwy drugi GT tej samej strony | Rozszczepienie źródła prawdy | Wysoka | S | **P1** |
| **F4** | WAL nie działa, błąd połknięty; hot journal w repo | Powtórka `malformed` | Wysoka (zmierzone) | XS | **P1** |
| **F5** | Brak `Cache-Control` na GT | Stary GT z cache przeglądarki | Średnia | XS | P2 |
| **F6** | 200 + pusty graf zamiast 404 | Mylące, nie niszczy | Wysoka | XS | P2 |
| **F7** | Drobne (`upsert_page`, `/legacy`, auto-draft) | Kosmetyka listy stron | Wysoka | XS | P3 |

Reguła z promptu (cichy zapis > błąd widoku) daje: **F1 i F3 przed wszystkim innym.**

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
