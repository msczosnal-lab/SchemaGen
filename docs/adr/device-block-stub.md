# ADR: device_block — zlozone urzadzenia z terminalami

**Status:** stub — etap 2+  
**Data:** 2026-06-15

## Kontekst

Na schemacie wystepuja:
- **Prosty symbol** — jeden bbox, 1–2 terminale (stycznik, bezpiecznik)
- **device_block** — szafa, modul IO, listwa z wieloma zaciskami; jeden obrys, wiele punktow podlaczenia

Etap 1: oznaczamy device_block **jednym bboxem + haslem blokowym** (`modul PLC`, `listwa zaciskowa`). Bez terminali.

## Decyzja (etap 1)

Nie implementujemy trybu terminali. YOLO nadal widzi jeden prostokat (`element`).

## Plan etap 2+

| Pole | Propozycja |
|------|------------|
| `kind` w bbox | `symbol` \| `device_block` |
| Terminale | `terminals[]` w LabelRecord — wspolrzedne w bboxie (0–1) |
| Relacje | GraphBuilder laczy `wire` z `component_id:terminal_id` |

Osobny prompt labelera: tryb „terminale w obrysie” po dzialajacym filarze polaczen.

## Wplyw na trening

Detekcja = obrys urzadzenia. Terminale = warstwa grafu, nie osobna klasa YOLO na start.
