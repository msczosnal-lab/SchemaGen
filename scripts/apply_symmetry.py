"""symmetry.json (z element_review.py) -> config/symbol-symmetry.yaml.

Prompt 028, Czesc B. Konwencja jak apply_reassign.py: DRY-RUN domyslnie,
zapis dopiero po --apply, zapis atomowy (tmp + os.replace).

symmetry.json:
    {"<klasa>": {"mirror_h":bool,"mirror_v":bool,"rotations":[90,180,270],"note":str}}

Uzycie:
    python scripts/apply_symmetry.py                  # dry-run: pokaz diff
    python scripts/apply_symmetry.py --apply
    python scripts/apply_symmetry.py --file data/symmetry.json --apply

Bezpieczenstwo: klasa nieobecna w symmetry.json NIE jest kasowana z YAML-a
(scalanie, nie nadpisanie) — chyba ze --replace. Dzieki temu przeglad jednej
klasy przez filtr `--class` nie kasuje wiedzy o pozostalych.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Uruchomienie: python scripts/apply_symmetry.py (bez wymogu pip install -e .)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from scripts._pick_input import pick_input
except ModuleNotFoundError:  # uruchomienie z katalogu scripts/
    from _pick_input import pick_input

from backend.class_map import class_distribution, load_palette_map
from backend.paths import ROOT
from backend.symmetry import (
    ALLOWED_ROTATIONS,
    SymmetryConfig,
    SymmetrySpec,
    dump_symmetry,
    load_symmetry_file,
)

DEFAULT_OUT = ROOT / "config" / "symbol-symmetry.yaml"


def _find_input(explicit: Path | None) -> Path | None:
    """Najnowszy symmetry.json — patrz scripts/_pick_input.py (BŁĄD 2026-07-19)."""
    candidates = [explicit] if explicit else [
        ROOT / "data" / "symmetry.json",
        ROOT / "data" / "output" / "symmetry.json",
        ROOT / "Downloads" / "symmetry.json",
        Path.home() / "Downloads" / "symmetry.json",
        Path.cwd() / "symmetry.json",
    ]
    return pick_input(candidates, "symmetry.json")


def parse_incoming(data: dict, known: set[str]) -> tuple[dict[str, SymmetrySpec], list[str]]:
    """symmetry.json -> {klasa: SymmetrySpec}, + lista ostrzezen."""
    specs: dict[str, SymmetrySpec] = {}
    warn: list[str] = []
    if not isinstance(data, dict):
        return specs, ["symmetry.json: korzen nie jest obiektem — nic nie wczytano"]
    for cls, entry in data.items():
        name = str(cls)
        if not isinstance(entry, dict):
            warn.append(f"{name}: wpis nie jest obiektem — pominiety")
            continue
        rots: list[int] = []
        for r in entry.get("rotations") or []:
            if isinstance(r, bool) or not isinstance(r, int):
                warn.append(f"{name}: rotacja {r!r} nie jest liczba — pominieta")
            elif r not in ALLOWED_ROTATIONS:
                warn.append(f"{name}: rotacja {r} spoza {list(ALLOWED_ROTATIONS)} — pominieta")
            elif r not in rots:
                rots.append(r)
        if known and name not in known:
            warn.append(f"{name}: klasa nieznana w danych GT — wpis zachowany")
        specs[name] = SymmetrySpec(
            mirror_h=bool(entry.get("mirror_h")),
            mirror_v=bool(entry.get("mirror_v")),
            rotations=tuple(sorted(rots)),
            note=str(entry.get("note") or ""),
        )
    return specs, warn


def merge(
    current: SymmetryConfig,
    incoming: dict[str, SymmetrySpec],
    replace: bool = False,
) -> tuple[SymmetryConfig, list[tuple[str, str, str]]]:
    """Scal wpisy. Zwraca (nowa konfiguracja, [(klasa, przed, po)] dla zmian)."""
    out = SymmetryConfig(specs={} if replace else dict(current.specs))
    changes: list[tuple[str, str, str]] = []
    for cls, spec in incoming.items():
        old = current.get(cls)
        # note z YAML nie ginie, gdy UI go nie odeslalo
        if not spec.note and old.note:
            spec = SymmetrySpec(spec.mirror_h, spec.mirror_v, spec.rotations, old.note)
        if (old.mirror_h, old.mirror_v, old.rotations) != (
            spec.mirror_h,
            spec.mirror_v,
            spec.rotations,
        ):
            changes.append((cls, _fmt(old), _fmt(spec)))
        out.specs[cls] = spec
    if replace:
        for cls in current.specs:
            if cls not in incoming:
                changes.append((cls, _fmt(current.specs[cls]), "(usuniete)"))
    return out, changes


def find_denied_conflicts(
    current: SymmetryConfig,
    incoming: dict[str, SymmetrySpec],
) -> list[str]:
    """Klasy, ktorym symmetry.json nadaje zgode wbrew JAWNEMU zakazowi w repo.

    Zakaz "jawny" = wpis istnieje, nie ma zadnej zgody i ma `note` (uzasadnienie).
    Brak wpisu to tez brak zgody, ale domyslny — nadanie zgody klasie bez wpisu
    jest normalna praca przegladu i nie jest konfliktem.

    Powod istnienia tego bezpiecznika: jedno przypadkowe klikniecie na
    `strzalka_potencjalu_wejsciowa` cicho zatruwa dataset — lustro zamienia ja
    w klase przeciwna. Konfiguracja fail-safe musi bronic sie takze przed UI.
    """
    return [
        cls
        for cls, spec in incoming.items()
        if spec.any_allowed
        and cls in current
        and not current.get(cls).any_allowed
        and current.get(cls).note
    ]


def _fmt(s: SymmetrySpec) -> str:
    parts = []
    if s.mirror_h:
        parts.append("mirror_h")
    if s.mirror_v:
        parts.append("mirror_v")
    parts += [f"rot{r}" for r in s.rotations]
    return ",".join(parts) if parts else "(brak zgody)"


def write_atomic(path: Path, text: str) -> None:
    """Zapis atomowy — tmp w tym samym katalogu + os.replace (niezmiennik CLAUDE.md)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--apply", action="store_true", help="zapisz (domyslnie dry-run)")
    ap.add_argument(
        "--replace",
        action="store_true",
        help="zastap caly plik (domyslnie: scal — klasy spoza symmetry.json zostaja)",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="nadpisz JAWNE zakazy z uzasadnieniem (`note`) w symbol-symmetry.yaml",
    )
    args = ap.parse_args()

    path = _find_input(args.file)
    if path is None:
        return 1
    print(f"Plik symetrii: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[BŁĄD] {path.name}: niepoprawny JSON ({exc})")
        return 1

    try:
        known = set(class_distribution(_records(), load_palette_map()))
    except Exception as exc:  # noqa: BLE001 — brak GT nie moze blokowac zapisu configu
        print(f"[UWAGA] nie udalo sie wczytac klas z GT ({exc}) — walidacja nazw pominieta")
        known = set()

    incoming, warn = parse_incoming(data, known)
    for w in warn:
        print(f"[UWAGA] {w}")
    if not incoming:
        print("Brak wpisow do zastosowania.")
        return 1

    current = load_symmetry_file(args.out, known_classes=known or None)
    for w in current.warnings:
        print(f"[UWAGA] {args.out.name}: {w}")

    conflicts = find_denied_conflicts(current, incoming)
    if conflicts:
        print(f"\n[BŁĄD] {len(conflicts)} klas ma w repo UDOKUMENTOWANY ZAKAZ, "
              "a symmetry.json nadaje im zgode:")
        for cls in conflicts:
            print(f"  {cls}")
            print(f"      repo:  BRAK ZGODY — {current.get(cls).note}")
            print(f"      nowy:  {_fmt(incoming[cls])}")
        if not args.force:
            print("\nZapis WSTRZYMANY. Albo popraw symmetry.json, albo — jesli zakaz "
                  "jest bledny — usun/zmien `note` w YAML, albo uzyj --force.")
            return 1
        print("\n[UWAGA] --force: zakazy zostaja nadpisane mimo uzasadnien w repo.")

    merged, changes = merge(current, incoming, replace=args.replace)

    allowed = sorted(c for c, s in merged.specs.items() if s.any_allowed)
    print(f"\nWpisow w wyniku: {len(merged.specs)} | z jakakolwiek zgoda: {len(allowed)}")
    if changes:
        print(f"\nZmiany ({len(changes)}):")
        for cls, before, after in changes:
            print(f"  {cls:<34} {before}  ->  {after}")
    else:
        print("\nBrak zmian wzgledem obecnego pliku.")

    if allowed:
        print("\nKlasy z dozwolona augmentacja:")
        for c in allowed:
            print(f"  {c:<34} {_fmt(merged.specs[c])}")
    no_consent = len(merged.specs) - len(allowed)
    if no_consent:
        print(f"\n{no_consent} klas jawnie bez zgody (+ kazda klasa bez wpisu — fail-safe).")

    if not args.apply:
        print(f"\nDRY-RUN — nic nie zapisano. Dodaj --apply, aby zapisac do {args.out}.")
        return 0

    write_atomic(args.out, dump_symmetry(merged))
    print(f"\nZAPISANO -> {args.out}")
    return 0


def _records():
    from train.dataset_export import load_all_training_records

    return load_all_training_records()


if __name__ == "__main__":
    raise SystemExit(main())
