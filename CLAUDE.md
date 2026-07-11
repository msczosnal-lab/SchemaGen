Za każdym razem, gdy wprowadzasz zmianę w kodzie uzupełnij nazwę commita, aby wysłać ją na komputer główny

## Niezmienniki danych GT (nie łamać)
- Źródłem prawdy GT są pliki `gt/<page_id>.json` w repo (wersjonowane gitem). SQLite `schematic_graph` to tylko cache odbudowywalny z `gt/`.
- Każdy zapis GT: atomowo (tmp + os.replace), nigdy w miejscu. Na starcie odbuduj cache z `gt/`.
- Pusty graf (0 symboli i 0 linii) NIE nadpisuje istniejącego niepustego (guard `skipped_empty_overwrite`, `allow_empty=true` by wymusić).
- `data/schemagen.db` + `-wal/-shm/-journal` są gitignore. Nigdy nie trzymać jedynej kopii GT w binarnej bazie.
- Baza: WAL + busy_timeout. Backup bazy poza tym i tak jest w `gt/` (git).
