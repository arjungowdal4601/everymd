# 0008 Brief: page notes, then one final pass (module 4)

Decided 2026-10-03. While reading, the copy-editor writes a one- or two-sentence page note for every page (what it covers, terms it defines, tables and figures). After the last page, one text-only Deep Agents call reads every page note and continuity note plus the first two pages in full, and writes `name.brief.md` (what this is, summary with page references, key terms, best for / not covered) through a `submit_brief` tool. The brief is saved exactly as written. Web pages get an outline and no page references; EPUB and email get a one-paragraph summary; single images get no brief (module 6 captions them).

The brief is made whenever the AI layer is on, so no fifth control was added and the vision rule "four controls, nothing more" stands. This was my choice of default (Arjun asked to build it without picking between a fifth `rag_layer` setting and always-on); it costs about $0.001 per 5-page document at low reasoning. Revisit if Arjun wants a switch.

Approved by Arjun in Claude Code (voice dictation, quoted as transcribed): "Okay, I want you to plan and implement the module four. Okay."
