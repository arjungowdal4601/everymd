---
name: track-record
description: Keeps a project's Track Record in .trackrecord/ (where things stand, the owner's approved decisions in their own words, work in progress, a dated change log and an honest impact log) so any agent can pick up the work, respects what the owner decided, and can answer what happened and why. Use when starting work in a folder that has .trackrecord/, before changing anything a recorded decision or vision rule covers, after meaningful work, when the owner approves, rejects or reverses a decision, when asked what happened, when or why, and when asked to start, update, check or compact the Track Record.
metadata:
  version: 1.0.0
---

# Track Record

Keep the owner's decisions honoured across agents, make handover instant, and keep an honest record of how the project grows. What you write is testimony for the next agent: short, true, and in the owner's words where it matters.

## The records (.trackrecord/)

- **STATE.md**: where things stand. Read it first. Keep it current and quick to read.
- **vision.md**: why the project exists, who it's for, and the rules the owner cares about.
- **architecture.md**: how it's built or organized. Only what the files can't tell.
- **decisions/**: one decision or pivot per file, numbered (0001, 0002…).
- **work/**: one piece of work per file. Finished or dropped ones move to work/done/.
- **change.md**: one line per meaningful change, starting with its date. Search it; don't read it whole.
- **IMPACT.md**: each time these records helped, or failed to help.
- **archive/**: what compaction moved out. Never bulk-read it.

Shape each record however serves the project. Good examples of each: [examples.md](examples.md).

## Two things that are never flexible

1. **Approval is the owner's exact words, with who and when.** Without them a decision is only a proposal. Silence is never approval.
2. **Every change.md line starts with its date** (YYYY-MM-DD).

## Working with it

- **Start**: read STATE.md, then tell the owner in one line where things stand and what's next. If STATE.md looks out of date against the files or git, say so.
- **Find things**: search change.md, decisions/ and work/ for the topic and open only what's relevant. For "what happened since…", run `python3 <skill>/scripts/trackrecord.py since <date> --topic <word>`.
- **Guard**: before changing something, check whether a decision or vision rule covers it. If the request contradicts one, stop and ask: name the decision, explain the conflict, and offer options (keep it, supersede it, or make a one-off exception that you record). Never silently override.
- **Decisions**: when the owner approves, rejects or reverses something, record it with their exact words and the date. An approved decision isn't rewritten; a change of mind becomes a new decision that says what it supersedes.
- **After meaningful work**: update the work item (where it stopped, the next step, what was actually checked and what wasn't), add a dated change.md line that links to it, update STATE.md, and update architecture.md if the structure changed.
- **Impact**: when the records really helped (a guard catch, a smooth handover, a "why" answered) or you missed something they held, add one honest line to IMPACT.md with your agent name.
- **Compact**: when a record has become slow to read or holds things the next agent won't need, compact it yourself, without asking, following [compacting.md](compacting.md). The owner never manages upkeep; that's your job.
- **Check**: run `trackrecord.py check` after updating records. Fix any likely secret or broken link it reports; everything else is information for your judgment.

`<skill>` is whichever installed copy exists: `.claude/skills/track-record` or `.agents/skills/track-record`. The helper is optional; everything works as plain Markdown without it.

## Never

Store secrets, personal data, raw transcripts or invented intent. Mark your own interpretations as yours ("my reading:"), never as the owner's. Don't record greetings, read-only answers or trivial edits.

## Starting a Track Record

If asked to start one, run `trackrecord.py init`, then draft vision.md with the owner (purpose, audience, rules that need approval) and write STATE.md.
