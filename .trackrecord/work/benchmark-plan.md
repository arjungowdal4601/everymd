# Benchmark: everymd against open-source converters

Goal: Arjun wants a benchmark (accuracy percentages and specific cases) showing where everymd stands against the major open-source document-to-Markdown converters, as the project's selling point (2026-10-03, voice dictation). Later step he mentioned: one public document per input type. Not interested in testing open-source models as everymd's own model for now.
Done when: shortlist agreed, benchmarks chosen per type, runs done in Docker and results published.
Touches: decision 0004 (gpt-6-luna for runs), 0001 (no output policing).

Update 2026-10-03: Arjun decided not to benchmark for now ("let's not do comparison then"). Kept for reference.
Where it stopped (2026-10-03): research only (3 web-research agents). Shortlist and benchmark options presented to Arjun; nothing chosen or run.
Findings worth keeping:
- No public benchmark compares a pipeline alone with the same pipeline plus an LLM fix; plain Docling scores low (olmOCR-Bench 50.3 per Marker's README, Jul 2026; ParseBench 50.65), and GPT-6 Luna alone scores 59.32 (low) / 64.21 (high) on ParseBench. "Docling vs Docling + copy-editor" is the clearest story.
- PDF: olmOCR-Bench (1,403 PDFs, ODC-BY, unit tests), OmniDocBench v1.6 (1,651 pages, data non-commercial, saturated at the top), ParseBench (~2,078 enterprise pages, Apache-2.0, run by LlamaIndex), DP-Bench via opendataloader-bench (Docling, Marker, MinerU, PyMuPDF4LLM, Unstructured, MarkItDown side by side).
- HTML: WebMainBench (HTML to Markdown ground truth), WCXB 2026, ScrapingHub AEB (archived). Office/EPUB: only AgentDocBench (38 docs, run by a competitor). Email: nothing public.
- Risk to measure: LLM correction can over-correct clean text (ICDAR 2026 HIPE-OCRepair) and damage tables (arXiv 2607.13347).
- The leading VLM parsers (PaddleOCR-VL, MinerU2.5, olmOCR 2, Chandra 2, dots.ocr) need an NVIDIA GPU; on the Mac use their published scores.
