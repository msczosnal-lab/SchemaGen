# Zadanie 002: labeler — linie graficzne + kolory semantyczne

**Status:** OPEN — po akceptacji 001 i 003; priorytet po 008a lub równolegle  
**Model:** Sonnet, effort High  
**Pliki:** `labeler/static/app.js`, `labeler/static/index.html` (jesli trzeba UI), `labeler/app.py` (tylko jesli brakuje pol w API)

## Kontekst wazny

**Linia na schemacie ≠ polaczenie elektryczne.** Linia moze byc:
- kablem (`wire`),
- szyna (`bus`),
- obrysem urzadzenia (`device_stroke`) — np. falownik fioletowy,
- ramka obudowy (`frame`),
- linia przerywana (`dash`),
- crossing bez polaczenia (`crossing`).

Kolory semantyczne: `config/semantic-colors.yaml` — uzytkownik definiuje grupy (kable czarne, falownik fioletowy, silnik niebieski…).

Model danych juz gotowy:
- `backend/models/label.py` → `LineAnnotation`, `LabelRecord.lines`
- Eksport: `labeler/export.py` → `SchemaModel.graphic_lines`

## Implementuj

1. **Tryb polyline** (przelacznik bbox / linia):
   - klik = kolejny punkt, Enter lub double-click = zakoncz linie
   - Esc = anuluj biezaca linie
2. **Wybor roli linii:** wire, bus, device_stroke, frame, dash, crossing, leader, other
3. **Wybor semantic_group** z listy grup z `GET /api/semantic-groups` (dodaj endpoint czytajacy YAML) lub hardcoded z config
4. **Eyedropper:** klik na piksel obrazu → sugestia `semantic_group` przez prosty match hex (albo wywolaj logike z `backend/colors/palette.py` po stronie serwera — endpoint `/api/match-color?hex=...`)
5. Rysowanie istniejacych linii po zaladowaniu strony
6. Del — usuwa zaznaczona linie
7. Zapis w `LabelRecord.lines` przez POST `/api/annotations`

## Opcjonalnie (jesli czas)

- Osobny tryb **Connection logic** — reczne `from`/`to` miedzy terminalami (nie mylic z rysowaniem linii)

## Test akceptacji

```
pytest labeler/tests
# reczny: 1 linia wire (czarna), 1 device_stroke (fiolet), eksport → schema.json ma graphic_lines
```

## Zakazy

- Nie traktuj kazdej linii jako Connection
- React, npm, cloud API

## Po ukonczeniu

1. `sync/commit-message.txt` = `[Claude] labeler: linie i kolory (prompt 002)`

## Poprawka (runda N)

*(Cursor)*
