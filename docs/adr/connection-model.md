# ADR: model połączeń — typy Connection, linia opisu kabla, granica grafiki

**Status:** Proposed — do review Filip
**Data:** 2026-06-27
**Deciderzy:** Filip (Cursor), ZW (Claude)
**Powiązane:** [`device-block-stub.md`](device-block-stub.md), [`schematic-interpretation.md`](../schematic-interpretation.md)

## Kontekst

Walidacja filaru połączeń (GraphBuilder 004 + sito + net-builder) na p040/p035 pokazała, że model „co jest połączeniem" jest niedospecyfikowany. Decyzje Filipa po przeglądzie nakładek:

1. **Bez osobnego typu „szyna/bus".** Linia z wieloma odczepami to **jeden kabel (potencjał) + odczepy**, nie odrębny typ. (Przy okazji znika problem „niebieskie = potencjał albo ramka" — nie ma już roli `bus`.)
2. **Nowy typ linii `cable_marker`** — przerywana, która **przecina** kable; ma etykietę literową na końcu: nazwa/typ kabla i/lub średnice przewodów. To **adnotacja opisująca kable, nie połączenie**.
3. **Mostki w listwie** (regresja z tej sesji) — realne połączenia złączka↔złączka, inny typ niż kabel. Sito niesłusznie je kasowało.

Siły: brak modelu terminali (device_block etap 2); kontrakt `SchemaModel` (Pydantic) zmieniamy świadomie (rozszerzenia enuma OK, usuwanie wartości = ryzyko).

## Decyzja

### 1. Typy POŁĄCZEŃ (Connection)

| Typ | Co łączy | Reprezentacja |
|-----|----------|---------------|
| **kabel** | symbol ↔ symbol | `Connection` `kind ∈ {power, signal, pe, control}` |
| **mostek (terminal-link)** | złączka ↔ złączka w listwie/bloku | `Connection` `kind = "link"` (NOWY) |

**Szyna NIE jest osobnym typem.** Net z wieloma odczepami = jeden kabel = wspólny `potential` (`net_k`), a każdy odczep to `Connection` z tym potencjałem. Net-builder już to robi (gwiazda + `potential`).

### 2. Rola linii `cable_marker` (NOWA) — opis kabla

**Co:** linia **przerywana** przecinająca jeden lub więcej kabli (`wire`), z **etykietą na końcu** (OCR): nazwa/typ kabla, średnice żył.

**Czym jest:** **adnotacja**, NIGDY `Connection`. Tworzy relację: `cable_marker` → kable, które przecina + dane z etykiety (nazwa/typ/średnica).

**Wartość:** z tego powstaje **lista kablowa** prosto ze schematu (nazwa kabla + przekrój + które żyły obejmuje). Łączy się z domeną listy kablowej (skill `naftoport-lista-kabli`).

### 3. Granica: co JEST połączeniem, co NIE

**Connection:** net `wire` łączący ≥2 punkty podłączenia (symbol/terminal).
**Grafika / adnotacja (NIGDY Connection):** `frame` (obrys), `cable_marker` (opis kabla), `leader` (linia do tekstu), `crossing` bez kropki, **tabelka** (gęsta siatka wewnątrz bbox).
**Korekta regresji:** linia wewnątrz bbox nie jest automatycznie grafiką — mostek terminal↔terminal to połączenie; tylko gęsta siatka = tabelka.

### 4. Mapowanie na SchemaModel

| Pole | Zmiana | Ryzyko |
|------|--------|--------|
| `ConnectionKind` | += `"link"` | Niskie (additive) |
| `LineRole` | += `"cable_marker"` | Niskie (additive) |
| `LineRole` `"bus"` | **deprecated** — klasyfikator przestaje ją nadawać (długie linie → `wire`); wartość zostaje w enumie dla wstecznej zgodności | Niskie (nie usuwamy z Literal) |
| `Connection.potential` | szyna/odczepy = `net_k` (bez zmian) | — |
| `Connection.from/to` | teraz `component_id`; docelowo `component_id:terminal_id` (device-block etap 2) | — |

## Opcje rozważane

### Mostek terminal-link — jak odróżnić od tabelki wewnątrz bbox

**A — typ symbolu rozstrzyga (TERAZ).** Sito demotuje wnętrze tylko *prostych* symboli; wnętrza `device_block` (listwa/moduł z palety) nie kasuje → odcinki = kandydaci na `link`. Tanie, ale tabelka w device_block może przejść jako link.

**B — model terminali (DOCELOWA, etap 2).** `terminals[]` w bboxie; mostek = odcinek między terminalami. Poprawne, ale wymaga trybu terminali w labelerze + GT.

**C — heurystyka tabela-vs-mostek.** Gęsta siatka ≥N równoległych krótkich = tabela; pojedyncza poprzeczka = mostek. Bez zmian modelu, krucha.

**Rekomendacja:** A + C teraz, B docelowo.

### cable_marker — jak wykryć

**Sygnały:** (1) styl **przerywany** (`dash`), (2) **przecina** ≥1 net `wire` (krzyżuje, nie kończy się na nim), (3) **etykieta OCR na końcu** (litera/symbol + ewent. liczba = średnica).

**Heurystyka v1:** linia dashed, której ścieżka krzyżuje ≥1 wire (przecięcie w środku, nie na końcu), a w pobliżu jednego z końców jest tekst OCR → `cable_marker`; przypnij etykietę i listę przeciętych nettów. Bez OCR na końcu → zostaw `dash` (niepewne).

## Trade-off

- Usunięcie `bus` upraszcza model i kasuje błędne niebieskie, kosztem utraty geometrycznego sygnału „długa linia = szyna" — ale szyna i tak wychodzi z net-buildera (potencjał), więc strata pozorna.
- `cable_marker` zależny od OCR etykiety — przy braku OCR część markerów zostanie jako `dash`. Akceptowalne (recall OCR to osobny temat).
- Mostki: A+C to kompromis poprawność/nakład; B usuwa zgadywanie, ale później.

## Konsekwencje

- **Łatwiejsze:** prostszy model (kabel + mostek; szyna = potencjał); znikają błędne `bus`; `cable_marker` daje listę kablową; mostki przestają znikać.
- **Trudniejsze:** sito musi znać typ symbolu (device_block vs prosty); detekcja `cable_marker` zależy od OCR i geometrii przecięć.
- **Do rewizji:** przy modelu terminali (B) `from/to` → `component_id:terminal_id`; heurystyki A/C zbędne dla device_block.

## Action Items

1. [ ] Akceptacja: drop `bus` (deprecate), `kind="link"`, rola `cable_marker` (Filip).
2. [ ] `backend/models/schema.py`: `ConnectionKind += "link"`; `LineRole += "cable_marker"`; komentarz „bus deprecated".
3. [ ] `LineClassifier`: przestań nadawać `bus` (długie osiowe → `wire`); `CONNECTION_ROLES = {wire}`. Aktualizacja testów `test_line_classifier`.
4. [ ] Sito: nie demotuj wnętrza `device_block` (Opcja A) + heurystyka tabela (C).
5. [ ] net-builder: odcinki wewnątrz device_block → `Connection kind="link"`.
6. [ ] `cable_marker`: detekcja (dashed × przecięcie wire × etykieta OCR) → adnotacja + relacja marker→kable + spec.
7. [ ] (etap 2, osobny prompt) tryb terminali w labelerze → Opcja B.
