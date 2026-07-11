# Autoryzacja konektora GitHub (dla Claude / Cowork)

Po co: żeby Claude mógł commitować/pushować i tworzyć PR-y przez **API GitHuba**,
z pominięciem lokalnego `.git` i kruchego GitSyncDaemona (to on dziś blokował push).

## Kroki (na claude.ai, w przeglądarce)
1. Zaloguj się na claude.ai (to samo konto, na którym działa Cowork).
2. Wejdź w **Ustawienia → Konektory** (Settings → Connectors; u części kont pod
   „Capabilities"). Konektor **GitHub** jest częścią pluginu **engineering**.
3. Kliknij **Connect / Authorize** przy GitHub → przejdź OAuth GitHuba.
4. Nadaj dostęp do konta/organizacji i **do repozytorium `SchemaGen`**
   (wybierz „only select repositories" i wskaż to repo — minimalny zakres).
5. Zatwierdź. Po chwili w Cowork pojawią się narzędzia GitHub (commit, PR, itp.).

## Weryfikacja
- W nowej sesji Cowork poproś Claude: „wypchnij commit przez GitHub" — powinien użyć
  narzędzi GitHub, nie lokalnego gita.

## Zakres/bezpieczeństwo
- Daj dostęp tylko do repo `SchemaGen`, nie do całego konta.
- To NIE zastępuje git na maszynie — to druga, niezależna droga pushowania,
  na wypadek gdy daemon/`.git` znów się posypie.
- Nie potrzebujesz żadnego innego MCP (filesystem, bazy) — Cowork ma już pliki lokalnie.
