"""Testy budowy mapy klas YOLO z pola `tag`."""

from backend.class_map import (
    build_class_map,
    normalize_tag,
    resolve_class_id,
    slugify,
    tag_to_class,
)
from backend.models.label import BboxAnnotation, LabelRecord


def _rec(page_id, tags):
    return LabelRecord(
        page_id=page_id, image_path=f"{page_id}.png", image_width=100, image_height=100,
        bboxes=[BboxAnnotation(id=f"{page_id}_{i}", class_name="element",
                               x=i, y=i, width=5, height=5, tag=t)
                for i, t in enumerate(tags)],
    )


def test_normalize_and_slug_polish():
    assert normalize_tag("Wyłącznik") == "wylacznik"
    assert slugify("Strzałka potencjału (wejściowa)") == "strzalka_potencjalu_wejsciowa"


def test_tag_matches_palette_label():
    # "silnik" (palette label_pl) -> kanoniczne id "motor"
    assert tag_to_class("silnik") == "motor"
    assert tag_to_class("Silnik") == "motor"  # case/akcent-insensitive


def test_empty_tag_is_none():
    assert tag_to_class("") is None
    assert tag_to_class("   ") is None


def test_build_class_map_multiclass():
    recs = [_rec("p1", ["silnik", "rozłącznik", "silnik"]),
            _rec("p2", ["", "wolne hasło xyz"])]
    cmap, dist = build_class_map(recs)
    # 3 klasy: motor, disconnector (z palety) + slug wolnego hasla; pusty pominiety
    assert "motor" in cmap and "disconnector" in cmap
    assert "wolne_haslo_xyz" in cmap
    assert dist["motor"] == 2
    assert len(cmap) == 3


def test_min_count_buckets_rare_to_inny():
    recs = [_rec("p1", ["silnik", "silnik", "rzadka klasa"])]
    cmap, _ = build_class_map(recs, min_count=2)
    assert "motor" in cmap
    assert "inny" in cmap          # rzadka -> inny
    assert "rzadka_klasa" not in cmap


def test_resolve_class_id_skips_unknown():
    cmap = {"motor": 0, "inny": 1}
    assert resolve_class_id("silnik", cmap) == 0
    assert resolve_class_id("", cmap) is None       # bez tagu
    assert resolve_class_id("cos nowego", cmap) == 1  # -> inny


def test_min_count_excludes_when_not_bucketing():
    recs = [_rec("p1", ["silnik", "silnik", "rzadka klasa"])]
    cmap, _ = build_class_map(recs, min_count=2, bucket_rare=False)
    assert "motor" in cmap
    assert "inny" not in cmap            # brak smietnika
    assert "rzadka_klasa" not in cmap    # wykluczona
    assert len(cmap) == 1


def test_group_merge_from_config():
    # config/class-groups.yaml scala rodzine zaciskow w "zacisk"
    assert tag_to_class("złączka") == "zacisk"
    assert tag_to_class("terminal przyłączeniowy") == "zacisk"
    assert tag_to_class("terminale urządzenia") == "zacisk"
    # terminal_plc i kontenery wg configu osobno
    assert tag_to_class("terminal plc") == "terminal_plc"
    assert tag_to_class("silnik") == "motor"  # spoza grup -> bez zmian
