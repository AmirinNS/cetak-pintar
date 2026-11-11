"""Arithmetic guarantees for the constructive generators."""

from dataclasses import FrozenInstanceError
from random import Random

import pytest

from modules.problems import (
    ArithmeticProblem,
    CountingProblem,
    DivisionProblem,
    DivisionStep,
    addition,
    borrows,
    carries,
    counting,
    division,
    division_steps,
    grid_blanks,
    multiplication,
    subtraction,
)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [(19, 81, True), (99, 1, True), (999, 1, True), (0, 0, False), (123, 456, False)],
)
def test_carries_directed(a, b, expected):
    assert carries(a, b) is expected


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (100, 1, True),
        (100, 99, True),
        (101, 2, True),
        (0, 0, False),
        (9, 1, False),
        (987, 654, False),
    ],
)
def test_borrows_directed(a, b, expected):
    assert borrows(a, b) is expected


@pytest.mark.parametrize("start", range(1, 1000, 100))
@pytest.mark.parametrize("count", [15, 30, 60])
def test_grid_guarantees_over_200_seeds(start, count):
    for seed in range(200):
        blanks = grid_blanks(Random(seed), start, count)
        assert len(blanks) == count
        assert blanks == sorted(set(blanks))
        assert all(start <= value <= start + 99 for value in blanks)
        assert blanks == grid_blanks(Random(seed), start, count)


@pytest.mark.parametrize("digits", [1, 2, 3])
@pytest.mark.parametrize("regroup", [False, True])
def test_addition_guarantees_over_200_seeds(digits, regroup):
    n = 16 if digits == 3 else 20
    saw_four_digit_sum = False
    for seed in range(200):
        problems = addition(Random(seed), digits, regroup, n)
        assert len(problems) == n
        assert problems == addition(Random(seed), digits, regroup, n)
        for problem in problems:
            assert 10 ** (digits - 1) <= problem.a < 10**digits
            assert 10 ** (digits - 1) <= problem.b < 10**digits
            assert problem.answer == problem.a + problem.b
            assert carries(problem.a, problem.b) is regroup
            # Each carry reduces the total digit sum by nine, independently of
            # the column-by-column predicate used above.
            operand_digit_sum = sum(map(int, str(problem.a) + str(problem.b)))
            answer_digit_sum = sum(map(int, str(problem.answer)))
            assert (operand_digit_sum > answer_digit_sum) is regroup
            saw_four_digit_sum |= problem.answer >= 1000
    if digits == 3 and regroup:
        assert saw_four_digit_sum


@pytest.mark.parametrize(
    ("digits", "borrow"),
    [(1, False), (2, False), (3, False), (2, True), (3, True)],
)
def test_subtraction_guarantees_over_200_seeds(digits, borrow):
    n = 16 if digits == 3 else 20
    for seed in range(200):
        problems = subtraction(Random(seed), digits, borrow, n)
        assert len(problems) == n
        assert problems == subtraction(Random(seed), digits, borrow, n)
        for problem in problems:
            assert 10 ** (digits - 1) <= problem.a < 10**digits
            assert 1 <= problem.b <= problem.a
            assert problem.answer == problem.a - problem.b >= 0
            assert borrows(problem.a, problem.b) is borrow
            # Applying the addition digit-sum identity to b + answer = a also
            # detects borrowing without reusing the predicate's algorithm.
            parts_digit_sum = sum(map(int, str(problem.b) + str(problem.answer)))
            top_digit_sum = sum(map(int, str(problem.a)))
            assert (parts_digit_sum > top_digit_sum) is borrow


@pytest.mark.parametrize("n", [0, 1, 20])
def test_single_digit_borrow_is_impossible(n):
    with pytest.raises(ValueError, match="at least two digits"):
        subtraction(Random(0), 1, True, n)


def test_zero_requested_problems():
    assert addition(Random(0), 3, True, 0) == []
    assert subtraction(Random(0), 3, True, 0) == []
    assert multiplication(Random(0), [2, 3], 0) == []


def test_problem_is_frozen():
    problem = ArithmeticProblem(19, 81, 100)
    with pytest.raises(FrozenInstanceError):
        problem.answer = 0


def test_generators_share_a_deterministic_random_stream():
    first = Random(2147483647)
    second = Random(2147483647)
    assert grid_blanks(first, 901, 60) == grid_blanks(second, 901, 60)
    assert addition(first, 3, True, 16) == addition(second, 3, True, 16)
    assert subtraction(first, 3, True, 16) == subtraction(second, 3, True, 16)
    assert multiplication(first, [2, 3, 4], 20) == multiplication(second, [2, 3, 4], 20)
    assert first.getstate() == second.getstate()


@pytest.mark.parametrize(
    ("tables", "expected_capacity"),
    [
        ([7], 12),
        ([2, 3], 24),
        ([2, 3, 4, 5], 48),
        (list(range(1, 13)), 144),
    ],
)
def test_multiplication_pool_size_and_exact_capacity(tables, expected_capacity):
    rng = Random(42)
    # Exact capacity works
    probs = multiplication(rng, tables, expected_capacity)
    assert len(probs) == expected_capacity
    assert all(isinstance(p, ArithmeticProblem) for p in probs)
    assert all(p.answer == p.a * p.b for p in probs)


@pytest.mark.parametrize(
    ("tables", "excess_n"),
    [
        ([7], 13),
        ([2, 3], 25),
        ([2, 3, 4, 5], 49),
    ],
)
def test_multiplication_capacity_plus_one_raises(tables, excess_n):
    with pytest.raises(ValueError, match="pool capacity"):
        multiplication(Random(0), tables, excess_n)


def test_multiplication_negative_count_raises():
    with pytest.raises(ValueError, match="negative"):
        multiplication(Random(0), [2, 3], -1)


def test_multiplication_single_table_covers_all_twelve_factors():
    rng = Random(999)
    probs = multiplication(rng, [7], 12)
    assert len(probs) == 12
    assert all(p.a == 7 for p in probs)
    assert {p.b for p in probs} == set(range(1, 13))
    assert all(p.answer == 7 * p.b for p in probs)


def test_multiplication_guarantees_over_200_seeds():
    tables = [2, 3, 4, 5]
    n = 24
    for seed in range(200):
        rng = Random(seed)
        probs = multiplication(rng, tables, n)
        assert len(probs) == n
        # Determinism
        assert probs == multiplication(Random(seed), tables, n)
        # Operand and answer invariants
        assert all(p.a in tables for p in probs)
        assert all(1 <= p.b <= 12 for p in probs)
        assert all(p.answer == p.a * p.b for p in probs)
        # Sampling without replacement: unique (table, factor) pairs on each sheet
        pairs = [(p.a, p.b) for p in probs]
        assert len(set(pairs)) == n


@pytest.mark.parametrize(
    ("dividend", "divisor", "expected"),
    [
        (12, 9, [(1, 12, 12, 1, 9, 3)]),
        (100, 4, [(1, 10, 10, 2, 8, 2), (2, 0, 20, 5, 20, 0)]),
        (101, 5, [(1, 10, 10, 2, 10, 0), (2, 1, 1, 0, 0, 1)]),
        (208, 2, [(0, 2, 2, 1, 2, 0), (1, 0, 0, 0, 0, 0), (2, 8, 8, 4, 8, 0)]),
        (999, 9, [(0, 9, 9, 1, 9, 0), (1, 9, 9, 1, 9, 0), (2, 9, 9, 1, 9, 0)]),
    ],
)
def test_division_directed_steps(dividend, divisor, expected):
    assert division_steps(dividend, divisor) == tuple(DivisionStep(*step) for step in expected)


@pytest.mark.parametrize("digits", [2, 3])
@pytest.mark.parametrize("remainder", [False, True])
@pytest.mark.parametrize("divisors", [(2,), (9,), tuple(range(2, 10))])
def test_division_guarantees_over_200_seeds(digits, remainder, divisors):
    count = 8 if digits == 3 else 12
    for seed in range(200):
        problems = division(Random(seed), digits, divisors, remainder, count)
        assert len(problems) == count
        assert problems == division(Random(seed), digits, divisors, remainder, count)
        for problem in problems:
            assert 10 ** (digits - 1) <= problem.dividend < 10**digits
            assert problem.divisor in divisors
            assert (problem.quotient, problem.remainder) == divmod(
                problem.dividend, problem.divisor
            )
            assert problem.dividend == problem.divisor * problem.quotient + problem.remainder
            assert (problem.remainder > 0) is remainder
            assert 0 <= problem.remainder < problem.divisor
            assert len(problem.steps) == len(str(problem.quotient))
            assert tuple(step.col for step in problem.steps) == tuple(
                range(problem.steps[0].col, digits)
            )
            previous_difference = 0
            quotient = 0
            for index, step in enumerate(problem.steps):
                expected_brought_down = int(
                    str(problem.dividend)[:step.col + 1] if index == 0
                    else str(problem.dividend)[step.col]
                )
                assert step.brought_down == expected_brought_down
                assert step.partial == previous_difference * 10 + step.brought_down
                assert step.product == step.q_digit * problem.divisor
                assert step.difference == step.partial - step.product
                assert 0 <= step.q_digit <= 9
                assert 0 <= step.difference < problem.divisor
                previous_difference = step.difference
                quotient = quotient * 10 + step.q_digit
            assert quotient == problem.quotient
            assert previous_difference == problem.remainder


def test_division_zero_count_and_stable_divisor_order():
    assert division(Random(0), 2, [2, 3], True, 0) == []
    assert division(Random(42), 3, [9, 2, 9], True, 8) == division(
        Random(42), 3, [2, 9], True, 8
    )


def test_division_values_are_frozen():
    step = DivisionStep(1, 12, 12, 1, 9, 3)
    problem = DivisionProblem(12, 9, 1, 3, (step,))
    with pytest.raises(FrozenInstanceError):
        step.q_digit = 0
    with pytest.raises(FrozenInstanceError):
        problem.quotient = 0


@pytest.mark.parametrize("max_n", [5, 10, 20])
@pytest.mark.parametrize(
    "shapes",
    [
        ("star",),
        ("apple", "fish"),
        ("star", "circle", "apple", "fish", "flower"),
    ],
)
def test_counting_guarantees_over_200_seeds(max_n: int, shapes: tuple[str, ...]) -> None:
    n = 12
    for seed in range(200):
        problems = counting(Random(seed), max_n, shapes, n)
        assert len(problems) == n
        # Determinism guarantee
        assert problems == counting(Random(seed), max_n, shapes, n)
        for p in problems:
            assert 1 <= p.count <= max_n
            assert p.shape in shapes
            assert len(p.positions) == p.count
            # Guaranteed non-overlapping
            assert len(set(p.positions)) == p.count
            # Guaranteed inside small grid bounds
            for col, row in p.positions:
                assert 0 <= col < p.grid_cols
                assert 0 <= row < p.grid_rows


def test_counting_validation_and_errors() -> None:
    rng = Random(42)
    with pytest.raises(ValueError, match="cannot be negative"):
        counting(rng, 10, ["star"], -1)
    with pytest.raises(ValueError, match="at least 1"):
        counting(rng, 0, ["star"], 5)
    with pytest.raises(ValueError, match="cannot be empty"):
        counting(rng, 10, [], 5)


def test_counting_values_are_frozen() -> None:
    problem = CountingProblem(
        shape="star",
        count=3,
        positions=((0, 0), (1, 1), (2, 0)),
        grid_cols=4,
        grid_rows=2,
    )
    with pytest.raises(FrozenInstanceError):
        problem.count = 4
    with pytest.raises(FrozenInstanceError):
        problem.shape = "circle"


