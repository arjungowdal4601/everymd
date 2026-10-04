"""Regressions found by the adversarial review of the page-streaming change, offline."""

import json
import os

import pytest

from everymd import convert, names, publish
from everymd.assemble import front_matter
from everymd.detect import Detected
from everymd.headings import Headings, numbering_level


def _found(path):
    return Detected("pdf", str(path), path, "pdf", "extension")


def test_a_folder_that_is_not_everymd_output_is_never_replaced(inputs, tmp_path):
    (tmp_path / "report").mkdir()
    (tmp_path / "report" / "precious.html").write_text("keep me")
    result = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    assert (tmp_path / "report" / "precious.html").read_text() == "keep me"
    assert result.markdown_path.parent.name.startswith("report-")


def test_older_outputs_without_source_id_are_matched_by_source(inputs, tmp_path):
    legacy = tmp_path / "report"
    legacy.mkdir()
    (legacy / "report.json").write_text(json.dumps({"source": str(inputs / "report.pdf"), "versions": {}}))
    assert names.belongs_to(legacy, _found(inputs / "report.pdf"))
    assert not names.belongs_to(legacy, _found(tmp_path / "other" / "report.pdf"))


def test_published_folders_keep_normal_permissions(inputs, tmp_path):
    result = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    umask = os.umask(0)
    os.umask(umask)
    assert os.stat(result.markdown_path.parent).st_mode & 0o777 == 0o777 & ~umask, "not private (0700)"


def test_a_killed_run_is_kept_as_failed_by_the_next_run(tmp_path):
    stale = tmp_path / ".report.partial-dead0000"
    stale.mkdir()
    (stale / ".lock").write_text("")
    (stale / "report.json").write_text(json.dumps({"status": "running", "estimated_cost_usd": 0.12}))
    stage = publish.Stage(tmp_path, "report", owns=lambda folder: True, fallback="report-x")
    failed = json.loads((tmp_path / ".report.failed" / "report.json").read_text())
    assert failed["status"] == "killed" and failed["estimated_cost_usd"] == 0.12
    assert stage.dir.exists() and not stale.exists()


def test_long_names_fit_the_file_name_limit(tmp_path):
    name = names.output_name(_found(tmp_path / ("報告" * 60 + ".pdf")))
    assert len((f".{name}-12345678.partial-12345678").encode()) <= 255


def test_url_names_are_decoded():
    found = Detected("url", "https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC", None, "url", "url")
    assert names.output_name(found) == "ja.wikipedia.org-日本"


def test_numbering_and_bookmark_matching():
    assert numbering_level("2.0 Scope") == 1 and numbering_level("2.1.0 Data") == 2
    from docling_core.types.doc import DoclingDocument, ProvenanceItem, BoundingBox, Size
    from everymd.headings import Bookmark

    doc = DoclingDocument(name="d")
    doc.add_page(page_no=3, size=Size(width=600, height=800))
    prov = ProvenanceItem(page_no=3, bbox=BoundingBox(l=0, t=10, r=10, b=0), charspan=(0, 1))
    for text in ("3 Methods", "Data", "Metadata standards"):
        doc.add_heading(text=text, level=1, prov=prov)
    Headings([Bookmark("Methods", 3, 1), Bookmark("Metadata standards", 3, 2)]).apply(doc, 3)
    levels = {item.text: item.level for item in doc.texts}
    assert levels == {"3 Methods": 1, "Data": 1, "Metadata standards": 2}


def test_front_matter_handles_noncharacters():
    import yaml

    title = "x￾y￿"
    assert yaml.safe_load(front_matter({"title": title}).strip("-\n"))["title"] == title


def test_spanning_tables_print_their_caption_once():
    from docling_core.types.doc import DocItemLabel, DoclingDocument, ImageRefMode, TableCell, TableData
    from everymd import tables

    doc = DoclingDocument(name="t")
    cells = [TableCell(text="Group", start_row_offset_idx=0, end_row_offset_idx=1, start_col_offset_idx=0,
                       end_col_offset_idx=2, col_span=2, column_header=True),
             TableCell(text="a", start_row_offset_idx=1, end_row_offset_idx=2, start_col_offset_idx=0, end_col_offset_idx=1),
             TableCell(text="b", start_row_offset_idx=1, end_row_offset_idx=2, start_col_offset_idx=1, end_col_offset_idx=2)]
    table = doc.add_table(data=TableData(num_rows=2, num_cols=2, table_cells=cells))
    table.captions.append(doc.add_text(label=DocItemLabel.CAPTION, text="Table 1: Caption").get_ref())
    table.footnotes.append(doc.add_text(label=DocItemLabel.FOOTNOTE, text="1 A footnote.").get_ref())
    out = tables.page_markdown(doc, None, ImageRefMode.PLACEHOLDER, {})
    assert out.count("Table 1: Caption") == 1 and out.count("A footnote") == 1 and 'colspan="2"' in out


def test_a_blank_page_is_not_a_scan(tmp_path):
    from reportlab.pdfgen.canvas import Canvas
    from everymd import scan

    pdf = tmp_path / "with-blank.pdf"
    canvas = Canvas(str(pdf))
    canvas.drawString(72, 720, "Text with a link")
    canvas.showPage()
    canvas.showPage()  # blank page
    canvas.save()
    assert scan.pages_without_text(pdf) == set()


def test_web_pages_without_pages_get_a_pageless_brief_message(scripted):
    from conftest import done, submit_brief
    from everymd import brief
    from everymd.docling_step import Unit

    model = scripted(submit_brief("x"), done())
    unit = Unit(1, "# Guide\n\n## Setup\n\ntext")
    unit.headings = ["# Guide", "## Setup"]
    brief.make([unit], {}, model=model, title="Guide", kind="html", style="web", has_pages=False)
    text = next(m.content for m in model.seen_requests[0] if m.type == "human")
    assert "Pages:" not in text and "Headings Docling found:\n# Guide\n## Setup" in text
