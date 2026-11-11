"""Seeded, constructive worksheet problem generators."""

from collections.abc import Sequence
from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class ArithmeticProblem:
    a: int
    b: int
    answer: int


def carries(a: int, b: int) -> bool:
    """Return whether addition carries in any column, including incoming carries."""
    carry = 0
    carried = False
    while a or b:
        carry = (a % 10 + b % 10 + carry) // 10
        carried = carried or bool(carry)
        a //= 10
        b //= 10
    return carried


def borrows(a: int, b: int) -> bool:
    """Return whether subtraction borrows in any column, propagating each borrow."""
    borrow = 0
    borrowed = False
    while a or b:
        borrow = int(a % 10 - borrow < b % 10)
        borrowed = borrowed or bool(borrow)
        a //= 10
        b //= 10
    return borrowed


def grid_blanks(rng: Random, start: int, count: int) -> list[int]:
    """Return sorted, distinct displayed numbers to blank in a 100-cell grid."""
    return sorted(rng.sample(range(start, start + 100), count))


def addition(rng: Random, digits: int, regroup: bool, n: int) -> list[ArithmeticProblem]:
    """Build exact-width operands, forcing at least one carry when requested."""
    problems = []
    for _ in range(n):
        forced_column = rng.randrange(digits) if regroup else None
        a = b = carry = 0
        for column in range(digits):
            minimum = int(column == digits - 1)
            forced = column == forced_column
            lower_a = max(minimum, 1 - carry) if forced else minimum
            upper_a = 9 if regroup else 9 - carry - minimum
            digit_a = rng.randint(lower_a, upper_a)
            lower_b = max(minimum, 10 - carry - digit_a) if forced else minimum
            upper_b = 9 if regroup else 9 - carry - digit_a
            digit_b = rng.randint(lower_b, upper_b)
            a += digit_a * 10**column
            b += digit_b * 10**column
            carry = (digit_a + digit_b + carry) // 10
        problems.append(ArithmeticProblem(a, b, a + b))
    return problems


def subtraction(rng: Random, digits: int, borrow: bool, n: int) -> list[ArithmeticProblem]:
    """Build nonnegative differences with a positive bottom operand.

    A required borrow starts below the leading column. The leading column always
    settles an incoming borrow so the completed top operand is at least the bottom.
    """
    if digits == 1 and borrow:
        raise ValueError("Borrowing requires at least two digits")

    problems = []
    for _ in range(n):
        forced_column = rng.randrange(digits - 1) if borrow else None
        nonzero_column = rng.randrange(digits)
        a = b = incoming = 0
        for column in range(digits):
            minimum_a = int(column == digits - 1)
            minimum_b = int(column == nonzero_column)
            if not borrow or column == digits - 1:
                digit_a = rng.randint(max(minimum_a, incoming + minimum_b), 9)
                digit_b = rng.randint(minimum_b, digit_a - incoming)
            elif column == forced_column:
                digit_a = rng.randint(minimum_a, min(9, 8 + incoming))
                digit_b = rng.randint(max(minimum_b, digit_a - incoming + 1), 9)
            else:
                digit_a = rng.randint(minimum_a, 9)
                digit_b = rng.randint(minimum_b, 9)
            a += digit_a * 10**column
            b += digit_b * 10**column
            incoming = int(digit_a - incoming < digit_b)
        problems.append(ArithmeticProblem(a, b, a - b))
    return problems


def multiplication(rng: Random, tables: Sequence[int], n: int) -> list[ArithmeticProblem]:
    """Sample n multiplication problems without replacement from the stable ordered pool.

    The pool consists of (t, f) for t in sorted(set(tables)) and f in 1..12.
    Raises ValueError if n exceeds pool capacity or is negative.
    """
    sorted_tables = sorted(set(tables))
    pool = [(t, f) for t in sorted_tables for f in range(1, 13)]
    if n > len(pool):
        raise ValueError(f"Requested {n} problems, but pool capacity is {len(pool)}")
    if n < 0:
        raise ValueError(f"Requested count cannot be negative: {n}")
    sampled = rng.sample(pool, n)
    return [ArithmeticProblem(t, f, t * f) for t, f in sampled]


@dataclass(frozen=True)
class DivisionStep:
    col: int
    brought_down: int
    partial: int
    q_digit: int
    product: int
    difference: int


@dataclass(frozen=True)
class DivisionProblem:
    dividend: int
    divisor: int
    quotient: int
    remainder: int
    steps: tuple[DivisionStep, ...]


def division_steps(dividend: int, divisor: int) -> tuple[DivisionStep, ...]:
    """Work left to right, using zero-based dividend columns.

    Bring down the leading prefix until it reaches the divisor. That first
    step records the whole prefix as brought_down, with previous difference 0.
    Every later step brings down one digit, including when its quotient digit
    is zero. Thus partial = previous_difference * 10 + brought_down for every
    step. Products and differences end at col in the written working.
    """
    steps = []
    difference = prefix = 0
    for col, digit in enumerate(map(int, str(dividend))):
        if not steps:
            prefix = prefix * 10 + digit
            if prefix < divisor:
                continue
            brought_down = prefix
        else:
            brought_down = digit
        partial = difference * 10 + brought_down
        q_digit, difference = divmod(partial, divisor)
        steps.append(
            DivisionStep(col, brought_down, partial, q_digit, q_digit * divisor, difference)
        )
    return tuple(steps)


def division(
    rng: Random, digits: int, divisors: Sequence[int], remainder: bool, n: int
) -> list[DivisionProblem]:
    """Choose divisor and quotient, then a remainder within exact-width bounds.

    For nonzero remainders, boundary quotients restrict the remainder interval
    to keep the dividend in range. No candidate rejection or retry is needed.
    Callers validate digits (2 or 3) and nonempty divisors (2..9) in the spec.
    """
    minimum, maximum = 10 ** (digits - 1), 10**digits - 1
    choices = sorted(set(divisors))
    problems = []
    for _ in range(n):
        divisor = rng.choice(choices)
        if remainder:
            quotient = rng.randint(minimum // divisor, (maximum - 1) // divisor)
            residual = rng.randint(
                max(1, minimum - divisor * quotient),
                min(divisor - 1, maximum - divisor * quotient),
            )
        else:
            quotient = rng.randint((minimum + divisor - 1) // divisor, maximum // divisor)
            residual = 0
        dividend = divisor * quotient + residual
        problems.append(
            DivisionProblem(
                dividend, divisor, quotient, residual, division_steps(dividend, divisor)
            )
        )
    return problems


@dataclass(frozen=True)
class CountingProblem:
    shape: str
    count: int
    positions: tuple[tuple[int, int], ...]
    grid_cols: int
    grid_rows: int


def _counting_grid_dimensions(max_n: int) -> tuple[int, int]:
    """Return (cols, rows) for the small grid inside each counting box."""
    if max_n <= 6:
        return (3, 2)
    if max_n <= 12:
        return (4, 3)
    if max_n <= 20:
        return (5, 4)
    cols = 5
    rows = (max_n + cols - 1) // cols
    return (cols, rows)


def counting(
    rng: Random, max_n: int, shapes: Sequence[str], n: int
) -> list[CountingProblem]:
    """Generate n picture counting problems with non-overlapping positions.

    Each problem has a randomly selected shape from shapes, a count from 1 to max_n,
    and deterministic non-overlapping grid positions inside the box's small grid.
    """
    if n < 0:
        raise ValueError(f"Requested count cannot be negative: {n}")
    if max_n < 1:
        raise ValueError(f"max_n must be at least 1, got {max_n}")
    shape_choices = tuple(shapes)
    if not shape_choices:
        raise ValueError("shapes cannot be empty")

    grid_cols, grid_rows = _counting_grid_dimensions(max_n)
    all_cells = [(col, row) for row in range(grid_rows) for col in range(grid_cols)]

    problems: list[CountingProblem] = []
    for _ in range(n):
        shape = rng.choice(shape_choices)
        count = rng.randint(1, max_n)
        sampled = sorted(rng.sample(all_cells, count))
        problems.append(
            CountingProblem(
                shape=shape,
                count=count,
                positions=tuple(sampled),
                grid_cols=grid_cols,
                grid_rows=grid_rows,
            )
        )
    return problems


