"""Ingest — PDF/obraz do PNG."""

from __future__ import annotations

from pathlib import Path

from backend.paths import RAW, ensure_data_dirs


def pdf_to_png(pdf_path: str | Path, output_dir: str | Path | None = None, dpi: int = 200) -> list[Path]:
    """Konwertuje PDF na PNG (jedna strona = jeden plik)."""
    import fitz  # PyMuPDF

    pdf_path = Path(pdf_path)
    out = Path(output_dir) if output_dir else RAW
    ensure_data_dirs()
    out.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    results: list[Path] = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi)
        dest = out / f"{pdf_path.stem}_p{i:03d}.png"
        pix.save(dest)
        results.append(dest)
    doc.close()
    return results


def normalize_image_path(input_path: str | Path) -> Path:
    """Kopiuje obraz do data/raw/ jesli lezy poza projektem."""
    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Brak pliku: {src}")
    if src.suffix.lower() == ".pdf":
        pages = pdf_to_png(src)
        return pages[0]
    if src.parent.resolve() == RAW.resolve():
        return src
    ensure_data_dirs()
    dest = RAW / src.name
    if src.resolve() != dest.resolve():
        dest.write_bytes(src.read_bytes())
    return dest
