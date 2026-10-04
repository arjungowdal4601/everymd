"""A 5-page PDF where page breaks cut things in half, to test the copy-editor's continuity note.

- pages 1-2: a table runs onto page 2, which has no header row
- pages 2-3: a sentence is cut, and the word "irrigation" is split as "irriga-" / "tion"
- pages 3-4: a numbered list runs from item 3 on page 3 to item 4 on page 4
- pages 4-5: a figure sits on page 4 and its caption on page 5
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

WIDTH, HEIGHT = A4
LEFT = 60
COLUMNS = [("Site", LEFT), ("Date", LEFT + 90), ("Moisture (%)", LEFT + 220), ("Battery (V)", LEFT + 360)]


def _rows():
    return [
        (f"S{i:02d}", f"2026-04-{(i % 28) + 1:02d}", str((i * 7) % 40 + 15), f"{3.3 + (i % 5) * 0.1:.1f}")
        for i in range(1, 41)
    ]


def _frame(canvas: Canvas, page: int) -> None:
    canvas.setFont("Helvetica", 9)
    canvas.drawString(LEFT, HEIGHT - 30, "Sensor Field Log - spring survey")
    canvas.drawRightString(WIDTH - LEFT, 28, f"Page {page} of 5")


def _lines(canvas: Canvas, y: float, lines: list[str], size: int = 11, font: str = "Helvetica") -> float:
    canvas.setFont(font, size)
    for line in lines:
        canvas.drawString(LEFT, y, line)
        y -= size + 5
    return y


def _table(canvas: Canvas, y: float, rows: list[tuple], header: bool) -> float:
    right = LEFT + 470
    if header:
        canvas.setFont("Helvetica-Bold", 10)
        for title, x in COLUMNS:
            canvas.drawString(x + 4, y - 14, title)
        canvas.rect(LEFT, y - 20, right - LEFT, 20)
        y -= 20
    canvas.setFont("Helvetica", 10)
    for row in rows:
        for (_, x), value in zip(COLUMNS, row):
            canvas.drawString(x + 4, y - 14, value)
        canvas.rect(LEFT, y - 20, right - LEFT, 20)
        y -= 20
    for _, x in COLUMNS[1:]:
        canvas.line(x, y, x, y + 20 * (len(rows) + header))
    return y


def make_continuity_pdf(path: Path, chart: Path) -> None:
    rows = _rows()
    canvas = Canvas(str(path), pagesize=A4)
    canvas.setTitle("Sensor Field Log")

    _frame(canvas, 1)
    y = _lines(canvas, HEIGHT - 70, ["Sensor Field Log"], size=22, font="Helvetica-Bold")
    y = _lines(canvas, y - 12, ["1 Readings"], size=15, font="Helvetica-Bold")
    y = _lines(canvas, y - 4, ["Soil moisture and battery voltage for every site in the spring survey."])
    _table(canvas, y - 10, rows[:28], header=True)
    canvas.showPage()

    _frame(canvas, 2)
    _table(canvas, HEIGHT - 60, rows[28:], header=False)
    _lines(canvas, 120, [
        "These readings come from the spring survey. Volunteers checked every site twice and",
        "logged the lower value. Sites in the river valley stayed wetter than the hill sites,",
        "as in earlier years. All readings above were taken before the irriga-",
    ])
    canvas.showPage()

    _frame(canvas, 3)
    y = _lines(canvas, HEIGHT - 60, [
        "tion schedule changed in May, so the dry readings at sites S31 to S40 are expected",
        "and need no follow-up.",
    ])
    y = _lines(canvas, y - 20, ["2 Maintenance steps"], size=15, font="Helvetica-Bold")
    _lines(canvas, y - 4, ["Do these steps at every site visit:"])
    _lines(canvas, 160, [
        "1.  Clean the sensor probe with a dry cloth.",
        "2.  Check the battery voltage and write it in the log.",
        "3.  Replace the battery if it reads below 3.4 V.",
    ])
    canvas.showPage()

    _frame(canvas, 4)
    _lines(canvas, HEIGHT - 60, [
        "4.  Push the probe back in at a depth of 10 cm.",
        "5.  Photograph the site and upload the photo.",
    ])
    canvas.drawImage(str(chart), LEFT, 90, width=440, height=440 * 620 / 1000)
    canvas.showPage()

    _frame(canvas, 5)
    y = _lines(canvas, HEIGHT - 60, ["Figure 1: Sensors online by region, Q1 and Q2 2026."], font="Helvetica-Oblique")
    y = _lines(canvas, y - 20, ["3 Next steps"], size=15, font="Helvetica-Bold")
    _lines(canvas, y - 4, ["Repeat the survey after the summer, using the same sites and the same steps."])
    canvas.save()


if __name__ == "__main__":
    inputs = Path(__file__).resolve().parent / "inputs"
    make_continuity_pdf(inputs / "continuity.pdf", inputs / "chart.png")
    print("wrote", inputs / "continuity.pdf")
