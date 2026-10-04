# AGENTS.md

Project rules for every AI coding assistant working in this repo (Codex, Claude Code, others). `CLAUDE.md` imports this file, so this is the single source of truth. Edit rules here, not there.

<!-- track-record:start -->
## Track Record

This project keeps a Track Record in `.trackrecord/`: where things stand, the owner's approved decisions, work in progress and a dated change log.

- At the start of every session, read `.trackrecord/STATE.md`.
- Follow the track-record skill (`.agents/skills/track-record/SKILL.md`; Claude Code also has it at `.claude/skills/track-record/`).
- Never contradict an approved decision in `.trackrecord/decisions/` or a rule in `.trackrecord/vision.md` without asking the owner first.
- After meaningful work, update the records as the skill describes.
<!-- track-record:end -->

## 1. File size: 350 lines maximum

- No code file (source, tests, scripts, Dockerfile, compose) may exceed **350 lines**. Treat **300 lines** as the signal to split; aim to land files between 300 and 350 only when the content is genuinely cohesive.
- Split by responsibility (one tool per module, one concern per file), never by arbitrary cutting.
- Check before finishing any task:

  ```bash
  find . -type f \( -name '*.py' -o -name 'Dockerfile*' -o -name '*.yml' \) -not -path './.venv/*' -not -path './node_modules/*' -print0 | xargs -0 wc -l | awk '$1 > 350 && $2 != "total"'
  ```

  Any output means a file is over the limit and must be split.

## 2. Everything runs in Docker

- The project must be Dockerized: `Dockerfile`, `docker-compose.yml`, `.dockerignore`.
- Run, test, and lint **inside the container** (`docker compose run --rm app pytest`, not host Python). The host needs only Docker.
- Pin the base image tag and pin dependency versions in a lockfile.
- Secrets (API keys) come from environment variables or an untracked `.env` file passed at run time. Never bake them into an image, commit them, or print them.
- Do not pull images, build, or run containers that spend money or touch external systems without the user's go-ahead.

## 3. Agent construction: harness first, then tools

- Use Python **LangChain Deep Agents** (`deepagents`, `create_deep_agent`). Do not hand-roll an agent loop, and do not rebuild what the harness already provides (filesystem, subagents, summarization, memory, approvals).
- Always pass `model=` explicitly.
- Order of work:
  1. Build the bare harness: `create_deep_agent(model=..., system_prompt=...)`. Run it.
  2. Add **one tool at a time**, each justified by a stated requirement.
  3. Add subagents, memory, middleware, or sandboxes only after a proven need.
- Put behavior, tone, coverage, exclusions, and quality bars in the **prompt**, not in Python.
- Verify against the installed `deepagents` version before designing (see section 5). Never code from memory; the package is pre-1.0 and changes weekly.

## 4. Give the LLM freedom: do not police its output

AI assistants tend to wrap model output in normalizers and auditors. **Do not.**

**Forbidden** (applied to anything the model wrote):
- Normalization, cleanup, trimming, or reformatting functions.
- Regex, keyword, heading, length, or "contains X" checks.
- Truncating, clamping, or capping output length in application code.
- Custom Pydantic validators that judge meaning, completeness, relevance, or correctness.
- Rejecting, repairing, rewriting, or re-asking a completed response because it looks wrong.
- Grader/rubric/"critic" loops, unless the user explicitly asks for one.
- Tight schemas: no enums, regex patterns, min/max bounds, or long required-field lists for model-authored text.

**Structured output** is allowed only when downstream code truly needs fields. Then:
- Use the framework's own mechanism (`response_format` on `create_deep_agent`) with a **minimal, loose** schema: few fields, plain types, descriptions instead of constraints.
- If framework parsing fails, surface the error. Do not hand-write a fallback parser or repair prompt.

**Still allowed in application code** (these are not output policing): authentication and authorization, validating untrusted *inputs* to tools, network and sandbox safety, atomic persistence, transport/retry handling for failed API calls, and logging.

## 5. Skill and reference material

- **Claude Code:** invoke the `deep-agents-builder` skill (installed at `~/.claude/skills/deep-agents-builder/`) before any agent work.
- **Codex and other tools without Claude skills:** read `~/.claude/skills/deep-agents-builder/SKILL.md` first, then only the files in `references/` the task needs (`harness.md`, `memory-context.md`, `production-validation.md`, `testing.md`, `sources.md`). If that path is missing, ask the user.
- Run the read-only inspector inside the container to get the real version, signature, and default middleware stack (no API key, no network):

  ```bash
  docker compose run --rm app python /path/to/inspect_deepagents.py --build
  ```

  Copy `inspect_deepagents.py` into the repo's `scripts/` (or mount the skill directory) so the container can reach it.

## 6. Testing

- Write offline contract tests with a scripted fake model (see the skill's `references/testing.md`). They prove wiring, not model quality. Say so when reporting.
- Never run paid model calls or evaluations without the user's approval.

## 7. Model policy (owner's decision, 2026-10-02)

- The copy-editor uses OpenAI **`gpt-6-luna` only**. Do not call, test with, or switch the default to any other model.
- **Testing and development runs use reasoning effort `low`.** The production default lives in `everymd/models.py`.
- The model is switchable from `everymd/models.py` or `EVERYMD_MODEL` (decision 0011). Keep every provider detail in that file; the default and all test runs stay `gpt-6-luna` unless the owner says otherwise.

## 8. Handoff

End each task by stating: the `deepagents` version used, the harness shape, why each non-default capability exists, how it was verified in Docker, and anything not verified.
