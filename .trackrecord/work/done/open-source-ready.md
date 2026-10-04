# Prepare everymd for open-source release

Started 2026-10-04 by Codex on `chore/open-source-ready`, from updated `main`.
Arjun requested the supplied open-source readiness checklist plus branch cleanup.
Decision [0017](../../decisions/0017-open-source-on-github.md) records the boundary:
prepare a private, unmerged PR; Arjun publishes a fresh repository himself.

Verified at start: clean checkout; `main` includes merged PRs #1–#3 and #5.
Two local and two remote branches before this work: `main` and
`eval/real-documents`. There are no redundant merged branches to delete.
The evaluation branch has unique tooling and stays protected with PR #4.

History audit: all 29 commits reachable from `main` at `18627bc`; 414 unique
blobs, 383 text blobs. No identifiable secret candidates, committed `.env`,
`eval/` content or blobs over 5 MB. Known home path in the evaluation brief
is removed from the current archival copy; history still retains it.

Implemented: thin CLI with eight offline contracts, pinned packaging metadata,
concise README and guides, contributor/security/CI files, dependency notices,
sample provenance and publication steps. Fresh-clone Docker build passed in
130.05 s; CLI, folder mount and Python example passed with AI off and zero cost.
Wheel installation and console entry point work outside the checkout in Docker.
32 relative documentation links and isolated CI cache transfer pass. Rebuilt-image
offline suite: 156 passed, 3 live skipped, 81 deprecation warnings in 285.35 s.

Initially delivered in private, unmerged [PR #6](https://github.com/arjungowdal4601/everymd/pull/6).
Arjun subsequently delegated the merge under [0019](../../decisions/0019-merge-private-readiness-pr.md).
Both GitHub Docker checks passed (156 passed, 3 live skipped), then PR #6 merged
at 349689b on 2026-10-04. Local main fast-forwarded; the fully merged release
branch was deleted locally/remotely after an ancestry check. Two local/remote
branches remain: main and protected evaluation. Evaluation ref/PR #4 unchanged.
Anonymous public Git installation remains unverified. No paid calls or publication.

Limits: two unchanged bundled 1,182-line Track Record helpers exceed 350 lines
under Arjun's prior approved exception, carried into decision 0018. Report this
rather than claim an empty literal size check. Upstream cleanup warnings follow
successful free conversions; no pipeline or model behavior was changed.
