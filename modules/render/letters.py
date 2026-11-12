"""Original ball-and-stick tracing centerlines, independent of font outlines.

Coordinates use a baseline of 0, cap height of 1, x-height of 0.5, and
descenders down to -0.3. Each stroke is one continuous pen movement.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from math import cos, radians, sin

from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

X_HEIGHT = 0.5
Point = tuple[float, float]


@dataclass(frozen=True)
class Line:
    start: Point
    end: Point


@dataclass(frozen=True)
class Arc:
    bounds: tuple[float, float, float, float]
    start_angle: float
    extent: float


@dataclass(frozen=True)
class Glyph:
    advance: float
    strokes: tuple[tuple[Line | Arc, ...], ...]


def _lines(*points: Point) -> tuple[Line, ...]:
    return tuple(Line(start, end) for start, end in pairwise(points))


# Drawn for this project. Arcs specify an ellipse's bounds and angles in degrees,
# counterclockwise for positive extents. Separate tuples mark pen lifts.
GLYPHS: dict[str, Glyph] = {
    "A": Glyph(0.8, (
        _lines((0.08, 0), (0.4, 1), (0.72, 0)),
        _lines((0.2, 0.38), (0.6, 0.38)),
    )),
    "B": Glyph(0.8, (
        _lines((0.08, 1), (0.08, 0)),
        (Line((0.08, 1), (0.38, 1)), Arc((0.08, 0.5, 0.68, 1), 90, -180),
         Line((0.38, 0.5), (0.08, 0.5))),
        (Line((0.08, 0.5), (0.4, 0.5)), Arc((0.08, 0, 0.72, 0.5), 90, -180),
         Line((0.4, 0), (0.08, 0))),
    )),
    "C": Glyph(0.8, ((Arc((0.08, 0, 0.72, 1), 45, 270),),)),
    "D": Glyph(0.8, (
        _lines((0.08, 1), (0.08, 0)),
        (Line((0.08, 1), (0.4, 1)), Arc((0.08, 0, 0.72, 1), 90, -180),
         Line((0.4, 0), (0.08, 0))),
    )),
    "E": Glyph(0.72, (
        _lines((0.64, 1), (0.08, 1), (0.08, 0), (0.64, 0)),
        _lines((0.08, 0.5), (0.54, 0.5)),
    )),
    "F": Glyph(0.72, (
        _lines((0.08, 0), (0.08, 1), (0.64, 1)),
        _lines((0.08, 0.5), (0.54, 0.5)),
    )),
    "G": Glyph(0.8, ((
        Arc((0.08, 0, 0.72, 1), 45, 315), Line((0.72, 0.5), (0.43, 0.5)),
    ),)),
    "H": Glyph(0.8, (
        _lines((0.08, 1), (0.08, 0)), _lines((0.72, 1), (0.72, 0)),
        _lines((0.08, 0.5), (0.72, 0.5)),
    )),
    "I": Glyph(0.48, (
        _lines((0.24, 1), (0.24, 0)), _lines((0.06, 1), (0.42, 1)),
        _lines((0.06, 0), (0.42, 0)),
    )),
    "J": Glyph(0.72, (
        (Line((0.56, 1), (0.56, 0.22)), Arc((0.08, 0, 0.56, 0.44), 0, -180)),
        _lines((0.22, 1), (0.66, 1)),
    )),
    "K": Glyph(0.8, (
        _lines((0.08, 1), (0.08, 0)),
        _lines((0.7, 1), (0.08, 0.42)), _lines((0.26, 0.59), (0.72, 0)),
    )),
    "L": Glyph(0.72, (_lines((0.08, 1), (0.08, 0), (0.64, 0)),)),
    "M": Glyph(0.94, (
        _lines((0.08, 0), (0.08, 1), (0.47, 0.4), (0.86, 1), (0.86, 0)),
    )),
    "N": Glyph(0.8, (_lines((0.08, 0), (0.08, 1), (0.72, 0), (0.72, 1)),)),
    "O": Glyph(0.8, ((Arc((0.08, 0, 0.72, 1), 90, 360),),)),
    "P": Glyph(0.8, (
        _lines((0.08, 1), (0.08, 0)),
        (Line((0.08, 1), (0.4, 1)), Arc((0.08, 0.5, 0.72, 1), 90, -180),
         Line((0.4, 0.5), (0.08, 0.5))),
    )),
    "Q": Glyph(0.84, (
        (Arc((0.08, 0, 0.72, 1), 90, 360),), _lines((0.46, 0.25), (0.78, 0)),
    )),
    "R": Glyph(0.8, (
        _lines((0.08, 1), (0.08, 0)),
        (Line((0.08, 1), (0.4, 1)), Arc((0.08, 0.5, 0.72, 1), 90, -180),
         Line((0.4, 0.5), (0.08, 0.5))),
        _lines((0.37, 0.5), (0.72, 0)),
    )),
    "S": Glyph(0.8, ((
        Arc((0.08, 0.5, 0.72, 1), 30, 240), Arc((0.08, 0, 0.72, 0.5), 90, -240),
    ),)),
    "T": Glyph(0.8, (
        _lines((0.06, 1), (0.74, 1)), _lines((0.4, 1), (0.4, 0)),
    )),
    "U": Glyph(0.8, ((
        Line((0.08, 1), (0.08, 0.3)), Arc((0.08, 0, 0.72, 0.6), 180, 180),
        Line((0.72, 0.3), (0.72, 1)),
    ),)),
    "V": Glyph(0.8, (_lines((0.08, 1), (0.4, 0), (0.72, 1)),)),
    "W": Glyph(1.04, (
        _lines((0.08, 1), (0.28, 0), (0.52, 0.6), (0.76, 0), (0.96, 1)),
    )),
    "X": Glyph(0.8, (
        _lines((0.08, 1), (0.72, 0)), _lines((0.72, 1), (0.08, 0)),
    )),
    "Y": Glyph(0.8, (
        _lines((0.08, 1), (0.4, 0.5), (0.72, 1)), _lines((0.4, 0.5), (0.4, 0)),
    )),
    "Z": Glyph(0.8, (_lines((0.08, 1), (0.72, 1), (0.08, 0), (0.72, 0)),)),
    "a": Glyph(0.64, (
        (Arc((0.08, 0, 0.56, X_HEIGHT), 0, 360),),
        _lines((0.56, X_HEIGHT), (0.56, 0)),
    )),
    "b": Glyph(0.64, (
        _lines((0.08, 1), (0.08, 0)), (Arc((0.08, 0, 0.56, X_HEIGHT), 180, -360),),
    )),
    "c": Glyph(0.64, ((Arc((0.08, 0, 0.56, X_HEIGHT), 45, 270),),)),
    "d": Glyph(0.64, (
        (Arc((0.08, 0, 0.56, X_HEIGHT), 0, 360),), _lines((0.56, 1), (0.56, 0)),
    )),
    "e": Glyph(0.64, ((
        Line((0.08, 0.25), (0.56, 0.25)), Arc((0.08, 0, 0.56, X_HEIGHT), 0, 300),
    ),)),
    "f": Glyph(0.58, (
        (Arc((0.2, 0.8, 0.52, 1), 0, 180), Line((0.2, 0.9), (0.2, 0))),
        _lines((0.06, X_HEIGHT), (0.44, X_HEIGHT)),
    )),
    "g": Glyph(0.64, (
        (Arc((0.08, 0, 0.56, X_HEIGHT), 0, 360),),
        (Line((0.56, X_HEIGHT), (0.56, -0.15)), Arc((0.08, -0.3, 0.56, 0), 0, -180)),
    )),
    "h": Glyph(0.64, (
        _lines((0.08, 1), (0.08, 0)),
        (Arc((0.08, 0.1, 0.56, X_HEIGHT), 180, -180), Line((0.56, 0.3), (0.56, 0))),
    )),
    "i": Glyph(0.36, (
        _lines((0.18, X_HEIGHT), (0.18, 0)), _lines((0.18, 0.72), (0.18, 0.72)),
    )),
    "j": Glyph(0.42, (
        (Line((0.3, X_HEIGHT), (0.3, -0.15)), Arc((0.06, -0.3, 0.3, 0), 0, -180)),
        _lines((0.3, 0.72), (0.3, 0.72)),
    )),
    "k": Glyph(0.64, (
        _lines((0.08, 1), (0.08, 0)),
        _lines((0.54, X_HEIGHT), (0.08, 0.2)), _lines((0.28, 0.33), (0.56, 0)),
    )),
    "l": Glyph(0.36, (_lines((0.18, 1), (0.18, 0)),)),
    "m": Glyph(0.88, (
        _lines((0.08, X_HEIGHT), (0.08, 0)),
        (Arc((0.08, 0.1, 0.44, X_HEIGHT), 180, -180), Line((0.44, 0.3), (0.44, 0))),
        (Arc((0.44, 0.1, 0.8, X_HEIGHT), 180, -180), Line((0.8, 0.3), (0.8, 0))),
    )),
    "n": Glyph(0.64, (
        _lines((0.08, X_HEIGHT), (0.08, 0)),
        (Arc((0.08, 0.1, 0.56, X_HEIGHT), 180, -180), Line((0.56, 0.3), (0.56, 0))),
    )),
    "o": Glyph(0.64, ((Arc((0.08, 0, 0.56, X_HEIGHT), 90, 360),),)),
    "p": Glyph(0.64, (
        _lines((0.08, X_HEIGHT), (0.08, -0.3)),
        (Arc((0.08, 0, 0.56, X_HEIGHT), 180, -360),),
    )),
    "q": Glyph(0.64, (
        (Arc((0.08, 0, 0.56, X_HEIGHT), 0, 360),),
        _lines((0.56, X_HEIGHT), (0.56, -0.3)),
    )),
    "r": Glyph(0.56, (
        _lines((0.08, X_HEIGHT), (0.08, 0)),
        (Arc((0.08, 0.1, 0.5, X_HEIGHT), 180, -135),),
    )),
    "s": Glyph(0.64, ((
        Arc((0.08, 0.25, 0.56, X_HEIGHT), 30, 240),
        Arc((0.08, 0, 0.56, 0.25), 90, -240),
    ),)),
    "t": Glyph(0.58, (
        (Line((0.26, 0.85), (0.26, 0.14)), Arc((0.26, 0, 0.54, 0.28), 180, 180)),
        _lines((0.08, X_HEIGHT), (0.48, X_HEIGHT)),
    )),
    "u": Glyph(0.64, (
        (Line((0.08, X_HEIGHT), (0.08, 0.18)), Arc((0.08, 0, 0.56, 0.36), 180, 180)),
        _lines((0.56, X_HEIGHT), (0.56, 0)),
    )),
    "v": Glyph(0.64, (_lines((0.08, X_HEIGHT), (0.32, 0), (0.56, X_HEIGHT)),)),
    "w": Glyph(0.88, (
        _lines((0.08, X_HEIGHT), (0.26, 0), (0.44, 0.35), (0.62, 0), (0.8, X_HEIGHT)),
    )),
    "x": Glyph(0.64, (
        _lines((0.08, X_HEIGHT), (0.56, 0)), _lines((0.56, X_HEIGHT), (0.08, 0)),
    )),
    "y": Glyph(0.64, (
        _lines((0.08, X_HEIGHT), (0.32, 0)), _lines((0.56, X_HEIGHT), (0.176, -0.3)),
    )),
    "z": Glyph(0.64, (
        _lines((0.08, X_HEIGHT), (0.56, X_HEIGHT), (0.08, 0), (0.56, 0)),
    )),
}


def _glyph(letter: str) -> Glyph:
    glyph = GLYPHS.get(letter)
    if glyph is None:
        raise ValueError(f"Unknown letter: '{letter}'")
    return glyph


def letter_width(letter: str, height: float) -> float:
    """Return the glyph's advance in points, including side bearings."""
    return _glyph(letter).advance * height


def _start(segment: Line | Arc) -> Point:
    if isinstance(segment, Line):
        return segment.start
    x1, y1, x2, y2 = segment.bounds
    angle = radians(segment.start_angle)
    return (x1 + x2) / 2 + (x2 - x1) / 2 * cos(angle), (
        (y1 + y2) / 2 + (y2 - y1) / 2 * sin(angle)
    )


def draw_letter(
    c: Canvas, letter: str, x: float, y: float, height: float, dotted: bool
) -> None:
    """Draw at baseline (x, y), with height measured to the cap line in points."""
    glyph = _glyph(letter)
    c.saveState()
    try:
        c.translate(x, y)
        c.scale(height, height)
        color = HexColor("#6b6b6b" if dotted else "#333333")
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(0.028 if dotted else 0.035)
        c.setLineCap(1)
        c.setLineJoin(1)
        c.setDash([0.012, 0.06] if dotted else [])
        for stroke in glyph.strokes:
            start_x, start_y = _start(stroke[0])
            path = c.beginPath()
            path.moveTo(start_x, start_y)
            for segment in stroke:
                if isinstance(segment, Line):
                    path.lineTo(*segment.end)
                else:
                    path.arcTo(*segment.bounds, segment.start_angle, segment.extent)
            c.drawPath(path, stroke=1, fill=0)
            if dotted:
                c.circle(start_x, start_y, 0.028, stroke=0, fill=1)
    finally:
        c.restoreState()
