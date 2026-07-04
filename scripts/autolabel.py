"""Auto-generowanie wstepnych bboxow (pre-annotacja) modelem -> do bazy.

Model proponuje bboxy na NIEOZNACZONYCH stronach i zapisuje je jako adnotacje.
Potem otwierasz strone w labelerze, akceptujesz/poprawiasz/usuwasz, Ctrl+S.
Tag bboxa = przewidziana klasa (mapuje sie z powrotem na klase przy eksporcie).

Uzycie:
    python scripts/autolabel.py --all-unlabeled --conf 0.3            # dry-run
    python scripts/autolabel.py --all-unlabeled --conf 0.3 --apply
    python scripts/autolabel.py --page <PNG> --conf 0.25 --apply
    python scripts/autolabel.py --pages "data/raw/*p04*.png" --apply --force
"""

from __future__ import annotations

import argparse
import glob
import json
import sqlite3
from pathlib import Path

import cv2

from backend.db import load_annotation, save_annotation
from backend.models.label import BboxAnnotation, LabelRecord
from backend.paths import DB_PATH, MODELS, RAW, REGISTRY_PATH
from backend.runtime_config import yolo_conf_threshold
from labeler.export import load_class_map
from backend.recognize.symbol_detector import OnnxSymbolDetector


def active_version() -> str:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8")).get("active") or "symbols_mc_v5"
        except (json.JSONDecodeError, OSError):
            pass
    return "symbols_mc_v5"


def _annotated_pages() -> set[str]:
    if not DB_PATH.exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT page_id, payload_json FROM annotations").fetchall()
    conn.close()
    out = set()
    for pid, payload in rows:
        try:
            if json.loads(payload).get("bboxes"):
                out.add(pid)
        except Exception:
            pass
    return out


def _has_bboxes(page_id: str) -> bool:
    data = load_annotation(page_id)
    return bool(data and data.get("bboxes"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--page", type=Path, help="pojedynczy PNG")
    g.add_argument("--pages", nargs="*", help="globy PNG")
    g.add_argument("--all-unlabeled", action="store_true", help="wszystkie strony bez bboxow")
    ap.add_argument("--conf", type=float, default=None)
    ap.add_argument("--version", default=None)
    ap.add_argument("--model", type=Path, default=None)
    ap.add_argument("--apply", action="store_true", help="zapisz do bazy (inaczej dry-run)")
    ap.add_argument("--force", action="store_true", help="nadpisz strony, ktore juz maja bboxy")
    args = ap.parse_args()

    conf = args.conf if args.conf is not None else yolo_conf_threshold()
    onnx = args.model or (MODELS / f"{args.version or active_version()}.onnx")
    if not onnx.exists():
        print(f"[BŁĄD] Brak modelu: {onnx}")
        return 1

    if args.page:
        pages = [args.page]
    elif args.pages:
        pages = sorted({Path(p) for pat in args.pages for p in glob.glob(pat)})
    else:
        annotated = _annotated_pages()
        pages = [p for p in sorted(RAW.glob("*.png")) if p.stem not in annotated]
    if not pages:
        print("Brak stron do przetworzenia.")
        return 1

    det = OnnxSymbolDetector(str(onnx), load_class_map())
    total = 0
    written = 0
    for page in pages:
        pid = page.stem
        if not args.force and _has_bboxes(pid):
            print(f"{pid}: pomijam (ma juz bboxy; --force aby nadpisac)")
            continue
        img = cv2.imread(str(page))
        if img is None:
            print(f"{pid}: nie wczytano")
            continue
        H, W = img.shape[:2]
        dets = det.detect(str(page), conf_threshold=conf)
        bboxes = [
            BboxAnnotation(
                id=f"auto_{pid}_{i}", class_name="element",
                x=float(d.x), y=float(d.y), width=float(d.width), height=float(d.height),
                tag=d.class_name, seq=i + 1,
            )
            for i, d in enumerate(dets)
        ]
        total += len(bboxes)
        print(f"{pid}: {len(bboxes)} propozycji")
        if args.apply:
            record = LabelRecord(
                page_id=pid, image_path=f"{pid}{page.suffix}",
                image_width=W, image_height=H, bboxes=bboxes,
            )
            save_annotation(pid, record.model_dump())
            written += 1

    print(f"\n{'ZAPISANO' if args.apply else 'DRY-RUN'}: {total} propozycji "
          f"na {written if args.apply else len(pages)} stronach.")
    if args.apply:
        print("Otworz labeler (python -m labeler.app), przejrzyj strony, popraw, Ctrl+S.")
        print("[RYZYKO] To sa PROPOZYCJE modelu — zaakceptuj/usun zanim uzyjesz do treningu.")
    else:
        print("Dodaj --apply aby zapisac do bazy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
