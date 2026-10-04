"""Page files: one Markdown file per page (or slide), next to the complete document. Each is written as
soon as its page is finished, so a long document shows its progress on disk."""

from __future__ import annotations

from pathlib import Path

from .agent import PageEdit
from .assemble import front_matter


def file_name(name: str, number: int, anchor: str, last: int) -> str:
    """report.p0001.md for pages, deck.s0001.md for slides; wider numbers past 9,999 pages."""
    letter = "s" if anchor == "slide" else "p"
    return f"{name}.{letter}{number:0{max(4, len(str(last)))}d}.md"


def write_page(
    out: Path,
    name: str,
    number: int,
    block: str,
    edit: PageEdit | None,
    *,
    anchor: str,
    numbers: list[int],
    shared: dict,
) -> Path:
    """Write one page file. `block` is the page's text exactly as it appears in the complete document;
    the front-matter links the pages together and keeps the copy-editor's notes as written.
    `numbers` are all the page numbers of the document, in order."""
    last = numbers[-1]
    position = numbers.index(number)
    previous = numbers[position - 1] if position else None
    following = numbers[position + 1] if position + 1 < len(numbers) else None
    fields = {
        **shared,
        anchor: number,
        f"{anchor}s": len(numbers),
        "full_document": f"{name}.md",
        "previous": file_name(name, previous, anchor, last) if previous is not None else None,
        "next": file_name(name, following, anchor, last) if following is not None else None,
        "ai_copy_edited": edit is not None,
        "ai_continuity_note": edit.continuity_note if edit else None,
        "ai_page_note": edit.page_note if edit else None,
    }
    path = out / file_name(name, number, anchor, last)
    path.write_text(front_matter(fields) + "\n\n" + block + "\n", encoding="utf-8")
    return path


def write(
    out: Path,
    name: str,
    pages: list[tuple[int, str, PageEdit | None]],
    *,
    anchor: str,
    shared: dict,
) -> list[Path]:
    """Write every page file from (number, block, copy-editor edit or None) entries."""
    numbers = [number for number, _, _ in pages]
    return [
        write_page(out, name, number, block, edit, anchor=anchor, numbers=numbers, shared=shared)
        for number, block, edit in pages
    ]
