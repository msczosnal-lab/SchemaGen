# Prompt startowy — Cursor: review analizy 019 + zlecenie 018

Wklej do nowej sesji Cursor (PC Filip).

---

Jesteś Cursor — reviewer i koordynator projektu SchemaGen (offline, Python/FastAPI/YOLO ONNX, bez cloud API w runtime). Wczytaj w kolejności:

1. `sync/analysis/019-terminals-lines-findings.md` — kompletna analiza Fable 5 (terminale + linie), ze statusem hipotez, danymi z main (§7/§7b) i odpowiedziami Filipa (sekcja „Pytania — ODPOWIEDZI")
2. `sync/prompts/019-fable5-terminals-lines-analysis.md` — sekcja „Wynik"
3. `sync/KOLEJNE-ZADANIE.md`, `sync/zw-to-filip.md` — stan projektu

## Stan (skrót, szczegóły w findings)

- **Główna przyczyna p027 (0 connections) potwierdzona w pełnej skali:** szyna listwy = segmenty tuszu 73–74 px przerywane kółkami węzłów 21–22 px; runtime Hough `min_len=132`, `gap=10` → szyna niewidoczna → brak terminali → brak połączeń. Sito NIE jest winne.
- **Druga warstwa (po naprawie Hougha):** `_point_at_node` blokuje union-find w pasie listwy; `_nodes_on_net` widzi tylko końce linii; `terminal_tol=79 px` vs pitch złączek 94 px → fałszywe terminale sąsiadów.
- **Kolory:** objaw „czerwony/zielony losowy" = kolory overlayu (zielony=wire, czerwony=Connection), nie tusz. Realny błąd palety: niebieski #134088/#105090 nie łapie się do `motor_device` #0066CC.
- **Strzałki:** 15 detekcji `wyjsciowa` na p027 to **TP, nie FP** — braki w GT (Filip doznacza). `arrow_supplement` wyłączany przez pojedynczą raw detekcję klasy (`c not in have`).
- **Decyzje Filipa:** pattern `zlaczka` = left/right 0.5 required + top/bottom 0.5 optional; strzałka = osobny symbol z terminalem u nasady; glify strzałek doznaczyć jako klasa 7/8.

## Twoje zadania (ta sesja)

1. **Review findings** — zaakceptuj albo dopisz `## Poprawka (runda 1)` w pliku 019. Szczególnie oceń §5 (podział 018) i pkt „węzły-na-ścieżce" w `net_builder.py` — to JEDYNA proponowana zmiana wspólnej, wrażliwej funkcji i wymaga Twojej zgody (ryzyko regresji mostków/odczepów; testy star/require_terminal muszą przejść bez zmiany wyniku).
2. **Napisz `sync/prompts/018-lines-quality.md`** (dla Claude) na bazie findings §5 — zakres: Hough pod kółka węzłów (dwuprzebiegowy lub morfologia CLOSE; punkt startowy kalibracji: min_len≈66/gap≈25 działał na kaflu bez eksplozji szumu), skalowany `gap_tol` w `_merge_collinear`, kalibracja niebieskiego w `semantic-colors.yaml`, rozjaśnienie kolorów overlay (wire vs frame w preview_lines to dwie zielenie), opcjonalnie 3-linijkowy fix `arrow_supplement` (`need` + nazwa `roi_top_frac`). Kryteria akceptacji z findings §5 (m.in. szyna p027 ≥90% szerokości rzędu jako wire; brak regresji p040 w `eval_val_pages.py`).
3. **Napisz `sync/prompts/018-terminals-strategy.md`** — TerminalResolver (nowy plik `backend/recognize/terminal_resolver.py`), `config/terminal-patterns.yaml` (struktura w findings §4, pattern złączki wg decyzji Filipa), endpoint labelera „zapisz wzorzec klasy", walidacja terminal-to-terminal, rozdzielenie `terminal_tol` (kontakt/join/pattern) w `config/runtime.yaml`. Kryterium listwy p027: 58 złączek × (2 terminale osiowe + 0–2 odczepy), odczep → Connection `zlaczka:top/bottom ↔ strzalka:base`, szyna = jeden potential. Zdecyduj, czy „węzły-na-ścieżce" idą w tym promptcie, czy jako osobny 018c po review.
4. **Zaktualizuj `sync/KOLEJNE-ZADANIE.md`:** 018-lines-quality = aktywne (Claude), 018-terminals-strategy = kolejka, 016-e2e-metrics = bez zmian (po smoke), Filip = doznaczenie strzałek 7/8 na listwach + smoke 015.
5. Commit: `sync/commit-message.txt` = `[Cursor] sync: review 019 + prompty 018-lines/018-terminals`.

## Ograniczenia (twarde, bez zmian)

- Kontrakt `SchemaModel` (`backend/models/schema.py`) nietykalny.
- `derive_mostek_terminals` działa — pattern mostka deleguje, nie ujednolicać.
- Sito zawsze włączone — poprawki logiki, nie flaga off.
- Zakaz cloud API w `backend/recognize/`, `train/`, `labeler/`.
- pytest: 213 passed to baseline — każdy prompt 018 musi go utrzymać.

## Otwarte drobiazgi (do wciągnięcia w prompty wg Twojego uznania)

- Duplikaty nazw klas GT („terminal PLC" vs „terminal_plc", etykiety PL vs klasy YOLO) — ujednolicić przed eksportem wzorców terminali.
- Martwy klucz `"bus"` w `scripts/preview_lines.py:28`.
- Drift labeler↔runtime: JS ma zaszyte `0.012/12` zamiast czytać config; labeler nie przekazuje `merge_tol` (dedup 15 vs 12 px).
- OCR odłożone — nie planować w tej rundzie.
