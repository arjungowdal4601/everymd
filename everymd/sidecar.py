"""The lossless Docling JSON next to the Markdown (`name.docling.json`).

Pages are converted one at a time, so the sidecar is joined from per-page documents that no longer
hold page bitmaps (their pictures are already saved as files under images/). docling-core's
`concatenate` renumbers pages from 1 and closes gaps (docling#3890), so the original page numbers are
put back afterwards, the same way Docling's own VLM pipeline does.
"""

from __future__ import annotations

from pathlib import Path

from docling_core.types.doc import ContentLayer, DoclingDocument, ImageRefMode
from docling_core.types.doc.document import DocItem


def light_copy(doc: DoclingDocument) -> DoclingDocument:
    """Drop the pixels a per-page document still holds (page bitmap, decoded pictures)."""
    for page in doc.pages.values():
        page.image = None
    for picture in doc.pictures:
        if picture.image is not None:
            picture.image._pil = None  # the file under images/ (picture.image.uri) is the copy kept
    return doc


def _restore_page_numbers(doc: DoclingDocument, original: list[int]) -> DoclingDocument:
    mapping = dict(zip(sorted(doc.pages), original))
    if all(old == new for old, new in mapping.items()):
        return doc
    doc.pages = {mapping[n]: page for n, page in doc.pages.items()}
    for number, page in doc.pages.items():
        page.page_no = number
    for item, _ in doc.iterate_items(traverse_pictures=True, included_content_layers=set(ContentLayer)):
        if isinstance(item, DocItem):
            for prov in item.prov:
                prov.page_no = mapping.get(prov.page_no, prov.page_no)
    return doc


def save_pages(docs: list[DoclingDocument], path: Path, name: str) -> None:
    """Join per-page documents (in page order) into one sidecar with the original page numbers."""
    if not docs:
        return
    merged = docs[0] if len(docs) == 1 else DoclingDocument.concatenate(docs)
    merged = _restore_page_numbers(merged, [n for doc in docs for n in sorted(doc.pages)])
    merged.name = name
    merged.origin = next((doc.origin for doc in docs if doc.origin is not None), None)  # concatenate drops it
    merged.save_as_json(path, image_mode=ImageRefMode.PLACEHOLDER)


def save_whole(doc: DoclingDocument, path: Path) -> None:
    """A document converted in one go (no pages, or read natively). Pictures point into images/ next
    to it; page renders are left out. Docling resolves a relative artifacts folder against the JSON's
    own folder, so pass just "images"."""
    page_images = {number: page.image for number, page in doc.pages.items()}
    try:
        for page in doc.pages.values():
            page.image = None
        doc.save_as_json(path, artifacts_dir=Path("images"), image_mode=ImageRefMode.REFERENCED)
    finally:
        for number, image in page_images.items():
            doc.pages[number].image = image
