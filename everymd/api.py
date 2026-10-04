"""convert(): detect the input, make it page-able, read it page by page, then write the complete document,
the Docling sidecar, the brief, the index and the report. Everything is written into a staging folder that
replaces the previous output only once the conversion has finished."""

from __future__ import annotations

import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

from langchain_core.language_models import BaseChatModel

from . import brief, config, models, names, publish, report, sidecar, stream
from .assemble import blocks, front_matter
from .detect import SLIDE_KINDS, detect
from .prepare import Prepared, prepare


@dataclass
class ConvertResult:
    markdown_path: Path
    report_path: Path
    json_path: Path
    markdown: str = field(repr=False)
    report: dict = field(repr=False)
    page_paths: list[Path] = field(default_factory=list)  # one file per page or slide; [] without pages
    brief_path: Path | None = None  # name.brief.md, written when the AI layer is on (not for single images)
    index_path: Path | None = None  # name.index.md: which pages contain what (documents with pages, not web)


def convert(
    source: str | Path,
    output_dir: str | Path = "outputs",
    resolution: str = "high",
    use_gpu: bool = True,
    llm_layer: bool = True,
    batch_size: int | None = 1,
    model: str | BaseChatModel | None = None,
) -> ConvertResult:
    """Convert one file or URL to LLM-ready Markdown. The input type is detected automatically.
    `model` is a "provider:model" name or a LangChain chat model; by default models.py decides."""
    if resolution not in config.RESOLUTIONS:
        raise ValueError(f"resolution must be one of {list(config.RESOLUTIONS)}, not {resolution!r}")
    if batch_size is not None and (isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size < 1):
        raise ValueError("batch_size must be a positive whole number, or None for all pages at once")

    started = time.monotonic()
    found = detect(source)
    llm = models.build(model) if llm_layer else None  # fail fast if the key or provider package is missing
    output_root = Path(output_dir)
    name = names.folder_name(output_root, found)
    stage = publish.Stage(output_root, name, owns=lambda folder: names.belongs_to(folder, found),
                          fallback=names.hashed_name(found))
    reading = stream.Reading(name=name, kind=found.kind)
    run = _Run(found, name, resolution, use_gpu, llm, batch_size, started)
    try:
        with tempfile.TemporaryDirectory(prefix="everymd-") as work:
            run.prepared = prepare(found, name, Path(work), run.notes)
            reading.kind = run.prepared.kind
            stream.read(
                run.prepared, stage.dir, name=name, llm=llm, resolution=resolution, use_gpu=use_gpu,
                batch_size=batch_size, shared=run.shared(), reading=reading,
                on_batch=lambda current: stage.progress(run.report(current, None, "running")),
            )
        written = _write_outputs(run, reading, stage)
        stage.publish()  # may move to the fallback name: paths are resolved afterwards
    except BaseException as exc:
        failed = stage.fail(run.report(reading, None, "failed", error=f"{type(exc).__name__}: {exc}"))
        if isinstance(exc, Exception):
            exc.add_note(f"everymd kept what it had done, and a report of the spend, in {failed}")
        raise
    return written.result(stage.final_path)


class _Run:
    """The conversion's settings and running notes, and the report built from them."""

    def __init__(self, found, name, resolution, use_gpu, llm, batch_size, started):
        self.found, self.name, self.resolution, self.use_gpu = found, name, resolution, use_gpu
        self.llm, self.batch_size, self.started = llm, batch_size, started
        self.notes: list[str] = []
        self.prepared: Prepared | None = None
        self.extra_usage: dict = {}  # the brief's call

    def shared(self) -> dict:
        """Front-matter every output file carries."""
        return {
            "title": self.name,
            "source": self.found.source,
            "detected_type": self.prepared.kind if self.prepared else self.found.kind,
            "resolution": self.resolution,
            "ai_model": models.name_of(self.llm) if self.llm is not None else None,
        }

    def report(self, reading: stream.Reading, page_paths: list[Path] | None, status: str, **extra) -> dict:
        from . import __version__

        prepared = self.prepared
        usage = brief.merge_usage(reading.usage, self.extra_usage)
        scan = prepared.scan if prepared else None
        return {
            "status": status,
            **extra,
            "source": self.found.source,
            "source_id": names.identity(self.found),
            "detected_type": prepared.kind if prepared else self.found.kind,
            "detection": {"label": self.found.label, "method": self.found.method},
            "rendered_to_pdf": prepared.rendered if prepared else False,
            "renderer": prepared.renderer if prepared else None,
            "resolution": self.resolution,
            "use_gpu": self.use_gpu,
            "device": reading.device,
            "llm_layer": self.llm is not None,
            "copy_editor_input": reading.copy_editor_input,
            "batch_size": self.batch_size,
            "model": models.name_of(self.llm) if self.llm is not None else None,
            "reasoning_effort": getattr(self.llm, "reasoning_effort", None),
            **report.cost_fields(usage),
            "seconds": round(time.monotonic() - self.started, 1),
            "scanned_pages": sorted(scan.pages_without_text) if scan else [],
            "rotated_pages": scan.rotated if scan else {},
            "links": {"found": reading.link_stats.found, "placed": reading.link_stats.placed,
                      "for_copy_editor": reading.link_stats.for_editor},
            "pages": report.pages_field(reading.units, reading.edits),
            "page_files": sorted(path.name for path in (reading.page_paths if page_paths is None else page_paths)),
            "notes": self.notes + reading.notes + (reading.editor.notes if reading.editor else []),
            "versions": {"everymd": __version__, "docling": metadata.version("docling")},
        }


@dataclass
class _Written:
    """What _write_outputs wrote into the staging folder; turned into final paths after publishing."""

    markdown_path: Path
    report_path: Path
    json_path: Path
    markdown: str
    report: dict
    page_paths: list[Path]
    brief_path: Path | None
    index_path: Path | None

    def result(self, final) -> ConvertResult:
        return ConvertResult(
            final(self.markdown_path), final(self.report_path), final(self.json_path), self.markdown, self.report,
            [final(p) for p in self.page_paths], final(self.brief_path) if self.brief_path else None,
            final(self.index_path) if self.index_path else None,
        )


def _write_outputs(run: _Run, reading: stream.Reading, stage: publish.Stage) -> _Written:
    prepared, name, units, edits = run.prepared, run.name, reading.units, reading.edits
    title = reading.title or name
    single_image = prepared.kind == "image" and len(units) == 1 and reading.anchor is not None
    fields = {
        **run.shared(),
        "title": title,
        "pages": len(units) if reading.anchor else None,
        "converted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "converter": {"everymd": _version(), "docling": metadata.version("docling")},
        "ai_copy_edited": bool(edits),
    }
    fields = {key: fields[key] for key in ("title", "source", "detected_type", "pages", "converted_at",
                                           "converter", "resolution", "ai_copy_edited", "ai_model")}
    caption = edits[units[0].number].page_note if single_image and units[0].number in edits else None
    if prepared.kind == "image":  # a single image's caption is its page note, kept exactly as written
        fields["ai_caption"] = caption
    page_blocks = blocks(units, edits, anchor=reading.anchor, notes=prepared.speaker_notes)
    markdown = front_matter(fields) + "\n\n" + "\n\n".join(b for b in page_blocks if b) + "\n"
    stage.path(f"{name}.md").write_text(markdown, encoding="utf-8")

    page_paths = sorted(reading.page_paths, key=lambda p: p.name)
    if reading.anchor and reading.titles_used != {title}:  # the title turned up after early pages: refresh
        from . import pages

        entries = [(u.number, b, edits.get(u.number)) for u, b in zip(units, page_blocks)]
        page_paths = pages.write(stage.dir, name, entries, anchor=reading.anchor, shared={**run.shared(), "title": title})

    json_path = stage.path(f"{name}.docling.json")
    if reading.whole_doc is not None:
        sidecar.save_whole(reading.whole_doc, json_path)
    else:
        sidecar.save_pages(reading.light_docs, json_path, name)

    brief_path = index_path = None
    if run.llm is not None and not single_image:
        style = brief.style_for(prepared.kind, reading.anchor is not None, prepared.kind in SLIDE_KINDS)
        made = brief.make(units, edits, model=run.llm, title=title, kind=prepared.kind, style=style,
                          has_pages=reading.anchor is not None)
        run.extra_usage, run.notes = made.usage, run.notes + made.notes
        if made.markdown is not None:
            shared = {key: fields[key] for key in ("title", "source", "detected_type", "ai_model")}
            brief_path = brief.save(stage.dir, name, made.markdown, shared)
            if made.index is not None:
                index_path = brief.save(stage.dir, name, made.index, shared, kind="index")

    data = run.report(reading, page_paths, "complete", caption=caption,
                      brief_file=brief_path.name if brief_path else None,
                      index_file=index_path.name if index_path else None)
    report.write(stage.path("report.json"), data)
    return _Written(stage.path(f"{name}.md"), stage.path("report.json"), json_path, markdown, data,
                    page_paths, brief_path, index_path)


def _version() -> str:
    from . import __version__

    return __version__


# Kept importable from here for callers of the earlier API.
estimate_cost = report.estimate_cost
token_totals = report.token_totals
output_name = names.output_name
