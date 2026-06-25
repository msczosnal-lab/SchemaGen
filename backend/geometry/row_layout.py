"""Grupowanie bboxow w poziome wiersze (os Y) i resolver kontekstu.

Czyste funkcje — bez I/O. Uzywane przez ContextResolver (GT labeler) oraz
post-NMS dedup detekcji YOLO (symbol_detector).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol, TypeVar

import yaml

from backend.class_map import load_palette_map, tag_to_class
from backend.models.label import BboxAnnotation
from backend.paths import TRAIN_CLASSES

TDet = TypeVar("TDet", bound="_DetLike")


@dataclass
class Row:
    """Poziomy rzad bboxow o wspolnej osi Y."""

    index: int
    bboxes: list[BboxAnnotation] = field(default_factory=list)
    classes: list[str | None] = field(default_factory=list)

    @property
    def mean_cy(self) -> float:
        if not self.bboxes:
            return 0.0
        return sum(b.y + b.height / 2 for b in self.bboxes) / len(self.bboxes)


@dataclass
class ContextAssignment:
    """Przypisanie kontekstowe bboxa w wierszu."""

    bbox_id: str
    role: str
    row_index: int
    anchor_id: str | None = None
    strip_kind: str | None = None


class _DetLike(Protocol):
    x: float
    y: float
    width: float
    height: float
    confidence: float
    class_name: str


def _cy(b: BboxAnnotation) -> float:
    return b.y + b.height / 2


def _median_height(bboxes: list[BboxAnnotation]) -> float:
    if not bboxes:
        return 1.0
    hs = sorted(b.height for b in bboxes if b.height > 0)
    return hs[len(hs) // 2] if hs else 1.0


@lru_cache(maxsize=1)
def _load_row_rules() -> dict[str, frozenset[str]]:
    if not TRAIN_CLASSES.exists():
        return {}
    data = yaml.safe_load(TRAIN_CLASSES.read_text(encoding="utf-8")) or {}
    rules = data.get("row_rules") or {}
    return {k: frozenset(v or []) for k, v in rules.items()}


def group_into_rows(
    bboxes: list[BboxAnnotation],
    y_tol_factor: float = 0.4,
) -> list[Row]:
    """Grupuj bboxy w wiersze po srodku Y.

    `y_tol_factor` * mediana wysokosci w wierszu = max odchylenie cy od sredniej.
    """
    if not bboxes:
        return []
    ordered = sorted(bboxes, key=lambda b: (_cy(b), b.x))
    rows: list[Row] = []
    current: list[BboxAnnotation] = [ordered[0]]
    current_cy = _cy(ordered[0])

    for b in ordered[1:]:
        cy = _cy(b)
        tol = y_tol_factor * _median_height(current + [b])
        if abs(cy - current_cy) <= tol:
            current.append(b)
            current_cy = sum(_cy(x) for x in current) / len(current)
        else:
            rows.append(Row(index=len(rows), bboxes=current))
            current = [b]
            current_cy = cy
    rows.append(Row(index=len(rows), bboxes=current))
    return rows


def _classes_for(bboxes: list[BboxAnnotation]) -> list[str | None]:
    pmap = load_palette_map()
    return [tag_to_class(b.tag, pmap) for b in bboxes]


def _split_row_by_strip_anchors(row: Row, classes: list[str | None]) -> list[Row]:
    """Na jednym Y moze byc kilka listw — podzial od kotwic listwa/zwarta (sort X)."""
    rules = _load_row_rules()
    strip_kinds = rules.get("strip_kinds", frozenset())
    paired = sorted(zip(row.bboxes, classes), key=lambda t: t[0].x)
    bboxes = [p[0] for p in paired]
    classes = [p[1] for p in paired]
    anchor_indices = [i for i, c in enumerate(classes) if c in strip_kinds]
    if len(anchor_indices) <= 1:
        return [Row(index=row.index, bboxes=bboxes, classes=classes)]

    segments: list[Row] = []
    if anchor_indices[0] > 0:
        segments.append(
            Row(
                index=len(segments),
                bboxes=bboxes[: anchor_indices[0]],
                classes=classes[: anchor_indices[0]],
            )
        )
    for ai, start in enumerate(anchor_indices):
        end = anchor_indices[ai + 1] if ai + 1 < len(anchor_indices) else len(bboxes)
        segments.append(
            Row(index=len(segments), bboxes=bboxes[start:end], classes=classes[start:end])
        )
    return segments


def find_anchor_in_row(
    row: Row,
    classes: list[str | None],
    anchor_classes: frozenset[str],
) -> BboxAnnotation | None:
    """Pierwsza kotwica w wierszu (sort X) sposrod `anchor_classes`."""
    paired = sorted(zip(row.bboxes, classes), key=lambda t: t[0].x)
    for b, cls in paired:
        if cls in anchor_classes:
            return b
    return None


def assign_contextual(
    row: Row,
    classes: list[str | None],
    *,
    strip_members: frozenset[str],
    strip_kinds: frozenset[str],
    cable_members: frozenset[str],
    cable_anchor: frozenset[str],
    device_terminals: frozenset[str],
    inline_no_parent: frozenset[str],
) -> list[ContextAssignment]:
    """Przypisz role kontekstowe bboxom w jednym (pod-)wierszu."""
    strip_anchor = find_anchor_in_row(row, classes, strip_kinds)
    strip_kind = None
    if strip_anchor:
        idx = row.bboxes.index(strip_anchor)
        strip_kind = classes[idx]
    cable_anchor_box = find_anchor_in_row(row, classes, cable_anchor)

    out: list[ContextAssignment] = []
    for b, cls in zip(row.bboxes, classes):
        if not cls:
            continue
        if cls in strip_members:
            out.append(
                ContextAssignment(
                    bbox_id=b.id,
                    role=cls,
                    row_index=row.index,
                    anchor_id=strip_anchor.id if strip_anchor else None,
                    strip_kind=strip_kind,
                )
            )
        elif cls in cable_members:
            out.append(
                ContextAssignment(
                    bbox_id=b.id,
                    role=cls,
                    row_index=row.index,
                    anchor_id=cable_anchor_box.id if cable_anchor_box else None,
                )
            )
        elif cls in device_terminals:
            out.append(ContextAssignment(bbox_id=b.id, role=cls, row_index=row.index))
        elif cls in inline_no_parent:
            out.append(ContextAssignment(bbox_id=b.id, role=cls, row_index=row.index))
        elif cls in strip_kinds:
            out.append(
                ContextAssignment(
                    bbox_id=b.id, role=cls, row_index=row.index, strip_kind=cls
                )
            )
        elif cls in cable_anchor:
            out.append(ContextAssignment(bbox_id=b.id, role=cls, row_index=row.index))
    return out


class ContextResolver:
    """Przypisuje role kontekstowe bboxom w wierszach (GT z labelera)."""

    def resolve(self, bboxes: list[BboxAnnotation]) -> list[ContextAssignment]:
        rules = _load_row_rules()
        strip_members = rules.get("strip_members", frozenset())
        strip_kinds = rules.get("strip_kinds", frozenset())
        cable_members = rules.get("cable_members", frozenset())
        cable_anchor = rules.get("cable_anchor", frozenset())
        device_terminals = rules.get("device_terminals", frozenset())
        inline_no_parent = rules.get("inline_no_parent", frozenset())

        assignments: list[ContextAssignment] = []
        for row in group_into_rows(bboxes):
            classes = _classes_for(row.bboxes)
            for sub in _split_row_by_strip_anchors(row, classes):
                sub_classes = sub.classes or _classes_for(sub.bboxes)
                assignments.extend(
                    assign_contextual(
                        sub,
                        sub_classes,
                        strip_members=strip_members,
                        strip_kinds=strip_kinds,
                        cable_members=cable_members,
                        cable_anchor=cable_anchor,
                        device_terminals=device_terminals,
                        inline_no_parent=inline_no_parent,
                    )
                )
        return assignments


def dedup_detections_by_row(
    detections: list[TDet],
    y_tol_factor: float = 0.4,
    x_overlap_iou: float = 0.3,
) -> list[TDet]:
    """Post-NMS: w jednym wierszu i tej samej klasie zostaw najwyzsze conf przy nakladaniu X."""
    if len(detections) <= 1:
        return detections

    by_class: dict[str, list[TDet]] = {}
    for d in detections:
        by_class.setdefault(d.class_name, []).append(d)

    kept: list[TDet] = []
    for group in by_class.values():
        if len(group) == 1:
            kept.append(group[0])
            continue
        pseudo = [
            BboxAnnotation(
                id=str(i),
                class_name="element",
                x=d.x,
                y=d.y,
                width=d.width,
                height=d.height,
            )
            for i, d in enumerate(group)
        ]
        rows = group_into_rows(pseudo, y_tol_factor=y_tol_factor)
        id_to_det = {str(i): group[i] for i in range(len(group))}
        for row in rows:
            row_dets = [id_to_det[b.id] for b in row.bboxes]
            row_dets.sort(key=lambda d: d.x)
            accepted: list[TDet] = []
            for det in row_dets:
                drop = False
                for prev in list(accepted):
                    if _x_iou(prev, det) >= x_overlap_iou:
                        if det.confidence <= prev.confidence:
                            drop = True
                            break
                        accepted.remove(prev)
                if not drop:
                    accepted.append(det)
            kept.extend(accepted)
    return kept


def _x_iou(a: _DetLike, b: _DetLike) -> float:
    ax1, ax2 = a.x, a.x + a.width
    bx1, bx2 = b.x, b.x + b.width
    inter = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    if inter <= 0:
        return 0.0
    union = a.width + b.width - inter
    return inter / union if union > 0 else 0.0
