# everymd v0.1 build

Goal: build everymd v0.1 from the build brief (`personal-development/everymd/BUILD-PROMPT.md`) and SPEC.md: the `everymd` module, sample inputs, `examples.ipynb` with committed outputs, tests, Track Record, then ship to the private repo.
Done when: pytest passes in Docker, the notebook runs top to bottom with nbclient, the manual quality check is written up honestly, no secrets are in the diff, and the repo is pushed (decision 0002).
Touches: decisions 0001–0005.

Finished 2026-10-02: shipped to https://github.com/arjungowdal4601/everymd (private), 8 commits on `main`. The first push was declined by GitHub's email privacy setting; the unpushed commits were re-authored with the GitHub no-reply address and pushed.

Checked:
- pytest in Docker: 73 passed, 1 skipped (the live test). The live test (`EVERYMD_LIVE=1`, gpt-6-luna, low reasoning) passed when run on its own.
- The notebook ran top to bottom with nbclient in Docker (366 s, no stderr or errors in any cell); every sample was copy-edited for $0.0153 in total (per-sample figures in `samples/README.md`).
- Manual review: the scan with and without the copy-editor (formula `q` fixed to `g`, chart described, tables intact), the PPTX speaker notes (all three slides), and the HTML page (navigation, cookie banner and footer removed; its chart now loads after the fix).
- Secret scan: the key value and key patterns appear nowhere outside `.env`; `.env` is gitignored.

Not checked:
- Native macOS runs (Apple Vision OCR, MPS, host Chrome): the code paths exist but were not run.
- Legacy DOC/PPT/RTF/ODT/ODP and MSG inputs: no samples.
- Long documents (50+ pages) and memory use beyond the samples.
- Copy-editor quality beyond the samples; there is no evaluation set yet.
