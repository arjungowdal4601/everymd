# Fix the real-document evaluation's findings, and read truly page by page

Goal: Arjun asked (2026-10-03, voice dictation, before going to sleep) to plan and fix, on my own and without asking, every issue the real-document evaluation found that can be fixed, with deep research, including the memory failure, and to make the reading truly "one page at a time" as he had asked in decision 0006.
Done when: the fixes are built, tested offline in Docker, re-run on the evaluation's real documents with the AI on, scored against the frozen gold, reviewed, documented, committed and merged into `main`.
Touches: decisions 0006, 0007 (updated by 0014), 0008, 0001 (no output policing: every fix is an input, Docling-handling or prompt change), 0004 (gpt-6-luna, low reasoning for tests). New decisions 0013-0016.

Where it stands (2026-10-04):
- Research: 7 agents (eval findings for PDFs and for other types, prompt practice on the web, code review, and Docling-only experiments on streaming/memory, links/headings and scans). Reports in the session scratchpad; the key numbers are in decisions 0013-0016 and the change log.
- Built on branch `fix/page-streaming-and-eval-findings`: one Docling conversion per page with `malloc_trim` after each page (stream.py); staged, atomic output with failure/killed-run reports (publish.py); PDF link annotations placed into Docling's text (links.py); document-wide heading levels from the PDF outline and dotted numbering (headings.py); sideways scans turned upright, 300-DPI OCR and table crops for scanned pages (scan.py, docling_step.py); HTML for spanning tables and kept table/picture footnotes (tables.py); sidecar joined from per-page documents (sidecar.py); rewritten prompts (prompts.py, brief.py); no copy-editor for inputs without page images; collision-safe folder names (names.py); clear errors for protected/damaged/empty files; URLs that are files are downloaded; Chromium waits for load (not network idle) and writes a PDF outline; Codex's three small fixes (HTTP errors, cache-write price, brief note).
- An adversarial review (50 agents) confirmed 38 defects in the first version; all fixed, with regression tests (tests/test_review_fixes.py).
- Measured so far, Docling only: continuity.pdf page 2 ends `irriga-`, page 3 starts `tion schedule changed`; census scan excerpt number recall p2 0.51 -> 0.87, p3 0.41 -> 0.73 after turning pages upright and 300-DPI OCR.

Results (2026-10-04, all at low reasoning, scored with the evaluation's own metrics against its frozen gold, link targets stripped because the gold was read from page images):
- The 78-page census scan completes (Docling only) at 3.3-3.5 GB, 4.3 GB peak; it ran out of memory at 5.45 GB before. 17 sideways pages turned upright.
- Mean composite over the 13 documents: old Docling 0.827, old everymd 0.799, new Docling 0.866, new everymd 0.892. Biggest gains: nist8425 0.864 -> 0.945, colbertv2 0.800 -> 0.864, ehshouseholds 0.859 -> 0.900, censusform 0.553 -> 0.669, populationchart 0.181 -> 1.0; qlora 0.896 -> 0.949 with the final prompt.
- Placeholder `#` links 24 -> 0; true page-break duplicates 12 -> 3; the e-book licence clause is correct again; chart labels stay as text and no values are invented.
- Worse than before on one document: the live Wikipedia URL (0.880 -> 0.835): with 30+ real links now in Docling's text, the copy-editor at low reasoning no longer rebuilds the infobox into a table. The saved copy of the same page improved (0.798 -> 0.872).
- Still open: the copy-editor sometimes restarts a list item continued from the previous page (nist 19/20); dense scanned tables remain the hardest case; production medium reasoning is untested.
- Spend for this work: about $0.40 estimated (corpus re-runs $0.35, live tests and notebook $0.05).
- Tests: 148 offline and 3 live pass in Docker.
