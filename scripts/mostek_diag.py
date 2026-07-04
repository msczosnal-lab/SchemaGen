"""Diagnostyka orientacji mostka — dlaczego mostek_orient=null / tiles=0.

Uruchom lokalnie (PC ZW, z danymi):
    python scripts/mostek_diag.py
"""
from __future__ import annotations

from collections import Counter

from backend.paths import RAW, ROOT
from labeler.export import find_raw_image
from train.dataset_export import load_labeled_records, _load_page_images
from train.mostek_tiles import (
    expand_mostek_orientations_auto,
    load_exemplars,
    load_mostek_config,
)


def main() -> None:
    recs = load_labeled_records()
    print(f"rekordow z adnotacjami: {len(recs)}")

    # 1) rozklad tagow — ile jest 'mostek'
    tags = Counter()
    for r in recs:
        for b in r.bboxes:
            tags[b.tag.strip().lower()] += 1
    mostek_n = tags.get("mostek", 0)
    print(f"bboxow 'mostek' (dokladny tag): {mostek_n}")
    like = {t: n for t, n in tags.items() if "most" in t}
    print(f"tagi zawierajace 'most': {like}")

    # 2) obrazy stron — czy sie laduja
    mostek_recs = [r for r in recs if any(b.tag.strip().lower() == "mostek" for b in r.bboxes)]
    print(f"stron z mostkami: {len(mostek_recs)}")
    found = sum(1 for r in mostek_recs if find_raw_image(r, RAW) is not None)
    print(f"  z odnalezionym PNG (find_raw_image): {found}")
    imgs = _load_page_images(mostek_recs, RAW)
    print(f"  faktycznie wczytanych obrazow: {len(imgs)}  (RAW={RAW})")
    if mostek_recs and not imgs:
        r = mostek_recs[0]
        print(f"  [DIAG] przyklad: page_id={r.page_id} image_path={getattr(r,'image_path',None)} "
              f"find={find_raw_image(r, RAW)}")

    # 3) tryb + auto-przypisanie
    cfg = load_mostek_config()
    tpl = load_exemplars(ROOT / cfg.get("exemplar_dir", "data/mostek_exemplars"))
    print(f"eksemplarze (override): {'SA (8)' if tpl else 'brak -> tryb AUTO'}")
    if imgs:
        log = expand_mostek_orientations_auto(mostek_recs, imgs)
        print(f"AUTO log: {log.as_dict()}")
    else:
        print("[BLAD] brak wczytanych obrazow -> maybe_expand zwroci None (mostek_orient=null).")


if __name__ == "__main__":
    main()
