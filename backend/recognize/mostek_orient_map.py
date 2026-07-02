# COWORK_TASK: sync/prompts/012-mostek-orientacja.md
"""Mapowanie 8 klas YOLO mostka -> (symbol bazowy, orientacja) + podzial potencjalow.

Detektor zwraca `class_name` = jedna z 8 orientacji (`mostek_r0`..`mostek_m270`)
albo generyczny `mostek` (gdy eksemplarze niedostepne / orientacja niepewna).

Ten modul NIE zmienia kontraktu SchemaModel ani sygnatur protocols/ — dostarcza
czyste funkcje pomocnicze dla net_builder/graph_builder.

Reguła podzialu potencjalow: mostek ma 3 terminale; orientacja mowi, KTORY z
nich jest terminalem WSPOLNYM (laczy pozostale dwa potencjaly). Odwzorowanie
orientacja -> krawedz terminala wspolnego jest DANE DOMENOWE (kanoniczny ksztalt
w r0) i pochodzi z config/mostek-orient.yaml (`common_terminal`). Bez wpisu w
configu funkcja zwraca None -> net_builder zachowuje dotychczasowe (geometryczne)
scalanie terminal<->terminal.
"""

from __future__ import annotations

MOSTEK_BASE = "mostek"
ORIENT_CLASSES = frozenset(
    f"mostek_{o}"
    for o in ("r0", "r90", "r180", "r270", "m0", "m90", "m180", "m270")
)


def is_mostek_class(class_name: str) -> bool:
    """True dla generycznego `mostek` i wszystkich 8 orientacji."""
    return class_name == MOSTEK_BASE or class_name in ORIENT_CLASSES


def base_symbol(class_name: str) -> str:
    """Symbol bazowy dla klasy mostka (do logiki niezaleznej od orientacji)."""
    return MOSTEK_BASE if is_mostek_class(class_name) else class_name


def orientation_of(class_name: str) -> str | None:
    """Sufiks orientacji (`r90`, `m0`, ...) albo None dla generycznego/nie-mostka."""
    if class_name in ORIENT_CLASSES:
        return class_name.split("_", 1)[1]
    return None


def common_terminal_side(class_name: str, mapping: dict | None = None) -> str | None:
    """Krawedz (top/right/bottom/left) terminala WSPOLNEGO dla danej orientacji.

    `mapping` = sekcja `common_terminal` z config/mostek-orient.yaml. Brak wpisu
    lub generyczny `mostek` -> None (net_builder scala geometrycznie jak dotad).
    """
    orient = orientation_of(class_name)
    if orient is None:
        return None
    m = mapping if mapping is not None else _load_common_terminal_map()
    return m.get(orient)


def _load_common_terminal_map() -> dict:
    import yaml

    from backend.paths import CONFIG

    path = CONFIG / "mostek-orient.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("common_terminal") or {}
