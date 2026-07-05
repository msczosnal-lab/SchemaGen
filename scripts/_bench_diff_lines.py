"""Jednorazowy benchmark diff_lines na p027."""
import time
from pathlib import Path

import cv2

from backend.catalog import load_catalog
from backend.paths import resolve_page_id
from backend.recognize.pipeline import recognize_file
from backend.runtime_config import line_match_tol
from backend.validate.diff_metrics import diff_lines
from labeler.export import label_to_schema

pid = "p027"
cat = load_catalog()
rec = next(r for r in cat if resolve_page_id(r.page_id) == pid)
gt = label_to_schema(rec)
img = Path("data/raw") / f"22_A_153_PL_Adamed_AGV_SA2_20250706_{pid}.png"
im = cv2.imread(str(img))
print(f"image shape: {im.shape if im is not None else None}")
print(f"GT lines: {len(gt.graphic_lines)}")

t0 = time.perf_counter()
rt = recognize_file(str(img))
print(f"RT lines: {len(rt.graphic_lines)}, recognize: {time.perf_counter() - t0:.1f}s")

tol = line_match_tol()
t1 = time.perf_counter()
res = diff_lines(gt, rt, tol)
t_diff = time.perf_counter() - t1
print(f"diff_lines: {t_diff:.2f}s, f1={res['f1']}, tol={tol}")
