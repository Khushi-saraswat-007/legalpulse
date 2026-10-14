"""Step 1: raw file (PDF / DOCX / TXT) -> plain text, one paragraph or line per row."""
from __future__ import annotations

import re
from pathlib import Path

from . import config
from .errors import EmptyDocumentError, ScannedPDFError, UnsupportedFormatError

SUPPORTED = {".pdf", ".docx", ".txt"}

# "Page 3", "Page 3 of 10", "3 of 10" on a line of their own = page furniture, not contract text.
# NLP-EX-09: also EDGAR print footers such as "Source: COMPANY, 8-K, 8/15/2019" (must end in a date)
_PAGE_FURNITURE = re.compile(
    r"^\s*(page\s+\d+(\s+of\s+\d+)?|\d+\s+of\s+\d+|source:\s.{3,150},\s*\d{1,2}/\d{1,2}/\d{4})\s*$", re.I)


def read_text(path: str | Path) -> str:
    """Return the text of a contract file. Raises a clear error instead of returning junk."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise UnsupportedFormatError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED))}")
    if ext == ".pdf":
        text = _read_pdf(path)
    elif ext == ".docx":
        text = _read_docx(path)
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
    text = clean_text(text)
    if not text.strip():
        raise EmptyDocumentError(f"No text found in {path.name}")
    return text


def clean_text(text: str) -> str:
    """Normalise whitespace and drop page numbers / footers."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    text = text.replace("’", "'").replace("‘", "'")
    lines = []
    for ln in text.split("\n"):
        ln = re.sub(r"[ \t]+", " ", ln).strip()
        if _PAGE_FURNITURE.match(ln):
            continue
        lines.append(ln)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _read_pdf(path: Path) -> str:
    import pdfplumber  # lazy import: only needed for PDFs

    pages = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
    except Exception as exc:  # corrupt / encrypted file
        raise EmptyDocumentError(f"Could not read PDF {path.name}: {exc}") from exc
    if not pages:
        raise EmptyDocumentError(f"PDF {path.name} has no pages")
    empty = sum(1 for p in pages if len(p.strip()) < config.MIN_CHARS_PER_PAGE)
    if empty / len(pages) > config.SCANNED_PAGE_FRACTION:
        raise ScannedPDFError(
            f"{path.name}: {empty}/{len(pages)} pages have no text layer. "
            "This looks like a scanned PDF; run OCR (e.g. ocrmypdf) first.")
    return _drop_repeated_lines("\n".join(pages), pages)


def _drop_repeated_lines(text: str, pages: list[str]) -> str:
    """Remove running headers/footers: identical short lines that appear on >= 3 pages."""
    if len(pages) < 3:
        return text
    counts: dict[str, int] = {}
    for p in pages:
        for ln in {l.strip() for l in p.split("\n") if l.strip()}:
            counts[ln] = counts.get(ln, 0) + 1
    repeated = {ln for ln, n in counts.items() if n >= 3 and len(ln) < 80 and not re.match(r"^\d", ln)}
    return "\n".join(l for l in text.split("\n") if l.strip() not in repeated)


def _read_docx(path: Path) -> str:
    """Paragraphs in order. Word auto-numbering (1., 1.1 ...) is not stored in the text, so we
    rebuild it from the numbering properties when the paragraph does not already start with a number."""
    import docx  # python-docx
    from docx.oxml.ns import qn

    try:
        document = docx.Document(str(path))
    except Exception as exc:
        raise EmptyDocumentError(f"Could not read DOCX {path.name}: {exc}") from exc

    counters: dict[int, int] = {}
    out = []
    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        numpr = para._p.find(f".//{qn('w:numPr')}")
        if numpr is not None and not re.match(r"^(\d+(\.\d+)*[.)]?|\(?[a-z]\)|\(?[ivx]+\))\s", text):
            ilvl_el = numpr.find(qn("w:ilvl"))
            ilvl = int(ilvl_el.get(qn("w:val"))) if ilvl_el is not None else 0
            counters[ilvl] = counters.get(ilvl, 0) + 1
            for deeper in [k for k in counters if k > ilvl]:
                del counters[deeper]
            label = ".".join(str(counters.get(i, 1)) for i in range(ilvl + 1))
            text = f"{label}. {text}" if ilvl == 0 else f"{label} {text}"
        out.append(text)
    return "\n".join(out)
