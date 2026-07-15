# COWORK_TASK: sync/prompts/014-tiling.md
"""Tiling: eksport datasetu YOLO w OKNACH natywnej rozdzielczosci.

Problem: strony ~6600px skalowane do imgsz=1536 robia z symbolu ~10px -> YOLO nie
lapie. Rozwiazanie: tniemy strone na nachodzace okna ~win px (bez skalowania),
uczymy i inferujemy na oknach. Symbol zostaje w natywnym rozmiarze.

Geometria (windows/clip/nms) jest wspoldzielona z runtime (slicing inferencji).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from backend.class_map import build_class_map, load_palette_map, resolve_class_id
from backend.models.label import LabelRecord
from backend.paths import DATA, RAW
from labeler.export import find_raw_image
from train.dataset_export import (
    load_all_training_records,
    load_val_page_ids,
    persist_class_map,
)

TILED = DATA / "labeled_tiled"


def windows(W: int, H: int, win: int, overlap: float = 0.2) -> list[tuple[int, int, int, int]]:
    """Nachodzace okna (x0,y0,x1,y1) pokrywajace obraz WxH. Ostatnie dosuniete do brzegu."""
    if win <= 0:
        return [(0, 0, W, H)]
    step = max(1, int(round(win * (1.0 - overlap))))

    def starts(total: int) -> list[int]:
        if total <= win:
            return [0]
        xs = list(range(0, total - win + 1, step))
        if xs[-1] != total - win:
            xs.append(total - win)
        return xs

    return [(x, y, x + win, y + win) for y in starts(H) for x in starts(W)]


def clip_bbox(bx, by, bw, bh, win, min_visible: float = 0.35):
    """Przytnij bbox (piksele strony) do okna. Zwraca (x,y,w,h) w wsp. OKNA albo None,
    gdy widoczne < min_visible powierzchni bboxa."""
    x0, y0, x1, y1 = win
    ix0, iy0 = max(bx, x0), max(by, y0)
    ix1, iy1 = min(bx + bw, x1), min(by + bh, y1)
    iw, ih = ix1 - ix0, iy1 - iy0
    if iw <= 0 or ih <= 0:
        return None
    area = bw * bh
    if area <= 0 or (iw * ih) / area < min_visible:
        return None
    return (ix0 - x0, iy0 - y0, iw, ih)


def _iou(a, b) -> float:
    ax0, ay0, ax1, ay1 = a[0], a[1], a[0] + a[2], a[1] + a[3]
    bx0, by0, bx1, by1 = b[0], b[1], b[0] + b[2], b[1] + b[3]
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    inter = iw * ih
    ua = a[2] * a[3] + b[2] * b[3] - inter
    return inter / ua if ua > 0 else 0.0


def nms(boxes: list, scores: list, iou_thr: float = 0.45) -> list[int]:
    """Non-max suppression -> indeksy zachowane. boxes: [(x,y,w,h)]."""
    order = sorted(range(len(boxes)), key=lambda i: scores[i], reverse=True)
    keep: list[int] = []
    while order:
        i = order.pop(0)
        keep.append(i)
        order = [j for j in order if _iou(boxes[i], boxes[j]) < iou_thr]
    return keep


def tile_page(page: np.ndarray, bboxes: list, win: int, overlap: float, min_visible: float):
    """page: HxW(x?) ; bboxes: [(x,y,w,h,cls_id)]. Zwraca [(okno_img, [(x,y,w,h,cls_id)])]
    tylko dla okien z >=1 bboxem."""
    H, W = page.shape[:2]
    out = []
    for wnd in windows(W, H, win, overlap):
        x0, y0, x1, y1 = wnd
        labels = []
        for (bx, by, bw, bh, cid) in bboxes:
            c = clip_bbox(bx, by, bw, bh, wnd, min_visible)
            if c is not None:
                labels.append((c[0], c[1], c[2], c[3], cid))
        if labels:
            out.append((page[y0:y1, x0:x1], labels))
    return out


def export_tiled(
    out_dir: Path | None = None,
    raw_dir: Path | None = None,
    win: int = 1536,
    overlap: float = 0.2,
    min_visible: float = 0.35,
    min_count: int = 5,
    records: list[LabelRecord] | None = None,
) -> dict:
    """Zbuduj dataset YOLO w oknach. Reszta pipeline'u treningu bez zmian
    (data.yaml wskazuje na okna)."""
    import shutil

    from PIL import Image

    out = out_dir or TILED
    raw = raw_dir or RAW
    recs = records if records is not None else load_all_training_records()
    palette = load_palette_map()
    class_map, _dist = build_class_map(recs, min_count=min_count, bucket_rare=False)
    if not class_map:
        class_map = {"element": 0}
    persist_class_map(class_map)
    val_ids = load_val_page_ids()

    for sub in ("images", "labels"):
        d = out / sub
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    for split in ("train", "val"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    n = {"train": 0, "val": 0}
    for rec in recs:
        src = find_raw_image(rec, raw)
        if src is None:
            continue
        try:
            page = np.asarray(Image.open(src).convert("L"))
        except Exception:
            continue
        bxs = []
        for b in rec.bboxes:
            cid = resolve_class_id(b.tag, class_map, palette)
            if cid is not None:
                bxs.append((b.x, b.y, b.width, b.height, cid))
        if not bxs:
            continue
        split = "val" if rec.page_id in val_ids else "train"
        for i, (wimg, labels) in enumerate(tile_page(page, bxs, win, overlap, min_visible)):
            wh, ww = wimg.shape[:2]
            stem = f"{rec.page_id}__w{i:03d}"
            Image.fromarray(wimg).save(out / "images" / split / f"{stem}.png")
            lines = [
                f"{cid} {(x + w / 2) / ww:.6f} {(y + h / 2) / wh:.6f} {w / ww:.6f} {h / wh:.6f}"
                for (x, y, w, h, cid) in labels
            ]
            (out / "labels" / split / f"{stem}.txt").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
            n[split] += 1

    import yaml

    (out / "data.yaml").write_text(
        yaml.dump({
            "path": str(out.resolve()),
            "train": "images/train",
            "val": "images/val",
            "names": {idx: name for name, idx in class_map.items()},
        }, allow_unicode=True),
        encoding="utf-8",
    )
    return {"train": n["train"], "val": n["val"], "classes": len(class_map),
            "data_yaml": str(out / "data.yaml"), "win": win, "overlap": overlap}


def _cli() -> None:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Eksport datasetu YOLO w oknach (tiling).")
    ap.add_argument("--win", type=int, default=1536)
    ap.add_argument("--overlap", type=float, default=0.2)
    ap.add_argument("--min-visible", type=float, default=0.35)
    ap.add_argument("--min-count", type=int, default=5)
    args = ap.parse_args()
    print(json.dumps(export_tiled(win=args.win, overlap=args.overlap,
                                  min_visible=args.min_visible, min_count=args.min_count),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
