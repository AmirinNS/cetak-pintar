"""Checks for original tracing glyph geometry and actual PDF drawing."""

from __future__ import annotations

import io
import math
from string import ascii_letters, ascii_lowercase

import pytest
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from modules.render.letters import GLYPHS, X_HEIGHT, Arc, Line, draw_letter, letter_width


def _arc_point(arc: Arc, angle: float) -> tuple[float, float]:
    x1, y1, x2, y2 = arc.bounds
    radians = math.radians(angle)
    return ((x1 + x2) / 2 + (x2 - x1) / 2 * math.cos(radians),
            (y1 + y2) / 2 + (y2 - y1) / 2 * math.sin(radians))


def test_all_letters_exist() -> None:
    assert set(GLYPHS) == set(ascii_letters)
    assert X_HEIGHT == 0.5


@pytest.mark.parametrize("letter", ascii_letters)
def test_glyph_bounds_and_continuous_strokes(letter: str) -> None:
    glyph = GLYPHS[letter]
    assert glyph.advance > 0
    assert glyph.strokes
    for stroke in glyph.strokes:
        assert stroke
        previous_end = None
        for segment in stroke:
            if isinstance(segment, Line):
                points = (segment.start, segment.end)
                start, end = points
            else:
                assert isinstance(segment, Arc)
                x1, y1, x2, y2 = segment.bounds
                assert x1 < x2 and y1 < y2
                assert 0 < abs(segment.extent) <= 360
                points = ((x1, y1), (x2, y2))
                start = _arc_point(segment, segment.start_angle)
                end = _arc_point(segment, segment.start_angle + segment.extent)
            for x, y in points:
                assert 0 <= x <= glyph.advance
                assert -0.3 <= y <= 1
            if previous_end is not None:
                assert start == pytest.approx(previous_end, abs=1e-9)
            previous_end = end


@pytest.mark.parametrize("letter", sorted(set(ascii_lowercase) - set("bdfhijklt")))
def test_lowercase_body_stays_below_x_height(letter: str) -> None:
    for stroke in GLYPHS[letter].strokes:
        for segment in stroke:
            top = max(segment.start[1], segment.end[1]) if isinstance(segment, Line) else (
                segment.bounds[3]
            )
            assert top <= X_HEIGHT


@pytest.mark.parametrize("letter", ascii_letters)
@pytest.mark.parametrize("dotted", [False, True])
def test_draws_every_glyph_and_restores_canvas(letter: str, dotted: bool, monkeypatch) -> None:
    buffer = io.BytesIO()
    canvas = Canvas(buffer, invariant=1)
    canvas.setLineWidth(7)
    canvas.setDash([3, 5])
    canvas.setLineCap(2)
    canvas.translate(11, 13)
    original_circle = canvas.circle
    dots = []

    def record_circle(x, y, radius, stroke, fill):
        dots.append((x, y, radius, stroke, fill))
        original_circle(x, y, radius, stroke=stroke, fill=fill)

    monkeypatch.setattr(canvas, "circle", record_circle)
    state = (canvas._lineWidth, canvas._lineCap, canvas._lineDash,
             canvas._strokeColorObj, canvas._fillColorObj, canvas._currentMatrix)
    draw_letter(canvas, letter, 100, 200, 40, dotted)
    assert state == (canvas._lineWidth, canvas._lineCap, canvas._lineDash,
                     canvas._strokeColorObj, canvas._fillColorObj, canvas._currentMatrix)
    assert len(dots) == (len(GLYPHS[letter].strokes) if dotted else 0)
    if dotted:
        for dot, glyph_stroke in zip(dots, GLYPHS[letter].strokes, strict=True):
            segment = glyph_stroke[0]
            start = segment.start if isinstance(segment, Line) else (
                _arc_point(segment, segment.start_angle)
            )
            assert dot[:2] == pytest.approx(start)
            assert dot[2:] == (0.028, 0, 1)
    canvas.save()
    content = PdfReader(buffer).pages[0].get_contents()
    operators = [operator for arguments, operator in content.operations]
    assert operators.count(b"S") == len(GLYPHS[letter].strokes)
    caps = [arguments for arguments, operator in content.operations if operator == b"J"]
    assert caps[-1] == [1]
    dashes = [arguments for arguments, operator in content.operations if operator == b"d"]
    assert dashes[-1][0] == pytest.approx([0.012, 0.06] if dotted else [])
    widths = [arguments for arguments, operator in content.operations if operator == b"w"]
    assert widths[-1] == pytest.approx([0.028 if dotted else 0.035])
    colors = [arguments for arguments, operator in content.operations if operator == b"RG"]
    assert colors[-1] == pytest.approx([107 / 255 if dotted else 0.2] * 3, abs=1e-6)
    if any(isinstance(segment, Arc) for stroke in GLYPHS[letter].strokes for segment in stroke):
        assert b"c" in operators


@pytest.mark.parametrize("letter", ascii_letters)
def test_letter_width_scales_with_cap_height(letter: str) -> None:
    assert letter_width(letter, 40) == pytest.approx(GLYPHS[letter].advance * 40)
    assert letter_width(letter, 80) == pytest.approx(letter_width(letter, 40) * 2)


@pytest.mark.parametrize("letter", ["", "AA", "1", "é", "unknown"])
def test_unknown_letter_raises_value_error(letter: str) -> None:
    canvas = Canvas(io.BytesIO())
    with pytest.raises(ValueError, match="Unknown letter"):
        draw_letter(canvas, letter, 10, 20, 40, True)
    with pytest.raises(ValueError, match="Unknown letter"):
        letter_width(letter, 40)
