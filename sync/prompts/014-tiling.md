# 014 — Tiling (okna natywnej rozdzielczosci)

**Cel:** strony ~6600px skalowane do 1536 robia z symbolu ~10px -> YOLO nie lapie.
Tniemy strone na nachodzace okna ~1536px BEZ skalowania. Symbol zostaje natywny.

## Trening
- `train/tiled_export.py` — dataset YOLO w oknach (windows/clip/nms). CLI:
  `python -m train.tiled_export --win 1536 --overlap 0.2 --min-visible 0.35`
  -> `data/labeled_tiled/` (tylko okna z >=1 bboxem).
- Trening: `python -m train.train_symbols --data data/labeled_tiled/data.yaml --name symbols_tiled_v1 --cache`

## Runtime (MUSI pasowac do treningu)
- `config/runtime.yaml`: `yolo_tiled: true`, `yolo_tile_win: 1536`, `yolo_tile_overlap: 0.2`.
- `backend/recognize/symbol_detector.py::detect_tiled` — tnie strone, wykrywa w oknach,
  przenosi bbox do wsp. strony, globalny NMS. graph_builder wola go gdy `yolo_tiled`.

## Uwagi
- win treningu == yolo_tile_win runtime (inaczej znow mismatch skali).
- Wiecej okien/epoke -> wolniej; `--cache` lagodzi. Okna bez symboli pomijane.
- `--cache` w train_symbols: cache obrazow, szybsze epoki bez straty jakosci.
