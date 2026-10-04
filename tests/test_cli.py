"""Offline CLI contracts: forwarding and parsing, without model calls."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from everymd import __main__ as cli


@pytest.fixture
def conversion(monkeypatch):
    calls = []
    result = SimpleNamespace(
        markdown_path=Path("outputs/report/report.md"),
        json_path=Path("outputs/report/report.docling.json"),
        report_path=Path("outputs/report/report.json"),
        brief_path=None, index_path=None,
        page_paths=[Path("outputs/report/report.p0001.md")],
        report={"estimated_cost_usd": 0},
    )

    def fake(source, **kwargs):
        calls.append((source, kwargs))
        return result

    monkeypatch.setattr(cli, "convert", fake)
    return calls, result


def test_defaults_and_output_paths(conversion, capsys):
    calls, _ = conversion
    assert cli.main(["report.pdf"]) == 0
    assert calls == [("report.pdf", {"output_dir": "outputs", "resolution": "high",
                                   "llm_layer": True, "batch_size": 1})]
    printed = capsys.readouterr().out
    assert "Markdown: outputs/report/report.md" in printed
    assert "Report: outputs/report/report.json" in printed
    assert "Page: outputs/report/report.p0001.md" in printed
    assert "Estimated cost (USD): 0.000000" in printed
    assert "Brief:" not in printed


def test_unicode_url_options_and_unknown_cost(conversion, capsys):
    calls, result = conversion
    result.report["estimated_cost_usd"] = None
    result.brief_path = Path("outputs/report/report.brief.md")
    result.index_path = Path("outputs/report/report.index.md")
    source = "https://example.org/été.pdf"
    cli.main([source, "--out", "résultats", "--resolution", "low", "--no-ai", "--batch-size", "3"])
    assert calls == [(source, {"output_dir": "résultats", "resolution": "low",
                              "llm_layer": False, "batch_size": 3})]
    printed = capsys.readouterr().out
    assert "Estimated cost (USD): unknown" in printed
    assert "Brief: outputs/report/report.brief.md" in printed
    assert "Index: outputs/report/report.index.md" in printed


@pytest.mark.parametrize("arguments", [
    [], ["file.pdf", "--resolution", "wrong"], ["file.pdf", "--batch-size", "0"],
    ["file.pdf", "--batch-size", "-2"], ["file.pdf", "--batch-size", "1.5"],
])
def test_invalid_input_arguments_never_call_conversion(arguments, conversion):
    calls, _ = conversion
    with pytest.raises(SystemExit) as exc:
        cli.main(arguments)
    assert exc.value.code == 2
    assert calls == []


def test_conversion_failure_surfaces(conversion, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("input is unreadable")

    monkeypatch.setattr(cli, "convert", fail)
    with pytest.raises(OSError, match="input is unreadable"):
        cli.main(["missing.pdf", "--no-ai"])
