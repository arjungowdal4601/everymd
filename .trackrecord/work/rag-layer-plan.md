# RAG layer plan: page files, table screenshots, captions, brief, summary, index

Goal: make everymd a foundation for RAG systems. Arjun asked (2026-10-02, voice dictation) for a "brief" or summary of big documents built page by page like his framework memory (vectorless_rag_v1), an index ("from which page number to which page number what contains"), captions for single images, a summary rather than an index for HTML pages, page-wise output plus the complete output, and table/image screenshots linked. He asked for deep research and an HTML explainer first, with no code changes.
Done when: Arjun has decided the open questions in the plan and the approved features are built and tested in Docker.
Touches: vision rule "four controls, nothing more" (a `rag_layer` switch would need a new decision), decisions 0001 (no output policing) and 0004 (gpt-6-luna only).

Where it stopped (2026-10-02): research done (21-agent workflow: 8 angles, each fact-checked; 3 designs; judge; critic). Plan is archived at `docs/history/rag-foundation-plan.html`. This entry describes the historical proposal; current implemented modules are recorded in later decisions.
Update 2026-10-02: per-page files and one-page-at-a-time Docling are built (decision 0006). Arjun found the plan pages hard to follow; explain it one module at a time (modules: 1 converter, 2 page splitter, 3 reading memory, 4 brief, 5 index, 6 captions).
Update 2026-10-03: modules 2 (table screenshots) and 3 (continuity note) built in PR #2. Next to explain: module 4 (brief).
Update 2026-10-03: module 4 (brief) built in PR #2 (decision 0008): page notes plus one final pass, no new control. Next to explain: module 5 (index).
Update 2026-10-03: module 5 (index) built in PR #2 (decision 0009), in the brief's call. Next to explain: module 6 (captions).
Update 2026-10-03: module 6 (single-image caption in front-matter) built in PR #2 (decision 0010). All six modules built. Update 2026-10-03: notebook and samples/outputs re-run with all modules; merged into main. Not done: JSON index; captions for pictures inside documents; long-document and medium-reasoning runs.
Next: Arjun answers the decisions in section 11 of the plan; record each as a decision in his words; then build v0.2 (page files, table screenshots, `position` note, heading hierarchy check, report provenance, kept rendered PDF, clean re-runs, web metadata) one change at a time.

My reading of the research (not approved): notes per page plus one final synthesis is the recommended way to build the brief (as v1 wrote its Document Summary); a living brief file edited every page is the alternative to A/B in a paid run.

Checked: sources and claims via fact-check agents (39 confirmed, 40 confirmed with corrections, 1 wrong and dropped). Not checked: any model behaviour or cost for notes, brief or index; medium-reasoning cost; Docling heading hierarchy on the samples.
