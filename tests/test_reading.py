"""Reading page by page, offline (Docling only, no model): each page holds exactly its own text, links and
heading levels come from the PDF, sideways scans are turned upright, and the sidecar keeps page numbers."""

import json

import pytest
from PIL import Image

from everymd import convert, headings, render, scan
from everymd.docling_step import Unit

GUIDE = """<html><head><title>Guide</title></head><body>
<h1>Field guide</h1>
<h2>Setup</h2><p>Read the <a href="https://example.com/setup/">setup notes</a> before the first visit.</p>
<h3>Details</h3><p>Write to <a href="mailto:team@example.com">the team</a> with questions.</p>
<h2>Usage</h2><p>Plain text with no link.</p>
</body></html>"""


def _body(path) -> str:
    return path.read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()


def test_text_cut_by_a_page_break_stays_on_its_own_page(inputs, tmp_path):
    result = convert(inputs / "continuity.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    page2, page3 = _body(result.page_paths[1]), _body(result.page_paths[2])
    assert page2.endswith("irriga-"), "page 2 ends exactly where the page ends"
    assert "schedule changed" not in page2, "no text from page 3 on page 2"
    assert page3.split("\n\n", 1)[1].startswith("tion schedule changed in May"), "page 3 starts with its own fragment"


def test_sidecar_keeps_every_page_and_its_number(inputs, tmp_path):
    result = convert(inputs / "continuity.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    sidecar = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert sorted(int(n) for n in sidecar["pages"]) == [1, 2, 3, 4, 5]
    provs = {p["page_no"] for item in sidecar["texts"] for p in item.get("prov", [])}
    assert provs == {1, 2, 3, 4, 5}


@pytest.fixture(scope="module")
def guide(tmp_path_factory):
    folder = tmp_path_factory.mktemp("guide")
    page = folder / "guide.html"
    page.write_text(GUIDE, encoding="utf-8")
    return convert(page, output_dir=folder / "out", resolution="low", llm_layer=False)


def test_links_inside_sentences_come_from_the_pdf(guide):
    assert "[setup notes](https://example.com/setup/)" in guide.markdown, "exact URL, trailing slash kept"
    assert "[the team](mailto:team@example.com)" in guide.markdown
    assert "](#)" not in guide.markdown
    assert guide.report["links"]["placed"] == 2


def test_heading_levels_come_from_the_outline(guide):
    lines = [line for line in guide.markdown.splitlines() if line.startswith("#")]
    assert "## Setup" in lines and "### Details" in lines and "## Usage" in lines, lines


def test_numbering_gives_subsection_levels():
    assert headings.numbering_level("2.1 Sampling") == 2
    assert headings.numbering_level("B.4 Results") == 2
    assert headings.numbering_level("3.2.1 Data") == 3
    assert headings.numbering_level("2 Methods") is None
    assert headings.numbering_level("A Comprehensive Study") is None


def test_outline_levels_are_counted_over_the_whole_document(tmp_path):
    pdf = tmp_path / "guide.pdf"
    (tmp_path / "guide.html").write_text(GUIDE, encoding="utf-8")
    render.web_to_pdf((tmp_path / "guide.html").as_uri(), pdf)
    levels = {b.title: b.level for b in headings.read_outline(pdf)}
    assert levels == {"Setup": 1, "Details": 2, "Usage": 1}, "the single top entry is the title"


def _scanned_page(inputs, tmp_path, turn: int):
    """Page 1 of the report as a picture (no text layer), turned `turn` degrees counter-clockwise."""
    import pypdfium2 as pdfium

    image = pdfium.PdfDocument(str(inputs / "report.pdf"))[0].render(scale=2).to_pil()
    path = tmp_path / f"scan-{turn}.pdf"
    image.rotate(turn, expand=True).save(path, resolution=144)
    return path


def test_a_sideways_scan_is_turned_upright(inputs, tmp_path):
    pdf = _scanned_page(inputs, tmp_path, 90)
    upright, info = scan.upright_pdf(pdf, tmp_path)
    assert info.pages_without_text == {1} and info.rotated == {1: 90}
    import pypdfium2 as pdfium

    page = pdfium.PdfDocument(str(upright))[0]
    assert scan.orientation(page.render(scale=2).to_pil(), scan._engine()) == 0, "upright after turning"


def test_upright_scans_and_born_digital_pages_are_left_alone(inputs, tmp_path):
    upright, info = scan.upright_pdf(_scanned_page(inputs, tmp_path, 0), tmp_path)
    assert info.pages_without_text == {1} and info.rotated == {}
    same, info = scan.upright_pdf(inputs / "report.pdf", tmp_path)
    assert same == inputs / "report.pdf" and info.pages_without_text == set()


def test_scanned_pages_send_sharp_table_crops(inputs, tmp_path):
    result = convert(_scanned_page(inputs, tmp_path, 0), output_dir=tmp_path / "out", resolution="high", llm_layer=False)
    assert result.report["scanned_pages"] == [1]
    shot = Image.open(result.markdown_path.parent / "images" / "table-p0001-1.png")
    assert shot.width > 900, "table screenshots on scanned pages are cut at 300 DPI"


def test_copy_editor_message_carries_headers_links_and_crops(scripted):
    from conftest import done, submit
    from everymd.agent import CopyEditor
    from everymd.links import PageLink

    unit = Unit(2, "Docling text", Image.new("RGB", (400, 600), "white"))
    unit.furniture, unit.links = ["NIST IR 8425 September 2022"], [PageLink("Technical Report", "https://gov.uk/tr")]
    unit.table_images = [Image.new("RGB", (300, 200), "white")]
    model = scripted(submit(2, "Docling text"), done())
    editor = CopyEditor(model, total=26, title="QLoRA", scan=True)
    editor.edit([unit])
    human = next(m for m in model.seen_requests[0] if m.type == "human")
    texts = [b["text"] for b in human.content if b["type"] == "text"]
    assert texts[0] == "Copy-edit page 2 of 26 of “QLoRA”."
    assert any("NIST IR 8425 September 2022" in t for t in texts)
    assert any('"Technical Report" -> https://gov.uk/tr' in t for t in texts)
    assert sum(1 for b in human.content if b["type"] == "image_url") == 2, "page image plus one table crop"
    assert any("the spelling is the author's" in t for t in texts), "words from the text layer are not respelled"
    assert "sharper images of their tables" in model.seen_requests[0][0].content


def test_the_next_page_gets_the_previous_tables_column_names(scripted):
    from conftest import done, submit
    from everymd.agent import CopyEditor

    first = Unit(1, "| Site | Date |\n|---|---|\n| S01 | x |", Image.new("RGB", (100, 100), "white"))
    first.table_headers = ["| Site | Date | Moisture (%) | Battery (V) |"]
    second = Unit(2, "| S29 | y |", Image.new("RGB", (100, 100), "white"))
    model = scripted(submit(1, "one"), done(), submit(2, "two"), done())
    editor = CopyEditor(model, total=2)
    editor.edit([first])
    editor.edit([second])
    human = next(m for m in model.seen_requests[2] if m.type == "human")
    texts = [b["text"] for b in human.content if b["type"] == "text"]
    assert any("Column names of the tables on page 1" in t and "| Site | Date | Moisture (%) | Battery (V) |" in t for t in texts)
