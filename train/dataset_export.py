# COWORK_TASK: sync/prompts/005-train-symbols.md

"""Eksport datasetu YOLO z SQLite -> train/val + kopie PNG.

PC ZW: tylko kod + testy (mock/fixture). Pelny eksport (z prawdziwym
data/schemagen.db i data/raw/*.png) uruchamia Filip lokalnie.

Struktura wynikowa (data/labeled/):
    data.yaml
    export-manifest.json
    images/train/<page>.png   images/val/<page>.png
    labels/train/<page>.txt   labels/val/<page>.txt
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from backend.db import list_pages, load_annotation
from backend.models.label import LabelRecord
from backend.paths import LABELED, RAW
from labeler.export import find_raw_image, yolo_label_lines
from backend.class_map import build_class_map, load_palette_map
from backend.paths import SYMBOL_CLASSES


def load_labeled_records() -> list[LabelRecord]:
    """Rekordy z adnotacjami z SQLite (bbox>0, pomijajac strony `test_*`)."""
    records: list[LabelRecord] = []
    for page in list_pages():
        page_id = page["id"]
        if page_id.startswith("test_") or page_id.startswith("test"):
            continue
        data = load_annotation(page_id)
        if not data:
            continue
        record = LabelRecord.model_validate(data)
        if record.bboxes:
            records.append(record)
    return records


def split_train_val(
    records: list[LabelRecord], val_ratio: float = 0.2
) -> tuple[list[LabelRecord], list[LabelRecord]]:
    """Deterministyczny podzial (sort po page_id). **Ostatnie** strony ida do val.

    Przy <=1 rekordzie ta sama strona trafia do train i val (za malo danych).
    """
    ordered = sorted(records, key=lambda r: r.page_id)
    n = len(ordered)
    if n <= 1:
        return ordered, ordered
    n_val = max(1, round(n * val_ratio))
    n_val = min(n_val, n - 1)  # zostaw min. 1 w train
    n_train = n - n_val
    train = ordered[:n_train]
    val = ordered[n_train:]
    return train, val


def _write_split(
    records: list[LabelRecord],
    out: Path,
    split: str,
    class_map: dict[str, int],
    raw_dir: Path,
    palette_map: dict[str, str] | None = None,
) -> int:
    images_dir = out / "images" / split
    labels_dir = out / "labels" / split
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for record in records:
        src = find_raw_image(record, raw_dir)
        if src is None:
            continue  # bez obrazu nie ma sensu tworzyc labela
        shutil.copy2(src, images_dir / f"{record.page_id}{src.suffix}")
        lines = yolo_label_lines(record, class_map, palette_map)
        label_file = labels_dir / f"{record.page_id}.txt"
        label_file.write_text(
            "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
        )
        written += 1
    return written


def persist_class_map(class_map: dict[str, int]) -> None:
    """Zapisz wygenerowana liste klas do config/symbol-classes.yaml (zrodlo prawdy)."""
    names = [name for name, _ in sorted(class_map.items(), key=lambda kv: kv[1])]
    SYMBOL_CLASSES.write_text(
        "# AUTO-GENEROWANE przez train/dataset_export.py (z pola `tag` adnotacji).\n"
        "# Nie edytuj recznie — zostanie nadpisane przy kolejnym eksporcie.\n"
        + yaml.dump({"classes": names}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def export_dataset(
    output_dir: Path | None = None,
    val_ratio: float = 0.2,
    records: list[LabelRecord] | None = None,
    raw_dir: Path | None = None,
    min_count: int = 1,
) -> dict:
    """Zbuduj dataset YOLO multi-class train/val + data.yaml + export-manifest.json.

    Klasy sa wyprowadzane z pola `tag` WSZYSTKICH adnotacji (paleta jako kanon).
    `min_count` — klasy ponizej tego progu trafiaja do `inny` (domyslnie 1 = wszystkie).
    """
    out = output_dir or LABELED
    raw = raw_dir or RAW
    recs = records if records is not None else load_labeled_records()
    palette_map = load_palette_map()
    class_map, distribution = build_class_map(recs, min_count=min_count)
    if not class_map:
        class_map = {"element": 0}
    persist_class_map(class_map)

    train, val = split_train_val(recs, val_ratio)
    out.mkdir(parents=True, exist_ok=True)
    n_train = _write_split(train, out, "train", class_map, raw, palette_map)
    n_val = _write_split(val, out, "val", class_map, raw, palette_map)

    data_yaml = {
        "path": str(out.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {idx: name for name, idx in class_map.items()},
    }
    yaml_path = out / "data.yaml"
    yaml_path.write_text(yaml.dump(data_yaml, allow_unicode=True), encoding="utf-8")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classes": {name: idx for name, idx in class_map.items()},
        "val_ratio": val_ratio,
        "train_pages": [r.page_id for r in train],
        "val_pages": [r.page_id for r in val],
        "train_count": n_train,
        "val_count": n_val,
        "total_bboxes": sum(len(r.bboxes) for r in recs),
        "num_classes": len(class_map),
        "class_distribution": dict(distribution.most_common()),
    }
    manifest_path = out / "export-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "data_yaml": str(yaml_path),
        "manifest": str(manifest_path),
        "train": n_train,
        "val": n_val,
        "classes": len(class_map),
    }


if __name__ == "__main__":
    summary = export_dataset()
    print(
        f"Dataset: train={summary['train']} val={summary['val']} "
        f"klasy={summary['classes']} -> {summary['data_yaml']}"
    )
