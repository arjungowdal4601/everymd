# Task for Codex: test everymd end to end on real documents, score it, and propose improvements

Historical evaluation task brief from 2026-10-03; its evaluation data lives only in the private evaluation branch, and these instructions are not a release workflow.

You are working in the everymd repo. everymd converts any document to Markdown for AI apps: Docling converts, then a LangChain Deep Agents "copy-editor" (OpenAI `gpt-6-luna`) compares each page image with Docling's Markdown and fixes what's wrong. It also writes per-page files, a continuity note per page, a brief, an index and, for single images, a caption. The audience is developers who are stuck getting correct information out of PDFs.

Your job has three parts:
1. **Test** the whole pipeline on real documents downloaded from the web, one or more per input type.
2. **Score** everymd's output against your own careful reading of each document, and against Docling alone.
3. **Review** the code for things to improve or remove, and report everything in one clear report.

Read this whole file before starting.

---

## 0. Before you start

1. Read `AGENTS.md` (project rules), then `.trackrecord/STATE.md`, and follow `.agents/skills/track-record/SKILL.md`. Read the decisions in `.trackrecord/decisions/` and never contradict one without asking Arjun.
2. Before touching anything in `everymd/agent.py`, `everymd/brief.py` or `everymd/models.py`, read `~/.claude/skills/deep-agents-builder/SKILL.md` as `AGENTS.md` section 5 says.
3. Run `git status`. The working tree may have uncommitted Track Record edits made by Claude on `main`; keep them. Create a branch `eval/real-documents` from `main` and include those edits in your first commit. Never commit to `main` and never merge.
4. Check that Docker works and the image exists: `docker compose run --rm app pytest -q` must pass (about 106 passed, 3 skipped) before you change anything. If it doesn't, stop and report.
5. You need network access (to download documents and to call the OpenAI API). If your sandbox blocks it, ask Arjun for approval rather than working around it.

## 1. Hard rules

- **Budget: $3.00 of OpenAI API spend in total, aim for under $1.50.** This covers only `gpt-6-luna` calls made by everymd; your own Codex usage doesn't count. Keep a ledger in `eval/results/budget.json`: after every `convert()` with the copy-editor on, add that run's `report.json` → `estimated_cost_usd`, plus 20% for the cache-write price the estimate leaves out. **Stop all paid runs when the ledger reaches $2.50**, and say so in the report. Before the first paid run, print your planned page count and estimated cost (about $0.001 per page at low reasoning, from `samples/README.md`).
- **Model:** `gpt-6-luna` only, with `EVERYMD_REASONING_EFFORT=low` for every run (decision 0004). Do not set `EVERYMD_MODEL` to anything else and do not call any other provider.
- **Secrets:** the key is in `.env` (gitignored). Never print, log or commit it. Never run `docker compose config` (it prints the environment).
- **Everything runs in Docker:** `docker compose run --rm app ...`. Don't install anything on the host. You may `pip install` scoring helpers inside a throwaway container run if really needed, but prefer what's already in the image (pypdfium2, Pillow, rapidfuzz may be absent; use `difflib` from the standard library if so).
- **Files stay at or under 350 lines** (`AGENTS.md` section 1); split by responsibility.
- **Don't police the model's output inside everymd** (`AGENTS.md` section 4, decision 0001). The scoring code you write is offline evaluation: it lives in `eval/`, reads finished outputs and never feeds back into the pipeline. Do not add validators, checks, retries or repair loops to `everymd/` because of what you find; propose prompt changes instead.
- **Downloaded documents:** only from reputable public sources over HTTPS, at most 50 MB each. Put them in `eval/inputs/` and add that folder to `.gitignore`. Never open Office files with macros enabled and never execute anything you download. Commit a document (or text copied from it) only if its licence allows redistribution (public domain, CC BY, CC BY-SA, Open Government Licence) and record the licence; otherwise commit only its URL and SHA-256.
- **Never commit** private documents, API keys, or large binaries other than licence-cleared inputs under 5 MB each.

## 2. Pick the documents (about 12 documents, about 150-250 pages in total)

Find real documents on the web that a developer would actually struggle with. Prefer public-domain or openly licensed sources: arXiv (CC BY papers), US government (GAO, NIST, NASA, Census and BLS reports are public domain), GOV.UK (Open Government Licence; it publishes DOCX, ODT and PPTX files), Wikimedia Commons (CC images), Project Gutenberg (EPUB), Internet Archive (public-domain scans), Wikipedia (CC BY-SA), Apache Software Foundation public mailing-list archives (for a real email; save one message as `.eml`).

Cover every type and every hard case at least once:

| Type | What to find |
|---|---|
| Digital PDF | A research paper with display formulas, multi-column layout and tables (arXiv) |
| Digital PDF | A government or financial report with a table that runs across a page break, footnotes, and running headers and footers |
| Long PDF | 30-60 pages (tests continuity notes, the brief, the index, time and memory) |
| Scanned PDF | A real scan, not a born-digital file: old typewritten or printed pages, ideally slightly skewed, with a table |
| Image | A photo or scan of a form, receipt or invoice (PNG/JPG) |
| Image | A chart or diagram with readable values |
| Word | A real `.docx` with headings, a table, a list and an image (GOV.UK publishes many) |
| Word, legacy | An `.odt` or `.rtf` if you can find one |
| PowerPoint | A real `.pptx` with a chart or table and speaker notes if possible |
| Web | One live URL (a Wikipedia article with tables) and one saved `.html` file |
| EPUB | A Project Gutenberg book (or a few chapters) |
| Email | A real public mailing-list message as `.eml`, ideally with an HTML part |
| Non-English | Optional: one PDF in another language |

Record each in `eval/sources.csv`: `id, type, url, licence, sha256, pages, why_chosen, downloaded_at`.

## 3. Make your own reference ("gold") reading, before looking at everymd's output

For each document, produce what a perfect conversion would be, page by page, from looking at the pages yourself:

1. **Get page images.** Inside Docker, render every page to PNG at about 150 dpi under `eval/work/<id>/pages/p0001.png` and so on:
   - PDFs and images: use pypdfium2 or Pillow.
   - Word, PowerPoint and HTML: print to PDF first with the same renderers everymd uses (`everymd.render.office_to_pdf` with LibreOffice, `everymd.render.web_to_pdf` with Chromium; both are in the image), then render that PDF.
   - EPUB and email: there are no pages; use the source text and HTML directly.
2. **Look at each page image** with your image-viewing tool. If you cannot view images, stop and tell Arjun; the method depends on it.
3. **Write the gold Markdown** for that page to `eval/gold/<id>/p0001.md`, following the conventions in `README.md` → "What you get" (Markdown tables, or HTML for merged cells; formulas as `$$...$$` / `$...$`; no running headers, footers or page numbers; headings at the right level; a continued table keeps its column names). Write it **blind**: do not open everymd's or Docling's output for that document until its gold is finished.
4. **Gold for long documents:** you don't need gold for every page. For documents over 15 pages, write gold for about 8 pages, choosing the hardest: tables across page breaks, formulas, figures, the first two pages and the last page. Note which pages have gold.
5. Also write, per document, a short **gold summary**: what the document is, and which pages contain which main topics. You'll use it to check the brief and the index.

## 4. Run everymd

For each document, run inside Docker with outputs under `eval/outputs/`:

1. **Docling only:** `convert(src, output_dir="eval/outputs/docling", resolution="high", llm_layer=False)`.
2. **everymd:** `convert(src, output_dir="eval/outputs/everymd", resolution="high", llm_layer=True, batch_size=1)` with `EVERYMD_REASONING_EFFORT=low`.

Record per run: seconds, pages, tokens, estimated cost, notes, peak memory (`docker stats` sampling is fine) and any exception with its traceback.

**Extra pipeline tests** (cheap; use small documents):

- `batch_size=3` vs `batch_size=1` on one 6-10 page PDF: quality and cost difference.
- `resolution="low"` vs `"high"` on the scanned PDF: quality and time difference.
- Re-running the same document into the same folder: stale page files, brief and index are removed or replaced correctly.
- Failure cases, which should fail clearly or degrade gracefully and never hang (Docling only is fine for most): a corrupted PDF, a password-protected PDF, an empty or zero-page PDF, a very large image (around 8000 px), an `.xlsx` (should be rejected), a URL that returns 404, a filename with spaces and non-ASCII characters, a folder path.
- Model switching, **offline only**: confirm `EVERYMD_MODEL` and `models.build()` behave as `README.md` describes without making any non-OpenAI call (the existing tests cover most of this; just confirm they pass).
- The full offline suite and the live tests: `docker compose run --rm app pytest -q` and `docker compose run --rm -e EVERYMD_LIVE=1 app pytest -q tests/test_live.py` (live tests cost under a cent; count them in the ledger).

## 5. Score

Score **Docling only** and **everymd** against your gold for every page that has gold, so the report shows what the copy-editor adds and where it breaks something.

**Automatic metrics** (write them in `eval/score/`, deterministic, standard library first):

- **Text similarity:** 1 − normalized edit distance after light normalization (collapse whitespace, unify quotes and dashes, strip everymd's invisible `<!-- ... -->` comments, the `![Table screenshot](...)` lines and `> **AI-generated description:**` lines). Report per page and per document.
- **Word recall and precision:** recall = gold words found in the output (missing content); precision = output words found in gold (invented or garbled content).
- **Tables:** cell-level F1 after parsing Markdown and HTML tables into grids; also whether a continued table has its column names.
- **Headings:** precision and recall of heading text, and whether levels match.
- **Formulas:** fraction of gold display formulas present in the output, comparing LaTeX with whitespace removed.
- **Numbers:** recall of every number in the gold (money, dates, percentages, measurements). Developers care most about this; wrong numbers are the worst error.

**Your judgment per page** (the automatic metrics miss meaning). Compare the page image, the gold, Docling's output and everymd's output, and record in `eval/results/<id>.json`:

- Errors, each with severity: **critical** (wrong number or value, invented content, lost table or section), **major** (wrong structure, broken reading order, missing paragraph or formula), **minor** (formatting, a heading level off by one).
- **Regressions:** things Docling had right that the copy-editor made worse. This matters as much as the fixes.
- **Fixes:** things Docling had wrong that the copy-editor fixed.
- Whether each picture got a sensible AI description, and the caption for single images.
- **Continuity:** did tables, lists, sentences and split words carry across page breaks?

**Adjudicate:** wherever your gold and everymd's output disagree, look at the page image again and decide who is right. If your gold was wrong, fix the gold and log it in `eval/results/adjudications.md`. Be strict and honest; you are both the reference and the judge, so state that limitation in the report.

**Brief, index and caption:** check every statement and every page reference in each `*.brief.md` and `*.index.md` against the document and your gold summary. Count correct, wrong and unsupported claims and wrong page references. Check that web pages got an outline and no index, and that EPUB and email briefs are one paragraph.

**Cost and speed:** cost per page, seconds per page (Docling vs copy-editor), peak memory.

## 6. Review the code: improve and remove

Read all of `everymd/`, `tests/`, the `Dockerfile`, `docker-compose.yml`, `README.md`, `samples/` and `docs/`. List:

- Bugs found by the tests above (with the failing document and page).
- Things to **remove**: dead code, unused settings in `config.py` or `models.py`, duplicated logic, stale docs (for example `docs/history/rag-foundation-plan.html` describes plans that are now built), test helpers nobody uses, dependencies nobody imports.
- Things to **simplify or improve**: files close to 300 lines (`everymd/api.py` is about 268), unclear names, prompt wording the scores show is weak (for example the known gap: joining a word split by a hyphen across pages), slow steps, error messages a developer wouldn't understand, README gaps for developers.

**What you may change yourself, on the branch:** clear bugs proven by a test, each fixed with a regression test in its own commit, and docs that are plainly out of date. **What you must only propose:** prompt changes, removals of features, anything touching a decision in `.trackrecord/decisions/`, new dependencies, and anything larger than about 50 lines. For each proposal give the evidence, expected impact and effort.

After any change: `docker compose run --rm app pytest -q` must pass, and the 350-line check in `AGENTS.md` must print nothing.

## 7. Deliverables

All on branch `eval/real-documents`:

- `eval/README.md`: the method in plain words, and how to re-run it.
- `eval/sources.csv`, `eval/score/` (scoring scripts), `eval/gold/` (only for licence-cleared documents), `eval/results/` (per-document JSON, `scores.json`, `budget.json`, `adjudications.md`). `eval/inputs/`, `eval/work/` and `eval/outputs/` are gitignored.
- **`eval/REPORT.md`**, written for Arjun in simple language:
  1. **Summary in five lines:** does the copy-editor help, by how much, where it fails, total spend.
  2. **Table per document:** type, pages, Docling-only score vs everymd score (text similarity, number recall, table F1), critical errors (Docling vs everymd), regressions, cost, seconds.
  3. **Table per type** (PDF, scan, image, Word, PowerPoint, web, EPUB, email): averages.
  4. **The 10 worst errors** with page reference and a short before/after snippet.
  5. **Regressions** the copy-editor introduced.
  6. **Brief, index and caption accuracy.**
  7. **Pipeline tests:** what passed and failed (batch size, resolution, re-runs, failure cases).
  8. **Bugs fixed on the branch** (commit list) and **proposals** ranked by impact, with evidence.
  9. **Budget:** ledger total and how many paid runs.
  10. **Limits of this evaluation:** you made the gold and judged it; small sample; low reasoning only.
- Track Record: add `.trackrecord/work/real-document-eval.md`, a line in `.trackrecord/change.md`, and update `.trackrecord/STATE.md`, as the track-record skill describes. Run `python3 .agents/skills/track-record/scripts/trackrecord.py check`.
- Commit with clear messages. Push the branch and open a pull request against `main` titled "Real-document evaluation" if `gh` is available, but **do not merge it**.

## 8. Handoff

End by stating, as `AGENTS.md` section 8 asks: the `deepagents` version, whether the harness changed (it shouldn't), how everything was verified in Docker, total API spend, and what you could not test or verify.
