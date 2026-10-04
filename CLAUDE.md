# CLAUDE.md

@AGENTS.md

## Claude Code specifics

- The rules above in `AGENTS.md` apply in full. Codex also reads that file, so keep shared rules there and put only Claude-specific notes here.
- Before any agent, tool-calling, or harness work, invoke the `deep-agents-builder` skill via the Skill tool. It is installed globally at `~/.claude/skills/deep-agents-builder/`.
- Prefer the dedicated Read/Edit/Grep tools over shell equivalents, and run project commands through `docker compose`, not host Python.
- When a change would push a file past 300 lines, split it in the same change rather than leaving it for later.
