"""Work out what kind of input we have: URLs by scheme, files by content first, extension second."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse


class UnsupportedInput(ValueError):
    """The input exists, but this version of everymd does not convert it."""


# Magika label or file extension -> everymd kind.
KINDS = {
    "pdf": "pdf",
    "png": "image", "jpeg": "image", "jpg": "image", "tiff": "image", "tif": "image",
    "bmp": "image", "webp": "image",
    "docx": "docx", "doc": "doc", "odt": "odt", "rtf": "rtf",
    "pptx": "pptx", "ppt": "ppt", "odp": "odp",
    "html": "html", "htm": "html", "xhtml": "html",
    "epub": "epub",
    "eml": "email", "msg": "email", "outlook": "email",
}
SPREADSHEETS = {"xlsx", "xlsm", "xls", "ods", "csv", "tsv"}

# How each kind is made page-able (see render.py).
OFFICE_KINDS = {"docx", "doc", "odt", "rtf", "pptx", "ppt", "odp"}
WEB_KINDS = {"html", "url"}
SLIDE_KINDS = {"pptx", "ppt", "odp"}
# File extension Docling expects for each kind when we stage the input under a clean name.
EXTENSIONS = {
    "pdf": "pdf", "docx": "docx", "doc": "doc", "odt": "odt", "rtf": "rtf",
    "pptx": "pptx", "ppt": "ppt", "odp": "odp", "html": "html", "epub": "epub",
}
IMAGE_EXTENSIONS = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "tiff": "tif", "tif": "tif", "bmp": "bmp", "webp": "webp"}


@dataclass(frozen=True)
class Detected:
    kind: str  # pdf, image, docx, doc, odt, rtf, pptx, ppt, odp, html, url, epub or email
    source: str  # exactly what the caller passed
    path: Path | None  # None for URLs
    label: str  # the Magika label, the file extension, or "url"
    method: str  # "url", "magika" or "extension"


@lru_cache(maxsize=1)
def _magika():
    from magika import Magika

    return Magika()


def _content_label(path: Path) -> str:
    result = _magika().identify_path(path)
    return str(result.output.label).lower()


def detect(source: str | Path) -> Detected:
    """Return what `source` is, or raise UnsupportedInput with a clear message."""
    text = str(source)
    if urlparse(text).scheme in ("http", "https"):
        return Detected("url", text, None, "url", "url")

    path = Path(text).expanduser()
    if path.is_dir():
        raise UnsupportedInput(f"'{path}' is a folder. everymd converts one file at a time.")
    if not path.is_file():
        raise FileNotFoundError(f"No such file: {path}")
    if path.stat().st_size == 0:
        raise UnsupportedInput(f"'{path.name}' is empty (0 bytes).")

    label = _content_label(path)
    extension = path.suffix.lower().lstrip(".")
    if label in SPREADSHEETS or (label not in KINDS and extension in SPREADSHEETS):
        raise UnsupportedInput(
            f"'{path.name}' is a spreadsheet. Spreadsheets (XLSX, XLS, ODS, CSV) are not supported in this version."
        )
    if label in KINDS:
        return Detected(KINDS[label], text, path, label, "magika")
    if extension in KINDS:
        return Detected(KINDS[extension], text, path, extension, "extension")
    raise UnsupportedInput(
        f"Can't convert '{path.name}': its content looks like '{label}', which everymd does not support."
    )
