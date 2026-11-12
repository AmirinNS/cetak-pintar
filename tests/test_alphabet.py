"""Unit tests for modules.alphabet generators."""

import string
from dataclasses import FrozenInstanceError
from random import Random

import pytest

from modules.alphabet import (
    MatchSet,
    MissingRow,
    match_sets,
    missing_rows,
    picture_items,
    scramble,
    trace_letters,
)

# --- trace_letters tests ---


def test_trace_letters_sheet_zero_uppercase():
    assert trace_letters(0, 4, "upper") == ["A", "B", "C", "D"]


def test_trace_letters_sheet_zero_lowercase():
    assert trace_letters(0, 4, "lower") == ["a", "b", "c", "d"]


def test_trace_letters_wraps_after_z():
    # Sheet 6 with per_sheet=4 starts at 4*6 = 24 (Y), giving Y, Z, A, B
    assert trace_letters(6, 4, "upper") == ["Y", "Z", "A", "B"]
    assert trace_letters(6, 4, "lower") == ["y", "z", "a", "b"]


def test_trace_letters_multiple_sheets_continuity():
    all_letters = []
    for sheet in range(7):
        all_letters.extend(trace_letters(sheet, 4, "upper"))
    # First 26 letters are A..Z, then wrapped A, B
    assert "".join(all_letters[:26]) == string.ascii_uppercase
    assert all_letters[26:] == ["A", "B"]


@pytest.mark.parametrize("per_sheet", [1, 3, 5, 6, 26])
def test_trace_letters_different_per_sheet(per_sheet):
    result = trace_letters(0, per_sheet, "upper")
    assert len(result) == per_sheet
    assert result == list(string.ascii_uppercase[:per_sheet])


@pytest.mark.parametrize("invalid_case", ["UPPER", "title", "mix", "", "Upper"])
def test_trace_letters_invalid_case_raises(invalid_case):
    with pytest.raises(ValueError, match="Invalid case"):
        trace_letters(0, 4, invalid_case)


def test_trace_letters_negative_sheet_index_raises():
    with pytest.raises(ValueError, match="sheet_index must be non-negative"):
        trace_letters(-1, 4, "upper")


@pytest.mark.parametrize("invalid_per_sheet", [0, -1, -5])
def test_trace_letters_invalid_per_sheet_raises(invalid_per_sheet):
    with pytest.raises(ValueError, match="per_sheet must be positive"):
        trace_letters(0, invalid_per_sheet, "upper")


# --- missing_rows tests ---


@pytest.mark.parametrize("case", ["upper", "lower"])
@pytest.mark.parametrize("blanks_count", [1, 2, 3])
def test_missing_rows_structure_and_constraints(case, blanks_count):
    rng = Random(42)
    rows = missing_rows(rng, case, blanks_count, 20)
    assert len(rows) == 20

    alphabet = string.ascii_uppercase if case == "upper" else string.ascii_lowercase

    for row in rows:
        assert isinstance(row, MissingRow)
        assert len(row.letters) == 6
        assert len(row.blanks) == blanks_count

        # Letters must be 6 consecutive letters from the alphabet
        start_idx = alphabet.index(row.letters[0])
        # Start letter must be in A..U (0..20)
        assert 0 <= start_idx <= 20
        expected_letters = tuple(alphabet[start_idx + i] for i in range(6))
        assert row.letters == expected_letters

        # Blanks must never be at index 0, and sampled from 1..5
        assert 0 not in row.blanks
        assert all(1 <= b <= 5 for b in row.blanks)
        # Blanks must be strictly sorted and distinct
        assert row.blanks == tuple(sorted(row.blanks))
        assert len(set(row.blanks)) == blanks_count


def test_missing_rows_start_letter_distribution():
    # Verify over many rows that start letters span across A..U and never exceed U
    rng = Random(12345)
    rows = missing_rows(rng, "upper", blanks=2, n=500)
    start_letters = {row.letters[0] for row in rows}

    allowed_starts = set(string.ascii_uppercase[:21])  # A through U
    assert start_letters == allowed_starts
    assert not any(row.letters[0] in string.ascii_uppercase[21:] for row in rows)


def test_missing_rows_determinism():
    rows_a = missing_rows(Random(999), "upper", blanks=2, n=10)
    rows_b = missing_rows(Random(999), "upper", blanks=2, n=10)
    assert rows_a == rows_b


@pytest.mark.parametrize("invalid_blanks", [0, -1, 4, 5, 10])
def test_missing_rows_invalid_blanks_raises(invalid_blanks):
    with pytest.raises(ValueError, match="blanks must be between 1 and 3"):
        missing_rows(Random(0), "upper", invalid_blanks, 5)


@pytest.mark.parametrize("invalid_case", ["UPPER", "mix", "capital", ""])
def test_missing_rows_invalid_case_raises(invalid_case):
    with pytest.raises(ValueError, match="Invalid case"):
        missing_rows(Random(0), invalid_case, 2, 5)


def test_missing_rows_negative_n_raises():
    with pytest.raises(ValueError, match="n must be non-negative"):
        missing_rows(Random(0), "upper", 2, -1)


def test_missing_row_immutability():
    row = MissingRow(letters=("A", "B", "C", "D", "E", "F"), blanks=(1, 3))
    with pytest.raises(FrozenInstanceError):
        row.letters = ("X", "Y")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.blanks = (2, 4)  # type: ignore[misc]


# --- match_sets tests ---


@pytest.mark.parametrize("pairs_count", [1, 2, 3, 5, 6, 10, 26])
def test_match_sets_structure_and_permutation(pairs_count):
    rng = Random(2026)
    sets = match_sets(rng, n_sets=15, pairs=pairs_count)
    assert len(sets) == 15

    for ms in sets:
        assert isinstance(ms, MatchSet)
        assert len(ms.left) == pairs_count
        assert len(ms.right) == pairs_count
        assert len(ms.pairs) == pairs_count

        # Left consists of distinct uppercase letters, sorted alphabetically
        assert len(set(ms.left)) == pairs_count
        assert all(c in string.ascii_uppercase for c in ms.left)
        assert ms.left == tuple(sorted(ms.left))

        # Right is a permutation of lowercase left
        assert sorted(ms.right) == sorted(c.lower() for c in ms.left)
        assert set(ms.right) == {c.lower() for c in ms.left}

        # pairs[i] is index in right that matches left[i]
        for i, left_char in enumerate(ms.left):
            match_idx = ms.pairs[i]
            assert ms.right[match_idx] == left_char.lower()

        # pairs contains every index 0..pairs_count-1 exactly once
        assert sorted(ms.pairs) == list(range(pairs_count))

        # When pairs >= 2, right must differ from left order
        if pairs_count >= 2:
            assert ms.right != tuple(c.lower() for c in ms.left)


def test_match_sets_pairs_one():
    rng = Random(7)
    sets = match_sets(rng, n_sets=3, pairs=1)
    for ms in sets:
        assert len(ms.left) == 1
        assert ms.right == (ms.left[0].lower(),)
        assert ms.pairs == (0,)


def test_match_sets_determinism():
    sets_a = match_sets(Random(12345), n_sets=5, pairs=5)
    sets_b = match_sets(Random(12345), n_sets=5, pairs=5)
    assert sets_a == sets_b


@pytest.mark.parametrize("invalid_pairs", [0, -1, 27, 50])
def test_match_sets_invalid_pairs_raises(invalid_pairs):
    with pytest.raises(ValueError, match="pairs must be between 1 and 26"):
        match_sets(Random(0), 2, invalid_pairs)


def test_match_sets_negative_n_sets_raises():
    with pytest.raises(ValueError, match="n_sets must be non-negative"):
        match_sets(Random(0), -1, 5)


def test_match_set_immutability():
    ms = MatchSet(left=("A", "B"), right=("b", "a"), pairs=(1, 0))
    with pytest.raises(FrozenInstanceError):
        ms.left = ("C", "D")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ms.right = ("d", "c")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ms.pairs = (0, 1)  # type: ignore[misc]


@pytest.mark.parametrize("themes,n", [
    (("animals",), 12), (("fruits",), 8), (("vehicles", "sports"), 12),
])
def test_picture_items_distinct_per_sheet(themes, n):
    items = picture_items(Random(42), themes, n)
    assert len(items) == len(set(items)) == n
    assert all(item.theme in themes for item in items)
    assert items == picture_items(Random(42), themes, n)


def test_picture_items_repeat_fresh_passes():
    items = picture_items(Random(42), ("animals",), 30)
    assert len(items) == 30
    assert len(set(items[:12])) == len(set(items[12:24])) == 12
    assert len(set(items[24:])) == 6
    assert picture_items(Random(42), ("animals",), 0) == []


@pytest.mark.parametrize("word", ["CAT", "RAMBUTAN", "ELEPHANT", "SWIMMING", "AAAAAAAB", "AB"])
def test_scramble_changes_word_and_preserves_letters(word):
    for seed in range(100):
        hint = scramble(Random(seed), word)
        assert hint != word
        assert sorted(hint) == sorted(word)
        assert hint == scramble(Random(seed), word)


@pytest.mark.parametrize("word", ["", "A", "AAAA"])
def test_scramble_single_letter_type(word):
    assert scramble(Random(42), word) == word
