# Zadanie 019: Analiza + plan — terminale i linie (Faza 4b)

**Status:** DONE — analiza + review Cursor 2026-07-04
**Wykonawca:** Claude (Fable 5), na glownym PC z pelnym repo + danymi (`data/raw`, `data/labeled_tiled`, modele w `models/registry.json`)
**Model docelowy jakosci:** ~65% -> 99.5%. Symbole (YOLO) NIE sa glownym blokerem.

---

## 0. Twoja misja

1. Przeanalizuj kod wymieniony w sekcji 3 (juz czesciowo scytowany ponizej — zweryfikuj na zywym repo, bo mogl sie zmienic).
2. Zbierz dane lokalne (sekcja 6) — realne overlaye, JSON, liczby na p027/p035/p040.
3. Zweryfikuj hipotezy (sekcja 4) na tych danych — potwierdz/odrzuc kazda, z dowodem (liczba, zrzut, cytat kodu).
4. Zaproponuj architekture `TerminalResolver` (sekcja 5) — skonkretyzuj na bazie tego co znajdziesz, nie kopiuj sekcji 5 1:1 jesli dane pokaza inaczej.
5. Napisz **plan wdrozenia** rozbity na proponowane prompty Cowork (sekcja 7) — z zakresem plikow, kolejnoscia, kryteriami akceptacji per prompt.
6. Jesli cos blokuje analize (brak danych, niejasna reguła Filipa, sprzeczne obserwacje) — zapisz pytanie w sekcji "Pytania do Filipa" na dole tego pliku (dopisz sekcje) zamiast zgadywac.
7. Nie zmieniaj kontraktu `SchemaModel` (backend/models/schema.py) ani sygnatur w `backend/recognize/*` bez konsultacji z Cursor — to analiza/plan, implementacja idzie pozniej przez osobne prompty 018-*.
8. Wynik zapisz jako nowy plik `sync/analysis/019-terminals-lines-findings.md` (utworz katalog `sync/analysis/` jesli nie istnieje) + zaktualizuj ten plik (019) sekcja "Wynik" na dole.

---

## 1. Definicja terminala (Filip, KRYTYCZNE — nie negocjowalne)

Terminal to miejsce, gdzie:

1. **Na GT:** czarna linia przecina bbox symbolu dokladnie w tym punkcie (przeciecie z krawedzia bboxa).
2. **Na runtime:** wykryta linia (czerwony lub zielony przewod) przecina bbox **odczytanego** symbolu w **tym samym miejscu**, w ktorym oryginalny bbox (GT) byl przeciety przez krawedz.

Innymi slowy: pozycja terminala jest wlasnoscia **klasy symbolu** (geometria elementu), nie przypadkowym miejscem gdzie akurat wyladowal koniec wykrytej linii w danej instancji. Runtime ma **odtworzyc** pozycje z GT, a nie wymyslic nowa za kazdym razem z geometrii lokalnego Hougha.

### Reguła "wire terminal-to-terminal" (formalizacja na potrzeby kryteriow akceptacji)

> Kazda linia klasyfikowana jako `wire` (kandydat na `Connection`) MUSI laczyc dwa terminale (lub konczyc sie w terminalu na obu koncach). Segment, ktory:
> - nie dotyka bboxa w miejscu **zgodnym z pozycja terminala danej klasy** (patternem), LUB
> - nie laczy sie (koniec-do-konca lub koniec-na-sciezce) z inna linia prowadzaca docelowo do terminala,
>
> NIE jest przewodem i nie powinien trafic do `build_connections`/`derive_auto_terminals` jako kandydat.

Propozycja Filipa do zweryfikowania w analizie: mozna szukac **krotszych segmentow** (rozbicie fragmentacji), ale trzeba **odrzucac** segmenty, ktore nie spelniaja powyzszego (patrz sekcja 4.4 — auto-derive na zlaczce).

**Kryterium akceptacji dla przyszlej implementacji** (do przeniesienia do promptu 018-terminals-strategy):
- Dla kazdej klasy symbolu z GT-galeria wzorcow terminali (sekcja 2), >= 95% instancji na val-pages ma terminale w pozycji zgodnej z patternem (tolerancja `terminal_tol_*`).
- 0% polaczen `Connection` z linii, ktore nie spelniaja reguly terminal-to-terminal (mierzalne: kazdy `Connection.from_ref`/`to` ma format `comp:terminal_id`, nie bare `comp` — gdy `connection_require_terminal: true`, co juz jest w `config/runtime.yaml:45`).

---

## 2. Strategia GT terminali (juz zdecydowana przez Filipa — zaimplementuj plan, nie kwestionuj kierunku)

- GT terminali trzymamy **per klasa symbolu** (galeria/wzorzec), NIE per bbox na kazdej stronie walidacyjnej z osobna.
- Workflow:
  1. **Auto-derive** kandydatow: przeciecie bbox<->linia (juz istnieje: `derive_auto_terminals` w `backend/recognize/net_builder.py:194-233`, wywolywane z labelera przez `POST /api/derive-terminals` i `/api/derive-terminals-page` w `labeler/app.py:142-194`, UI w `labeler/static/crop_review.js` tryb `"terminal"` — `enterTerminalMode()` linia ~306, `deriveTerminalsForPage()` ~104).
  2. Filip koryguje w labelerze (crop_review terminal mode juz istnieje — sprawdz czy wystarcza do "zapisz jako wzorzec klasy" czy trzeba dopisac UI/endpoint).
  3. Wynik zapisany jako **class pattern** — NOWY plik, proponowana nazwa `config/terminal-patterns.yaml` (nie istnieje jeszcze w repo — zweryfikuj). Struktura do zaproponowania w analizie, np.:
     ```yaml
     zlaczka:
       terminals:
         - {edge: left, frac: 0.5}
         - {edge: right, frac: 0.5}
     mostek:
       terminals:  # 3 stuby — pattern MOZE delegowac do derive_mostek_terminals zamiast stalych frac
       ...
     ```
- Rola `derive_auto_terminals`: daje **kandydatow** (surowe kontakty linia<->bbox). Class pattern **filtruje/uzupelnia**:
  - `zlaczka` -> dokladnie 1 stub oczekiwany (sprawdz w GT czy to prawda — zlaczka jednostronna vs dwustronna, patrz p027 w sekcji 4.4).
  - `mostek` -> dokladnie 3 stuby (juz dziala przez `derive_mostek_terminals`, `backend/recognize/mostek_terminals.py:21-48`, wywolywane w `graph_builder.py:120-121` PRZED `derive_auto_terminals` — zachowaj ta kolejnosc, nie zmieniaj bez powodu).
- `derive_mostek_terminals` (perimeter-crossing na binaryzowanym crop, `_stub_rel_positions` w `mostek_terminals.py:51-77`) **dziala dobrze** — zostaw jako osobna sciezke dla klasy mostek. Nie probuj zastapic go ogolnym mechanizmem, chyba ze znajdziesz twardy dowod regresji.

---

## 3. Kod do przeanalizowania (pliki + co w nich sprawdzic)

Sciagnij aktualna tresc (mogla sie zmienic od czasu pisania tego promptu) i zweryfikuj cytowane numery linii.

| Plik | Co sprawdzic |
|---|---|
| `backend/recognize/net_builder.py` | `derive_auto_terminals` (linia ~194): dedup `merge_tol=min(tol,15.0)` — czy to dalej wystarcza dla gesto ulozonych zlaczek w listwie (p027, rozstaw?). `build_connections`+`_group_into_nets` union-find: `_lines_joined` laczy PO KONCU dotykajacym sciezki drugiej linii, ALE **wylacza** polaczenie gdy koniec pada na wezel/terminal (`_point_at_node`) — to bezposrednio determinuje czy fragmentacja linii na dlugiej szynie (p027) w ogole moze sie scalic w jeden `net`, skoro kazdy segment konczy sie blisko kolejnej zlaczki (=terminal=wezel!). **To realny kandydat na przyczyne "brakuje dlugiej szyny p027" — zweryfikuj empirycznie.** |
| `backend/recognize/mostek_terminals.py` | Dziala — uzyj jako wzorzec jak PORZADNIE wyprowadzac terminale z geometrii tuszu zamiast z linii. Rozwaz w analizie: czy podobny perimeter-scan (bez zaleznosci od wykrytych linii) dalby stabilniejsze terminale dla `zlaczka`/`listwa` niz `derive_auto_terminals` (ktory zalezy od jakosci Hougha — circular dependency: zle linie -> zle terminale -> gorsze `Connection`). |
| `backend/recognize/graph_builder.py` | Kolejnosc pipeline'u (`build()`, linia ~73-167): detect -> arrow_supplement -> ocr -> trace+classify -> **sieve (3b)** -> ROI cut (3c) -> terminale auto/mostek (4) -> `recover_terminal_bridges` (4b) -> `build_net_connections` (5) -> `RelationResolver` (6). Sito(3b) i ROI(3c) dzialaja PRZED terminalami(4) — sito nie zna jeszcze terminali wiec `apply_sieve` demotuje linie do `other`/`frame` na podstawie samej geometrii bboxa, a `recover_terminal_bridges` (4b) probuje odzyskac TYLKO mostki (2 rozne terminale TEGO SAMEGO komponentu) — nie odzyskuje np. przewodu miedzy dwoma RÓŻNYMI zlaczkami zdemotowanego przez pomylke. Sprawdz czy to nie ucina bus wire w p027 (linia biegnaca "wzdluz" wielu bboxow zlaczek w rzedzie moze wygladac dla sita jak "linia rownolegla do krawedzi bbox" -> `frame`). |
| `backend/recognize/line_tracer.py` | `LineTracer.trace()`: Canny+dilate+HoughLinesP -> `_merge_collinear` (kolinearne w tolerancji `angle_tol_deg=6`, `gap_tol=12px` — STALA, nie skalowana z rozmiarem strony jak Hough! Na stronie 6600px `gap_tol=12px` to bardzo malo wzgledem `hough_gap_frac`-owego `max_line_gap` uzywanego W HOUGHU. Czy to wystarcza do sklejenia fragmentow dlugiej szyny z drobnymi przerwami w druku/skanie?). `_sample_color`: probkuje kolor prostopadle do linii, bierze piksel najdalej od bieli (`d = abs(b-255)+abs(g-255)+abs(r-255)`) — mediana z 9 (potem 15 po scaleniu) probek. Sprawdz czy to metoda odporna na JPEG/skan artefakty czy raczej zrodlo "losowego" koloru czerwony/zielony (szum na granicy linii, antyaliasing). |
| `backend/recognize/line_classifier.py` | `_role_for`/`_color_role_hint`: rola `wire` to DOMYSLNA gdy grupa nie ma pojedynczej roli. `is_connection_candidate` = `role == "wire"` (rola `"bus"` WYCOFANA wg komentarza linia 19-23 — sprawdz czy caly kod jest z tym spojny, np. `ROLE_COLORS_BGR` w `scripts/preview_lines.py:28` nadal ma klucz `"bus"`, martwy kod czy uzywany?). **KLUCZOWA OBSERWACJA do zweryfikowania:** `config/semantic-colors.yaml` NIE MA zdefiniowanej grupy dla koloru **czerwonego** w ogole (tylko `cable`=czarny, `motor_device`=niebieski, `inverter`=fiolet, `enclosure`=zielony `#00AA44`, `dashed_aux`=szary, `pe_wire`=zielony `#00AA44` — **`enclosure` i `pe_wire` maja IDENTYCZNY stroke `#00AA44`**, co czyni `ColorPalette.match_color` niejednoznacznym miedzy tymi dwiema grupami dla kazdej zielonej linii — rozstrzyga kolejnosc w dict, nie semantyka). To bezposrednio tlumaczy zglaszany objaw "kolory czerwony/zielony losowe": (a) czerwony nie ma dopasowania -> `semantic_group=""`, rola pozostaje `wire` ale bez `pe`/specjalnej klasyfikacji; (b) zielony dostaje losowo (wg kolejnosci w YAML) `enclosure` LUB `pe_wire` -> wplywa na `_kind_for_net` w `net_builder.py:295-300` (`kind="pe"` tylko gdy trafi w `pe_wire`, nie w `enclosure`). **To do potwierdzenia/odrzucenia w analizie z realnymi probkami kolorow z p027/p035/p040.** |
| `backend/recognize/line_sieve.py` | `_is_box_edge` (linia ~119-142): demotuje do `frame` linie rownolegle do boku bbox z pokryciem >= `EDGE_OVERLAP_MIN=0.6`. Rozwaz: dla listwy zlaczkowej gdzie zlaczki stoja w rzedzie CIASNO obok siebie (p027, y≈2905, x 541-6004, 58 sztuk), pozioma szyna laczaca je bedzie w duzej czesci geometrycznie "rownolegla i blisko" gornej/dolnej krawedzi wielu bboxow pod rzad — sprawdz czy `_is_box_edge` (petla `for c in components`) fałszywie lapie fragmenty tej szyny jako "obrys" pojedynczych zlaczek zamiast przewodu przechodzacego. `_containing_component`/`_bridges_two_terminals`: dziala tylko dla linii CALKOWICIE wewnatrz JEDNEGO bboxa — nie pokrywa przypadku "linia miedzy dwoma sasiednimi bboxami przechodzi tuz nad/pod trzecim". |
| `backend/recognize/arrow_supplement.py` | Fallback szablonowy dziala dla brakujacego recall (p040: 2 strzalki znalezione w pelnym pipeline vs 0 w samym YOLO). Ale Filip zglasza ogolnie: "arrows worst — missing recall, NOT wej/wyj confusion" — sprawdz czy `arrow_supplement` pokrywa **obie** klasy (`strzalka_potencjalu_wejsciowa`/`wyjsciowa`, linia 20-23) i czy `roi_top_frac=0.93` (config linia 54, uzywane jako "gorne" ale nazwa `roi_top_frac` z `cutoff = roi_frac * gray.shape[0]` filtrujace `y > cutoff` czyli w istocie ODRZUCA hity PONIZEJ cutoff, czyli ROI to GORNE 93% wysokosci — zweryfikuj czy to zamierzone, nazwa jest myląca) nie ucina prawidlowych trafien np. na p035 gdzie "one wyjsciowa at edge" (mozliwe ze przy samej krawedzi strony, blisko marginesu ROI). |
| `labeler/app.py` | `/api/derive-terminals` (linia 142-155) i `/api/derive-terminals-page` (180-194) — TEN SAM algorytm co runtime (`derive_auto_terminals`), z `tol` domyslnie 12.0 z body (nie ze `config/runtime.yaml` — sprawdz spojnosc: JS wysyla `terminalTol()` z `crop_review.js:96-98` liczone identycznie jak `_terminal_tol` w `graph_builder.py:210-219`, OK zsynchronizowane recznie — ryzyko driftu przy zmianie configu, bo JS ma stala `0.012`/`12` zaszyta w kodzie, nie czyta `config/runtime.yaml`). |
| `labeler/static/crop_review.js` | Tryb `"terminal"`: `enterTerminalMode()` (~306) wola `deriveTerminalsForPage()` (~104) TYLKO raz per strona (`pageTerminalsDerived` flag), **NIE nadpisuje** recznych terminali (`if (b.terminals && b.terminals.length) continue` — linia ~128). Sprawdz czy UI ma juz mechanizm "zapisz ten zestaw terminali jako wzorzec dla calej klasy X" (prawdopodobnie NIE — do zaprojektowania w sekcji 5/7). |
| `config/semantic-colors.yaml` | Patrz obserwacja wyzej (brak czerwonego, kolizja `enclosure`/`pe_wire`). Zaproponuj czy dodac np. grupe `phase_wire`/`red_wire` i/lub naprawic kolizje stroke. |
| `config/runtime.yaml` | `terminal_tol_frac: 0.012`, `terminal_tol_min: 12.0` -> ~84px na stronie 6600px szer/wys (potwierdz przelicznik: `max(12, 0.012*6600)=79.2px`, w promptcie Filipa podano "~84px" dla nieco innej rozdzielczosci — dopasuj do faktycznego rozmiaru p027/p035/p040, sprawdz `cv2.imread(...).shape`). `hough_min_len_frac: 0.02`, `hough_gap_frac: 0.0015` -> na 6600px: `min_len=132px`, `gap=9.9px` (floor 4). `roi_bottom_cut_frac: 0.93`. `connection_require_terminal: true`. |

---

## 4. Lista hipotez do zweryfikowania (z realnymi danymi, nie samym czytaniem kodu)

Dla kazdej: potwierdz/odrzuc + dowod (liczba/zrzut/cytat).

### 4.1 Fragmentacja linii (dlugie przewody znikaja)
- **H1:** `_merge_collinear` w `line_tracer.py` ma stala `gap_tol=12px` niezalezna od rozdzielczosci strony — na 6600px stronie to zbyt malo by sklejac realne przerwy w druku/skanie dlugiej szyny.
- **H2:** Nawet po sklejeniu w `LineTracer`, `_group_into_nets` (union-find w `net_builder.py`) **odmawia** laczenia dwoch segmentow, jesli miejsce styku wypada na terminalu/komponencie (`_point_at_node`) — co jest **zamierzone** dla odczepow, ale w przypadku szyny przechodzacej DOKLADNIE przez rzad zlaczek (p027) moze rozbijac jeden fizyczny przewod na N niepowiazanych `net`-ow zamiast jednego potential z N odczepami. Sprawdz: czy to jest w ogole zle (bo N odczepow na wspolnym potencjale to WLASNIE ten przypadek "net z >2 symbolami" ktory kod juz obsluguje w `build_connections` linia 60-67), czy problem lezy calkowicie ZANIM (linie nigdy nie docieraja jako kandydaci wire, bo `line_sieve`/Hough je gubi/demotuje).
- **H3:** `line_sieve._is_box_edge` falszywie demotuje fragmenty bus wire przebiegajacej blisko/wzdluz gornych krawedzi rzedu zlaczek do roli `frame`.

### 4.2 Kolory losowe czerwony/zielony
- **H4:** patrz sekcja 3 (`line_classifier.py`/`semantic-colors.yaml`) — brak grupy dla czerwonego + kolizja `enclosure`/`pe_wire` na zielonym.
- **H5:** `_sample_color` w `line_tracer.py` probkuje niestabilnie na granicach linii (antyaliasing/JPEG) — sprawdz rozrzut hex dla tej samej fizycznej linii miedzy kolejnymi uruchomieniami/tile'ami (tiled inference moze probkowac ten sam przewod w dwoch nakladajacych sie tile'ach z lekko innym wynikiem).

### 4.3 Sito demotuje prawdziwe przewody
- **H6:** patrz H3. Dodatkowo sprawdz `EDGE_OVERLAP_MIN=0.6` — czy dla listwy 58 zlaczek próg pokrycia 60% wzgledem KROTSZEGO zakresu (`_overlap_frac`) jest zbyt niski (latwo osiagalny nawet dla przewodu, nie tylko obrysu).

### 4.4 Auto-derive zawodzi na zlaczce (p027)
- **H7:** YOLO widzi 58 `zlaczka` w rzedzie (y≈2905, x 541-6004) — symbole OK. Ale brakuje poziomej szyny -> `derive_auto_terminals` nie ma z czego wyprowadzic terminali (`contacts` puste, bo brak linii wire dotykajacej bboxa w tym miejscu) -> zlaczki zostaja BEZ terminali -> `_resolve_node` z `require_terminal=True` (config: `connection_require_terminal: true`) zwraca `None` dla kazdego konca -> zero polaczen. **To prawdopodobnie GLOWNA przyczyna p027**: problem nie jest w derive_auto_terminals per se, tylko w tym ze WEJSCIOWA linia (szyna) nigdy nie dotarla jako kandydat do tego kroku. Potwierdz sprawdzajac faktyczne `graphic_lines` (role) w okolicy y≈2905 na p027 przez `preview_lines.py`/`preview_schema.py`.
- **H8 (kontrapunkt/alternatywa):** Moze linia bus TAM JEST wykryta poprawnie jako `wire`, ale `derive_auto_terminals`'s `dedup=min(tol,15.0)=12px` scala sasiednie stuby GDY zlaczki stoja gesciej niz 12px od siebie brzeg-do-brzegu (rozstaw 58 zlaczek na ~5463px szerokosci = ~94px/zlaczke, wiec per-zlaczka mieszczą się 2 terminale przy szerokosci bboxa < ~24px — mozliwe dla waskich zlaczek). Zweryfikuj faktyczna szerokosc pojedynczego bboxa zlaczka z detection JSON.

### 4.5 Arrows — recall, nie confusion
- **H9:** Braki recall strzalek sa w warstwie YOLO surowej (0 detekcji na p040 bez `arrow_supplement`), NIE w klasyfikacji wej/wyj. `arrow_supplement` czesciowo laty ten problem (2/N na p040), ale nie w pelni (p035: `strzalka_wejsciowa x3 conf 0.39-0.45` — niska pewnosc mimo ze to juz supplement czy czysty YOLO? sprawdz zrodlo tych detekcji w danych z preview_detection). Rozwaz: czy warto rozszerzyc galerie szablonow (`_template_gallery`, max 12/klase) lub czy to problem danych treningowych (mala reprezentacja klasy w `data/labeled_tiled`).

---

## 5. Proponowana architektura: `TerminalResolver`

Szkic do zweryfikowania/skorygowania po analizie (NIE architektura ostateczna — Twoim zadaniem jest ja doprecyzowac na bazie znalezisk):

```
TerminalResolver.resolve(component, lines, image_bgr, patterns) -> list[Terminal]
  1. Jesli component.type ma pattern w terminal-patterns.yaml:
     a. policz kandydatow geometrycznych: derive_auto_terminals (linie) LUB
        perimeter-scan a la derive_mostek_terminals (tusz na obwodzie) — wybor
        metody per-klasa w patternie (np. zlaczka/mostek/listwa -> perimeter,
        inne -> line-contact)
     b. dopasuj kandydatow do oczekiwanych pozycji z patternu (edge+frac),
        w tolerancji terminal_tol; brakujace pozycje z patternu -> uzupelnij
        (nawet bez lokalnego dowodu linii, bo pozycja jest wlasnoscia klasy)
     c. odrzuc kandydatow NIE pasujacych do zadnej pozycji z patternu (szum)
  2. Jesli brak patternu dla klasy: fallback do dzisiejszego derive_auto_terminals
     (degradacja lagodna, nie crash)
  3. Walidacja terminal-to-terminal (sekcja 1) na etapie build_connections:
     odrzuc `wire` segmenty, ktorych ZADEN koniec nie rozwiazuje sie do
     (component, terminal) po kroku 1-2 dla OBU komponentow docelowych
```

Pytania architektoniczne do rozstrzygniecia w analizie:
- Gdzie zyje `TerminalResolver` — nowy plik `backend/recognize/terminal_resolver.py`, czy rozszerzenie `net_builder.py`?
- Czy `terminal-patterns.yaml` edytowany recznie przez Cursor/Filip, czy generowany z labelera (eksport z GT po korekcie)? (Filip: "auto derive -> Filip koryguje -> zapisz jako class pattern" sugeruje eksport z labelera — potrzebny nowy endpoint `/api/save-terminal-pattern` czy podobny).
- Jak pattern radzi sobie z komponentami o zmiennej liczbie terminali w obrebie klasy (np. `listwa`/`zlaczka` czasem 1 stub, czasem 2 — wejscie+wyjscie)? Model pattern per-klasa z LISTA pozycji czy z REGULAMI (np. "co najmniej N na krawedzi X")?
- Czy `derive_mostek_terminals` powinien zostac jako odrebna funkcja (dziala!) i pattern dla `mostek` po prostu deleguje do niej, zamiast probowac ujednolicic wszystko w jednym mechanizmie?

---

## 6. Dane do zebrania lokalnie (RTX PC — masz dostep, Cursor nie ma)

1. `python scripts/preview_schema.py --page p027 --source both` i analogicznie dla `p035`, `p040` — porownaj GT vs runtime overlay, szczegolna uwaga na okolice y≈2905 (p027, rzad zlaczek) i x≈320 (p035, strzalki wejsciowe).
2. `python scripts/preview_lines.py --page data/raw/<p027-plik>.png` — sprawdz role (`wire`/`frame`/`other`) przypisane liniom w okolicy rzedu zlaczek p027. To bezposrednio zweryfikuje H3/H6/H7.
3. `python scripts/preview_detection.py ...` (jak Filip juz robil dla smoke, conf=0.25, tiled) — jesli jest flaga do zrzutu surowego JSON detekcji, zapisz pelne bboxy zlaczek p027 zeby policzyc realny rozstaw/szerokosc (H8).
4. Sprawdz czy istnieje `line_diag`-podobny skrypt (`scripts/diag_coords.py`? sprawdz tresc) — jesli nie ma dedykowanej diagnostyki linia-po-linii z kolorem hex + rola + semantic_group, rozwaz zaproponowanie malego skryptu diagnostycznego (read-only, do sync/analysis, NIE do produkcyjnego kodu) jako czesc analizy.
5. Zbierz histogram `detected_color` (hex) dla linii sklasyfikowanych jako `wire` bez `semantic_group` (puste) na wszystkich 3 stronach — to bezposredni dowod na H4/H5.
6. Zmierz realny rozmiar obrazu (`cv2.imread(...).shape`) dla p027/p035/p040 zeby podac dokladne efektywne `terminal_tol`/`hough_*` w px (nie przyblizenia z tego promptu).

Zapisz surowe dane/wnioski z tego kroku do `sync/fable5-smoke-context.md` (jeśli uznasz za przydatne do przyszlych analiz — opcjonalne wg dyspozycji Filipa).

---

## 7. Proponowany podzial na prompty Cowork (do implementacji PO akceptacji analizy)

Zaproponuj (i skoryguj wg wlasnych ustalen) konkretny zakres dla:

- **`018-lines-quality.md`** — naprawa `LineTracer`/`line_sieve` dla dlugich fragmentowanych szyn (p027 bus wire), skalowanie `gap_tol` z rozmiarem strony, korekta `_is_box_edge`/`EDGE_OVERLAP_MIN` dla rzedow gesto ulozonych symboli, naprawa `semantic-colors.yaml` (czerwony + kolizja enclosure/pe_wire).
- **`018-terminals-strategy.md`** — `TerminalResolver` + `config/terminal-patterns.yaml` + endpoint(y) labelera do zapisu wzorca klasy + walidacja terminal-to-terminal w `build_connections`.

Podaj: kolejnosc (ktory pierwszy — Filip juz zasugerowal 1) lines, 2) terminals), zaleznosci miedzy nimi (terminale zalezy od jakosci linii wejsciowych — TerminalResolver dla klas "line-contact" nie zadziala dobrze dopoki linie sa zle), przyblizony zakres plikow, i draft kryteriow akceptacji per prompt (miary: recall bus wire p027, % zlaczek z terminalami, F1 connections na val-pages via `eval_val_pages.py`).

OCR pozostaje odlozone — nie planuj dla niego promptu w tej rundzie.

---

## 8. Ograniczenia (twarde)

- **Zakaz cloud API** w `backend/recognize/`, `train/`, `labeler/` (reguła projektu, offline-only).
- **Nie zmieniaj** kontraktu `SchemaModel` (pola/typy w `backend/models/schema.py`) bez zgody Cursor.
- **Union-find w `net_builder.py`** (`_group_into_nets`/`_lines_joined`/`_point_at_node`) jest wrazliwy — zmiany tu maja szeroki wplyw na wszystkie polaczenia, nie tylko na przypadek p027. Kazda proponowana zmiana w tej funkcji w planie 018 musi miec jawnie wypisane ryzyko regresji dla mostkow/odczepow, ktore juz dzialaja.
- **Sieve (`apply_sieve`) jest zawsze WLACZONY** w `graph_builder.py` krok 3b — nie opcjonalny w configu. Plan nie powinien proponowac flagi wylaczajacej go, tylko poprawki logiki.
- Sito i `derive_mostek_terminals` dla klasy `mostek` dzialaja dobrze — nie przepisuj od zera bez wyraznego dowodu na regresje.
- GPU RTX 2080 = twardy limit (YOLO nano/ONNX/batch<=8) — nie dotyczy tej analizy (bez treningu), ale pamietaj przy planowaniu ewentualnych zmian w `arrow_supplement`/template matching (CPU, OK).

---

## Pytania do Filipa

*(pelna lista + kontekst: sekcja "Pytania do Filipa" w findings)*

1. Hex realnych kolorow przewodow (PE-zielony, fazowy-czerwony) z pipety na p027/p035 — do kalibracji `semantic-colors.yaml`.
2. Zlaczka p027: czy odczep gora/dol (do glifu strzalki) to terminal zlaczki, czy strzalka to osobny symbol z wlasnym terminalem?
3. Glify strzalek przy zlaczkach p027 — doznaczyc jako klasa 7/8 przed retrainem, czy czesc symbolu zlaczki?
4. `git status`/`pytest` na glownym PC po commicie (kopia ZW miala artefakty synchronizacji plikow).

---

## Wynik

**Findings:** [`sync/analysis/019-terminals-lines-findings.md`](../analysis/019-terminals-lines-findings.md) (2026-07-04, Fable 5)

**TL;DR:** Glowna przyczyna p027 odtworzona empirycznie na kaflach `labeled_tiled`: szyna listwy jest przerywana kolkami wezlow co ~94 px (segmenty tuszu 67–76 px, przerwy 21–22 px), a runtime Hough ma `min_len=132 > 76` i `gap=10 < 21` — szyna w 100% niewidoczna, stad zero terminali i zero connections. Sito NIE jest winne (szyna biegnie przez SRODKI bboxow, 40 px od krawedzi). Po naprawie Hougha ujawnia sie druga warstwa: `_point_at_node` blokuje union-find w calym pasie listwy (46 netow vs 5), `_nodes_on_net` widzi tylko KONCE linii (scalona szyna -> 2 wezly na 16 zlaczek), a `terminal_tol=79 px` przy pitchu 94 px daje 6–10 falszywych terminali/zlaczke. Kolory: brak grupy czerwieni + remis `enclosure`/`pe_wire` rozstrzygany kolejnoscia dict (zielen ZAWSZE enclosure, `kind=pe` nigdy). Plan: 018-lines-quality najpierw, potem 018-terminals-strategy (szczegoly + kryteria akceptacji w findings §5).

**Status hipotez (final, po raporcie `019_diag_main.py` z main — findings §7b):** H1 ✅ (wtorna), H2 ✅, H3 ❌ (dla p027), H4 ⚠️ bledy kodu realne, ale NIE przyczyna objawu (strony nie maja czerwonego/zielonego tuszu — objaw to kolory OVERLAYU: zielony=wire, czerwony=Connection w preview_schema), H5 ❌ (deterministyczne, 0 roznic), H6 ❌ (nie bloker), H7 ✅ **glowna przyczyna, potwierdzona w pelnej skali** (szyna p027: segmenty 73-74 px < min_len 132, przerwy 21-22 px > gap 10; pelnostronicowy trace = 0 linii w pasie listwy), H8 ❌ (problem odwrotny: tol kontaktu za duzy), H9 ✅ zamkniete (p040 supplement dziala 0→2; p027: 15× wyjsciowa = TP brak w GT; mechanizm `c not in have` kruchy na p035). Nowe: niebieski tusz #134088/#105090 nie laczy sie z `motor_device` #0066CC (pusta grupa); GT terminali zlaczki 6/533 — pattern to decyzja Filipa, nie ekstrakcja z GT.

**Review Cursor (2026-07-04):** findings zaakceptowane — [`018-lines-quality.md`](018-lines-quality.md) aktywne, [`018-terminals-strategy.md`](018-terminals-strategy.md) kolejka. Szczegoly: findings § Poprawka (runda 1).

**Ograniczenie:** sesja na PC ZW bez `data/raw`/GT DB — kroki sekcji 6 wymagajace pelnych stron/kolorow rozpisane dla Filipa w findings §6.
