"""Command-line entry point: arguments in, convert(), output paths and cost out."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import convert
from .config import RESOLUTIONS


def positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("batch size must be a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("batch size must be a positive integer")
    return number


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert one document or trusted URL to Markdown.")
    parser.add_argument("source", help="one file path or trusted URL")
    parser.add_argument("--out", default="outputs", help="output root (default: outputs)")
    parser.add_argument("--resolution", choices=RESOLUTIONS, default="high")
    parser.add_argument("--no-ai", action="store_true", help="Docling only; no model calls or API key")
    parser.add_argument("--batch-size", type=positive_integer, default=1,
                        help="pages per copy-editor pass (default: 1)")
    args = parser.parse_args(argv)
    result = convert(args.source, output_dir=args.out, resolution=args.resolution,
                     llm_layer=not args.no_ai, batch_size=args.batch_size)
    for label, path in (("Markdown", result.markdown_path), ("Docling JSON", result.json_path),
                        ("Report", result.report_path), ("Brief", result.brief_path),
                        ("Index", result.index_path)):
        if path is not None:
            print(f"{label}: {path}")
    for path in result.page_paths:
        print(f"Page: {path}")
    cost = result.report.get("estimated_cost_usd")
    print("Estimated cost (USD): unknown" if cost is None else f"Estimated cost (USD): {cost:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
