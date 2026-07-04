"""Sciezki projektu — jedno zrodlo prawdy."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
LABELED = DATA / "labeled"
MODELS = DATA / "models"
DB_PATH = DATA / "schemagen.db"
REGISTRY_PATH = MODELS / "registry.json"
MANIFEST_PATH = DATA / "dataset-manifest.json"
CONFIG = ROOT / "config"
BLOCKS = ROOT / "blocks"
SCHEMA = ROOT / "schema"
SYMBOL_CLASSES = CONFIG / "symbol-classes.yaml"
TRAIN_CLASSES = CONFIG / "train-classes.yaml"
VAL_PAGES = CONFIG / "val-pages.yaml"
SYMBOL_PALETTE = CONFIG / "symbol-palette.yaml"
SYMBOL_REFERENCE = CONFIG / "symbol-reference.yaml"
VALIDATION_RULES = CONFIG / "validation-rules.json"
DRIVE_CONFIG = CONFIG / "901_Drive_Design.xml"
ATLAS = DATA / "atlas"
ATLAS_QET = ATLAS / "qet"
ATLAS_CROPS = ATLAS / "crops"

# Domyslny prefiks stron Adamed AGV SA2 (skrot p040 -> pelny page_id).
_DEFAULT_PAGE_PREFIX = "22_A_153_PL_Adamed_AGV_SA2_20250706"


def resolve_page_id(raw: str) -> str:
    """Skrot p040 lub pelny stem PNG -> page_id (bez rozszerzenia)."""
    s = raw.strip()
    if s.endswith((".png", ".jpg", ".jpeg")):
        return Path(s).stem
    if s.startswith("22_"):
        return s
    if s.startswith("p") and s[1:].isdigit():
        return f"{_DEFAULT_PAGE_PREFIX}_{s}"
    return s


def raw_image_path(page_arg: str) -> Path | None:
    """Znajdz plik obrazu strony w data/raw/."""
    pid = resolve_page_id(page_arg)
    for ext in (".png", ".jpg", ".jpeg"):
        p = RAW / f"{pid}{ext}"
        if p.exists():
            return p
    return None


def ensure_data_dirs() -> None:
    for path in (RAW, LABELED, MODELS, LABELED / "labels", LABELED / "images"):
        path.mkdir(parents=True, exist_ok=True)
