"""report.json: what happened in a conversion, what it cost, and what each page's copy-editor wrote."""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import models


def token_totals(usage: dict) -> dict[str, int]:
    """Sum LangChain usage metadata across models."""
    totals = {"input": 0, "cached_input": 0, "cache_write": 0, "output": 0, "reasoning": 0}
    for item in usage.values():
        details = item.get("input_token_details") or {}
        totals["input"] += item.get("input_tokens", 0)
        totals["output"] += item.get("output_tokens", 0)
        totals["cached_input"] += details.get("cache_read", 0)
        totals["cache_write"] += details.get("cache_creation", 0)
        totals["reasoning"] += (item.get("output_token_details") or {}).get("reasoning", 0)
    return totals


def estimate_cost(usage: dict) -> float | None:
    """Estimated USD from the price table in models.py; None if a model's price is unknown."""
    total = 0.0
    for model, item in usage.items():
        price = models.price_of(model)
        if price is None:
            return None
        details = item.get("input_token_details") or {}
        cached = details.get("cache_read", 0)
        written = details.get("cache_creation", 0)
        total += (item.get("input_tokens", 0) - cached - written) * price["input"]
        total += written * price.get("cache_write", price["input"])
        total += cached * price["cached_input"] + item.get("output_tokens", 0) * price["output"]
    return round(total / 1_000_000, 6)


def cost_fields(usage: dict) -> dict:
    return {
        "tokens": token_totals(usage),
        "estimated_cost_usd": estimate_cost(usage),
        "prices": {"checked": models.PRICES_CHECKED, "source": models.PRICES_SOURCE},
    }


def pages_field(units, edits) -> list[dict]:
    """What the copy-editor did on each page, its notes kept exactly as written."""
    rows = []
    for unit in units:
        edit = edits.get(unit.number)
        rows.append({
            "number": unit.number,
            "edited_by": "copy-editor" if edit else "docling",
            "changes": edit.changes if edit else [],
            "continuity_note": edit.continuity_note if edit else None,
            "page_note": edit.page_note if edit else None,
        })
    return rows


def write(path: Path, report: dict) -> None:
    """Write report.json atomically (a crash never leaves half a file)."""
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)
