# Real-document evaluation

Started 2026-10-03 by Codex on `eval/real-documents`.
Completed 2026-10-03: [Real-document evaluation PR #4](https://github.com/arjungowdal4601/everymd/pull/4) pushed, created against `main` and attached to the Codex chat. Left unmerged for Arjun's review.

Arjun requested implementation of the approved real-document evaluation plan:
paired Docling/everymd conversions, blind visual references, accuracy-first
rankings, code review, and a report. Paid calls are restricted to gpt-6-luna
at low reasoning; estimated spend aims below $1.50, stops at $2.50, and has a
$3 ceiling. No prompt changes or large production changes are approved.

## Verified
- Docker baseline: 106 passed, 3 live tests skipped, 22 deprecation warnings.
- Docker inspector: deepagents 0.7.21; existing submission-tool harness retained.
- Existing uncommitted owner records and task brief preserved in the first commit.
- 14 public inputs acquired; 239 physical pages plus pageless EPUB/email.
- 84 blind reference pages/units frozen before real conversions on 2026-10-03.
- Saved-HTML CSS localization confound corrected before freeze; licenses and
  original/localized source hashes recorded. Unclear-rights gold stays ignored.
- Final offline suite: 242 passed, 3 live skipped (75.10 seconds, 22 Docling
  deprecation warnings). Separate unchanged live suite: 3 passed (113.82 seconds).
- Failure matrix: 10 PASS, 2 FAIL, no hangs or paid calls. HTTP error-page bug
  and misleading interrupted-brief note fixed in separate commits. Larger
  failed-rerun and missing-report persistence fixes remain proposals.
- Docling-only corpus sweep: 13 successful inputs, one 78-page scan process
  killed without output. Cgroup OOM evidence and memory observations are logged;
  the precise expensive stage is not established.
- Paid primary sweep complete: 13 successful pairs, full 78-page scan fails
  during shared Docling preprocessing in both. Zero model calls on that scan;
  SIGKILL plus container OOM events, exact killed-PID attribution unverified.
- 76 scored pages/units: critical defects 18→5; five documents improve, six are
  unchanged, two worsen. Equal-document error rate rises 0.306→0.317; composite
  falls 0.824→0.796. Scores do not support universal improvement.
- Batch1/3, genuine-scan high/low, and successful cloned AI-off/on reruns done.
  Both scan excerpts have severe numeric defects. Manual live review finds a
  duplicated split-word continuation and changed brief threshold despite pytest
  assertions passing. Original artifacts remain isolated and preserved.
- Cache-write estimate omission reproduced and fixed in `23f0e38`. Original
  reports remain intact; append-only repricing of the first eight paid runs
  records $0.055007 buffered estimate, independently unverified. Later runs
  use the corrected estimator and are recorded in `eval/results/budget.json`.
- Bundled-helper size exception recorded in decision 0012.
- Final estimated ledger spend $0.293047 including 20% buffer; no unknown costs
  or outstanding reservations. Repricing consistency check unchanged for all
  21 nonzero paid runs; independent billing unverified.
- Report, document/format rankings, file matrix, worst errors, auxiliary ledgers
  and proposals are in `eval/REPORT.md`. Same Codex team authored and judged gold;
  source corrections and a slide severity reclassification preserve originals.

## Delivery and limits
Report, tooling and public-safe evidence are published on `eval/real-documents`.
PR #4 stays unmerged; no further implementation is required for this evaluation.
Arjun can review the report and choose larger proposals. Source authors
adjudicated after the freeze; independent human review, provider billing,
production medium reasoning, GPU and fresh-image rebuilds are unverified.
