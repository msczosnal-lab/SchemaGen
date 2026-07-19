"""Symetrie symboli — dozwolone transformacje geometryczne dla augmentacji.

Prompt 028, Czesc B. Zrodlo: `config/symbol-symmetry.yaml`.

Zasada bezpieczenstwa (fail-safe): BRAK wpisu dla klasy = BRAK zgody na
jakakolwiek transformacje. Orientacja symbolu niesie znaczenie
(`strzalka_potencjalu_wejsciowa` vs `..._wyjsciowa` roznia sie wylacznie
kierunkiem — lustro zamienia jedna w druga i uczy siec bledu). Dlatego
domyslna odpowiedz na "czy wolno obrocic?" brzmi NIE, dopoki czlowiek
jawnie nie stwierdzi inaczej w pliku konfiguracyjnym.

Klucz = kanoniczna klasa (`type`, ta sama przestrzen nazw co
`config/symbol-classes.yaml` i `backend.class_map.bbox_class`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from backend.paths import CONFIG

SYMBOL_SYMMETRY = CONFIG / "symbol-symmetry.yaml"

#: Jedyne dozwolone katy obrotu. Dowolny kat wymagalby przeliczania bboxa do
#: obrysu prostokatnego (axis-aligned), co rozmywa etykiete — bbox rosnie,
#: a symbol w nim nie.
ALLOWED_ROTATIONS: tuple[int, ...] = (90, 180, 270)

#: Kanoniczne nazwy transformacji uzywane w UI i w generatorze augmentacji.
TRANSFORM_KEYS: tuple[str, ...] = ("mirror_h", "mirror_v", "rot90", "rot180", "rot270")


@dataclass(frozen=True)
class SymmetrySpec:
    """Dozwolone transformacje jednej klasy symbolu."""

    mirror_h: bool = False
    mirror_v: bool = False
    rotations: tuple[int, ...] = ()
    note: str = ""

    def allows(self, transform: str) -> bool:
        """Czy transformacja o tej nazwie (TRANSFORM_KEYS) jest dozwolona."""
        if transform == "mirror_h":
            return self.mirror_h
        if transform == "mirror_v":
            return self.mirror_v
        if transform.startswith("rot"):
            try:
                return int(transform[3:]) in self.rotations
            except ValueError:
                return False
        return False

    @property
    def any_allowed(self) -> bool:
        return self.mirror_h or self.mirror_v or bool(self.rotations)

    def transforms(self) -> list[str]:
        """Lista dozwolonych transformacji w kolejnosci TRANSFORM_KEYS."""
        return [t for t in TRANSFORM_KEYS if self.allows(t)]

    def as_dict(self) -> dict:
        return {
            "mirror_h": self.mirror_h,
            "mirror_v": self.mirror_v,
            "rotations": list(self.rotations),
            "note": self.note,
        }


#: Zwracany dla kazdej klasy bez wpisu — nic nie wolno.
NO_SYMMETRY = SymmetrySpec()


@dataclass
class SymmetryConfig:
    """Wczytany i zwalidowany plik symetrii."""

    specs: dict[str, SymmetrySpec] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def get(self, cls: str | None) -> SymmetrySpec:
        """Symetria klasy. Brak wpisu / brak klasy -> NO_SYMMETRY (fail-safe)."""
        if not cls:
            return NO_SYMMETRY
        return self.specs.get(cls, NO_SYMMETRY)

    def allows(self, cls: str | None, transform: str) -> bool:
        return self.get(cls).allows(transform)

    def __contains__(self, cls: object) -> bool:
        return cls in self.specs


def parse_symmetry(
    data: dict | None,
    known_classes: set[str] | frozenset[str] | None = None,
) -> SymmetryConfig:
    """Zwaliduj surowy YAML -> SymmetryConfig.

    Bledy schematu NIE podnosza wyjatku — psujacy sie plik konfiguracyjny nie
    moze wywrocic przegladarki ani eksportu. Kazdy problem lezy w
    `cfg.warnings`, a wpis nie do odczytania jest pomijany (czyli klasa
    dostaje NO_SYMMETRY — bezpieczny domyslny).

    `known_classes` (opcjonalne): jesli podane, klasa spoza tego zbioru daje
    ostrzezenie, ale wpis zostaje wczytany (klasa moze pojawic sie pozniej).
    """
    cfg = SymmetryConfig()
    if not data:
        return cfg
    if not isinstance(data, dict):
        cfg.warnings.append("plik symetrii: korzen nie jest mapa — zignorowany")
        return cfg

    raw = data.get("symmetry")
    if raw is None:
        cfg.warnings.append("plik symetrii: brak klucza 'symmetry'")
        return cfg
    if not isinstance(raw, dict):
        cfg.warnings.append("plik symetrii: 'symmetry' nie jest mapa — zignorowane")
        return cfg

    for cls, entry in raw.items():
        name = str(cls)
        if entry is None:
            # jawnie pusty wpis = jawny brak zgody; nie jest bledem
            cfg.specs[name] = NO_SYMMETRY
            continue
        if not isinstance(entry, dict):
            cfg.warnings.append(f"{name}: wpis nie jest mapa — pominiety")
            continue

        unknown = set(entry) - {"mirror_h", "mirror_v", "rotations", "note"}
        if unknown:
            cfg.warnings.append(f"{name}: nieznane klucze {sorted(unknown)} — zignorowane")

        mh = _as_bool(entry.get("mirror_h"), name, "mirror_h", cfg)
        mv = _as_bool(entry.get("mirror_v"), name, "mirror_v", cfg)
        rots = _as_rotations(entry.get("rotations"), name, cfg)
        note = str(entry.get("note") or "")

        if known_classes is not None and name not in known_classes:
            cfg.warnings.append(f"{name}: klasa nieznana w danych GT — wpis zachowany")

        cfg.specs[name] = SymmetrySpec(mirror_h=mh, mirror_v=mv, rotations=rots, note=note)

    return cfg


def _as_bool(value, cls: str, key: str, cfg: SymmetryConfig) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    cfg.warnings.append(f"{cls}.{key}: oczekiwano true/false, jest {value!r} — przyjeto false")
    return False


def _as_rotations(value, cls: str, cfg: SymmetryConfig) -> tuple[int, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        cfg.warnings.append(f"{cls}.rotations: oczekiwano listy, jest {value!r} — przyjeto []")
        return ()
    out: list[int] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            cfg.warnings.append(f"{cls}.rotations: {item!r} nie jest liczba calkowita — pominiete")
            continue
        if item in ALLOWED_ROTATIONS:
            if item not in out:
                out.append(item)
        elif item in (0, 360):
            cfg.warnings.append(f"{cls}.rotations: {item} to identycznosc — pominiete")
        else:
            cfg.warnings.append(
                f"{cls}.rotations: {item} nie jest wielokrotnoscia 90 z {list(ALLOWED_ROTATIONS)}"
                " — pominiete"
            )
    return tuple(sorted(out))


def load_symmetry_file(
    path: Path | None = None,
    known_classes: set[str] | frozenset[str] | None = None,
) -> SymmetryConfig:
    """Wczytaj plik symetrii (bez cache). Brak pliku = pusta konfiguracja."""
    src = path or SYMBOL_SYMMETRY
    if not src.exists():
        cfg = SymmetryConfig()
        cfg.warnings.append(f"brak pliku {src.name} — zadna klasa nie ma zgody na transformacje")
        return cfg
    try:
        data = yaml.safe_load(src.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # nieparsowalny YAML nie moze wywrocic narzedzia
        cfg = SymmetryConfig()
        cfg.warnings.append(f"{src.name}: blad skladni YAML ({exc}) — plik zignorowany")
        return cfg
    return parse_symmetry(data, known_classes)


@lru_cache(maxsize=1)
def load_symmetry() -> SymmetryConfig:
    """Konfiguracja symetrii z domyslnej sciezki (cache'owana)."""
    return load_symmetry_file()


def dump_symmetry(cfg: SymmetryConfig) -> str:
    """SymmetryConfig -> tekst YAML (stabilna kolejnosc, komentarz naglowkowy)."""
    header = (
        "# Dozwolone transformacje geometryczne dla augmentacji treningowej.\n"
        "# Klucz = kanoniczna klasa symbolu (`type`, ta sama przestrzen nazw co\n"
        "# config/symbol-classes.yaml).\n"
        "#\n"
        "# Brak wpisu = BRAK zgody na jakakolwiek transformacje (bezpieczny domyslny —\n"
        "# orientacja symbolu jest znaczaca). rotations: tylko 90/180/270.\n"
        "#\n"
        "# Generowane przez scripts/apply_symmetry.py z symmetry.json\n"
        "# (scripts/element_review.py). Mozna edytowac recznie.\n"
    )
    body = {
        "symmetry": {
            cls: cfg.specs[cls].as_dict() for cls in sorted(cfg.specs)
        }
    }
    return header + yaml.safe_dump(body, allow_unicode=True, sort_keys=False, default_flow_style=False)
