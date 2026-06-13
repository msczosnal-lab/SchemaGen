# Skrzynka: Filip → ZW

> Pisze **tylko Filip** (Cursor). ZW czyta na starcie sesji i nie edytuje tego pliku.
> Najnowsze wpisy na górze.

---

## 2026-06-13 [Filip]

Temat: MA1+MA1 nadal — infrastruktura handoff + dual-pass w MVP (test EPLAN u Filipa)
Kontekst: build OK, MVP + probe TryRenumber_MA — silniki +B2/+B4 nadal -MA1/-MA1. Cursor (Filip) dodał: `sync/prompts/1.7g-ma-global-dt.md`, `Start-ClaudeSession.cmd/.ps1`, dual-pass z `numbering-rules.xml` w `SchemaGen_MVP.cs`, STARTVALUE/STEPVALUE w akcji. Jeśli test nadal MA1+MA1 → Plan B (FUNC_COUNTER) po stronie ZW.
Do zrobienia po stronie ZW: opcjonalnie Plan B jeśli Filip potwierdzi brak MA2 po teście; w przeciwnym razie — nic. Start sesji: `Start-ClaudeSession.cmd` + `@sync/prompts/1.7g-ma-global-dt.md`
Do zrobienia po stronie Filip: `build_addin.ps1`, skopiuj MVP + `config/numbering-rules.xml` → `Skrypty\Schemagen\config\`, przeładuj DLL, świeży Hello_world, uruchom MVP, sprawdź MA1+MA2 i `output/renumber-devices.json` Commit: (auto GitSync po push)