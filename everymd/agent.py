"""The copy-editor: a LangChain Deep Agent that patches Docling's Markdown against each page image.

It is fed pages as Docling produces them (`CopyEditor.edit`), one batch at a time, and carries the end of
the previous page and the continuity note from one batch to the next. Each batch is one Deep Agents run
with a single tool, `submit_page`; what the model writes is kept exactly as written.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from deepagents import GeneralPurposeSubagentProfile, HarnessProfile, create_deep_agent, register_harness_profile
from langchain.tools import tool
from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from . import config, links, models, prompts
from .docling_step import Unit

log = logging.getLogger(__name__)

# Kept for callers that read the prompt; the text lives in prompts.py.
SYSTEM_PROMPT = prompts.COPY_EDITOR

# The copy-editor needs nothing but submit_page: hide Deep Agents' filesystem tools and subagent.
# Deep Agents keeps profiles per process and per `provider:model`, so this also applies to any other
# Deep Agent the same process builds on the same model (see the README).
_HIDDEN_TOOLS = frozenset({"ls", "read_file", "write_file", "edit_file", "delete", "glob", "grep", "execute"})
_PROFILE = HarnessProfile(
    excluded_tools=_HIDDEN_TOOLS,
    general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
)
_registered_keys: set[str] = set()


@dataclass
class PageEdit:
    markdown: str
    changes: list[str]
    continuity_note: str | None = None  # written for the next page, kept exactly as written
    page_note: str | None = None  # what this page covers, for the brief, kept exactly as written


@dataclass
class EditResult:
    pages: dict[int, PageEdit] = field(default_factory=dict)
    usage: dict = field(default_factory=dict)  # LangChain usage metadata per model name
    notes: list[str] = field(default_factory=list)


def register_profile(llm: BaseChatModel) -> None:
    """Deep Agents looks profiles up by `provider:model`; register ours once for the model in use."""
    key = models.profile_key(llm)
    if key and key not in _registered_keys:
        register_harness_profile(key, _PROFILE)
        _registered_keys.add(key)


def _submit_tool(expected: set[int], submitted: dict[int, PageEdit]):
    @tool
    def submit_page(
        page_number: int,
        markdown: str,
        changes: list[str] | None = None,
        continuity_note: str | None = None,
        page_note: str | None = None,
    ) -> str:
        """Submit the finished Markdown for one page. Call it once per page.

        Args:
            page_number: The page you are submitting.
            markdown: The complete corrected Markdown for that page.
            changes: Short notes on what you changed; empty if nothing.
            continuity_note: The note for the next page: where I am, still open, watch for.
            page_note: One or two sentences on what this page covers, for the brief.
        """
        if page_number not in expected:
            return f"Page {page_number} is not in this batch. Submit pages {sorted(expected)}."
        submitted[page_number] = PageEdit(markdown, list(changes or []), continuity_note, page_note)
        remaining = sorted(expected - submitted.keys())
        return f"Saved page {page_number}." + (f" Still to submit: {remaining}." if remaining else " All pages submitted.")

    return submit_page


class CopyEditor:
    """Edits pages batch by batch as they arrive, keeping the reading context between batches."""

    def __init__(
        self,
        model: str | BaseChatModel | None = None,
        *,
        total: int,
        title: str = "",
        slides: bool = False,
        single_image: bool = False,
        scan: bool = False,
        web: bool = False,
        text_only: bool = False,
    ):
        self.llm = models.build(model)
        register_profile(self.llm)
        self.total, self.title = total, title
        self.slides, self.single_image, self.scan, self.text_only = slides, single_image, scan, text_only
        self.web = web
        self.pages: dict[int, PageEdit] = {}
        self.notes: list[str] = []
        self._usage = UsageMetadataCallbackHandler()
        self._tail = ""
        self._note: tuple[int, str] | None = None  # (page it was written after, text)
        self._tables: tuple[int, list[str]] | None = None  # (previous page, its tables' column names from Docling)
        self._failed_in_a_row = 0
        self.stopped = False

    @property
    def usage(self) -> dict:
        return dict(self._usage.usage_metadata)

    def prompt(self, text_only: bool) -> str:
        base = prompts.TEXT_ONLY if text_only else prompts.COPY_EDITOR
        base += prompts.SLIDES_NOTE if self.slides else ""
        base += prompts.WEB_NOTE if self.web else ""
        if not text_only:
            base += prompts.TABLE_CROPS_NOTE if self.scan else ""
            base += prompts.IMAGE_NOTE if self.single_image else ""
        return base

    def edit(self, batch: list[Unit]) -> None:
        """Copy-edit one batch. Pages the model doesn't submit keep Docling's Markdown."""
        if not batch:
            return
        if self.stopped:
            self._remember_tail(batch)
            return
        with_images = [unit for unit in batch if unit.image is not None]
        if self.text_only or not with_images:  # nothing to look at: structure only (empty pages skipped)
            pages, text_only = [unit for unit in batch if unit.markdown.strip()], True
        else:  # a page Docling could not render has nothing to check against: keep its output
            pages, text_only = with_images, False
            for unit in batch:
                if unit.image is None:
                    self.notes.append(f"Page {unit.number} has no page image; kept Docling's output.")
        if pages:
            self._edit(pages, text_only)
        self._remember_tail(batch)

    def _edit(self, batch: list[Unit], text_only: bool) -> None:
        submitted: dict[int, PageEdit] = {}
        agent = create_deep_agent(
            model=self.llm,
            tools=[_submit_tool({unit.number for unit in batch}, submitted)],
            system_prompt=self.prompt(text_only),
        )
        limit = config.RECURSION_BASE + config.RECURSION_PER_PAGE * len(batch)
        span = f"{batch[0].number}-{batch[-1].number}" if len(batch) > 1 else str(batch[0].number)
        try:
            agent.invoke(
                {"messages": [self._message(batch, text_only)]},
                config={"callbacks": [self._usage], "recursion_limit": limit},
            )
            failure = None
        except Exception as exc:  # API, network or run-limit failure: keep what was submitted
            log.warning("Copy-editor failed on pages %s: %s", span, exc)
            failure = f"{type(exc).__name__}: {exc}"
            self.notes.append(f"Copy-editor stopped on pages {span}: {failure}")
        for unit in batch:
            if unit.number in submitted:
                self.pages[unit.number] = submitted[unit.number]
                if submitted[unit.number].continuity_note:
                    self._note = (unit.number, submitted[unit.number].continuity_note)
            else:
                self.notes.append(f"Page {unit.number} was not submitted by the copy-editor; kept Docling's output.")
        self._failed_in_a_row = self._failed_in_a_row + 1 if failure and not submitted else 0
        if self._failed_in_a_row >= config.MAX_FAILED_BATCHES:
            self.stopped = True
            self.notes.append(
                f"Copy-editor turned off after {self._failed_in_a_row} failed batches in a row (last error: "
                f"{failure}); the remaining pages keep Docling's output."
            )

    def _remember_tail(self, batch: list[Unit]) -> None:
        last = batch[-1]
        self._tables = (last.number, last.table_headers) if last.table_headers else None
        source = self.pages[last.number].markdown if last.number in self.pages else last.markdown
        self._tail = source[-config.PREVIOUS_TAIL_CHARS :]

    def _message(self, batch: list[Unit], text_only: bool) -> HumanMessage:
        numbers = ", ".join(str(unit.number) for unit in batch)
        what = f"page {numbers}" if len(batch) == 1 else f"pages {numbers}"
        of = f" of {self.total}" if self.total else ""
        title = f" of “{self.title}”" if self.title else ""
        blocks: list[dict] = [{"type": "text", "text": f"Copy-edit {what}{of}{title}."}]
        if self._note:
            blocks.append({
                "type": "text",
                "text": f'<continuity_note written_after_page="{self._note[0]}">\n{self._note[1]}\n</continuity_note>',
            })
        if self._tail:
            blocks.append({
                "type": "text",
                "text": "End of the previous page as already written. It is context only: don't copy any of it "
                f"into this page.\n<previous>\n{self._tail}\n</previous>",
            })
        if self._tables:
            names = "\n".join(f"- {header}" for header in self._tables[1])
            blocks.append({
                "type": "text",
                "text": f"Column names of the tables on page {self._tables[0]}, as Docling read them (use them when a "
                f"table continues on this page without its header row):\n{names}",
            })
        for unit in batch:
            blocks.extend(self._unit_blocks(unit, text_only))
        return HumanMessage(content=blocks)

    def _unit_blocks(self, unit: Unit, text_only: bool) -> list[dict]:
        n = unit.number
        blocks = [{
            "type": "text",
            "text": f'Page {n}, Docling\'s Markdown:\n<docling_markdown page="{n}">\n{unit.markdown}\n</docling_markdown>',
        }]
        if unit.furniture:
            listed = "\n".join(f"- {text}" for text in unit.furniture)
            blocks.append({
                "type": "text",
                "text": f'Page {n}, running headers and footers Docling left out of the text:\n<furniture page="{n}">\n{listed}\n</furniture>',
            })
        if unit.links:
            blocks.append({
                "type": "text",
                "text": f"Page {n}, links printed on this page that are not in Docling's Markdown (words -> address):\n"
                f'<links page="{n}">\n{links.as_context(unit.links)}\n</links>',
            })
        if unit.image is not None and not text_only:
            source = (
                "it is a scan, so Docling read its words with OCR: check every word and number against the image"
                if unit.scanned else
                "Docling read its words from the file's own text layer, so the spelling is the author's (typos "
                "included); fix only characters that are missing or garbled compared with the image"
            )
            blocks.append({"type": "text", "text": f"Page {n}: {source}."})
            blocks.append({"type": "text", "text": f"Page {n}, page image:"})
            blocks.append(models.image_block(unit.image, self.llm))
            for k, crop in enumerate(unit.table_images, start=1):
                blocks.append({"type": "text", "text": f"Page {n}, table {k} at a higher resolution:"})
                blocks.append(models.image_block(crop, self.llm))
        return blocks


def copy_edit(
    units: list[Unit],
    *,
    batch_size: int | None,
    model: str | BaseChatModel | None = None,
    text_only: bool = False,
    slides: bool = False,
    single_image: bool = False,
    title: str = "",
) -> EditResult:
    """Copy-edit a list of pages that are all in memory, batch by batch."""
    editor = CopyEditor(
        model,
        total=max((unit.number for unit in units), default=0),
        title=title,
        slides=slides,
        single_image=single_image,
        text_only=text_only,
    )
    size = batch_size or len(units)
    for start in range(0, len(units), size):
        editor.edit(units[start : start + size])
    return EditResult(editor.pages, editor.usage, editor.notes)
