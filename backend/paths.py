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
SYMBOL_PALETTE = CONFIG / "symbol-palette.yaml"
SYMBOL_REFERENCE = CONFIG / "symbol-reference.yaml"
VALIDATION_RULES = CONFIG / "validation-rules.json"
DRIVE_CONFIG = CONFIG / "901_Drive_Design.xml"
ATLAS = DATA / "atlas"
ATLAS_QET = ATLAS / "qet"
ATLAS_CROPS = ATLAS / "crops"


def ensure_data_dirs() -> None:
    for path in (RAW, LABELED, MODELS, LABELED / "labels", LABELED / "images"):
        path.mkdir(parents=True, exist_ok=True)
