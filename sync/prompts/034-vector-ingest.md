# Zadanie 034: Ekstrakcja wektorowa z PDF — linie i tekst bez rozpoznawania

**Status:** AKTYWNE — zastępuje 033 (loop Hougha WSTRZYMANY)
**Model:** Opus 4.8, tryb zadaniowy (NIE loop — uzasadnienie na końcu)
**Data ustalenia:** 2026-07-19

## Ustalenie — zmierzone, nie hipoteza

`sync/sources/22_A_153_PL_Adamed_AGV_SA2_20250706.pdf`, strona 28 (`d[27]`):

```
stron: 200 | sciezek: 929 | slow: 441

{'items': [('l', Point(1133.86, 830.66), Point(1190.55, 830.66))],
 'type': 's', 'color': (0.0, 0.0, 0.0), 'width': 0.7087, 'dashes': '[] 0', ...}

('Arkusz', bbox=(1136.69, 822.84, 1155.11, 829.18))
```

**Linie schematu są w PDF zapisane wprost.** Początek, koniec, grubość, kolor, wzór kreskowania.

Dotychczas: `backend/ingest/__init__.py` robi `page.get_pixmap(dpi=...)` → PNG → Hough → detekcja linii z pikseli. Wynik na p028: `P=0.248 R=0.768 F1=0.375`, 158 segmentów runtime wobec 42 linii GT.

Rasteryzujemy dane, które mamy wprost, a potem próbujemy je odtworzyć.

## Cel

Nowa ścieżka `vector` obok istniejącej `raster`. **Nie usuwać rastrowej** — SchematWRT01 lub przyszłe skany mogą jej wymagać. Wybór ścieżki: automatyczny (`len(get_drawings()) > 0`), z możliwością wymuszenia.

## Zakres

### 034a — ekstraktor (`backend/ingest/vector.py`, NOWY)

```python
def extract_vector_page(pdf_path, page_no, dpi) -> VectorPage
```

Zwraca w **pikselach PNG** (mnożnik `dpi/72`, ta sama skala co `pdf_to_png`):

- `lines`: segmenty z `get_drawings()` — `items` typu `'l'` (linia) i boki `'re'` (prostokąt), z `color`, `width`, `dashes`
- `curves`: `'c'` — na razie tylko liczone, nie używane
- `words`: `get_text('words')` → tekst + bbox

**Kontrakt:** ta sama przestrzeń współrzędnych co GT (piksele PNG w `pdf_dpi()`). Bez tego nic się nie zwaliduje.

### 034b — filtr treści schematu

929 ścieżek ≠ 42 linie GT. W nadmiarze są: ramka arkusza, tabliczka rysunkowa, kreski wewnątrz symboli, siatka.

Filtruj po **znanej geometrii i atrybutach**, nie po progach dobieranych na oko:

1. ramka i tabliczka — pozycja przy krawędziach + `roi_bottom_cut_frac` (już w configu)
2. kreski symboli — segmenty w całości wewnątrz bboxa wykrytego symbolu
3. `color` → `config/semantic-colors.yaml` (wire/bus już zdefiniowane; **kolor jest teraz dany, nie zgadywany z pikseli**)
4. `width` i `dashes` — linia sterowania vs zasilania vs odniesienia

Każde kryterium **osobno mierzalne** na p028: ile ścieżek odsiewa, ile prawdziwych linii gubi.

### 034c — scalanie segmentów

PDF potrafi zapisać jedną linię jako kilka kolinearnych segmentów. Scalać: ten sam kolor, szerokość, kolinearne, przerwa < tolerancja.

To jest jedyne miejsce w 034, gdzie występuje próg. Wszystko inne jest deterministyczne.

### 034d — wpięcie w pipeline

`GraphBuilder` bierze linie z `VectorPage` zamiast z `line_tracer`, gdy strona jest wektorowa. `net_builder` i emisja connections **bez zmian** — dostają lepsze wejście, nie nowy kontrakt.

Tolerancja terminala (`terminal_tol_*`) przy dokładnych końcach może zejść dramatycznie — ale **nie zmieniać jej w 034**. Najpierw pomiar z obecną, potem osobna decyzja.

## Walidacja — twarda

GT linii istnieje na 5 stronach: p028 (42), p029 (76), p030 (8), p033 (117), p040 (17).

```powershell
python scripts/diff_gt_runtime.py --page p028 --json
```

| Metryka | Dziś (Hough) | Próg akceptacji 034 |
|---|---|---|
| lines P | 0.248 | **≥ 0.85** |
| lines R | 0.768 | **≥ 0.90** |
| lines F1 | 0.375 | **≥ 0.87** |

Progi są wysokie **celowo**. Dane są dokładne co do ułamka punktu — jeśli wynik jest w okolicach 0,5, to znaczy że filtr (034b) jest zły albo skala się nie zgadza. Wtedy szukać błędu, nie obniżać progu.

Pierwszy sanity-check przed pisaniem filtra: **surowa liczba segmentów po odsianiu ramki i tabliczki, wobec 42 z GT**. Jeśli rząd wielkości się nie zgadza, dalsza praca nie ma sensu.

## Konsekwencja dla filaru OCR

`get_text('words')` daje treść i pozycję każdego słowa. Dla stron wektorowych **PaddleOCR (`.venv-ocr`) przestaje być potrzebny**.

Nie usuwać go w 034. Zmierzyć: `tags f1` na p028 z OCR i ze słowami z PDF (dziś `tags f1 = 0.043` — czyli praktycznie nie działa). Decyzja o wycofaniu OCR osobno, na podstawie liczb.

## Poza zakresem

- Usuwanie ścieżki rastrowej i `line_tracer.py`
- Zmiana `net_builder` / emisji connections
- Zmiana modelu YOLO i klas
- Zmiana wag SCORE
- Zmiana tolerancji terminala

## Dlaczego to NIE jest loop

Loop służy do szukania po omacku, gdy nie wiadomo, która zmiana pomoże — iteracja, pomiar, cofnięcie. Tu wiadomo, co zrobić: odczytać dane, które są w pliku.

Loop w tym zadaniu byłby szkodliwy: nagradzałby drobne poprawki metryki zamiast wymusić poprawny odczyt. Jeśli po 034 wynik jest 0,5 zamiast 0,9, właściwą reakcją jest znalezienie błędu w skali albo filtrze — nie dostrajanie progu, aż liczba urośnie.

Loop wraca **po** 034, na tym, co zostanie naprawdę niepewne: filtr treści schematu i scalanie segmentów.
