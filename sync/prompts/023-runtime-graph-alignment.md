# Zadanie 023: Runtime graph alignment — emisja connections OD–DO

**Status:** AKTYWNE (Cursor)
**Zależność:** 022-labeler-graph-v2 ✅ (remap ID w diff); loop 032 STOP (plateau)
**Baseline:** [`sync/analysis/023-p028-conn-baseline.md`](../analysis/023-p028-conn-baseline.md)

## Kontekst

GT v2 opisuje graf jawny: linie OD terminalu DO terminalu. Runtime (`net_builder`) scala segmenty w nety union-find, ale dla netów ≥3 węzłów emitował **gwiazdę** do kotwicy `node_ids[0]`. Diff po remapie IoU (022) nadal daje ~4/42 na p028 — głównie **topologia**, nie ID.

## Cel

GraphBuilder / net_builder emituje krawędzie zgodne z GT:
- **Rail** (`zlaczka`, `mostek`, …): łańcuch sąsiadów `link` (sort koliniarny)
- **Power**: pary z końców segmentów `GraphicLine` w necie
- **Fallback**: gwiazda `net_k` tylko gdy chain/segmenty nie pokryją węzłów

## Pliki

| Plik | Zmiana |
|------|--------|
| `backend/recognize/connection_path.py` | wspólne: sort koliniarny, rail detect, segment pairs |
| `backend/recognize/net_builder.py` | `_emit_multi_node` zamiast samej gwiazdy |
| `labeler/rail_extractor.py` | import z `connection_path` (bez duplikacji) |
| `backend/tests/test_net_builder.py` | testy łańcucha rail |

## Poza zakresem

- Zmiana wag eval / `_norm_conn` undirected
- ContextResolver listwy (`zlacze`, `listwa_zlaczek`)
- Re-arm loop 032

## Walidacja

```powershell
pytest backend/tests/test_net_builder.py -q
python scripts/diff_gt_runtime.py --page p028
python scripts/eval_val_pages.py
```

Kryterium: p028 Conn match >> 4/42; średnia 6 stron GT bez regresji SCORE >−1.0; val-pages mean ≥ 30.77.

## Retrain YOLO (równolegle, Filip GPU)

Po `tiled_export` z GT v2 — patrz `TRENING-SIEC.md`, wersja docelowa `symbols_tiled_v1-3`.
