"""Tests for worksheet PDF rendering pipeline."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from random import Random
from unittest.mock import MagicMock

import pytest
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from modules.alphabet import match_sets, missing_rows, picture_items, scramble
from modules.i18n import t
from modules.layout import MATCH_PAIRS, cards_per_sheet, plan_sheets
from modules.problems import (
    DivisionProblem,
    addition,
    counting,
    division,
    division_steps,
    grid_blanks,
    multiplication,
    subtraction,
)
from modules.render import pages
from modules.render.pages import (
    draw_div_answers,
    draw_match,
)
from modules.render.pdf import render
from modules.render.primitives import CONTENT_W, MARGIN_X, PAGE_H
from modules.spec import Spec, parse_spec


def _page_text_positions(page):
    """Collect (text, x, y) for each non-empty text run via pypdf's visitor."""
    collected = []

    def visitor(text, current_matrix, text_matrix, font, size):
        stripped = text.strip()
        if stripped:
            collected.append((stripped, text_matrix[4], text_matrix[5]))

    page.extract_text(visitor_text=visitor)
    return collected


def _arithmetic_answer_boxes(count):
    """Recompute each 4-column arithmetic card box and its answer-row baseline.

    Mirrors the layout in modules.render.pages so the check can require the
    answer to land in its own card's answer row instead of matching a stray digit
    in an operand, operator, or question badge elsewhere on the sheet.
    """
    cols = 4
    rows = count // cols
    gap = 9.0
    start_y = PAGE_H - 84.0
    bottom_y = 44.0
    card_w = (CONTENT_W - (cols - 1) * gap) / cols
    card_h = (start_y - bottom_y - (rows - 1) * gap) / rows
    boxes = []
    for r in range(rows):
        for col in range(cols):
            idx = r * cols + col
            if idx >= count:
                break
            x = MARGIN_X + col * (card_w + gap)
            y = start_y - (r + 1) * card_h - r * gap
            gh = 20.0 if card_h > 140.0 else 18.0
            gy = y + (card_h - 4 * gh) / 2.0 - 5.0
            answer_y = gy + (gh - 10.0) / 2.0
            boxes.append((x, y, card_w, card_h, answer_y))
    return boxes


def _assert_arithmetic_answers(page, problems):
    """Assert each problem's answer is the single text run in its card's answer row.

    The answer row is the only grid row that carries the answer, so requiring a
    lone run at that baseline both proves the answer is printed and makes the
    number of answer entries equal the number of problems.
    """
    boxes = _arithmetic_answer_boxes(len(problems))
    positions = _page_text_positions(page)
    assert len(boxes) == len(problems)
    for (x, _y, w, _h, answer_y), problem in zip(boxes, problems, strict=True):
        row = [
            text
            for text, tx, ty in positions
            if x <= tx <= x + w and abs(ty - answer_y) < 1.0
        ]
        assert row == [str(problem.answer)], (problem.answer, row)


def test_not_implemented_topics() -> None:
    """Renderer must raise NotImplementedError naming unhandled topics."""
    spec = Spec(t=("unknown_topic",), pages=1, ans=0, seed=1)
    with pytest.raises(NotImplementedError) as exc_info:
        render(spec)
    assert "unknown_topic" in str(exc_info.value)


def test_page_count_a4_and_metadata() -> None:
    """PDF must match plan_sheets page count, A4 geometry, and CetakPintar metadata."""
    spec = Spec(t=("grid", "add", "sub"), pages=3, ans=1, seed=42)
    expected_sheets = plan_sheets(spec)

    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))

    # Page count
    assert len(reader.pages) == len(expected_sheets)
    assert len(reader.pages) == 6  # 3 content + 3 answers

    # Metadata
    assert reader.metadata is not None
    assert reader.metadata.title == "CetakPintar"
    assert reader.metadata.author == "CetakPintar"

    # A4 geometry: width ~595.28, height ~841.89
    for page in reader.pages:
        box = page.mediabox
        assert pytest.approx(float(box.width), 0.1) == 595.28
        assert pytest.approx(float(box.height), 0.1) == 841.89


@pytest.mark.parametrize("lang", ["ms", "en"])
def test_grid_rendering_and_answers(lang: str) -> None:
    """Grid start 1 and 901 render correctly and extracted answers match expected blanks."""
    for start in (1, 901):
        spec = Spec(
            t=("grid",),
            pages=1,
            ans=1,
            seed=777,
            grid_start=start,
            grid_blanks=30,
            lang=lang,
        )
        pdf_bytes = render(spec)
        reader = PdfReader(io.BytesIO(pdf_bytes))

        assert len(reader.pages) == 2

        content_text = reader.pages[0].extract_text()
        answer_text = reader.pages[1].extract_text()

        rng = Random(777)
        blanks = grid_blanks(rng, start, 30)

        # Check that header reflects language
        if lang == "ms":
            assert "CARTA NOMBOR 100" in content_text
            assert "SKEMA JAWAPAN" in answer_text
            assert "[SKEMA JAWAPAN]" not in answer_text
            assert "Untuk guru / ibu bapa" in answer_text
            assert "CetakPintar" in content_text
            assert "Halaman 1 / 2" in content_text
        else:
            assert "100-NUMBER GRID" in content_text
            assert "ANSWER KEY" in answer_text
            assert "[ANSWER KEY]" not in answer_text
            assert "For teachers and parents" in answer_text
            assert "CetakPintar" in content_text
            assert "Page 1 of 2" in content_text

        # 901 grid includes 1000
        if start == 901:
            assert "1000" in answer_text

        # All 30 blank numbers must be present on the answer page
        for b in blanks:
            assert str(b) in answer_text


@pytest.mark.parametrize("digits", [1, 2, 3])
@pytest.mark.parametrize("regroup", [0, 1])
def test_addition_rendering_and_answers(digits: int, regroup: int) -> None:
    """Addition with 1, 2, 3 digits and regrouping extracts expected answers."""
    spec = Spec(
        t=("add",),
        pages=1,
        ans=1,
        seed=100 + digits,
        add_digits=digits,
        add_regroup=regroup,
    )
    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))

    assert len(reader.pages) == 2
    count = cards_per_sheet(spec, "add")
    assert count in (16, 20)

    rng = Random(100 + digits)
    expected_probs = addition(rng, digits, bool(regroup), count)

    _assert_arithmetic_answers(reader.pages[1], expected_probs)


@pytest.mark.parametrize("digits", [1, 2, 3])
@pytest.mark.parametrize("borrow", [0, 1])
def test_subtraction_rendering_and_answers(digits: int, borrow: int) -> None:
    """Subtraction with 1, 2, 3 digits and borrowing extracts expected answers."""
    if digits == 1 and borrow == 1:
        return  # Impossible combination rejected by spec

    spec = Spec(
        t=("sub",),
        pages=1,
        ans=1,
        seed=200 + digits,
        sub_digits=digits,
        sub_borrow=borrow,
    )
    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))

    assert len(reader.pages) == 2
    count = cards_per_sheet(spec, "sub")
    assert count in (16, 20)

    rng = Random(200 + digits)
    expected_probs = subtraction(rng, digits, bool(borrow), count)

    _assert_arithmetic_answers(reader.pages[1], expected_probs)


def test_four_digit_sum_overflow_in_addition() -> None:
    """Three-digit addition sums up to 4 digits fit and are extracted intact."""
    # Find a seed or test cases with 4-digit sums
    spec = Spec(t=("add",), pages=1, ans=1, seed=999, add_digits=3, add_regroup=1)
    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))

    rng = Random(999)
    probs = addition(rng, 3, True, 16)
    has_four_digits = any(p.answer >= 1000 for p in probs)
    assert has_four_digits

    answer_text = reader.pages[1].extract_text()
    for p in probs:
        assert str(p.answer) in answer_text


def test_multi_page_round_robin_sheets() -> None:
    """Multi-page sheets render all pages with correct page counts and sequence."""
    spec = Spec(t=("grid", "add", "sub"), pages=5, ans=1, seed=123)
    sheets = plan_sheets(spec)
    assert len(sheets) == 10  # 5 content + 5 answers

    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 10

    # Verify footers reflect total pages
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        assert f"Halaman {i} / 10" in text


def test_determinism_across_subprocesses() -> None:
    """Byte-identical output for the same spec across processes with different PYTHONHASHSEED."""
    code = """
import sys
from modules.spec import Spec
from modules.render.pdf import render

spec = Spec(
    t=('grid', 'add', 'sub', 'trace', 'missing', 'match'),
    pages=6,
    ans=1,
    seed=98765,
    grid_start=101,
    add_digits=2,
    add_regroup=1,
    sub_digits=2,
    sub_borrow=1,
    abc_case='upper',
    missing_blanks=2,
)
pdf_bytes = render(spec)
sys.stdout.buffer.write(pdf_bytes)
"""

    env1 = dict(os.environ, PYTHONHASHSEED="0")
    env2 = dict(os.environ, PYTHONHASHSEED="123456789")

    proc1 = subprocess.run(
        [sys.executable, "-c", code],
        env=env1,
        capture_output=True,
        check=True,
    )
    proc2 = subprocess.run(
        [sys.executable, "-c", code],
        env=env2,
        capture_output=True,
        check=True,
    )

    assert len(proc1.stdout) > 0
    assert proc1.stdout == proc2.stdout


@pytest.mark.parametrize(
    ("tables", "expected_sheets"),
    [
        ((7,), 1),
        ((1, 2, 3, 4, 5, 6), 1),
        ((1, 2, 3, 4, 5, 6, 7), 2),
        (tuple(range(1, 13)), 2),
    ],
)
@pytest.mark.parametrize("lang", ["ms", "en"])
def test_sifir_ref_rendering_sheet_counts(
    tables: tuple[int, ...], expected_sheets: int, lang: str
) -> None:
    """Multiplication reference tables render 1, 6, 7, and 12 tables matching plan_sheets."""
    spec = Spec(
        t=("sifir_ref",),
        pages=expected_sheets,
        ans=1,  # ans=1 has no effect on sifir_ref since ref has no answer sheet
        seed=123,
        sifir_tables=tables,
        lang=lang,
    )
    planned = plan_sheets(spec)
    assert len(planned) == expected_sheets

    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == expected_sheets

    # Metadata and A4 checks
    assert reader.metadata is not None
    assert reader.metadata.title == "CetakPintar"
    assert reader.metadata.author == "CetakPintar"

    # Verify extracted text
    page1_text = reader.pages[0].extract_text()
    if lang == "ms":
        assert "JADUAL SIFIR" in page1_text
    else:
        assert "MULTIPLICATION TABLES" in page1_text

    if len(tables) == 1:
        # Table 7
        if lang == "ms":
            assert "SIFIR 7" in page1_text
        else:
            assert "TABLE 7" in page1_text
        # Products up to 12 x 7 = 84
        assert "84" in page1_text
    elif len(tables) >= 7:
        # Page 2 must contain table 7
        page2_text = reader.pages[1].extract_text()
        if lang == "ms":
            assert "SIFIR 7" in page2_text
        else:
            assert "TABLE 7" in page2_text


@pytest.mark.parametrize(
    ("tables", "sifir_n", "lang"),
    [
        ((7,), 1, "ms"),
        ((7,), 12, "ms"),
        ((2, 3, 4, 5), 24, "ms"),
        ((7,), 1, "en"),
        ((7,), 12, "en"),
        ((2, 3, 4, 5), 24, "en"),
    ],
)
def test_sifir_practice_rendering_and_answers(
    tables: tuple[int, ...], sifir_n: int, lang: str
) -> None:
    """Sifir practice with sifir_n=1, 12, 24 renders content and answers match products."""
    seed = 888
    spec = Spec(
        t=("sifir",),
        pages=1,
        ans=1,
        seed=seed,
        sifir_tables=tables,
        sifir_n=sifir_n,
        lang=lang,
    )
    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))

    assert len(reader.pages) == 2

    content_text = reader.pages[0].extract_text()
    answer_text = reader.pages[1].extract_text()

    if lang == "ms":
        assert "LATIHAN SIFIR" in content_text
        assert "SKEMA JAWAPAN" in answer_text
    else:
        assert "MULTIPLICATION PRACTICE" in content_text
        assert "ANSWER KEY" in answer_text

    rng = Random(seed)
    expected_probs = multiplication(rng, tables, sifir_n)
    for p in expected_probs:
        assert str(p.answer) in answer_text


def test_sifir_determinism_across_subprocesses() -> None:
    """Byte-identical output for sifir and sifir_ref across different PYTHONHASHSEED."""
    code = """
import sys
from modules.spec import Spec
from modules.render.pdf import render

spec = Spec(
    t=('sifir_ref', 'sifir'),
    pages=2,
    ans=1,
    seed=54321,
    sifir_tables=(2, 3, 4, 5),
    sifir_n=16,
)
pdf_bytes = render(spec)
sys.stdout.buffer.write(pdf_bytes)
"""

    env1 = dict(os.environ, PYTHONHASHSEED="0")
    env2 = dict(os.environ, PYTHONHASHSEED="999888777")

    proc1 = subprocess.run(
        [sys.executable, "-c", code],
        env=env1,
        capture_output=True,
        check=True,
    )
    proc2 = subprocess.run(
        [sys.executable, "-c", code],
        env=env2,
        capture_output=True,
        check=True,
    )

    assert len(proc1.stdout) > 0
    assert proc1.stdout == proc2.stdout



@pytest.mark.parametrize("digits", [2, 3])
@pytest.mark.parametrize("remainder", [0, 1])
@pytest.mark.parametrize("lang", ["ms", "en"])
def test_division_rendering_and_answers(digits, remainder, lang):
    spec = Spec(
        t=("div",), pages=1, ans=1, seed=31415, lang=lang,
        div_digits=digits, div_rem=remainder,
    )
    reader = PdfReader(io.BytesIO(render(spec)))
    assert len(reader.pages) == len(plan_sheets(spec)) == 2
    assert t("div_title", lang=lang) in reader.pages[0].extract_text()
    answers = reader.pages[1].extract_text()
    assert t("answer_key_title", lang=lang) in answers
    problems = division(Random(31415), digits, spec.div_divisors, bool(remainder),
                        cards_per_sheet(spec, "div"))
    for problem in problems:
        summary = t("div_result", lang=lang, dividend=problem.dividend,
                    divisor=problem.divisor, quotient=problem.quotient, remainder=problem.remainder)
        assert summary in answers
        assert summary not in reader.pages[0].extract_text()


def division_fixture_pdf(lang):
    """Build a review PDF using all five directed long-division fixtures."""
    problems = []
    for dividend, divisor in [(12, 9), (100, 4), (101, 5), (208, 2), (999, 9)]:
        quotient, remainder = divmod(dividend, divisor)
        problems.append(DivisionProblem(dividend, divisor, quotient, remainder,
                                        division_steps(dividend, divisor)))
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=A4, invariant=1)
    canvas.setTitle("CetakPintar")
    canvas.setAuthor("CetakPintar")
    spec = Spec(t=("div",), pages=1, seed=0, lang=lang, div_digits=3)
    draw_div_answers(canvas, spec, problems, 1, 1)
    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


@pytest.mark.parametrize("lang", ["ms", "en"])
def test_division_directed_working_alignment(lang):
    page = PdfReader(io.BytesIO(division_fixture_pdf(lang))).pages[0]
    positions = []

    def record_text(text, current_matrix, text_matrix, font, size):
        if text.strip():
            positions.append((text.strip(), text_matrix[4], text_matrix[5]))

    text = page.extract_text(visitor_text=record_text)
    for dividend, divisor in [(12, 9), (100, 4), (101, 5), (208, 2), (999, 9)]:
        quotient, remainder = divmod(dividend, divisor)
        assert t("div_result", lang=lang, dividend=dividend, divisor=divisor,
                 quotient=quotient, remainder=remainder) in text
        _, dividend_x, dividend_y = next(item for item in positions if item[0] == str(dividend))
        digits = len(str(dividend))

        def assert_number(value, col, baseline, origin_x=dividend_x):
            # Extracted text starts at the first digit. Compare its last digit's
            # position to the corresponding dividend column, independent of width.
            expected_x = origin_x + (col + 1 - len(str(value))) * 14
            assert any(
                value_text == str(value)
                and abs(x - expected_x) < 0.01
                and abs(y - baseline) < 0.01
                for value_text, x, y in positions
            ), (value, col, baseline)

        assert_number(quotient, digits - 1, dividend_y + 17)
        steps = division_steps(dividend, divisor)
        for index, step in enumerate(steps):
            if index:
                assert_number(step.partial, step.col, dividend_y - index * 28)
            assert_number(step.product, step.col, dividend_y - index * 28 - 14)
        assert_number(remainder, digits - 1, dividend_y - len(steps) * 28)


def test_division_mixed_sheets_without_answers():
    spec = Spec(t=("grid", "add", "sub", "sifir_ref", "sifir", "div"),
                pages=8, ans=0, seed=91, div_digits=3, div_rem=1)
    reader = PdfReader(io.BytesIO(render(spec)))
    assert len(reader.pages) == len(plan_sheets(spec)) == 8
    assert t("div_title") in reader.pages[5].extract_text()


def test_division_determinism_across_subprocesses():
    code = """
import sys
from modules.spec import Spec
from modules.render.pdf import render
spec = Spec(t=('div',), pages=2, seed=2147483647, div_digits=3, div_rem=1)
sys.stdout.buffer.write(render(spec))
"""
    outputs = [
        subprocess.run([sys.executable, "-c", code], capture_output=True, check=True,
                       env=dict(os.environ, PYTHONHASHSEED=hash_seed)).stdout
        for hash_seed in ("0", "987654321")
    ]
    assert outputs[0].startswith(b"%PDF-")
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("lang", ["ms", "en"])
def test_division_summary_has_normal_character_spacing(lang):
    page = PdfReader(io.BytesIO(division_fixture_pdf(lang))).pages[0]
    character_spacing = 0
    summaries = 0

    def check_spacing(operator, operands, current_matrix, text_matrix):
        nonlocal character_spacing, summaries
        if operator == b"Tc":
            character_spacing = float(operands[0])
        if operator == b"Tj" and b" = " in operands[0]:
            summaries += 1
            assert character_spacing == 0

    page.extract_text(visitor_operand_before=check_spacing)
    assert summaries == 5


@pytest.mark.parametrize("lang", ["ms", "en"])
@pytest.mark.parametrize("count_max", [5, 10, 20])
def test_count_rendering_and_answers(lang: str, count_max: int) -> None:
    spec = Spec(t=("count",), pages=1, ans=1, seed=54321, count_max=count_max, lang=lang)
    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))

    assert len(reader.pages) == 2
    content_text = reader.pages[0].extract_text()
    answer_text = reader.pages[1].extract_text()

    if lang == "ms":
        assert "KIRA DAN TULIS" in content_text
        assert "SKEMA JAWAPAN" in answer_text
    else:
        assert "COUNT AND WRITE" in content_text
        assert "ANSWER KEY" in answer_text

    rng = Random(54321)
    problems = counting(rng, count_max, spec.count_shapes, 12)
    for p in problems:
        assert str(p.count) in answer_text


@pytest.mark.parametrize("shape", ["star", "circle", "apple", "fish", "flower"])
def test_every_shape_renders(shape: str) -> None:
    spec = Spec(t=("count",), pages=1, ans=1, seed=99, count_shapes=(shape,))
    pdf_bytes = render(spec)
    assert pdf_bytes.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2


def test_count_determinism_across_subprocesses() -> None:
    code = """
import sys
from modules.spec import Spec
from modules.render.pdf import render
spec = Spec(t=('count',), pages=2, seed=12345, count_max=20)
sys.stdout.buffer.write(render(spec))
"""
    outputs = [
        subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            check=True,
            env=dict(os.environ, PYTHONHASHSEED=hash_seed),
        ).stdout
        for hash_seed in ("0", "987654321")
    ]
    assert outputs[0].startswith(b"%PDF-")
    assert outputs[0] == outputs[1]


def test_answer_check_detects_omitted_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Omitting the answer row must fail the per-card answer check (review M7)."""
    spec = Spec(t=("add",), pages=1, ans=1, seed=101, add_digits=1, add_regroup=1)
    count = cards_per_sheet(spec, "add")
    expected_probs = addition(Random(101), 1, True, count)

    real_draw = pages._draw_aligned_number

    def omit_answer_row(c, val, row, *args, **kwargs):
        if row == 0:
            return  # broken renderer: skip the answer row only
        real_draw(c, val, row, *args, **kwargs)

    monkeypatch.setattr(pages, "_draw_aligned_number", omit_answer_row)

    reader = PdfReader(io.BytesIO(render(spec)))
    with pytest.raises(AssertionError):
        _assert_arithmetic_answers(reader.pages[1], expected_probs)


@pytest.mark.parametrize(
    ("spec_kwargs", "expected_pages"),
    [
        ({"t": ("trace",), "pages": 3, "ans": 1}, 3),
        ({"t": ("trace",), "pages": 3, "ans": 0}, 3),
        ({"t": ("missing",), "pages": 2, "ans": 1}, 4),
        ({"t": ("missing",), "pages": 2, "ans": 0}, 2),
        ({"t": ("match",), "pages": 2, "ans": 1}, 4),
        ({"t": ("match",), "pages": 2, "ans": 0}, 2),
        ({"t": ("trace", "missing", "match"), "pages": 3, "ans": 1}, 5),
    ],
)
def test_alphabet_page_counts_and_structure(
    spec_kwargs: dict, expected_pages: int
) -> None:
    """Alphabet topic page counts match plan_sheets accounting across answer modes."""
    spec = Spec(**spec_kwargs, seed=42)
    expected_sheets = plan_sheets(spec)
    assert len(expected_sheets) == expected_pages

    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == expected_pages

    # Metadata and A4 dimensions
    assert reader.metadata is not None
    assert reader.metadata.title == "CetakPintar"
    for idx, page in enumerate(reader.pages, start=1):
        box = page.mediabox
        assert pytest.approx(float(box.width), 0.1) == 595.28
        assert pytest.approx(float(box.height), 0.1) == 841.89
        text = page.extract_text()
        assert f"Halaman {idx} / {expected_pages}" in text


def test_abc_preset_rendering() -> None:
    """Preset abc includes first_letter with four content and three answer pages."""
    spec, errors = parse_spec("preset=abc&seed=1")
    assert errors == []
    sheets = plan_sheets(spec)
    assert len(sheets) == 7

    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 7

    # Verify trace sheets have no answer sheet, and missing/match have answer sheets
    p1_text = reader.pages[0].extract_text()
    assert "SURIH HURUF" in p1_text
    p2_text = reader.pages[1].extract_text()
    assert "HURUF TERTINGGAL" in p2_text
    p3_text = reader.pages[2].extract_text()
    assert "PADANKAN HURUF" in p3_text
    p4_text = reader.pages[3].extract_text()
    assert "HURUF PERTAMA" in p4_text
    p5_text = reader.pages[4].extract_text()
    assert "SKEMA JAWAPAN" in p5_text
    assert "Jawapan Huruf Tertinggal" in p5_text
    p6_text = reader.pages[5].extract_text()
    assert "SKEMA JAWAPAN" in p6_text
    assert "Jawapan Padankan Huruf" in p6_text
    assert "Jawapan Huruf Pertama" in reader.pages[6].extract_text()


@pytest.mark.parametrize("case", ["upper", "lower"])
def test_trace_rendering(case: str) -> None:
    """Letter tracing renders 4 rows on ruled lines without an answer key."""
    spec = Spec(t=("trace",), pages=2, ans=1, seed=10, abc_case=case)
    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2

    for page in reader.pages:
        text = page.extract_text()
        assert "SURIH HURUF" in text
        # Contains badges 1 to 4
        for num in ("1", "2", "3", "4"):
            assert num in text


@pytest.mark.parametrize("case", ["upper", "lower"])
@pytest.mark.parametrize("blanks", [1, 2, 3])
@pytest.mark.parametrize("lang", ["ms", "en"])
def test_missing_letters_rendering_and_answers(case: str, blanks: int, lang: str) -> None:
    """Extracted text on missing letters answer sheet must contain every blank answer."""
    seed = 777
    spec = Spec(
        t=("missing",),
        pages=1,
        ans=1,
        seed=seed,
        abc_case=case,
        missing_blanks=blanks,
        lang=lang,
    )
    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2

    expected_rows = missing_rows(Random(seed), case, blanks, cards_per_sheet(spec, "missing"))
    assert len(expected_rows) == 12

    content_text = reader.pages[0].extract_text()
    answer_text = reader.pages[1].extract_text()

    if lang == "ms":
        assert "HURUF TERTINGGAL" in content_text
        assert "SKEMA JAWAPAN" in answer_text
        assert "Jawapan Huruf Tertinggal" in answer_text
    else:
        assert "MISSING LETTERS" in content_text
        assert "ANSWER KEY" in answer_text
        assert "Missing Letters Answers" in answer_text

    # On answer sheet, check that every blank letter was rendered
    for row in expected_rows:
        for blank_idx in row.blanks:
            blank_letter = row.letters[blank_idx]
            assert blank_letter in answer_text

        # Verify that all 6 consecutive letters are present in answer text
        for letter in row.letters:
            assert letter in answer_text


@pytest.mark.parametrize("lang", ["ms", "en"])
def test_match_rendering_and_answers(lang: str) -> None:
    """Extracted text on match answer sheet must contain all matching pairs."""
    seed = 888
    spec = Spec(t=("match",), pages=1, ans=1, seed=seed, lang=lang)
    pdf_bytes = render(spec)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2

    expected_match_sets = match_sets(Random(seed), cards_per_sheet(spec, "match"), MATCH_PAIRS)
    assert len(expected_match_sets) == 3

    content_text = reader.pages[0].extract_text()
    answer_text = reader.pages[1].extract_text()

    if lang == "ms":
        assert "PADANKAN HURUF" in content_text
        assert "SKEMA JAWAPAN" in answer_text
        assert "Jawapan Padankan Huruf" in answer_text
    else:
        assert "LETTER MATCHING" in content_text
        assert "ANSWER KEY" in answer_text
        assert "Letter Matching Answers" in answer_text

    # Content sheet contains both left uppercase and right lowercase letters
    for ms in expected_match_sets:
        for c in ms.left:
            assert c in content_text
        for c in ms.right:
            assert c in content_text

    # Answer sheet renders pair labels A - a at the bottom of each card
    for ms in expected_match_sets:
        for k in range(len(ms.left)):
            left_char = ms.left[k]
            right_char = ms.right[ms.pairs[k]]
            expected_pair = f"{left_char} - {right_char}"
            assert expected_pair in answer_text


def test_match_canvas_connecting_lines() -> None:
    """Verify that draw_match draws lines connecting left dots to paired right dots.

    Robust assertion strategy explanation:
    1. On the answer sheet, draw_match draws explicit connecting lines from
       (left_dot_x, left_y) to (right_dot_x, right_y) where right_y is determined
       by match_set.pairs[left_idx].
    2. We verify the canvas.line() coordinates match the geometry of the pairs.
    3. The answer sheet additionally renders pair summary labels (e.g. 'A - a')
       at the bottom of each card, enabling clean text verification via pypdf.
    """
    spec = Spec(t=("match",), pages=1, ans=1, seed=42)
    m_sets = match_sets(Random(42), 1, MATCH_PAIRS)
    assert len(m_sets) == 1
    m_set = m_sets[0]

    canvas = MagicMock()
    draw_match(canvas, spec, m_sets, is_answer=True, page_num=1, total_pages=1)

    # Filter to connecting lines between left and right dots
    # In draw_match, left_dot_x = MARGIN_X + 85.0 and right_dot_x = MARGIN_X + CONTENT_W - 85.0
    left_dot_x = MARGIN_X + 85.0
    right_dot_x = MARGIN_X + CONTENT_W - 85.0

    connecting_lines = [
        call.args
        for call in canvas.line.call_args_list
        if pytest.approx(call.args[0], 0.1) == left_dot_x
        and pytest.approx(call.args[2], 0.1) == right_dot_x
    ]

    assert len(connecting_lines) == MATCH_PAIRS

    # Calculate item_y formula from draw_match
    # card_y for 1 card:
    top = PAGE_H - 84.0
    bottom = 44.0
    card_h = top - bottom
    card_y = top - card_h
    usable_top = card_y + card_h - 28.0
    usable_bottom = card_y + 28.0
    n_items = len(m_set.left)
    item_step = (usable_top - usable_bottom) / (n_items - 1)

    for left_idx, right_idx in enumerate(m_set.pairs):
        expected_y_left = usable_top - left_idx * item_step
        expected_y_right = usable_top - right_idx * item_step
        x1, y1, x2, y2 = connecting_lines[left_idx]
        assert pytest.approx(y1, 0.1) == expected_y_left
        assert pytest.approx(y2, 0.1) == expected_y_right




@pytest.mark.parametrize("topic", ["first_letter", "guess_word"])
@pytest.mark.parametrize("lang", ["ms", "en"])
@pytest.mark.parametrize("hint", [0, 1])
def test_picture_answers_and_hints_in_each_card(topic, lang, hint):
    spec = Spec(t=(topic,), pages=1, lang=lang, guess_hint=hint, seed=42)
    rng = Random(spec.seed)
    items = picture_items(rng, spec.themes, cards_per_sheet(spec, topic))
    hints = [scramble(rng, getattr(item, lang)) for item in items] if topic == "guess_word" else []
    reader = PdfReader(io.BytesIO(render(spec)))
    assert len(reader.pages) == len(plan_sheets(spec)) == 2
    content_runs = _page_text_positions(reader.pages[0])
    answer_runs = _page_text_positions(reader.pages[1])
    cols = 3 if topic == "first_letter" else 2
    gap = 12.0
    width = (CONTENT_W - (cols - 1) * gap) / cols
    height = (PAGE_H - 84.0 - 44.0 - 3 * gap) / 4
    for index, item in enumerate(items):
        x = MARGIN_X + index % cols * (width + gap)
        y = PAGE_H - 84.0 - (index // cols + 1) * height - index // cols * gap
        answer_letters = [
            text for text, tx, ty in answer_runs
            if x <= tx <= x + width and y + 20 <= ty <= y + 42
        ]
        assert "".join(answer_letters) == getattr(item, lang)
        content_letters = [
            text for text, tx, ty in content_runs
            if x <= tx <= x + width and y + 20 <= ty <= y + 42
        ]
        assert content_letters == []
        if topic == "guess_word":
            expected_hint = " ".join(hints[index])
            for runs in (content_runs, answer_runs):
                drawn_hints = [
                    text for text, tx, ty in runs
                    if x <= tx <= x + width and y <= ty < y + 20
                ]
                assert drawn_hints == ([expected_hint] if hint else [])


@pytest.mark.parametrize("ans", [0, 1])
def test_picture_mixed_page_counts(ans):
    spec = Spec(t=("first_letter", "guess_word"), pages=5, ans=ans, seed=42)
    reader = PdfReader(io.BytesIO(render(spec)))
    assert len(reader.pages) == len(plan_sheets(spec)) == 5 * (1 + ans)


def test_picture_payload_and_scrambled_hints_reused(monkeypatch):
    received = []
    calls = []

    def record(c, spec, problems, is_answer, page_num, total_pages):
        received.append((problems, is_answer))

    def count_scramble(rng, word):
        calls.append(word)
        return scramble(rng, word)

    monkeypatch.setattr("modules.render.pdf.draw_guess_word", record)
    monkeypatch.setattr("modules.render.pdf.scramble", count_scramble)
    render(Spec(t=("guess_word",), pages=2, seed=42))
    assert len(calls) == 16
    assert len(received) == 4
    assert [is_answer for _, is_answer in received] == [False, False, True, True]
    assert received[0][0] is received[2][0]
    assert received[1][0] is received[3][0]


@pytest.mark.parametrize("topic", ["first_letter", "guess_word"])
def test_picture_determinism_across_hash_seeds(topic):
    code = f"""
import sys
from modules.spec import Spec
from modules.render.pdf import render
sys.stdout.buffer.write(render(Spec(t=({topic!r},), pages=2, seed=42)))
"""
    outputs = [subprocess.run(
        [sys.executable, "-c", code], env=dict(os.environ, PYTHONHASHSEED=hash_seed),
        capture_output=True, check=True,
    ).stdout for hash_seed in ("0", "123456789")]
    assert outputs[0].startswith(b"%PDF")
    assert outputs[0] == outputs[1]


def test_picture_maximum_pdf_size_and_image_reuse():
    spec = Spec(t=("first_letter", "guess_word"), pages=20, ans=1, seed=42)
    pdf = render(spec)
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 40
    assert len(pdf) < 3_000_000
    images = set()
    for page in reader.pages:
        for reference in page["/Resources"]["/XObject"].values():
            if reference.get_object()["/Subtype"] == "/Image":
                images.add(reference.idnum)
    assert len(images) <= 49  # 48 vocabulary images plus the shared footer logo.
