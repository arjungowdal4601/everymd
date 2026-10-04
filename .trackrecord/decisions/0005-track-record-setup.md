# 0005 Track Record setup: parent pointer, records in git, hooks on

Decided 2026-10-02 while installing Track Record 1.0.0 (commit 4db0c7e).

- Sessions often start in `~/Documents/projects/`, so that folder has an `AGENTS.md` (imported by its `CLAUDE.md`) pointing agents to `everymd/.trackrecord/STATE.md`.
- `.trackrecord/` is committed with the project.
- Hooks are installed for Claude Code (`.claude/settings.json`) and Codex (`.codex/hooks.json`). Codex runs them only after the owner trusts them with `/hooks`.

Approved by Arjun on 2026-10-02 in Claude Code, choosing "Yes, ~/Documents/projects/", "Commit with the project (Recommended)" and "Yes, Claude Code and Codex".
