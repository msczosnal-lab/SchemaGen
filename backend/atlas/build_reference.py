"""CLI: skanuje biblioteke QET → config/symbol-reference.yaml + crops PNG.

Uzycie:
    python -m backend.atlas.build_reference \\
        --qet-dir data/atlas/qet \\
        --out config/symbol-reference.yaml \\
        --crops-dir data/atlas/crops

Wymagane wczesniej:
    git clone --depth 1 https://github.com/qelectrotech/qelectrotech-elements.git data/atlas/qet
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from backend.atlas.qet_parser import QetElement, parse_elmt
from backend.atlas.qet_render import save_crop
from backend.paths import CONFIG, DATA

# Podkatalogi allpole pod WRT01 (kolejnosc = priorytet)
_P0_SUBDIRS = [
    "200_fuses_protective_gears",
    "310_relays_contactors_contacts",
    "130_terminals_terminal_strips",
    "391_consumers_actuators",
    "380_signaling_operating",
    "390_sensors_instruments",
    "330_transformers_power_supplies",
    "340_converters_inverters",
    "392_generators_sources",
    "395_electronics_semiconductors",
    "140_connectors_plugs",
    "450_high_voltage",
]

# Pomijamy: odnośniki między folio, kable, połączenia pomocnicze, dom
_SKIP_ALLPOLE_SUBDIRS = {
    "100_folio_referencing",
    "110_network_supplies",
    "114_connections",
    "120_cables_wiring",
    "500_home_installation",
}

_P1_DIRS = ["10_electric/91_en_60617"]
_P2_MANUFACTURERS = ["Siemens", "WAGO", "ABB", "Schneider"]

# Mapowanie slow kluczowych → prefiks tagu IEC 81346-1
_TAG_MAP: list[tuple[str, str]] = [
    (r"fuse|bezpiecznik|fusible|sicherung", "F"),
    (r"circuit.?breaker|wyłącznik|disjoncteur|leitungsschutz", "QF"),
    (r"contactor|stycznik|contacteur|sch[uü]tz", "KM"),
    (r"relay|przekaźnik|relais|relé", "KA"),
    (r"motor|silnik|moteur", "M"),
    (r"disconnector|rozłącznik|sectionneur|trennschalter", "QS"),
    (r"terminal|listwa|borne|klemme|zacisk", "X"),
    (r"push.?button|przycisk|bouton|taster", "SB"),
    (r"emergency|awaryj|urgence|not.?aus", "SF"),
    (r"lamp|light|lampka|voyant|signalleuchte", "HG"),
    (r"transformer|transformator|transformateur", "T"),
    (r"inverter|falownik|onduleur|frequenz|variateur|drive", "UF"),
    (r"soft.?start|łagod|d[eé]marreur|sanftanlauf", "US"),
    (r"sensor|czujnik|capteur|geber", "SQ"),
    (r"switch|selector|przełącznik|commutateur|schalter", "SA"),
    (r"capacitor|kondensator|condensateur", "C"),
    (r"resistor|rezystor|r[eé]sistance|widerstand", "R"),
    (r"diode|dioda", "V"),
]


def _tag_prefix(name_en: str, name_pl: str) -> Optional[str]:
    text = f"{name_en} {name_pl}".lower()
    for pattern, prefix in _TAG_MAP:
        if re.search(pattern, text):
            return prefix
    return None


def _slug_from_name(name_en: str, fallback: str) -> str:
    s = name_en.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "_", s).strip("_")
    return s or re.sub(r"[^\w]", "_", fallback.lower())


def _collect_p0_files(qet_dir: Path) -> list[Path]:
    """Urzadzenia z 10_allpole — tylko podkatalogi P0, bez folio/kabli."""
    base = qet_dir / "10_electric" / "10_allpole"
    if not base.exists():
        return []
    files: list[Path] = []
    for sub in _P0_SUBDIRS:
        d = base / sub
        if d.exists():
            files.extend(sorted(d.rglob("*.elmt")))
    return files


def _is_usable_element(el: QetElement) -> bool:
    """Pomija symbole bez rysowalnej geometrii (same terminale / puste)."""
    if el.geometry.drawable_count() == 0:
        return False
    bb = el.geometry.bounding_box()
    if bb is None:
        return False
    x_min, y_min, x_max, y_max = bb
    return (x_max - x_min) >= 2 and (y_max - y_min) >= 2


def _collect_files(qet_dir: Path, rel_dirs: list[str]) -> list[Path]:
    files: list[Path] = []
    for d in rel_dirs:
        base = qet_dir / d
        if base.exists():
            files.extend(sorted(base.rglob("*.elmt")))
    return files


def _collect_manufacturer_files(qet_dir: Path, names: list[str]) -> list[Path]:
    files: list[Path] = []
    base = qet_dir / "10_electric" / "20_manufacturers_articles"
    if not base.exists():
        return files
    for mfr in names:
        prefix = mfr.lower().split()[0]
        for sub in sorted(base.iterdir()):
            if sub.is_dir() and sub.name.lower().startswith(prefix):
                files.extend(sorted(sub.rglob("*.elmt")))
                break
    return files


def build(
    qet_dir: Path,
    out_yaml: Path,
    crops_dir: Path,
    max_symbols: int = 120,
    include_manufacturers: bool = True,
    dry_run: bool = False,
) -> list[dict]:
    """Buduje atlas i zapisuje YAML + PNG. Zwraca liste wpisow."""
    all_batches: list[tuple[list[Path], int]] = [
        (_collect_p0_files(qet_dir), 0),
        (_collect_files(qet_dir, _P1_DIRS), 1),
    ]
    if include_manufacturers:
        all_batches.append((_collect_manufacturer_files(qet_dir, _P2_MANUFACTURERS), 2))

    slug_to_refs: dict[str, list[str]] = {}
    slug_to_element: dict[str, QetElement] = {}

    for batch_files, _priority in all_batches:
        for p in batch_files:
            if len(slug_to_refs) >= max_symbols:
                break
            try:
                el = parse_elmt(p)
            except Exception:
                continue
            if not el.name_en() or not _is_usable_element(el):
                continue
            slug = _slug_from_name(el.name_en(), p.stem)
            ref = f"qet:{p.relative_to(qet_dir).as_posix()}"
            if slug in slug_to_refs:
                # Dedup: ten sam ksztalt semantyczny — dodaj tylko ref
                slug_to_refs[slug].append(ref)
            else:
                slug_to_refs[slug] = [ref]
                slug_to_element[slug] = el

    symbols: list[dict] = []
    for slug, refs in slug_to_refs.items():
        el = slug_to_element[slug]
        crop_rel = f"data/atlas/crops/{slug}.png"

        if not dry_run:
            try:
                save_crop(el, crops_dir / f"{slug}.png")
            except Exception as exc:
                print(f"[WARN] render failed for {slug}: {exc}", file=sys.stderr)

        entry: dict = {
            "id": slug,
            "yolo_class": "element",
            "iec_ref": None,
            "default_description": el.name_en(),
            "atlas_crop": crop_rel,
            "source_refs": refs,
        }
        if el.name_pl():
            entry["aliases_pl"] = [el.name_pl()]
        tag = _tag_prefix(el.name_en(), el.name_pl())
        if tag:
            entry["tag_prefix"] = tag

        symbols.append(entry)

    if not dry_run:
        _write_yaml(out_yaml, symbols)

    return symbols


def _write_yaml(out_yaml: Path, symbols: list[dict]) -> None:
    meta = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {
                "id": "qet",
                "type": "gpl_lib",
                "ref": "data/atlas/qet",
                "license": "GNU/GPL — atrybucja w README/docs",
            }
        ],
        "tag_standard": "IEC 81346-1",
    }
    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    out_yaml.write_text(
        yaml.dump(
            {"meta": meta, "symbols": symbols},
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Buduje symbol-reference.yaml z lokalnej biblioteki QET."
    )
    parser.add_argument(
        "--qet-dir",
        default=str(DATA / "atlas" / "qet"),
        help="Sciezka do sklonowanego repo qelectrotech-elements",
    )
    parser.add_argument(
        "--out",
        default=str(CONFIG / "symbol-reference.yaml"),
        help="Sciezka wyjsciowa YAML",
    )
    parser.add_argument(
        "--crops-dir",
        default=str(DATA / "atlas" / "crops"),
        help="Katalog na crop-y PNG",
    )
    parser.add_argument("--max-symbols", type=int, default=120)
    parser.add_argument(
        "--no-manufacturers",
        action="store_true",
        help="Pominij katalog producentow (P2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Wypisz liczbe symboli bez zapisu plikow",
    )
    args = parser.parse_args(argv)

    qet_dir = Path(args.qet_dir)
    if not qet_dir.exists():
        print(f"[ERROR] Brak katalogu QET: {qet_dir}", file=sys.stderr)
        print(
            "Sklonuj: git clone --depth 1 "
            "https://github.com/qelectrotech/qelectrotech-elements.git data/atlas/qet",
            file=sys.stderr,
        )
        sys.exit(1)

    symbols = build(
        qet_dir=qet_dir,
        out_yaml=Path(args.out),
        crops_dir=Path(args.crops_dir),
        max_symbols=args.max_symbols,
        include_manufacturers=not args.no_manufacturers,
        dry_run=args.dry_run,
    )

    mode = "[DRY-RUN] " if args.dry_run else ""
    print(f"{mode}Zbudowano {len(symbols)} symboli → {args.out}")


if __name__ == "__main__":
    main()
