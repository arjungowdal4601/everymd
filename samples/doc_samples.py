"""Office, web, ebook and email samples for everymd (called from make_samples.py)."""

from __future__ import annotations

import zipfile
from email.message import EmailMessage
from email.utils import format_datetime
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.shared import Inches
from pptx import Presentation
from pptx.util import Inches as PptInches
from pptx.util import Pt


def make_docx(path: Path, chart: Path) -> None:
    """Headings, a bullet list, a table and an image."""
    doc = Document()
    doc.add_heading("Project Proposal: Community Sensor Network", level=0)
    doc.add_heading("Background", level=1)
    doc.add_paragraph(
        "Local growers lose crops every summer because they cannot see when soil dries out. "
        "This proposal extends the water sensor pilot into a permanent community network."
    )
    doc.add_heading("Goals", level=1)
    for goal in (
        "Keep at least 90% of sensors online through the year.",
        "Send growers a text message when soil moisture drops below 20%.",
        "Share anonymised readings with the regional water authority.",
    ):
        doc.add_paragraph(goal, style="List Bullet")
    doc.add_heading("Budget", level=1)
    rows = [("Item", "Cost (EUR)"), ("40 soil moisture sensors", "740"), ("Gateway and SIM plan", "380"), ("Training sessions", "450"), ("Total", "1,570")]
    table = doc.add_table(rows=len(rows), cols=2)
    table.style = "Table Grid"
    for r, (item, cost) in enumerate(rows):
        table.cell(r, 0).text = item
        table.cell(r, 1).text = cost
    doc.add_heading("Expected impact", level=1)
    doc.add_paragraph("The pilot already showed steady growth in three of four regions:")
    doc.add_picture(str(chart), width=Inches(5.5))
    doc.add_paragraph("Figure 1: Sensors online per region during the pilot.")
    doc.save(path)


def make_pptx(path: Path, chart: Path, regions: list[tuple[str, int, int]]) -> None:
    """Three slides with a table, a chart image and speaker notes on every slide."""
    prs = Presentation()
    title = prs.slides.add_slide(prs.slide_layouts[0])
    title.shapes.title.text = "Board Update: Q2 2026"
    title.placeholders[1].text = "Community water sensor pilot"
    title.notes_slide.notes_text_frame.text = "Welcome the board. The pilot finished its second quarter on schedule."

    rollout = prs.slides.add_slide(prs.slide_layouts[5])
    rollout.shapes.title.text = "Sensor rollout by region"
    shape = rollout.shapes.add_table(len(regions) + 1, 3, PptInches(1), PptInches(1.8), PptInches(8), PptInches(3))
    for c, header in enumerate(("Region", "Q1 sensors", "Q2 sensors")):
        shape.table.cell(0, c).text = header
    for r, (name, q1, q2) in enumerate(regions, start=1):
        for c, value in enumerate((name, str(q1), str(q2))):
            cell = shape.table.cell(r, c)
            cell.text = value
            cell.text_frame.paragraphs[0].font.size = Pt(18)
    rollout.notes_slide.notes_text_frame.text = "South is the only region that shrank: seven sensors failed after the June storms."

    growth = prs.slides.add_slide(prs.slide_layouts[5])
    growth.shapes.title.text = "Growth by region"
    growth.shapes.add_picture(str(chart), PptInches(1.2), PptInches(1.6), width=PptInches(7.6))
    growth.notes_slide.notes_text_frame.text = "Point out that East grew fastest. Ask the board to approve the Q3 budget."
    prs.save(path)


HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Garden Sensor Guide</title>
<style>
  body { font-family: sans-serif; margin: 0; }
  .site-nav { background: #234; color: #fff; padding: 12px 24px; }
  .site-nav a { color: #fff; margin-right: 18px; }
  main { max-width: 760px; margin: 24px auto; padding: 0 24px; }
  table { border-collapse: collapse; } td, th { border: 1px solid #999; padding: 6px 10px; }
  pre { background: #f4f4f4; padding: 12px; }
  .cookie { background: #ffe; border: 1px solid #cc9; padding: 10px 24px; }
  footer { background: #eee; padding: 16px 24px; font-size: 13px; }
</style>
</head>
<body>
<header class="site-nav">
  <a href="#">Home</a><a href="#">Shop</a><a href="#">Blog</a><a href="#">Contact</a><a href="#">Sign in</a>
</header>
<div class="cookie">We use cookies to improve your experience. <button>Accept all</button> <button>Settings</button></div>
<main>
  <h1>Setting up a garden moisture sensor</h1>
  <p>A soil moisture sensor tells you when to water. This guide shows how to wire one to a small
  board, calibrate it and read values every ten minutes.</p>
  <h2>What you need</h2>
  <ul>
    <li>One capacitive soil moisture sensor</li>
    <li>A microcontroller board with an analogue input</li>
    <li>Three jumper wires and a USB cable</li>
  </ul>
  <h2>Calibration values</h2>
  <table>
    <tr><th>Soil state</th><th>Raw reading</th><th>Moisture</th></tr>
    <tr><td>Dry air</td><td>3,100</td><td>0%</td></tr>
    <tr><td>Damp soil</td><td>2,050</td><td>48%</td></tr>
    <tr><td>Glass of water</td><td>1,250</td><td>100%</td></tr>
  </table>
  <h2>Reading the sensor</h2>
  <pre><code>import time

DRY, WET = 3100, 1250

def moisture(raw):
    return round(100 * (DRY - raw) / (DRY - WET))

while True:
    print(moisture(read_adc()))
    time.sleep(600)</code></pre>
  <p>Water the bed when the value stays below 20% for an hour.</p>
</main>
<footer>&copy; 2026 Example Gardens &middot; Privacy &middot; Terms &middot; Follow us on social media</footer>
</body>
</html>
"""


def make_epub(path: Path) -> None:
    """A minimal valid EPUB 3 with two chapters."""
    container = (
        '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'
    )
    opf = """<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">urn:uuid:5d1c9a52-7f0e-4c43-9a51-everymd-sample</dc:identifier>
    <dc:title>The Small Garden Booklet</dc:title>
    <dc:language>en</dc:language>
    <meta property="dcterms:modified">2026-10-02T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="ch1"/><itemref idref="ch2"/></spine>
</package>"""
    page = (
        '<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops"><head><title>{title}</title></head><body>{body}</body></html>'
    )
    nav = page.format(title="Contents", body=(
        '<nav epub:type="toc"><h1>Contents</h1><ol><li><a href="ch1.xhtml">Choosing a bed</a></li>'
        '<li><a href="ch2.xhtml">Watering</a></li></ol></nav>'
    ))
    ch1 = page.format(title="Choosing a bed", body=(
        "<h1>Chapter 1: Choosing a bed</h1><p>Pick a spot with six hours of sun and soil that drains "
        "within a day of rain.</p><ul><li>Raised beds warm up faster in spring.</li>"
        "<li>Ground beds hold water longer in summer.</li></ul>"
    ))
    ch2 = page.format(title="Watering", body=(
        "<h1>Chapter 2: Watering</h1><p>Water deeply and less often. A moisture sensor removes the "
        "guesswork: water when it reads below 20%.</p><p>Morning watering loses the least to evaporation.</p>"
    ))
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        for name, data in (
            ("META-INF/container.xml", container), ("OEBPS/content.opf", opf),
            ("OEBPS/nav.xhtml", nav), ("OEBPS/ch1.xhtml", ch1), ("OEBPS/ch2.xhtml", ch2),
        ):
            zf.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)


def make_eml(path: Path) -> None:
    """A plain-text email with an HTML alternative."""
    msg = EmailMessage()
    msg["From"] = "Priya Nair <priya@example.org>"
    msg["To"] = "Pilot volunteers <volunteers@example.org>"
    msg["Subject"] = "Pilot update: 497 sensors online"
    msg["Date"] = format_datetime(datetime(2026, 9, 30, 9, 15, tzinfo=timezone.utc))
    msg.set_content(
        "Hi all,\n\nQuick update on the water sensor pilot:\n\n"
        "- 497 sensors are online, up from 425 last quarter.\n"
        "- South lost 7 sensors in the June storms; replacements arrive next week.\n"
        "- The Q3 budget (EUR 2,735) goes to the steering group on Monday.\n\n"
        "Thanks for all the weekend installs!\nPriya\n"
    )
    msg.add_alternative(
        "<html><body><p>Hi all,</p><p>Quick update on the water sensor pilot:</p>"
        "<table border='1'><tr><th>Quarter</th><th>Sensors online</th></tr>"
        "<tr><td>Q1 2026</td><td>425</td></tr><tr><td>Q2 2026</td><td>497</td></tr></table>"
        "<p>South lost 7 sensors in the June storms; replacements arrive next week.</p>"
        "<p>Thanks for all the weekend installs!<br>Priya</p></body></html>",
        subtype="html",
    )
    path.write_bytes(bytes(msg))


def make_all(inputs: Path, chart: Path, regions: list[tuple[str, int, int]]) -> None:
    make_docx(inputs / "proposal.docx", chart)
    make_pptx(inputs / "board_deck.pptx", chart, regions)
    (inputs / "page.html").write_text(HTML.replace("</h1>", "</h1>\n  <img src=\"chart.png\" alt=\"Sensors online by region\" width=\"600\">", 1), encoding="utf-8")
    make_epub(inputs / "booklet.epub")
    make_eml(inputs / "update.eml")
