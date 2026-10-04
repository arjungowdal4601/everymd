"""Links printed on each page, recovered from the PDF's link annotations and placed into Docling's text.

Docling keeps a link only when it covers at least half of a whole text block, so links inside a
sentence (almost all links in Word files and web pages) never reach its Markdown, and the copy-editor
sees blue underlined words with no address. The PDF still has every link: a rectangle and a URL.
Every character whose centre lies inside a link rectangle takes that URL; consecutive characters with
the same URL form one anchor. Each anchor is then linked in Docling's Markdown for the page where it
occurs once (or, when it occurs several times, inside the text block the link sits on). Anchors that
can't be placed this way are handed to the copy-editor as a short list. This works on Docling's text,
before any model sees it.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

KEEP_SCHEMES = {"http", "https", "mailto", "ftp", "tel"}


@dataclass
class PageLink:
    text: str  # anchor words as printed; "" for a link on a picture
    url: str
    at: tuple[float, float] | None = None  # centre of the first character (PDF points, bottom-left origin)


@dataclass
class LinkStats:
    found: int = 0
    placed: int = 0
    for_editor: int = 0
    counts: dict = field(default_factory=dict)


def _inside(box, rect) -> bool:
    x, y = (box.l + box.r) / 2, (box.t + box.b) / 2
    return min(rect.l, rect.r) <= x <= max(rect.l, rect.r) and min(rect.t, rect.b) <= y <= max(rect.t, rect.b)


def _new_line(last, box) -> bool:
    """The next character moved back to the left and down by more than half a line."""
    height = max(abs(last.t - last.b), abs(box.t - box.b))
    return box.l < last.l and abs((box.t + box.b) / 2 - (last.t + last.b) / 2) > height / 2


def _anchors(chars, rects) -> list[PageLink]:
    links: list[PageLink] = []
    run_url, text, last, first = None, "", None, None

    def close():
        if run_url is not None and text.strip():
            links.append(PageLink(" ".join(text.split()), run_url, first))

    for cell in chars:
        char = cell.text
        box = cell.rect.to_bounding_box()
        if not char.strip():
            if run_url is not None:
                text += " "
            continue
        url = next((u for r, u in rects if _inside(box, r)), None)
        if url != run_url:
            close()
            run_url, text, last = url, "", None
            first = ((box.l + box.r) / 2, (box.t + box.b) / 2)
        if url is None:
            continue
        if last is not None and _new_line(last, box):
            text = text.rstrip() + ("" if text.rstrip().endswith("-") else " ")
        text += char
        last = box
    close()
    return [PageLink(link.text.rstrip(",.;:"), link.url, link.at) for link in links]


def page_links(pdf: Path) -> dict[int, list[PageLink]]:
    """Web, mail and phone links per 1-based page number. Internal jumps and file links are left out.
    Pages are read one at a time with only their characters, and let go straight after."""
    from docling_core.types.doc import BoundingBox, CoordOrigin
    from docling_parse.pdf_parser import ContentConfig, ContentLevel, DoclingPdfParser

    skip = ContentLevel.SKIP
    only_chars = ContentConfig(word_cells_content_level=skip, line_cells_content_level=skip,
                               shapes_content_level=skip, bitmaps_content_level=skip, include_bitmap_bytes=False)
    result: dict[int, list[PageLink]] = {}
    doc = DoclingPdfParser(loglevel="fatal").load(path_or_stream=str(pdf), content_config=only_chars)
    try:
        for page_no in range(1, doc.number_of_pages() + 1):
            try:
                page = doc.get_page(page_no, content_config=only_chars)
                # characters are relative to the crop box, link rectangles are in raw PDF space
                ox, oy = page.dimension.crop_bbox.l, page.dimension.crop_bbox.b
                rects = []
                for link in page.hyperlinks:
                    if link.uri is None or urlparse(str(link.uri)).scheme.lower() not in KEEP_SCHEMES:
                        continue
                    r = link.rect.to_bounding_box()
                    box = BoundingBox(l=r.l - ox, r=r.r - ox, t=r.t - oy, b=r.b - oy, coord_origin=CoordOrigin.BOTTOMLEFT)
                    rects.append((box, str(link.uri)))
                if rects:
                    links = _anchors(page.char_cells, rects)
                    used = {link.url for link in links}
                    links += [PageLink("", url) for _, url in rects if url not in used]  # links on pictures
                    result[page_no] = links
            except Exception:  # one page that can't be decoded loses only its own links
                continue
            finally:
                doc.unload_pages((page_no, page_no + 1))
    finally:
        doc.unload()
    return result


# Between two words: some whitespace, but at most one line break, so a link never crosses a blank line.
_GAP = r"(?:[^\S\n]+\n?[^\S\n]*|\n[^\S\n]*)"
_LINKS = re.compile(r"!?\[[^\]\n]*\]\([^)\n]*\)|<a\s[^>]*>.*?</a>", re.S)
_TAG = re.compile(r"<[^>]*>")


def _pattern(anchor: str) -> re.Pattern:
    """The anchor's words in order, tolerant of a line break, Docling's `\\_` escape and a dropped hyphen."""
    words = [re.escape(w).replace("_", r"\\?_").replace(r"\-", r"-?") for w in anchor.split()]
    return re.compile(r"(?<![\w\[])" + _GAP.join(words) + r"(?!\w)")


def _covered(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(a <= start and end <= b for a, b in spans)


def _html_line(md: str, pos: int) -> bool:
    """The position is inside an HTML block (Docling writes spanning tables as HTML)."""
    return md[md.rfind("\n", 0, pos) + 1 : pos].lstrip().startswith("<")


def _block_text(doc, page_no: int, at: tuple[float, float]) -> str:
    """The text of Docling's item on this page whose box contains the point."""
    from docling_core.types.doc import CoordOrigin

    height = doc.pages[page_no].size.height
    x, y = at
    for item, _ in doc.iterate_items(page_no=page_no):
        for prov in getattr(item, "prov", None) or []:
            if prov.page_no != page_no:
                continue
            box = prov.bbox if prov.bbox.coord_origin == CoordOrigin.BOTTOMLEFT else prov.bbox.to_bottom_left_origin(height)
            if box.l - 1 <= x <= box.r + 1 and box.b - 1 <= y <= box.t + 1:
                return getattr(item, "text", "") or ""
    return ""


def place(doc, page_no: int, md: str, links: list[PageLink], stats: LinkStats) -> tuple[str, list[PageLink]]:
    """Link each anchor in Docling's Markdown for this page; return the Markdown and the links left over."""
    edits: list[tuple[int, int, str]] = []
    left: list[PageLink] = []
    taken: list[tuple[int, int]] = []
    linked = [(m.start(), m.end()) for m in _LINKS.finditer(md)]
    tags = [(m.start(), m.end()) for m in _TAG.finditer(md)]
    for link in links:
        stats.found += 1
        if not link.text:
            left.append(link)
            continue
        regex = _pattern(link.text)
        if any(link.url in md[a:b] and regex.search(md[a:b].replace("[", " ", 1)) for a, b in linked):
            continue  # Docling already linked these words to this address
        spans = [(m.start(), m.end()) for m in regex.finditer(md)]
        spans = [s for s in spans if not any(a < s[1] and s[0] < b for a, b in taken + tags)]
        free = [s for s in spans if not _covered(linked, *s)]
        choice = free[0] if len(free) == 1 else None
        if choice is None and len(free) > 1 and link.at is not None:
            block = _block_text(doc, page_no, link.at)
            head = block[:40].strip()
            start = md.find(head) if head else -1
            if start < 0 and head:
                start = md.find(head.replace("_", "\\_"))
            inside = [s for s in free if start >= 0 and start <= s[0] <= start + len(block) + 40]
            choice = inside[0] if inside else None
        if choice is None:
            left.append(link)
            continue
        taken.append(choice)
        words = md[choice[0]:choice[1]]
        if _html_line(md, choice[0]):
            edits.append((choice[0], choice[1], f'<a href="{html.escape(link.url, quote=True)}">{words}</a>'))
        else:
            edits.append((choice[0], choice[1], f"[{words}]({link.url})"))
        stats.placed += 1
    for start, end, new in sorted(edits, reverse=True):
        md = md[:start] + new + md[end:]
    stats.for_editor += len(left)
    return md, left


def as_context(links: list[PageLink]) -> str:
    """One line per link for the copy-editor: words -> address."""
    seen, lines = set(), []
    for link in links:
        if (link.text, link.url) in seen:
            continue
        seen.add((link.text, link.url))
        lines.append(f'- "{link.text}" -> {link.url}' if link.text else f"- (a picture) -> {link.url}")
    return "\n".join(lines)
