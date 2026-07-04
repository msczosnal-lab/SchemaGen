"""Diagnostyka 019 — uruchom na GLOWNYM PC (pelne repo + data/raw + GT DB).

READ-ONLY: niczego nie zapisuje poza raportem sync/analysis/019-diag-output.md.

Uruchomienie (z katalogu repo):
    python sync/analysis/019_diag_main.py
    python sync/analysis/019_diag_main.py --no-yolo   # pomin sekcje F (ONNX)

Odpowiada na pytania z 019-terminals-lines-findings.md:
  A. rozmiary stron p027/p035/p040 (efektywne progi Hough/terminal_tol w px)
  B. run-length tuszu na szynie p027 (weryfikacja 67-76/21-22 px w pelnej skali)
  C. realne kolory przewodow (Q1/H5): top kolory nasycone + histogram
     detected_color per rola + stabilnosc _sample_color (2 przebiegi)
  D. linie w pasie listwy p027 y~2905 (H7 na pelnej stronie)
  E. GT terminale per klasa z SQLite (Q2: ile terminali ma zlaczka w GT)
  F. strzalki: YOLO raw vs po arrow_supplement na p027/p035/p040 (H9)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from backend.paths import DB_PATH, RAW, resolve_page_id  # noqa: E402

PAGES = ("p027", "p035", "p040")
OUT = REPO / "sync" / "analysis" / "019-diag-output.md"
_report: list[str] = []


def say(line: str = "") -> None:
    print(line)
    _report.append(line)


def page_png(short: str) -> Path | None:
    p = RAW / f"{resolve_page_id(short)}.png"
    return p if p.exists() else None


# ------------------------------------------------------------------ A: rozmiary
def sec_a() -> dict[str, tuple[int, int]]:
    say("## A. Rozmiary stron + efektywne progi\n")
    sizes: dict[str, tuple[int, int]] = {}
    for pg in PAGES:
        p = page_png(pg)
        if p is None:
            say(f"- {pg}: BRAK pliku w data/raw")
            continue
        img = cv2.imread(str(p))
        h, w = img.shape[:2]
        sizes[pg] = (w, h)
        big = max(w, h)
        say(
            f"- {pg}: {w}x{h} -> hough min_len={max(20, round(0.02 * big))} px, "
            f"gap={max(4, round(0.0015 * big))} px, terminal_tol={max(12.0, 0.012 * big):.1f} px"
        )
    say()
    return sizes


# ------------------------------------------------- B: run-length szyny p027
def sec_b() -> None:
    say("## B. Run-length tuszu na szynie p027 (pas y 2820-3000)\n")
    p = page_png("p027")
    if p is None:
        say("- BRAK p027\n")
        return
    img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
    band = img[2820:3000, :]
    dark = (band < 128).sum(axis=1)
    y_bus = 2820 + int(np.argmax(dark))
    row = (img[y_bus, :] < 128).astype(int)
    runs: list[tuple[int, int]] = []
    i = 0
    while i < len(row):
        j = i
        while j < len(row) and row[j] == row[i]:
            j += 1
        runs.append((int(row[i]), j - i))
        i = j
    ink = sorted(l for v, l in runs if v == 1)
    gaps = sorted(l for v, l in runs if v == 0)[1:-1]  # bez marginesow strony
    say(f"- y szyny: {y_bus}, tusz w wierszu: {sum(ink)}/{len(row)} px")
    if ink:
        say(f"- segmenty tuszu: n={len(ink)} min/med/max = {ink[0]}/{ink[len(ink)//2]}/{ink[-1]} px")
    if gaps:
        small = [g for g in gaps if g <= 60]
        say(f"- przerwy: n={len(gaps)} med={gaps[len(gaps)//2]} px; przerwy<=60px (kolka): "
            f"n={len(small)} min/med/max = {min(small)}/{sorted(small)[len(small)//2]}/{max(small)} px"
            if small else f"- przerwy: n={len(gaps)} (brak <=60px)")
    say()


# ------------------------------------------------------- C: kolory (Q1 / H5)
def _top_saturated(img: np.ndarray, k: int = 10) -> list[tuple[str, int]]:
    b, g, r = img[..., 0].astype(int), img[..., 1].astype(int), img[..., 2].astype(int)
    mx = np.maximum(np.maximum(b, g), r)
    mn = np.minimum(np.minimum(b, g), r)
    mask = ((mx - mn) > 40) & (mx < 250)  # nasycone, nie-biale
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return []
    q = 32  # kwantyzacja
    bb = (b[ys, xs] // q) * q + q // 2
    gg = (g[ys, xs] // q) * q + q // 2
    rr = (r[ys, xs] // q) * q + q // 2
    cnt = Counter(zip(rr, gg, bb))
    return [(f"#{r_:02x}{g_:02x}{b_:02x}", n) for (r_, g_, b_), n in cnt.most_common(k)]


def sec_c() -> None:
    say("## C. Kolory (Q1 z findings + H5)\n")
    from backend.recognize.line_classifier import LineClassifier
    from backend.recognize.line_tracer import LineTracer

    for pg in PAGES:
        p = page_png(pg)
        if p is None:
            continue
        img = cv2.imread(str(p))
        say(f"### {pg}")
        say(f"- czy strona kolorowa: {'TAK' if (_top_saturated(img, 1)) else 'NIE (grayscale)'}")
        top = _top_saturated(img)
        if top:
            say("- top kolory nasycone (kwant. 32): " + ", ".join(f"{h} x{n}" for h, n in top))
        # 2x trace -> histogram detected_color per rola + stabilnosc (H5)
        tracer = LineTracer()
        segs1 = tracer.trace(str(p))
        segs2 = tracer.trace(str(p))
        h, w = img.shape[:2]
        lines = LineClassifier().classify(segs1, image_size=(w, h))
        per_role: dict[str, Counter] = defaultdict(Counter)
        no_group = Counter()
        for ln in lines:
            per_role[ln.role][ln.detected_color] += 1
            if ln.role == "wire" and not ln.semantic_group:
                no_group[ln.detected_color] += 1
        for role, cnt in sorted(per_role.items()):
            say(f"- rola {role}: {sum(cnt.values())} linii, top hex: "
                + ", ".join(f"{c or '(brak)'} x{n}" for c, n in cnt.most_common(6)))
        say("- wire BEZ semantic_group (H4): "
            + (", ".join(f"{c} x{n}" for c, n in no_group.most_common(8)) or "0"))
        c1 = Counter(s.detected_color for s in segs1)
        c2 = Counter(s.detected_color for s in segs2)
        diff = sum((c1 - c2).values()) + sum((c2 - c1).values())
        say(f"- stabilnosc _sample_color 2 przebiegow (H5): roznych probek {diff} "
            f"(0 = deterministyczne)\n")


# --------------------------------------------- D: pas listwy p027 (H7 pelna strona)
def sec_d() -> None:
    say("## D. Linie w pasie listwy p027 (y 2850-2960)\n")
    p = page_png("p027")
    if p is None:
        say("- BRAK p027\n")
        return
    from backend.recognize.line_classifier import LineClassifier
    from backend.recognize.line_tracer import LineTracer

    img = cv2.imread(str(p))
    h, w = img.shape[:2]
    lines = LineClassifier().classify(LineTracer().trace(str(p)), image_size=(w, h))
    band = [ln for ln in lines if ln.points
            and 2850 <= sum(pt[1] for pt in ln.points) / len(ln.points) <= 2960]
    horiz = [ln for ln in band if abs(ln.points[0][1] - ln.points[-1][1]) < 20]
    say(f"- linii w pasie: {len(band)} (poziomych: {len(horiz)}), role: "
        + str(dict(Counter(ln.role for ln in band))))
    if horiz:
        longest = max(abs(ln.points[-1][0] - ln.points[0][0]) for ln in horiz)
        say(f"- najdluzsza pozioma: {longest:.0f} px (szyna ma ~5460 px; "
            f"<100 px = potwierdzenie H7 na pelnej stronie)")
    say()


# ------------------------------------------------------ E: GT terminale (Q2)
def sec_e() -> None:
    say("## E. GT terminale per klasa (SQLite) — Q2\n")
    if not DB_PATH.exists():
        say("- BRAK data/schemagen.db\n")
        return
    db = sqlite3.connect(str(DB_PATH))
    rows = db.execute("SELECT page_id, payload_json FROM annotations").fetchall()
    db.close()
    per_class: dict[str, Counter] = defaultdict(Counter)  # tag -> Counter(n_terminali)
    for _pid, payload in rows:
        try:
            rec = json.loads(payload)
        except Exception:
            continue
        for b in rec.get("bboxes", []):
            tag = (b.get("tag") or b.get("type") or "?").strip() or "?"
            per_class[tag][len(b.get("terminals") or [])] += 1
    if not per_class:
        say("- baza bez adnotacji z terminalami")
    for tag in sorted(per_class):
        cnt = per_class[tag]
        total = sum(cnt.values())
        with_t = total - cnt.get(0, 0)
        if with_t == 0:
            continue
        say(f"- {tag}: {total} bbox, z terminalami {with_t}, "
            f"rozklad liczby terminali: {dict(sorted(cnt.items()))}")
    say()


# ----------------------------------------------------- F: strzalki (H9)
def sec_f() -> None:
    say("## F. Strzalki: YOLO raw vs po supplement (H9)\n")
    try:
        from backend.recognize.arrow_supplement import supplement_arrow_detections
        from backend.recognize.graph_builder import _active_model_path
        from backend.recognize.symbol_detector import OnnxSymbolDetector
        from backend.runtime_config import yolo_tile_overlap, yolo_tile_win

        det = OnnxSymbolDetector(_active_model_path())
    except Exception as e:
        say(f"- pominiete (ONNX niedostepny): {e}\n")
        return
    arrows = ("strzalka_potencjalu_wejsciowa", "strzalka_potencjalu_wyjsciowa")
    for pg in PAGES:
        p = page_png(pg)
        if p is None:
            continue
        raw = det.detect_tiled(str(p), win=yolo_tile_win(), overlap=yolo_tile_overlap())
        img = cv2.imread(str(p))
        supp = supplement_arrow_detections(img, raw)
        def stat(dets):
            out = {}
            for a in arrows:
                ds = [d for d in dets if d.class_name == a]
                out[a.rsplit("_", 1)[-1]] = (
                    f"{len(ds)} (conf {min(d.confidence for d in ds):.2f}-"
                    f"{max(d.confidence for d in ds):.2f})" if ds else "0")
            return out
        say(f"- {pg}: raw YOLO {stat(raw)} | po supplement {stat(supp)}")
        for a in arrows:
            n_raw = sum(1 for d in raw if d.class_name == a)
            n_supp = sum(1 for d in supp if d.class_name == a)
            if n_raw > 0 and n_supp == n_raw:
                say(f"    UWAGA: {a} ma {n_raw} raw detekcji -> supplement WYLACZONY "
                    f"dla tej klasy (findings H9b — 1 FP blokuje uzupelnienie)")
    say()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-yolo", action="store_true", help="pomin sekcje F (ONNX)")
    args = ap.parse_args()
    say("# 019 diag — wynik z glownego PC\n")
    sec_a()
    for fn in (sec_b, sec_c, sec_d, sec_e):
        try:
            fn()
        except Exception as e:  # sekcje niezalezne
            say(f"[BLAD sekcji {fn.__name__}] {e}\n")
    if not args.no_yolo:
        try:
            sec_f()
        except Exception as e:
            say(f"[BLAD sekcji F] {e}\n")
    OUT.write_text("\n".join(_report) + "\n", encoding="utf-8")
    print(f"\nRaport zapisany: {OUT}")


if __name__ == "__main__":
    main()
