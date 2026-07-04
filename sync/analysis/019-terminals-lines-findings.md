# 019 — Findings: terminale + linie (Fable 5, 2026-07-04)

**Zakres:** analiza kodu + eksperymenty na realnym tuszu (kafle `data/labeled_tiled`, p027 w010–w015). NIE implementacja.

**Ograniczenie środowiska [RYZYKO]:** sesja biegła na PC ZW, nie na głównym PC z danymi. W tej kopii repo: `data/raw` = tylko `IEC60617.pdf` (brak PNG stron), `data/schemagen.db` = 0 adnotacji, kafle `labeled_tiled` są **grayscale**. Skutki: (a) kroki z sekcji 6 promptu wymagające pełnych stron/kolorów (preview_schema, histogram hex, rozmiary stron) — do wykonania przez Filipa, komendy niżej; (b) H5 nieweryfikowalna lokalnie. Mimo to główna oś (p027) została **odtworzona empirycznie** na kaflach.

---

## TL;DR

1. **Główna przyczyna p027 (bus wire) znaleziona i odtworzona:** szyna listwy jest przerywana kółkami węzłów co ~94 px. Segmenty tuszu między kółkami mają **67–76 px**, przerwy (kółka) **21–22 px**. Runtime Hough na stronie ~6600 px: `min_line_length=132` (>76!) i `max_line_gap=10` (<21!) → **szyna w 100% niewidoczna dla LineTracera**. Zero linii → `derive_auto_terminals` bez kontaktów → złączki bez terminali → `connection_require_terminal: true` → **0 connections**. Sito NIE jest winne (H3/H6 odrzucone dla p027).
2. **Nawet po naprawie Hougha pipeline nie złoży listwy:** (a) `_point_at_node` z `node_tol=79.2` blokuje union-find fragmentów w całym pasie listwy (eksperyment: 46 netów zamiast 5); (b) `_nodes_on_net` patrzy **tylko na końce** linii — scalona szyna 1535 px dotykająca 16 złączek daje węzły tylko na 2 skrajnych; (c) `terminal_tol=79.2` px przy pitchu złączek 94 px → **zanieczyszczenie terminalami sąsiadów** (6–10 terminali/złączkę zamiast 2–4).
3. **Kolory:** potwierdzone w kodzie — brak grupy dla czerwieni; `enclosure` i `pe_wire` mają identyczny stroke `#00AA44`, a `match_color` rozstrzyga remis **kolejnością w dict** → zieleń ZAWSZE `enclosure`, `pe_wire` nigdy → `kind="pe"` nigdy nie powstaje z koloru. Do tego `enclosure` (2 role) nie daje hinta → zielona ramka dostaje rolę `wire` [BŁĄD].
4. **Strzałki:** `arrow_supplement` odpala się tylko gdy klasa ma **zero** detekcji na stronie — jeden FP wyłącza uzupełnienie całej klasy. Na p027 rząd złączek ma realne glify strzałek (góra/dół przy każdym kółku), **nieoznaczone w GT jako strzałki** → gotowe źródło FP `strzalka_wyjsciowa` i szumu treningowego.
5. Proponowany podział: **018-lines-quality najpierw** (bez linii TerminalResolver klasy line-contact nie ma na czym pracować), potem **018-terminals-strategy** (TerminalResolver + terminal-patterns.yaml + walidacja terminal-to-terminal).

---

## 1. Metodologia eksperymentu (odtwarzalne)

Brak pełnych stron → pipeline uruchomiony na kaflu `p027__w013` (1536×1536, środek rzędu 58 złączek, 16 złączek GT w kaflu) z parametrami **przeliczonymi na skalę pełnej strony 6600 px**: `min_line_length=132`, `hough_threshold=132`, `max_line_gap=10`, `edge_tol=26.4`, `terminal_tol=79.2`, `merge_tol=12`, `require_terminal=True`. Komponenty = bboxy GT z `labels/train/*w013.txt` (klasa 5 = zlaczka). Kroki jak `graph_builder.build()` 3→3b→4→4b→5 (bez OCR/YOLO/ROI).

Zmierzone na tuszu (wiersz szyny, y=487 kafla):
- pokrycie tuszem: 1196/1536 px; **17 segmentów** tuszu 31–74 px (mediana 73); **14 przerw** po 21–22 px (kółka węzłów, białe w środku),
- bboxy złączek: szer. 24–73 px (med. ~50), wys. 63–100 px (med. ~83), **pitch 78–108 px (med. ~94)**, przerwa brzeg–brzeg min. 10 px,
- szyna przechodzi przez **środki** bboxów (cy≈488 vs szyna y=487; krawędzie góra/dół ~40 px od szyny).

Wyniki wariantów:

| Wariant | segs | najdł. pozioma w pasie | terminale/złączkę | connections |
|---|---|---|---|---|
| **A** runtime (132/10) | 5 | **0 px (szyny brak)** | 0 (3 szt. po 1) | **0** |
| **B** min_len=40, gap=25 | 336 | 1535 px | 6–10 (szum!) | 51 (24 między komp.) |
| **C** min_len=66, gap=25 | 171 | 1535 px | 1–6 | 14 (tylko **2** między komp.) |
| **D** min_len=40, gap=10 | — | 16 fragmentów 67–76 px | 6–10 | 66, 15 potentials |

Wariant A odtwarza dokładnie objaw p027 („symbole są, połączeń zero"). D dodatkowo: union-find z `node_tol=79.2` → **46 netów**; ta sama geometria bez blokady węzłów → **5 netów** (dowód H2). C: pojedyncza scalona szyna → tylko 2 connections między komponentami (dowód „końce-tylko" w `_nodes_on_net`).

---

## 2. Status hipotez

| Hipoteza | Werdykt | Dowód |
|---|---|---|
| **H1** `_merge_collinear` gap_tol=12 px stały | **POTWIERDZONA, ale wtórna** | `line_tracer.py:96` — stała, wywołanie `_merge_collinear(segments)` bez argumentów (l.254). 12 px < 21–22 px przerwy kółek → nie sklei fragmentów szyny nawet gdyby Hough je dał. Wtórna, bo przy runtime paramach Hough nie daje NIC (wariant A). |
| **H2** `_point_at_node` blokuje scalanie na listwie | **POTWIERDZONA** | Wariant D: 46 netów z blokadą vs 5 bez. Przy pitch 94 px < node_tol 79,2 px×2 praktycznie każdy punkt pasa listwy jest „na węźle". Uwaga: łańcuch fragment-po-fragmencie NADAL dawał connections (66 szt.) — topologicznie łańcuch ≈ szyna, ale liczba i adresy są śmieciowe przez zanieczyszczenie terminali (niżej). |
| **H3** `_is_box_edge` demotuje szynę | **ODRZUCONA dla p027** | Szyna biegnie przez środki bboxów: 40 px od krawędzi góra/dół > edge_tol 26,4 px. Wariant B: tylko 6 demotów w pasie (fragmenty przypadkowe), C: 0. Sito nie jest blokerem listwy. |
| **H4** brak czerwieni + kolizja enclosure/pe_wire | **POTWIERDZONA (kod)** | `semantic-colors.yaml`: brak grupy z czerwonym stroke; `enclosure.stroke == pe_wire.stroke == #00AA44`. `palette.match_color`: remis rozstrzyga `dist < best[0]` (ostro) → wygrywa **pierwsza** grupa w dict = `enclosure` (YAML zachowuje kolejność) → **deterministycznie**, nie losowo: zieleń nigdy nie jest `pe_wire`, `_kind_for_net` nigdy nie da `pe` z koloru. Bonus [BŁĄD]: `enclosure` ma `roles: [frame, device_stroke]` → `_color_role_hint` zwraca None (len≠1) → zielona ramka obudowy dostaje rolę **wire** i wchodzi do kandydatów Connection. Czerwień: żadna grupa w progu (threshold 0,2366) → `semantic_group=""`, rola wire — czerwone przewody działają, ale bez semantyki. |
| **H5** `_sample_color` niestabilne (antyaliasing/JPEG) | **NIEROZSTRZYGNIĘTA** | Kafle w tej kopii repo są grayscale (max|B−G|=0). Wymaga stron kolorowych u Filipa (komenda niżej). Kod: metoda „najdalej od bieli" w pasie ±3 px weźmie najciemniejszy piksel — na styku czarnego symbolu z kolorową linią wygra czerń; podejrzenie zasadne, dowodu brak. |
| **H6** EDGE_OVERLAP_MIN=0.6 za niski | **ODRZUCONA jako bloker p027** | jw. H3. Uwaga na przyszłość: `_overlap_frac` liczy pokrycie względem KRÓTSZEGO zakresu, więc długa szyna vs wąski bbox (50 px) osiąga 1.0 trywialnie — gdyby szyna biegła po krawędzi bboxów (inna strona/klasa), demot nastąpi. Zostawić na radarze przy 018-lines, nie ruszać progu bez przypadku testowego. |
| **H7** szyna nie dociera do derive_auto_terminals | **POTWIERDZONA — GŁÓWNA PRZYCZYNA** | Wariant A: 0 poziomych linii w pasie listwy przy paramach runtime. Przyczyna pierwotna: **min_line_length=132 px > 76 px** (najdłuższy segment tuszu między kółkami) i **max_line_gap=10 px < 21 px** (przerwa kółka). Szyna nie istnieje dla Hougha, reszta pipeline'u głoduje. |
| **H8** dedup 12 px scala terminale gęstych złączek | **ODRZUCONA — problem jest ODWROTNY** | Szer. bboxa med. ~50 px > 2×12 px → lewy/prawy terminal się nie sklejają. Realny problem: `derive_auto_terminals` zbiera kontakty per-komponent w promieniu `tol=79.2` px, a pitch złączek to 94 px → koniec linii przy złączce A jest też w tolerancji złączek B/C → **6–10 terminali/złączkę** (warianty B/D). `merge_tol` jest OK; za duży jest `tol` kontaktu względem gęstości rzędu. Drift drobny: labeler wywołuje `derive_auto_terminals(comp, lines, tol)` **bez merge_tol** → dedup=min(tol,15)=15 px vs runtime 12 px. |
| **H9** strzałki: recall w YOLO, nie confusion | **CZĘŚCIOWO (kod + dataset)** | (a) `arrow_supplement` pokrywa obie klasy (`_ARROW_CLASSES`, mapa 7/8 zgodna z data.yaml). (b) [BŁĄD logiczny] `need = [c for c in want if c not in have]` — wystarczy JEDNA detekcja YOLO (choćby FP z p027!) by wyłączyć supplement całej klasy na stronie. (c) `roi_top_frac=0.93`: nazwa myląca — `cutoff=0.93*H`, odrzucane `y > cutoff`, czyli ROI = GÓRNE 93%, ucinane dolne 7% — strzałka przy dolnej krawędzi (p035?) przepada. (d) Dataset: klasa 7 = **84** instancje, klasa 8 = **343** (4× mniej wejściowych). (e) Na p027 przy każdej złączce są glify strzałek góra/dół **nieoznaczone jako klasa 7/8** w GT kafli → konflikt etykiet: model karany za wykrywanie kształtu, który gdzie indziej jest klasą — to jednocześnie tłumaczy FP `strzalka_wyjsciowa` w pasie y2770–3015 i niski recall. Weryfikacja źródła detekcji p035 wymaga danych u Filipa. |

---

## 3. Znaleziska dodatkowe (poza hipotezami)

1. **[BŁĄD architektoniczny] Węzły tylko z końców linii.** `_nodes_on_net` iteruje `(line.points[0], line.points[-1])`. Scalona szyna przez N złączek = 2 węzły. Wniosek dla 018: węzeł musi powstawać też tam, gdzie **ścieżka** linii przechodzi przez terminal komponentu (zgodne z definicją Filipa: terminal = punkt przecięcia linii z bboxem, niezależnie czy to koniec segmentu Hougha).
2. **`terminal_tol` pełni 3 role naraz** (kontakt terminala, `join_tol` union-find, `bridge_tol` sita) — skalowany frakcją strony (79 px) jest sensowny dla „czy linia sięga symbolu", ale absurdalny jako promień dedup/join w rzędzie o pitchu 94 px. Rozdzielić w configu.
3. **Martwy klucz** `"bus"` w `ROLE_COLORS_BGR` (`scripts/preview_lines.py:28`) — kosmetyka, do sprzątnięcia przy 018-lines. Legacy `bus` obsłużone poprawnie w labelerze (`_gt_line_role`).
4. **Labeler nie ma** mechanizmu „zapisz terminale jako wzorzec klasy" (grep po `pattern/wzorzec` w `crop_review.js` — brak). Potrzebny endpoint + przycisk (zakres 018-terminals).
5. **`diag_coords.py`** istnieje, ale dotyczy bboxów, nie linii. Brak diagnostyki linia-po-linii (hex + rola + grupa) — proponuję mały read-only `scripts/diag_lines.py` w ramach 018-lines (kryterium: histogram detected_color per rola na stronę).
6. **[RYZYKO] Spójność kopii repo ZW:** cztery pliki w montowanej kopii miały uszkodzenia odczytu (`net_builder.py` ucięty, `graph_builder.py` null-bytes, `runtime_config.py`, `symbol_detector.py`) — przez narzędzia plikowe Windows czytają się poprawnie, więc to artefakt synchronizacji sandboxa, ale warto po commicie sprawdzić `git status`/`pytest` na głównym PC.
7. Kafle `labeled_tiled` są **grayscale** (eksport `convert("L")`) — jeśli kolory przewodów mają być cechą treningową/diagnostyczną, trzeba pamiętać, że YOLO ich nie widzi (dziś OK, symbole są czarno-białe).

---

## 4. Architektura `TerminalResolver` (doprecyzowana po analizie)

Nowy plik `backend/recognize/terminal_resolver.py` (nie rozszerzać net_buildera — union-find jest wrażliwy, prompt 019 §8). `net_builder.derive_auto_terminals` zostaje jako fallback i źródło kandydatów.

```
TerminalResolver.resolve(component, lines, image_bgr, patterns) -> list[Terminal]
  1. pattern = patterns.get(component.type)
  2. brak patternu -> fallback: derive_auto_terminals (dzisiejsze zachowanie)
  3. method z patternu:
     - "perimeter": skan obwodu tuszu (uogólnione derive_mostek_terminals;
       mostek DELEGUJE do istniejącej funkcji — nie ruszać, działa)
     - "line-contact": kandydaci = kontakty linia<->bbox, ale liczone też dla
       PRZEJŚCIA ścieżki przez bbox (nie tylko końców) — patrz znalezisko 3.1
  4. dopasuj kandydatów do pozycji z patternu (edge+frac, tolerancja
     terminal_tol_pattern — NOWY, mniejszy niż terminal_tol kontaktu);
     brakujące pozycje patternu UZUPEŁNIJ (pozycja jest własnością klasy —
     definicja Filipa), kandydatów spoza patternu ODRZUĆ (anty-zanieczyszczenie
     z sąsiadów, wariant B/D: 6–10 -> oczekiwane 2–4)
  5. walidacja terminal-to-terminal zostaje w build_connections (net_builder),
     nie w resolverze: wire, którego żaden koniec/przejście nie rozwiązuje się
     do (comp, terminal), odpada jako kandydat Connection
```

`config/terminal-patterns.yaml` (nie istnieje — potwierdzone) — propozycja struktury pod zmienną liczbę terminali:

```yaml
version: 1
classes:
  zlaczka:
    method: perimeter        # stabilniejsze niż line-contact (uniezależnia od Hougha)
    expected:                # reguły, nie sztywna lista — złączka bywa 2–4-stubowa
      - {edge: left,  frac: 0.5, required: true}    # szyna listwy
      - {edge: right, frac: 0.5, required: true}
      - {edge: top,    frac: 0.5, required: false}  # odczep w górę (strzałka)
      - {edge: bottom, frac: 0.5, required: false}
    frac_tol: 0.15
  mostek:
    method: delegate         # -> derive_mostek_terminals (działa, zostawić)
```

Odpowiedzi na pytania architektoniczne z §5 promptu: (a) osobny plik; (b) YAML generowany **z labelera** (workflow Filipa: auto-derive → korekta → „zapisz jako wzorzec klasy" → `POST /api/save-terminal-pattern` zapisuje uśrednione edge+frac per klasa), ręczna edycja przez Cursor dozwolona; (c) zmienna liczba terminali = pozycje `required: true/false` + `frac_tol`, nie sztywna lista; (d) mostek deleguje, bez unifikacji.

---

## 5. Plan wdrożenia — podział na prompty

### 018-lines-quality (PIERWSZY — terminale line-contact głodują bez linii)

Pliki: `backend/recognize/line_tracer.py`, `line_sieve.py` (drobiazg), `config/runtime.yaml`, `config/semantic-colors.yaml`, `backend/colors/palette.py` (remis), `scripts/preview_lines.py` (martwy klucz), nowy `scripts/diag_lines.py`.

1. **Hough dwuprzebiegowy albo domknięcie morfologiczne pod kółka węzłów:** przerwy 21–22 px to systematyczna cecha notacji (kółko węzła), nie szum. Opcje do decyzji w prompcie: (a) drugi przebieg Hough z `min_len≈0.008*max(W,H)` i `gap≈0.004*max(W,H)` tylko dla linii osiowych + scalanie; (b) `cv2.morphologyEx(CLOSE)` kernelem 1×25/25×1 przed Houghem na masce osiowej. Wariant C eksperymentu (min_len 66/gap 25) dał szynę 1535 px bez eksplozji szumu (171 segs vs 336 przy min_len 40) — dobry punkt startowy kalibracji.
2. **`_merge_collinear`: `gap_tol` skalowany** z rozmiarem strony (`max(12, hough_gap*2.5)`), nie stała 12.
3. **semantic-colors.yaml:** dodać `phase_wire` (czerwony, roles [wire]); rozdzielić stroke `enclosure` vs `pe_wire` (Filip potwierdza realne kolory z wydruku); [BŁĄD] rozważyć w `match_color` tie-break po roli/stylu zamiast kolejności dict + hint dla grup wielorolowych (enclosure→frame, nie wire).
4. Sprzątanie: martwy `"bus"` w preview_lines; `diag_lines.py` (read-only histogram kolor/rola/grupa).
5. **NIE ruszać:** `EDGE_OVERLAP_MIN`, union-find, sito (poza pkt 4 nic w line_sieve).

Kryteria akceptacji:
- p027: pozioma szyna y≈2905 wykryta jako `wire` ciągły ≥ 90% szerokości rzędu (preview_lines);
- p040: `eval_val_pages.py --page p040` bez regresji connections vs stan sprzed zmiany;
- liczba segmentów na p035 nie rośnie > 2× (kontrola szumu po obniżeniu progów);
- zielona linia klasyfikowana `pe_wire` (po rozdzieleniu kolorów), czerwona dostaje grupę.

### 018-terminals-strategy (DRUGI — zależy od jakości linii)

Pliki: nowy `backend/recognize/terminal_resolver.py` + testy, nowy `config/terminal-patterns.yaml`, `graph_builder.py` (krok 4 podmienia wywołanie), `net_builder.py` (węzły z przejścia ścieżki przez terminal — JAWNE ryzyko regresji mostków/odczepów: wymagane testy `test_net_builder` star/require_terminal bez zmian wyniku), `labeler/app.py` + `crop_review.js` (endpoint + UI „zapisz wzorzec klasy"), `config/runtime.yaml` (rozdzielenie `terminal_tol` na kontakt / join / pattern-match).

Kolejność wewnątrz promptu: resolver+patterns → węzły-na-ścieżce → walidacja terminal-to-terminal → labeler UI.

Kryteria akceptacji (z §1 promptu 019):
- ≥ 95% instancji klas z patternem na val-pages ma terminale zgodne z patternem (tolerancja `terminal_tol_*`);
- 0% Connection z linii łamiących regułę terminal-to-terminal (`from_ref`/`to` zawsze `comp:terminal` przy `connection_require_terminal: true`);
- p027 rząd 58 złączek: ≥ 95% złączek ma ≥ 1 terminal, jeden wspólny potential szyny (lub łańcuch równoważny), 0 terminali „pożyczonych" od sąsiada (test: terminal w odległości > pitch/2 od centrum właściciela = błąd);
- mostki p040: wynik `derive_mostek_terminals` bajt-w-bajt bez zmian (delegacja);
- pytest: dotychczasowe 213 + nowe testy resolvera zielone.

Zależność jawna: pkt „węzły-na-ścieżce" w net_builderze to jedyna zmiana wspólnej funkcji — jeśli Cursor woli, można ją wydzielić do osobnego mini-promptu 018c po review.

### Odłożone (nie w tej rundzie)
OCR (decyzja Filipa), retrain strzałek — najpierw doznaczenie glifów strzałek przy złączkach w GT (inaczej retrain utrwali konflikt etykiet), fix `need`/`roi_top_frac` w arrow_supplement można wcisnąć do 018-lines jako 3-linijkowy patch, jeśli Filip potwierdzi objaw na p035.

---

## 6. Do wykonania przez Filipa (dane niedostępne na ZW)

```powershell
python scripts/preview_lines.py --page data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_p027.png   # role w pasie y~2905
python scripts/preview_schema.py --page p027 --source both
python -c "import cv2; [print(p, cv2.imread(f'data/raw/22_A_153_PL_Adamed_AGV_SA2_20250706_{p}.png').shape) for p in ('p027','p035','p040')]"
```
plus histogram `detected_color` dla wire bez grupy (H5) — mogę dostarczyć skrypt w 018-lines (`diag_lines.py`).

---

## Pytania do Filipa

1. **Kolory realne na skanach:** jaki dokładnie kolor ma przewód „zielony" (PE?) i „czerwony" na p027/p035 — hex z pipety (2–3 próbki)? Bez tego kalibracja `semantic-colors.yaml` będzie zgadywana. Przykład poprawnej odpowiedzi: `PE: #00a844, fazowy: #e53935`.
2. **Złączka p027 — ile terminali w GT?** Z tuszu wynika: 2 na osi szyny (L/P) + odczepy góra/dół do glifów strzałek. Czy odczep góra/dół to osobny terminal złączki, czy strzałka jest osobnym symbolem z własnym terminalem? Determinuje pattern `zlaczka` w terminal-patterns.yaml.
3. **Glify strzałek przy złączkach p027:** doznaczyć jako klasa 7/8 w GT (przed ewentualnym retrainem), czy traktować jako część symbolu złączki? Obecny stan (nieoznaczone) psuje i recall, i FP.
4. Czy `git status`/`pytest` na głównym PC czyste po tym commicie (patrz znalezisko 3.6 o artefaktach synchronizacji kopii ZW)?
