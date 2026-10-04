# 0003 Docker-first runtime

Decided 2026-10-02. Tests and the examples notebook run in a Linux container that includes LibreOffice and Playwright's Chromium. Inside Docker on a Mac there is no GPU and no Apple Vision OCR, so Docling runs on CPU with RapidOCR. The code still uses Apple Vision and MPS when run natively on macOS.

This resolved the build brief's LibreOffice question without a host install: LibreOffice lives in the image, so Word and PowerPoint files get real page images.

Rejected: Mac-native first with a host LibreOffice install; Mac-native without LibreOffice (Office files in text-only mode).

Approved by Arjun on 2026-10-02 in Claude Code, choosing "Docker-first (Recommended)" to the question "Your AGENTS.md says everything runs in Docker, but the build brief relies on Mac-only features (Apple Vision OCR, MPS GPU, your Chrome). Which runtime comes first?" Earlier the same day: "It has to be Dockerized." (see 0001).
