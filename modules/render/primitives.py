"""Drawing primitives for CetakKira worksheets."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from modules.i18n import t

PAGE_W, PAGE_H = A4  # 595.275590551181, 841.8897637795276
MARGIN_X: float = 28.0
CONTENT_W: float = PAGE_W - 2 * MARGIN_X  # 539.275590551181
LOGO_PATH: str = str(Path(__file__).resolve().parents[2] / "static" / "img" / "logo-print.png")
LOGO_SIZE: float = 14.0

# Standard grayscale palette
COLOR_BLACK: Color = colors.black
COLOR_DARK: Color = HexColor("#333333")
COLOR_MID: Color = HexColor("#777777")
COLOR_LIGHT: Color = HexColor("#b0b0b0")
COLOR_FAINT: Color = HexColor("#e0e0e0")
COLOR_PILL_BG: Color = HexColor("#f4f4f4")
COLOR_ANSWER_BG: Color = HexColor("#ebebeb")


def rounded_box(
    c: Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    radius: float = 6.0,
    stroke: int = 1,
    fill: int = 0,
    stroke_color: Color = COLOR_BLACK,
    fill_color: Color = COLOR_PILL_BG,
    line_width: float = 0.85,
) -> None:
    """Draw a rectangle with rounded corners."""
    c.saveState()
    c.setStrokeColor(stroke_color)
    c.setFillColor(fill_color)
    c.setLineWidth(line_width)
    c.roundRect(x, y, w, h, radius, stroke=stroke, fill=fill)
    c.restoreState()


def ruled_line(
    c: Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    stroke_color: Color = COLOR_BLACK,
    line_width: float = 0.8,
) -> None:
    """Draw a single straight line."""
    c.saveState()
    c.setStrokeColor(stroke_color)
    c.setLineWidth(line_width)
    c.line(x1, y1, x2, y2)
    c.restoreState()


def badge_number(
    c: Canvas,
    cx: float,
    cy: float,
    num: int | str,
    radius: float = 7.5,
) -> None:
    """Draw a circular question-number badge with centered text."""
    c.saveState()
    c.setStrokeColor(COLOR_BLACK)
    c.setFillColor(COLOR_BLACK)
    c.setLineWidth(0.8)
    c.circle(cx, cy, radius, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 8)
    # Baseline offset approx 2.5 pt below center
    c.drawCentredString(cx, cy - 2.8, str(num))
    c.restoreState()


def draw_header(
    c: Canvas,
    title: str,
    subtitle: str | None = None,
    instruction: str | None = None,
    lang: str = "ms",
    is_answer: bool = False,
    score_max: int | None = None,
) -> None:
    """Draw standard page header with title, metadata fields, and instruction banner.

    Guaranteed no overlap between left-aligned titles/subtitles and right-aligned
    metadata fields across all Malay and English variations.
    """
    c.saveState()

    # Split column boundary: left side [28 .. 320], right side [330 .. PAGE_W - 28]
    right_x = 330.0
    right_end_x = PAGE_W - MARGIN_X

    # Row 1 (y = PAGE_H - 34): Title on left; Name field on right (content pages only)
    row1_y = PAGE_H - 34.0
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(COLOR_BLACK)
    c.drawString(MARGIN_X, row1_y, title)

    if not is_answer:
        label_name = t("label_name", lang=lang)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(COLOR_BLACK)
        c.drawString(right_x, row1_y, label_name)
        name_line_start = right_x + c.stringWidth(label_name, "Helvetica-Bold", 9) + 5
        ruled_line(c, name_line_start, row1_y, right_end_x, row1_y, line_width=0.8)
    else:
        # On answer sheets, display plain target label without brackets
        target_text = t("label_answer_target", lang=lang)
        c.setFont("Helvetica", 8.5)
        c.setFillColor(COLOR_MID)
        c.drawRightString(right_end_x, row1_y, target_text)

    # Row 2 (y = PAGE_H - 51): Subtitle on left; Date and Score fields on right
    row2_y = PAGE_H - 51.0
    if subtitle:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(COLOR_MID)
        c.drawString(MARGIN_X, row2_y, subtitle)

    if not is_answer:
        label_date = t("label_date", lang=lang)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(COLOR_BLACK)
        c.drawString(right_x, row2_y, label_date)

        date_lbl_w = c.stringWidth(label_date, "Helvetica-Bold", 9)
        date_line_start = right_x + date_lbl_w + 5
        date_line_end = right_x + 130.0
        ruled_line(c, date_line_start, row2_y, date_line_end, row2_y, line_width=0.8)

        if score_max is not None:
            score_x = date_line_end + 12.0
            label_score = t("label_score", lang=lang)
            c.drawString(score_x, row2_y, label_score)
            score_lbl_w = c.stringWidth(label_score, "Helvetica-Bold", 9)
            score_line_start = score_x + score_lbl_w + 4
            score_line_end = score_line_start + 24.0
            ruled_line(c, score_line_start, row2_y, score_line_end, row2_y, line_width=0.8)
            c.drawString(score_line_end + 3.0, row2_y, f"/ {score_max}")

    # Row 3 (y = PAGE_H - 74): Instruction pill across full content width
    inst_y = PAGE_H - 74.0
    inst_h = 18.0
    rounded_box(
        c,
        MARGIN_X,
        inst_y,
        CONTENT_W,
        inst_h,
        radius=4.0,
        stroke=1,
        fill=1,
        stroke_color=COLOR_BLACK,
        fill_color=COLOR_PILL_BG,
        line_width=0.8,
    )

    inst_label = t("label_instruction", lang=lang)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(COLOR_BLACK)
    label_w = c.stringWidth(inst_label, "Helvetica-Bold", 8.5)
    c.drawString(MARGIN_X + 8.0, inst_y + 5.0, inst_label)

    if instruction:
        c.setFont("Helvetica", 8.5)
        c.drawString(MARGIN_X + 8.0 + label_w + 6.0, inst_y + 5.0, instruction)

    c.restoreState()


def draw_footer(
    c: Canvas,
    page_num: int,
    total_pages: int,
    lang: str = "ms",
) -> None:
    """Draw clean footer with dividing rule, brand mark, and localized page number."""
    c.saveState()

    rule_y = 36.0
    text_y = 24.0

    # Thin dividing rule
    ruled_line(
        c, MARGIN_X, rule_y, PAGE_W - MARGIN_X, rule_y, stroke_color=COLOR_FAINT, line_width=0.5
    )

    # Brand mark on left: logo, then name
    c.drawImage(
        LOGO_PATH, MARGIN_X, text_y - 4.0, LOGO_SIZE, LOGO_SIZE, mask="auto"
    )
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(COLOR_MID)
    c.drawString(MARGIN_X + LOGO_SIZE + 4.0, text_y, t("brand_footer", lang=lang))

    # Page number on right
    c.setFont("Helvetica", 8.5)
    page_text = t("page_format", lang=lang, current=page_num, total=total_pages)
    c.drawRightString(PAGE_W - MARGIN_X, text_y, page_text)

    c.restoreState()


def grid_cell(
    c: Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str = "",
    is_blank: bool = False,
    is_answer: bool = False,
) -> None:
    """Draw a single cell of the 100-number grid."""
    c.saveState()

    # Fill background if it's a highlighted blank on the answer sheet
    if is_blank and is_answer:
        c.setFillColor(COLOR_ANSWER_BG)
        c.rect(x, y, w, h, stroke=0, fill=1)

    # Cell border
    c.setStrokeColor(COLOR_MID)
    c.setLineWidth(0.6)
    c.rect(x, y, w, h, stroke=1, fill=0)

    if text:
        c.setFillColor(COLOR_BLACK)
        # Dynamic font size based on text length: 1-2 digits -> 18, 3 digits -> 16, 4 digits -> 14
        if len(text) >= 4:
            font_size = 13.5
            baseline_y = y + (h - 10.0) / 2.0
        elif len(text) == 3:
            font_size = 16.0
            baseline_y = y + (h - 12.0) / 2.0
        else:
            font_size = 18.0
            baseline_y = y + (h - 14.0) / 2.0

        c.setFont("Helvetica-Bold", font_size)
        c.drawCentredString(x + w / 2.0, baseline_y, text)
    elif is_blank and not is_answer:
        # Draw a writing guide line for the student
        line_pad = max(6.0, w * 0.15)
        line_y = y + 10.0
        ruled_line(
            c,
            x + line_pad,
            line_y,
            x + w - line_pad,
            line_y,
            stroke_color=COLOR_LIGHT,
            line_width=0.7,
        )

    c.restoreState()
