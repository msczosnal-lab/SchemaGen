# Start sesji Claude — SchemaGen Builder

> **Zawsze nowa sesja.** Nie wznawiaj starego linku z `session_…` — każda implementacja = świeży start.

## Jak uruchomić (PC ZW)

1. `Start-GitSync.cmd Claude` — poczekaj na pull (repo aktualne).
2. Otwórz **[claude.ai/code](https://claude.ai/code)** → **New session** (nie stara sesja z historią).
3. Wklej prompt z [`sync/PROMPT-CLAUDE-002-OCR.md`](PROMPT-CLAUDE-002-OCR.md) (filar tekst: PaddleOCR) **lub** skrót „kolejne zadanie”.
4. Claude czyta pliki lokalne z repo — nie musisz ręcznie wklejać promptów z `sync/prompts/`.

## Prompt startowy (kopiuj całość)

```
SchemaGen — Builder (Claude Cowork). Nowa sesja implementacji.

Projekt: offline rozpoznawanie schematów elektrycznych. Python 3.11+, FastAPI, YOLO ONNX, RTX 2080.
Zakaz cloud API w runtime: backend/recognize/, train/, labeler/.

Przed implementacją wczytaj pliki w tej kolejności:
1. sync/KOLEJNE-ZADANIE.md          — aktywne zadanie (źródło prawdy)
2. sync/filip-to-zw.md              — najnowszy wpis na górze pliku
3. docs/claude-cowork-instructions.md
4. sync/prompts/NNN-*.md              — plik wskazany w KOLEJNE-ZADANIE.md

Twoja rola (Builder):
- Implementuj NotImplementedError i COWORK_TASK.
- Nie zmieniaj bez wyraźnej zgody w prompcie: sygnatur backend/protocols/, kontraktu SchemaModel JSON, modeli Pydantic (GraphicLine, SchemaModel).

Zasady domenowe:
- GraphicLine ≠ Connection — linia na rysunku to nie kabel logiczny.
- Kolory semantyczne: config/semantic-colors.yaml.
- Tylko role wire/bus → kandydaci na Connection w GraphBuilder.

Po zakończeniu:
1. pytest backend/tests labeler/tests
2. python -m backend.cli validate schema/fixtures/page1_expected.json
3. Wpis w sync/zw-to-filip.md (co zrobione, pliki, wynik testów)
4. sync/commit-message.txt = jedna linia [Claude] opis (tylko jeśli plik pusty lub już zaczyna się od [Claude])
5. GitSync: Start-GitSync.cmd Claude

Zacznij: przeczytaj KOLEJNE-ZADANIE.md, podsumuj aktywny prompt i plan kroków, potem implementuj.
```

## Skrót (gdy sesja już zna repo)

```
kolejne zadanie
```

Claude wtedy czyta: `sync/KOLEJNE-ZADANIE.md` → `sync/filip-to-zw.md` → aktywny prompt.

## Po zakończeniu pracy

| Plik | Co wpisać |
|------|-----------|
| `sync/zw-to-filip.md` | Raport: pliki, testy, uwagi |
| `sync/commit-message.txt` | `[Claude] …` — jedna linia |
| `sync/TASKS.md` | Opcjonalnie: wiersz ze statusem DONE |

Cursor review → ewentualnie `## Poprawka (runda N)` w aktywnym pliku `sync/prompts/`.

## Dlaczego nowa sesja?

- Stara sesja ma kontekst z poprzednich promptów — ryzyko pomyłek (np. 002 zamiast 003).
- `KOLEJNE-ZADANIE.md` jest jedynym źródłem prawdy co jest **AKTYWNE**.
- GitSync synchronizuje kod i sync/ między PC Filip a PC ZW.
