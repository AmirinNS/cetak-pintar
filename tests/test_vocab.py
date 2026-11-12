"""Unit tests for modules.vocab vocabulary data."""

import re
from dataclasses import FrozenInstanceError

import pytest
from PIL import Image

from modules.vocab import THEMES, VOCAB, VocabItem, image_path, items_for

WORD_RE = re.compile(r"^[A-Z]{3,8}$")


def test_vocab_has_48_items():
    assert len(VOCAB) == 48


def test_themes_are_the_four_approved():
    assert THEMES == ("animals", "fruits", "vehicles", "sports")


def test_ids_are_unique():
    ids = [item.id for item in VOCAB]
    assert len(ids) == len(set(ids))


def test_every_theme_is_known():
    assert all(item.theme in THEMES for item in VOCAB)


@pytest.mark.parametrize("theme", THEMES)
def test_twelve_items_per_theme(theme):
    assert sum(1 for item in VOCAB if item.theme == theme) == 12


@pytest.mark.parametrize("item", VOCAB, ids=lambda item: f"{item.theme}/{item.id}")
def test_both_words_match_pattern(item):
    assert WORD_RE.match(item.ms), item.ms
    assert WORD_RE.match(item.en), item.en


def test_vocab_item_is_frozen():
    item = VOCAB[0]
    assert isinstance(item, VocabItem)
    with pytest.raises(FrozenInstanceError):
        item.ms = "X"  # type: ignore[misc]


def test_items_for_single_theme():
    animals = items_for(("animals",))
    assert len(animals) == 12
    assert all(item.theme == "animals" for item in animals)
    assert animals == tuple(item for item in VOCAB if item.theme == "animals")


def test_items_for_returns_canonical_theme_order():
    # Ask for fruits and animals in reverse; canonical order puts animals first.
    result = items_for(("fruits", "animals"))
    themes_in_result = [item.theme for item in result]
    assert themes_in_result == ["animals"] * 12 + ["fruits"] * 12


def test_items_for_all_themes_returns_everything_in_order():
    assert items_for(THEMES) == VOCAB


def test_items_for_dedupes_and_ignores_unknown():
    assert items_for(("animals", "animals")) == items_for(("animals",))
    assert items_for(("animals", "nope")) == items_for(("animals",))


def test_items_for_empty_returns_empty():
    assert items_for(()) == ()


def test_image_path_resolves_under_static_img_vocab():
    item = VOCAB[0]
    path = image_path(item)
    assert path.is_absolute()
    assert path == path.resolve()
    assert path.parts[-5:-2] == ("static", "img", "vocab")
    assert path.parts[-2] == item.theme
    assert path.name == f"{item.id}.png"


def test_every_item_has_a_png_on_disk():
    missing = [image_path(item).as_posix() for item in VOCAB if not image_path(item).is_file()]
    assert not missing, f"missing line-art PNGs: {missing}"


def test_committed_pngs_are_512_square_1bit():
    offenders = []
    for item in VOCAB:
        path = image_path(item)
        if not path.is_file():
            continue
        with Image.open(path) as img:
            if img.size != (512, 512) or img.mode != "1":
                offenders.append(f"{path.name}: {img.size} {img.mode}")
    assert not offenders, "; ".join(offenders)
