"""Render a ResumeLayout to a one-page US Letter PDF.

Uses reportlab (pure Python, no locally installed Chrome/browser engine
required) so the generator works in any environment that can pip install a
requirements.txt - see docs/tailoring.md for why this was chosen over a
headless-browser HTML-to-PDF approach.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from pipeline.resume import ResumeLayout

_MARGIN = 0.6 * inch
_FONT = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"


class ResumeTooLongError(Exception):
    """Raised when a layout cannot fit on one US Letter page."""


def _wrap(text: str, canvas_obj: canvas.Canvas, font: str, size: float, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if canvas_obj.stringWidth(candidate, font, size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def render_pdf(layout: ResumeLayout, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = LETTER
    max_width = width - 2 * _MARGIN

    c = canvas.Canvas(str(output_path), pagesize=LETTER)
    y = height - _MARGIN

    def line_break(amount: float) -> None:
        nonlocal y
        y -= amount
        if y < _MARGIN:
            raise ResumeTooLongError(
                "Resume content does not fit on one US Letter page. "
                "Shorten bullets, drop lower-priority accomplishments, or "
                "trim skills/education/projects in profile.yaml."
            )

    def draw(text: str, font: str, size: float, extra_gap: float = 0.0) -> None:
        nonlocal y
        c.setFont(font, size)
        c.drawString(_MARGIN, y, text)
        line_break(size + 2 + extra_gap)

    def draw_wrapped_bullet(text: str, font: str, size: float) -> None:
        nonlocal y
        c.setFont(font, size)
        bullet_indent = 0.2 * inch
        wrapped = _wrap(text, c, font, size, max_width - bullet_indent)
        for i, part in enumerate(wrapped):
            prefix = "- " if i == 0 else "  "
            c.drawString(_MARGIN + bullet_indent, y, prefix + part)
            line_break(size + 2)

    def draw_wrapped_plain(text: str, font: str, size: float, extra_gap: float = 0.0) -> None:
        nonlocal y
        c.setFont(font, size)
        wrapped = _wrap(text, c, font, size, max_width)
        for part in wrapped:
            c.drawString(_MARGIN, y, part)
            line_break(size + 2)
        line_break(extra_gap)

    # Header
    draw(layout.candidate_name, _FONT_BOLD, 16, extra_gap=2)
    draw_wrapped_plain(layout.contact_line, _FONT, 9, extra_gap=6)

    # Experience
    if layout.role_sections:
        draw("EXPERIENCE", _FONT_BOLD, 11, extra_gap=2)
        for section in layout.role_sections:
            date_range = " - ".join(p for p in [section.start_date, section.end_date] if p)
            header = f"{section.role}, {section.company}" if section.company else section.role
            c.setFont(_FONT_BOLD, 10)
            c.drawString(_MARGIN, y, header)
            if date_range:
                date_width = c.stringWidth(date_range, _FONT, 9)
                c.setFont(_FONT, 9)
                c.drawString(width - _MARGIN - date_width, y, date_range)
            line_break(12)
            for bullet in section.bullets:
                draw_wrapped_bullet(bullet, _FONT, 9.5)
            line_break(4)

    # Skills
    if layout.skill_groups:
        draw("SKILLS", _FONT_BOLD, 11, extra_gap=2)
        for label, values in layout.skill_groups:
            pretty_label = label.replace("_", " ").title()
            draw_wrapped_bullet(f"{pretty_label}: {', '.join(values)}", _FONT, 9.5)
        line_break(4)

    # Education
    if layout.education:
        draw("EDUCATION", _FONT_BOLD, 11, extra_gap=2)
        for entry in layout.education:
            degree = entry.get("degree", "")
            school = entry.get("school", "")
            grad_year = entry.get("graduation_year", "")
            text = ", ".join(str(p) for p in [degree, school, grad_year] if p)
            draw_wrapped_bullet(text, _FONT, 9.5)
        line_break(4)

    # Projects
    if layout.projects:
        draw("PROJECTS", _FONT_BOLD, 11, extra_gap=2)
        for title, bullets in layout.projects:
            draw_wrapped_plain(title, _FONT_BOLD, 9.5)
            for bullet in bullets:
                draw_wrapped_bullet(bullet, _FONT, 9.5)

    c.showPage()
    c.save()
