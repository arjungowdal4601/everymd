"""The full pipeline with the copy-editor off: every sample converts and the outputs keep their contract."""

import json
import re
from pathlib import Path

import pytest

from everymd import convert

SAMPLES = ["report.pdf", "scanned_report.pdf", "invoice.png", "chart.png", "proposal.docx",
           "board_deck.pptx", "page.html", "booklet.epub", "update.eml"]
PAGED = {"report.pdf": "page", "scanned_report.pdf": "page", "invoice.png": "page", "chart.png": "page",
         "proposal.docx": "page", "board_deck.pptx": "slide", "page.html": "page"}
REPORT_FIELDS = {
    "source", "detected_type", "detection", "rendered_to_pdf", "renderer", "resolution", "use_gpu", "device",
    "llm_layer", "copy_editor_input", "batch_size", "model", "reasoning_effort", "tokens", "estimated_cost_usd",
    "prices", "seconds", "pages", "page_files", "caption", "brief_file", "index_file", "notes", "versions",
}
IMAGE_LINK = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


@pytest.fixture(scope="session")
def results(inputs, tmp_path_factory):
    out = tmp_path_factory.mktemp("outputs")
    return {name: convert(inputs / name, output_dir=out, resolution="low", llm_layer=False) for name in SAMPLES}


@pytest.mark.parametrize("name", SAMPLES)
def test_front_matter_and_files(results, name):
    result = results[name]
    assert result.markdown.startswith("---\n")
    front = result.markdown.split("\n---\n", 1)[0]
    for key in ("title:", "source:", "detected_type:", "pages:", "converted_at:", "converter:",
                "resolution:", "ai_copy_edited: false", "ai_model: null"):
        assert key in front, key
    assert result.markdown_path.read_text(encoding="utf-8") == result.markdown
    sidecar = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert sidecar.get("schema_name") == "DoclingDocument"


@pytest.mark.parametrize("name", SAMPLES)
def test_report_fields(results, name):
    report = json.loads(results[name].report_path.read_text(encoding="utf-8"))
    assert REPORT_FIELDS <= report.keys()
    assert report["llm_layer"] is False and report["estimated_cost_usd"] == 0.0
    assert [page["edited_by"] for page in report["pages"]] == ["docling"] * len(report["pages"])


@pytest.mark.parametrize("name", PAGED)
def test_paged_inputs_have_anchors(results, name):
    assert f"<!-- {PAGED[name]}: 1 -->" in results[name].markdown


@pytest.mark.parametrize("name", ["booklet.epub", "update.eml"])
def test_pageless_inputs_have_no_anchors(results, name):
    assert "<!-- page:" not in results[name].markdown


@pytest.mark.parametrize("name", SAMPLES)
def test_image_links_resolve_to_files(results, name):
    result = results[name]
    for link in IMAGE_LINK.findall(result.markdown):
        assert link.startswith("images/"), link
        assert (result.markdown_path.parent / link).is_file(), link


def test_pictures_are_saved_for_the_report(results):
    assert IMAGE_LINK.findall(results["report.pdf"].markdown), "the chart should be linked as an image file"


@pytest.mark.parametrize("name", ["proposal.docx", "board_deck.pptx", "page.html"])
def test_office_and_web_files_are_rendered_to_pdf(results, name):
    assert results[name].report["rendered_to_pdf"] is True


def test_html_relative_images_load_when_printed(results):
    from PIL import Image

    result = results["page.html"]
    widths = [Image.open(result.markdown_path.parent / link).width for link in IMAGE_LINK.findall(result.markdown)]
    assert widths and max(widths) > 300, "the chart next to page.html should render, not a broken-image icon"


def test_speaker_notes_are_attached_to_their_slides(results):
    markdown = results["board_deck.pptx"].markdown
    slide_two = markdown.split("<!-- slide: 2 -->", 1)[1].split("<!-- slide: 3 -->", 1)[0]
    assert "**Speaker notes:** South is the only region that shrank" in slide_two
    assert "**Speaker notes:** Welcome the board" in markdown


def test_detected_type_reaches_front_matter(results):
    assert 'detected_type: "email"' in results["update.eml"].markdown
    assert 'detected_type: "pptx"' in results["board_deck.pptx"].markdown


def test_without_libreoffice_office_files_convert_natively(inputs, tmp_path, monkeypatch):
    monkeypatch.setattr("everymd.render.find_soffice", lambda: None)
    result = convert(inputs / "proposal.docx", output_dir=tmp_path, resolution="low", llm_layer=False)
    assert result.report["rendered_to_pdf"] is False
    assert any("LibreOffice is not installed" in note for note in result.report["notes"])
    assert "Budget" in result.markdown


def test_bad_arguments_are_rejected(inputs, tmp_path):
    with pytest.raises(ValueError, match="resolution"):
        convert(inputs / "report.pdf", output_dir=tmp_path, resolution="ultra", llm_layer=False)
    with pytest.raises(ValueError, match="batch_size"):
        convert(inputs / "report.pdf", output_dir=tmp_path, batch_size=0, llm_layer=False)


def test_outputs_land_in_a_folder_named_after_the_input(results):
    result = results["invoice.png"]
    assert result.markdown_path == result.markdown_path.parent / "invoice.md"
    assert Path(result.report_path).name == "report.json"


def test_relative_output_dir_keeps_images_in_one_place(inputs, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = convert(inputs / "report.pdf", output_dir="out", resolution="low", llm_layer=False)
    folder = result.markdown_path.parent
    assert not (folder / "out").exists(), "no nested copy of the output folder"
    uris = re.findall(r'"uri": "([^"]+)"', result.json_path.read_text(encoding="utf-8"))
    assert uris and all(uri.startswith("images/") and (folder / uri).is_file() for uri in uris)


def _body(path):
    """A page file's text after its front-matter."""
    return path.read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()


def test_one_page_file_per_page_with_the_same_text_as_the_full_file(results):
    result = results["report.pdf"]
    names = [path.name for path in result.page_paths]
    assert names == ["report.p0001.md", "report.p0002.md"]
    assert result.report["page_files"] == names
    for number, path in enumerate(result.page_paths, start=1):
        text = _body(path)
        assert text.startswith(f"<!-- page: {number} -->")
        assert text in result.markdown
    first = result.page_paths[0].read_text(encoding="utf-8")
    assert 'page: 1' in first and 'next: "report.p0002.md"' in first and "previous: null" in first
    assert 'full_document: "report.md"' in first


def test_slides_get_slide_files_with_their_speaker_notes(results):
    paths = results["board_deck.pptx"].page_paths
    assert [path.name for path in paths] == ["board_deck.s0001.md", "board_deck.s0002.md", "board_deck.s0003.md"]
    assert "**Speaker notes:** South is the only region that shrank" in _body(paths[1])


@pytest.mark.parametrize("name", ["booklet.epub", "update.eml"])
def test_pageless_inputs_get_no_page_files(results, name):
    assert results[name].page_paths == []


def test_rerun_removes_old_page_files(inputs, tmp_path):
    first = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    stale = first.markdown_path.parent / "report.p0099.md"  # e.g. from a longer earlier version of the file
    stale.write_text("old", encoding="utf-8")
    result = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    assert result.markdown_path.parent == first.markdown_path.parent, "its own folder is reused"
    assert not stale.exists()
    assert len(result.page_paths) == 2


def test_docling_reads_one_page_at_a_time(inputs, tmp_path, monkeypatch):
    from everymd import docling_step

    options, _ = docling_step.pdf_options("low", use_gpu=False)
    assert (options.ocr_batch_size, options.layout_batch_size, options.table_batch_size, options.queue_max_size) == (1, 1, 1, 1)
    calls, trims = [], []
    real = docling_step.convert_page

    def one_page(source, page_no, *args, **kwargs):
        calls.append(page_no)
        run = real(source, page_no, *args, **kwargs)
        assert sorted(run.doc.pages) == [page_no], "each call holds exactly one page"
        return run

    monkeypatch.setattr(docling_step, "convert_page", one_page)
    monkeypatch.setattr(docling_step, "release_memory", lambda: trims.append(1))
    convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    assert calls == [1, 2] and len(trims) == 2, "one Docling call per page, memory handed back after each"



def test_tables_get_a_screenshot_linked_under_them(results):
    from PIL import Image

    result = results["report.pdf"]
    folder = result.markdown_path.parent
    for number, path in enumerate(result.page_paths, start=1):
        link = f"![Table screenshot](images/table-p{number:04d}-1.png)"
        text = _body(path)
        assert link in text
        assert text.index("|") < text.index(link), "the link sits after the table"
        assert Image.open(folder / f"images/table-p{number:04d}-1.png").width > 100


def test_table_link_does_not_change_the_rest_of_the_page(inputs):
    from docling_core.types.doc import ImageRefMode

    from everymd import docling_step, tables

    doc, _, _ = docling_step.run(inputs / "report.pdf", "low", False)
    for page in sorted(doc.pages):
        # Simple tables, no footnotes: the same as Docling's own export, except underscores as printed.
        expected = doc.export_to_markdown(page_no=page, image_mode=ImageRefMode.PLACEHOLDER, escape_underscores=False)
        assert tables.page_markdown(doc, page, ImageRefMode.PLACEHOLDER, {}) == expected
