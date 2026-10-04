# everymd runtime: Docling, LibreOffice and headless Chromium in one CPU image.
FROM python:3.13.9-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/cache/huggingface \
    PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright

# LibreOffice renders Office files to PDF; metric-compatible fonts keep rendered
# Office pages close to the originals. OCR uses Docling's bundled RapidOCR models.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libreoffice-writer-nogui libreoffice-impress-nogui \
      fonts-dejavu-core fonts-liberation2 fonts-crosextra-carlito fonts-crosextra-caladea \
      libgl1 libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch first (Docker on a Mac has no GPU access), then everything else.
COPY requirements.txt requirements.lock ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --index-url https://download.pytorch.org/whl/cpu -c requirements.lock torch torchvision \
 && pip install -r requirements.txt -c requirements.lock

RUN playwright install --with-deps chromium

# A named Jupyter kernel, so editors show "everymd (Docker)" in their kernel list.
RUN python -m ipykernel install --name everymd --display-name "everymd (Docker)"

COPY . .
CMD ["python", "-m", "pytest", "-q"]
