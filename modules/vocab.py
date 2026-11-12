"""Approved picture-vocabulary data for the first_letter and guess_word topics.

Each item pairs a Malay word (ms) and an English word (en) for one line-art image.
Words are uppercase A to Z only, 3 to 8 letters, single words, so letter boxes and
first-letter logic stay simple. Image paths derive from theme and id and resolve
against this module the same way LOGO_PATH does in modules/render/primitives.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

THEMES: tuple[str, ...] = ("animals", "fruits", "vehicles", "sports")

# static/img/vocab, resolved from this file (modules/vocab.py -> repo root is parents[1]).
VOCAB_IMG_DIR: Path = Path(__file__).resolve().parents[1] / "static" / "img" / "vocab"


@dataclass(frozen=True)
class VocabItem:
    """One vocabulary item: stable id, theme, and the Malay and English words."""

    id: str
    theme: str
    ms: str
    en: str


VOCAB: tuple[VocabItem, ...] = (
    # animals
    VocabItem("cat", "animals", "KUCING", "CAT"),
    VocabItem("dog", "animals", "ANJING", "DOG"),
    VocabItem("rabbit", "animals", "ARNAB", "RABBIT"),
    VocabItem("chicken", "animals", "AYAM", "CHICKEN"),
    VocabItem("duck", "animals", "ITIK", "DUCK"),
    VocabItem("cow", "animals", "LEMBU", "COW"),
    VocabItem("goat", "animals", "KAMBING", "GOAT"),
    VocabItem("elephant", "animals", "GAJAH", "ELEPHANT"),
    VocabItem("tiger", "animals", "HARIMAU", "TIGER"),
    VocabItem("giraffe", "animals", "ZIRAFAH", "GIRAFFE"),
    VocabItem("horse", "animals", "KUDA", "HORSE"),
    VocabItem("fish", "animals", "IKAN", "FISH"),
    # fruits
    VocabItem("apple", "fruits", "EPAL", "APPLE"),
    VocabItem("banana", "fruits", "PISANG", "BANANA"),
    VocabItem("orange", "fruits", "OREN", "ORANGE"),
    VocabItem("grapes", "fruits", "ANGGUR", "GRAPES"),
    VocabItem("mango", "fruits", "MANGGA", "MANGO"),
    VocabItem("durian", "fruits", "DURIAN", "DURIAN"),
    VocabItem("papaya", "fruits", "BETIK", "PAPAYA"),
    VocabItem("coconut", "fruits", "KELAPA", "COCONUT"),
    VocabItem("lemon", "fruits", "LEMON", "LEMON"),
    VocabItem("pear", "fruits", "PIR", "PEAR"),
    VocabItem("cherry", "fruits", "CERI", "CHERRY"),
    VocabItem("rambutan", "fruits", "RAMBUTAN", "RAMBUTAN"),
    # vehicles
    VocabItem("car", "vehicles", "KERETA", "CAR"),
    VocabItem("bus", "vehicles", "BAS", "BUS"),
    VocabItem("truck", "vehicles", "LORI", "TRUCK"),
    VocabItem("bicycle", "vehicles", "BASIKAL", "BICYCLE"),
    VocabItem("ship", "vehicles", "KAPAL", "SHIP"),
    VocabItem("boat", "vehicles", "BOT", "BOAT"),
    VocabItem("taxi", "vehicles", "TEKSI", "TAXI"),
    VocabItem("scooter", "vehicles", "SKUTER", "SCOOTER"),
    VocabItem("train", "vehicles", "TREN", "TRAIN"),
    VocabItem("rocket", "vehicles", "ROKET", "ROCKET"),
    VocabItem("tractor", "vehicles", "TRAKTOR", "TRACTOR"),
    VocabItem("plane", "vehicles", "PESAWAT", "PLANE"),
    # sports
    VocabItem("tennis", "sports", "TENIS", "TENNIS"),
    VocabItem("golf", "sports", "GOLF", "GOLF"),
    VocabItem("rugby", "sports", "RAGBI", "RUGBY"),
    VocabItem("hockey", "sports", "HOKI", "HOCKEY"),
    VocabItem("bowling", "sports", "BOLING", "BOWLING"),
    VocabItem("cricket", "sports", "KRIKET", "CRICKET"),
    VocabItem("swimming", "sports", "RENANG", "SWIMMING"),
    VocabItem("running", "sports", "LARI", "RUNNING"),
    VocabItem("archery", "sports", "MEMANAH", "ARCHERY"),
    VocabItem("karate", "sports", "KARATE", "KARATE"),
    VocabItem("boxing", "sports", "TINJU", "BOXING"),
    VocabItem("silat", "sports", "SILAT", "SILAT"),
)


def items_for(themes) -> tuple[VocabItem, ...]:
    """Return the items for the given themes in canonical theme order.

    THEMES order (animals, fruits, vehicles, sports) governs the result regardless of
    the order themes arrive in, and within each theme the VOCAB order is preserved.
    Duplicate themes collapse. Unknown themes match nothing. The spec layer validates
    that themes is a non-empty subset of THEMES before calling this.
    """
    selected = set(themes)
    return tuple(item for item in VOCAB if item.theme in selected)


def image_path(item: VocabItem) -> Path:
    """Return the absolute path to the item's committed line-art PNG."""
    return VOCAB_IMG_DIR / item.theme / f"{item.id}.png"
