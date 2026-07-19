"""Generates a Certificate of Completion PDF for a finished enrollment.

Uses reportlab (pure-Python, no native system libraries) rather than an HTML-to-PDF renderer
like WeasyPrint, which requires Pango/Cairo/GDK-Pixbuf to be installed on the host — a real
problem for local Windows development and unnecessary complexity for the production image.
The "logo" is drawn as a vector seal (concentric circles + a star) rather than a fabricated
brand image, since no real logo asset exists for this project.
"""

import io
import math

from django.conf import settings
from django.utils import timezone
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

PRIMARY = HexColor("#4f46e5")
GOLD = HexColor("#d4af37")
MUTED = HexColor("#555555")


def generate_certificate_pdf(enrollment) -> bytes:
    buffer = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    _draw_border(c, width, height)
    _draw_seal(c, width / 2, 3.0 * cm)

    project_name = str(settings.PROJECT_METADATA["NAME"])
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(PRIMARY)
    c.drawCentredString(width / 2, height - 2.6 * cm, project_name)

    c.setFont("Times-Italic", 14)
    c.setFillColor(MUTED)
    c.drawCentredString(width / 2, height - 3.6 * cm, "Certificate of Completion")

    c.setFont("Times-Bold", 34)
    c.setFillColor(GOLD)
    c.drawCentredString(width / 2, height - 5.3 * cm, "CERTIFICATE OF COMPLETION")

    c.setFont("Times-Italic", 13)
    c.setFillColor(MUTED)
    c.drawCentredString(width / 2, height - 7.2 * cm, "This certifies that")

    student_name = enrollment.student.get_display_name()
    c.setFont("Times-Bold", 28)
    c.setFillColor(PRIMARY)
    c.drawCentredString(width / 2, height - 8.6 * cm, student_name)

    # underline beneath the name
    name_width = c.stringWidth(student_name, "Times-Bold", 28)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(
        width / 2 - name_width / 2 - 0.5 * cm,
        height - 9.1 * cm,
        width / 2 + name_width / 2 + 0.5 * cm,
        height - 9.1 * cm,
    )

    c.setFont("Times-Italic", 13)
    c.setFillColor(MUTED)
    c.drawCentredString(width / 2, height - 10.2 * cm, "has successfully completed the course")

    c.setFont("Times-Bold", 20)
    c.setFillColor(PRIMARY)
    c.drawCentredString(width / 2, height - 11.3 * cm, enrollment.course.title)

    completed_at = timezone.localtime(timezone.now()).strftime("%B %d, %Y")
    c.setFont("Helvetica", 11)
    c.setFillColor(MUTED)
    c.drawCentredString(
        width / 2,
        3.0 * cm,
        f"Instructor: {enrollment.course.instructor.get_display_name()}    ·    Completed on {completed_at}",
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def _draw_border(c: canvas.Canvas, width: float, height: float) -> None:
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(6)
    c.rect(1 * cm, 1 * cm, width - 2 * cm, height - 2 * cm)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.rect(1.3 * cm, 1.3 * cm, width - 2.6 * cm, height - 2.6 * cm)


def _draw_seal(c: canvas.Canvas, cx: float, cy: float) -> None:
    c.setFillColor(GOLD)
    c.circle(cx, cy, 1.5 * cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx, cy, 1.2 * cm, fill=1, stroke=0)
    c.setFillColor(GOLD)
    _draw_star(c, cx, cy, outer_r=0.85 * cm, inner_r=0.35 * cm)


def _draw_star(c: canvas.Canvas, cx: float, cy: float, outer_r: float, inner_r: float) -> None:
    """Draws a 5-point star as a vector path — avoids relying on a Unicode glyph (e.g. "★")
    being present in a base-14 PDF font's encoding, which isn't guaranteed."""
    path = c.beginPath()
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        r = outer_r if i % 2 == 0 else inner_r
        x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.close()
    c.drawPath(path, fill=1, stroke=0)
