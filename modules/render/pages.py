"""Page renderers for CetakPintar worksheet topics."""

from __future__ import annotations

from typing import Sequence

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

from modules.alphabet import MatchSet, MissingRow
from modules.i18n import t
from modules.layout import MATCH_PAIRS, cards_per_sheet
from modules.problems import ArithmeticProblem, CountingProblem, DivisionProblem
from modules.render.letters import draw_letter, letter_width
from modules.render.primitives import (
    COLOR_ANSWER_BG,
    COLOR_BLACK,
    COLOR_FAINT,
    COLOR_LIGHT,
    COLOR_MID,
    COLOR_PILL_BG,
    CONTENT_W,
    MARGIN_X,
    PAGE_H,
    badge_number,
    draw_footer,
    draw_header,
    grid_cell,
    rounded_box,
    ruled_line,
)
from modules.render.shapes import draw_shape
from modules.spec import Spec


def draw_grid(
    c: Canvas,
    spec: Spec,
    blanks: Sequence[int],
    is_answer: bool,
    page_num: int,
    total_pages: int,
) -> None:
    """Render a 100-number grid practice sheet or answer sheet."""
    start = spec.grid_start
    end = start + 99
    blanks_set = set(blanks)

    # 1. Header
    if not is_answer:
        title = t("grid_title", lang=spec.lang)
        subtitle = t("grid_subtitle", lang=spec.lang, start=start, end=end)
        instruction = t("grid_instruction", lang=spec.lang)
        score_max = len(blanks)
    else:
        title = t("answer_key_title", lang=spec.lang)
        subtitle = t("grid_answer_subtitle", lang=spec.lang, start=start, end=end)
        instruction = t("answer_key_instruction", lang=spec.lang)
        score_max = None

    draw_header(
        c,
        title=title,
        subtitle=subtitle,
        instruction=instruction,
        lang=spec.lang,
        is_answer=is_answer,
        score_max=score_max,
    )

    # 2. Grid layout
    cell_w = CONTENT_W / 10.0
    cell_h = 67.0
    grid_top_y = PAGE_H - 84.0

    # Outer border around entire grid
    rounded_box(
        c,
        MARGIN_X,
        grid_top_y - 10 * cell_h,
        CONTENT_W,
        10 * cell_h,
        radius=6.0,
        stroke=1,
        fill=0,
        line_width=1.0,
    )

    # Draw cells
    for row in range(10):
        for col in range(10):
            num = start + row * 10 + col
            x = MARGIN_X + col * cell_w
            y = grid_top_y - (row + 1) * cell_h
            is_blank = num in blanks_set

            if is_blank:
                text = str(num) if is_answer else ""
                grid_cell(c, x, y, cell_w, cell_h, text=text, is_blank=True, is_answer=is_answer)
            else:
                grid_cell(
                    c, x, y, cell_w, cell_h, text=str(num), is_blank=False, is_answer=is_answer
                )

    # 3. Footer
    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def _draw_aligned_number(
    c: Canvas,
    val: int,
    row: int,
    gx: float,
    gy: float,
    gw: float,
    gh: float,
    total_cols: int,
    font_name: str = "Helvetica-Bold",
    font_size: float = 14.0,
) -> None:
    """Draw a right-aligned integer where each digit is precisely centered in its grid cell.

    Uses a single TextObject with character spacing so digits align with grid columns
    and pypdf extracts the complete multi-digit integer as a single word.
    """
    val_str = str(val)
    w_d = c.stringWidth("0", font_name, font_size)
    char_space = gw - w_d
    start_col = total_cols - len(val_str)
    cell_x = gx + start_col * gw
    x_start = cell_x + (gw - w_d) / 2.0
    baseline_y = gy + row * gh + (gh - 10.0) / 2.0

    t = c.beginText(x_start, baseline_y)
    t.setFont(font_name, font_size)
    t.setCharSpace(char_space)
    t.textOut(val_str)
    t.setCharSpace(0)
    c.drawText(t)


def _draw_arithmetic_card(
    c: Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    q_num: int,
    problem: ArithmeticProblem,
    op: str,
    num_digit_cols: int,
    is_answer: bool,
) -> None:
    """Draw a single vertical arithmetic card with guided place-value grid lines."""
    c.saveState()

    # Outer card border
    rounded_box(c, x, y, w, h, radius=6.0, stroke=1, fill=0, line_width=0.85)

    # Question number badge
    badge_number(c, x + 12.0, y + h - 12.0, q_num)

    # Place-value grid geometry
    # Total columns: 1 operator col + num_digit_cols
    total_cols = num_digit_cols + 1
    if total_cols <= 3:
        gw = 20.0
    elif total_cols == 4:
        gw = 19.0
    else:
        gw = 18.0

    gh = 20.0 if h > 140.0 else 18.0

    gx = x + (w - total_cols * gw) / 2.0
    gy = y + (h - 4 * gh) / 2.0 - 5.0

    # Light inner grid lines for place-value alignment
    c.setStrokeColor(COLOR_LIGHT)
    c.setLineWidth(0.5)

    # Vertical grid lines
    for i in range(total_cols + 1):
        c.line(gx + i * gw, gy, gx + i * gw, gy + 4 * gh)

    # Horizontal grid lines (rows 0, 2, 3, 4)
    for j in (0, 2, 3, 4):
        c.line(gx, gy + j * gh, gx + total_cols * gw, gy + j * gh)

    # Thick horizontal calculation separator line above answer row (j = 1)
    c.setStrokeColor(COLOR_BLACK)
    c.setLineWidth(1.5)
    c.line(gx, gy + gh, gx + total_cols * gw, gy + gh)

    # Digits baseline offset
    digit_baseline_offset = (gh - 10.0) / 2.0

    # Operator in Row 1 (operator col = 0)
    c.setFillColor(COLOR_BLACK)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(gx + 0.5 * gw, gy + 1 * gh + digit_baseline_offset, op)

    # Top operand (problem.a) in Row 2
    _draw_aligned_number(c, problem.a, 2, gx, gy, gw, gh, total_cols)

    # Bottom operand (problem.b) in Row 1
    _draw_aligned_number(c, problem.b, 1, gx, gy, gw, gh, total_cols)

    # Answer in Row 0 (only when is_answer is True)
    if is_answer:
        # Subtle shaded background in answer row
        c.setFillColor(HexColor("#f0f0f0"))
        c.rect(gx + gw, gy, num_digit_cols * gw, gh, stroke=0, fill=1)
        # Redraw answer text
        c.setFillColor(COLOR_BLACK)
        _draw_aligned_number(c, problem.answer, 0, gx, gy, gw, gh, total_cols)

    c.restoreState()


def draw_add(
    c: Canvas,
    spec: Spec,
    problems: Sequence[ArithmeticProblem],
    is_answer: bool,
    page_num: int,
    total_pages: int,
) -> None:
    """Render an addition practice sheet or answer sheet."""
    count = cards_per_sheet(spec, "add")
    # Addition reserves 1 overflow column beyond the widest operand
    num_digit_cols = spec.add_digits + 1

    # 1. Header
    if not is_answer:
        title = t("add_title", lang=spec.lang)
        sub_key = "add_subtitle_regroup" if spec.add_regroup else "add_subtitle_no_regroup"
        subtitle = t(sub_key, lang=spec.lang, digits=spec.add_digits)
        instruction = t("add_instruction", lang=spec.lang)
        score_max = count
    else:
        title = t("answer_key_title", lang=spec.lang)
        subtitle = t("add_answer_subtitle", lang=spec.lang, digits=spec.add_digits)
        instruction = t("answer_key_instruction", lang=spec.lang)
        score_max = None

    draw_header(
        c,
        title=title,
        subtitle=subtitle,
        instruction=instruction,
        lang=spec.lang,
        is_answer=is_answer,
        score_max=score_max,
    )

    # 2. Cards grid layout
    cols = 4
    rows = count // cols  # 4 for 16 cards, 5 for 20 cards
    gap_x = 9.0
    gap_y = 9.0
    start_y = PAGE_H - 84.0
    bottom_y = 44.0

    card_w = (CONTENT_W - (cols - 1) * gap_x) / cols
    card_h = (start_y - bottom_y - (rows - 1) * gap_y) / rows

    for r in range(rows):
        for c_idx in range(cols):
            idx = r * cols + c_idx
            if idx >= len(problems):
                break
            x = MARGIN_X + c_idx * (card_w + gap_x)
            y = start_y - (r + 1) * card_h - r * gap_y
            _draw_arithmetic_card(
                c,
                x=x,
                y=y,
                w=card_w,
                h=card_h,
                q_num=idx + 1,
                problem=problems[idx],
                op="+",
                num_digit_cols=num_digit_cols,
                is_answer=is_answer,
            )

    # 3. Footer
    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def draw_sub(
    c: Canvas,
    spec: Spec,
    problems: Sequence[ArithmeticProblem],
    is_answer: bool,
    page_num: int,
    total_pages: int,
) -> None:
    """Render a subtraction practice sheet or answer sheet."""
    count = cards_per_sheet(spec, "sub")
    # Subtraction digits match the widest operand
    num_digit_cols = spec.sub_digits

    # 1. Header
    if not is_answer:
        title = t("sub_title", lang=spec.lang)
        sub_key = "sub_subtitle_borrow" if spec.sub_borrow else "sub_subtitle_no_borrow"
        subtitle = t(sub_key, lang=spec.lang, digits=spec.sub_digits)
        instruction = t("sub_instruction", lang=spec.lang)
        score_max = count
    else:
        title = t("answer_key_title", lang=spec.lang)
        subtitle = t("sub_answer_subtitle", lang=spec.lang, digits=spec.sub_digits)
        instruction = t("answer_key_instruction", lang=spec.lang)
        score_max = None

    draw_header(
        c,
        title=title,
        subtitle=subtitle,
        instruction=instruction,
        lang=spec.lang,
        is_answer=is_answer,
        score_max=score_max,
    )

    # 2. Cards grid layout
    cols = 4
    rows = count // cols  # 4 for 16 cards, 5 for 20 cards
    gap_x = 9.0
    gap_y = 9.0
    start_y = PAGE_H - 84.0
    bottom_y = 44.0

    card_w = (CONTENT_W - (cols - 1) * gap_x) / cols
    card_h = (start_y - bottom_y - (rows - 1) * gap_y) / rows

    for r in range(rows):
        for c_idx in range(cols):
            idx = r * cols + c_idx
            if idx >= len(problems):
                break
            x = MARGIN_X + c_idx * (card_w + gap_x)
            y = start_y - (r + 1) * card_h - r * gap_y
            _draw_arithmetic_card(
                c,
                x=x,
                y=y,
                w=card_w,
                h=card_h,
                q_num=idx + 1,
                problem=problems[idx],
                op="-",
                num_digit_cols=num_digit_cols,
                is_answer=is_answer,
            )

    # 3. Footer
    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def _draw_reference_table(
    c: Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    t_num: int,
    lang: str,
) -> None:
    """Draw a single multiplication reference table showing rows 1 through 12."""
    c.saveState()

    # Outer border
    rounded_box(c, x, y, w, h, radius=6.0, stroke=1, fill=0, line_width=0.85)

    # Header pill
    header_h = 26.0 if h <= 360.0 else 30.0
    c.setFillColor(COLOR_PILL_BG)
    c.roundRect(x, y + h - header_h, w, header_h, 6.0, stroke=0, fill=1)
    # Square bottom corners of header
    c.rect(x, y + h - header_h, w, 6.0, stroke=0, fill=1)

    # Dividing rule below header
    ruled_line(
        c,
        x,
        y + h - header_h,
        x + w,
        y + h - header_h,
        stroke_color=COLOR_BLACK,
        line_width=0.8,
    )

    # Header title
    title_text = t("sifir_table_header", lang=lang, table=t_num)
    title_font_size = 11.5 if h <= 360.0 else 13.0
    c.setFont("Helvetica-Bold", title_font_size)
    c.setFillColor(COLOR_BLACK)
    title_baseline = y + h - header_h + (header_h - 10.0) / 2.0
    c.drawCentredString(x + w / 2.0, title_baseline, title_text)

    # 12 equation rows
    row_h = (h - header_h) / 12.0
    font_size = 10.5 if h <= 360.0 else 12.5

    for i in range(1, 13):
        ry = y + h - header_h - i * row_h

        # Alternating subtle row shading
        if i % 2 == 0:
            c.setFillColor(HexColor("#fafafa"))
            c.rect(x + 0.5, ry, w - 1.0, row_h, stroke=0, fill=1)

        # Subtle row separator
        if i < 12:
            ruled_line(c, x, ry, x + w, ry, stroke_color=COLOR_FAINT, line_width=0.4)

        prod = i * t_num
        eq_str = f"{i}  ×  {t_num}  =  {prod}"
        baseline_y = ry + (row_h - font_size * 0.8) / 2.0

        c.setFont("Helvetica-Bold", font_size)
        c.setFillColor(COLOR_BLACK)
        c.drawCentredString(x + w / 2.0, baseline_y, eq_str)

    c.restoreState()


def draw_sifir_ref(
    c: Canvas,
    spec: Spec,
    tables: Sequence[int],
    page_num: int,
    total_pages: int,
    is_answer: bool = False,
) -> None:
    """Render a multiplication reference sheet showing up to 6 tables."""
    tables_str = ", ".join(str(x) for x in sorted(tables))
    title = t("sifir_ref_title", lang=spec.lang)
    subtitle = t("sifir_ref_subtitle", lang=spec.lang, tables=tables_str)
    instruction = t("sifir_ref_instruction", lang=spec.lang)

    draw_header(
        c,
        title=title,
        subtitle=subtitle,
        instruction=instruction,
        lang=spec.lang,
        is_answer=False,
        score_max=None,
    )

    n_tables = len(tables)
    start_y = PAGE_H - 84.0
    bottom_y = 44.0
    available_h = start_y - bottom_y
    gap_x = 12.0
    gap_y = 12.0

    if n_tables <= 1:
        cols, rows = 1, 1
        table_w = 230.0
        table_h = 490.0
    elif n_tables <= 2:
        cols, rows = 2, 1
        table_w = 220.0
        table_h = 490.0
    elif n_tables <= 3:
        cols, rows = 3, 1
        table_w = (CONTENT_W - 2 * gap_x) / 3.0
        table_h = 490.0
    elif n_tables <= 4:
        cols, rows = 2, 2
        table_w = 220.0
        table_h = (available_h - gap_y) / 2.0
    else:
        cols, rows = 3, 2
        table_w = (CONTENT_W - 2 * gap_x) / 3.0
        table_h = (available_h - gap_y) / 2.0

    total_grid_h = rows * table_h + (rows - 1) * gap_y
    grid_top_y = start_y - (available_h - total_grid_h) / 2.0

    for r in range(rows):
        if r == 0:
            count_in_row = min(cols, n_tables)
        else:
            count_in_row = n_tables - cols

        row_total_w = count_in_row * table_w + (count_in_row - 1) * gap_x
        row_start_x = MARGIN_X + (CONTENT_W - row_total_w) / 2.0
        y = grid_top_y - (r + 1) * table_h - r * gap_y

        for col_idx in range(count_in_row):
            t_idx = r * cols + col_idx
            if t_idx >= n_tables:
                break
            x = row_start_x + col_idx * (table_w + gap_x)
            _draw_reference_table(
                c,
                x=x,
                y=y,
                w=table_w,
                h=table_h,
                t_num=tables[t_idx],
                lang=spec.lang,
            )

    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def _sifir_grid_dimensions(count: int) -> tuple[int, int]:
    """Return (cols, rows) for adapting sifir practice cards to 1..24."""
    if count <= 1:
        return 1, 1
    if count <= 2:
        return 2, 1
    if count <= 3:
        return 3, 1
    if count <= 4:
        return 2, 2
    if count <= 6:
        return 3, 2
    if count <= 8:
        return 4, 2
    if count <= 9:
        return 3, 3
    if count <= 12:
        return 3, 4
    if count <= 16:
        return 4, 4
    if count <= 20:
        return 4, 5
    return 4, 6


def draw_sifir(
    c: Canvas,
    spec: Spec,
    problems: Sequence[ArithmeticProblem],
    is_answer: bool,
    page_num: int,
    total_pages: int,
) -> None:
    """Render a vertical multiplication practice sheet or answer sheet."""
    count = len(problems)
    tables_str = ", ".join(str(x) for x in sorted(spec.sifir_tables))

    # 1. Header
    if not is_answer:
        title = t("sifir_title", lang=spec.lang)
        subtitle = t("sifir_subtitle", lang=spec.lang, tables=tables_str)
        instruction = t("sifir_instruction", lang=spec.lang)
        score_max = count
    else:
        title = t("answer_key_title", lang=spec.lang)
        subtitle = t("sifir_answer_subtitle", lang=spec.lang, tables=tables_str)
        instruction = t("answer_key_instruction", lang=spec.lang)
        score_max = None

    draw_header(
        c,
        title=title,
        subtitle=subtitle,
        instruction=instruction,
        lang=spec.lang,
        is_answer=is_answer,
        score_max=score_max,
    )

    # 2. Adaptive card layout
    cols, rows = _sifir_grid_dimensions(count)
    gap_x = 9.0
    gap_y = 9.0
    start_y = PAGE_H - 84.0
    bottom_y = 44.0
    available_h = start_y - bottom_y

    if count <= 4:
        card_w = min(180.0, (CONTENT_W - (cols - 1) * gap_x) / cols)
        card_h = min(150.0, (available_h - (rows - 1) * gap_y) / rows)
    else:
        card_w = (CONTENT_W - (cols - 1) * gap_x) / cols
        card_h = (available_h - (rows - 1) * gap_y) / rows

    total_grid_w = cols * card_w + (cols - 1) * gap_x
    origin_x = MARGIN_X + (CONTENT_W - total_grid_w) / 2.0
    total_grid_h = rows * card_h + (rows - 1) * gap_y
    origin_y = start_y - (available_h - total_grid_h) / 2.0

    for r in range(rows):
        for c_idx in range(cols):
            idx = r * cols + c_idx
            if idx >= count:
                break
            x = origin_x + c_idx * (card_w + gap_x)
            y = origin_y - (r + 1) * card_h - r * gap_y
            _draw_arithmetic_card(
                c,
                x=x,
                y=y,
                w=card_w,
                h=card_h,
                q_num=idx + 1,
                problem=problems[idx],
                op="×",
                num_digit_cols=3,
                is_answer=is_answer,
            )

    # 3. Footer
    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def draw_sifir_answers(
    c: Canvas,
    spec: Spec,
    problems: Sequence[ArithmeticProblem],
    page_num: int,
    total_pages: int,
) -> None:
    """Render answer sheet for multiplication practice."""
    draw_sifir(c, spec, problems, is_answer=True, page_num=page_num, total_pages=total_pages)


def _draw_division_card(
    c: Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    q_num: int,
    problem: DivisionProblem,
    is_answer: bool,
    lang: str,
) -> None:
    """Draw fresh long division, ending each working row at its dividend column."""
    c.saveState()
    rounded_box(c, x, y, w, h)
    badge_number(c, x + 12, y + h - 12, q_num)
    digits = len(str(problem.dividend))
    cell = 14.0
    gx = x + (w - (digits + 2) * cell) / 2 + 2 * cell
    baseline = y + h - 55
    c.setFillColor(COLOR_BLACK)
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(gx - 10, baseline, str(problem.divisor))
    ruled_line(c, gx - 4, baseline - 4, gx - 4, baseline + 13)
    ruled_line(c, gx - 4, baseline + 13, gx + digits * cell, baseline + 13)
    _draw_aligned_number(c, problem.dividend, 0, gx, baseline - 2, cell, cell, digits, font_size=13)

    if is_answer:
        _draw_aligned_number(
            c, problem.quotient, 0, gx, baseline + 17 - 2, cell, cell, digits, font_size=13
        )
        for index, step in enumerate(problem.steps):
            # The next partial combines this difference with the next digit.
            # Zero quotient steps still draw a zero product and a subtraction rule.
            partial_y = baseline - index * 2 * cell
            if index:
                _draw_aligned_number(
                    c, step.partial, 0, gx, partial_y - 2, cell, cell, step.col + 1,
                    font_size=13,
                )
            product_y = partial_y - cell
            _draw_aligned_number(
                c, step.product, 0, gx, product_y - 2, cell, cell, step.col + 1,
                font_size=13,
            )
            left = gx + (step.col + 1 - len(str(step.partial))) * cell
            c.drawRightString(left - 2, product_y, "-")
            ruled_line(c, left, product_y - 3, gx + (step.col + 1) * cell, product_y - 3)
        final_y = baseline - len(problem.steps) * 2 * cell
        _draw_aligned_number(
            c, problem.remainder, 0, gx, final_y - 2, cell, cell, digits, font_size=13
        )
        c.setFont("Helvetica", 8.5)
        c.drawCentredString(
            x + w / 2, y + 11,
            t("div_result", lang=lang, dividend=problem.dividend, divisor=problem.divisor,
              quotient=problem.quotient, remainder=problem.remainder),
        )
    c.restoreState()


def draw_div(
    c: Canvas,
    spec: Spec,
    problems: Sequence[DivisionProblem],
    is_answer: bool,
    page_num: int,
    total_pages: int,
) -> None:
    """Render division cards with working space or complete column-aligned working."""
    subtitle_key = "div_subtitle_remainder" if spec.div_rem else "div_subtitle_exact"
    draw_header(
        c,
        title=t("answer_key_title" if is_answer else "div_title", lang=spec.lang),
        subtitle=t("div_answer_subtitle" if is_answer else subtitle_key,
                   lang=spec.lang, digits=spec.div_digits),
        instruction=t("answer_key_instruction" if is_answer else "div_instruction", lang=spec.lang),
        lang=spec.lang,
        is_answer=is_answer,
        score_max=None if is_answer else len(problems),
    )
    cols, rows = (2, 4) if spec.div_digits == 3 else (3, 4)
    gap = 9.0
    top = PAGE_H - 84
    card_w = (CONTENT_W - (cols - 1) * gap) / cols
    card_h = (top - 44 - (rows - 1) * gap) / rows
    for index, problem in enumerate(problems):
        row, col = divmod(index, cols)
        _draw_division_card(
            c, MARGIN_X + col * (card_w + gap), top - (row + 1) * card_h - row * gap,
            card_w, card_h, index + 1, problem, is_answer, spec.lang,
        )
    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def draw_div_answers(
    c: Canvas,
    spec: Spec,
    problems: Sequence[DivisionProblem],
    page_num: int,
    total_pages: int,
) -> None:
    """Render the full long-division answer sheet for a practice sheet."""
    draw_div(c, spec, problems, is_answer=True, page_num=page_num, total_pages=total_pages)


def _draw_counting_card(
    c: Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    q_num: int,
    problem: CountingProblem,
    is_answer: bool,
) -> None:
    """Draw a single counting box with shapes and an answer box."""
    c.saveState()
    rounded_box(c, x, y, w, h)
    badge_number(c, x + 12, y + h - 12, q_num)

    ans_box_w = 46.0
    ans_box_h = 28.0
    ans_x = x + (w - ans_box_w) / 2
    ans_y = y + 10.0

    rounded_box(
        c,
        ans_x,
        ans_y,
        ans_box_w,
        ans_box_h,
        radius=4.0,
        stroke=1,
        fill=1,
        fill_color=COLOR_PILL_BG,
        line_width=1.0,
    )

    if is_answer:
        c.setFillColor(COLOR_BLACK)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(ans_x + ans_box_w / 2, ans_y + 8.0, str(problem.count))

    draw_margin_x = 10.0
    draw_x = x + draw_margin_x
    draw_w = w - 2 * draw_margin_x
    draw_y = ans_y + ans_box_h + 8.0
    draw_h = (y + h - 18.0) - draw_y

    cols = problem.grid_cols
    rows = problem.grid_rows
    cell_w = draw_w / cols
    cell_h = draw_h / rows
    shape_size = min(cell_w, cell_h) * 0.82

    for col, row in problem.positions:
        cx = draw_x + (col + 0.5) * cell_w
        cy = draw_y + (rows - 1 - row + 0.5) * cell_h
        draw_shape(c, problem.shape, cx, cy, shape_size)

    c.restoreState()


def draw_count(
    c: Canvas,
    spec: Spec,
    problems: Sequence[CountingProblem],
    is_answer: bool,
    page_num: int,
    total_pages: int,
) -> None:
    """Render a picture counting practice sheet or answer sheet."""
    draw_header(
        c,
        title=t("answer_key_title" if is_answer else "count_title", lang=spec.lang),
        subtitle=t(
            "count_answer_subtitle" if is_answer else "count_subtitle",
            lang=spec.lang,
            max=spec.count_max,
        ),
        instruction=t(
            "answer_key_instruction" if is_answer else "count_instruction",
            lang=spec.lang,
        ),
        lang=spec.lang,
        is_answer=is_answer,
        score_max=None if is_answer else len(problems),
    )
    cols = 3
    rows = 4
    gap = 9.0
    top = PAGE_H - 84.0
    card_w = (CONTENT_W - (cols - 1) * gap) / cols
    card_h = (top - 44.0 - (rows - 1) * gap) / rows
    for index, problem in enumerate(problems):
        row, col = divmod(index, cols)
        _draw_counting_card(
            c,
            MARGIN_X + col * (card_w + gap),
            top - (row + 1) * card_h - row * gap,
            card_w,
            card_h,
            index + 1,
            problem,
            is_answer,
        )
    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def draw_count_answers(
    c: Canvas,
    spec: Spec,
    problems: Sequence[CountingProblem],
    page_num: int,
    total_pages: int,
) -> None:
    """Render the counting answer sheet for a practice sheet."""
    draw_count(c, spec, problems, is_answer=True, page_num=page_num, total_pages=total_pages)


def draw_trace(
    c: Canvas,
    spec: Spec,
    letters: Sequence[str],
    page_num: int,
    total_pages: int,
    is_answer: bool = False,
) -> None:
    """Render an alphabet letter tracing practice sheet with ruled guidelines."""
    sub_key = "trace_subtitle_upper" if spec.abc_case == "upper" else "trace_subtitle_lower"
    draw_header(
        c,
        title=t("trace_title", lang=spec.lang),
        subtitle=t(sub_key, lang=spec.lang),
        instruction=t("trace_instruction", lang=spec.lang),
        lang=spec.lang,
        is_answer=False,
        score_max=None,
    )

    num_rows = len(letters)
    top = PAGE_H - 84.0
    bottom = 44.0
    available_h = top - bottom
    gap = 14.0
    row_h = (available_h - (num_rows - 1) * gap) / num_rows
    # Height of glyph measured to cap line in points
    glyph_h = 56.0

    for idx, char in enumerate(letters):
        card_x = MARGIN_X
        card_y = top - (idx + 1) * row_h - idx * gap
        card_w = CONTENT_W

        # Outer card container
        rounded_box(
            c, card_x, card_y, card_w, row_h, radius=6.0, stroke=1, fill=0, line_width=0.85
        )

        # Question / row number badge
        badge_number(c, card_x + 14.0, card_y + row_h - 14.0, idx + 1)

        # Ruled writing lines span horizontally across the card
        line_x1 = card_x + 24.0
        line_x2 = card_x + card_w - 24.0
        y_base = card_y + 46.0

        # Cap line (solid)
        ruled_line(
            c,
            line_x1,
            y_base + glyph_h,
            line_x2,
            y_base + glyph_h,
            stroke_color=COLOR_LIGHT,
            line_width=0.75,
        )

        # Midline (dashed x-height line)
        c.saveState()
        c.setStrokeColor(COLOR_LIGHT)
        c.setLineWidth(0.75)
        c.setDash([3.5, 3.5])
        c.line(line_x1, y_base + 0.5 * glyph_h, line_x2, y_base + 0.5 * glyph_h)
        c.restoreState()

        # Baseline (solid)
        ruled_line(c, line_x1, y_base, line_x2, y_base, stroke_color=COLOR_MID, line_width=0.9)

        # Solid model letter at left on the ruled lines
        model_x = line_x1 + 14.0
        draw_letter(c, char, model_x, y_base, glyph_h, dotted=False)
        w = letter_width(char, glyph_h)

        # Subtle vertical dashed divider separating model letter from tracing area
        divider_x = model_x + w + 18.0
        c.saveState()
        c.setStrokeColor(COLOR_LIGHT)
        c.setLineWidth(0.6)
        c.setDash([2.5, 2.5])
        c.line(divider_x, card_y + 16.0, divider_x, card_y + row_h - 16.0)
        c.restoreState()

        # Dotted repeats filling the row on the ruled lines
        practice_start_x = divider_x + 18.0
        practice_end_x = line_x2 - 14.0
        avail_w = practice_end_x - practice_start_x
        repeat_step = max(w + 20.0, 52.0)
        num_repeats = max(3, int(avail_w / repeat_step))
        step = (avail_w - w) / (num_repeats - 1) if num_repeats > 1 else 0.0

        for r_idx in range(num_repeats):
            rep_x = practice_start_x + r_idx * step
            draw_letter(c, char, rep_x, y_base, glyph_h, dotted=True)

    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def draw_missing(
    c: Canvas,
    spec: Spec,
    problems: Sequence[MissingRow],
    is_answer: bool,
    page_num: int,
    total_pages: int,
) -> None:
    """Render a missing-letters alphabet practice sheet or answer sheet."""
    if not is_answer:
        title = t("missing_title", lang=spec.lang)
        sub_key = (
            "missing_subtitle_upper" if spec.abc_case == "upper" else "missing_subtitle_lower"
        )
        subtitle = t(sub_key, lang=spec.lang)
        instruction = t("missing_instruction", lang=spec.lang)
        score_max = len(problems) * spec.missing_blanks
    else:
        title = t("answer_key_title", lang=spec.lang)
        subtitle = t("missing_answer_subtitle", lang=spec.lang)
        instruction = t("answer_key_instruction", lang=spec.lang)
        score_max = None

    draw_header(
        c,
        title=title,
        subtitle=subtitle,
        instruction=instruction,
        lang=spec.lang,
        is_answer=is_answer,
        score_max=score_max,
    )

    num_rows = len(problems)
    top = PAGE_H - 84.0
    bottom = 44.0
    available_h = top - bottom
    gap = 10.0
    row_h = (available_h - (num_rows - 1) * gap) / num_rows

    boxes_start_x = MARGIN_X + 32.0
    avail_w = CONTENT_W - 32.0
    box_gap = 7.0
    box_w = (avail_w - 5 * box_gap) / 6.0

    for row_idx, row_data in enumerate(problems):
        row_y = top - (row_idx + 1) * row_h - row_idx * gap

        # Row number badge
        badge_number(c, MARGIN_X + 12.0, row_y + row_h / 2.0, row_idx + 1)

        # 6 consecutive letter boxes
        for col_idx, letter in enumerate(row_data.letters):
            box_x = boxes_start_x + col_idx * (box_w + box_gap)
            is_blank = col_idx in row_data.blanks

            if is_blank and is_answer:
                # Answer blank: highlighted background with filled answer
                rounded_box(
                    c,
                    box_x,
                    row_y,
                    box_w,
                    row_h,
                    radius=5.0,
                    stroke=1,
                    fill=1,
                    fill_color=COLOR_ANSWER_BG,
                    line_width=1.0,
                )
                c.setFillColor(COLOR_BLACK)
                c.setFont("Helvetica-Bold", 19)
                c.drawCentredString(box_x + box_w / 2.0, row_y + (row_h - 14.0) / 2.0, letter)
            elif is_blank and not is_answer:
                # Practice blank: empty box for pupil to write in
                rounded_box(
                    c,
                    box_x,
                    row_y,
                    box_w,
                    row_h,
                    radius=5.0,
                    stroke=1,
                    fill=0,
                    line_width=0.85,
                )
            else:
                # Given letter
                rounded_box(
                    c,
                    box_x,
                    row_y,
                    box_w,
                    row_h,
                    radius=5.0,
                    stroke=1,
                    fill=0,
                    line_width=0.85,
                )
                c.setFillColor(COLOR_BLACK)
                c.setFont("Helvetica-Bold", 19)
                c.drawCentredString(box_x + box_w / 2.0, row_y + (row_h - 14.0) / 2.0, letter)

    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def draw_missing_answers(
    c: Canvas,
    spec: Spec,
    problems: Sequence[MissingRow],
    page_num: int,
    total_pages: int,
) -> None:
    """Render the missing-letters answer sheet for a practice sheet."""
    draw_missing(c, spec, problems, is_answer=True, page_num=page_num, total_pages=total_pages)


def draw_match(
    c: Canvas,
    spec: Spec,
    problems: Sequence[MatchSet],
    is_answer: bool,
    page_num: int,
    total_pages: int,
) -> None:
    """Render a letter matching practice sheet or answer sheet."""
    if not is_answer:
        title = t("match_title", lang=spec.lang)
        subtitle = t("match_subtitle", lang=spec.lang)
        instruction = t("match_instruction", lang=spec.lang)
        score_max = len(problems) * MATCH_PAIRS
    else:
        title = t("answer_key_title", lang=spec.lang)
        subtitle = t("match_answer_subtitle", lang=spec.lang)
        instruction = t("answer_key_instruction", lang=spec.lang)
        score_max = None

    draw_header(
        c,
        title=title,
        subtitle=subtitle,
        instruction=instruction,
        lang=spec.lang,
        is_answer=is_answer,
        score_max=score_max,
    )

    num_cards = len(problems)
    top = PAGE_H - 84.0
    bottom = 44.0
    available_h = top - bottom
    gap = 14.0
    card_h = (available_h - (num_cards - 1) * gap) / num_cards

    for card_idx, match_set in enumerate(problems):
        card_x = MARGIN_X
        card_y = top - (card_idx + 1) * card_h - card_idx * gap
        card_w = CONTENT_W

        # Card container
        rounded_box(
            c, card_x, card_y, card_w, card_h, radius=6.0, stroke=1, fill=0, line_width=0.85
        )

        # Question / card badge
        badge_number(c, card_x + 14.0, card_y + card_h - 14.0, card_idx + 1)

        left_char_x = card_x + 48.0
        left_dot_x = card_x + 85.0
        right_dot_x = card_x + card_w - 85.0
        right_char_x = card_x + card_w - 48.0

        usable_top = card_y + card_h - 28.0
        usable_bottom = card_y + 28.0
        n_items = len(match_set.left)
        item_step = (usable_top - usable_bottom) / (n_items - 1) if n_items > 1 else 0.0

        # Draw left uppercase column and right lowercase column
        c.setFont("Helvetica-Bold", 17)
        c.setFillColor(COLOR_BLACK)

        for k, char in enumerate(match_set.left):
            y = usable_top - k * item_step
            c.drawCentredString(left_char_x, y - 5.5, char)
            c.circle(left_dot_x, y, 3.2, stroke=0, fill=1)

        for k, char in enumerate(match_set.right):
            y = usable_top - k * item_step
            c.drawCentredString(right_char_x, y - 5.5, char)
            c.circle(right_dot_x, y, 3.2, stroke=0, fill=1)

        # On answer sheet, draw matching connecting lines and pair text summary
        if is_answer:
            c.saveState()
            c.setStrokeColor(COLOR_BLACK)
            c.setLineWidth(1.2)
            for left_idx, right_idx in enumerate(match_set.pairs):
                y_left = usable_top - left_idx * item_step
                y_right = usable_top - right_idx * item_step
                c.line(left_dot_x, y_left, right_dot_x, y_right)
            c.restoreState()

            pairs_text = "   ".join(
                f"{match_set.left[k]} - {match_set.right[match_set.pairs[k]]}"
                for k in range(n_items)
            )
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(COLOR_MID)
            c.drawCentredString(card_x + card_w / 2.0, card_y + 9.0, pairs_text)

    draw_footer(c, page_num=page_num, total_pages=total_pages, lang=spec.lang)


def draw_match_answers(
    c: Canvas,
    spec: Spec,
    problems: Sequence[MatchSet],
    page_num: int,
    total_pages: int,
) -> None:
    """Render the letter matching answer sheet for a practice sheet."""
    draw_match(c, spec, problems, is_answer=True, page_num=page_num, total_pages=total_pages)


