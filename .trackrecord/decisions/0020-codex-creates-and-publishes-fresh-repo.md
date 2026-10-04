# 0020 — Codex creates and publishes the fresh public repo

Approved by Arjun Gowda L, 2026-10-04, in the attached launch brief: "creating a new repo and adding things like keeping old one as private, and all these things will be handled by Codex" / "after the ChatGPT does that [the checks], I think we can go public."

The same brief explicitly says:

> The new repo is created PRIVATE and stays private until Arjun says "go public" in this chat. Report and wait at the end of phase B.

This updates 0017's assignment of publication to Arjun: Codex may perform final checks and private staging now, then publish only after the explicit go-public instruction. It does not authorize making the original repository public, merging PR #4, publishing to PyPI, buying GitHub Pro or posting launch messages.

Done 2026-10-04: PR #7 and the launch evidence correction in PR #8 merged after both respective checks passed. The original repository (ID 1401458006) was renamed to `everymd-private`, without changing private visibility. Its evaluation PR #4 and branch head were preserved. A separate private `everymd` (ID 1404144309) was created from verified main, with one main commit `c70f25e`, no parents and no tags. Metadata and an unpublished v0.1.0 draft are set.

Visibility change: **not performed**. Initial replacement Docker CI passed. GitHub blocks vulnerability reporting and the first social-preview upload until public visibility; private branch protection GET and the requested PUT after successful CI returned HTTP 403 requiring GitHub Pro or public visibility. These are deferred without changing visibility to work around them.

The replacement starts from the frozen, reviewed snapshot. These subsequent decision and handoff records stay in the private repository; copy them into the replacement through its PR flow only if Arjun asks. See [launch checks](../../docs/private-launch-checks.md) and [publication procedure](../../docs/release.md).
