"""Parser plikow .elmt (QElectroTech XML) — nazwy, geometria, terminale."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class QetTerminal:
    x: float
    y: float
    orientation: str
    name: str


@dataclass
class QetGeometry:
    """Prymitywy geometryczne z pliku .elmt (wspolrzedne wzgl. hotspota)."""

    lines: list[tuple[float, float, float, float]] = field(default_factory=list)
    rects: list[tuple[float, float, float, float]] = field(default_factory=list)
    circles: list[tuple[float, float, float]] = field(default_factory=list)  # cx, cy, r
    arcs: list[tuple[float, float, float, float, float, float]] = field(
        default_factory=list
    )  # x, y, w, h, start_deg, span_deg
    polygons: list[list[tuple[float, float]]] = field(default_factory=list)
    terminals: list[QetTerminal] = field(default_factory=list)

    def all_points(self) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        for x1, y1, x2, y2 in self.lines:
            pts += [(x1, y1), (x2, y2)]
        for x, y, w, h in self.rects:
            pts += [(x, y), (x + w, y + h)]
        for cx, cy, r in self.circles:
            pts += [(cx - r, cy - r), (cx + r, cy + r)]
        for x, y, w, h, _s, _a in self.arcs:
            pts += [(x, y), (x + w, y + h)]
        for poly in self.polygons:
            pts += poly
        for t in self.terminals:
            pts.append((t.x, t.y))
        return pts

    def bounding_box(self) -> tuple[float, float, float, float] | None:
        pts = self.all_points()
        if not pts:
            return None
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)


@dataclass
class QetElement:
    path: Path
    width: float
    height: float
    hotspot_x: float
    hotspot_y: float
    names: dict[str, str]  # lang → name
    geometry: QetGeometry

    def name_en(self) -> str:
        return self.names.get("en") or self.names.get("fr") or next(iter(self.names.values()), "")

    def name_pl(self) -> str:
        return self.names.get("pl", "")

    def slug(self) -> str:
        name = self.name_en()
        s = name.strip().lower()
        s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
        s = re.sub(r"[\s_-]+", "_", s).strip("_")
        return s or re.sub(r"[^\w]", "_", self.path.stem.lower())


def parse_elmt(path: Path) -> QetElement:
    """Parsuje plik .elmt i zwraca QetElement."""
    tree = ET.parse(path)
    root = tree.getroot()

    width = float(root.get("width", 50))
    height = float(root.get("height", 60))
    hotspot_x = float(root.get("hotspot_x", width / 2))
    hotspot_y = float(root.get("hotspot_y", height / 2))

    names: dict[str, str] = {}
    for name_el in root.findall("./names/name"):
        lang = name_el.get("lang", "en")
        text = (name_el.text or "").strip()
        if text:
            names[lang] = text

    geom = QetGeometry()
    desc = root.find("description")
    if desc is not None:
        for child in desc:
            _parse_primitive(child, geom)

    return QetElement(
        path=path,
        width=width,
        height=height,
        hotspot_x=hotspot_x,
        hotspot_y=hotspot_y,
        names=names,
        geometry=geom,
    )


def _parse_primitive(child: ET.Element, geom: QetGeometry) -> None:
    tag = child.tag
    if tag == "line":
        geom.lines.append((
            float(child.get("x1", 0)),
            float(child.get("y1", 0)),
            float(child.get("x2", 0)),
            float(child.get("y2", 0)),
        ))
    elif tag == "rect":
        geom.rects.append((
            float(child.get("x", 0)),
            float(child.get("y", 0)),
            float(child.get("width", 0)),
            float(child.get("height", 0)),
        ))
    elif tag == "circle":
        diameter = float(child.get("diameter", 10))
        geom.circles.append((
            float(child.get("x", 0)),
            float(child.get("y", 0)),
            diameter / 2,
        ))
    elif tag == "arc":
        geom.arcs.append((
            float(child.get("x", 0)),
            float(child.get("y", 0)),
            float(child.get("width", 20)),
            float(child.get("height", 20)),
            float(child.get("start", 0)),
            float(child.get("angle", 90)),
        ))
    elif tag == "polygon":
        pts = [(float(pt.get("x", 0)), float(pt.get("y", 0))) for pt in child.findall("point")]
        if pts:
            geom.polygons.append(pts)
    elif tag == "terminal":
        geom.terminals.append(QetTerminal(
            x=float(child.get("x", 0)),
            y=float(child.get("y", 0)),
            orientation=child.get("orientation", "n"),
            name=child.get("name", ""),
        ))
    # text, dynamic_text, input — pomijamy (metadane, nie geometria)
