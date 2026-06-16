"""Testy eksportu datasetu YOLO (bez GPU/ultralytics, na fixturach)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from backend.models.label import BboxAnnotation, LabelRecord
from train.dataset_export import export_dataset, split_train_val
from train.train_symbols import train


def _record(page_id: str) -> LabelRecord:
    return LabelRecord(
        page_id=page_id,
        image_path=f"{page_id}.png",
        image_width=100,
        image_height=100,
        bboxes=[
            BboxAnnotation(id="a", class_name="element", x=10, y=10, width=20, height=20,
                           tag="silnik")
        ],
    )


def _make_raw(raw_dir: Path, page_ids: list[str]) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for pid in page_ids:
        (raw_dir / f"{pid}.png").write_bytes(b"\x89PNG\r\n")  # atrapa PNG


def test_split_train_val_deterministic() -> None:
    recs = [_record(f"p{i}") for i in range(5)]
    train_recs, val_recs = split_train_val(recs, val_ratio=0.2)
    assert len(val_recs) == 1
    assert len(train_recs) == 4
    # val to OSTATNIA strona po sortowaniu (p4)
    assert [r.page_id for r in val_recs] == ["p4"]
    # zadna strona nie jest jednoczesnie w train i val
    assert not ({r.page_id for r in train_recs} & {r.page_id for r in val_recs})


def test_split_single_record_shared() -> None:
    recs = [_record("only")]
    train_recs, val_recs = split_train_val(recs)
    assert train_recs == val_recs == recs


def test_export_dataset_structure(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    page_ids = ["p1", "p2", "p3"]
    _make_raw(raw, page_ids)
    records = [_record(p) for p in page_ids]
    out = tmp_path / "dataset"

    summary = export_dataset(output_dir=out, records=records, raw_dir=raw, val_ratio=0.34)

    assert summary["train"] + summary["val"] == 3
    assert (out / "data.yaml").exists()
    # obrazy i labels istnieja w odpowiednich splitach
    imgs = list((out / "images" / "train").glob("*.png")) + list(
        (out / "images" / "val").glob("*.png")
    )
    txts = list((out / "labels" / "train").glob("*.txt")) + list(
        (out / "labels" / "val").glob("*.txt")
    )
    assert len(imgs) == 3
    assert len(txts) == 3

    data = yaml.safe_load((out / "data.yaml").read_text(encoding="utf-8"))
    assert data["train"] == "images/train"
    assert data["val"] == "images/val"
    assert data["names"] == {0: "motor"}

    # export-manifest.json z lista stron train/val
    import json

    manifest = json.loads((out / "export-manifest.json").read_text(encoding="utf-8"))
    assert manifest["train_count"] + manifest["val_count"] == 3
    assert manifest["total_bboxes"] == 3
    assert set(manifest["train_pages"]) | set(manifest["val_pages"]) == set(page_ids)


def test_export_label_content(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _make_raw(raw, ["p1"])
    out = tmp_path / "dataset"
    export_dataset(output_dir=out, records=[_record("p1")], raw_dir=raw)

    label = (out / "labels" / "train" / "p1.txt").read_text(encoding="utf-8").strip()
    parts = label.split()
    assert len(parts) == 5
    assert parts[0] == "0"  # klasa element
    # cx = (10 + 20/2)/100 = 0.2 ; bw = 20/100 = 0.2
    assert parts[1].startswith("0.2")
    assert parts[3].startswith("0.2")


def test_export_skips_record_without_image(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _make_raw(raw, ["p1"])  # brak p2.png
    out = tmp_path / "dataset"
    records = [_record("p1"), _record("p2")]
    summary = export_dataset(output_dir=out, records=records, raw_dir=raw)
    assert summary["train"] + summary["val"] == 1


def test_train_missing_dataset_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        train(data_yaml=str(tmp_path / "nope.yaml"))
