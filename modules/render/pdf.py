"""PDF generation entrypoint for CetakPintar worksheets."""

from __future__ import annotations

import io
from random import Random

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from modules.alphabet import match_sets, missing_rows, picture_items, scramble, trace_letters
from modules.layout import MATCH_PAIRS, cards_per_sheet, plan_sheets
from modules.problems import (
    addition,
    counting,
    division,
    grid_blanks,
    multiplication,
    subtraction,
)
from modules.render.pages import (
    draw_add,
    draw_count,
    draw_count_answers,
    draw_div,
    draw_div_answers,
    draw_first_letter,
    draw_grid,
    draw_guess_word,
    draw_match,
    draw_match_answers,
    draw_missing,
    draw_missing_answers,
    draw_sifir,
    draw_sifir_answers,
    draw_sifir_ref,
    draw_sub,
    draw_trace,
)
from modules.spec import Spec

SUPPORTED_TOPICS: frozenset[str] = frozenset(
    {
        "grid", "count", "add", "sub", "sifir_ref", "sifir", "div", "trace", "missing", "match",
        "first_letter", "guess_word",
    }
)


def render(spec: Spec) -> bytes:
    """Render a worksheet Spec to PDF bytes.

    Uses A4 paper size, ReportLab invariant mode for byte-identical determinism,
    Helvetica font family, and sets PDF metadata Title and Author to 'CetakPintar'.

    Raises NotImplementedError naming any unsupported topic in the spec.
    """
    for topic in spec.t:
        if topic not in SUPPORTED_TOPICS:
            raise NotImplementedError(
                f"Topic '{topic}' is not implemented in renderer"
            )

    sheets = plan_sheets(spec)
    total_pages = len(sheets)

    # Deterministic RNG initialization
    seed = spec.seed if spec.seed is not None else 0
    rng = Random(seed)

    # Pre-generate problems for each content sheet in order
    sheet_data: dict[tuple[str, int], list] = {}
    for kind, topic, sheet_idx in sheets:
        if kind == "content":
            if topic == "grid":
                sheet_data[(topic, sheet_idx)] = grid_blanks(
                    rng, spec.grid_start, spec.grid_blanks
                )
            elif topic == "count":
                sheet_data[(topic, sheet_idx)] = counting(
                    rng, spec.count_max, spec.count_shapes, cards_per_sheet(spec, "count")
                )
            elif topic == "add":
                count = cards_per_sheet(spec, "add")
                sheet_data[(topic, sheet_idx)] = addition(
                    rng, spec.add_digits, bool(spec.add_regroup), count
                )
            elif topic == "sub":
                count = cards_per_sheet(spec, "sub")
                sheet_data[(topic, sheet_idx)] = subtraction(
                    rng, spec.sub_digits, bool(spec.sub_borrow), count
                )
            elif topic == "sifir_ref":
                sorted_tables = sorted(spec.sifir_tables)
                sheet_data[(topic, sheet_idx)] = sorted_tables[
                    sheet_idx * 6 : (sheet_idx + 1) * 6
                ]
            elif topic == "sifir":
                count = cards_per_sheet(spec, "sifir")
                sheet_data[(topic, sheet_idx)] = multiplication(
                    rng, spec.sifir_tables, count
                )
            elif topic == "div":
                sheet_data[(topic, sheet_idx)] = division(
                    rng,
                    spec.div_digits,
                    spec.div_divisors,
                    bool(spec.div_rem),
                    cards_per_sheet(spec, "div"),
                )
            elif topic == "trace":
                sheet_data[(topic, sheet_idx)] = trace_letters(
                    sheet_idx, cards_per_sheet(spec, "trace"), spec.abc_case
                )
            elif topic == "missing":
                sheet_data[(topic, sheet_idx)] = missing_rows(
                    rng,
                    spec.abc_case,
                    spec.missing_blanks,
                    cards_per_sheet(spec, "missing"),
                )
            elif topic == "match":
                sheet_data[(topic, sheet_idx)] = match_sets(
                    rng, cards_per_sheet(spec, "match"), MATCH_PAIRS
                )
            elif topic in ("first_letter", "guess_word"):
                items = picture_items(rng, spec.themes, cards_per_sheet(spec, topic))
                if topic == "guess_word":
                    sheet_data[(topic, sheet_idx)] = [
                        (item, scramble(rng, item.ms if spec.lang == "ms" else item.en))
                        for item in items
                    ]
                else:
                    sheet_data[(topic, sheet_idx)] = items

    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4, invariant=1)
    c.setTitle("CetakPintar")
    c.setAuthor("CetakPintar")

    for page_idx, (kind, topic, sheet_idx) in enumerate(sheets, start=1):
        is_answer = kind == "answer"
        data = sheet_data[(topic, sheet_idx)]

        if topic == "grid":
            draw_grid(
                c,
                spec=spec,
                blanks=data,
                is_answer=is_answer,
                page_num=page_idx,
                total_pages=total_pages,
            )
        elif topic == "count":
            if is_answer:
                draw_count_answers(c, spec, data, page_idx, total_pages)
            else:
                draw_count(c, spec, data, False, page_idx, total_pages)
        elif topic == "add":
            draw_add(
                c,
                spec=spec,
                problems=data,
                is_answer=is_answer,
                page_num=page_idx,
                total_pages=total_pages,
            )
        elif topic == "sub":
            draw_sub(
                c,
                spec=spec,
                problems=data,
                is_answer=is_answer,
                page_num=page_idx,
                total_pages=total_pages,
            )
        elif topic == "sifir_ref":
            draw_sifir_ref(
                c,
                spec=spec,
                tables=data,
                page_num=page_idx,
                total_pages=total_pages,
            )
        elif topic == "sifir":
            if is_answer:
                draw_sifir_answers(
                    c,
                    spec=spec,
                    problems=data,
                    page_num=page_idx,
                    total_pages=total_pages,
                )
            else:
                draw_sifir(
                    c,
                    spec=spec,
                    problems=data,
                    is_answer=False,
                    page_num=page_idx,
                    total_pages=total_pages,
                )

        elif topic == "div":
            if is_answer:
                draw_div_answers(c, spec, data, page_idx, total_pages)
            else:
                draw_div(c, spec, data, False, page_idx, total_pages)
        elif topic == "trace":
            draw_trace(
                c,
                spec=spec,
                letters=data,
                page_num=page_idx,
                total_pages=total_pages,
            )
        elif topic == "missing":
            if is_answer:
                draw_missing_answers(c, spec, data, page_idx, total_pages)
            else:
                draw_missing(c, spec, data, False, page_idx, total_pages)
        elif topic == "match":
            if is_answer:
                draw_match_answers(c, spec, data, page_idx, total_pages)
            else:
                draw_match(c, spec, data, False, page_idx, total_pages)
        elif topic == "first_letter":
            draw_first_letter(c, spec, data, is_answer, page_idx, total_pages)
        elif topic == "guess_word":
            draw_guess_word(c, spec, data, is_answer, page_idx, total_pages)

        c.showPage()

    c.save()
    return buf.getvalue()
