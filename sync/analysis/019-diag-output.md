# 019 diag — wynik z glownego PC

## A. Rozmiary stron + efektywne progi

- p027: 6617x4678 -> hough min_len=132 px, gap=10 px, terminal_tol=79.4 px
- p035: 6617x4678 -> hough min_len=132 px, gap=10 px, terminal_tol=79.4 px
- p040: 6617x4678 -> hough min_len=132 px, gap=10 px, terminal_tol=79.4 px

## B. Run-length tuszu na szynie p027 (pas y 2820-3000)

- y szyny: 2945, tusz w wierszu: 3901/6617 px
- segmenty tuszu: n=61 min/med/max = 2/73/74 px
- przerwy: n=58 med=21 px; przerwy<=60px (kolka): n=55 min/med/max = 21/21/22 px

## C. Kolory (Q1 z findings + H5)

### p027
- czy strona kolorowa: TAK
- top kolory nasycone (kwant. 32): #105090 x65391, #103050 x11857, #305090 x1309, #103090 x1127, #303050 x792, #5070b0 x547, #7090b0 x460, #305070 x305, #90b0d0 x302, #b0b0d0 x240
- rola dash: 17 linii, top hex: #959595 x2, #636363 x2, #838383 x2, #9b9b9b x2, #858585 x1, #717171 x1
- rola wire: 149 linii, top hex: #000000 x125, #ffffff x6, #134088 x3, #2b2b2b x2, #cecece x2, #cdcdcd x1
- wire BEZ semantic_group (H4): #ffffff x6, #134088 x3, #cecece x2, #cdcdcd x1, #fbfbfb x1, #f1f1f1 x1, #fcfcfc x1, #1e2f53 x1
- stabilnosc _sample_color 2 przebiegow (H5): roznych probek 0 (0 = deterministyczne)

### p035
- czy strona kolorowa: TAK
- top kolory nasycone (kwant. 32): #105090 x71259, #103050 x11857, #1050b0 x2838, #305090 x1452, #103090 x1128, #303050 x792, #7090b0 x787, #5070b0 x756, #90b0d0 x740, #3070b0 x366
- rola dash: 12 linii, top hex: #959595 x2, #4e4e4e x2, #575757 x1, #5c5c5c x1, #717171 x1, #6f6f6f x1
- rola wire: 255 linii, top hex: #000000 x234, #134088 x4, #c4c4c4 x2, #050505 x2, #0f0f0f x2, #cdcdcd x1
- wire BEZ semantic_group (H4): #134088 x4, #c4c4c4 x2, #cdcdcd x1, #f1f1f1 x1, #e8e8e8 x1, #1e2f53 x1, #d8d8d8 x1, #ffffff x1
- stabilnosc _sample_color 2 przebiegow (H5): roznych probek 0 (0 = deterministyczne)

### p040
- czy strona kolorowa: TAK
- top kolory nasycone (kwant. 32): #105090 x65391, #103050 x11857, #305090 x1309, #103090 x1127, #303050 x792, #5070b0 x547, #7090b0 x460, #305070 x305, #90b0d0 x302, #b0b0d0 x240
- rola dash: 8 linii, top hex: #9d9d9d x1, #6f6f6f x1, #737373 x1, #777777 x1, #999999 x1, #868686 x1
- rola wire: 223 linii, top hex: #000000 x197, #134088 x4, #ffffff x2, #020202 x2, #1f1f1f x2, #acacac x1
- wire BEZ semantic_group (H4): #134088 x4, #ffffff x2, #acacac x1, #ececec x1, #f1f1f1 x1, #1e2f53 x1, #d8d8d8 x1, #f2f2f2 x1
- stabilnosc _sample_color 2 przebiegow (H5): roznych probek 0 (0 = deterministyczne)

## D. Linie w pasie listwy p027 (y 2850-2960)

- linii w pasie: 0 (poziomych: 0), role: {}

## E. GT terminale per klasa (SQLite) — Q2

- -KS2_12: 1 bbox, z terminalami 1, rozklad liczby terminali: {2: 1}
- Strzałka potencjału (wejściowa): 63 bbox, z terminalami 6, rozklad liczby terminali: {0: 57, 1: 6}
- Strzałka potencjału (wyjściowa): 162 bbox, z terminalami 5, rozklad liczby terminali: {0: 157, 1: 5}
- Stycznik odcinajacy sekcje 12: 1 bbox, z terminalami 1, rozklad liczby terminali: {1: 1}
- mostek: 176 bbox, z terminalami 6, rozklad liczby terminali: {0: 170, 1: 3, 3: 3}
- przekaźnik: 45 bbox, z terminalami 4, rozklad liczby terminali: {0: 41, 2: 4}
- relay: 6 bbox, z terminalami 5, rozklad liczby terminali: {0: 1, 2: 5}
- styk NC: 20 bbox, z terminalami 2, rozklad liczby terminali: {0: 18, 2: 2}
- styki: 164 bbox, z terminalami 2, rozklad liczby terminali: {0: 162, 2: 2}
- terminal PLC: 121 bbox, z terminalami 3, rozklad liczby terminali: {0: 118, 1: 3}
- terminal_plc: 79 bbox, z terminalami 2, rozklad liczby terminali: {0: 77, 1: 2}
- wyłącznik nadprądowy: 10 bbox, z terminalami 1, rozklad liczby terminali: {0: 9, 2: 1}
- wyłącznik różnicowo-prądowy: 1 bbox, z terminalami 1, rozklad liczby terminali: {4: 1}
- złączka: 533 bbox, z terminalami 6, rozklad liczby terminali: {0: 527, 1: 3, 2: 1, 3: 2}

## F. Strzalki: YOLO raw vs po supplement (H9)

- p027: raw YOLO {'wejsciowa': '0', 'wyjsciowa': '15 (conf 0.25-0.73)'} | po supplement {'wejsciowa': '0', 'wyjsciowa': '15 (conf 0.25-0.73)'}
    UWAGA: strzalka_potencjalu_wyjsciowa ma 15 raw detekcji -> supplement WYLACZONY dla tej klasy (findings H9b — 1 FP blokuje uzupelnienie)
- p035: raw YOLO {'wejsciowa': '3 (conf 0.39-0.45)', 'wyjsciowa': '1 (conf 0.92-0.92)'} | po supplement {'wejsciowa': '3 (conf 0.39-0.45)', 'wyjsciowa': '1 (conf 0.92-0.92)'}
    UWAGA: strzalka_potencjalu_wejsciowa ma 3 raw detekcji -> supplement WYLACZONY dla tej klasy (findings H9b — 1 FP blokuje uzupelnienie)
    UWAGA: strzalka_potencjalu_wyjsciowa ma 1 raw detekcji -> supplement WYLACZONY dla tej klasy (findings H9b — 1 FP blokuje uzupelnienie)
- p040: raw YOLO {'wejsciowa': '0', 'wyjsciowa': '0'} | po supplement {'wejsciowa': '2 (conf 0.99-1.00)', 'wyjsciowa': '0'}

