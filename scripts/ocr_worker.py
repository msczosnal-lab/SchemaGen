"""Subprocess OCR — izolacja paddle od torch w procesie rodzica.

Uruchamiany przez PaddleOcrEngine gdy torch jest juz zaladowany (YOLO/ONNX).
Stdout: JSON list[{text, bbox, confidence}].

[ENV] OCR wymaga paddlepaddle CPU (nie -gpu obok torch). Przy bledzie libpaddle:
  pip uninstall paddlepaddle-gpu -y && pip install paddlepaddle
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Przed jakimkolwiek importem ML — CPU-only, bez pobierania modeli online w petli.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.recognize.ocr_engine import extract_text_inprocess  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", type=Path)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--cpu", action="store_true")
    args = ap.parse_args()
    if not args.image.exists():
        print(json.dumps({"error": f"brak pliku: {args.image}"}), file=sys.stderr)
        return 1
    try:
        dets = extract_text_inprocess(
            args.image, use_gpu=not args.cpu, lang=args.lang
        )
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    payload = [
        {"text": d.text, "bbox": d.bbox, "confidence": d.confidence}
        for d in dets
    ]
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
