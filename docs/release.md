# Publication procedure

Arjun delegated launch setup to Codex on 2026-10-04 in decision 0020. Phase A and
private staging are authorized. The replacement stays **private** until Arjun
explicitly says **“go public”** in this chat. The original
[everymd-private](https://github.com/arjungowdal4601/everymd-private) must remain
private permanently: deleting its evaluation branch would not hide PR #4's
third-party transcriptions.

See [verified launch checks](private-launch-checks.md). These updated instructions
and launch records are private-only; the replacement keeps its reviewed snapshot
unless Arjun asks to sync records through its normal PR flow. No PyPI release or
launch posts are included.

## Phase A: verify reviewed main

1. Update private main. PR #7 and the launch evidence correction in PR #8 were
   merged only after both respective Docker checks passed.
2. Export `git archive main` into a temporary directory. Inspect file sizes,
   secrets, personal paths/Gmail, README links and images, credits and code sizes.
   Exclude root `eval/`, `.env` and `outputs/`; approved tracked sample outputs stay.
   Only the two bundled Track Record helpers exceed 350 lines (0018).
3. Run from that archive, with no project secrets:

   ```bash
   docker compose build
   docker compose run --rm -e EVERYMD_LIVE=0 -e EVERYMD_REASONING_EFFORT=low app pytest -q
   docker compose run --rm app python -m everymd samples/inputs/report.pdf --no-ai
   ```

4. If a check fails, fix it through a private PR into main, then export and verify
   again. Never hand-patch the replacement tree. The memory claim now states the
   actual **4.32 GiB measured Docling-only peak**, rather than “never above 4.3”.

## Phase B: stage a fresh private repository

Already performed on 2026-10-04:

1. Rename the original without changing visibility and update this checkout:

   ```bash
   gh repo rename everymd-private --repo arjungowdal4601/everymd --yes
   git remote set-url origin https://github.com/arjungowdal4601/everymd-private.git
   ```

2. Create a **new private**, empty `arjungowdal4601/everymd`, without initializing
   another README or licence. Never make the original public.
3. Export reviewed main into a separate untouched directory and create one commit:

   ```bash
   launch_snapshot=$(mktemp -d -t everymd-launch)
   git archive main | tar -x -C "$launch_snapshot"
   cd "$launch_snapshot"
   git init -b main
   git config user.name "Arjun Gowda L"
   git config user.email "67260474+arjungowdal4601@users.noreply.github.com"
   git add .
   git commit -m "Publish everymd v0.1 source"
   git remote add origin https://github.com/arjungowdal4601/everymd.git
   git push -u origin main
   ```

   No `--all`, `--mirror`, private branches, PR refs or tags. Compare tree hashes.
   Actual source: private main `82b433e`; replacement root `c70f25e`; identical tree
   `27ef1c39776a87a0e9efd3f442f21e7a301bada7`.

4. Set metadata:

   ```bash
   gh repo edit arjungowdal4601/everymd \
     --description "Docling reads your document; an AI copy-editor checks every page against its image and fixes what's wrong. PDFs, scans, Word, slides and web pages to Markdown your AI can use, one page at a time." \
     --add-topic pdf,markdown,pdf-to-markdown,docx,pptx,html-to-markdown,document-parsing,document-parser,pdf-parser,docling,ocr,scanned-documents,table-extraction,rag,llm,ai-agents,deep-agents,langchain,python,developer-tools \
     --enable-issues --enable-discussions
   ```

5. Check the signed-in page: GIF animation, badges, description, topics, one branch
   and one commit. The tests badge's private-repo “repo or workflow not found”
   message is expected. Save an unpublished `v0.1.0` draft targeting the root
   commit; verify no Git tag is created.
6. Wait for the replacement's `tests` check to pass, then request main protection:
   require PRs and `tests`, disallow force-pushes/deletions, enforce for admins.
   For this solo-maintainer repo, a PR is required without requiring another
   person's approval. Store the desired API payload privately for retry.

Three GitHub restrictions prevent completing settings while this new repo is private:

- The vulnerability-reporting PUT returned HTTP 404. GitHub offers
  [private vulnerability reporting for public repositories](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
- General settings has no Social preview upload. GitHub permits a
  [first image upload only for a public repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview),
  or a private repo that already had an image. The ready asset is
  [social-preview.png](assets/social-preview.png), 1280×640 and under 1 MB.
- The protection API returned HTTP 403: “Upgrade to GitHub Pro or make this
  repository public to enable this feature.”
  [Private branch protection needs a supported paid GitHub plan](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches).

Keep it private and report these blockers. Do not temporarily expose it or buy a
plan to bypass the gate. **Stop after phase B and wait for “go public”.**

## Phase C: only after explicit “go public”

1. Change **only the replacement**:

   ```bash
   gh repo edit arjungowdal4601/everymd --visibility public --accept-visibility-change-consequences
   ```

2. Immediately apply main protection, enable vulnerability reporting and upload
   the social preview in Settings → General. Verify the applied settings.
3. In a fresh Docker environment without GitHub credentials, confirm anonymous
   HTTPS clone and Git installation into a Python 3.13 virtual environment. Use
   `python:3.13.9-slim-bookworm`; install Git inside the container, create the venv
   there, then `pip install git+https://github.com/arjungowdal4601/everymd`.
   Docker remains the complete supported conversion runtime. Keep conversions
   `--no-ai`; any paid call needs separate authorization.
4. In the replacement checkout, with the requested noreply identity, annotate and
   push the tag, then publish the existing draft:

   ```bash
   git tag -a v0.1.0 -m "everymd v0.1.0"
   git push origin v0.1.0
   gh release edit v0.1.0 --repo arjungowdal4601/everymd --draft=false
   ```

5. Verify badges and the security-report link while signed out. The current
   README has no stars badge; do not invent a successful stars-badge check.
6. Record the actual visibility-change time and verification in the private repo
   through a PR into main. Copy records to the replacement only if Arjun asks.
