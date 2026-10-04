# 0017 Open-source on GitHub

Decided by Arjun on 2026-10-04. Supersedes [0002](0002-private-github-repo.md)
for the distribution plan: everymd will be an open-source GitHub project.
This existing repository remains private because evaluation branches and PR
history contain third-party transcriptions. A fresh public repository receives
`main` only after owner review; evaluation branches and PR #4 are excluded.

Arjun's supplied task brief: "Arjun, the owner, has decided to publish everymd
on GitHub as an open-source project." / "Nothing becomes public in this task."
/ "The public repo gets main only." / "Arjun publishes it himself."

Scope from Arjun's brief: prepare `chore/open-source-ready`, a thin CLI and installable
Python metadata, documentation, history/rights checks and Docker offline
verification. No paid calls, visibility changes, new repository, public posts,
tags, PyPI publication or merge. Keep the pipeline, prompts and default model
unchanged; retain the evaluation branch and PR #4.

This approves Git-based Python installation, updating the v0.1 vision's former
"not a pip package for now" restriction. PyPI publication remains deferred.
