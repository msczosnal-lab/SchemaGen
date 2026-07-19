"""Wybor pliku wejsciowego dla apply_* — po DACIE, nie po kolejnosci na liscie.

Powod ([BŁĄD] 2026-07-19): `apply_reassign.py` mial staly ranking sciezek, w ktorym
`data/output/reassignments.json` stalo PRZED `~/Downloads`. Plik sprzed miesiaca
przeslonil swiezy eksport z przegladarki i skrypt zastosowal go bez slowa —
uzytkownik zobaczyl "ZAPISANO: 25 retag" i mial prawo sadzic, ze to jego 242 zmiany.

Zasady:
  - sprawdzamy WSZYSTKIE kandydackie sciezki, nie pierwsza lepsza,
  - wybieramy NAJNOWSZY plik wg mtime,
  - wypisujemy wszystkie znalezione z data i liczba wpisow, zaznaczajac wybrany,
  - ostrzegamy, gdy wybrany plik jest starszy niz `stale_days`.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

STALE_DAYS = 2


def _entry_count(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — podglad ma nie wywracac wyboru pliku
        return "?"
    if isinstance(data, list):
        return str(len(data))
    if isinstance(data, dict):
        # reviewed.json ma ksztalt {"reviewed": [...], "all_classes": [...]} —
        # liczba kluczy (2) nie mowi nic o zawartosci
        if isinstance(data.get("reviewed"), list):
            return str(len(data["reviewed"]))
        return str(len(data))
    return "?"


def pick_input(
    candidates: list[Path | None],
    label: str,
    stale_days: int = STALE_DAYS,
) -> Path | None:
    """Najnowszy istniejacy plik z listy kandydatow. None = nie znaleziono."""
    found = [c for c in candidates if c and c.exists()]
    if not found:
        print(f"[BŁĄD] Nie znaleziono {label}. Sprawdzone:")
        for c in candidates:
            if c:
                print(f"  - {c}")
        print("Wskaz: --file <sciezka>")
        return None

    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    chosen = found[0]

    if len(found) > 1:
        print(f"[UWAGA] Znaleziono {len(found)} plikow {label} — wybieram NAJNOWSZY:")
    for path in found:
        stamp = datetime.fromtimestamp(path.stat().st_mtime)
        mark = "->" if path == chosen else "  "
        print(f"  {mark} {stamp:%Y-%m-%d %H:%M}  {_entry_count(path):>5} wpisow  {path}")

    age_days = (datetime.now() - datetime.fromtimestamp(chosen.stat().st_mtime)).days
    if age_days >= stale_days:
        print(f"\n[RYZYKO] Wybrany plik ma {age_days} dni. Jesli wlasnie wyeksportowales "
              "nowy z przegladarki, to NIE JEST on — sprawdz sciezke pobierania "
              "albo wskaz --file.")
    return chosen
