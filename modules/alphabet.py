"""Alphabet worksheet problem generators for tracing, missing letters, and matching."""

import string
from dataclasses import dataclass
from random import Random

from modules.vocab import VocabItem, items_for


@dataclass(frozen=True)
class MissingRow:
    """Row of consecutive alphabet letters with designated blank positions."""

    letters: tuple[str, ...]
    blanks: tuple[int, ...]


@dataclass(frozen=True)
class MatchSet:
    """Letter matching set with uppercase left, lowercase shuffled right, and pair indices."""

    left: tuple[str, ...]
    right: tuple[str, ...]
    pairs: tuple[int, ...]


def trace_letters(sheet_index: int, per_sheet: int, case: str) -> list[str]:
    """Return letters for a tracing sheet, wrapping around the alphabet after Z.

    Letters follow sequence 4*i .. 4*i + 3 when per_sheet=4 (e.g., sheet 6 gives
    Y, Z, A, B). Supported cases are 'upper' and 'lower'.
    """
    if sheet_index < 0:
        raise ValueError(f"sheet_index must be non-negative, got {sheet_index}")
    if per_sheet <= 0:
        raise ValueError(f"per_sheet must be positive, got {per_sheet}")
    if case not in ("upper", "lower"):
        raise ValueError(f"Invalid case: {case!r}, must be 'upper' or 'lower'")

    alphabet = string.ascii_uppercase if case == "upper" else string.ascii_lowercase
    start_pos = (sheet_index * per_sheet) % len(alphabet)
    return [alphabet[(start_pos + i) % len(alphabet)] for i in range(per_sheet)]


def missing_rows(rng: Random, case: str, blanks: int, n: int) -> list[MissingRow]:
    """Generate n rows of 6 consecutive letters with blanks designated at positions 1..5.

    The start letter is sampled uniformly from A..U so that 6 consecutive letters
    always fit within the alphabet without wrapping. Blanks must be between 1 and 3,
    and are sampled from positions 1..5 (index 0 is never blank) and sorted.
    """
    if case not in ("upper", "lower"):
        raise ValueError(f"Invalid case: {case!r}, must be 'upper' or 'lower'")
    if not (1 <= blanks <= 3):
        raise ValueError(f"blanks must be between 1 and 3, got {blanks}")
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")

    alphabet = string.ascii_uppercase if case == "upper" else string.ascii_lowercase
    rows: list[MissingRow] = []
    for _ in range(n):
        # Uniform start in A..U (indices 0..20, since 20 + 6 = 26)
        start = rng.randint(0, 20)
        letters = tuple(alphabet[start + i] for i in range(6))
        blank_indices = tuple(sorted(rng.sample(range(1, 6), blanks)))
        rows.append(MissingRow(letters=letters, blanks=blank_indices))
    return rows


def match_sets(rng: Random, n_sets: int, pairs: int) -> list[MatchSet]:
    """Generate letter matching sets of uppercase left and shuffled lowercase right.

    The left column contains `pairs` distinct uppercase letters, sorted alphabetically
    for clean and predictable worksheet presentation. The right column contains the
    same letters in lowercase, shuffled such that the right column order differs from
    the left column order whenever pairs >= 2. `pairs[i]` records the index in `right`
    that matches `left[i]`.
    """
    if not (1 <= pairs <= 26):
        raise ValueError(f"pairs must be between 1 and 26, got {pairs}")
    if n_sets < 0:
        raise ValueError(f"n_sets must be non-negative, got {n_sets}")

    sets: list[MatchSet] = []
    for _ in range(n_sets):
        # Sample distinct uppercase letters and sort alphabetically
        left_letters = tuple(sorted(rng.sample(string.ascii_uppercase, pairs)))
        lower_letters = tuple(c.lower() for c in left_letters)

        if pairs >= 2:
            shuffled = list(lower_letters)
            while True:
                rng.shuffle(shuffled)
                if tuple(shuffled) != lower_letters:
                    break
            right_letters = tuple(shuffled)
        else:
            right_letters = lower_letters

        pair_indices = tuple(right_letters.index(c.lower()) for c in left_letters)
        sets.append(MatchSet(left=left_letters, right=right_letters, pairs=pair_indices))
    return sets


def picture_items(rng: Random, themes: tuple[str, ...], n: int) -> list[VocabItem]:
    """Sample picture items, using fresh shuffled passes if n exceeds the pool."""
    pool = items_for(themes)
    items: list[VocabItem] = []
    while len(items) < n:
        items.extend(rng.sample(pool, min(n - len(items), len(pool))))
    return items


def scramble(rng: Random, word: str) -> str:
    """Shuffle letters, swapping two distinct letters if the shuffle is unchanged."""
    letters = list(word)
    rng.shuffle(letters)
    if "".join(letters) == word:
        for index, letter in enumerate(letters):
            if letter != letters[0]:
                letters[0], letters[index] = letters[index], letters[0]
                break
    return "".join(letters)
