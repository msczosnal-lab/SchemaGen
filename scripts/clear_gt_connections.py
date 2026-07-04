"""Wyczysc STARE connections z GT (SQLite) dla strony — zostawia bboxy/linie/terminale.

Connections w GT to zapisany wynik starego net-buildera (gwiazda) — nieaktualny po
fixach. Zgodnie z decyzja 'GT bez conn' (connections = wynik algorytmu, nie wzorzec).

Uzycie:
    python scripts/clear_gt_connections.py --page p040           # dry-run (tylko pokaz)
    python scripts/clear_gt_connections.py --page p040 --apply   # faktyczne czyszczenie
"""

from __future__ import annotations

import argparse

from backend.db import load_annotation, save_annotation


def _page_id(raw: str) -> str:
    if raw.startswith("22_"):
        return raw
    return f"22_A_153_PL_Adamed_AGV_SA2_20250706_{raw}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", required=True, help="page_id lub skrot (np. p040)")
    ap.add_argument("--apply", action="store_true", help="bez tego = dry-run")
    args = ap.parse_args()

    pid = _page_id(args.page)
    data = load_annotation(pid)
    if not data:
        print(f"[BLAD] brak adnotacji dla {pid}")
        return 1

    n_conn = len(data.get("connections") or [])
    print(
        f"{pid}: connections={n_conn} | "
        f"bboxes={len(data.get('bboxes') or [])} | lines={len(data.get('lines') or [])}"
    )
    if n_conn == 0:
        print("Brak connections do wyczyszczenia.")
        return 0
    if not args.apply:
        print("dry-run — dodaj --apply aby wyczyscic (bboxy/linie/terminale zostaja).")
        return 0

    data["connections"] = []
    if "potentials" in data:
        data["potentials"] = []
    save_annotation(pid, data)
    print(f"Wyczyszczono {n_conn} connections. Bboxy/linie/terminale nietkniete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
