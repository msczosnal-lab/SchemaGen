"""One-off inventory — delete after run."""
import json
import re
import sys
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

base = Path(__file__).parent
items = []

for p in sorted(base.iterdir()):
    if p.name.startswith("_"):
        continue
    if p.suffix.lower() == ".pdf":
        doc = fitz.open(p)
        text_len = sum(len(doc[i].get_text()) for i in range(min(3, len(doc))))
        m = re.match(r"(\d+)_A_(\d+)_PL", p.stem)
        items.append(
            {
                "file": p.name,
                "project_code": m.group(2) if m else None,
                "year_prefix": m.group(1) if m else None,
                "pages": len(doc),
                "size_kb": p.stat().st_size // 1024,
                "content_hint": "text/vector" if text_len > 500 else "scan_or_sparse",
            }
        )
        doc.close()
    elif p.suffix.lower() == ".lnk":
        data = p.read_bytes()
        paths = re.findall(rb"C:\\Users\\[^\x00\x01-\x1f]{10,220}\.pdf", data)
        target = paths[0].decode("ascii", errors="replace") if paths else None
        items.append(
            {
                "file": p.name,
                "type": "shortcut",
                "target_pdf": target,
                "note": "Skrót OneDrive (PC ZW) — skopiuj PDF lokalnie, jeśli potrzebny",
            }
        )

manifest = {
    "path": "sync/sources/",
    "pdf_count": sum(1 for i in items if i.get("pages")),
    "total_pages": sum(i.get("pages", 0) for i in items),
    "items": items,
}

out = base / "MANIFEST.json"
out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(manifest, indent=2, ensure_ascii=False))
