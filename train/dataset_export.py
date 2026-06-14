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
from labeler.export import find_raw_image, load_class_map, yolo_label_lines


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
        lines = yolo_label_lines(record, class_map)
        label_file = labels_dir / f"{record.page_id}.txt"
        label_file.write_text(
            "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
        )
        written += 1
    return written


def export_dataset(
    output_dir: Path | None = None,
    val_ratio: float = 0.2,
    records: list[LabelRecord] | None = None,
    raw_dir: Path | None = None,
) -> dict:
    """Zbuduj dataset YOLO train/val i data.yaml. Zwraca podsumowanie + sciezke yaml."""
    out = output_dir or DATASET_DIR
    raw = raw_dir or RAW
    recs = records if records is not None else load_labeled_records()
    class_map = load_class_map() or {"element": 0}

    train, val = split_train_val(recs, val_ratio)
    n_train = _write_split(train, out, "train", class_map, raw)
    n_val = _write_split(val, out, "val", class_map, raw)

    data_yaml = {
        "path": str(out.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {idx: name for name, idx in class_map.items()},
    }
    yaml_path = out / "data.yaml"
    out.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(yaml.dump(data_yaml, allow_unicode=True), encoding="utf-8")

    return {
        "data_yaml": str(yaml_path),
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
