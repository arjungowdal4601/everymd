"""Docling behind the resolution profiles: one page per conversion, exported to Markdown with its images."""

from __future__ import annotations

import ctypes
import os
import platform
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.pipeline_options import (
    CodeFormulaVlmOptions,
    OcrAutoOptions,
    OcrMacOptions,
    PdfPipelineOptions,
    RapidOcrOptions,
    TableFormerMode,
    TableStructureOptions,
)
from docling.datamodel.vlm_engine_options import TransformersVlmEngineOptions
from docling.document_converter import DocumentConverter, ImageFormatOption, PdfFormatOption
from docling_core.types.doc import DoclingDocument, ImageRefMode

from . import config, sidecar, tables
from .facts import TitleFinder, furniture_text, headings_on, table_headers, title_of  # noqa: F401


@dataclass
class Unit:
    """One page or slide, or the whole document when it has no pages."""

    number: int
    markdown: str
    image: Any = None  # PIL image of the page, kept only until the copy-editor has seen it
    table_images: list = field(default_factory=list)  # sharper table crops, for scanned pages
    links: list = field(default_factory=list)  # links printed on the page that Docling's text misses
    furniture: list[str] = field(default_factory=list)  # running headers/footers Docling left out
    headings: list[str] = field(default_factory=list)  # headings that start on this page, as Markdown
    scanned: bool = False  # no text layer: Docling read the words with OCR
    table_headers: list[str] = field(default_factory=list)  # column names of the page's tables, as Docling read them


def gpu_device() -> str | None:
    """The accelerator Docling can use here: CUDA, Apple MPS, or None (CPU, e.g. in Docker)."""
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return None


def _ocr_options(profile: dict):
    """Apple Vision on macOS; elsewhere RapidOCR. Regions without a text layer are read at scan_dpi
    (300 DPI read more digits right on every gold page of the eval's census scan); `OcrAutoOptions`
    would drop the scale."""
    if platform.system() == "Darwin":
        return OcrMacOptions(scale=profile["scan_dpi"] / 72) if profile["scan_dpi"] else OcrMacOptions()
    if not profile["scan_dpi"]:
        return OcrAutoOptions()
    # RapidOCR's own 2,000 px cap stays: lifting it let its detector (which stretches each region's short
    # side to 736 px) blow a thin strip up into a huge image and crash inside OpenCV.
    return RapidOcrOptions(backend="onnxruntime", lang=[], scale=profile["scan_dpi"] / 72)


def pdf_options(resolution: str, use_gpu: bool, scan: bool = False) -> tuple[PdfPipelineOptions, str]:
    """Pipeline options for PDFs and images at a resolution profile, plus the device name. For scanned
    documents the stored page images are rendered at scan_dpi, so table crops for the copy-editor are sharp."""
    profile = config.RESOLUTIONS[resolution]
    device = gpu_device() if use_gpu else None
    images_scale = profile["images_scale"]
    if scan and profile["scan_dpi"]:
        images_scale = max(images_scale, profile["scan_dpi"] / 72)
    options = PdfPipelineOptions(
        images_scale=images_scale,
        generate_page_images=True,
        generate_picture_images=True,
        do_ocr=True,
        ocr_options=_ocr_options(profile),
        do_table_structure=True,
        table_structure_options=TableStructureOptions(
            mode=TableFormerMode.ACCURATE if profile["accurate_tables"] else TableFormerMode.FAST,
            do_cell_matching=True,
        ),
        do_formula_enrichment=profile["formulas"],
        do_code_enrichment=profile["code"],
        ocr_batch_size=config.DOCLING_PAGES_AT_ONCE,
        layout_batch_size=config.DOCLING_PAGES_AT_ONCE,
        table_batch_size=config.DOCLING_PAGES_AT_ONCE,
        queue_max_size=config.DOCLING_PAGES_AT_ONCE,
        accelerator_options=AcceleratorOptions(
            device=AcceleratorDevice(device) if device else AcceleratorDevice.CPU,
            num_threads=min(os.cpu_count() or 4, 8),
        ),
    )
    if device is None and (profile["formulas"] or profile["code"]):
        options.code_formula_options = _cpu_code_formula_options(options.code_formula_options)
    return options, device or "cpu"


def _cpu_code_formula_options(default: CodeFormulaVlmOptions) -> CodeFormulaVlmOptions:
    """Docling runs its formula/code model in bfloat16, which took 3-5 minutes per formula on CPU
    in Docker; float32 gives the same result in about 10 seconds."""
    spec = default.model_spec.model_copy(deep=True)
    for engine_config in spec.engine_overrides.values():
        engine_config.extra_config["torch_dtype"] = "float32"
    return CodeFormulaVlmOptions(engine_options=TransformersVlmEngineOptions(torch_dtype="float32"), model_spec=spec)


@lru_cache(maxsize=1)  # one set of models in memory; a different profile reloads them (a few seconds)
def _converter(resolution: str, use_gpu: bool, scan: bool) -> tuple[DocumentConverter, str]:
    options, device = pdf_options(resolution, use_gpu, scan)
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options),
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=options),
        }
    )
    return converter, device


@dataclass
class PageRun:
    doc: DoclingDocument
    page_count: int
    device: str
    notes: list[str]


def convert_page(source: Path, page_no: int, resolution: str, use_gpu: bool, scan: bool = False) -> PageRun:
    """Convert one page. A page Docling can't read comes back empty with a note, so one bad page
    never stops a long document; a file it can't open at all raises."""
    converter, device = _converter(resolution, use_gpu, scan)
    result = converter.convert(source, page_range=(page_no, page_no), raises_on_error=False)
    errors = [error.error_message for error in (result.errors or [])]
    if not result.input.valid:
        raise RuntimeError("; ".join(errors) or "Docling could not open the document")
    notes = [f"Docling, page {page_no}: {message}" for message in errors]
    if result.status == ConversionStatus.FAILURE and not notes:
        notes.append(f"Docling could not read page {page_no}; it is left empty.")
    return PageRun(result.document, result.input.page_count, device, notes)


def run(source: Path | str, resolution: str, use_gpu: bool) -> tuple[DoclingDocument, str, list[str]]:
    """Convert a whole document in one call (inputs without pages: e-books, emails, native fallbacks)."""
    converter, device = _converter(resolution, use_gpu, False)
    result = converter.convert(source)
    return result.document, device, [f"Docling: {error.error_message}" for error in (result.errors or [])]


def export_page(doc: DoclingDocument, page_no: int, out_dir: Path, *, crops: bool) -> tuple[Unit, DoclingDocument, list[str]]:
    """The page's Markdown, with pictures saved under images/ and a screenshot under each table.
    Returns the unit, a pixel-free copy of the page's document for the sidecar, and notes."""
    notes: list[str] = []
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    page = doc.pages.get(page_no)
    image = page.image.pil_image if page is not None and page.image is not None else None
    try:
        shots = tables.save_images(doc, images_dir)
    except Exception as exc:  # screenshots are extra; never fail the conversion over them
        shots = {}
        notes.append(f"Could not save table screenshots on page {page_no} ({type(exc).__name__}: {exc}).")
    for each in doc.pages.values():
        each.image = None  # so the copy below doesn't duplicate the page bitmap
    with_refs, mode = _with_picture_files(doc, images_dir, out_dir, notes)
    markdown = tables.page_markdown(with_refs, page_no, mode, {ref: link for ref, (link, _) in shots.items()})
    unit = Unit(
        page_no,
        markdown,
        image,
        table_images=[crop for _, crop in shots.values()] if crops else [],
        furniture=furniture_text(doc, page_no),
        headings=headings_on(doc, page_no),
        table_headers=table_headers(doc, page_no),
    )
    return unit, sidecar.light_copy(with_refs), notes


def export_whole(doc: DoclingDocument, out_dir: Path, *, furniture: bool) -> tuple[list[Unit], list[str]]:
    """Markdown for a document converted in one go: one unit, or one per page when it has pages."""
    notes: list[str] = []
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    with_refs, mode = _with_picture_files(doc, images_dir, out_dir, notes)
    if not doc.pages:
        markdown = tables.page_markdown(with_refs, None, mode, {}, furniture=furniture)
        return [Unit(1, markdown, headings=headings_on(doc, None))], notes
    units = []
    for number in sorted(doc.pages):
        image = doc.pages[number].image.pil_image if doc.pages[number].image is not None else None
        units.append(Unit(number, tables.page_markdown(with_refs, number, mode, {}), image,
                          furniture=furniture_text(doc, number), headings=headings_on(doc, number)))
    return units, notes


def _with_picture_files(doc: DoclingDocument, images_dir: Path, out_dir: Path, notes: list[str]):
    try:
        # Private Docling helper: saves picture files and points the Markdown at them.
        return doc._with_pictures_refs(image_dir=images_dir, page_no=None, reference_path=out_dir), ImageRefMode.REFERENCED
    except Exception as exc:  # keep converting with image placeholders instead of failing
        notes.append(f"Could not save picture files ({type(exc).__name__}: {exc}); images are placeholders.")
        return doc, ImageRefMode.PLACEHOLDER


def release_memory() -> None:
    """Hand memory freed after a page back to the system. Docling's ~100 threads each keep a glibc
    malloc arena, so without this the process grows page after page although nothing leaks (measured:
    20 pages 2.6 -> 4.0 GB without, flat at about 2.8 GB with)."""
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except (OSError, AttributeError):  # macOS or musl: nothing to trim
        pass
