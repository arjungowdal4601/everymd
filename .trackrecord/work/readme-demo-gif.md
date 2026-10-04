# README demo GIF

Started 2026-10-04. Arjun asked for a fast-motion product demo for the top of the README, "think like Steve Jobs", "simple, it's not heavy", with the AI layer on top of Docling as the hero ("even the doc link gives all these things, but we are using an add-on AI layer there to help"). He approved the script after a web-research pass and said "go, build the GIF using hyperframes".

## Where it stands
- 2026-10-04 Arjun: "is it added to readme file? Now when I open this repo ... I should see this GIF going on. And you have to add to the GitHub certain tags ... study them like ponytail hyperframes and caveman ... how can I make this GitHub repo popular". Done on branch `docs/readme-demo-and-launch`:
  - README hero modelled on caveman, ponytail and hyperframes: a centred one-line promise, badges, the GIF (a poster for reduced motion), a three-number proof strip, a three-row before/after from the real sample, and a nav row.
  - The GIF, poster and a 1280x640 social preview are in `docs/assets/`. The HyperFrames source is in `videos/readme-demo/` (README there explains re-rendering; renders/ is ignored, and `videos` is excluded from the Docker build context).
  - The census and NIST images are credited in THIRD_PARTY.md (both U.S. Government works, public domain).
  - Topics, description, Discussions and social preview can't go on this private repo usefully (the public repo is a fresh one, decision 0017), so they are one `gh repo edit` command plus one upload in docs/release.md step 5.
- Updated 2026-10-04: PR #7 merged after both checks passed. The final audit caught “never above 4.3 GiB” against a measured 4.32 GiB peak. Private PR #8 corrected README and actual GIF to **4.32 GiB, Docling only**, changed “No lag” to “Steady memory”, added a Docker renderer and updated HyperFrames to 0.8.120; both checks passed before merge.
- Current video: 27.0 s, 324 frames, 960x540, 5,439,674 bytes, loops. Content derives from scanned_report and continuity samples, the NIST 8425 diagram description and the 78-page Statistical Abstract 1920 run with AI off. The actual rendered long-scan frame was visually checked. The larger GIF remains the only permitted file over 5 MB.
- Under Arjun's new [0020](../decisions/0020-codex-creates-and-publishes-fresh-repo.md), Codex renamed the original to [everymd-private](https://github.com/arjungowdal4601/everymd-private), kept it private, and staged a separate private [everymd](https://github.com/arjungowdal4601/everymd) from reviewed main. One main commit, no old history, no tags. Description, 20 topics, Issues/Discussions and the draft release are set. See [full checks](../../docs/private-launch-checks.md).

- 2026-10-04 (later) Arjun: "in the GIF video, I have seen that we have only mentioned as PDF ... we support docs, ... emails ... HTML support ... why these are not mentioned ... the repo readme looks ... more confined towards PDFs" and "the animation where it corrects ... looks good ... if you want you can add anything on top of it". He approved the plan ("go ahead, implement it"). On branch `docs/any-document-demo`:
  - GIF: the fix scene is unchanged. The hook now reads "Documents are messy." (census scans plus Word, slide, web page, invoice and email). A new 3.4 s beat "Any document in." shows eight real samples, each with its .md file and the change made (green = an AI change on that page; e-book and email in grey: "no page check · brief"). The long scene stays "Long PDFs. Steady memory." because memory was measured only on the 78-page PDF scan. 30.4 s, 960x540, 12 fps, 64 colours, 5.43 MB.
  - README: the tagline lists all formats; a format strip; a "## Any document in" table linking each format to its real sample output; Word and URL quick-start commands (both run, no AI); "What you get" uses `<name>`; speaker notes noted as .pptx only.
  - Topics in docs/release.md: `pdf-converter`, `pdf-extractor-rag` and `docker` swapped for `docx`, `pptx` and `html-to-markdown`.
  - A review panel (3 lenses plus a skeptic) confirmed 27 findings; all were fixed or reworded. Two code bugs it found were left out of scope and offered as separate tasks: an EPUB titled by its first chapter instead of dc:title, and lost code indentation across a page break in the page.html sample.

## Checked
- `npx hyperframes check` passes (57/57 WCAG AA). A four-lens review plus a skeptic confirmed 44 findings; all were fixed, and a recheck confirmed them.
- Fresh main archive: Docker build passed; 156 tests passed, 3 live skipped; no-AI sample completed with two page files and $0 estimated cost. 20 README paths resolve; source, privacy, credits and size checks pass. The upstream CLI cleanup warning is recorded in the full checks.
- Signed-in replacement page: GIF plays, static badges, metadata and topics render; tests badge has the expected private-repo message. Draft release is unpublished and no tag exists. Initial replacement Docker CI passed.
- GitHub blocks first social-preview upload and vulnerability reporting until public visibility. Private branch protection returns HTTP 403 requiring GitHub Pro or public visibility. The PNG is ready; no visibility workaround or plan purchase was performed.

## Next
1. Wait for Arjun's explicit “go public”; then Codex may follow phase C in [docs/release.md](../../docs/release.md). Only the replacement may become public; the original and PR #4 stay private. Retry the three blocked settings, verify anonymous installation/badges/security, annotate the tag and publish the existing draft.
2. New launch records remain private; sync to the replacement through its PR flow only if Arjun asks.
3. Launch ideas are in the conversation of 2026-10-04 (Show HN, r/LocalLLaMA and r/Rag, LinkedIn with the GIF, an agent skill later); no launch posts are authorized by this staging task.
