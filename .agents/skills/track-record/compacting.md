# Compacting the Track Record

Compaction keeps every record quick to use: keep what the next agent needs, move out what it doesn't. Nothing is ever deleted; moved material goes to `archive/` with a short summary that links to it.

There are no size thresholds. You judge. Compact when you notice a record has become slow to read or full of material that no longer helps (finished work, superseded detail, repetition, old change lines nobody needs day to day), or when the owner says "compact the track record". Do it yourself, without asking. The owner sees a dated COMPACT line in change.md and can recover anything from the archive.

## Recall first, then precision

Start by listing everything that might still matter, so nothing important is missed. Only then cut. Overly aggressive compaction loses subtle context whose importance only shows up later, so when in doubt, keep it or leave a one-line pointer to where it went.

**Always keep:**
- current truth;
- active work and next steps;
- every decision, and the owner's exact words;
- unresolved problems and open questions;
- anything still referenced from a record you're keeping.

**Move out:**
- finished work (`work/done/` items nobody is building on);
- superseded detail (old approaches, notes overtaken by a later decision);
- repetition (the same fact in several places: keep it in its one home, link from the others);
- old change lines, whole periods at a time (for example, everything before last month);
- stale notes that describe how things used to be.

## Rules

- **Never delete.** Move material into `archive/`, organized however makes sense (by month works well: `archive/2026-09/`).
- **Never rewrite an approved decision or an owner quote.** Decisions stay in `decisions/`; superseded ones are already marked by the decision that replaced them. Because decisions aren't edited, a decision that links to a work item keeps pointing at the old path once that item is archived. So in decisions, name work items rather than linking to them, and link only to other decisions.
- **Summarize what moved.** Each archive batch gets a `SUMMARY.md`: a few lines on what is there and why it's no longer needed day to day, plus links to every moved file. Anything still worth knowing goes in the summary, not just the link.
- **Log it.** Append one dated line to change.md, for example `- 2026-11-02 [COMPACT] Moved September work and change history to archive/2026-09/ ([summary](archive/2026-09/SUMMARY.md))`. Compaction itself isn't an IMPACT event.

## The helper does the moving

You decide what to move; `compact-move` moves it safely. It never deletes, keeps links pointing at the moved files, creates or updates the batch's `SUMMARY.md`, and appends the COMPACT line.

```bash
# See the plan first
python3 <skill>/scripts/trackrecord.py compact-move work/done --to archive/2026-09 --change-before 2026-10-01 --dry-run
# Then do it, with your own wording for the change.md line
python3 <skill>/scripts/trackrecord.py compact-move work/done --to archive/2026-09 --change-before 2026-10-01 --note "Moved September's finished work and change history to archive/2026-09/"
```

- Pass files or folders inside `.trackrecord/` to move them (decisions and the core records stay put).
- `--change-before DATE` moves change.md lines dated before DATE into the batch's own `change.md`; `since` still finds them.
- To compact STATE.md, vision.md or architecture.md, edit them: move the outgoing text into a file in the archive folder yourself, then run `compact-move --to archive/LABEL --summary-stub` to list it in the summary and log the COMPACT line.
- Re-running the same command changes nothing.

Then fill in the summary and run `trackrecord.py check`.

## Before and after

STATE.md before, after a busy month on Pantry:

```markdown
# State

Pantry: plan meals from what's in the cupboard. Private beta.

## In progress
- Shopping list export: CSV done 2026-09-30; PDF stopped at page layout.

## Done recently
- Accent-insensitive search (2026-10-02). Took three tries: first tried unaccent() in SQL, then
  normalising on write, finally normalising on both sides. Normalise-on-write was dropped because...
- Supabase migration (2026-09-20). Steps were: export users, recreate policies, ...(40 lines)...
- Recipe import from JSON-LD (2026-09-12) ...
- Firebase notes: the old custom-claims setup used ...

## Next
1. Fix PDF column widths.

## Decisions
- 0003 Supabase (replaces 0002). 0001 No ads.
```

After compacting:

```markdown
# State

Pantry: plan meals from what's in the cupboard. Private beta.

## In progress
- [Shopping list export](work/shopping-list-export.md): CSV done; PDF stopped at page layout.

## Next
1. Fix PDF column widths.

## Decisions that matter now
- [0003](decisions/0003-supabase-for-auth-and-data.md) Supabase for auth and data (replaces 0002).
- [0001](decisions/0001-no-ads.md) No ads.

## Recent
- 2026-10-02 Accent-insensitive search shipped.
- Older history: [archive/2026-09](archive/2026-09/SUMMARY.md).
```

What happened: the migration walkthrough and the search attempts moved to `archive/2026-09/state-notes.md`; the finished work items moved with `compact-move`; the Firebase notes went too, because decision 0003 already records why Firebase was left. The summary says so in three lines, and change.md got one COMPACT line.
