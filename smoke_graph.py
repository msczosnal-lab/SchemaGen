"""Ad-hoc smoke GraphBuildera po sicie (frame/text) — liczby + nakladka per rola.

Uruchom:  .venv311\\Scripts\\python.exe smoke_graph.py *p040*
Wynik: data/output/calib/<strona>_graph.png
Kolory: wire=zielony, bus=niebieski, frame=szary, other=zolty (faint), bbox symbolu=czerwony.
Oceń wzrokowo: czy obramówki urządzeń/tekst sa SZARE/żółTE (odsiane), a przewody zielone/niebieskie.
Plik throwaway — skasuj po walidacji.
"""

from __future__ import annotations

import glob
import os
import sys

import cv2

from backend.recognize.pipeline import recognize_file

OUT_DIR = "data/output/calib"
VIEW_W = 2200
ROLE_COLOR = {
    "wire": (0, 200, 0),
    "bus": (255, 0, 0),
    "frame": (150, 150, 150),
    "other": (0, 220, 220),
}


def main() -> None:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*p040*"
    matches = glob.glob(f"data/raw/{pattern}.png")
    if not matches:
        print(f"Brak strony dla wzorca data/raw/{pattern}.png")
        return
    path = matches[0]
    os.makedirs(OUT_DIR, exist_ok=True)
    model = recognize_file(path)

    roles: dict[str, int] = {}
    for ln in model.graphic_lines:
        roles[ln.role] = roles.get(ln.role, 0) + 1
    print(f"Strona: {path}")
    print(f"components : {len(model.components)}")
    print(f"graphic_lines per rola: {dict(sorted(roles.items()))}")
    print(f"connections: {len(model.connections)}")
    for c in model.connections[:20]:
        print(f"  {c.from_ref} -> {c.to} ({c.kind})")

    img = cv2.imread(path)
    h, w = img.shape[:2]
    thick = max(2, int(round(max(w, h) / 900)))
    for comp in model.components:
        if len(comp.bbox) >= 4:
            x1, y1, x2, y2 = (int(v) for v in comp.bbox[:4])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), thick)
    for ln in model.graphic_lines:
        color = ROLE_COLOR.get(ln.role)
        if color is None:
            continue
        pts = ln.points
        for i in range(len(pts) - 1):
            p1 = (int(pts[i][0]), int(pts[i][1]))
            p2 = (int(pts[i + 1][0]), int(pts[i + 1][1]))
            cv2.line(img, p1, p2, color, thick)

    scale = VIEW_W / w
    view = cv2.resize(img, (VIEW_W, int(round(h * scale))))
    base = os.path.splitext(os.path.basename(path))[0]
    fname = f"{OUT_DIR}/{base}_graph.png"
    cv2.imwrite(fname, view)
    print(f"Nakladka: {fname}")


if __name__ == "__main__":
    main()
