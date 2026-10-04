"""Assemble the final Markdown: YAML front-matter, invisible anchors, pages, speaker notes, AI labels."""

from __future__ import annotations

import json
import re

from .agent import PageEdit
from .docling_step import Unit


# JSON leaves DEL, the C1 control characters, lone surrogates and U+FFFE/U+FFFF raw, but YAML forbids
# them (they turn up in badly decoded PDF titles). Writing them as \u escapes keeps the loaded value identical.
_YAML_UNSAFE = re.compile("[\x7f-\x9f\ud800-\udfff\ufffe\uffff]")


def front_matter(fields: dict) -> str:
    """YAML front-matter. Values are written as JSON, which is valid YAML and needs no escaping rules."""
    lines = ["---"]
    for key, value in fields.items():
        encoded = _YAML_UNSAFE.sub(lambda m: f"\\u{ord(m.group()):04x}", json.dumps(value, ensure_ascii=False))
        lines.append(f"{key}: {encoded}")
    lines.append("---")
    return "\n".join(lines)


def _comment_safe(text: str) -> str:
    """Only stop the text from closing its HTML comment early; everything else stays as written."""
    return text.replace("-->", "->")


def ai_label(edit: PageEdit, docling_markdown: str) -> str | None:
    """The invisible label for a page the copy-editor changed, or None if it changed nothing."""
    if edit.changes:
        return "<!-- ai-edited: " + "; ".join(_comment_safe(change) for change in edit.changes) + " -->"
    if edit.markdown != docling_markdown:
        return "<!-- ai-edited: revised by the copy-editor (no change list given) -->"
    return None


def block(unit: Unit, edit: PageEdit | None, *, anchor: str | None, notes: dict[int, str]) -> str:
    """One page's Markdown block: its anchor, its text (the copy-editor's exactly as written, else
    Docling's), its speaker notes and the invisible AI label. The complete document and the page files
    are both built from these blocks, so a page file is exactly that page's text in the complete file.
    `anchor` is "page", "slide", or None for documents without pages."""
    parts: list[str] = []
    if anchor:
        parts.append(f"<!-- {anchor}: {unit.number} -->")
    parts.append(edit.markdown if edit else unit.markdown.strip())
    if unit.number in notes:
        parts.append(f"**Speaker notes:** {notes[unit.number]}")
    label = ai_label(edit, unit.markdown) if edit else None
    if label:
        parts.append(label)
    return "\n\n".join(part for part in parts if part)


def blocks(units: list[Unit], edits: dict[int, PageEdit], *, anchor: str | None, notes: dict[int, str]) -> list[str]:
    return [block(unit, edits.get(unit.number), anchor=anchor, notes=notes) for unit in units]
