---
format: 1920x1080
duration: 30.4s
message: "Docling reads your document; an AI editor checks every page against the original and fixes it."
arc: Hook → Problem (almost right) → Solution (AI fixes) → Proof (nothing lost, memory, long PDFs) → Brand
audience: developers stuck getting correct information out of PDFs
mode: autonomous
---

Design (no frame.md; house style):
- Concept: a red pen that turns green. Docling's draft gets red marks, and the AI pass turns each one green. Every scene speaks that one colour language.
- Palette: bg #0b0f0d, surface #141a17, line #26312c, fg #eef3ef, muted #9aa8a0, accent (AI / fixed) #57d68d, mistake #ff6b5b (only for mistakes).
- Type: Montserrat 900 for statements, JetBrains Mono 400/700 for Markdown and labels (the human voice against the machine voice).
- Focal: the headline anchored top-left. The stage below has the page on the left and the Markdown on the right. Background: a dot grid plus one accent glow, drifting slowly (persistent in index.html).

## Frame 1 — Hook

- scene: A crooked pile of mixed documents (scans, Word, slide, web page, invoice, email); "Documents are messy."
- duration: 3s
- status: animated
- transition_in: cut
- src: compositions/01-hook.html
- motion: kinetic-type-beats (Hook); spring-pop-entrance (pages); match-cut handoff, where the scan page straightens into Frame 2's page slot

## Frame 2 — Docling reads it, AI fixes it

- scene: Docling's Markdown types in; red marks show the mistakes; the AI scan band runs down the page and each red mark turns green
- duration: 11s
- status: animated
- transition_in: cut (match cut)
- src: compositions/02-fix.html
- motion: agent-progress-theater (A, checklist theater); discrete-text-sequence (typing and fixes); css-marker-patterns / hw-underline (red squiggles); ambient-glow-bloom traveling sweep (the AI scan band); spring-pop-entrance with the success-check (green ticks)

Captions: "Docling reads it." → "Almost right." → "AI checks every page." → "And fixes it." Every line and every fix comes from samples/outputs/docling-only/scanned_report and samples/outputs/scanned_report.

## Frame 2b — Any document in

- scene: Eight real samples (PDF, scan, Word, slides, web, image, e-book, email) become their .md files; each card shows the change made, from that sample's report.json (e-book and email: read natively, brief written, no page check)
- duration: 3.4s
- status: animated
- transition_in: cut
- src: compositions/02b-any.html
- motion: spring-pop-entrance (staggered group); discrete reveal of output lines

## Frame 3 — Nothing lost

- scene: Four tiles (tables, formulas, images, charts) each earn a green tick
- duration: 3s
- status: animated
- transition_in: cut
- src: compositions/03-kept.html
- motion: spring-pop-entrance (staggered group); success-check

## Frame 4 — It remembers

- scene: The page 1 table's column names ride a note card to page 2, where Docling had made row S29 the header; the header returns and S29 drops into the body
- duration: 4.6s
- status: animated
- transition_in: cut
- src: compositions/04-memory.html
- motion: spring-pop-entrance (card); nudge-curve (card travel); discrete-text-sequence (header insert)

## Frame 5 — Long PDFs

- scene: Pages stream out one by one as page files, the counter runs to 78, and the memory line stays flat
- duration: 2.4s
- status: animated
- transition_in: cut
- src: compositions/05-long.html
- motion: counting-dynamic-scale (without the scale growth); waterfall-entry (page files); svg-path-draw (flat memory line)

## Frame 6 — Brand

- scene: The everymd wordmark, "Every document. Ready for AI.", "Open source · built on Docling"
- duration: 3s
- status: animated
- transition_in: cut
- src: compositions/06-end.html
- motion: titlecard-reveal (one restrained move, then a still hold)
