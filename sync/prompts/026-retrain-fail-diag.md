# Zadanie 026: symbols_tiled_v1-3 — mAP50 = 0.0001, diagnoza eksportu

**Status:** BLOKUJĄCE (przed jakimkolwiek kolejnym treningiem)
**Model:** Opus 4.8 (diagnoza), potem Sonnet 5 na fix eksportu
**Nie uruchamiać ponownie treningu przed zamknięciem kroku 1.** 150 epok = godziny; przyczyna jest w danych, nie w hiperparametrach.

## Fakty

```
map50: 0.00010287     # praktycznie zero
epochs: 150, batch: 4, imgsz: 1536, model: yolov8n.pt
preview_batch --conf 0.18: 30 stron → 2 detekcje (obie `zlaczka`)
Ultralytics 8.4.67 ... CPU (Intel Core i7-9700KF)
```

mAP 0.0001 po 150 epokach to **nie** niedouczenie i nie zła klasa modelu. To etykiety, które nie pokrywają się z obrazem. Sieć nie ma czego dopasować.

## USTALONE 2026-07-19 — przyczyna główna: pusty zbiór treningowy

Rozkład klas w `data/labeled_tiled/labels/`:

```
relay 114 · led 56 · ekranowanie_kabla 44 · push_button 32 · strzalka_wej 28
emergency_stop 26 · strzalka_wyj 22 · ground 19 · gniazdo_rj_45 17 · cewka_zaworow 16
styki_przekaznika 16 · polaczenie_przewodow 15 · styk_nc 15 · styk_stycznika 14
zlaczka 10 · terminal_block 10 · przekaznik_polaryzowany 9 · mostek 7 · styki 5 · styki_nc 5
```

**Razem 480 bbox na 20 klas.** Klasy ogonowe: 5–10 przykładów. mAP ≈ 0 przy `yolov8n`, 1536 px, 150 epok to w tych warunkach wynik **oczekiwany**, nie usterka.

Przyczyna strukturalna — `config/val-pages.yaml` zawiera p028, p029, p030, p033 (+ p025/p035/p040/p045/p050 nieoznaczone). Z 6 stron GT:

| Strona | Split | GT |
|---|---|---|
| p028, p029, p030, p033 | **val** | pełne |
| p031 | train | pusta (~505 B) |
| p034 | train | 31 KB |

**Efektywny zbiór treningowy = jedna strona (p034).** Cały bogaty GT siedzi po stronie walidacyjnej.

Potwierdzenie pośrednie: `zlaczka` ma 10 przykładów, choć to najliczniejszy element na schematach — i jest jedyną klasą, którą model cokolwiek wykrył (2 detekcje na 30 stronach).

### DECYZJA Filipa 2026-07-19

**Opcja 1 — zamrozić tor modelu.** Aktywny pozostaje `symbols_tiled_v1-2`, conf 0.18. Nie trenować do czasu ~15–20 oznaczonych stron. `config/val-pages.yaml` **bez zmian** — baseline val 30.77 zachowany, porównania pozostają ważne.

`symbols_tiled_v1-3` nie wchodzi do `registry.json`. Wagi zostają w `data/runs/` jako artefakt nieudanego cyklu.

Zadanie Filipa: doznaczanie stron (priorytet: strony z `contactor` i `custom_urzadzenie` po stronie **train**, nie val).

Przed następnym treningiem wymagane: scalenie duplikatów klas (niżej) + `class_report.py --min-count 5` pokazujący ≥100 przykładów na klasę produkcyjną.

### Opcja odrzucona — przesunięcie splitu

Zostawić 2 strony val, resztę do train. Odrzucone: unieważnia baseline val 30.77, a **samo przesunięcie nie tworzy danych** — 480 bbox rozdzielone inaczej to nadal 480. Doznaczanie jest i tak konieczne, więc split zmieniamy dopiero razem z nowym materiałem.

Docelowo: 20 klas × ~100 przykładów ≈ 2 000 bbox. Dziś 480, czyli ~25 %.

### [BŁĄD] Duplikaty klas EN/PL — potwierdzone przez Filipa

W jednym `data.yaml` współistnieją nazwy angielskie (`relay`, `led`, `push_button`, `terminal_block`, `ground`, `emergency_stop`) i polskie (`zlaczka`, `mostek`, `styki_przekaznika`, `cewka_zaworow`) — **opisują częściowo te same elementy**. Pozostałość po mieszance GT v2 z label v1 / atlasem symboli.

Skutek: model uczy się sprzecznych celów na tym samym kształcie, a i tak niskie liczności są dodatkowo rozdzielone między dwie etykiety (`zlaczka` 10 + `terminal_block` 10 zamiast 20).

**Zadanie: scalenie przestrzeni klas — blokuje następny trening.**

1. `python scripts/visualize_class_crops.py` — przejrzeć crops per klasa, ustalić faktyczne pary duplikatów. Nie zgadywać po nazwie: `styki` / `styki_nc` / `styk_nc` / `styki_przekaznika` / `styk_stycznika` to pięć etykiet o niejasnym podziale i wymagają rozstrzygnięcia razem.
2. Mapa scaleń w `config/class-aliases.yaml`; kanoniczna nazwa **polska** — spójnie z GT v2 i resztą configów.
3. Alias stosowany w `dataset_export` **i** `tiled_export` przez wspólną funkcję. Nie duplikować logiki — to dokładnie ten rozjazd, który 023 musiał naprawiać.
4. Migracja istniejącego GT: skrypt idempotentny z `--dry-run`, zapis atomowy przez `gt_store` (niezmienniki `CLAUDE.md`).
5. Testy: GT z aliasem eksportuje się do jednego class_id; `class_report` po scaleniu bez nazw angielskich.

Kontrola po scaleniu: **suma bbox musi zostać 480** — scalenie zmienia przypisanie klas, nie tworzy i nie gubi etykiet. Inna liczba = błąd migracji.

Ponadto z listy retrain **brakuje w ogóle**: `contactor`, `custom_urzadzenie`, `urzadzenie`. Zgodne z ustaleniem, że pierwsze dwa są tylko na stronach val.

---

## Hipoteza poboczna — rozjazd skali GT ↔ obraz: OBALONA

```
plikow: 54 | pustych: 0 | bbox: 480 | poza [0,1]: 0
```

Wszystkie współrzędne w zakresie, żaden plik etykiet nie jest pusty. **`tiled_export` po przejściu na GT v2 (023) działa poprawnie** — nie ma rozjazdu skali ani zepsutej normalizacji. Poniższe kroki 1–3 zachowane jako procedura na przyszłość, ale w tym cyklu **nie są potrzebne**.

Konsekwencja dla 025: rozjazd skali **nie jest** wspólną przyczyną błędu labelera i porażki treningu. To dwie osobne sprawy — objaw „złe bboxy w labelerze" wymaga własnej diagnozy, hipoteza skali odpada.

Otwarte z it5 loop 032: `zlaczka GT x=5558 vs RT x=442, IoU=0` — skoro eksport jest zdrowy, ten rozjazd dotyczy ścieżki **runtime**, nie GT. Przenieść do 024 jako osobny wątek.

Poszlaki, wszystkie zbieżne:

1. `tiled_export` przełączony w 023 na `load_all_training_records()` (GT v2) — **zmiana świeża, nigdy nie zwalidowana wizualnie**. Poprzedni v1-2 uczył się poprawnie na starej ścieżce.
2. loop 032 it5: `zlaczka GT x=5558 vs RT x=442, IoU=0` — rozjazd współrzędnych ~12,6× był już obserwowany i **nigdy nie wyjaśniony**, tylko obejściem („brak bezpiecznej zmiany").
3. W repo istnieją `scripts/reingest_highdpi.py` i `scripts/scale_annotations.py` — historia zmian DPI. GT v2 mógł zostać zapisany w innej rozdzielczości niż PNG w `data/raw/`.
4. Filip niezależnie zgłasza: **labeler pokazuje złe bboxy**. To prawdopodobnie ten sam błąd widziany z drugiej strony — patrz 025.

**Jedna przyczyna, dwa objawy.** Jeśli GT ma współrzędne w innej skali niż obraz: labeler rysuje ramki obok symboli, a YOLO trenuje na szumie.

## Krok 1 — weryfikacja wizualna (minuty, nie godziny)

```powershell
python scripts/visualize_yolo_dataset.py --data data/labeled_tiled/data.yaml --limit 20
```

Patrzeć na kafelki: czy ramki leżą **na** symbolach.

- Ramki obok / poza kadrem / w rogu → **eksport zepsuty**, przejdź do kroku 2
- Ramki poprawne → hipoteza obalona, sprawdzać `data.yaml` (mapowanie klas, ścieżki train/val), a nie skalę

Dodatkowo: `python scripts/class_report.py --min-count 5` i porównać liczności klas z tym, co realnie wylądowało w `data/labeled_tiled/labels/`. Rozjazd liczb = filtr `--min-visible 0.35` odrzucił prawie wszystko (drugi możliwy sprawca: przy złej skali bboxy wypadają poza kafelek i `min-visible` je wycina — dałoby dokładnie taki obraz: prawie puste labelki, mAP≈0).

## Krok 2 — źródło rozjazdu

Porównać dla p028 (i p034 z it5):

| Wielkość | Skąd |
|---|---|
| Rozmiar obrazu w GT v2 | `gt/*.json` pole page width/height |
| Faktyczny rozmiar PNG | `data/raw/*.png` |
| bbox w GT v2 | `gt/*.json` |
| bbox po `load_all_training_records()` | wyjście funkcji |
| bbox znormalizowany w `labels/*.txt` | `data/labeled_tiled/` |

Rozjazd pokaże się na jednym z tych przejść. Nie zgadywać — wypisać wszystkie pięć.

Wynik → `sync/analysis/026-tiled-export-diag.md`.

## Krok 3 — fix + test regresji

Po naprawie: test w `backend/tests/` (lub `train/tests/`), który dla znanej strony sprawdza, że bbox z GT v2 po eksporcie ląduje w tym samym miejscu obrazu co przed. Bez tego testu ten błąd wróci przy następnej zmianie źródła GT.

## [RYZYKO] Trening szedł na CPU

Log eksportu: `torch-2.5.1+cu121 CPU (Intel Core i7-9700KF)`. Jeśli **trening** też szedł na CPU, to przy 150 epokach × 1536 px `batch 4` mogło zostać ukończone byle jak lub torch nie widzi RTX 2080. Sprawdzić:

```powershell
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

To nie tłumaczy mAP≈0 (na CPU model też by się nauczył, tylko wolniej), ale trzeba to zamknąć przed kolejnym cyklem — inaczej każda iteracja kosztuje wielokrotnie za dużo.

## Stan modelu produkcyjnego

`symbols_tiled_v1-3` **nie wchodzi** do `data/models/registry.json`. Aktywny pozostaje **`symbols_tiled_v1-2`, conf 0.18**. Nie podmieniać do czasu mAP porównywalnego z v1-2.
