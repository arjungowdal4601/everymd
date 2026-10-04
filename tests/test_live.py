"""Opt-in live test with the real copy-editor (gpt-6-luna). Costs a fraction of a cent.

    docker compose run --rm -e EVERYMD_LIVE=1 app pytest tests/test_live.py
"""

import os
import re

import pytest

from everymd import convert

pytestmark = pytest.mark.skipif(
    os.environ.get("EVERYMD_LIVE") != "1" or not os.environ.get("OPENAI_API_KEY"),
    reason="live test: set EVERYMD_LIVE=1 and OPENAI_API_KEY",
)

MISREAD_FORMULA = re.compile(r"\$\$\s*q\s*=")  # Docling's OCR reads the scanned "g =" as "q ="


def test_scanned_formula_comes_out_right(inputs, tmp_path, monkeypatch):
    monkeypatch.setenv("EVERYMD_REASONING_EFFORT", "low")  # owner's rule: test runs use low reasoning
    # Docling used to read the scanned "g =" as "q ="; since scans are read at 300 DPI it reads it right, and
    # the copy-editor must not break it.
    edited = convert(inputs / "scanned_report.pdf", output_dir=tmp_path, resolution="high", llm_layer=True, batch_size=1)
    assert not MISREAD_FORMULA.search(edited.markdown)
    assert re.search(r"\bg\s*=", edited.markdown)
    assert "+24.6%" in edited.markdown  # the table survives the edit
    assert edited.report["model"] == "gpt-6-luna" and edited.report["reasoning_effort"] == "low"
    assert edited.report["estimated_cost_usd"] > 0


def test_copy_editor_keeps_pages_connected(inputs, tmp_path, monkeypatch):
    monkeypatch.setenv("EVERYMD_REASONING_EFFORT", "low")
    result = convert(inputs / "continuity.pdf", output_dir=tmp_path, resolution="high", llm_layer=True, batch_size=1)
    page = {n: path.read_text(encoding="utf-8").split("\n---\n", 1)[1] for n, path in enumerate(result.page_paths, start=1)}
    assert "Moisture" in page[2] and "continued from page 1" in page[2], "page 2's table gets its column names"
    # Each page holds exactly its own text (decision 0014): the sentence cut by the page break is not
    # completed on page 2 and not repeated on page 3.
    assert "schedule changed" not in page[2], "page 2 doesn't borrow page 3's words"
    assert page[3].count("schedule changed in May") == 1
    assert re.search(r"^\s*4\.", page[4], re.MULTILINE), "the list keeps counting at 4"
    assert all(p["continuity_note"] for p in result.report["pages"][:-1]), "every page but the last writes a note"
    assert all(p["page_note"] for p in result.report["pages"]), "every page writes a page note"
    assert result.brief_path is not None and result.brief_path.is_file(), "the brief is written"
    assert result.index_path is not None and result.index_path.is_file(), "the index is written"


def test_single_image_gets_a_caption(inputs, tmp_path, monkeypatch):
    monkeypatch.setenv("EVERYMD_REASONING_EFFORT", "low")
    result = convert(inputs / "chart.png", output_dir=tmp_path, resolution="low", llm_layer=True)
    assert result.report["caption"], "the copy-editor writes a caption for a single image"
    assert "ai_caption:" in result.markdown.split("\n---\n", 1)[0]
