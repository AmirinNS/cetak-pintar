"""Command-line interface for generating CetakPintar worksheet PDFs."""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

from werkzeug.datastructures import MultiDict

from modules.render.pdf import render
from modules.spec import MAX_SEED, parse_spec, spec_to_query

# (multidict key, argparse destination) for every topic option flag.
TOPIC_OPTIONS: tuple[tuple[str, str], ...] = (
    ("grid_start", "grid_start"),
    ("grid_blanks", "grid_blanks"),
    ("count_max", "count_max"),
    ("count_shapes", "count_shapes"),
    ("add_digits", "add_digits"),
    ("add_regroup", "add_regroup"),
    ("sub_digits", "sub_digits"),
    ("sub_borrow", "sub_borrow"),
    ("sifir_tables", "sifir_tables"),
    ("sifir_n", "sifir_n"),
    ("div_digits", "div_digits"),
    ("div_divisors", "div_divisors"),
    ("div_rem", "div_rem"),
    ("abc_case", "abc_case"),
    ("missing_blanks", "missing_blanks"),
    ("themes", "themes"),
    ("guess_hint", "guess_hint"),
)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the worksheet CLI."""
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Generate a printable A4 math and alphabet worksheet PDF with an answer key.",
    )
    parser.add_argument(
        "--preset",
        help="preset name (t1, t2, t3, abc); explicit flags override the preset",
    )
    parser.add_argument(
        "--topics",
        help=(
            "comma-separated topics: grid, count, add, sub, sifir_ref, sifir, div, "
            "trace, missing, match, first_letter, guess_word"
        ),
    )
    parser.add_argument("--pages", help="total content sheets, 1 to 20")
    parser.add_argument("--lang", help="worksheet language, ms or en (default ms)")
    parser.add_argument("--no-answers", action="store_true", help="omit the answer sheets")
    parser.add_argument(
        "--seed",
        help="random seed, 0 to 2147483647; one is picked and printed when omitted",
    )
    parser.add_argument("--grid-start", help="first number in the grid: 1, 101, ... 901")
    parser.add_argument("--grid-blanks", help="blanks to leave in the grid, 15 to 60")
    parser.add_argument("--count-max", help="maximum count: 5, 10 or 20 (default 10)")
    parser.add_argument(
        "--count-shapes",
        help="comma-separated shapes: star, circle, apple, fish, flower",
    )
    parser.add_argument("--add-digits", help="digits per addition operand: 1, 2 or 3")
    parser.add_argument(
        "--add-regroup",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="require a carrying column",
    )
    parser.add_argument("--sub-digits", help="digits in the top subtraction operand: 1, 2 or 3")
    parser.add_argument(
        "--sub-borrow",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="require borrowing, needs --sub-digits 2 or 3",
    )
    parser.add_argument("--sifir-tables", help="comma-separated tables, 1 to 12")
    parser.add_argument("--sifir-n", help="questions per sifir sheet")
    parser.add_argument("--div-digits", help="dividend digits: 2 or 3")
    parser.add_argument("--div-divisors", help="comma-separated divisors, 2 to 9")
    parser.add_argument(
        "--div-rem",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="require a nonzero remainder",
    )
    parser.add_argument(
        "--abc-case",
        help="letter case for tracing and missing letters: upper or lower",
    )
    parser.add_argument(
        "--missing-blanks",
        help="blanks per row for missing letters: 1, 2, or 3",
    )
    parser.add_argument(
        "--themes",
        help="comma-separated themes: animals, fruits, vehicles, sports",
    )
    parser.add_argument(
        "--guess-hint",
        choices=["0", "1"],
        help="show scrambled letter hints for guess_word: 0 or 1 (default 1)",
    )
    parser.add_argument("-o", "--output", required=True, help="PDF path to write")
    return parser


def build_params(args: argparse.Namespace, seed: str) -> MultiDict:
    """Turn parsed CLI arguments into the multidict parse_spec expects."""
    pairs: list[tuple[str, str]] = []
    if args.preset is not None:
        pairs.append(("preset", args.preset))
    if args.topics is not None:
        pairs.append(("t", args.topics))
    if args.pages is not None:
        pairs.append(("pages", args.pages))
    if args.lang is not None:
        pairs.append(("lang", args.lang))
    pairs.append(("ans", "0" if args.no_answers else "1"))
    pairs.append(("seed", seed))

    for key, dest in TOPIC_OPTIONS:
        value = getattr(args, dest)
        if value is None:
            continue
        if isinstance(value, bool):
            pairs.append((key, "1" if value else "0"))
        else:
            pairs.append((key, str(value)))

    return MultiDict(pairs)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    args = build_parser().parse_args(argv)

    seed = (
        args.seed
        if args.seed is not None and args.seed.strip()
        else str(secrets.randbelow(MAX_SEED + 1))
    )
    spec, errors = parse_spec(build_params(args, seed))
    if errors:
        for field, message_key in errors:
            print(f"{field}: {message_key}", file=sys.stderr)
        return 2

    try:
        pdf_bytes = render(spec)
    except (NotImplementedError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output = Path(args.output)
    try:
        output.write_bytes(pdf_bytes)
    except OSError as exc:
        print(f"error: cannot write {output}: {exc}", file=sys.stderr)
        return 2

    print(spec_to_query(spec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
