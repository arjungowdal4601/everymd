# Contributing

Use Python 3.13 through Docker. Clone the repo, then:

```bash
docker compose build
docker compose run --rm -e EVERYMD_LIVE=0 app pytest
```

These tests use scripted fake models and do not need a key. They verify wiring,
not model quality. Live tests cost money and require explicit approval.

Keep source, tests, scripts and Docker/YAML files at 350 lines or fewer; split by
responsibility around 300 lines. Two unchanged bundled Track Record helpers
currently exceed this limit; see the readiness report before changing them.
Follow [AGENTS.md](AGENTS.md), including the rule against grading, normalizing,
rewriting or retrying completed model output in application code. Put desired
model behavior in prompts and use framework mechanisms for required structure.

For a bad conversion, include the input type, resolution profile, model, what
went wrong, a redacted `report.json` and a screenshot of the affected source
page. Include a small input only when you have permission to share it. Remove
private text, URLs and identifiers before uploading. Never share an API key,
`.env`, passwords or access tokens. Use the
[bug template](.github/ISSUE_TEMPLATE/bug_report.yml).

The optional Claude Code and Codex hooks in `.claude/` and `.codex/` read
`.trackrecord/STATE.md` at session start and run a local record check at the end.
They use host Python 3 and Git, perform local file checks and emit reminders;
they do not call a model, publish anything or read your API key. Review and trust
hooks in your coding tool before enabling them. Conversion itself runs in Docker.

Open a focused PR with the behavior changed and the Docker verification command.
For security reports, follow [SECURITY.md](SECURITY.md). Community expectations
are in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
