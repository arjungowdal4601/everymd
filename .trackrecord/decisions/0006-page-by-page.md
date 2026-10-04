# 0006 Page by page: Docling one page at a time, one Markdown file per page

Decided 2026-10-02. everymd reads a document the way a person does: Docling processes one page at a time (each stage takes one page, at most one page waits between stages), the copy-editor already works one page at a time, and the output has one Markdown file per page (`name.p0001.md`, `.s0001.md` for slides) next to the complete stitched `name.md`. Documents without pages (EPUB, email) get only the complete file.

Measured on the 9-page web sample: one page at a time was 3-5% slower and used about 8% less peak memory (3.8 GB vs 4.1 GB); most memory is Docling's models.

Not yet decided: whether the stitched file should become optional (it is always written today), and whether Docling and the copy-editor should be interleaved page by page (today Docling finishes all pages before the copy-editor starts).

Approved by Arjun on 2026-10-02 in Claude Code (voice dictation, quoted as transcribed). His intent: "we'll read one page at a time. And then uh, we'll convert it to markdown file, and then if they need then we can provide a final uh, stitch of markdown file okay or else we'll provide a individual markdown files ... this is how humans read because that's why i wanted to mimic like this". Approval of the two changes: "yes, build both changes Yeah, this should um, exactly match how I need it. Okay, this is how you have to build."
