"""Form context preparation and parameter normalization for CetakPintar web UI."""

from __future__ import annotations

import secrets
import urllib.parse
from typing import Any

from werkzeug.datastructures import MultiDict

from modules.i18n import get_error_message, t
from modules.spec import (
    MAX_SEED,
    MIN_SEED,
    PRESETS,
    VALID_ABC_CASES,
    VALID_COUNT_MAX,
    VALID_GRID_STARTS,
    VALID_SHAPES,
    VALID_TOPICS,
    expand_preset,
)
from modules.vocab import THEMES

MATH_TOPICS: tuple[str, ...] = ("grid", "count", "add", "sub", "sifir_ref", "sifir", "div")
ABC_TOPICS: tuple[str, ...] = ("trace", "missing", "match", "first_letter", "guess_word")
VALID_MISSING_BLANKS: tuple[int, ...] = (1, 2, 3)
ALL_SIFIR_TABLES: tuple[int, ...] = tuple(range(1, 13))
ALL_DIVISORS: tuple[int, ...] = tuple(range(2, 10))
THEME_ICONS: dict[str, str] = {
    "animals": "cat",
    "fruits": "apple",
    "vehicles": "car",
    "sports": "tennis",
}


def resolve_seed(raw_seed: Any) -> int:
    """Return a valid integer seed from raw input or generate a cryptographically random one."""
    if raw_seed is not None and str(raw_seed).strip() != "":
        try:
            val = int(str(raw_seed).strip())
            if MIN_SEED <= val <= MAX_SEED:
                return val
        except ValueError:
            pass
    return secrets.randbelow(MAX_SEED + 1)


def build_form_context(
    args: MultiDict | dict[str, Any],
    errors: list[tuple[str, str]] | None = None,
    seed_override: int | None = None,
) -> dict[str, Any]:
    """Build template context dictionary for the index worksheet form.

    Prefills all controls from query parameters or preset, preserves raw inputs
    when errors are present, and provides localized error lookups.
    """
    if isinstance(args, MultiDict):
        raw_map = {k: args.getlist(k) for k in args.keys()}
    else:
        raw_map = {
            k: [str(x) for x in v] if isinstance(v, (list, tuple)) else [str(v)]
            for k, v in args.items()
        }

    # Language
    lang = "ms"
    if "lang" in raw_map and raw_map["lang"]:
        candidate = raw_map["lang"][0].strip().lower()
        if candidate in ("ms", "en"):
            lang = candidate

    # Seed
    raw_seed_present = "seed" in raw_map and bool(raw_map["seed"])
    raw_seed_val = raw_map["seed"][0] if raw_seed_present else None

    if seed_override is not None:
        seed = str(seed_override)
        seed_resolved = seed_override
    elif raw_seed_present and raw_seed_val is not None:
        stripped = raw_seed_val.strip()
        if stripped == "":
            seed_resolved = resolve_seed(None)
            seed = str(seed_resolved)
        else:
            try:
                val = int(stripped)
                if MIN_SEED <= val <= MAX_SEED:
                    seed_resolved = val
                    seed = str(val)
                else:
                    seed_resolved = resolve_seed(None)
                    seed = stripped
            except ValueError:
                seed_resolved = resolve_seed(None)
                seed = stripped
    else:
        seed_resolved = resolve_seed(None)
        seed = str(seed_resolved)

    # Preset expansion
    preset_name = ""
    preset_dict: dict[str, Any] = {}
    if "preset" in raw_map and raw_map["preset"]:
        p_val = raw_map["preset"][0].strip()
        if p_val in PRESETS:
            preset_name = p_val
            preset_dict = expand_preset(p_val)

    # Determine default baseline (preset t1 if completely empty)
    is_empty_request = (
        not raw_map
        or (len(raw_map) == 1 and "lang" in raw_map)
        or (len(raw_map) == 1 and "seed" in raw_map)
        or (len(raw_map) == 2 and "lang" in raw_map and "seed" in raw_map)
    )
    if is_empty_request and not preset_dict:
        preset_dict = expand_preset("t1")
        preset_name = "t1"

    # Selected topics
    selected_topics: list[str] = []
    if "t" in raw_map:
        for item in raw_map["t"]:
            for part in item.split(","):
                cleaned = part.strip()
                if cleaned and cleaned in VALID_TOPICS and cleaned not in selected_topics:
                    selected_topics.append(cleaned)
    elif "t" in preset_dict:
        selected_topics = list(preset_dict["t"])

    # Pages
    pages_raw = (
        raw_map["pages"][0].strip()
        if "pages" in raw_map and raw_map["pages"]
        else str(preset_dict.get("pages", 4))
    )

    # Ans
    ans_raw = (
        raw_map["ans"][0].strip()
        if "ans" in raw_map and raw_map["ans"]
        else str(preset_dict.get("ans", 1))
    )

    # Grid options
    grid_start_raw = (
        raw_map["grid_start"][0].strip()
        if "grid_start" in raw_map and raw_map["grid_start"]
        else str(preset_dict.get("grid_start", 1))
    )
    grid_blanks_raw = (
        raw_map["grid_blanks"][0].strip()
        if "grid_blanks" in raw_map and raw_map["grid_blanks"]
        else str(preset_dict.get("grid_blanks", 30))
    )

    # Count options
    count_max_raw = (
        raw_map["count_max"][0].strip()
        if "count_max" in raw_map and raw_map["count_max"]
        else str(preset_dict.get("count_max", 10))
    )
    count_shapes: list[str] = []
    if "count_shapes" in raw_map:
        for item in raw_map["count_shapes"]:
            for part in item.split(","):
                cleaned = part.strip()
                if cleaned in VALID_SHAPES and cleaned not in count_shapes:
                    count_shapes.append(cleaned)
    elif "count_shapes" in preset_dict:
        count_shapes = list(preset_dict["count_shapes"])
    else:
        count_shapes = list(VALID_SHAPES)

    # Add options
    add_digits_raw = (
        raw_map["add_digits"][0].strip()
        if "add_digits" in raw_map and raw_map["add_digits"]
        else str(preset_dict.get("add_digits", 1))
    )
    add_regroup_raw = (
        raw_map["add_regroup"][0].strip()
        if "add_regroup" in raw_map and raw_map["add_regroup"]
        else str(preset_dict.get("add_regroup", 0))
    )

    # Sub options
    sub_digits_raw = (
        raw_map["sub_digits"][0].strip()
        if "sub_digits" in raw_map and raw_map["sub_digits"]
        else str(preset_dict.get("sub_digits", 1))
    )
    sub_borrow_raw = (
        raw_map["sub_borrow"][0].strip()
        if "sub_borrow" in raw_map and raw_map["sub_borrow"]
        else str(preset_dict.get("sub_borrow", 0))
    )

    # Sifir options
    sifir_tables: list[int] = []
    if "sifir_tables" in raw_map:
        for item in raw_map["sifir_tables"]:
            for part in item.split(","):
                try:
                    num = int(part.strip())
                    if 1 <= num <= 12 and num not in sifir_tables:
                        sifir_tables.append(num)
                except ValueError:
                    pass
    elif "sifir_tables" in preset_dict:
        sifir_tables = list(preset_dict["sifir_tables"])
    else:
        sifir_tables = [2, 3, 4, 5]

    sifir_n_raw = (
        raw_map["sifir_n"][0].strip()
        if "sifir_n" in raw_map and raw_map["sifir_n"]
        else str(preset_dict.get("sifir_n", 12))
    )

    # Div options
    div_digits_raw = (
        raw_map["div_digits"][0].strip()
        if "div_digits" in raw_map and raw_map["div_digits"]
        else str(preset_dict.get("div_digits", 2))
    )
    div_divisors: list[int] = []
    if "div_divisors" in raw_map:
        for item in raw_map["div_divisors"]:
            for part in item.split(","):
                try:
                    num = int(part.strip())
                    if 2 <= num <= 9 and num not in div_divisors:
                        div_divisors.append(num)
                except ValueError:
                    pass
    elif "div_divisors" in preset_dict:
        div_divisors = list(preset_dict["div_divisors"])
    else:
        div_divisors = list(range(2, 10))

    div_rem_raw = (
        raw_map["div_rem"][0].strip()
        if "div_rem" in raw_map and raw_map["div_rem"]
        else str(preset_dict.get("div_rem", 0))
    )

    # Alphabet options
    abc_case_raw = (
        raw_map["abc_case"][0].strip()
        if "abc_case" in raw_map and raw_map["abc_case"]
        else str(preset_dict.get("abc_case", "upper"))
    )
    missing_blanks_raw = (
        raw_map["missing_blanks"][0].strip()
        if "missing_blanks" in raw_map and raw_map["missing_blanks"]
        else str(preset_dict.get("missing_blanks", 1))
    )

    # Picture options
    themes: list[str] = []
    if "themes" in raw_map:
        for item in raw_map["themes"]:
            for part in item.split(","):
                cleaned = part.strip()
                if cleaned in THEMES and cleaned not in themes:
                    themes.append(cleaned)
    elif "themes" in preset_dict:
        themes = list(preset_dict["themes"])
    else:
        themes = list(THEMES)

    guess_hint_raw = (
        raw_map["guess_hint"][0].strip()
        if "guess_hint" in raw_map and raw_map["guess_hint"]
        else str(preset_dict.get("guess_hint", 1))
    )

    # Format errors
    field_errors: dict[str, str] = {}
    error_list: list[dict[str, str]] = []
    if errors:
        for field, msg_key in errors:
            localized_msg = get_error_message(msg_key, lang=lang)
            field_errors[field] = localized_msg
            error_list.append({"field": field, "message": localized_msg})

    def lang_url(target_lang: str) -> str:
        params: list[tuple[str, str]] = [
            ("lang", target_lang),
            ("seed", str(seed_resolved)),
            ("pages", pages_raw),
            ("ans", ans_raw),
        ]
        if selected_topics:
            params.append(("t", ",".join(selected_topics)))
        if "grid" in selected_topics:
            params.append(("grid_start", grid_start_raw))
            params.append(("grid_blanks", grid_blanks_raw))
        if "count" in selected_topics:
            params.append(("count_max", count_max_raw))
            params.append(("count_shapes", ",".join(count_shapes)))
        if "add" in selected_topics:
            params.append(("add_digits", add_digits_raw))
            params.append(("add_regroup", add_regroup_raw))
        if "sub" in selected_topics:
            params.append(("sub_digits", sub_digits_raw))
            params.append(("sub_borrow", sub_borrow_raw))
        if "sifir_ref" in selected_topics or "sifir" in selected_topics:
            params.append(("sifir_tables", ",".join(str(x) for x in sorted(sifir_tables))))
        if "sifir" in selected_topics:
            params.append(("sifir_n", sifir_n_raw))
        if "div" in selected_topics:
            params.append(("div_digits", div_digits_raw))
            params.append(("div_divisors", ",".join(str(x) for x in sorted(div_divisors))))
            params.append(("div_rem", div_rem_raw))
        if "trace" in selected_topics or "missing" in selected_topics:
            params.append(("abc_case", abc_case_raw))
        if "missing" in selected_topics:
            params.append(("missing_blanks", missing_blanks_raw))
        if "first_letter" in selected_topics or "guess_word" in selected_topics:
            params.append(("themes", ",".join(themes)))
        if "guess_word" in selected_topics:
            params.append(("guess_hint", guess_hint_raw))
        query = urllib.parse.urlencode(params)
        return f"/?{query}"

    return {
        "lang": lang,
        "seed": seed,
        "seed_resolved": seed_resolved,
        "preset": preset_name,
        "selected_topics": selected_topics,
        "pages_val": pages_raw,
        "ans_val": ans_raw,
        "grid_start_val": grid_start_raw,
        "grid_blanks_val": grid_blanks_raw,
        "count_max_val": count_max_raw,
        "count_shapes": count_shapes,
        "add_digits_val": add_digits_raw,
        "add_regroup_val": add_regroup_raw,
        "sub_digits_val": sub_digits_raw,
        "sub_borrow_val": sub_borrow_raw,
        "sifir_tables": sifir_tables,
        "sifir_n_val": sifir_n_raw,
        "div_digits_val": div_digits_raw,
        "div_divisors": div_divisors,
        "div_rem_val": div_rem_raw,
        "abc_case_val": abc_case_raw,
        "missing_blanks_val": missing_blanks_raw,
        "themes": themes,
        "guess_hint_val": guess_hint_raw,
        "field_errors": field_errors,
        "error_list": error_list,
        "has_errors": bool(errors),
        "VALID_TOPICS": VALID_TOPICS,
        "MATH_TOPICS": MATH_TOPICS,
        "ABC_TOPICS": ABC_TOPICS,
        "VALID_ABC_CASES": VALID_ABC_CASES,
        "VALID_MISSING_BLANKS": VALID_MISSING_BLANKS,
        "VALID_GRID_STARTS": VALID_GRID_STARTS,
        "VALID_COUNT_MAX": VALID_COUNT_MAX,
        "VALID_SHAPES": VALID_SHAPES,
        "ALL_SIFIR_TABLES": ALL_SIFIR_TABLES,
        "ALL_DIVISORS": ALL_DIVISORS,
        "THEMES": THEMES,
        "THEME_ICONS": THEME_ICONS,
        "t": t,
        "lang_url": lang_url,
    }
