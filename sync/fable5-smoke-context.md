# Smoke context — terminale/linie (Filip, 2026-07-04)

Zrodlo: `preview_detection.py`, conf=0.25, tiled, model `symbols_tiled_v1-2`. Surowe
detekcje YOLO (bez `arrow_supplement`/pelnego pipeline), zapisane recznie przez Filipa
jako punkt wyjscia dla analizy Fable 5 (`sync/prompts/019-...`). Liczby przyblizone —
zweryfikuj na zywych danych, to jest tylko odczyt z podgladu, nie surowy JSON.

## p040

- 41 detekcji, YOLO-only: 0 `strzalka` (w pelnym pipeline `arrow_supplement` dokleja 2).
- 2 `mostek`.
- `zlaczka` rozproszone (3 w obszarze przekaznikow), NIE pelny rzad/strip.
- Duzo: `relay`, `styk_stycznika`, `terminal_plc`.

## p035

- 27 detekcji (malo).
- `zlaczka` rozproszone: y=1296, y=2443, y=2561 — brak zwartego paska.
- `strzalka_wejsciowa` x3 przy x≈320, conf 0.39-0.45 (niska pewnosc).
- 1x `strzalka_wyjsciowa` na krawedzi strony.

## p027

- 83 detekcje.
- **58x `zlaczka`** w jednym rzedzie, y≈2905, x od 541 do 6004 — symbole OK dla tego
  rzedu (YOLO widzi je poprawnie). Problem lezy w LINIACH: brak wykrytej poziomej
  szyny laczacej ten rzad -> to kandydat #1 na przyczyne "connections=0" dla tej listwy.
- Duzo FP `strzalka_wyjsciowa` (conf 0.25-0.72) w pasie y=2770-3015 — nakladajacym sie
  z obszarem listwy; mozliwe pomylenie fragmentow linii/symboli zlaczki ze strzalka.
- 2x `wylacznik_nadpradowy`, `terminal_plc`.
- 8x `mostek` przy roznych conf (0.39-0.82).

## Wnioski wstepne (do potwierdzenia przez Fable 5)

- Symbole (YOLO) sa w porzadku dla najgorszego przypadku (p027 rzad zlaczek) — problem
  NIE jest w detekcji, tylko w warstwie linii (brak bus wire) i/lub terminali
  (auto-derive nie ma z czego wyprowadzic terminali bez linii).
- FP `strzalka_wyjsciowa` w okolicy listwy p027 warto zweryfikowac czy to nie jest
  efekt uboczny fragmentow linii/symboli w gestym rzedzie mylonych z ksztaltem strzalki
  przez `arrow_supplement`/YOLO.
