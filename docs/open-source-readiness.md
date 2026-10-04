# Open-source readiness — 2026-10-04

Prepared privately on `chore/open-source-ready`. No model calls, tags, public
repo, visibility change or PyPI publication were performed. The existing private
repo keeps PR #4 and the evaluation branch. Follow-up owner authorization in
[0019](../.trackrecord/decisions/0019-merge-private-readiness-pr.md) allowed
[private PR #6](https://github.com/arjungowdal4601/everymd/pull/6) to merge on
2026-10-04 at `349689b`, after both GitHub Docker checks passed.

## Checklist and evidence

### Safety audit

- [x] All 29 commits reachable from `main` at `18627bc` audited: 414 unique
  blobs, 383 text blobs; no identifiable secret candidates. Scanner covers
  provider token formats, private-key headers, quoted/unquoted credential
  assignments and personal paths/emails. 37 matches were explicit placeholders,
  symbolic code references or the documented local Jupyter token. Values are
  never printed; binary blobs are inventoried rather than assumed plain text.
- [x] `.env` never committed; no `eval/` paths anywhere in main history.
  Entire `eval/`, outputs, secrets and caches are excluded from release builds
  and local output tracking. Committed generated sample outputs stay deliberate.
- [x] Personal-data check: one home path in the historical evaluation brief.
  Current archived text is sanitized; old history retains it. No personal email
  found; commits use the GitHub no-reply identity. Fictional sample people,
  addresses and example.org email addresses come from the generators.
- [x] All ten sample inputs regenerated in isolation and matched: exact image
  pixels; same PDF page text/rendered pixels; same Office/EPUB ZIP member content
  aside from timestamp-bearing core metadata; same decoded email headers/bodies;
  exact HTML. Only third-party sample output is the attributed Wikipedia article,
  including its derived images/JSON, under CC BY-SA 4.0.
- [x] All 26 direct requirements and bundled software/models inventoried in
  [THIRD_PARTY.md](../THIRD_PARTY.md). No restrictive direct Python licence
  identified. Binary/model redistribution needs upstream notices and applicable
  source offers; this is not a legal certification of every transitive component.
- [x] Twenty largest main-history blobs listed below; none over 5 MB.

### Open-source files

- [x] MIT licence already names **2026 Arjun Gowda L**, retained.
- [x] CONTRIBUTING: Docker tests, size rule, model freedom, safe conversion reports,
  local Claude/Codex hooks and links to project rules.
- [x] SECURITY: private GitHub reporting, early-version support and trusted-URL
  warning. Owner must enable private reporting on the future public repo.
- [x] Contributor Covenant 2.1 with its attribution, CC BY 4.0 notice and GitHub
  contact. Owner should confirm an available private conduct-reporting channel.
- [x] Bug/feature issue forms and PR template; no key requested.
- [x] Plain v0.1.0 changelog from the Track Record.
- [x] Docker CI on push/PR, project-secret-free and live tests disabled. Immutable
  action SHAs, Docker layer cache and Docling model-volume cache configured.
  YAML/schema-shape checks and isolated Docker cache restore/export pass locally;
  Both private GitHub CI runs passed: **156 passed, 3 live skipped**, including
  build and cache steps ([push run](https://github.com/arjungowdal4601/everymd/actions/runs/37184212961),
  [PR run](https://github.com/arjungowdal4601/everymd/actions/runs/37184209437)).
- [x] Proposed description: **Every document to Markdown that AI can use, with
  Docling and an optional page-image copy-editor.**
  Topics: `pdf, markdown, docling, ocr, llm, rag, document-parsing, langchain, deep-agents`.

### Internal working files

- [x] AGENTS, CLAUDE and tool/record folders retained. Hooks read local records and
  run local checks; no model or network call is part of their hook commands.
- [x] Historical plans moved to [docs/history](history/README.md), with archival
  notes and the home path removed. No internal file deleted.
- [x] Owner review flags: private-repo/evaluation links, earlier agent-generated
  plans and comparisons, quoted owner decisions, development incidents and
  evaluation spending remain in records. These are project history, not current
  public marketing claims. Do not silently publish them without owner review.

### Usability and verification

- [x] Thin CLI supports source, output root, resolution, AI off and batch size;
  prints artifacts and estimated cost. Eight new offline CLI contracts pass.
- [x] pyproject: Python 3.13+, runtime direct pins and optional dev pins match
  requirements.txt; wheel excludes samples, tests and evaluation. No PyPI upload.
- [x] README is 184 lines: source-backed example, free quick start, assistant
  setup prompt, three integration paths, outputs, measured sample costs and limits.
  Details moved to linked pages. No accuracy percentages or competitor claims.
- [x] Rebuilt-image fresh-clone Docker suite: **156 passed, 3 live skipped,
  81 upstream deprecation warnings, 285.35 seconds** (289.46 s shell wall time),
  zero paid calls. Earlier checkout run also passed in 181.82 s. Fake-model
  contracts prove wiring, not independent model quality.
- [x] Fresh private GitHub main clone with this branch merged locally: Docker
  build **130.05 s**, exact README CLI **20.78 s**, mounted-folder command
  **22.83 s**, Python snippet **17.84 s**. All conversions used AI off and both
  result reports record zero estimated model cost. See rehearsal details below.
- [x] Wheel and source distribution build in Docker; installation into a temporary
  container virtual environment succeeds. Console entry point and import from
  installed site-packages work outside the checkout with PYTHONPATH unset.
- [x] All **33** navigational relative documentation links resolve. Built image
  excludes `.env`, `.git`, evaluation and conversion outputs.
- [x] Docker Track Record checker passes with no likely secrets or broken links.
- [x] Size check explained: it lists only the two unchanged bundled 1,182-line
  Track Record helpers. Arjun's earlier approved exception is carried into
  [decision 0018](../.trackrecord/decisions/0018-bundled-track-record-size-exception.md).
  All other code files meet 350 lines; the literal command is not empty.

### Track Record and handoff

- [x] Decision 0017 supersedes 0002's distribution plan; existing evaluation repo
  stays private and Arjun publishes a new main-only repo. Git packaging approved,
  PyPI deferred. Decision 0018 preserves the prior bundled-helper exception.
  STATE, vision, architecture and change log updated.
- [x] Private [PR #6](https://github.com/arjungowdal4601/everymd/pull/6) created
  and attached, then merged after owner follow-up authorization and green CI.
  Local main updated; the fully merged release branch removed. Evaluation
  ref/PR #4 remain unchanged. Work record and decision 0019 record the follow-up.
- [x] Publication commands and owner decisions are in [release.md](release.md).
  Recommended new main snapshot avoids old home paths/private history; no history
  rewrite or public action is performed here.

## Branch review

Before this task: **2 local branches and 2 remote branches**, excluding the
`origin/HEAD` symbolic pointer. `main` contains merged PRs #1–#3 and #5.
Only `eval/real-documents` has unique work, intentionally excluded from main.
There were no redundant merged branches to delete at initial preflight. The
readiness branch started from updated main; initial handoff had three branches.
After owner-authorized PR #6 merge, all readiness commits were confirmed in main
and that branch was deleted locally/remotely. There are now **2 local branches
and 2 remote branches**: `main` and `eval/real-documents`. Main includes the
release preparation; no evaluation-only work was merged.

## Fresh-clone rehearsal

Rehearsed in `/tmp/everymd-readiness.cRBKgP/everymd` on Docker Desktop Linux
aarch64, cloning private GitHub `main` and merging the readiness commit locally.
Quick-start clone, directory change, build and free conversion were executed;
the setup prompt's template-copy step was also executed without reading `.env`.
The image is **1,250,049,582 bytes**; README's 5 GB figure is a disk allowance
for image, build and model caches, not a measured image size.

The build reused base/OS caches but rebuilt Python dependency and Chromium
layers. Conversions reused the existing Docling model-cache volume. These times
are not a cold-machine measurement. No host software or paid models were used.
The mounted `/data/report.pdf` correctly received a distinct hashed output
folder from the checkout's same-stem file.

Confusion observed: upstream model-configuration warnings and
`Error cleaning up engine: 'NoneType' object has no attribute 'info'` after the
output paths, despite exit code 0 and complete reports. The pipeline is unchanged
under this task's packaging-only scope. Native `pip install git+https://...` and
`playwright install chromium` were not rehearsed: the repository is private and
remote main does not yet contain packaging. Local Docker wheel installation
proves the backend/entry point; anonymous installation and native browser setup
remain owner checks after merge/publication. Paid prompt commands stayed skipped.

## Remaining owner decisions

Review internal history/docs, repository naming and a private GitHub contact for
conduct reports. The bundled-helper exception is already approved. Never change
this existing repo to public.
Public anonymous Git install, public Actions, native Mac/GPU execution and
independent model quality are not verified by this task.

Deep Agents **0.7.21** was inspected in Docker, including constructor signature,
default middleware and tools. Harness unchanged: explicit model with one
`submit_page` tool per batch plus final `submit_brief`; hidden filesystem,
execution and general-purpose subagent tools constrain the submission task.
Previous tail/continuity context and page notes support page breaks and summaries.

## Twenty largest main-history blobs

Distinct blobs, so older versions of a path can appear more than once.

| Blob | Bytes | File |
|---|---:|---|
| da52aadf2684 | 418,824 | samples/outputs/invoice/images/table-p0001-1.png |
| 4c664d3048c9 | 304,352 | samples/inputs/scanned_report.pdf |
| 4ef5bb35d5e4 | 237,269 | samples/outputs/continuity/continuity.docling.json |
| b98dd7127c35 | 237,242 | samples/outputs/continuity/continuity.docling.json |
| c486e93cfc0d | 206,923 | samples/outputs/en.wikipedia.org-Markdown/en.wikipedia.org-Markdown.docling.json |
| 2433691f0f8e | 206,351 | samples/outputs/en.wikipedia.org-Markdown/en.wikipedia.org-Markdown.docling.json |
| 874468d56913 | 206,225 | samples/outputs/en.wikipedia.org-Markdown/en.wikipedia.org-Markdown.docling.json |
| b7d77d669cc8 | 206,225 | samples/outputs/en.wikipedia.org-Markdown/en.wikipedia.org-Markdown.docling.json |
| 15c46ecd38a0 | 160,443 | samples/outputs/docling-only/scanned_report/images/table-p0001-1.png; samples/outputs/scanned_report/images/table-p0001-1.png |
| 78876a0faac2 | 147,653 | samples/outputs/continuity/images/table-p0001-1.png |
| f90d5dafadcc | 143,356 | samples/outputs/docling-only/scanned_report/images/image_000000_7ad22add76279dff9008e7df79f51f38987ce9f10ad8b935bd9d9b9ad8bdd796.png; samples/outputs/scanned_report/images/image_000000_7ad22add76279dff9008e7df79f51f38987ce9f10ad8b935bd9d9b9ad8bdd796.png |
| 9d5b3f204e7e | 125,858 | samples/outputs/docling-only/scanned_report/images/table-p0002-1.png; samples/outputs/scanned_report/images/table-p0002-1.png |
| 44bdde0b20dd | 115,605 | samples/outputs/invoice/images/table-p0001-1.png |
| 79e532b10ef2 | 94,995 | samples/outputs/en.wikipedia.org-Markdown/images/table-p0002-1.png |
| 97487f9dc929 | 73,693 | samples/inputs/invoice.png |
| bffaf2fdc6e4 | 69,852 | samples/outputs/docling-only/scanned_report/images/table-p0001-1.png; samples/outputs/scanned_report/images/table-p0001-1.png |
| 816ddd67fe95 | 66,991 | samples/outputs/report/report.docling.json |
| 0ce421ed58f0 | 66,968 | samples/outputs/report/report.docling.json |
| e8cbd50e82b6 | 66,782 | samples/outputs/report/report.docling.json |
| 8076a36d9108 | 66,733 | samples/outputs/docling-only/scanned_report/scanned_report.docling.json |
