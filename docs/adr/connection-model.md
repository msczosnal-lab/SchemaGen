# ADR: model połączeń — typy Connection vs grafika

**Status:** Proposed — do review Filip
**Data:** 2026-06-27
**Deciderzy:** Filip (Cursor), ZW (Claude)
**Powiązane:** [`device-block-stub.md`](device-block-stub.md), [`schematic-interpretation.md`](../schematic-interpretation.md)

## Kontekst

Po wdrożeniu filaru połączeń (GraphBuilder 004 + sito + net-builder) walidacja wzrokowa na p040/p035 ujawniła, że **model „co jest połączeniem" jest niedospecyfikowany** — w jednej sesji dwa razy źle potraktowałem realne sygnały:

1. **Mostki w listwie** (poziome odcinki wewnątrz listwy złączek) zostały skasowane przez sito „wnętrza bbox" jako tabelka. To **realne połączenia** — łączą złączki, nie kable. Inny typ niż kabel device↔device.
2. **Niebieskie (`bus`)** myli realną szynę zbiorczą z obramówką urządzenia, której sito nie złapało.

Siły w grze:
- Klepanie heurystyk bez taksonomii → ciągłe przeróbki (regresja mostków to dowód).
- Brak modelu terminali (device_block etap 2 jeszcze nie zrobiony) — nie wiemy, *gdzie* są punkty podłączenia.
- Kontrakt `SchemaModel` (Pydantic) nie powinien się zmieniać bez zgody; rozszerzenia enuma są OK.

## Decyzja

Ustalamy **taksonomię połączeń** i **granicę Connection vs grafika**, oraz minimalne mapowanie na `SchemaModel`. Implementacja w krokach (ten ADR to model; kod osobno).

### 1. Taksonomia połączeń

| Typ | Co łączy | Rysunek | Reprezentacja |
|-----|----------|---------|---------------|
| **kabel** | symbol ↔ symbol (device↔device) | linia `wire` między urządzeniami | `Connection` `kind ∈ {power, signal, pe, control}` |
| **mostek (terminal-link)** | złączka ↔ złączka w listwie/bloku | krótki odcinek wewnątrz `device_block` łączący terminale | `Connection` `kind = "link"` (NOWY) |
| **szyna / potencjał** | net wieloodczepowy (≥3 punkty) | długa linia `bus` + odczepy | `Connection.potential = net_k` (już jest); nie nowy `kind` |

### 2. Co JEST połączeniem, co NIE

**Connection:** net `wire`/`bus` łączący ≥2 punkty podłączenia (symbol lub terminal).

**Grafika (NIGDY Connection):** `frame` (obrys urządzenia), `leader` (linia do tekstu), `crossing` bez kropki, **tabelka** (gęsta siatka linii wewnątrz bbox, bez funkcji łączenia).

**Kluczowa korekta:** linia wewnątrz bbox **nie jest automatycznie grafiką**. Rozróżnienie:
- łączy dwa punkty podłączenia (przeciwległe strefy terminali) → **mostek** (Connection),
- część gęstej siatki równoległych krótkich linii → **tabelka** (grafika).

### 3. Mapowanie na SchemaModel

- `ConnectionKind`: **dodać `"link"`** → `{power, signal, pe, control, link, other}`.
- `Connection.potential`: `net_k` dla szyn (bez zmian).
- `Connection.from/to`: na teraz `component_id`. Docelowo (device-block etap 2) `component_id:terminal_id` — zgodnie z [`device-block-stub.md`](device-block-stub.md).

## Opcje rozważane (jak modelować mostki / naprawić regresję)

### Opcja A — typ symbolu rozstrzyga (pragmatyczna, TERAZ)
Sito „wnętrza bbox" demotuje linie **tylko wewnątrz prostych symboli** (bezpiecznik, stycznik — tam linia wewnętrzna = obrys/szum). Wewnątrz `device_block` (listwa, moduł — z palety `symbol-palette.yaml`) **nie demotuje** — odcinki traktuje jako kandydatów na mostki (`kind="link"`).

| Wymiar | Ocena |
|--------|-------|
| Złożoność | Niska |
| Koszt | Mały (typ z palety już mamy) |
| Poprawność | Średnia — tabelki wewnątrz device_block dalej mogą przejść jako link |
| Zależności | Typ `device_block` musi być w detekcji/palecie |

**Plusy:** cofa regresję, wykorzystuje istniejący podział symbol/device_block.
**Minusy:** nie odróżnia mostka od tabelki *wewnątrz* device_block.

### Opcja B — model terminali (DOCELOWA, etap 2)
`terminals[]` w bboxie (device-block etap 2). Mostek = odcinek między dwoma terminalami; tabelka = nie trafia w terminale.

| Wymiar | Ocena |
|--------|-------|
| Złożoność | Wysoka |
| Koszt | Duży — tryb terminali w labelerze + GT |
| Poprawność | Wysoka |
| Zależności | device-block etap 2 |

**Plusy:** rozstrzyga mostek vs tabelka jednoznacznie.
**Minusy:** za wcześnie — blokuje na pracy labelera/GT.

### Opcja C — heurystyka tabela-vs-mostek (geometria)
Odróżnij gęstą siatkę (≥N równoległych krótkich linii blisko siebie = tabela) od pojedynczej poprzeczki (= mostek).

| Wymiar | Ocena |
|--------|-------|
| Złożoność | Średnia |
| Koszt | Średni |
| Poprawność | Średnia — krucha na realnych skanach |
| Zależności | Brak |

**Plusy:** bez zmian modelu, działa też tam gdzie typ symbolu niepewny.
**Minusy:** progi do strojenia, łamliwa.

## Analiza trade-off

Najważniejszy konflikt: **poprawność teraz vs nakład**. B jest poprawne, ale wymaga pracy GT/labelera (etap 2) — blokuje. A jest tanie i cofa regresję, ale nie rozdziela mostka od tabelki w device_block. C łata tę lukę geometrycznie, kruche.

Rekomendacja: **A teraz + C jako sito drugiego rzędu wewnątrz device_block**, **B jako cel docelowy** (gdy ruszy tryb terminali). To cofa aktywną regresję małym kosztem, a gęste tabelki odsiewa heurystyką C, nie kasując pojedynczych mostków.

## Konsekwencje

- **Łatwiejsze:** mostki w listwie przestają znikać (cofnięta regresja); `kind="link"` daje czytelny sygnał w grafie; szyny mają `potential`.
- **Trudniejsze:** sito musi znać typ symbolu (device_block vs prosty) — wymaga typu w detekcji/palecie przy budowie grafu.
- **Do rewizji:** gdy ruszy model terminali (B), `from/to` → `component_id:terminal_id`, a heurystyki A/C stają się zbędne dla device_block.
- **Bus vs ramka (problem C z feedbacku):** częściowo poza tym ADR — `bus` jako rola geometryczna zostaje, ale ramka dłuższa niż bbox wymaga osobnego sygnału (np. domknięty prostokąt). Osobny, mniejszy temat.

## Action Items

1. [ ] Akceptacja taksonomii i `kind="link"` (Filip).
2. [ ] `ConnectionKind` += `"link"` w `backend/models/schema.py` (po akceptacji — zmiana kontraktu).
3. [ ] Sito: nie demotuj wnętrza `device_block`; demotuj wnętrze prostych symboli (Opcja A).
4. [ ] Heurystyka C (tabela = gęsta siatka) jako sito drugiego rzędu wewnątrz device_block.
5. [ ] net-builder: odcinki wewnątrz device_block → `Connection kind="link"`.
6. [ ] (etap 2, osobny prompt) tryb terminali w labelerze → Opcja B.
7. [ ] (osobno) bus vs ramka: sygnał domkniętego prostokąta.
