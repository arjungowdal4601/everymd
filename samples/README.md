# Samples

Every input except the web URL is an original document created by [`make_samples.py`](make_samples.py) (images and PDFs) and [`doc_samples.py`](doc_samples.py) (Office, web, ebook and email). The figures are invented. Recreate them with:

```bash
docker compose run --rm app python samples/make_samples.py
```

| Input | What it tests |
|---|---|
| `inputs/continuity.pdf` | Five pages where page breaks cut a table, a sentence (and a hyphenated word), a numbered list and a figure from its caption: tests the continuity note, the brief and the index |
| `inputs/report.pdf` | Digital PDF: a table, a bar-chart image, a formula line, a running header and footer, and a second page with a list and a table |
| `inputs/scanned_report.pdf` | The same report rasterised at 150 dpi in grey, rotated 0.8° and speckled. Docling's OCR misreads the formula's `g` as `q`; the copy-editor fixes it from the page image |
| `inputs/invoice.png` | An image with a ruled invoice table and totals: OCR plus table structure |
| `inputs/chart.png` | The chart used inside the other samples |
| `inputs/proposal.docx` | Word: title, headings, bullets, a table and an embedded image, rendered to PDF with LibreOffice |
| `inputs/board_deck.pptx` | PowerPoint: three slides with a table, a chart picture and speaker notes on every slide |
| `inputs/page.html` | A web page with a nav bar, a cookie banner and a footer around the content, plus a table, a list, a code block and a relative image |
| `inputs/booklet.epub` | A minimal valid EPUB 3 with two chapters (no page images, so Docling text and an AI brief, without copy-editing) |
| `inputs/update.eml` | An email with a plain-text body and an HTML alternative |
| Web URL | The Wikipedia article [Markdown](https://en.wikipedia.org/wiki/Markdown), printed to PDF with Chromium |

## Outputs

[`outputs/<name>/`](outputs/) holds `<name>.md`, one file per page or slide, `<name>.brief.md` and `<name>.index.md` (where the document has them), `<name>.docling.json`, `images/` (pictures and table screenshots) and `report.json` for each sample, produced by running [`examples.ipynb`](../examples.ipynb). [`outputs/docling-only/scanned_report/`](outputs/docling-only/scanned_report/) is the scan with `llm_layer=False`, for comparison with the copy-edited version.

## Timing and cost

Measured on 2026-10-04 by running the notebook in Docker on an Apple M5 (10 CPUs and 8 GB for Docker, no GPU) at `resolution="high"` and `batch_size=1`, with the copy-editor on `gpt-6-luna` at reasoning effort `low`. Costs are estimates from the prices in [`everymd/models.py`](../everymd/models.py) ($0.10 input, $0.01 cached input, $0.125 cache write, $0.50 output per 1M tokens, checked 2026-10-03). Times and costs include rendering, Docling, the copy-editor and the brief and index, not the one-time model download. Runs vary by a few seconds and a fraction of a cent.

| Sample | Type | Pages | Seconds | Est. cost (USD) | Tokens in / out |
|---|---|---|---|---|---|
| report.pdf | pdf | 2 | 31.7 | 0.0020 | 25,186 / 1,346 |
| continuity.pdf | pdf | 5 | 50.3 | 0.0039 | 60,402 / 2,618 |
| scanned_report.pdf | pdf | 2 | 40.8 | 0.0019 | 30,735 / 1,478 |
| scanned_report.pdf, Docling only | pdf | 2 | 18.2 | 0 | 0 / 0 |
| invoice.png | image | 1 | 12.0 | 0.0009 | 14,779 / 340 |
| proposal.docx | docx | 2 | 24.3 | 0.0017 | 23,359 / 1,193 |
| board_deck.pptx | pptx | 3 | 24.9 | 0.0020 | 28,873 / 919 |
| page.html | html | 2 | 25.9 | 0.0017 | 24,008 / 1,113 |
| Wikipedia URL | url | 9 | 164.5 | 0.0147 | 136,799 / 13,930 |
| booklet.epub | epub | 1 | 4.8 | 0.0003 | 1,558 / 299 |
| update.eml | email | 1 | 3.7 | 0.0003 | 1,534 / 195 |
| **All samples** | | 30 | 401 | **0.0294** | |

## Attribution

The web URL sample converts the Wikipedia article ["Markdown"](https://en.wikipedia.org/wiki/Markdown) by [Wikipedia contributors](https://en.wikipedia.org/w/index.php?title=Markdown&action=history), licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Its converted output in [`outputs/en.wikipedia.org-Markdown/`](outputs/en.wikipedia.org-Markdown/) is an adaptation (converted to Markdown and copy-edited by everymd on 2026-10-04) and is shared under the same licence.
