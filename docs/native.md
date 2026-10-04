# Native setup (optional)

Docker is the supported complete runtime. Native setup needs Git, Python 3.13+
and system dependencies; install those yourself before these commands.
On macOS, LibreOffice provides Office page images and installed Chrome can
render web pages. Apple Vision OCR and MPS can be used outside Docker.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/arjungowdal4601/everymd
playwright install chromium
python -m everymd path/to/document.pdf --no-ai
```

Linux Chromium may also require OS libraries; Playwright's installation guide
lists them. LibreOffice is needed for DOC/PPT and for page-image editing of other
Office formats. OCR, fonts, browser and rendering can differ from Docker.

Do not install system software through an assistant without approving it.
This preparation verifies Docker, not native Mac/GPU performance or every
provider. GitHub HTTPS installation becomes available without authentication
only after the owner creates the public repository.
