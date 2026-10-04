"""Robustness, offline: a failed run never damages the previous output and still reports its spend; names
never collide; bad inputs fail in plain words; URLs that are files are read as files; a broken model stops
being called."""

import http.server
import threading
from functools import partial

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from conftest import done, submit
from everymd import UnsupportedInput, convert, names, sidecar
from everymd.assemble import front_matter
from everymd.docling_step import Unit


def _tree(folder):
    return {p.relative_to(folder): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_a_failed_run_leaves_the_previous_output_untouched(inputs, tmp_path, monkeypatch):
    first = convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    before = _tree(first.markdown_path.parent)

    def broken(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(sidecar, "save_pages", broken)
    with pytest.raises(OSError, match="disk full") as caught:
        convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", llm_layer=False)
    assert _tree(first.markdown_path.parent) == before, "old output byte-identical"
    failed = tmp_path / ".report.failed" / "report.json"
    assert failed.is_file() and '"status": "failed"' in failed.read_text() and "disk full" in failed.read_text()
    assert any(".report.failed" in note for note in caught.value.__notes__)
    assert not list(tmp_path.glob(".report.partial-*")), "no half-written staging folder left behind"


def test_a_failed_run_still_reports_what_the_model_cost(inputs, tmp_path, monkeypatch, scripted):
    model = scripted(submit(1, "One"), done(), submit(2, "Two"), done())
    monkeypatch.setattr(sidecar, "save_pages", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):
        convert(inputs / "report.pdf", output_dir=tmp_path, resolution="low", model=model)
    text = (tmp_path / ".report.failed" / "report.json").read_text()
    assert '"edited_by": "copy-editor"' in text and '"estimated_cost_usd"' in text


def test_two_inputs_with_the_same_name_get_separate_folders(inputs, tmp_path):
    copy = tmp_path / "src" / "report.pdf"
    copy.parent.mkdir()
    copy.write_bytes((inputs / "report.pdf").read_bytes())
    first = convert(inputs / "report.pdf", output_dir=tmp_path / "out", resolution="low", llm_layer=False)
    second = convert(copy, output_dir=tmp_path / "out", resolution="low", llm_layer=False)
    again = convert(inputs / "report.pdf", output_dir=tmp_path / "out", resolution="low", llm_layer=False)
    assert first.markdown_path.parent.name == "report" == again.markdown_path.parent.name
    assert second.markdown_path.parent.name.startswith("report-") and first.markdown_path.exists()


def test_names_keep_letters_and_tell_url_queries_apart(tmp_path):
    assert names.output_name(_found(tmp_path / "報告 2026.pdf")) == "報告-2026"
    a = names.output_name(_url("https://en.wikipedia.org/w/index.php?title=Markdown&oldid=1"))
    b = names.output_name(_url("https://en.wikipedia.org/w/index.php?title=Docling&oldid=2"))
    assert a != b and a.startswith("en.wikipedia.org-index.php-")


def _found(path):
    from everymd.detect import Detected

    return Detected("pdf", str(path), path, "pdf", "extension")


def _url(url):
    from everymd.detect import Detected

    return Detected("url", url, None, "url", "url")


def test_bad_pdfs_fail_in_plain_words(tmp_path):
    from reportlab.pdfgen.canvas import Canvas

    locked = tmp_path / "locked.pdf"
    canvas = Canvas(str(locked), encrypt="secret")
    canvas.drawString(72, 720, "secret text")
    canvas.save()
    with pytest.raises(UnsupportedInput, match="password-protected"):
        convert(locked, output_dir=tmp_path, llm_layer=False)
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"%PDF-1.4\nthis is not really a pdf\n" * 50)
    with pytest.raises(UnsupportedInput, match="damaged or empty"):
        convert(broken, output_dir=tmp_path, llm_layer=False)
    for blank in (tmp_path / "blank.pdf", tmp_path / "blank.docx"):
        blank.write_bytes(b"")
        with pytest.raises(UnsupportedInput, match=r"is empty \(0 bytes\)"):
            convert(blank, output_dir=tmp_path, llm_layer=False)


class _Broken(GenericFakeChatModel):
    model_name: str = "gpt-6-luna"
    calls: int = 0

    def bind_tools(self, tools, **kwargs):
        return self

    def _get_ls_params(self, **kwargs):
        return {"ls_provider": "openai", "ls_model_name": self.model_name, "ls_model_type": "chat"}

    def _generate(self, *args, **kwargs):
        self.calls += 1
        raise RuntimeError("401 invalid api key")


def test_a_broken_model_stops_being_called(tmp_path):
    from everymd.agent import copy_edit

    model = _Broken(messages=iter([]))
    result = copy_edit([Unit(n, f"page {n}") for n in (1, 2, 3, 4)], batch_size=1, model=model)
    assert model.calls == 2, "two failed batches in a row, then no more calls"
    assert any("turned off after 2 failed batches" in note for note in result.notes)


def test_front_matter_escapes_characters_yaml_forbids():
    import yaml

    title = "Report\x9d 2026\x7f"
    assert yaml.safe_load(front_matter({"title": title}).strip("-\n"))["title"] == title


@pytest.fixture
def server(inputs, tmp_path):
    (tmp_path / "doc.pdf").write_bytes((inputs / "report.pdf").read_bytes())
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_a_url_that_is_a_pdf_is_read_as_a_pdf(server, tmp_path):
    result = convert(f"{server}/doc.pdf", output_dir=tmp_path / "out", resolution="low", llm_layer=False)
    assert result.report["detected_type"] == "pdf" and len(result.page_paths) == 2
    assert any("downloaded" in note for note in result.report["notes"])


def test_a_missing_url_is_an_error_not_a_document(server, tmp_path):
    from everymd.render import HTTPResponseError

    with pytest.raises(HTTPResponseError, match="404"):
        convert(f"{server}/missing", output_dir=tmp_path / "out", llm_layer=False)


def test_ebooks_skip_the_copy_editor_but_get_a_brief(inputs, tmp_path, scripted):
    from conftest import submit_brief

    model = scripted(submit_brief("# Brief: Booklet"), done())
    result = convert(inputs / "booklet.epub", output_dir=tmp_path, model=model)
    assert result.report["copy_editor_input"].startswith("skipped: no page images")
    assert all(tools == ["submit_brief"] for tools in model.seen_tools), "only the brief call was made"
    assert result.brief_path.is_file()


def test_an_interrupted_brief_keeps_the_conversion(inputs, tmp_path):
    from everymd import brief

    model = _Broken(messages=iter([]))
    made = brief.make([Unit(1, "text")], {}, model=model, title="T", kind="pdf", style="pages")
    assert made.markdown is None and made.notes[0].startswith("Brief stopped: RuntimeError: 401")
