"""Hierarchia bboxow i relacje przestrzenne — zrodlo prawdy geometrii.

Czyste funkcje: brak I/O, brak zaleznosci od FastAPI/DB.
JS w `labeler/static/app.js` jest lustrzanym odbiciem tej samej logiki.
"""

from __future__ import annotations

from backend.models.label import BboxAnnotation, LabelRecord, SpatialRelation

# Tolerancja zawierania w pikselach — drobne nieprecyzje rysowania nie psuja hierarchii.
EPS = 1.0


def _area(b: BboxAnnotation) -> float:
    return max(b.width, 0.0) * max(b.height, 0.0)


def contains(outer: BboxAnnotation, inner: BboxAnnotation) -> bool:
    """Czy `inner` lezy w calosci wewnatrz `outer` (zawieranie scisle).

    Czesciowe nachodzenie -> False. Bbox nie zawiera sam siebie ani bboxa
    o tej samej lub wiekszej powierzchni.
    """
    if outer.id == inner.id:
        return False
    if _area(inner) >= _area(outer):
        return False
    return (
        inner.x >= outer.x - EPS
        and inner.y >= outer.y - EPS
        and inner.x + inner.width <= outer.x + outer.width + EPS
        and inner.y + inner.height <= outer.y + outer.height + EPS
    )


def find_parent(bbox: BboxAnnotation, others: list[BboxAnnotation]) -> str | None:
    """Rodzic = najmniejszy bbox w pelni zawierajacy `bbox`.

    Remis powierzchni rozstrzygany deterministycznie po `id`.
    """
    best: BboxAnnotation | None = None
    for other in others:
        if contains(other, bbox):
            if (
                best is None
                or _area(other) < _area(best)
                or (_area(other) == _area(best) and other.id < best.id)
            ):
                best = other
    return best.id if best else None


def _depth_of(bbox_id: str, parent_map: dict[str, str]) -> int:
    depth = 0
    seen: set[str] = set()
    current = parent_map.get(bbox_id, "")
    while current:
        if current in seen:  # ochrona przed cyklem
            break
        seen.add(current)
        depth += 1
        current = parent_map.get(current, "")
    return depth


def compute_hierarchy(bboxes: list[BboxAnnotation]) -> list[BboxAnnotation]:
    """Ustawia `parent_id`, `depth`, `rel_bbox` dla kazdego bboxa (in place)."""
    by_id = {b.id: b for b in bboxes}
    parent_map: dict[str, str] = {}
    for b in bboxes:
        others = [o for o in bboxes if o.id != b.id]
        parent_map[b.id] = find_parent(b, others) or ""

    for b in bboxes:
        pid = parent_map[b.id]
        b.parent_id = pid
        b.depth = _depth_of(b.id, parent_map)
        parent = by_id.get(pid) if pid else None
        if parent and parent.width > 0 and parent.height > 0:
            b.rel_bbox = [
                (b.x - parent.x) / parent.width,
                (b.y - parent.y) / parent.height,
                b.width / parent.width,
                b.height / parent.height,
            ]
        else:
            b.rel_bbox = []
    return bboxes


def _centroid(b: BboxAnnotation) -> tuple[float, float]:
    return b.x + b.width / 2.0, b.y + b.height / 2.0


def _compass(a: BboxAnnotation, b: BboxAnnotation) -> str:
    """Relacja kierunkowa a -> b wg centroidow (os dominujaca)."""
    ax, ay = _centroid(a)
    bx, by = _centroid(b)
    dx = bx - ax
    dy = by - ay
    if abs(dx) >= abs(dy):
        return "left_of" if dx >= 0 else "right_of"
    return "above" if dy >= 0 else "below"


def compute_spatial_relations(bboxes: list[BboxAnnotation]) -> list[SpatialRelation]:
    """`contains` rodzic->dziecko + kompas miedzy rodzenstwem (wspolny parent_id)."""
    relations: list[SpatialRelation] = []

    for b in bboxes:
        if b.parent_id:
            relations.append(
                SpatialRelation(from_id=b.parent_id, to_id=b.id, relation="contains")
            )

    # Grupy rodzenstwa wg parent_id (rowniez korzen: parent_id == "").
    siblings: dict[str, list[BboxAnnotation]] = {}
    for b in bboxes:
        siblings.setdefault(b.parent_id, []).append(b)

    for group in siblings.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, c = group[i], group[j]
                relations.append(
                    SpatialRelation(from_id=a.id, to_id=c.id, relation=_compass(a, c))
                )
    return relations


def enrich_label_record(record: LabelRecord) -> LabelRecord:
    """Entry point: przelicza hierarchie i relacje na calym rekordzie.

    Zwraca nowy `LabelRecord` (kopia) z uzupelnionymi polami.
    """
    enriched = record.model_copy(deep=True)
    compute_hierarchy(enriched.bboxes)
    enriched.spatial_relations = compute_spatial_relations(enriched.bboxes)
    return enriched
