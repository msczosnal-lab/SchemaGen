"""Testy geometrii hierarchii bboxow."""

from backend.geometry.bbox_layout import (
    compute_hierarchy,
    compute_spatial_relations,
    contains,
    enrich_label_record,
    find_parent,
)
from backend.models.label import BboxAnnotation, LabelRecord


def _bbox(id_: str, x: float, y: float, w: float, h: float) -> BboxAnnotation:
    return BboxAnnotation(id=id_, class_name="element", x=x, y=y, width=w, height=h)


def test_contains_strict() -> None:
    outer = _bbox("a", 0, 0, 100, 100)
    inner = _bbox("b", 10, 10, 20, 20)
    assert contains(outer, inner)
    assert not contains(inner, outer)
    # identyczny bbox nie zawiera samego siebie
    assert not contains(outer, outer)


def test_contains_partial_overlap_false() -> None:
    a = _bbox("a", 0, 0, 50, 50)
    b = _bbox("b", 40, 40, 50, 50)  # nachodzi tylko rogiem
    assert not contains(a, b)
    assert find_parent(b, [a]) is None


def test_find_parent_smallest_area() -> None:
    big = _bbox("big", 0, 0, 100, 100)
    mid = _bbox("mid", 5, 5, 60, 60)
    child = _bbox("child", 10, 10, 10, 10)
    # oba zawieraja child -> wybor mniejszego (mid)
    assert find_parent(child, [big, mid]) == "mid"


def test_block_contains_symbol_depths() -> None:
    block = _bbox("element_1", 0, 0, 200, 200)
    symbol = _bbox("element_2", 50, 50, 40, 60)
    compute_hierarchy([block, symbol])
    assert block.parent_id == "" and block.depth == 0
    assert symbol.parent_id == "element_1" and symbol.depth == 1
    # rel_bbox = (x-px)/pw, (y-py)/ph, w/pw, h/ph
    assert symbol.rel_bbox == [50 / 200, 50 / 200, 40 / 200, 60 / 200]
    assert block.rel_bbox == []


def test_three_levels() -> None:
    a = _bbox("a", 0, 0, 300, 300)
    b = _bbox("b", 20, 20, 200, 200)
    c = _bbox("c", 40, 40, 50, 50)
    compute_hierarchy([a, b, c])
    assert a.depth == 0 and a.parent_id == ""
    assert b.depth == 1 and b.parent_id == "a"
    assert c.depth == 2 and c.parent_id == "b"


def test_sibling_relations() -> None:
    parent = _bbox("p", 0, 0, 200, 200)
    left = _bbox("left", 10, 80, 20, 20)
    right = _bbox("right", 150, 80, 20, 20)
    top = _bbox("top", 10, 10, 20, 20)
    bboxes = [parent, left, right, top]
    compute_hierarchy(bboxes)
    rels = compute_spatial_relations(bboxes)
    pairs = {(r.from_id, r.to_id): r.relation for r in rels}
    # zawieranie rodzic->dziecko
    assert pairs[("p", "left")] == "contains"
    # rodzenstwo: left jest na lewo od right
    assert pairs[("left", "right")] == "left_of"
    # top jest powyzej left (os pionowa dominuje)
    assert pairs[("left", "top")] == "below"


def test_enrich_old_record_without_fields() -> None:
    record = LabelRecord(
        page_id="p1",
        image_path="p1.png",
        bboxes=[_bbox("element_1", 0, 0, 200, 200), _bbox("element_2", 50, 50, 30, 30)],
    )
    assert record.bboxes[1].parent_id == ""  # stan przed enrich
    enriched = enrich_label_record(record)
    assert enriched.bboxes[1].parent_id == "element_1"
    assert enriched.bboxes[1].depth == 1
    assert any(
        r.relation == "contains" and r.from_id == "element_1" and r.to_id == "element_2"
        for r in enriched.spatial_relations
    )
    # oryginal nietkniety (kopia)
    assert record.bboxes[1].parent_id == ""
