# 0001 Project coding rules: 350-line files, Docker, freedom for the LLM, harness then tools

Decided 2026-10-02. Written into `AGENTS.md` (shared by Codex and Claude Code; `CLAUDE.md` imports it).

- No code file over 350 lines; around 300 is the signal to split.
- The project is Dockerized; run, test and lint in the container.
- The model's output is not policed: no normalizers, regex or keyword checks, length caps, judging validators, repair or retry loops, or tight schemas. Behaviour is steered through the prompt. When code truly needs fields, use the framework's own structured output (`response_format`) with a loose schema.
- Build the Deep Agents harness first, then add tools one at a time.
- Rules live in AGENTS.md because the owner works with both Codex and Claude Code.

My reading: this is why everymd has no "diff guard" from the research report. SPEC.md doesn't include one, and it would police model output.

Approved by Arjun on 2026-10-02 in Claude Code (voice dictation, quoted as transcribed): "no file must have code more than 350 lines. Okay, it should be there around 300 to 350 lines." / "make it as a Docker, a Docker container. It has to be Dockerized." / "the output should not have any Python restrictions. Like the LLM should get as much freedom it, it needs. There should be no uh, schema enforcement." / "If, they, if we require any structured output, we have to use the framework example itself, like with structured output, something like that. So it is like we have to build the harness and then we have to add tools so that we have to follow this methodology." / "I'm going to use both codex and uh, cloud for development."
