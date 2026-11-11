"""Black outline vector shapes drawn fresh with ReportLab paths.

Provides pure vector drawing functions for child-friendly counting shapes:
star, circle, apple, fish, flower. No bitmaps and no icon fonts.
"""

from __future__ import annotations

import math
from typing import Callable

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

LINE_WIDTH: float = 1.0


def draw_circle(c: Canvas, cx: float, cy: float, size: float) -> None:
    """Draw a clean, circular outline shape centered at (cx, cy)."""
    r = size * 0.44
    c.saveState()
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.white)
    c.setLineWidth(LINE_WIDTH)
    c.circle(cx, cy, r, stroke=1, fill=1)
    c.restoreState()


def draw_star(c: Canvas, cx: float, cy: float, size: float) -> None:
    """Draw a classic 5-pointed star outline centered at (cx, cy)."""
    r_outer = size * 0.46
    r_inner = r_outer * 0.42

    c.saveState()
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.white)
    c.setLineWidth(LINE_WIDTH)

    p = c.beginPath()
    for i in range(10):
        angle = math.pi / 2 + i * (math.pi / 5)
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    c.restoreState()


def draw_apple(c: Canvas, cx: float, cy: float, size: float) -> None:
    """Draw a cartoon apple with stem and leaf centered at (cx, cy)."""
    r = size * 0.40

    c.saveState()
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.white)
    c.setLineWidth(LINE_WIDTH)

    # Apple body with lobes and bottom dimple
    p = c.beginPath()
    p.moveTo(cx, cy + r * 0.35)
    # Right lobe
    p.curveTo(
        cx + r * 0.15, cy + r * 0.65,
        cx + r * 0.35, cy + r * 0.85,
        cx + r * 0.45, cy + r * 0.85,
    )
    p.curveTo(
        cx + r * 0.75, cy + r * 0.85,
        cx + r * 0.95, cy + r * 0.45,
        cx + r * 0.95, cy - r * 0.05,
    )
    # Bottom right to bottom notch
    p.curveTo(
        cx + r * 0.95, cy - r * 0.55,
        cx + r * 0.65, cy - r * 0.85,
        cx + r * 0.15, cy - r * 0.85,
    )
    p.curveTo(
        cx + r * 0.05, cy - r * 0.78,
        cx - r * 0.05, cy - r * 0.78,
        cx - r * 0.15, cy - r * 0.85,
    )
    # Bottom left to left side
    p.curveTo(
        cx - r * 0.65, cy - r * 0.85,
        cx - r * 0.95, cy - r * 0.55,
        cx - r * 0.95, cy - r * 0.05,
    )
    # Left lobe to top notch
    p.curveTo(
        cx - r * 0.95, cy + r * 0.45,
        cx - r * 0.75, cy + r * 0.85,
        cx - r * 0.45, cy + r * 0.85,
    )
    p.curveTo(
        cx - r * 0.35, cy + r * 0.85,
        cx - r * 0.15, cy + r * 0.65,
        cx, cy + r * 0.35,
    )
    p.close()
    c.drawPath(p, stroke=1, fill=1)

    # Leaf on the stem
    leaf = c.beginPath()
    leaf.moveTo(cx + r * 0.06, cy + r * 0.62)
    leaf.curveTo(
        cx + r * 0.35, cy + r * 0.82,
        cx + r * 0.55, cy + r * 0.75,
        cx + r * 0.50, cy + r * 0.55,
    )
    leaf.curveTo(
        cx + r * 0.35, cy + r * 0.52,
        cx + r * 0.20, cy + r * 0.55,
        cx + r * 0.06, cy + r * 0.62,
    )
    c.drawPath(leaf, stroke=1, fill=1)

    # Stem
    stem = c.beginPath()
    stem.moveTo(cx, cy + r * 0.35)
    stem.curveTo(
        cx + r * 0.02, cy + r * 0.60,
        cx + r * 0.06, cy + r * 0.80,
        cx + r * 0.15, cy + r * 0.95,
    )
    c.drawPath(stem, stroke=1, fill=0)

    c.restoreState()


def draw_fish(c: Canvas, cx: float, cy: float, size: float) -> None:
    """Draw a cartoon fish outline with tail fin and eye centered at (cx, cy)."""
    r = size * 0.42

    c.saveState()
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.white)
    c.setLineWidth(LINE_WIDTH)

    # Fish body and tail (facing left)
    p = c.beginPath()
    p.moveTo(cx - r * 0.85, cy)
    p.curveTo(
        cx - r * 0.50, cy + r * 0.65,
        cx + r * 0.15, cy + r * 0.65,
        cx + r * 0.55, cy + r * 0.15,
    )
    p.lineTo(cx + r * 0.95, cy + r * 0.55)
    p.lineTo(cx + r * 0.70, cy)
    p.lineTo(cx + r * 0.95, cy - r * 0.55)
    p.lineTo(cx + r * 0.55, cy - r * 0.15)
    p.curveTo(
        cx + r * 0.15, cy - r * 0.65,
        cx - r * 0.50, cy - r * 0.65,
        cx - r * 0.85, cy,
    )
    p.close()
    c.drawPath(p, stroke=1, fill=1)

    # Eye outline
    c.circle(cx - r * 0.50, cy + r * 0.15, r * 0.12, stroke=1, fill=1)
    # Pupil
    c.setFillColor(colors.black)
    c.circle(cx - r * 0.53, cy + r * 0.15, r * 0.05, stroke=1, fill=1)

    # Gill line
    c.setFillColor(colors.white)
    gill = c.beginPath()
    gill.moveTo(cx - r * 0.20, cy + r * 0.35)
    gill.curveTo(
        cx - r * 0.08, cy + r * 0.15,
        cx - r * 0.08, cy - r * 0.15,
        cx - r * 0.20, cy - r * 0.35,
    )
    c.drawPath(gill, stroke=1, fill=0)

    c.restoreState()


def draw_flower(c: Canvas, cx: float, cy: float, size: float) -> None:
    """Draw a daisy-like flower outline with 5 petals centered at (cx, cy)."""
    r = size * 0.44
    r_center = r * 0.38
    r_petal = r * 0.36
    d = r * 0.62

    c.saveState()
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.white)
    c.setLineWidth(LINE_WIDTH)

    # 5 round petals around center
    for k in range(5):
        angle = k * (2 * math.pi / 5) + math.pi / 10
        px = cx + d * math.cos(angle)
        py = cy + d * math.sin(angle)
        c.circle(px, py, r_petal, stroke=1, fill=1)

    # Center disk on top
    c.circle(cx, cy, r_center, stroke=1, fill=1)
    c.restoreState()


SHAPE_DISPATCH: dict[str, Callable[[Canvas, float, float, float], None]] = {
    "circle": draw_circle,
    "star": draw_star,
    "apple": draw_apple,
    "fish": draw_fish,
    "flower": draw_flower,
}


def draw_shape(c: Canvas, shape: str, cx: float, cy: float, size: float) -> None:
    """Dispatch drawing of a named shape centered at (cx, cy)."""
    fn = SHAPE_DISPATCH.get(shape)
    if fn is None:
        raise ValueError(f"Unknown shape: '{shape}'")
    fn(c, cx, cy, size)
