"""Facts about a converted page that the copy-editor and the brief need besides its Markdown: the
column names of its tables, its running headers and footers, its headings, and the document's title."""

from __future__ import annotations

from docling_core.types.doc import ContentLayer, DocItemLabel, DoclingDocument
from docling_core.types.doc.document import SectionHeaderItem


def table_headers(doc: DoclingDocument, page_no: int) -> list[str]:
    """The column names of each table on the page, as `| a | b |`: the next page needs them when the
    table continues there without its header row."""
    found = []
    for table in doc.tables:
        if not table.prov or table.prov[0].page_no != page_no or not table.data.grid:
            continue
        rows = [row for row in table.data.grid if any(cell.column_header for cell in row)] or table.data.grid[:1]
        names = []
        for index in range(len(rows[0])):
            parts = []
            for row in rows:
                text = " ".join((row[index].text or "").split()) if index < len(row) else ""
                if text and text not in parts:
                    parts.append(text)
            names.append(" / ".join(parts))
        found.append("| " + " | ".join(names) + " |")
    return found


def furniture_text(doc: DoclingDocument, page_no: int) -> list[str]:
    """Running headers and footers on the page (not bare page numbers): they often hold the date,
    report number or organisation, which the brief needs even though the page text drops them."""
    found: list[str] = []
    for item, _ in doc.iterate_items(page_no=page_no, included_content_layers={ContentLayer.FURNITURE}):
        text = " ".join((getattr(item, "text", "") or "").split())
        if text and not text.isdigit() and text not in found:
            found.append(text)
    return found


def headings_on(doc: DoclingDocument, page_no: int | None) -> list[str]:
    """Headings that start on this page (or in the whole document when page_no is None), as Markdown."""
    found = []
    for item, _ in doc.iterate_items(page_no=page_no):
        label = getattr(item, "label", None)
        if label == DocItemLabel.TITLE:
            found.append(f"# {item.text}")
        elif isinstance(item, SectionHeaderItem):
            found.append(f"{'#' * (item.level + 1)} {item.text}")
    return found


class TitleFinder:
    """The document's title, else its first heading, found as pages arrive."""

    def __init__(self) -> None:
        self.title: str | None = None
        self.heading: str | None = None

    def see(self, doc: DoclingDocument) -> None:
        for item, _ in doc.iterate_items():
            label = getattr(item, "label", None)
            text = (getattr(item, "text", "") or "").strip()
            if label == DocItemLabel.TITLE and text and self.title is None:
                self.title = text
            elif label == DocItemLabel.SECTION_HEADER and text and self.heading is None:
                self.heading = text

    def result(self, fallback: str) -> str:
        return self.title or self.heading or fallback


def title_of(doc: DoclingDocument, fallback: str) -> str:
    finder = TitleFinder()
    finder.see(doc)
    return finder.result(fallback)
