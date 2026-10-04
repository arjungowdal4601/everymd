---
workflow: general-video
flow: automation
storyboard: no
message: "Docling reads your document; an AI editor checks every page against the original and fixes it."
destination: github-readme
aspect: 1920x1080
language: en
audience: developers stuck getting correct information out of PDFs
length: 30.4s
angle: before-and-after product demo
---

## Intent

A fast, silent, looping product demo at the top of the everymd README. Anyone should understand it at a glance, without having to think. The owner asked for it to be thought out like Steve Jobs would: show the result, not the tech. The hero is the AI layer added on top of Docling: "even Docling gives all these things, but we are using an add-on AI layer there to help". The AI editing animation must be clearly visible.

Approved script:
1. "Documents are messy." A messy pile: census scans, a Word page, a slide, a web page, an invoice image and an email, with the scanned report landing on top.
2. "Docling reads it." then "Almost right." Red underlines appear on the mistakes.
3. "AI checks every page." then "And fixes it." The red marks turn green: formula, heading, chart description.
3b. "Any document in." Eight real samples (PDF, scan, Word, slides, web, image, e-book, email) become their .md files, each with the change made to it.
4. "Nothing lost." Ticks on table, formula, image, chart.
5. "It remembers across pages." A note card hops from page 1 to page 2, and the table's headers return.
6. "Long PDFs. Steady memory." Pages stack up and a counter runs to 78; the measured Docling-only peak is 4.32 GiB.
7. "everymd", then "Every document. Ready for AI.", then "Open source".

## Assets

- ../../samples/inputs/scanned_report.pdf: the messy scanned page (page 1).
- ../../samples/outputs/docling-only/scanned_report/: Docling's real "before" text.
- ../../samples/outputs/scanned_report/: everymd's real "after" text and its changes.
- ../../samples/inputs/continuity.pdf and ../../samples/outputs/continuity/: the table continued across a page break, and the continuity note.

## Notes

- Every piece of text and every fix shown must come from real output files. No invented claims, no other tools named, no accuracy percentages.
- Silent, with sound-off design: the on-screen text carries the message, at most about 5 words per line, each line on screen for 2 seconds or more.
- One layout throughout: the page on the left and the Markdown on the right.
- Deliverable: a GIF of 5 MB or less at 960x540 for the GitHub README (rendered at 1920x1080, then downscaled), plus a poster PNG.
- Nothing personal on screen: no file paths, no keys, no terminal.

## Update 2026-10-04

Arjun: "in the GIF video, I have seen that we have only mentioned as PDF ... we support docs ... emails ... HTML support ... why these are not mentioned" and "the animation where it corrects ... that looks good ... if you want you can add anything on top of it". The fix scene is unchanged; the hook and the new "Any document in." beat cover the other formats. The long scene stays "Long PDFs." because memory was measured only on the 78-page PDF scan, and e-books and email are read whole.

