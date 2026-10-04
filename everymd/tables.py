"""Docling's Markdown for one page, with what its default export leaves out or flattens:
- a screenshot of each table, cut from the page image and linked right under the table;
- tables with merged cells or several header rows as HTML (a Markdown table can't hold them, and
  Docling's own Markdown flattens them into one header row);
- footnotes Docling attached to a table or picture (its Markdown export drops them);
- underscores as printed (Docling escapes every `_` as `\\_` by default).
"""

from __future__ import annotations

from pathlib import Path

from docling_core.transforms.serializer.markdown import (
    MarkdownDocSerializer,
    MarkdownParams,
    MarkdownPictureSerializer,
    MarkdownTableSerializer,
)
from docling_core.transforms.serializer.html import HTMLDocSerializer, HTMLParams
from docling_core.types.doc import ContentLayer, DocItemLabel, DoclingDocument, ImageRefMode, TableItem


def save_images(doc: DoclingDocument, images_dir: Path) -> dict[str, tuple[str, object]]:
    """Save images/table-p0003-1.png for every table Docling found on a page with a rendered image.
    Returns {table ref: (link relative to the output folder, PIL image)}."""
    shots: dict[str, tuple[str, object]] = {}
    per_page: dict[int, int] = {}
    for table in doc.tables:
        if not table.prov:
            continue
        page_no = table.prov[0].page_no
        image = table.get_image(doc)  # crop of the page image; None when the page has no image
        if image is None:
            continue
        per_page[page_no] = per_page.get(page_no, 0) + 1
        name = f"table-p{page_no:04d}-{per_page[page_no]}.png"
        image.save(images_dir / name)
        shots[table.self_ref] = (f"images/{name}", image)
    return shots


def needs_html(table: TableItem) -> bool:
    """Merged cells or more than one header row: a Markdown table would lose the structure."""
    cells = table.data.table_cells
    if any(cell.row_span > 1 or cell.col_span > 1 for cell in cells):
        return True
    header_rows = {cell.start_row_offset_idx for cell in cells if cell.column_header}
    return len(header_rows) > 1


def page_markdown(
    doc: DoclingDocument,
    page_no: int | None,
    image_mode: ImageRefMode,
    links: dict[str, str],
    *,
    furniture: bool = False,
) -> str:
    """Docling's Markdown for one page (or the whole document when page_no is None)."""
    layers = {ContentLayer.BODY, ContentLayer.FURNITURE} if furniture else {ContentLayer.BODY}
    options: dict = {"image_mode": image_mode, "escape_underscores": False, "layers": layers}
    if page_no is not None:
        options["pages"] = {page_no}
    params = MarkdownParams(**options)
    serializer = MarkdownDocSerializer(
        doc=doc,
        table_serializer=_TableSerializer(links=links),
        picture_serializer=_PictureSerializer(),
        params=params,
    )
    return serializer.serialize().text


def _with_footnotes(text: str, item, doc_serializer, **kwargs) -> str:
    notes = doc_serializer.serialize_footnotes(item=item, **kwargs).text
    return f"{text}\n\n{notes}" if text and notes else text or notes


class _TableSerializer(MarkdownTableSerializer):
    def __init__(self, links: dict[str, str]):
        super().__init__()
        self.links = links

    def serialize(self, *, item, doc_serializer, doc, **kwargs):
        result = super().serialize(item=item, doc_serializer=doc_serializer, doc=doc, **kwargs)
        if kwargs.get("_nested_in_table") or not result.text:
            return result
        text = result.text
        if needs_html(item):
            # Docling's own export_to_html ignores add_caption=False: serialize the table alone, so the
            # caption (above, as Markdown) and the footnotes (below) are each written once.
            caption = doc_serializer.serialize_captions(item=item, **kwargs).text
            params = HTMLParams(labels=HTMLParams().labels - {DocItemLabel.CAPTION, DocItemLabel.FOOTNOTE},
                                layers=set(doc_serializer.params.layers))
            html = HTMLDocSerializer(doc=doc, params=params).serialize(item=item).text
            text = f"{caption}\n\n{html}" if caption else html
        text = _with_footnotes(text, item, doc_serializer, **kwargs)
        link = self.links.get(item.self_ref)
        if link:
            text = f"{text}\n\n![Table screenshot]({link})"
        result.text = text
        return result


class _PictureSerializer(MarkdownPictureSerializer):
    def serialize(self, *, item, doc_serializer, doc, **kwargs):
        result = super().serialize(item=item, doc_serializer=doc_serializer, doc=doc, **kwargs)
        result.text = _with_footnotes(result.text, item, doc_serializer, **kwargs)
        return result
