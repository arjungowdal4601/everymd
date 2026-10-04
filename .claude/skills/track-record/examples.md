# Track Record examples

These are illustrations, not templates. Two fictional projects run through them: **Pantry**, a small web app for planning meals from what's in the cupboard, and **Harbour Lights**, a short documentary being edited in a video folder. The people, quotes and dates are invented. Borrow whatever shape helps; leave out whatever doesn't.

## STATE.md

A lean "you are here" for Pantry might look like this. A fresh agent can read it in a minute and carry on.

```markdown
# State (updated 2026-10-03)

Pantry: plan meals from what's already in the cupboard. Web app in private beta with 40 households.

## In progress
- [Shopping list export](work/shopping-list-export.md): CSV works; PDF stopped at page layout (columns overflow on A4).
- [Pantry photo scan](work/photo-scan.md): spike only; owner hasn't approved the vendor yet.

## Next
1. Fix the PDF column widths, then ask Maya to try an export on her phone.
2. Write up the two photo-scan vendors for Maya to choose.

## Decisions that matter now
- [0003](decisions/0003-supabase-for-auth-and-data.md) Supabase for auth and data (replaces 0002).
- [0001](decisions/0001-no-ads.md) No ads, ever.

## Recent
- 2026-10-02 Accent-insensitive pantry search shipped.
- 2026-09-30 CSV export shipped.
```

## vision.md

Purpose, audience and the rules the owner cares about. A rule backed by a decision points to it.

```markdown
# Vision

Pantry helps busy households cook from what they already have, so less food goes in the bin.

For: people who plan the week's meals on a Sunday and shop once.

Rules that need Maya's approval to change:
- No ads, ever (see decision 0001).
- Recipes stay readable without an account.
- Household data never leaves the EU (see decision 0003).
```

## architecture.md

Only what an agent can't work out from the files in a minute.

For Pantry:

```markdown
# Architecture

- Row-level security is on for every table. The client only ever holds the anon key; anything needing the service key runs in an edge function.
- `pantry_items.quantity` is text, not a number ("half a bag"). Parsing happens in `lib/quantity.ts` only.
- Recipe import scrapes JSON-LD; sites without it fall back to the manual form. Don't add per-site scrapers.
```

For Harbour Lights, the same file describes how the folder is organized:

```markdown
# Architecture

- `footage/` is read-only camera originals; never re-encode in place. Proxies live in `proxies/`.
- Scenes are numbered by story order (S01–S09), not shoot order. The timeline in `project/harbour-lights.drp` follows the same numbers.
- Render settings are locked: 3840×2160, 25 fps, ProRes 422 HQ for masters, H.264 at 20 Mbps for review copies in `renders/review/`.
- Music cues are licensed per scene. Moving a cue to another scene needs a new licence; check `music/LICENCES.md`.
```

## decisions/

One decision or pivot per file, numbered so it can be referenced. The approval is the owner's exact words, with who and when.

A decision and the earlier one it replaced, for Pantry:

```markdown
# 0003 Supabase for auth and data

Decided 2026-09-20. Replaces 0002 (Firebase).

We move auth and data to Supabase, in its EU region. Firebase's document model made shared household lists awkward, and we need row-level rules per household.

Rejected: staying on Firebase with custom claims (more code, harder to audit); self-hosted Postgres (Maya doesn't want to run servers).

Approved by Maya on 2026-09-20 in Claude Code: "Yes, move to Supabase. EU region only, please."
```

```markdown
# 0002 Firebase for auth and data

Decided 2026-08-11. Superseded by 0003 on 2026-09-20.

Start on Firebase because the prototype already used it.

Approved by Maya on 2026-08-11 in Codex: "Fine, keep Firebase for now."
```

A decision migrated from older records, where the original wording wasn't kept:

```markdown
# 0001 No ads

Recorded 2026-08-02 in the old project notes, migrated 2026-10-01.

Pantry never shows ads.

Approval: the old notes say Maya decided this on 2026-08-02, but Maya's exact words weren't recorded then. Confirmed by Maya on 2026-10-01 while migrating, in Claude Code: "Yes, still no ads. That one doesn't change."
```

Until an owner confirms a migrated decision like this, it stays a proposal.

For Harbour Lights, a creative decision is recorded the same way:

```markdown
# 0004 Open on the pier shot

Decided 2026-09-30. The film opens on the long pier shot (S01, take 3) with no title card for the first 20 seconds.

Rejected: a cold open on the interview, which tested as "too newsy".

Approved by Sam on 2026-09-30 in Claude Code: "Open on the pier. Don't cut it, even if it feels slow."
```

## work/

One piece of work per file. This one stopped mid-way, and says honestly what was and wasn't checked:

```markdown
# Colour grade, scenes 1–3

Goal: a consistent warm grade for the harbour scenes, matched to the reference stills Sam picked.
Done when: S01–S03 match the stills side by side, and Sam signs off on a review render.
Touches: decision 0004 (the pier shot keeps its full length, so grade the whole take).

Where it stopped (2026-10-01): S01 and S02 graded. S03 has mixed daylight and sodium light; started a power window on the lamp posts, not finished.
Next: finish the S03 window, then render `renders/review/S01-S03_grade_v1.mp4`.

Checked: S01 and S02 compared against the stills on the scopes. Not checked: nothing rendered yet, so Sam hasn't seen any of it.
```

When it's finished or dropped, the file moves to `work/done/` with a closing line saying which.

## change.md

One line per meaningful change, each starting with its date, linking to the work item or decision behind it. A short tag helps searching.

```markdown
- 2026-09-20 [DECISION] Moved auth and data to Supabase, EU region ([decision](decisions/0003-supabase-for-auth-and-data.md))
- 2026-09-30 [ADDED] CSV export for shopping lists ([work](work/shopping-list-export.md))
- 2026-10-02 [FIXED] Pantry search ignores accents, so "creme" finds "crème" ([work](work/done/accent-search.md))
- 2026-10-03 [COMPACT] Moved August work and change history to archive/2026-08/ ([summary](archive/2026-08/SUMMARY.md))
```

## IMPACT.md

One honest line each time the records helped, or failed to help. Name the agent. Misses matter as much as wins.

```markdown
- 2026-09-24 [GUARD] Codex stopped before adding a sponsored-recipe slot and quoted decision 0001; Maya said no.
- 2026-09-28 [HANDOVER] Claude Code picked up the CSV export from STATE.md after a Codex session and continued without questions.
- 2026-10-01 [WHY] Answered "why did we leave Firebase?" from decision 0003 in one search.
- 2026-10-02 [MISS] Cursor added a Firebase analytics snippet despite decision 0003; caught in review, removed.
```
