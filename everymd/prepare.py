"""Make an input page-able, so the copy-editor gets page images: Office files and web pages become PDFs,
scanned pages are turned upright, and a URL that is a file is downloaded and read as that file."""

from __future__ import annotations

import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import config, render, scan
from .detect import EXTENSIONS, IMAGE_EXTENSIONS, OFFICE_KINDS, Detected, UnsupportedInput, detect

USER_AGENT = "Mozilla/5.0 (compatible; everymd document converter)"
HTML_TYPES = ("text/html", "application/xhtml+xml")
PAGE_TYPES = ("text/plain", "text/markdown")  # text a browser shows as a page


@dataclass
class Prepared:
    """What Docling will convert, and how it got there."""

    source: Path | str
    kind: str  # the kind actually converted (a URL that is a PDF is converted as "pdf")
    rendered: bool = False
    renderer: str | None = None
    has_pages: bool = False  # a PDF or image Docling reads one page at a time
    speaker_notes: dict[int, str] = field(default_factory=dict)
    scan: scan.ScanInfo = field(default_factory=scan.ScanInfo)


def prepare(found: Detected, name: str, work: Path, notes: list[str]) -> Prepared:
    shown = found.source if found.kind == "url" else found.path.name  # how errors name the input
    if found.kind == "url":
        downloaded = _download_if_file(found.source, work, name)
        if downloaded is None:
            return _render_web(found.source, found.source, name, work, notes, kind="url")
        try:
            found = detect(downloaded)
        except UnsupportedInput as exc:
            raise UnsupportedInput(str(exc).replace(downloaded.name, shown)) from exc
        if found.kind == "html":  # a web page served without a usable type: the browser prints it after all
            return _render_web(shown, shown, name, work, notes, kind="url")
        notes.append(f"The URL is a {found.kind} file, not a web page: it was downloaded and read as one.")
    staged = work / f"{name}.{_staged_extension(found)}"  # content decides the extension Docling sees
    shutil.copyfile(found.path, staged)
    if found.kind == "pdf":
        check_pdf(staged, shown)
        return _upright(Prepared(staged, "pdf", has_pages=True), work, notes)
    if found.kind == "image":
        source, info = scan.upright_image(staged, work)
        notes.extend(info.notes)
        return Prepared(source, "image", has_pages=True, scan=info)
    if found.kind in OFFICE_KINDS:
        prepared = _render_office(staged, found.kind, work, notes)
        if found.kind == "pptx":
            prepared.speaker_notes = render.pptx_notes(staged)
        return prepared
    if found.kind == "html":
        # Print the original file, not the staged copy, so its relative images and styles still load.
        return _render_web(found.path.resolve().as_uri(), staged, name, work, notes, kind="html")
    # EPUB and email have no pages: Docling reads their text directly from the file.
    return Prepared(staged, found.kind)


def check_pdf(path: Path, shown_name: str) -> None:
    """Fail early, in plain words, on a PDF that is password-protected, damaged or empty."""
    import pypdfium2 as pdfium

    try:
        document = pdfium.PdfDocument(str(path))
    except pdfium.PdfiumError as exc:
        if "password" in str(exc).lower():
            raise UnsupportedInput(f"'{shown_name}' is password-protected. Remove the password and try again.") from exc
        raise UnsupportedInput(f"'{shown_name}' could not be read as a PDF: it is damaged or empty ({exc}).") from exc
    try:
        if len(document) == 0:
            raise UnsupportedInput(f"'{shown_name}' is a PDF with no pages.")
    finally:
        document.close()


def _upright(prepared: Prepared, work: Path, notes: list[str]) -> Prepared:
    prepared.source, prepared.scan = scan.upright_pdf(Path(prepared.source), work)
    notes.extend(prepared.scan.notes)
    return prepared


def _staged_extension(found: Detected) -> str:
    if found.kind == "image":
        return IMAGE_EXTENSIONS.get(found.label, "png")
    if found.kind == "email":
        return "msg" if found.label in ("outlook", "msg") else "eml"
    return EXTENSIONS[found.kind]


def _render_office(staged: Path, kind: str, work: Path, notes: list[str]) -> Prepared:
    try:
        pdf = render.office_to_pdf(staged, work)
        return _upright(Prepared(pdf, kind, rendered=True, renderer="libreoffice", has_pages=True), work, notes)
    except FileNotFoundError:
        notes.append(
            "LibreOffice is not installed, so this file was read natively without page images; "
            "its text comes straight from the file and the copy-editor was not needed."
        )
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        notes.append(f"LibreOffice could not render this file ({exc}); it was read natively without page images.")
    return Prepared(staged, kind)


def _render_web(target: str, fallback: Path | str, name: str, work: Path, notes: list[str], *, kind: str) -> Prepared:
    pdf = work / f"{name}.pdf"
    try:
        renderer = render.web_to_pdf(target, pdf)
        return Prepared(pdf, kind, rendered=True, renderer=renderer, has_pages=True)
    except render.HTTPResponseError:
        raise  # an error response is not the requested document; do not convert it as fallback HTML
    except Exception as exc:  # no usable browser, or the page did not load
        notes.append(
            f"Could not print the page with a browser ({type(exc).__name__}: {exc}); "
            "Docling read it directly, without page images."
        )
        return Prepared(fallback, kind)


def _download_if_file(url: str, work: Path, name: str) -> Path | None:
    """Download the URL when it serves a file (a PDF, an image, a Word file...) rather than a web page.
    Returns None for web pages, and when the server can't be asked first (the browser then tries)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        response = urllib.request.urlopen(request, timeout=config.DOWNLOAD_TIMEOUT_S)
    except urllib.error.HTTPError as exc:
        if exc.code >= 400 and exc.code not in (403, 405, 429):
            raise render.HTTPResponseError(f"HTTP {exc.code} while loading {url}") from exc
        return None
    except (urllib.error.URLError, OSError, ValueError):
        return None
    with response:
        raw = response.headers.get("Content-Type")
        content_type = response.headers.get_content_type().lower() if raw and "/" in raw else ""
        if content_type in HTML_TYPES or content_type in PAGE_TYPES:
            return None  # a web page: the browser prints it
        # Anything else (a PDF, an image, a CSV, or no usable type at all) is downloaded and detected.
        target = work / f"{name}.download"
        size = 0
        with target.open("wb") as out:
            while chunk := response.read(1 << 20):
                size += len(chunk)
                if size > config.DOWNLOAD_MAX_BYTES:
                    raise UnsupportedInput(
                        f"'{url}' is larger than {config.DOWNLOAD_MAX_BYTES // (1024 * 1024)} MB; download it and pass the file."
                    )
                out.write(chunk)
    return target
