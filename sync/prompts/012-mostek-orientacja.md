# 012 — Orientacja mostka (8 klas D4)

**Cel:** mostek (3 terminale) wykrywany z orientacją. Sieć zwraca orientację
(8 klas), lustro chiralne (pełne 8), dane przez syntetyczne kafelki.

## Kontrakt
- 8 klas: `mostek_r0/r90/r180/r270` + `mostek_m0/m90/m180/m270` (grupa D4).
- Labeler: tag generyczny `mostek` (bez zmian w pickerze). Orientacja rozpoznawana
  automatycznie przy eksporcie przez dopasowanie do 8 eksemplarzy.
- `train_symbols.py`: globalna augmentacja (fliplr/flipud/degrees) ZOSTAJE 0.

## Kod
- `train/mostek_orient.py` — D4, Cayley, classify_crop (NCC), augment_d4, count_edge_crossings.
- `train/mostek_tiles.py` — expand_mostek_orientations, generate_tiles, write_tiles.
- `train/dataset_export.py` — maybe_expand_mostek / maybe_write_mostek_tiles.
- `backend/recognize/mostek_orient_map.py` — 8 klas → (mostek, orientacja).
- `config/mostek-orient.yaml` — parametry + `common_terminal` (do uzupełnienia).

## Uruchomienie (Filip, GPU)
1. `data/mostek_exemplars/` = 8 cropów (nazwa = klasa).
2. `python -m train.dataset_export --min-count 5` → manifest: `mostek_orient`, `mostek_tiles`.
3. train + export_onnx + preview p040.
4. Uzupełnij `common_terminal:` w config → podział potencjałów wg orientacji.

## Status
Kod + testy DONE (188 passed). Czeka: eksemplarze + re-train GPU + common_terminal.
