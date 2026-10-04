"""Output folder names: readable, filesystem-safe, and never shared by two different inputs.

A folder is reused only when it provably holds this same input's earlier conversion (its report.json
names the same source). Any other folder with that name (another input's output, or a folder that is not
everymd's at all) is left alone and this input gets the name plus a short hash of where it came from.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlparse

from .detect import Detected

MAX_BYTES = 200  # leaves room for "-<hash>", ".partial-<random>" and ".docling.json" under the 255-byte limit


def identity(found: Detected) -> str:
    """What makes an input this input: the URL, or the file's absolute path."""
    return found.source if found.kind == "url" else str(found.path.resolve())


def _short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def output_name(found: Detected) -> str:
    """A readable name from the file name or URL; letters in any script are kept."""
    if found.kind == "url":
        parsed = urlparse(found.source)
        last = unquote(Path(parsed.path).name)
        raw = f"{parsed.hostname}-{last}" if last else (parsed.hostname or "page")
        if parsed.query:  # index.php?title=A and index.php?title=B are different pages
            raw += f"-{_short_hash(parsed.query)}"
    else:
        raw = found.path.stem
    text = re.sub(r"[^\w.-]+", "-", unicodedata.normalize("NFKC", raw))
    text = text.encode("utf-8")[:MAX_BYTES].decode("utf-8", "ignore").strip("-._")
    return text or "document"


def belongs_to(folder: Path, found: Detected) -> bool:
    """True when the folder holds this input's own earlier conversion (so it may be replaced)."""
    try:
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(report, dict) or "versions" not in report:
        return False  # not an everymd report
    if report.get("source_id") is not None:
        return report["source_id"] == identity(found)
    source = report.get("source")  # written before source_id existed: compare the source as given
    if not isinstance(source, str):
        return False
    if found.kind == "url":
        return source == found.source
    return str(Path(source).expanduser().resolve()) == identity(found)


def hashed_name(found: Detected) -> str:
    return f"{output_name(found)}-{_short_hash(identity(found))}"


def folder_name(output_dir: Path, found: Detected) -> str:
    """This input's folder under output_dir: its plain name when free or its own, else name-<hash>."""
    name = output_name(found)
    if not (output_dir / name).exists() or belongs_to(output_dir / name, found):
        return name
    hashed = hashed_name(found)
    if (output_dir / hashed).exists() and not belongs_to(output_dir / hashed, found):
        raise FileExistsError(f"'{output_dir / hashed}' exists and is not this input's output; choose another output_dir.")
    return hashed
