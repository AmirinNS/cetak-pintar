"""Tests for vector shapes and counting box geometry."""

from __future__ import annotations

import io
import math
from random import Random

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from modules.layout import cards_per_sheet
from modules.problems import counting
from modules.render import pages
from modules.render.pdf import render
from modules.render.primitives import CONTENT_W, MARGIN_X, PAGE_H
from modules.render.shapes import (
    SHAPE_DISPATCH,
    draw_apple,
    draw_circle,
    draw_fish,
    draw_flower,
    draw_shape,
    draw_star,
)
from modules.spec import Spec


def test_every_shape_dispatch_and_execution() -> None:
    """Every shape executes correctly on a canvas and unknown shapes raise ValueError."""
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    for name in ("circle", "star", "apple", "fish", "flower"):
        draw_shape(c, name, 100.0, 100.0, 30.0)
    c.showPage()
    c.save()
    pdf_bytes = buf.getvalue()
    assert pdf_bytes.startswith(b"%PDF-")

    with pytest.raises(ValueError, match="Unknown shape"):
        draw_shape(c, "unknown_shape", 50.0, 50.0, 20.0)


def test_individual_shape_functions() -> None:
    """Individual shape functions can be called directly."""
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4)
    draw_circle(c, 50.0, 50.0, 25.0)
    draw_star(c, 100.0, 50.0, 25.0)
    draw_apple(c, 150.0, 50.0, 25.0)
    draw_fish(c, 200.0, 50.0, 25.0)
    draw_flower(c, 250.0, 50.0, 25.0)
    c.showPage()
    c.save()
    assert buf.getvalue().startswith(b"%PDF-")


@pytest.mark.parametrize("max_n", [5, 10, 20])
def test_shapes_inside_box_and_non_overlapping(max_n: int) -> None:
    """Verify that every shape center and bounds stay strictly inside the card and never overlap."""
    rng = Random(2026)
    problems = counting(rng, max_n, tuple(SHAPE_DISPATCH.keys()), 50)

    # Standard card geometry for 3x4 grid on A4
    card_w = 173.76
    card_h = 171.72
    card_x = 28.0
    card_y = 50.0

    ans_box_h = 28.0
    ans_y = card_y + 10.0

    draw_margin_x = 10.0
    draw_x = card_x + draw_margin_x
    draw_w = card_w - 2 * draw_margin_x
    draw_y = ans_y + ans_box_h + 8.0
    draw_h = (card_y + card_h - 18.0) - draw_y

    for p in problems:
        cols = p.grid_cols
        rows = p.grid_rows
        cell_w = draw_w / cols
        cell_h = draw_h / rows
        shape_size = min(cell_w, cell_h) * 0.82
        radius = shape_size / 2.0

        centers: list[tuple[float, float]] = []
        for col, row in p.positions:
            cx = draw_x + (col + 0.5) * cell_w
            cy = draw_y + (rows - 1 - row + 0.5) * cell_h

            # Inside the draw area
            assert cx - radius >= draw_x - 1e-6
            assert cx + radius <= draw_x + draw_w + 1e-6
            assert cy - radius >= draw_y - 1e-6
            assert cy + radius <= draw_y + draw_h + 1e-6

            # Inside the card box
            assert cx - radius >= card_x
            assert cx + radius <= card_x + card_w
            assert cy - radius >= card_y
            assert cy + radius <= card_y + card_h

            centers.append((cx, cy))

        # Non-overlapping: distance between any two shape centers
        # must be >= min(cell_w, cell_h) > shape_size
        for i in range(len(centers)):
            for j in range(i + 1, len(centers)):
                dist = math.hypot(centers[i][0] - centers[j][0], centers[i][1] - centers[j][1])
                assert dist >= shape_size


def _observe_draw_shape(monkeypatch: pytest.MonkeyPatch) -> list:
    """Spy on the counting renderer's real draw_shape, recording every call.

    The real shape is still drawn so the PDF stays complete; the recorded
    (shape, cx, cy, size) tuples let a test observe the renderer instead of
    reconstructing its geometry.
    """
    real_draw = pages.draw_shape
    calls: list = []

    def recorder(c, shape, cx, cy, size):
        calls.append((shape, cx, cy, size))
        real_draw(c, shape, cx, cy, size)

    monkeypatch.setattr(pages, "draw_shape", recorder)
    return calls


def _counting_card_boxes(count: int) -> list:
    """Recompute each counting card box (x, y, w, h) on the 3x4 sheet."""
    cols = 3
    rows = 4
    gap = 9.0
    top = PAGE_H - 84.0
    card_w = (CONTENT_W - (cols - 1) * gap) / cols
    card_h = (top - 44.0 - (rows - 1) * gap) / rows
    boxes = []
    for index in range(count):
        row, col = divmod(index, cols)
        x = MARGIN_X + col * (card_w + gap)
        y = top - (row + 1) * card_h - row * gap
        boxes.append((x, y, card_w, card_h))
    return boxes


def _assert_drawn_shapes_match(calls, problems) -> None:
    """Assert draw_shape ran once per position, with the right shape and center.

    Recomputes each expected center from the generated problem and requires a
    single matching recorded call, so the call count, shape names, and positions
    all track the generated problems.
    """
    boxes = _counting_card_boxes(len(problems))
    expected = []
    for (x, y, w, h), problem in zip(boxes, problems, strict=True):
        draw_x = x + 10.0
        draw_w = w - 20.0
        draw_y = y + 10.0 + 28.0 + 8.0
        draw_h = (y + h - 18.0) - draw_y
        cell_w = draw_w / problem.grid_cols
        cell_h = draw_h / problem.grid_rows
        for col, row in problem.positions:
            cx = draw_x + (col + 0.5) * cell_w
            cy = draw_y + (problem.grid_rows - 1 - row + 0.5) * cell_h
            expected.append((problem.shape, cx, cy))

    assert len(calls) == len(expected), (len(calls), len(expected))
    for shape, cx, cy in expected:
        hits = [
            (name, ax, ay)
            for name, ax, ay, _size in calls
            if name == shape and abs(ax - cx) < 0.01 and abs(ay - cy) < 0.01
        ]
        assert len(hits) == 1, (shape, cx, cy, hits)


@pytest.mark.parametrize("lang", ["ms", "en"])
@pytest.mark.parametrize("count_max", [5, 10, 20])
def test_counting_renderer_draws_expected_shapes(
    count_max: int, lang: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The counting renderer draws exactly the generated shapes at their centers.

    Observes the real draw_shape calls rather than reconstructing positions, so a
    renderer that skips drawing shapes fails here (review M7).
    """
    spec = Spec(t=("count",), pages=1, ans=0, seed=54321, count_max=count_max, lang=lang)
    problems = counting(
        Random(54321), count_max, spec.count_shapes, cards_per_sheet(spec, "count")
    )

    calls = _observe_draw_shape(monkeypatch)
    assert render(spec).startswith(b"%PDF-")
    _assert_drawn_shapes_match(calls, problems)


@pytest.mark.parametrize("shape", ["star", "circle", "apple", "fish", "flower"])
def test_single_shape_renderer_draws_that_shape(
    shape: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each individual shape is actually drawn by the counting renderer (review M7)."""
    spec = Spec(t=("count",), pages=1, ans=0, seed=99, count_shapes=(shape,))
    problems = counting(
        Random(99), spec.count_max, (shape,), cards_per_sheet(spec, "count")
    )

    calls = _observe_draw_shape(monkeypatch)
    assert render(spec).startswith(b"%PDF-")
    assert calls, "counting renderer drew no shapes"
    assert all(name == shape for name, *_ in calls)
    _assert_drawn_shapes_match(calls, problems)


def test_shape_check_detects_no_op_draw_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    """A no-op draw_shape must fail the shape check (review M7)."""
    spec = Spec(t=("count",), pages=1, ans=0, seed=54321, count_max=10, lang="ms")
    problems = counting(
        Random(54321), 10, spec.count_shapes, cards_per_sheet(spec, "count")
    )

    # Broken renderer: draw_shape draws nothing, so no calls are observed.
    monkeypatch.setattr(pages, "draw_shape", lambda *args: None)
    render(spec)

    with pytest.raises(AssertionError):
        _assert_drawn_shapes_match([], problems)
