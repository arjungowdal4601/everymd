<!-- vision.md: why the project exists, who it's for, and the rules the owner cares about. Rules change only with the owner's approval; point each to its decision. examples: .agents/skills/track-record/examples.md -->

# Vision

**Every document → Markdown that AI can use.** Docling converts at full quality; a copy-editor agent then checks each page against its image and fixes only what's wrong. everymd rebuilds Arjun's older `doc_processing` (which sent every page to a vision model) around that split. Source: the agreed spec at `~/Documents/projects/personal-development/everymd/SPEC.md` (revised 2026-10-02) and the research in `personal-development/reports/Any document to Markdown.md`.

For: developers building apps who are stuck getting correct information out of PDFs and other documents (Arjun, 2026-10-03: "this is built for developers who are want to build the app but they are stuck in ... extracting the correct information from PDF itself"). Arjun is also the first user.

Rules from the agreed spec, which need Arjun's approval to change:
- One file or URL per call; no folders. Excel is skipped in v1 and rejected with a clear message.
- The user sees four controls and nothing more: `resolution`, `use_gpu`, `llm_layer`, `batch_size`. Docling's internals stay hidden.
- The copy-editor patches; it never retypes a page from scratch, and it describes only meaningful images.
- Every AI edit and description is labelled as such.
- Output: one Markdown file with YAML front-matter, invisible page/slide anchors, referenced image files and the Docling JSON sidecar, plus a cost log.
- Git-based Python installation is approved in [0017](decisions/0017-open-source-on-github.md); PyPI publication remains deferred.
- Later, not v1: Excel, folders, PyPI publication, audio/video, ZIPs, a local hard-page VLM, an MCP server.

Rules from Arjun's decisions:
- Code files stay under 350 lines; Docker-first; no policing of model output; harness first, then tools (decision [0001](decisions/0001-project-coding-rules.md), [0003](decisions/0003-docker-first-runtime.md)).
- The copy-editor uses `gpt-6-luna` only, with low reasoning for tests (decision [0004](decisions/0004-gpt-6-luna-only.md)).
- This evaluation repo stays private; a fresh open-source repo receives only `main` after owner publication (decision [0017](decisions/0017-open-source-on-github.md), superseding [0002](decisions/0002-private-github-repo.md)).
