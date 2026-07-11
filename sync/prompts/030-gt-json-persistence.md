# 030 — GT jako pliki JSON w repo, SQLite = cache (Builder: Claude)

## Cel
Uczynić GT (grafy SchematicGraph) trwałym i przyjaznym gitowi. Każda strona = jeden
plik `gt/<page_id>.json`. Tabela SQLite `schematic_graph` staje się **cache**
odbudowywalnym z `gt/`. Uszkodzenie/wyzerowanie bazy = nie-zdarzenie (odbudowa z gita).

## Twarde zasady
- NIE zmieniaj kontraktu SchemaModel ani formatu `SchematicGraph.model_dump(mode="json", by_alias=True)`.
- Zachowaj istniejący guard: pusty graf nie nadpisuje niepustego (`skipped_empty_overwrite`).
- Zapis pliku ZAWSZE atomowo: tmp w tym samym katalogu + `os.replace`. Nigdy w miejscu.
- JSON czytelny: `indent=2`, `ensure_ascii=False`, klucze stabilne, końcówki LF.

## Zakres
1. `gt/` w repo (śledzony gitem). `data/schemagen.db` + `-wal/-shm/-journal` pozostają gitignore.
2. `backend/db.py` (lub nowy `backend/gt_store.py`):
   - `save_schematic_graph(page_id, payload)`: zapis atomowy do `gt/<page_id>.json`
     ORAZ upsert do cache SQLite. Guard empty-overwrite egzekwuj na podstawie pliku JSON,
     nie tylko bazy.
   - `load_schematic_graph(page_id)`: czytaj z cache; przy braku/rozjeździe — z `gt/<page_id>.json`.
   - `rebuild_cache_from_gt()`: skan `gt/*.json` → cache. Wołane na starcie aplikacji
     (labeler startup) tak, by świeża/uszkodzona baza sama się odbudowała.
3. Migracja jednorazowa `tools/export_gt_to_json.py`: obecne wiersze `schematic_graph`
   (aktywna baza) → `gt/*.json`. Uruchom i zacommituj powstałe pliki `gt/`.
4. Sanityzacja nazwy pliku: page_id waliduj do `[A-Za-z0-9._-]+`; inne znaki → `_`.
   Mapowanie odwracalne nie jest wymagane (page_id już są bezpieczne).

## Testy (pytest)
- round-trip: save → plik JSON istnieje i parsuje; load zwraca to samo.
- rebuild: wyczyść tabelę cache, `rebuild_cache_from_gt()`, load działa.
- guard: pusty payload nie nadpisuje niepustego pliku (chyba że allow_empty).
- atomowość: brak połowicznych plików przy błędzie (symulacja wyjątku w trakcie zapisu).

## Po zakończeniu
- `pytest backend/tests labeler/tests`
- Raport w `sync/zw-to-filip.md` (pliki, decyzje, wynik testów).
- `sync/commit-message.txt` = jedna linia `[Claude] 030 GT jako JSON + cache + migracja`.
