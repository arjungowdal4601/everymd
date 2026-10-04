"""Shared fixtures: sample inputs and a scripted chat model for offline copy-editor tests."""

from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from pydantic import Field

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "samples" / "inputs"


def pytest_report_header(config):
    names = ("docling", "deepagents", "langchain-openai", "magika")
    return "everymd dependencies: " + ", ".join(f"{name} {metadata.version(name)}" for name in names)


@pytest.fixture(scope="session")
def inputs() -> Path:
    if not (INPUTS / "update.eml").exists():
        sys.path.insert(0, str(ROOT / "samples"))
        import make_samples

        make_samples.main()
    return INPUTS


def _tool_name(tool) -> str:
    if isinstance(tool, dict):
        return tool.get("name") or tool["function"]["name"]
    return tool.name


class ScriptedModel(GenericFakeChatModel):
    """Replays scripted AIMessages in order. It reports itself as openai:gpt-6-luna, so the
    copy-editor's harness profile applies exactly as it does for the real model."""

    model_name: str = "gpt-6-luna"
    seen_tools: list = Field(default_factory=list)
    seen_requests: list = Field(default_factory=list)

    def bind_tools(self, tools, **kwargs):
        self.seen_tools.append(sorted(_tool_name(tool) for tool in tools))
        return self

    def _get_ls_params(self, **kwargs):
        return {"ls_provider": "openai", "ls_model_name": self.model_name, "ls_model_type": "chat"}

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.seen_requests.append(list(messages))
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


def submit(
    page: int,
    markdown: str,
    changes: list[str] | None = None,
    call_id: str | None = None,
    note: str | None = None,
    page_note: str | None = None,
) -> AIMessage:
    """A scripted model turn that calls submit_page."""
    args = {"page_number": page, "markdown": markdown, "changes": changes or []}
    if note is not None:
        args["continuity_note"] = note
    if page_note is not None:
        args["page_note"] = page_note
    return AIMessage(content="", tool_calls=[{"name": "submit_page", "args": args, "id": call_id or f"call_{page}"}])


def submit_brief(markdown: str, index: str | None = None) -> AIMessage:
    """A scripted model turn that calls submit_brief."""
    args = {"markdown": markdown} if index is None else {"markdown": markdown, "index": index}
    return AIMessage(content="", tool_calls=[{"name": "submit_brief", "args": args, "id": "call_brief"}])


def done() -> AIMessage:
    return AIMessage(content="done")


@pytest.fixture
def scripted():
    def make(*turns: AIMessage) -> ScriptedModel:
        return ScriptedModel(messages=iter(turns))

    return make
