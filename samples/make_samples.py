"""Create every sample input for everymd. All content is original and safe to commit.

Run it inside the container:

    docker compose run --rm app python samples/make_samples.py

This file builds the images and PDFs; doc_samples.py builds the Office, web, ebook
and email samples. Each sample exercises something specific (see samples/README.md).
"""

from __future__ import annotations

import random
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import continuity_sample
import doc_samples

INPUTS = Path(__file__).resolve().parent / "inputs"

# Shared, invented figures for the "water sensor pilot" used across samples.
REGIONS = [("North", 120, 150), ("South", 95, 88), ("East", 130, 162), ("West", 80, 97)]


def font(size: int) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def make_chart(path: Path) -> None:
    """Grouped bar chart with the values printed on the bars."""
    width, height = 1000, 620
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((width // 2, 30), "Sensors online by region", font=font(34), fill="black", anchor="mm")
    left, bottom, top = 110, height - 90, 90
    draw.line([(left, top), (left, bottom), (width - 40, bottom)], fill="black", width=3)
    for value in range(0, 201, 50):
        y = bottom - (bottom - top) * value / 200
        draw.line([(left - 8, y), (left, y)], fill="black", width=2)
        draw.text((left - 14, y), str(value), font=font(20), fill="black", anchor="rm")
    slot = (width - 40 - left) / len(REGIONS)
    for i, (region, q1, q2) in enumerate(REGIONS):
        x0 = left + i * slot + slot * 0.18
        for j, (value, colour) in enumerate([(q1, "#4C72B0"), (q2, "#DD8452")]):
            bx = x0 + j * slot * 0.32
            by = bottom - (bottom - top) * value / 200
            draw.rectangle([bx, by, bx + slot * 0.28, bottom], fill=colour)
            draw.text((bx + slot * 0.14, by - 14), str(value), font=font(20), fill="black", anchor="mm")
        draw.text((left + i * slot + slot / 2, bottom + 26), region, font=font(24), fill="black", anchor="mm")
    for k, (label, colour) in enumerate([("Q1 2026", "#4C72B0"), ("Q2 2026", "#DD8452")]):
        lx = width - 300 + k * 140
        draw.rectangle([lx, 70, lx + 22, 92], fill=colour)
        draw.text((lx + 30, 81), label, font=font(20), fill="black", anchor="lm")
    img.save(path)


def make_invoice(path: Path) -> None:
    """A text-heavy invoice image with a ruled table, for OCR."""
    img = Image.new("RGB", (1240, 1000), "white")
    draw = ImageDraw.Draw(img)
    draw.text((80, 70), "INVOICE", font=font(64), fill="black")
    meta = ["Invoice no. INV-2026-0142", "Date: 15 September 2026", "Bill to: Riverside Community Garden"]
    for i, line in enumerate(meta):
        draw.text((80, 170 + i * 40), line, font=font(28), fill="black")
    draw.text((760, 90), "Greenfield Sensors Ltd.\n12 Mill Lane, Leeds", font=font(26), fill="black", spacing=8)
    columns = [80, 600, 760, 960, 1160]
    rows = [
        ("Description", "Qty", "Unit price", "Amount"),
        ("Soil moisture sensor", "12", "18.50", "222.00"),
        ("Solar charger", "3", "42.00", "126.00"),
        ("Installation (hours)", "6", "35.00", "210.00"),
    ]
    top, row_h = 340, 62
    for r, row in enumerate(rows):
        y = top + r * row_h
        if r == 0:
            draw.rectangle([columns[0], y, columns[-1], y + row_h], fill="#E8E8E8")
        for c, cell in enumerate(row):
            draw.text((columns[c] + 14, y + row_h / 2), cell, font=font(28), fill="black", anchor="lm")
    bottom = top + len(rows) * row_h
    for r in range(len(rows) + 1):
        draw.line([(columns[0], top + r * row_h), (columns[-1], top + r * row_h)], fill="black", width=2)
    for x in columns:
        draw.line([(x, top), (x, bottom)], fill="black", width=2)
    totals = [("Subtotal", "558.00"), ("VAT 19%", "106.02"), ("Total due (EUR)", "664.02")]
    for i, (label, amount) in enumerate(totals):
        y = bottom + 50 + i * 46
        draw.text((760, y), label, font=font(28), fill="black")
        draw.text((1146, y), amount, font=font(28), fill="black", anchor="ra")
    draw.text((80, 900), "Payment within 30 days. Thank you for supporting local growers.", font=font(24), fill="black")
    img.save(path)


def _header_footer(canvas, doc) -> None:
    """Running header and footer, which the copy-editor should drop."""
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.drawString(2 * cm, A4[1] - 1.2 * cm, "Water Sensor Pilot - internal report")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page} of 2")
    canvas.restoreState()


def make_report(path: Path, chart: Path) -> None:
    """Two-page digital PDF: table, chart image, formula line, list, second table."""
    styles = getSampleStyleSheet()
    formula = ParagraphStyle("formula", parent=styles["Normal"], fontName="Times-Italic", fontSize=15, alignment=TA_CENTER)
    grid = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDDDDD")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ])
    rows = [["Region", "Q1 sensors", "Q2 sensors", "Change"]]
    rows += [[name, str(q1), str(q2), f"{(q2 - q1) / q1:+.1%}"] for name, q1, q2 in REGIONS]
    story = [
        Paragraph("Quarterly Field Report: Water Sensor Pilot", styles["Title"]),
        Paragraph(
            "This report summarises the second quarter of the community water sensor pilot. "
            "Volunteers installed soil moisture sensors in four regions and logged how many stayed online.",
            styles["BodyText"],
        ),
        Paragraph("1. Results by region", styles["Heading2"]),
        Table(rows, colWidths=[4 * cm, 3.2 * cm, 3.2 * cm, 3 * cm], style=grid),
        Spacer(1, 0.4 * cm),
        RLImage(str(chart), width=13 * cm, height=13 * cm * 620 / 1000),
        Paragraph("Figure 1: Sensors online per region, Q1 and Q2 2026.", styles["Italic"]),
        Paragraph("2. How growth is measured", styles["Heading2"]),
        Paragraph("Quarter-on-quarter growth for a region is computed as:", styles["BodyText"]),
        Paragraph("g = (Q2 &minus; Q1) / Q1 &times; 100", formula),
        Paragraph("A negative value means sensors went offline faster than new ones were installed.", styles["BodyText"]),
        PageBreak(),
        Paragraph("3. Next steps", styles["Heading2"]),
        ListFlowable(
            [ListItem(Paragraph(text, styles["BodyText"])) for text in (
                "Replace the 7 failed sensors in the South region before October.",
                "Add a second solar charger to every West site.",
                "Publish the anonymised readings as open data in Q4.",
            )],
            bulletType="bullet",
        ),
        Paragraph("4. Budget for Q3", styles["Heading2"]),
        Table(
            [["Item", "Cost (EUR)"], ["Replacement sensors", "1,295"], ["Solar chargers", "840"], ["Volunteer training", "600"], ["Total", "2,735"]],
            colWidths=[7 * cm, 4 * cm],
            style=grid,
        ),
        Spacer(1, 0.4 * cm),
        Paragraph("The pilot steering group will review these figures at its next meeting.", styles["BodyText"]),
    ]
    SimpleDocTemplate(str(path), pagesize=A4, title="Quarterly Field Report").build(
        story, onFirstPage=_header_footer, onLaterPages=_header_footer
    )


def make_scan(source_pdf: Path, path: Path) -> None:
    """Rasterise the report like a cheap office scan: grey, slightly rotated, a little noisy."""
    rng = random.Random(42)
    pages = []
    pdf = pdfium.PdfDocument(str(source_pdf))
    for page in pdf:
        img = page.render(scale=150 / 72).to_pil().convert("L")
        img = img.rotate(0.8, resample=Image.BICUBIC, expand=False, fillcolor=255)
        img = img.filter(ImageFilter.GaussianBlur(0.5))
        pixels = img.load()
        for _ in range(img.width * img.height // 400):
            x, y = rng.randrange(img.width), rng.randrange(img.height)
            pixels[x, y] = rng.choice((90, 160, 200))
        pages.append(img)
    pdf.close()
    pages[0].save(path, "PDF", resolution=150, save_all=True, append_images=pages[1:])


def main() -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    chart = INPUTS / "chart.png"
    make_chart(chart)
    make_invoice(INPUTS / "invoice.png")
    make_report(INPUTS / "report.pdf", chart)
    make_scan(INPUTS / "report.pdf", INPUTS / "scanned_report.pdf")
    doc_samples.make_all(INPUTS, chart, REGIONS)
    continuity_sample.make_continuity_pdf(INPUTS / "continuity.pdf", chart)
    for path in sorted(INPUTS.iterdir()):
        print(f"{path.name:22} {path.stat().st_size:>9,} bytes")


if __name__ == "__main__":
    main()
