"""Settings that live inside the code: resolution profiles and how much each step reads."""

from __future__ import annotations

# The user only picks a resolution name; these Docling settings stay hidden behind it.
# scan_dpi: OCR resolution, and the resolution of stored page images on scanned pages (no text layer),
# so table crops sent to the copy-editor are sharp. None keeps Docling's defaults (OCR at 216 DPI).
RESOLUTIONS: dict[str, dict] = {
    "low": {"images_scale": 1.0, "accurate_tables": False, "formulas": False, "code": False, "scan_dpi": None},
    "medium": {"images_scale": 1.5, "accurate_tables": True, "formulas": False, "code": False, "scan_dpi": 300},
    "high": {"images_scale": 2.0, "accurate_tables": True, "formulas": True, "code": False, "scan_dpi": 300},
    "max": {"images_scale": 3.0, "accurate_tables": True, "formulas": True, "code": True, "scan_dpi": 300},
}

# Docling converts one page per call (see stream.py), so each stage only ever holds that page.
DOCLING_PAGES_AT_ONCE = 1

# The model, its settings and prices live in models.py.

# What the copy-editor sees for each page.
PREVIOUS_TAIL_CHARS = 1200  # end of the previous corrected page, sent as context only

# Agent graph steps allowed per invocation: a base plus headroom for every page in the batch.
RECURSION_BASE = 12
RECURSION_PER_PAGE = 8
# Stop calling the copy-editor after this many batches in a row fail with nothing submitted
# (a wrong key or an outage); the remaining pages keep Docling's output.
MAX_FAILED_BATCHES = 2

# External renderers and downloads.
SOFFICE_TIMEOUT_S = 180
BROWSER_TIMEOUT_MS = 90_000
BROWSER_SETTLE_MS = 5_000  # after the page has loaded, wait at most this long for network quiet
DOWNLOAD_TIMEOUT_S = 60
DOWNLOAD_MAX_BYTES = 200 * 1024 * 1024  # a URL that is a file (not a web page) is downloaded up to this size

# The brief sees every page note plus this many first pages in full (title page, contents, intro).
BRIEF_FULL_PAGES = 2
# A document without pages (an e-book, an email) goes to the brief in full, up to this many characters.
BRIEF_PAGELESS_CHARS = 200_000
