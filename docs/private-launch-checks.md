# Private launch checks — 2026-10-04

The source is ready and staged privately. Public visibility is awaiting Arjun's explicit “go public”. Three GitHub settings are blocked while private; this is not an all-pass public launch.

- Original: [everymd-private](https://github.com/arjungowdal4601/everymd-private), repository ID 1401458006, still private. Evaluation [PR #4](https://github.com/arjungowdal4601/everymd-private/pull/4) remains open at `5f9a66036e4e479cca82d8e9a0df9ca3b2494495`.
- Replacement: [everymd](https://github.com/arjungowdal4601/everymd), repository ID 1404144309, private. One `main` branch, one root commit `c70f25e93b0962e753139268e55b86c6d39e7c17`, no parents and no Git tags.
- Exported source: private main `82b433eee259497b9a4d7c063af1d4d1f237cf74`. Both trees equal `27ef1c39776a87a0e9efd3f442f21e7a301bada7`, proving identical tracked bytes and modes. Subsequent launch records are private-only.

## Check results

| Check | Result | Evidence |
| --- | --- | --- |
| Main updated; PR #7 merged | PASS | Both Docker checks succeeded before merge `cb2acac`. |
| Fix findings through private main PR | PASS | [PR #8](https://github.com/arjungowdal4601/everymd-private/pull/8), exact head `f3724fb`, both checks succeeded before merge `82b433e`. |
| Archive file count and size | PASS | 254 files, 12,374,643 bytes. |
| Files over 5 MB | PASS | Only permitted GIF: 5,439,674 bytes. Re-render is larger than the previous 4,901,276-byte GIF. |
| Excluded private/runtime directories | PASS | No root `eval/`, `.env`, `outputs/` or `.git` in the source archive. Tracked sample outputs intentionally retained. |
| Secret marker scan | PASS | Text and ASCII markers in binary assets scanned; only six expected regex-pattern hits in the two helpers. No values printed. |
| Personal home paths/Gmail | PASS | No matching markers in the archive. |
| Snapshot Docker build | PASS | From the archived tree, using cached image layers; no project secrets. |
| Snapshot offline tests | PASS | 156 passed, 3 live skipped, 81 warnings; 269.25 s. New Docling cache volume. |
| Snapshot no-AI CLI | PASS, warning | Two page files and stitched Markdown; complete status, 12.7 s, AI off, model null, estimated cost $0.00. Upstream cleanup warning after output writing; exit 0. |
| README paths and picture | PASS | 20 relative Markdown/HTML paths resolve; GIF and reduced-motion poster sources present. |
| Hero numbers and before/after | PASS after fix | Measured Docling-only peak 4.32 GiB; 30 sample pages / $0.0294; heading, description and formula rows match recorded sample outputs. |
| GIF | PASS | HyperFrames 0.8.120 browser check: zero errors/warnings; actual rendered frame reviewed. 27 s, 324 frames, 960×540, loop 0. Playing on signed-in GitHub page. |
| Credits | PASS | Census 1920 and NIST 8425 public-domain figures, Wikipedia CC BY-SA 4.0, HyperFrames Apache-2.0 and no runtime dependency. |
| 350-line command | PASS with 0018 | Only the two bundled helpers exceed it, each 1,182 lines. New renderer Dockerfile is 7 lines. |
| Original repo preservation | PASS | Same repository ID and private visibility; unchanged evaluation head; local origin now points to `everymd-private`. |
| Fresh replacement history and identity | PASS | One parentless commit, one main branch, zero tags; Arjun Gowda L with requested noreply address as author and committer. |
| Description, topics, Issues, Discussions | PASS | Exact requested description, 20 unique topics; both features enabled and visible. |
| Signed-in badges | PASS with expected limitation | Five static badges render; tests shows “repo or workflow not found” while private. README has no stars badge. |
| Initial replacement CI | PASS | [Docker workflow](https://github.com/arjungowdal4601/everymd/actions/runs/37189326583): 156 passed, 3 skipped, 81 warnings; 231.32 s, targeting root `c70f25e`. |
| Main protection | BLOCKED | GET and requested PUT after successful CI returned HTTP 403 requiring GitHub Pro or public visibility. No protection applied. |
| Vulnerability reporting | BLOCKED | Requested PUT returned HTTP 404; feature is for public repositories. |
| Social preview upload | BLOCKED | New private repo's General settings omits it. First upload requires public visibility. Ready PNG is 1280×640 and under 1 MB. |
| Release | PASS | [v0.1.0 draft](https://github.com/arjungowdal4601/everymd/releases/tag/untagged-704cd3d781e5a1277e3b) is unpublished, targeting root commit; no tag created. |
| Public visibility/anonymous install/tag publication | NOT RUN | Explicit phase-C gate; neither repo made public. |

## Evidence and limits

Correction CI: [push run](https://github.com/arjungowdal4601/everymd-private/actions/runs/37188189464) and [PR run](https://github.com/arjungowdal4601/everymd-private/actions/runs/37188193896). Both passed 156 tests, skipped three live tests. The local archive, audit manifest, runtime logs, MP4, rendered frame and GitHub screenshot are retained in the task's temporary launch workspace. No `.env` was opened, printed or passed from the working checkout.

The CLI warning comes from Docling's VLM-engine cleanup code (`code_formula_vlm_model.py` and related engine wrappers). It followed a successful complete report and is recorded without changing the dependency or masking the warning. The 81 test warnings are upstream deprecations. No production code or prompt changed in this task.

The former “never above 4.3 GiB” claim understated the logged 4.32 GiB peak and did not identify the Docling-only run. README and actual GIF were corrected, and “No lag” became “Steady memory”. The draft release similarly uses measured memory and qualified content/continuity wording, rather than promising no extraction loss. The 78-page run was not repeated; evidence is the private long-run log. Sample cost is an existing estimate, not independently verified billing.

GitHub's [vulnerability-reporting documentation](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository), [social-preview rules](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview) and [branch-protection plan requirements](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches) explain the blocked settings. Keep the repo private until instructed; after public visibility, retry and verify all three. No plan purchase is part of this authorization.

Deep Agents **0.7.21** is installed. Harness unchanged: explicit model plus `submit_page`, and a separate `submit_brief` run. Filesystem/execution tools and the general-purpose subagent are hidden because page editing only needs submitted page text; continuity note and previous-page context support continued tables/lists/headings. Offline fake-model tests prove wiring, not current model quality. No paid model calls; estimated new model spend **$0.00**. Production medium reasoning, anonymous installation, signed-out security access and public badges remain unverified in this phase.
