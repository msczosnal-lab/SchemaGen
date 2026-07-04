# Zadanie 018: Strategia terminali (TerminalResolver + węzły na ścieżce)

**Status:** KOLEJKA — po zakończeniu [`018-lines-quality.md`](018-lines-quality.md)  
**Model:** Opus, effort High  
**Zależność:** jakość linii z 018-lines (szyna p027 musi być wykryta jako `wire`)  
**pytest baseline:** 213 passed (+ nowe testy resolvera)

## Kontekst

Po naprawie Hougha ujawnia się druga warstwa (findings §1–§3):

1. `derive_auto_terminals` zbiera kontakty w promieniu `terminal_tol≈79 px`, pitch złączek ~94 px → **6–10 fałszywych terminali/złączkę**
2. `_nodes_on_net` widzi **tylko końce** linii — scalona szyna 1535 px przez 16 złączek → 2 węzły zamiast N odczepów
3. GT terminali prawie puste (6/533 złączek) — wzorce per klasa z workflow labelera

**Decyzje Filipa** (findings ODPOWIEDZI):

- Terminal = punkt przecięcia linii z krawędzią bboxu — pozycja jest **własnością klasy** (pattern), nie końcem segmentu Hougha
- `zlaczka`: `left 0.5` + `right 0.5` (szyna, required); `top 0.5` / `bottom 0.5` (optional — odczep do strzałki)
- Strzałka = osobny symbol z terminalem u nasady odczepu
- Oczekiwany wynik p027: 58 złączek × (2 terminale osiowe + 0–2 odczepy); szyna → **jeden potential** z wieloma węzłami; odczep → Connection `zlaczka:top|bottom ↔ strzalka:base`

**Review Cursor:** zmiana `_nodes_on_net` (węzły-na-ścieżce) **w tym prompcie** — nie w 018-lines, nie jako osobny 018c. `_point_at_node` / `_lines_joined` — **nietknięte**.

Architektura: [`sync/analysis/019-terminals-lines-findings.md`](../analysis/019-terminals-lines-findings.md) §4, Poprawka runda 1.

## Reguły (nie zmieniać bez zgody Cursor)

- Kontrakt `SchemaModel` nietknięty
- `derive_mostek_terminals` — **delegacja**, wynik bajt-w-bajt bez zmian dla klasy `mostek`
- Union-find: **nie zmieniać** `_lines_joined` / `_point_at_node` (regresja mostków/odczepów)
- Istniejące testy [`backend/tests/test_net_builder.py`](../../backend/tests/test_net_builder.py) — **bez zmiany asercji**
- `connection_require_terminal: true` — zachować
- Bez cloud API w `backend/recognize/`, `labeler/`

## Kolejność implementacji

### Krok 1 — `config/terminal-patterns.yaml` + `TerminalResolver`

**NOWY** [`backend/recognize/terminal_resolver.py`](../../backend/recognize/terminal_resolver.py):

```python
def resolve(
    component: Component,
    lines: list[GraphicLine],
    image_bgr: np.ndarray | None,
    patterns: dict,
    *,
    contact_tol: float,
    pattern_tol: float,
) -> list[Terminal]:
```

Logika (findings §4):

1. `pattern = patterns.get(component.type)` — brak → fallback `derive_auto_terminals`
2. Metoda z patternu:
   - `"perimeter"`: skan obwodu tuszu (jak `derive_mostek_terminals`) — **złączka** left/right
   - `"line-contact"`: kontakty linia↔bbox, także **przejście ścieżki** przez bbox (nie tylko końce)
   - `"delegate"`: → `derive_mostek_terminals` (mostek)
3. Dopasuj kandydatów do pozycji patternu (`edge` + `frac`, `frac_tol`); brakujące **required** uzupełnij; nadmiarowe odrzuć (anty-zanieczyszczenie sąsiadów)

**NOWY** [`config/terminal-patterns.yaml`](../../config/terminal-patterns.yaml):

```yaml
version: 1
classes:
  zlaczka:
    method: perimeter
    expected:
      - {edge: left,  frac: 0.5, required: true}
      - {edge: right, frac: 0.5, required: true}
      - {edge: top,    frac: 0.5, required: false}
      - {edge: bottom, frac: 0.5, required: false}
    frac_tol: 0.15
  mostek:
    method: delegate
```

Loader w `backend/runtime_config.py` lub dedykowany moduł.

### Krok 2 — `graph_builder` + rozdzielenie `terminal_tol`

Pliki: [`backend/recognize/graph_builder.py`](../../backend/recognize/graph_builder.py), [`config/runtime.yaml`](../../config/runtime.yaml)

Krok 4 `build()` — kolejność zachowana:

1. `derive_mostek_terminals` dla `mostek` (jak dziś)
2. `TerminalResolver.resolve` dla pozostałych (zamiast samego `derive_auto_terminals`)
3. `recover_terminal_bridges` (4b) — bez zmian

Rozdziel `terminal_tol` na trzy role (findings §3.2):

| Klucz | Rola |
|-------|------|
| `terminal_tol_contact_frac` / `_min` | Czy linia sięga symbolu (`derive_auto_terminals`, kontakt) |
| `terminal_tol_join_frac` / `_min` | `join_tol` union-find, `bridge_tol` sita |
| `terminal_tol_pattern_frac` / `_min` | Dopasowanie kandydata do pozycji z patternu (mniejszy — anty-sąsiad przy pitch 94 px) |

Migracja: stary `terminal_tol_frac` → domyślnie contact; loadery w `runtime_config.py`.

### Krok 3 — `_nodes_on_net` — węzły na ścieżce

Plik: [`backend/recognize/net_builder.py`](../../backend/recognize/net_builder.py) (~linia 154)

Obecnie tylko końce linii. Rozszerz:

- Dla każdej linii w net, każdego odcinka `points[i]`→`points[i+1]`
- Dla każdego komponentu z `terminals`, każdego terminala (pozycja abs z rel)
- Jeśli `_pt_seg_dist(terminal_abs, odcinek) <= tol` → dodaj węzeł `comp:terminal_id` (przez `_resolve_node` lub równoważna logika z `require_terminal`)

**Nie ruszać** `_lines_joined` / `_point_at_node`.

**NOWY test** w `test_net_builder.py`: jedna pozioma linia przez 3 bboxy z terminalami left/right 0.5 → `_nodes_on_net` zwraca ≥3 węzły; `build_connections` emituje potential z wieloma symbolami.

Walidacja terminal-to-terminal pozostaje w `build_connections` — wire bez rozwiązania do `(comp, terminal)` odpada.

### Krok 4 — Labeler: zapis wzorca klasy

Pliki: [`labeler/app.py`](../../labeler/app.py), [`labeler/static/crop_review.js`](../../labeler/static/crop_review.js)

- `POST /api/save-terminal-pattern` — body: klasa + lista bboxów z skorygowanymi terminalami → uśrednione `edge`+`frac` → zapis do `terminal-patterns.yaml`
- UI: przycisk „Zapisz wzorzec klasy" w trybie terminal (po korekcie Filipa)
- **Ujednolić nazwy klas GT** przed eksportem (duplikaty `terminal PLC` / `terminal_plc`, etykiety PL vs klasy YOLO)

### Krok 5 — Drift labeler ↔ runtime

- [`labeler/static/crop_review.js`](../../labeler/static/crop_review.js): `terminalTol()` — czytaj z API/config, nie zaszyte `0.012`/`12`
- `derive-terminals` API: przekazuj `merge_tol` (dedup 12 vs 15 px)

## Testy

**NOWY** [`backend/tests/test_terminal_resolver.py`](../../backend/tests/test_terminal_resolver.py):

- złączka z patternem: dokładnie left+right, opcjonalne top/bottom gdy kandydat
- brak patternu → fallback `derive_auto_terminals`
- mostek → delegacja (mock: ten sam wynik co `derive_mostek_terminals`)
- odrzucenie kandydata poza patternem (anty-sąsiad)

Rozszerz `labeler/tests` dla endpointu save-pattern (jeśli dodany).

## Kryteria akceptacji

| Kryterium | Sprawdzenie |
|-----------|-------------|
| Pattern match | ≥95% instancji klas z patternem na val-pages — terminale zgodne z `terminal_tol_pattern` |
| terminal-to-terminal | 0% Connection łamiących regułę przy `connection_require_terminal: true` |
| p027 listwa | 58 złączek: ≥95% ma ≥1 terminal; jeden wspólny potential szyny; 0 terminali „pożyczonych" (> pitch/2 od centrum właściciela) |
| Odczepy | Connection `zlaczka:top|bottom ↔ strzalka:base` gdzie jest odczep + strzałka |
| mostek p040 | `derive_mostek_terminals` — wynik identyczny (delegacja) |
| Regresja net-builder | `test_mostek_between_terminals_*`, `test_two_wires_to_same_terminal_*`, `test_require_terminal_*`, `test_T_junction_*` — **bez zmiany asercji** |
| pytest | ≥213 + nowe testy resolvera zielone |

## Smoke (Filip)

```powershell
python scripts/preview_schema.py --page p027 --source runtime
python scripts/eval_val_pages.py --page p040
python -m pytest backend/tests labeler/tests train/tests -q
```

## Po ukończeniu

`sync/commit-message.txt` = `[Claude] recognize: terminal resolver + path nodes (prompt 018-terminals)`

## Poprawka (runda N)

*(Cursor)*
