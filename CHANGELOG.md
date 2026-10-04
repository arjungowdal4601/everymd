# Changelog

## 0.1.0 — 2026-10-04

Initial version, prepared for an owner-controlled GitHub release.

- Converts PDFs, scans, images, Office documents, web pages, EPUB and email
  to Markdown through Docling.
- Reads page-based inputs one page at a time and writes page files plus a
  stitched document, extracted images, table screenshots and Docling JSON.
- Optional Deep Agents copy-editor checks pages against their images,
  labels its changes and writes a brief and page index.
- Uses a switchable model, defaulting to `openai:gpt-6-luna`, and reports
  tokens, estimated cost and elapsed time.
- Adds page streaming, heading/link recovery, scan orientation handling,
  isolated output folders and preserved failure reports.
- Adds a thin CLI, Python packaging metadata, Docker-only CI and contributor
  documentation. No PyPI package or public release is published by this task.

This is early software. See the README for known limits.
