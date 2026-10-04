"""The copy-editor harness, offline: a scripted model stands in for gpt-6-luna. These tests prove the
wiring (batching, tools, fallbacks, labels), not the quality of a real model's edits."""

import pytest
from PIL import Image

from conftest import done, submit
from everymd import agent, convert, models
from everymd.assemble import ai_label, blocks
from everymd.docling_step import Unit


def body(units, edits, **kwargs) -> str:
    """The complete document's text: every page block, in order."""
    return "\n\n".join(b for b in blocks(units, edits, **kwargs) if b) + "\n"


def pages(*numbers: int) -> list[Unit]:
    return [Unit(n, f"Docling text for page {n}") for n in numbers]


def batches_seen(model) -> list[str]:
    """The 'Copy-edit page N of M.' line of every agent invocation, in order."""
    first_lines = []
    for request in model.seen_requests:
        human = next(m for m in request if m.type == "human")
        first_lines.append(human.content[0]["text"])
    return list(dict.fromkeys(first_lines))


@pytest.mark.parametrize(
    ("batch_size", "groups", "lines"),
    [
        (1, ["1", "2", "3"], ["Copy-edit page 1 of 3.", "Copy-edit page 2 of 3.", "Copy-edit page 3 of 3."]),
        (2, ["1, 2", "3"], ["Copy-edit pages 1, 2 of 3.", "Copy-edit page 3 of 3."]),
        (None, ["1, 2, 3"], ["Copy-edit pages 1, 2, 3 of 3."]),
    ],
)
def test_batch_size_groups_pages(scripted, batch_size, groups, lines):
    turns = []
    for group in groups:
        turns += [submit(int(n), f"Fixed {n}") for n in group.split(", ")] + [done()]
    model = scripted(*turns)
    result = agent.copy_edit(pages(1, 2, 3), batch_size=batch_size, model=model)
    assert batches_seen(model) == lines
    assert {n: edit.markdown for n, edit in result.pages.items()} == {1: "Fixed 1", 2: "Fixed 2", 3: "Fixed 3"}
    assert result.notes == []


def test_unsubmitted_page_keeps_docling_output(scripted):
    model = scripted(submit(1, "Fixed 1", ["fixed a heading"]), done())
    units = pages(1, 2)
    result = agent.copy_edit(units, batch_size=None, model=model)
    assert list(result.pages) == [1]
    assert result.notes == ["Page 2 was not submitted by the copy-editor; kept Docling's output."]
    text = body(units, result.pages, anchor="page", notes={})
    assert "Fixed 1" in text and "Docling text for page 2" in text
    assert "<!-- ai-edited: fixed a heading -->" in text


def test_model_markdown_is_kept_exactly_as_written():
    written = "\n\n  # Heading with spaces around it  \n\n" + "x" * 50_000 + "\n\n\n"
    text = body(pages(1), {1: agent.PageEdit(written, [])}, anchor="page", notes={})
    assert written in text


def test_only_submit_page_is_visible_to_the_model(scripted):
    model = scripted(submit(1, "x"), done())
    agent.copy_edit(pages(1), batch_size=1, model=model)
    assert model.seen_tools and all(tools == ["submit_page"] for tools in model.seen_tools)


def test_page_outside_the_batch_is_refused(scripted):
    model = scripted(submit(7, "wrong page"), submit(1, "right page"), done())
    result = agent.copy_edit(pages(1), batch_size=1, model=model)
    assert result.pages[1].markdown == "right page" and 7 not in result.pages
    tool_replies = [m.content for m in model.seen_requests[-2] if m.type == "tool"]
    assert any("not in this batch" in reply for reply in tool_replies)


def test_next_batch_gets_the_end_of_the_previous_page(scripted):
    model = scripted(submit(1, "First page ends with this sentence."), done(), submit(2, "Second"), done())
    agent.copy_edit(pages(1, 2), batch_size=1, model=model)
    second_call = model.seen_requests[2]
    texts = [block["text"] for m in second_call if m.type == "human" for block in m.content if block["type"] == "text"]
    assert any("<previous>" in t and "First page ends with this sentence." in t for t in texts)


def test_page_images_are_sent_downscaled_with_high_detail(scripted):
    unit = Unit(1, "text", Image.new("RGB", (3000, 1500), "white"))
    model = scripted(submit(1, "text"), done())
    agent.copy_edit([unit], batch_size=1, model=model)
    human = next(m for m in model.seen_requests[0] if m.type == "human")
    images = [block for block in human.content if block["type"] == "image_url"]
    assert len(images) == 1 and images[0]["image_url"]["detail"] == "high"
    assert images[0]["image_url"]["url"].startswith("data:image/png;base64,")
    assert max(Image.open(__import__("io").BytesIO(
        __import__("base64").b64decode(images[0]["image_url"]["url"].split(",", 1)[1]))).size) <= 2400


def test_text_only_mode_sends_no_images_and_says_so(scripted):
    unit = Unit(1, "text", Image.new("RGB", (100, 100), "white"))
    model = scripted(submit(1, "text"), done())
    agent.copy_edit([unit], batch_size=1, model=model, text_only=True)
    system, human = model.seen_requests[0][0], next(m for m in model.seen_requests[0] if m.type == "human")
    assert "whose image you can't see" in system.content and "Never change, add, remove" in system.content
    assert not [block for block in human.content if block["type"] == "image_url"]


def test_ai_labels():
    assert ai_label(agent.PageEdit("same", []), "same") is None
    assert ai_label(agent.PageEdit("new", ["a --> b", "two\nlines"]), "old") == "<!-- ai-edited: a -> b; two\nlines -->"
    assert "no change list given" in ai_label(agent.PageEdit("new", []), "old")


def test_missing_key_gives_a_clear_error(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("EVERYMD_MODEL", raising=False)
    monkeypatch.delenv("EVERYMD_BASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        models.build(None)


def test_convert_with_the_copy_editor_end_to_end(inputs, tmp_path, scripted):
    model = scripted(
        submit(1, "# Quarterly Field Report\n\nFixed page one.", ["promoted the title"]), done(),
        submit(2, "## 3. Next steps\n\nFixed page two.", []), done(),
    )
    result = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", batch_size=1, model=model)
    assert "ai_copy_edited: true" in result.markdown and 'ai_model: "gpt-6-luna"' in result.markdown
    assert "<!-- ai-edited: promoted the title -->" in result.markdown
    assert "Fixed page two." in result.markdown
    assert [p["edited_by"] for p in result.report["pages"]] == ["copy-editor", "copy-editor"]
    assert result.report["copy_editor_input"] == "page images"
    assert result.report["estimated_cost_usd"] == 0.0


def _human_texts(request) -> list[str]:
    human = next(m for m in request if m.type == "human")
    return [block["text"] for block in human.content if block["type"] == "text"]


def test_continuity_note_is_carried_to_the_next_page_as_written(scripted):
    note = "Where I am: # 1 Readings\nStill open: table, columns: Site | Date | Moisture (%) (started p. 1)\nWatch for: None"
    model = scripted(submit(1, "Page one", note=note), done(), submit(2, "Page two", note="Where I am: # 1 Readings"), done())
    result = agent.copy_edit(pages(1, 2), batch_size=1, model=model)
    second = _human_texts(model.seen_requests[2])
    assert f'<continuity_note written_after_page="1">\n{note}\n</continuity_note>' in second
    assert result.pages[1].continuity_note == note
    assert not any("continuity_note" in text for text in _human_texts(model.seen_requests[0]))


def test_a_missing_note_carries_the_last_one_with_its_page_number(scripted):
    model = scripted(submit(1, "one", note="Still open: list, last item 3"), done(), submit(2, "two"), done(), submit(3, "three"), done())
    agent.copy_edit(pages(1, 2, 3), batch_size=1, model=model)
    assert any('written_after_page="1"' in text for text in _human_texts(model.seen_requests[4]))


def test_prompt_asks_to_repeat_table_headers_not_drop_them():
    assert "drop a repeated header row" not in agent.SYSTEM_PROMPT
    assert "continued from page N" in agent.SYSTEM_PROMPT


def test_continuity_notes_reach_the_report_and_page_files(inputs, tmp_path, scripted):
    model = scripted(submit(1, "# One", note="Where I am: # 1 Intro"), done(), submit(2, "Two", note="Where I am: # 4 Budget"), done())
    result = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", batch_size=1, model=model)
    assert [page["continuity_note"] for page in result.report["pages"]] == ["Where I am: # 1 Intro", "Where I am: # 4 Budget"]
    assert 'ai_continuity_note: "Where I am: # 1 Intro"' in result.page_paths[0].read_text(encoding="utf-8")

