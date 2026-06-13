# sync/ — magistrala koordynacji dwóch agentów

Repo SchemaGen jest współdzielone przez dwa komputery (**ZW** = Cowork/Claude, **Filip** = Cursor IDE).
`GitSyncDaemon.ps1` synchronizuje pliki w obie strony co ~10 s. Ten katalog to warstwa
**komunikacji między modelami** — kontekst, zadania, statusy.

## Zasada bezkonfliktowa (obowiązkowa)

Auto-sync co 10 s = każdy plik edytowany przez **dwie strony naraz** powoduje konflikt rebase.
Dlatego pliki są **jednokierunkowe — jeden autor na plik**:

| Plik | Pisze | Czyta |
|------|-------|-------|
| `zw-to-filip.md`   | tylko ZW    | Filip |
| `filip-to-zw.md`   | tylko Filip | ZW    |
| `TASKS.md`         | obaj — **tylko dopisywanie** (append), nigdy edycja cudzych linii | obaj |
| `.status-*.json`   | daemon danej maszyny | człowiek/agent |

Reguły:
1. **Nigdy nie edytuj pliku, którego nie jesteś autorem.** Odpowiedź = wpis we własnej skrzynce.
2. `TASKS.md` — wyłącznie **dopisuj** nowe linie na końcu. Status zadania zmieniasz dodając nowy wpis, nie nadpisując stary.
3. Kod projektu (`scripts/`, `config/`, …) edytuje **jedna strona naraz**. Zanim ruszysz plik kodu, ogłoś to w swojej skrzynce; jeśli druga strona właśnie go trzyma — poczekaj.

## Start sesji (każdy agent)

1. Przeczytaj skrzynkę od drugiej strony (`filip-to-zw.md` lub `zw-to-filip.md`).
2. Przeczytaj `TASKS.md` — co jest OPEN.
3. Pracuj. Po zmianie dopisz krótki wpis do własnej skrzynki + do `TASKS.md`.

## Format wpisu (skrzynka)

```
## 2026-06-13 14:32 [ZW]
Temat: <jedno zdanie>
Kontekst: <co zrobiłem / czego potrzebuję>
Do zrobienia po stronie Filip: <konkret albo "—">
Commit: <hash jeśli dotyczy>
```
