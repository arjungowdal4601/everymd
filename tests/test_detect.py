"""Detection: content first, extension second, clear rejections."""

import shutil

import pytest

from everymd import UnsupportedInput, detect

EXPECTED = {
    "report.pdf": "pdf",
    "scanned_report.pdf": "pdf",
    "invoice.png": "image",
    "chart.png": "image",
    "proposal.docx": "docx",
    "board_deck.pptx": "pptx",
    "page.html": "html",
    "booklet.epub": "epub",
    "update.eml": "email",
}


@pytest.mark.parametrize(("name", "kind"), EXPECTED.items())
def test_each_sample_is_detected(inputs, name, kind):
    assert detect(inputs / name).kind == kind


def test_url_is_recognised_by_scheme():
    found = detect("https://en.wikipedia.org/wiki/Markdown")
    assert (found.kind, found.path, found.method) == ("url", None, "url")


def test_misnamed_pdf_is_still_detected_as_pdf(inputs, tmp_path):
    misnamed = tmp_path / "notes.txt"
    shutil.copyfile(inputs / "report.pdf", misnamed)
    found = detect(misnamed)
    assert (found.kind, found.method) == ("pdf", "magika")


def test_xlsx_is_rejected(tmp_path):
    from openpyxl import Workbook

    book = Workbook()
    book.active.append(["Region", "Q1", "Q2"])
    book.active.append(["North", 120, 150])
    path = tmp_path / "numbers.xlsx"
    book.save(path)
    with pytest.raises(UnsupportedInput, match="not supported in this version"):
        detect(path)


def test_csv_is_rejected(tmp_path):
    path = tmp_path / "numbers.csv"
    path.write_text("region,q1,q2\n" + "North,120,150\nSouth,95,88\nEast,130,162\nWest,80,97\n" * 5)
    with pytest.raises(UnsupportedInput, match="not supported in this version"):
        detect(path)


def test_folder_is_rejected(tmp_path):
    with pytest.raises(UnsupportedInput, match="one file at a time"):
        detect(tmp_path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        detect(tmp_path / "missing.pdf")
