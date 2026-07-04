# COWORK_TASK: sync/prompts/015-relations-layer.md

"""Warstwa relacji — tekst→symbol, OCR→potencjal, scalanie strzalek, context runtime.

Wykonywane PO net-builderze w GraphBuilder.build(). Nie modyfikuje graphic_lines
ani logiki union-find — tylko wypelnia tagi, potential, context_assignments.
"""

from __future__ import annotations

import re
from functools import lru_cache

import yaml

from backend.class_map import tag_to_class
from backend.geometry.row_layout import (
    ContextAssignment as RowContextAssignment,
    Row,
    assign_contextual,
    group_into_rows,
)
from backend.models.label import BboxAnnotation
from backend.models.schema import (
    Component,
    Connection,
    ContextAssignment,
    GraphicLine,
)
from backend.paths import TRAIN_CLASSES
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.ocr_engine import TextDetection
from backend.runtime_config import relations_settings

_INSTANCE_TAG_RE = re.compile(r"^-?[A-Z]\d+", re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_row_rules() -> dict[str, frozenset[str]]:
    if not TRAIN_CLASSES.exists():
        return {}
    data = yaml.safe_load(TRAIN_CLASSES.read_text(encoding="utf-8")) or {}
    rules = data.get("row_rules") or {}
    return {k: frozenset(v or []) for k, v in rules.items()}


def _split_row_by_strip_anchors_runtime(
    row_bboxes: list[BboxAnnotation],
    classes: list[str | None],
) -> list[tuple[list[BboxAnnotation], list[str | None]]]:
    """Podzial wiersza od kotwic listwy — kopia logiki row_layout bez importu prywatnej."""
    rules = _load_row_rules()
    strip_kinds = rules.get("strip_kinds", frozenset())
    paired = sorted(zip(row_bboxes, classes), key=lambda t: t[0].x)
    bboxes = [p[0] for p in paired]
    classes = [p[1] for p in paired]
    anchor_indices = [i for i, c in enumerate(classes) if c in strip_kinds]
    if len(anchor_indices) <= 1:
        return [(bboxes, classes)]
    segments: list[tuple[list[BboxAnnotation], list[str | None]]] = []
    if anchor_indices[0] > 0:
        segments.append((bboxes[: anchor_indices[0]], classes[: anchor_indices[0]]))
    for ai, start in enumerate(anchor_indices):
        end = anchor_indices[ai + 1] if ai + 1 < len(anchor_indices) else len(bboxes)
        segments.append((bboxes[start:end], classes[start:end]))
    return segments


class RelationResolver:
    """Dopina relacje semantyczne po net-builderze."""

    def resolve(
        self,
        components: list[Component],
        texts: list[TextDetection],
        connections: list[Connection],
        graphic_lines: list[GraphicLine],
        potentials: list[str],
        *,
        image_size: tuple[int, int] | None = None,
    ) -> tuple[
        list[Component],
        list[Connection],
        list[str],
        list[ContextAssignment],
        list[str],
    ]:
        cfg = relations_settings()
        assigned_text_idxs: set[int] = set()
        wire_label_idxs: set[int] = set()

        annotations = self._assign_tags_overlap_and_instance(
            components,
            texts,
            assigned_text_idxs,
            proximity_frac=float(cfg["tag_proximity_frac"]),
            image_size=image_size,
        )

        connections, wire_label_idxs = self._apply_wire_labels(
            connections,
            texts,
            graphic_lines,
            components,
            assigned_text_idxs,
            proximity_frac=float(cfg["wire_label_proximity_frac"]),
            image_size=image_size,
        )
        assigned_text_idxs |= wire_label_idxs

        annotations.extend(
            self._assign_tags_proximity_and_collect_annotations(
                components,
                texts,
                assigned_text_idxs,
                proximity_frac=float(cfg["tag_proximity_frac"]),
                image_size=image_size,
            )
        )

        connections, potentials = self._merge_potential_arrows(
            components,
            connections,
            potentials,
            arrow_classes=frozenset(cfg["potential_arrow_classes"]),
            merge_by_tag=bool(cfg["merge_potential_arrows_by_tag"]),
        )

        context_assignments = self._runtime_context(components)
        return components, connections, potentials, context_assignments, annotations
    def _assign_tags_overlap_and_instance(
        self,
        components: list[Component],
        texts: list[TextDetection],
        assigned: set[int],
        *,
        proximity_frac: float,
        image_size: tuple[int, int] | None,
    ) -> list[str]:
        annotations: list[str] = []
        radius = _proximity_radius(proximity_frac, image_size)

        for ti, t in enumerate(texts):
            best_i = -1
            best_overlap = 0.0
            for i, c in enumerate(components):
                ov = _intersection_area(t.bbox, c.bbox)
                if ov > best_overlap:
                    best_overlap = ov
                    best_i = i
            if best_i >= 0 and best_overlap > 0.0:
                c = components[best_i]
                if not c.tag:
                    c.tag = t.text.strip()
                else:
                    annotations.append(t.text)
                assigned.add(ti)

        for ti, t in enumerate(texts):
            if ti in assigned:
                continue
            if not _INSTANCE_TAG_RE.match(t.text.strip()):
                continue
            best_i = _nearest_component_index(t, components, radius)
            if best_i >= 0 and not components[best_i].tag:
                components[best_i].tag = t.text.strip()
                assigned.add(ti)

        return annotations

    def _assign_tags_proximity_and_collect_annotations(
        self,
        components: list[Component],
        texts: list[TextDetection],
        assigned: set[int],
        *,
        proximity_frac: float,
        image_size: tuple[int, int] | None,
    ) -> list[str]:
        annotations: list[str] = []
        radius = _proximity_radius(proximity_frac, image_size)

        for ti, t in enumerate(texts):
            if ti in assigned:
                continue
            best_i = _nearest_component_index(t, components, radius)
            if best_i >= 0 and not components[best_i].tag:
                components[best_i].tag = t.text.strip()
                assigned.add(ti)
            else:
                annotations.append(t.text)

        return annotations

    # ----------------------------------------------------------- wire labels
    def _apply_wire_labels(
        self,
        connections: list[Connection],
        texts: list[TextDetection],
        graphic_lines: list[GraphicLine],
        components: list[Component],
        assigned: set[int],
        *,
        proximity_frac: float,
        image_size: tuple[int, int] | None,
    ) -> tuple[list[Connection], set[int]]:
        if not connections or not texts:
            return connections, set()

        radius = _proximity_radius(proximity_frac, image_size)
        wire_lines = [
            ln for ln in graphic_lines
            if LineClassifier.is_connection_candidate(ln) and len(ln.points) >= 2
        ]
        if not wire_lines:
            return connections, set()

        comp_bbox = {c.id: c.bbox for c in components}
        out = [c.model_copy(deep=True) for c in connections]
        used_for_wire: set[int] = set()

        for conn in out:
            if conn.potential and conn.potential.startswith("net_"):
                continue
            if conn.potential:
                continue
            node_refs = {conn.from_ref.split(":")[0], conn.to.split(":")[0]}

            best_label = ""
            best_dist = radius + 1.0
            best_ti = -1
            for ti, t in enumerate(texts):
                cx = (t.bbox[0] + t.bbox[2]) / 2
                cy = (t.bbox[1] + t.bbox[3]) / 2
                if _inside_any_bbox(cx, cy, comp_bbox.values()):
                    continue
                for ln in wire_lines:
                    p0, p1 = ln.points[0], ln.points[-1]
                    d = _dist_to_segment(
                        cx, cy, float(p0[0]), float(p0[1]), float(p1[0]), float(p1[1])
                    )
                    if d > radius:
                        continue
                    touches_node = False
                    for nid in node_refs:
                        bb = comp_bbox.get(nid)
                        if not bb:
                            continue
                        for pt in (p0, p1):
                            if _point_in_bbox(pt, bb, margin=2.0):
                                touches_node = True
                                break
                        if touches_node:
                            break
                    if not touches_node:
                        continue
                    if d < best_dist:
                        best_dist = d
                        best_label = t.text.strip()
                        best_ti = ti

            if best_label:
                conn.potential = best_label
                if best_ti >= 0:
                    used_for_wire.add(best_ti)

        return out, used_for_wire

    # ---------------------------------------------------- potential arrows
    def _merge_potential_arrows(
        self,
        components: list[Component],
        connections: list[Connection],
        potentials: list[str],
        *,
        arrow_classes: frozenset[str],
        merge_by_tag: bool,
    ) -> tuple[list[Connection], list[str]]:
        if not merge_by_tag:
            return connections, potentials

        arrow_ids = {c.id for c in components if c.type in arrow_classes}
        if not arrow_ids:
            return connections, potentials

        groups: dict[str, list[str]] = {}
        for c in components:
            if c.id not in arrow_ids:
                continue
            key = _normalize_potential_key(c.tag)
            if not key:
                continue
            groups.setdefault(key, []).append(c.id)

        pot_map: dict[str, str] = {}
        new_potentials = list(potentials)
        for key, ids in groups.items():
            if len(ids) < 2:
                continue
            pot_id = f"pot_{key}"
            if pot_id not in new_potentials:
                new_potentials.append(pot_id)
            for cid in ids:
                pot_map[cid] = pot_id

        if not pot_map:
            return connections, potentials

        filtered: list[Connection] = []
        for conn in connections:
            a = conn.from_ref.split(":")[0]
            b = conn.to.split(":")[0]
            if a in pot_map and b in pot_map and pot_map[a] == pot_map[b]:
                continue
            updated = conn.model_copy(deep=True)
            pa = pot_map.get(a)
            pb = pot_map.get(b)
            if pa and not updated.potential:
                updated.potential = pa
            elif pb and not updated.potential:
                updated.potential = pb
            if pa and pb and pa == pb:
                updated.kind = "link"
            filtered.append(updated)

        return filtered, new_potentials

    # --------------------------------------------------------- context
    def _runtime_context(self, components: list[Component]) -> list[ContextAssignment]:
        if not components:
            return []

        rules = _load_row_rules()
        bboxes = [
            BboxAnnotation(
                id=c.id,
                class_name=c.type or "element",
                x=c.bbox[0],
                y=c.bbox[1],
                width=c.bbox[2] - c.bbox[0],
                height=c.bbox[3] - c.bbox[1],
                tag=c.tag,
            )
            for c in components
        ]
        classes = [_effective_class(c) for c in components]
        id_to_class = {c.id: cls for c, cls in zip(components, classes)}

        assignments: list[ContextAssignment] = []
        for row in group_into_rows(bboxes):
            row_classes = [id_to_class.get(b.id) for b in row.bboxes]
            for sub_bboxes, sub_classes in _split_row_by_strip_anchors_runtime(
                row.bboxes, row_classes
            ):
                sub_row = Row(index=row.index, bboxes=sub_bboxes, classes=sub_classes)
                assignments.extend(
                    assign_contextual(
                        sub_row,
                        sub_classes,
                        strip_members=rules.get("strip_members", frozenset()),
                        strip_kinds=rules.get("strip_kinds", frozenset()),
                        cable_members=rules.get("cable_members", frozenset()),
                        cable_anchor=rules.get("cable_anchor", frozenset()),
                        device_terminals=rules.get("device_terminals", frozenset()),
                        inline_no_parent=rules.get("inline_no_parent", frozenset()),
                    )
                )
        return assignments


# ----------------------------------------------------------------- helpers
def _effective_class(c: Component) -> str | None:
    if c.tag:
        cls = tag_to_class(c.tag)
        if cls:
            return cls
    return c.type or None


def _proximity_radius(frac: float, image_size: tuple[int, int] | None) -> float:
    if not image_size:
        return max(12.0, frac * 1000.0)
    w, h = image_size
    return max(12.0, frac * max(w, h))


def _intersection_area(a: list[float], b: list[float]) -> float:
    if len(a) < 4 or len(b) < 4:
        return 0.0
    ix1 = max(a[0], b[0])
    iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2])
    iy2 = min(a[3], b[3])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def _dist(x1: float, y1: float, x2: float, y2: float) -> float:
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


def _nearest_component_index(
    t: TextDetection, components: list[Component], radius: float
) -> int:
    tcx = (t.bbox[0] + t.bbox[2]) / 2
    tcy = (t.bbox[1] + t.bbox[3]) / 2
    best_i = -1
    best_d = radius + 1.0
    for i, c in enumerate(components):
        if c.tag:
            continue
        d = _dist_to_bbox(tcx, tcy, c.bbox)
        if d <= radius and d < best_d:
            best_d = d
            best_i = i
    return best_i


def _dist_to_bbox(cx: float, cy: float, bbox: list[float]) -> float:
    nx = max(bbox[0], min(cx, bbox[2]))
    ny = max(bbox[1], min(cy, bbox[3]))
    return _dist(cx, cy, nx, ny)


def _dist_to_segment(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> float:
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return _dist(px, py, x1, y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    qx = x1 + t * dx
    qy = y1 + t * dy
    return _dist(px, py, qx, qy)


def _point_in_bbox(
    pt: list[float] | tuple[float, float], bbox: list[float], *, margin: float
) -> bool:
    x, y = float(pt[0]), float(pt[1])
    return (
        bbox[0] - margin <= x <= bbox[2] + margin
        and bbox[1] - margin <= y <= bbox[3] + margin
    )


def _inside_any_bbox(cx: float, cy: float, bboxes) -> bool:
    for bb in bboxes:
        if _point_in_bbox((cx, cy), bb, margin=0.0):
            return True
    return False


def _normalize_potential_key(tag: str) -> str:
    s = (tag or "").strip().upper()
    s = re.sub(r"[^A-Z0-9_+-]+", "_", s)
    return s.strip("_")
