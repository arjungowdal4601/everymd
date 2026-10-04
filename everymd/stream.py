"""Read a document one page at a time, like a person: Docling converts a page, the copy-editor edits it
(`batch_size` pages at a time), its page file is written and its images are let go, then the next page.
Memory stays flat however long the document is (the eval's 78-page scan, which ran out of memory at
5.45 GB when converted whole, completes at 3.3-3.5 GB, 4.3 GB at its densest page). Documents without
pages are read in one go.

Converting one page per call also keeps each page's text on its own page: a whole-document conversion
joins a paragraph cut by a page break into one item and exports it on the first page, which is where the
duplicated text at page breaks came from.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from docling_core.types.doc import DoclingDocument

from . import docling_step, headings, links, models, pages
from .agent import CopyEditor, PageEdit
from .assemble import block
from .detect import SLIDE_KINDS, WEB_KINDS
from .docling_step import TitleFinder, Unit
from .prepare import Prepared

log = logging.getLogger(__name__)


@dataclass
class Reading:
    """Everything read so far; the conversion builds its outputs from this when the last page is done."""

    name: str
    kind: str
    anchor: str | None = None  # "page", "slide", or None for documents without pages
    units: list[Unit] = field(default_factory=list)  # text only once a page is finished
    notes: list[str] = field(default_factory=list)
    device: str = "cpu"
    title: str = ""
    page_paths: list[Path] = field(default_factory=list)
    titles_used: set[str] = field(default_factory=set)  # the titles page files were written with
    light_docs: list[DoclingDocument] = field(default_factory=list)
    whole_doc: DoclingDocument | None = None
    editor: CopyEditor | None = None
    copy_editor_input: str | None = None
    link_stats: links.LinkStats = field(default_factory=links.LinkStats)

    @property
    def edits(self) -> dict[int, PageEdit]:
        return self.editor.pages if self.editor else {}

    @property
    def usage(self) -> dict:
        return self.editor.usage if self.editor else {}


def read(
    prepared: Prepared,
    out: Path,
    *,
    name: str,
    llm,
    resolution: str,
    use_gpu: bool,
    batch_size: int | None,
    shared: dict,
    reading: Reading,
    on_batch: Callable[[Reading], None] = lambda reading: None,
) -> Reading:
    """Fill `reading` (passed in so the caller still has what was spent if this raises)."""
    if prepared.has_pages:
        _read_pages(prepared, out, name, llm, resolution, use_gpu, batch_size, shared, reading, on_batch)
    else:
        _read_whole(prepared, out, name, resolution, use_gpu, shared, reading, llm)
    return reading


def _read_pages(prepared, out, name, llm, resolution, use_gpu, batch_size, shared, reading, on_batch) -> None:
    source = Path(prepared.source)
    is_pdf = source.suffix.lower() == ".pdf"
    scan_pages = prepared.scan.pages_without_text
    scan_mode = bool(scan_pages)
    reading.anchor = "slide" if prepared.kind in SLIDE_KINDS else "page"
    levels = headings.Headings(headings.read_outline(source) if is_pdf else [])
    printed_links = _links(source, reading) if is_pdf else {}  # scanned pages simply have none
    finder = TitleFinder()
    pending: list[Unit] = []
    total = 1
    page_no = 0
    while page_no < total:
        page_no += 1
        started = time.monotonic()
        run = docling_step.convert_page(source, page_no, resolution, use_gpu, scan_mode)
        total, reading.device = run.page_count, run.device
        reading.notes += run.notes
        levels.apply(run.doc, page_no)
        finder.see(run.doc)
        unit, light, notes = docling_step.export_page(run.doc, page_no, out, crops=page_no in scan_pages)
        unit.scanned = page_no in scan_pages
        del run
        reading.notes += notes
        unit.markdown, unit.links = links.place(light, page_no, unit.markdown, printed_links.get(page_no, []), reading.link_stats)
        reading.light_docs.append(light)
        reading.units.append(unit)
        reading.title = finder.result("")
        if page_no == 1 and llm is not None:
            reading.editor = _editor(llm, prepared, total, reading.title, scan_mode)
            reading.copy_editor_input = "text only" if reading.editor.text_only else "page images"
        pending.append(unit)
        if reading.editor is None or page_no == total or (batch_size and len(pending) >= batch_size):
            if reading.editor is not None:
                reading.editor.title = reading.title
                reading.editor.edit(pending)
            _finish(pending, out, name, total, shared, reading, prepared)
            pending = []
            on_batch(reading)
        docling_step.release_memory()
        log.info("%s: page %d of %d read in %.1f s", name, page_no, total, time.monotonic() - started)


def _editor(llm, prepared: Prepared, total: int, title: str, scan_mode: bool) -> CopyEditor:
    return CopyEditor(
        llm,
        total=total,
        title=title,
        slides=prepared.kind in SLIDE_KINDS,
        single_image=prepared.kind == "image" and total == 1,
        scan=scan_mode,
        web=prepared.kind in WEB_KINDS,
        text_only=not models.sees_images(),
    )


def _links(source: Path, reading: Reading) -> dict:
    try:
        return links.page_links(source)
    except Exception as exc:  # links are extra; never fail the conversion over them
        reading.notes.append(f"Could not read the PDF's links ({type(exc).__name__}: {exc}).")
        return {}


def _finish(batch: list[Unit], out: Path, name: str, total: int, shared: dict, reading: Reading, prepared: Prepared) -> None:
    """Write the batch's page files and let go of its images."""
    numbers = list(range(1, total + 1))
    title = reading.title or name
    reading.titles_used.add(title)
    fields = {**shared, "title": title}
    for unit in batch:
        edit = reading.edits.get(unit.number)
        text = block(unit, edit, anchor=reading.anchor, notes=prepared.speaker_notes)
        reading.page_paths.append(
            pages.write_page(out, name, unit.number, text, edit, anchor=reading.anchor, numbers=numbers, shared=fields)
        )
        unit.image, unit.table_images = None, []


def _read_whole(prepared: Prepared, out: Path, name: str, resolution: str, use_gpu: bool, shared: dict, reading: Reading, llm) -> None:
    """E-books, emails and Office/web files that could not be printed: Docling reads the text straight
    from the file, so there is no page image to check it against and the copy-editor is not used."""
    doc, reading.device, notes = docling_step.run(prepared.source, resolution, use_gpu)
    reading.notes += notes
    units, notes = docling_step.export_whole(doc, out, furniture=prepared.kind == "epub")
    reading.notes += notes
    reading.units, reading.whole_doc = units, doc
    reading.title = docling_step.title_of(doc, "")
    if llm is not None:
        reading.copy_editor_input = "skipped: no page images (Docling's text comes straight from the file)"
    if doc.pages:
        reading.anchor = "slide" if prepared.kind in SLIDE_KINDS else "page"
        title = reading.title or name
        reading.titles_used.add(title)
        fields = {**shared, "title": title}
        entries = [(u.number, block(u, None, anchor=reading.anchor, notes=prepared.speaker_notes), None) for u in units]
        reading.page_paths = pages.write(out, name, entries, anchor=reading.anchor, shared=fields)
    for unit in units:
        unit.image = None
