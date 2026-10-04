"""The brief, the index and single-image captions, offline: a scripted model stands in for gpt-6-luna.
These tests prove the wiring (what the brief call sees, where files are saved, when they are skipped),
not the quality of real writing."""

from conftest import done, submit, submit_brief
from everymd import brief, convert
from everymd.agent import PageEdit
from everymd.docling_step import Unit

BRIEF = "# Brief: Quarterly Field Report\n\n## What this is\nA field report.\n\n  odd   spacing kept  \n"
INDEX = "# Index: Quarterly Field Report\n\n| Pages | Section | What's there |\n|---|---|---|\n| 1-2 | Intro | x |"


def _brief_request(model) -> str:
    """The text of the human message the brief call received."""
    request = next(r for r in model.seen_requests if any("Write the brief" in str(m.content) for m in r))
    return next(m.content for m in request if m.type == "human")


def test_brief_call_sees_every_page_note_and_the_first_pages(scripted):
    units = [Unit(n, f"Docling page {n}") for n in (1, 2, 3)]
    units[0].headings, units[0].furniture = ["# Report", "## 1 Intro"], ["Field Log, April 2026"]
    edits = {
        1: PageEdit("Fixed page 1", [], "Where I am: # Intro", "Title page."),
        3: PageEdit("Fixed page 3", [], None, "Budget table."),
    }
    model = scripted(submit_brief(BRIEF), done())
    result = brief.make(units, edits, model=model, title="Report", kind="pdf", style="pages")
    text = _brief_request(model)
    assert ('<page number="1">\nPage note: Title page.\nContinuity note: Where I am: # Intro\n'
            "Headings starting on this page: # Report; ## 1 Intro\n</page>") in text
    assert '<page number="2">\nPage note: None\nContinuity note: None\nHeadings starting on this page: None\n</page>' in text
    assert "Running headers and footers seen in the document:\n- Field Log, April 2026" in text, "dates in headers reach the brief"
    assert "Page note: Budget table." in text
    assert "Fixed page 1" in text and "Docling page 2" in text, "the first two pages go in full"
    assert "Fixed page 3" not in text, "later pages are seen only through their notes"
    assert result.markdown == BRIEF and result.notes == []
    assert model.seen_tools and all(tools == ["submit_brief"] for tools in model.seen_tools)


def test_web_pages_get_an_outline_and_no_page_references(scripted):
    model = scripted(submit_brief("x"), done())
    brief.make([Unit(1, "text")], {}, model=model, title="Page", kind="html", style="web")
    system = model.seen_requests[0][0].content
    assert "(p. 3)" not in system and "page reference" not in system and "## Outline" in system
    assert "Also write the index" not in system, "web pages get no index"


def test_only_documents_with_pages_or_slides_are_asked_for_an_index():
    assert "Pages | Section | What's there" in brief.system_prompt("pages")
    assert "Slides | Section | What's there" in brief.system_prompt("slides")
    assert "Also write the index" not in brief.system_prompt("pageless")


def test_styles():
    assert brief.style_for("url", True, False) == "web"
    assert brief.style_for("html", False, False) == "web"
    assert brief.style_for("epub", False, False) == "pageless"
    assert brief.style_for("pptx", True, True) == "slides"
    assert brief.style_for("pdf", True, False) == "pages"


def test_no_submission_means_no_brief_and_a_note(scripted):
    model = scripted(done())
    result = brief.make([Unit(1, "text")], {}, model=model, title="T", kind="pdf", style="pages")
    assert result.markdown is None
    assert result.notes == ["The brief was not submitted by the model; no brief file was written."]


def test_convert_writes_the_brief_file_as_written(inputs, tmp_path, scripted):
    model = scripted(
        submit(1, "# One", page_note="Title page and readings."), done(),
        submit(2, "Two", page_note="Next steps."), done(),
        submit_brief(BRIEF, INDEX), done(),
    )
    result = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", batch_size=1, model=model)
    assert result.brief_path == result.markdown_path.parent / "report.brief.md"
    text = result.brief_path.read_text(encoding="utf-8")
    assert text.startswith("---\n") and 'full_document: "report.md"' in text and "ai_generated:" in text
    assert text.endswith("\n---\n\n" + BRIEF + "\n"), "the brief is saved exactly as the model wrote it"
    assert result.report["brief_file"] == "report.brief.md"
    index = result.index_path.read_text(encoding="utf-8")
    assert index.endswith("\n---\n\n" + INDEX + "\n") and 'ai_generated: "index written' in index
    assert result.report["index_file"] == "report.index.md"
    assert [p["page_note"] for p in result.report["pages"]] == ["Title page and readings.", "Next steps."]
    assert 'ai_page_note: "Next steps."' in result.page_paths[1].read_text(encoding="utf-8")


def test_single_images_get_no_brief(inputs, tmp_path, scripted):
    model = scripted(submit(1, "An invoice"), done())
    result = convert(inputs / "invoice.png", output_dir=tmp_path, resolution="low", model=model)
    assert result.brief_path is None and result.report["brief_file"] is None
    assert result.index_path is None and result.report["index_file"] is None
    assert all(tools == ["submit_page"] for tools in model.seen_tools), "no brief call was made"


def test_no_brief_without_the_ai_layer_and_old_ones_are_removed(inputs, tmp_path, scripted):
    model = scripted(submit(1, "One"), done(), submit(2, "Two"), done(), submit_brief(BRIEF, INDEX), done())
    first = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", model=model)
    assert first.brief_path.is_file() and first.index_path.is_file()
    second = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    assert second.brief_path is None and not first.brief_path.exists()
    assert second.index_path is None and not first.index_path.exists()


def test_single_image_caption_goes_in_the_front_matter_as_written(inputs, tmp_path, scripted):
    caption = "Invoice INV-0142 from Northwind to Contoso, total $1,284.50.  "
    model = scripted(submit(1, "An invoice", page_note=caption), done())
    result = convert(inputs / "invoice.png", output_dir=tmp_path, resolution="low", model=model)
    assert "This input is a single image" in model.seen_requests[0][0].content
    assert f'ai_caption: "{caption}"' in result.markdown.split("\n---\n", 1)[0]
    assert result.report["caption"] == caption


def test_documents_and_images_without_the_ai_get_no_caption(inputs, tmp_path, scripted):
    image = convert(inputs / "chart.png", output_dir=tmp_path, resolution="low", llm_layer=False)
    assert "ai_caption: null" in image.markdown and image.report["caption"] is None
    model = scripted(submit(1, "One"), done(), submit(2, "Two"), done(), submit_brief(BRIEF), done())
    pdf = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", model=model)
    assert "ai_caption" not in pdf.markdown and "This input is a single image" not in model.seen_requests[0][0].content


def test_pageless_briefs_never_ask_for_page_references(scripted):
    model = scripted(submit_brief("x"), done())
    brief.make([Unit(1, "a whole e-book")], {}, model=model, title="Book", kind="epub", style="pageless")
    system = model.seen_requests[0][0].content
    text = _brief_request(model)
    assert "(p. 3)" not in system and "One paragraph" in system
    assert "Pages:" not in text and '<page number="1">' not in text and "a whole e-book" in text


def test_brief_is_told_to_keep_conditions_exact_and_not_claim_absence():
    prompt = brief.system_prompt("pages")
    assert "keeping words like below, at least and up to" in prompt
    assert "never say that the document lacks something" in prompt
