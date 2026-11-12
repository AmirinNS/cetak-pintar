"""Process raw line-art PNGs into clean 1-bit 512x512 worksheet assets.

For every <theme>/<id>.png found under each input root, the image is converted to
greyscale, thresholded to pure black and white, trimmed of its white border, padded
to a square with an even white margin, resized to 512x512 with a high-quality filter,
thresholded once more, and saved as a 1-bit PNG under the output root at
<output>/<theme>/<id>.png.

Dev-only asset tool. Pillow is a dev dependency (see pyproject.toml).

Usage:
    uv run python scripts/process_line_art.py RAW_ROOT [RAW_ROOT ...] OUTPUT_ROOT
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Sequence
from pathlib import Path

from PIL import Image, ImageOps

# Greyscale level at or above which a pixel turns white; below it turns black. 160
# sits between the anti-aliased grey edges and the solid black outlines of the raw
# art, so thick outlines stay black and the background stays white.
THRESHOLD = 160

# Fraction of the final square kept as an even white margin on the long edge.
MARGIN_RATIO = 0.06

# Output edge length in pixels.
SIZE = 512


def _to_black_and_white(image: Image.Image) -> Image.Image:
    """Threshold a greyscale image to pure black (0) and white (255)."""
    return image.point(lambda level: 255 if level >= THRESHOLD else 0, mode="L")


def _trim_white_border(image: Image.Image) -> Image.Image:
    """Crop the surrounding white, keeping the bounding box of the black pixels."""
    bbox = ImageOps.invert(image).getbbox()
    return image.crop(bbox) if bbox else image


def _pad_to_square(image: Image.Image) -> Image.Image:
    """Center the image on a white square with an even margin on its long edge."""
    width, height = image.size
    side = int(round(max(width, height) / (1 - 2 * MARGIN_RATIO)))
    canvas = Image.new("L", (side, side), 255)
    canvas.paste(image, ((side - width) // 2, (side - height) // 2))
    return canvas


def process_image(src: Path, dst: Path) -> int:
    """Process one raw PNG into a 1-bit 512x512 asset; return the output byte size."""
    with Image.open(src) as opened:
        grey = opened.convert("L")
    binary = _to_black_and_white(grey)
    trimmed = _trim_white_border(binary)
    squared = _pad_to_square(trimmed)
    resized = squared.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    final = _to_black_and_white(resized).convert("1", dither=Image.Dither.NONE)
    dst.parent.mkdir(parents=True, exist_ok=True)
    final.save(dst, format="PNG", optimize=True)
    return dst.stat().st_size


def iter_raw_images(input_roots: Sequence[str]) -> Iterator[tuple[str, str, Path]]:
    """Yield (theme, item_id, src_path) for every <theme>/<id>.png under the roots."""
    for root in input_roots:
        root_path = Path(root)
        for png in sorted(root_path.glob("*/*.png")):
            yield png.parent.name, png.stem, png


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, process every raw image, and print a per-file size summary."""
    parser = argparse.ArgumentParser(description="Process raw line art into 1-bit PNGs.")
    parser.add_argument("inputs", nargs="+", help="one or more raw art root directories")
    parser.add_argument(
        "output", help="output root; images land in <output>/<theme>/<id>.png"
    )
    args = parser.parse_args(argv)

    output_root = Path(args.output)
    total = 0
    count = 0
    for theme, item_id, src in iter_raw_images(args.inputs):
        dst = output_root / theme / f"{item_id}.png"
        size = process_image(src, dst)
        total += size
        count += 1
        print(f"{dst}  {SIZE}x{SIZE}  1-bit  {size} B")

    print(f"processed {count} image(s), {total} B total into {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
