Loop 032 v2: konwergencja runtime → GT, pętla OODA (Cursor /loop)

Cel nadrzędny: recognize_file() ma odtwarzać graf z gt/<page_id>.json. Metryka: średni SCORE stron GT (p028, p029, p030, p031, p033, p034) bez regresji żadnej strony. GT = wzorzec absolutny.

To NIE jest pętla strojenia parametrów. Baseline pokazuje błędy strukturalne (p031=0.00 — 100% linii GT nietrafione; p034=6.18 — 101 komponentów only_gt). Takich kubłów nie naprawi próg w YAML — wymagają nowej logiki lub przebudowy algorytmu. Każda iteracja to pełny cykl OODA:

1. OBSERWUJ


Score wszystkich stron GT masz w stanie loopa — nie przeliczaj wszystkiego co turę. Re-score pełny tylko przed akceptacją decyzji.
Dla wybranego kubła zbierz DANE DIAGNOSTYCZNE, nie zgaduj: raport --json z diff_gt_runtime, scripts/diag_lines.py, liczniki z pipeline. Pytanie: CO konkretnie runtime gubi (które linie/komponenty, gdzie na stronie, jaka wspólna cecha)?
Konsola Windows cp1250: uruchamiaj z PYTHONIOENCODING=utf-8 (UnicodeEncodeError na Δ = znany błąd, nie problem scoringu).


2. ORIENTACJA

Sklasyfikuj przyczynę źródłową kubła (jedna linia diagnozy w logu):


(a) parametr — logika dobra, próg zły,
(b) brak logiki — pipeline w ogóle nie ma mechanizmu (np. nie śledzi linii przez przecięcia, nie skleja szyn, nie widzi klasy obiektu),
(c) błąd algorytmu — mechanizm jest, ale działa źle strukturalnie,
(d) [MODEL] — brak w YOLO → lista do retrainu, pomiń.


Reguła anty-dłubaniu: ta sama rodzina parametrów max 2 próby na kubeł. Kubeł dalej dominuje → przyczyna to (b) lub (c), przejdź na poziom L2/L3. Strona ze score <15 z definicji ma przyczynę (b)/(c), nie (a).

3. DECYZJA

Wybierz poziom interwencji i zadeklaruj oczekiwany efekt (które strony, ile pkt):


L1 — parametr: zmiana w config/*.yaml (1 tura).
L2 — heurystyka: nowa/przebudowana funkcja w istniejącym module recognize (1–2 tury).
L3 — przebudowa: nowy moduł / wymiana algorytmu (np. tracer wektorowy zamiast Hough, skeleton-based line following, łączenie segmentów grafowo). Budżet do 3 tur, plan 3–5 kroków zapisany w stanie loopa. Score oceniasz PO ukończeniu całości, nie po każdym kroku.


Kolejność atakowania: kubeł strukturalny obecny na ≥2 stronach > kubeł jednostronicowy > kosmetyka. Tags/OCR (waga 0.10) na końcu.

4. WYKONAJ


Implementacja + test celowany (pytest modułu). Nowa logika = nowy test.
Re-score: najpierw strony docelowe decyzji; Δ>0 → pełne 6 stron.
Akceptacja per DECYZJA (nie per edycja): Δśredniej > 0 ORAZ żadna strona −1.0 pkt. Inaczej → revert całej decyzji (git), wróć do Orientacji z wnioskiem CZEGO się dowiedziałeś.
Co 3 zaakceptowane decyzje: python scripts/eval_val_pages.py — regresja → revert.
Nowe progi wprowadzone przez L2/L3 → config/*.yaml + runtime_config.py, nie hardcode.


Eskalacja do Filipa (JEDNO pytanie, opcje numerowane z rekomendacją)


L3 wymaga zmiany kontraktu (backend/models/schema.py, backend/protocols/, SchemaModel JSON) — zaproponuj, nie wykonuj,
podejrzenie błędu w GT (nie edytuj GT),
decyzja poprawia ≥2 strony, psuje 1 o >1 pkt,
score skacze >20 pkt po kosmetyce (błąd metryki?),
plan L3 po 3 turach nieukończony — pytanie: kontynuować (budżet +2) czy revert.


NIE pytaj o zgodę na L2/L3 wewnątrz backend/recognize/ — to jest istota tego loopa.

STOP gdy


Δśredniej < 1.0 przez 3 kolejne ZAAKCEPTOWANE decyzje (plateau), lub
12 decyzji, lub
zostały tylko kubły (d) [MODEL] → wypisz klasy do retrainu (dataset z GT, yolo_conf ≥ 0.18), lub
Filip STOP.


Po STOP: pełny pytest backend/tests labeler/tests; wpis w sync/filip-to-zw.md (tabela per strona start→koniec, lista decyzji L1/L2/L3 z diagnozami, kubły [MODEL]); sync/commit-message.txt: [Cursor] loop 032: śr. GT X→Y (N decyzji).

Zakazy (twarde)


Kontrakty: backend/models/schema.py, backend/protocols/, format gt/*.json — tylko przez eskalację.
Nie zmieniaj metryki ani config/eval-weights.yaml.
Nie edytuj gt/*.json ani DB adnotacji; data/schemagen.db = cache (CLAUDE.md).
Zakaz cloud API w backend/recognize/ — wszystko offline, RTX 2080, venv .venv311 (OCR .venv-ocr).


Ekonomia


Nie czytaj docs/, sync/analysis/, historii JSONL. Fragmenty plików (grep + zakres), nie całość.
Log decyzji: D3 [L2] diagnoza: tracer gubi linie przy skrzyżowaniach | nowy _cross_gap() line_tracer.py | śr 19.7→24.1 | ACC.
Stan loopa (sync/loop-032-state.json): scores per strona, ranking kubłów z diagnozami, aktywny plan L3, licznik decyzji.