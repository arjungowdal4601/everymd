# State (updated 2026-10-04)

everymd converts documents to Markdown, one page at a time: Docling reads a page, an optional Deep Agents copy-editor checks it against its image, then the page is written and released. Everything runs in Docker. This working checkout uses [everymd-private](https://github.com/arjungowdal4601/everymd-private), which must remain private. `main` is current. A separate [everymd](https://github.com/arjungowdal4601/everymd) is staged privately for publication.

## In progress
- [Private launch staging](../docs/private-launch-checks.md), authorized by [0020](decisions/0020-codex-creates-and-publishes-fresh-repo.md): fresh source snapshot of private main `82b433e`, one replacement main commit `c70f25e`, no old history or tags. Description, 20 topics, Issues, Discussions and a draft v0.1.0 release are set. Initial replacement Docker CI passed. No public visibility change or paid model calls.
- [README demo GIF](work/readme-demo-gif.md): now covers every format (hook, "Any document in." beat, README format table), on branch `docs/any-document-demo`. The replacement repo must be re-synced from main before going public, and its topics swapped (docx, pptx, html-to-markdown).
- [Evaluation PR #4](https://github.com/arjungowdal4601/everymd-private/pull/4) stays open and unmerged. Its branch head remains `5f9a660`; its third-party transcriptions stay private. Evaluation findings already landed on main; the evaluation tooling itself does not ship.

## Next
1. Wait for Arjun's explicit **“go public”**. Only the replacement repository may change visibility. Then enable branch protection and vulnerability reporting, upload the social preview, verify anonymous clone/Python 3.13 Git installation and badges, and create the annotated tag/publish the draft. Follow [docs/release.md](../docs/release.md).
2. GitHub currently blocks the first social-preview upload and vulnerability reporting while the new repo is private. Branch protection returns HTTP 403 requiring GitHub Pro or public visibility. No plan purchase or visibility workaround is authorized.
3. Arjun tries his documents privately. Known gaps: dense scanned tables, link-heavy infoboxes and continued list items at low reasoning; production medium reasoning is untested. Git installation is supported, PyPI remains deferred.
4. Update launch records in this private repo through PRs. Sync these new records to the replacement only if Arjun asks.

## Decisions that matter now
- [0020](decisions/0020-codex-creates-and-publishes-fresh-repo.md) Codex handles private launch setup; public visibility requires explicit “go public”.
- [0017](decisions/0017-open-source-on-github.md) Fresh public history from main files only; original evaluation repository stays private. Publication executor updated by 0020.
- [0018](decisions/0018-bundled-track-record-size-exception.md) Only the two bundled 1,182-line Track Record helpers are exempt from 350 lines.
- [0019](decisions/0019-merge-private-readiness-pr.md) PR #6's private merge was delegated and completed.
- [0013](decisions/0013-true-page-streaming.md), [0014](decisions/0014-page-text-as-printed.md), [0015](decisions/0015-no-copy-editor-without-page-images.md), [0016](decisions/0016-output-folder-names.md): true page streaming, printed fragments, image-required editing, separate output folders.
- [0011](decisions/0011-switchable-model.md), [0004](decisions/0004-gpt-6-luna-only.md): switchable model; default and tests use gpt-6-luna, low reasoning in development, medium in production.
- [0006](decisions/0006-page-by-page.md), [0007](decisions/0007-continuity-note.md), [0008](decisions/0008-brief.md), [0009](decisions/0009-index.md), [0010](decisions/0010-image-caption.md): page files, continuity, brief/index and image captions.
- [0001](decisions/0001-project-coding-rules.md), [0003](decisions/0003-docker-first-runtime.md), [0005](decisions/0005-track-record-setup.md): coding rules, Docker and Track Record. [0002](decisions/0002-private-github-repo.md) continues to protect the original repo.

## Recent
- 2026-10-04 Original repo renamed privately; replacement staged from the verified snapshot with one fresh commit. Both merged temporary branches removed after ancestry checks. `main` and private evaluation remain in the original repo.
- 2026-10-04 PR #8 merged after two passing Docker checks. Fresh main snapshot: 254 files, 12,374,643 bytes; 156 tests passed, 3 live skipped; no-AI sample complete, 12.7 s, $0 estimated model cost. Upstream Docling cleanup warning followed successful output writing.
- 2026-10-04 PR #7 merged after both Docker checks passed. README hero, GIF, poster, social-preview asset and credits included.
- 2026-10-04 PR #6 merged at 349689b after both Docker checks passed; release branch removed.
- 2026-10-04 Evaluation findings fixed: page streaming, links, headings, scans, prompts and robustness; 78-page Docling-only scan completed.
