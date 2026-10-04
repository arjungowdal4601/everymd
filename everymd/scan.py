"""Scanned pages: find the pages with no text layer and turn sideways ones upright before Docling reads them.

Docling's layout and table models read a page as it stands, so a table printed sideways comes out as
junk (the eval's 1920 census: 0 of 270 cells right on a sideways page, 170 once the page was upright).
The orientation comes from RapidOCR's own text detector and 0/180 line classifier, which Docling
already ships: on a sideways page most text boxes are tall, and the classifier says which way the text
reads. Pages are turned by setting the PDF's /Rotate on a temporary copy, which loses nothing. Pages
with a text layer are never touched, so born-digital PDFs pass through unchanged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

RENDER_SCALE = 2.0  # 144 DPI is enough to see which way text runs
MIN_BOXES = 10  # fewer text boxes than this: not enough evidence to turn a page


@dataclass
class ScanInfo:
    pages_without_text: set[int] = field(default_factory=set)  # 1-based
    rotated: dict[int, int] = field(default_factory=dict)  # page -> clockwise degrees applied
    notes: list[str] = field(default_factory=list)

    @property
    def any(self) -> bool:
        return bool(self.pages_without_text)


def pages_without_text(pdf: Path) -> set[int]:
    """1-based numbers of scanned or photographed pages: no text layer, but an image on the page.
    Blank pages (no text, no image) are not scans."""
    import pypdfium2 as pdfium
    import pypdfium2.raw as pdfium_c

    document = pdfium.PdfDocument(str(pdf))
    try:
        found = set()
        for index in range(len(document)):
            page = document[index]
            try:
                textpage = page.get_textpage()
                has_text = textpage.count_chars() > 0
                textpage.close()
                if not has_text and next(page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE]), None) is not None:
                    found.add(index + 1)
            finally:
                page.close()
        return found
    finally:
        document.close()


def _engine():
    from rapidocr import RapidOCR

    return RapidOCR(params={"Global.log_level": "error"})


def orientation(image, engine) -> int:
    """Clockwise degrees (0, 90, 180 or 270) that turn the page upright; 0 when there is too little text."""
    import numpy as np
    from rapidocr.main import RapidOCRError

    array, op = engine.preprocess_img(np.array(image.convert("RGB")))
    try:
        crops, det = engine.detect_and_crop(array, op)
    except RapidOCRError:  # no text boxes at all (a blank or picture-only page)
        return 0
    boxes = np.array(det.boxes) if det is not None and det.boxes is not None else np.zeros((0, 4, 2))
    if len(boxes) < MIN_BOXES:
        return 0
    width = np.linalg.norm(boxes[:, 1] - boxes[:, 0], axis=1)
    height = np.linalg.norm(boxes[:, 2] - boxes[:, 1], axis=1)
    tall, wide = height >= 1.5 * width, width >= 1.5 * height
    sideways = tall.sum() > wide.sum()
    chosen = [crop for crop, keep in zip(crops, tall if sideways else wide) if keep]
    labels = engine.text_cls(chosen).cls_res if chosen else []
    upside = sum(1 for label, score in labels if label == "180" and score > 0.9)
    upright = sum(1 for label, score in labels if label == "0" and score > 0.9)
    # RapidOCR turns tall crops 90 degrees counter-clockwise first, so on a sideways page "180"
    # means the text reads bottom to top.
    if sideways:
        return 90 if upside > upright else 270
    # On digit-heavy upright pages the 0/180 classifier is close to a coin flip: demand a clear margin.
    return 180 if upside >= 5 and upside >= 3 * upright else 0


def upright_pdf(pdf: Path, work: Path) -> tuple[Path, ScanInfo]:
    """A copy of the PDF with sideways or upside-down scanned pages turned upright (or the PDF itself)."""
    import pypdfium2 as pdfium

    info = ScanInfo()
    try:
        info.pages_without_text = pages_without_text(pdf)
    except Exception as exc:  # unreadable here: Docling reports it properly
        log.debug("Could not inspect the text layer: %s", exc)
        return pdf, info
    if not info.pages_without_text:
        return pdf, info
    try:
        engine = _engine()
    except Exception as exc:
        info.notes.append(f"Could not check page orientation ({type(exc).__name__}: {exc}).")
        return pdf, info
    document = pdfium.PdfDocument(str(pdf))
    try:
        for number in sorted(info.pages_without_text):
            page = document[number - 1]
            try:  # one odd page never stops the others from being checked
                angle = orientation(page.render(scale=RENDER_SCALE).to_pil(), engine)
                if angle:
                    page.set_rotation((page.get_rotation() + angle) % 360)
                    info.rotated[number] = angle
            except Exception as exc:
                info.notes.append(f"Could not check the orientation of page {number} ({type(exc).__name__}: {exc}).")
            finally:
                page.close()
        if not info.rotated:
            return pdf, info
        upright = work / f"{pdf.stem}.upright.pdf"
        document.save(str(upright))
    finally:
        document.close()
    turned = ", ".join(str(n) for n in sorted(info.rotated))
    info.notes.append(f"Turned scanned pages upright before reading them: {turned}.")
    return upright, info


def upright_image(path: Path, work: Path) -> tuple[Path, ScanInfo]:
    """An image turned upright (or the image itself). Images have no text layer: every frame is a scan.
    The turned copy keeps the image's DPI, so Docling sizes the page as the original."""
    from PIL import Image

    info = ScanInfo()
    try:
        with Image.open(path) as image:
            frames = getattr(image, "n_frames", 1)
            info.pages_without_text = set(range(1, frames + 1))
            if frames > 1:
                info.notes.append("Page orientation is not checked for multi-page images.")
                return path, info
            angle = orientation(image, _engine())
            if not angle:
                return path, info
            dpi = image.info.get("dpi")
            if dpi and angle in (90, 270):
                dpi = (dpi[1], dpi[0])
            turned = image.rotate(-angle, expand=True)  # PIL turns counter-clockwise
            upright = work / f"{path.stem}.upright.png"
            turned.save(upright, dpi=dpi) if dpi else turned.save(upright)
    except Exception as exc:
        info.notes.append(f"Could not check the image's orientation ({type(exc).__name__}: {exc}).")
        return path, info
    info.rotated[1] = angle
    info.notes.append(f"Turned the image {angle} degrees clockwise to read it upright.")
    return upright, info
