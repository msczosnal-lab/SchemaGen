# EPLAN SchemaGen

Narzędzie do automatycznego generowania schematów elektrycznych w EPLAN Electric P8 na podstawie konfiguracji XML.

## Dokumentacja projektu

| Dokument | Opis |
|----------|------|
| [docs/ROADMAP.md](docs/ROADMAP.md) | Ścieżka rozwoju — fazy 0–6 |
| [docs/session-log.md](docs/session-log.md) | Dziennik sesji (ostatni wpis = następny krok) |
| [docs/project-context.txt](docs/project-context.txt) | Kontekst techniczny, makra, MVP |
| [docs/eplan-data-paths.txt](docs/eplan-data-paths.txt) | Ścieżki instalacji EPLAN |

## Struktura repozytorium

```
├── .cursor/rules/     # Reguły dla agenta Cursor
├── config/            # XML konfiguracji (901_Drive_Design.xml)
├── docs/              # Dokumentacja, dziennik, notatki API
└── scripts/           # Kod źródłowy skryptów C# (kopiuj do EPLAN po testach)
```

## Szybki start w Cursor

1. Otwórz ten folder jako projekt w Cursor.
2. Sprawdź [docs/session-log.md](docs/session-log.md) — ostatni wpis = co robić teraz.
3. **Nowy chat** → tryb **Agent** → kontekst: `@docs/project-context.txt` `@docs/eplan-data-paths.txt`
4. Po zmianach: skopiuj `scripts/*.cs` do  
   `C:\Users\Public\EPLAN\Data\Skrypty\Schemagen\`
5. Testuj w EPLAN: **Narzędzia → Skrypty**.

## Aktualny krok

**Sesja 1.1** — napisać `scripts/SchemaGen_MVP.cs` otwierający `Hello_world.edb`.  
Szczegóły: [docs/ROADMAP.md](docs/ROADMAP.md) (Faza 1, sesja 1.1).
