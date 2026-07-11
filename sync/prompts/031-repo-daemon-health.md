# 031 — Zdrowie repo + bezpieczny sync + backup (Cursor, na maszynie z .git/daemonem)

## Kontekst
Dzisiejsze awarie (uszkodzony indeks gita, packed-refs, malformed SQLite, brak pusha,
truncation plików) mają wspólne źródło: **GitSyncDaemon co 5 s kasował wszystkie
`*.lock` i skanował folder z żywą bazą**. To wyścig z gitem i z zapisem SQLite.

## Zadania
1. **Napraw repo teraz** (daemon wyłączony):
   - `git status` — jeśli `unknown index entry format`: `del .git\index` → `git read-tree HEAD` → `git add -A`.
   - `git fsck --full` — usuń/odbuduj uszkodzone refy jeśli trzeba.
   - Zacommituj i wypchnij zaległe zmiany (w tym labeler v61, jeśli nie w HEAD).
2. **Przerób GitSyncDaemon — koniec kasowania locków na ślepo:**
   - NIGDY `Remove-Item .git\**\*.lock -Force`. Zamiast tego: usuwaj lock TYLKO gdy
     starszy niż 60 s ORAZ proces-właściciel nie żyje.
   - Jeden mutex/flaga „git w toku" — nie odpalać drugiej operacji równolegle.
   - Nie dotykać `data/` ani plików `.db*` (żadnego add/scan tam).
   - Commit+push tylko przy nazwanym wpisie w `sync/commit-message.txt`; pull `--rebase --autostash`.
3. **Gitignore/układ:** upewnij się, że `data/schemagen.db` + `-wal/-shm/-journal` są ignorowane,
   a nowy katalog `gt/` (z zadania 030) jest ŚLEDZONY.
4. **Backup bazy:** Harmonogram zadań Windows — codziennie kopiuj `data\schemagen.db`
   → `data\backups\schemagen-YYYYMMDD.db` (trzymaj ostatnie ~14). Dodatkowo kopia przy starcie labelera.
5. **OneDrive/sync systemowy:** jeśli repo leży pod OneDrive/kopią w chmurze — wyklucz folder
   `data\` z synchronizacji (żywa baza nie może być dotykana przez zewnętrzny sync).
6. **Review** PR-a z zadania 030 (GT↔JSON): czy zapis atomowy, guard zachowany, cache odbudowywalny.

## Definicja ukończenia
- `git fsck` czysty, push działa.
- Daemon nie kasuje aktywnych locków (test: uruchom `git rebase` ręcznie i sprawdź, że daemon nie psuje).
- Codzienny backup w `data\backups\`.

## 7. Push niezależny od daemona (GitHub)
Cel: żeby wypchnięcie zmian nie zależało od kruchego lokalnego daemona ani od uprawnień do `.git`.
- Skonfiguruj `git remote` na HTTPS z tokenem (PAT) lub SSH-key, tak by `git push` działał ręcznie
  z każdej maszyny bez daemona: `git push origin main` po commicie musi przechodzić samodzielnie.
- Daemon zostaje TYLKO do wygody (pull co jakiś czas + commit na nazwany message), ale NIE jest
  jedyną drogą pusha. Gdy daemon padnie, `git push` ręczny zawsze działa.
- Opcjonalnie (po stronie Claude/Cowork): autoryzuj konektor GitHub (plugin engineering) na claude.ai,
  wtedy Claude może tworzyć commity/PR-y przez API GitHuba — z pominięciem lokalnego `.git`.
  Instrukcja: `sync/GITHUB-KONEKTOR.md`.
