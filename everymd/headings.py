"""Heading levels for the whole document, applied one page at a time.

Docling's PDF path gives every heading level 1, and its own hierarchy stage ranks the levels it finds
within one conversion, so a page converted on its own would always start at level 1. Here the levels
come from the whole document instead:
1. the PDF's outline (bookmarks). Word, PowerPoint and printed web pages carry their headings there,
   and many PDFs do too. A heading on the page that matches a bookmark on the same page takes the
   bookmark's level, counted over the whole outline;
2. otherwise the heading's dotted numbering: `2.1` or `B.4` is one level below a top-level section.
Headings with neither keep Docling's level 1 (`##`). The title stays Docling's title (`#`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from docling_core.types.doc import DoclingDocument
from docling_core.types.doc.document import SectionHeaderItem

MATCH_THRESHOLD = 0.8
MAX_LEVEL = 5  # level 5 is `######`, Markdown's deepest heading
_LEADING_NUMBER = re.compile(r"^\s*(?:[A-Z]|\d+)(?:\.\d+)*\.?\s+")
_DOTTED = re.compile(r"^\s*(?:[A-Z]|\d{1,3})((?:\.\d{1,3})+)\.?(?:\s|$)")


@dataclass(frozen=True)
class Bookmark:
    title: str
    page: int | None  # 1-based, None when the bookmark has no page destination
    level: int  # 1 = top level of the document's outline


def read_outline(pdf: Path) -> list[Bookmark]:
    """The PDF's bookmarks with document-wide levels. A single top entry is the document's title
    (a web page's h1, a report's cover title), so the entries below it start at level 1."""
    import pypdfium2 as pdfium

    try:
        document = pdfium.PdfDocument(str(pdf))
    except Exception:  # unreadable or protected: no outline, numbering still works
        return []
    try:
        raw = []
        for bookmark in document.get_toc():
            title = (bookmark.get_title() or "").strip()
            if not title:
                continue
            dest = bookmark.get_dest()
            index = dest.get_index() if dest is not None else None
            raw.append((title, index + 1 if index is not None else None, bookmark.level))
    except Exception:
        return []
    finally:
        document.close()
    if not raw:
        return []
    top = min(level for _, _, level in raw)
    if sum(1 for _, _, level in raw if level == top) == 1 and len(raw) > 1:
        raw = [(title, page, level) for title, page, level in raw if level != top]
    depths = sorted({level for _, _, level in raw})
    rank = {depth: i + 1 for i, depth in enumerate(depths)}
    return [Bookmark(title, page, rank[level]) for title, page, level in raw]


def _norm(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "").lower()).strip()
    return re.sub(r"^[\W_]+|[\W_]+$", "", text)


def _similarity(heading: str, title: str) -> float:
    """Fuzzy match between a detected heading and a bookmark title, with and without the leading
    number (bookmarks often leave it out), counting containment as a strong match."""
    left = {_norm(heading), _norm(_LEADING_NUMBER.sub("", heading, count=1))} - {""}
    right = {_norm(title), _norm(_LEADING_NUMBER.sub("", title, count=1))} - {""}
    best = 0.0
    for a in left:
        for b in right:
            best = max(best, SequenceMatcher(None, a, b).ratio())
            if len(a) >= 4 and len(b) >= 4 and (_contains_words(a, b) or _contains_words(b, a)):
                best = max(best, 0.92)  # bookmarks are often a shortened heading
    return best


def _contains_words(short: str, long: str) -> bool:
    """`short` appears in `long` as whole words ("data" is not inside "metadata standards")."""
    a, b = short.split(), long.split()
    return any(b[i : i + len(a)] == a for i in range(len(b) - len(a) + 1))


def numbering_level(text: str) -> int | None:
    """`2.1 Sampling` -> 2, `B.4 Results` -> 2, `3.2.1 x` -> 3; None without dotted numbering."""
    match = _DOTTED.match(text or "")
    if match is None:
        return None
    parts = match.group(1).split(".")[1:]
    while parts and not parts[-1].strip("0"):  # 2.0 Scope is a top-level section, 2.1.0 a subsection
        parts.pop()
    return min(1 + len(parts), MAX_LEVEL)


class Headings:
    """Assigns heading levels page by page from document-wide signals."""

    def __init__(self, outline: list[Bookmark]):
        self.outline = outline

    def apply(self, doc: DoclingDocument, page_no: int) -> None:
        """Set the level of every heading on this page, in place, before it is exported."""
        candidates = [b for b in self.outline if b.page in (page_no, None)]
        found = [
            item for item in doc.texts
            if isinstance(item, SectionHeaderItem) and (not item.prov or item.prov[0].page_no == page_no)
        ]
        # Best matches first, so an exact heading always gets its own bookmark.
        pairs = []
        for h, item in enumerate(found):
            for b, bookmark in enumerate(candidates):
                threshold = MATCH_THRESHOLD if bookmark.page is not None else MATCH_THRESHOLD + 0.1
                score = _similarity(item.text, bookmark.title)
                if score >= threshold:
                    pairs.append((-score, h, b))
        levels: dict[int, int] = {}
        used: set[int] = set()
        for _, h, b in sorted(pairs):
            if h not in levels and b not in used:
                levels[h] = candidates[b].level
                used.add(b)
        for h, item in enumerate(found):
            level = levels.get(h, numbering_level(item.text))
            if level is not None:
                item.level = max(1, min(level, MAX_LEVEL))
