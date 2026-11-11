from __future__ import annotations

import math
import urllib.parse
from dataclasses import dataclass
from typing import Any

VALID_TOPICS: tuple[str, ...] = ("grid", "count", "add", "sub", "sifir_ref", "sifir", "div")
VALID_LANGUAGES: tuple[str, ...] = ("ms", "en")
VALID_GRID_STARTS: tuple[int, ...] = (1, 101, 201, 301, 401, 501, 601, 701, 801, 901)
VALID_COUNT_MAX: tuple[int, ...] = (5, 10, 20)
VALID_SHAPES: tuple[str, ...] = ("star", "circle", "apple", "fish", "flower")
MIN_SEED: int = 0
MAX_SEED: int = 2147483647

SCALAR_KEYS: frozenset[str] = frozenset(
    {
        "preset",
        "pages",
        "lang",
        "ans",
        "seed",
        "grid_start",
        "grid_blanks",
        "count_max",
        "add_digits",
        "add_regroup",
        "sub_digits",
        "sub_borrow",
        "sifir_n",
        "div_digits",
        "div_rem",
    }
)

PRESETS: dict[str, dict[str, Any]] = {
    "t1": {
        "t": ("grid", "count", "add", "sub"),
        "grid_start": 1,
        "grid_blanks": 30,
        "count_max": 10,
        "count_shapes": ("star", "circle", "apple", "fish", "flower"),
        "add_digits": 1,
        "add_regroup": 0,
        "sub_digits": 1,
        "sub_borrow": 0,
    },
    "t2": {
        "t": ("grid", "add", "sub", "sifir"),
        "grid_start": 101,
        "grid_blanks": 30,
        "add_digits": 2,
        "add_regroup": 1,
        "sub_digits": 2,
        "sub_borrow": 1,
        "sifir_tables": (2, 3, 4, 5, 10),
        "sifir_n": 12,
    },
    "t3": {
        "t": ("add", "sub", "sifir", "div"),
        "add_digits": 3,
        "add_regroup": 1,
        "sub_digits": 3,
        "sub_borrow": 1,
        "sifir_tables": (6, 7, 8, 9),
        "sifir_n": 12,
        "div_digits": 2,
        "div_divisors": (2, 3, 4, 5, 6, 7, 8, 9),
        "div_rem": 0,
    },
}


def expand_preset(name: str) -> dict[str, Any]:
    """Return a dictionary of explicit parameters for the given preset name."""
    if name not in PRESETS:
        raise KeyError(f"Unknown preset: {name}")
    return dict(PRESETS[name])


@dataclass(frozen=True)
class Spec:
    t: tuple[str, ...]
    pages: int = 4
    lang: str = "ms"
    ans: int = 1
    seed: int | None = None
    grid_start: int = 1
    grid_blanks: int = 30
    count_max: int = 10
    count_shapes: tuple[str, ...] = ("star", "circle", "apple", "fish", "flower")
    add_digits: int = 1
    add_regroup: int = 0
    sub_digits: int = 1
    sub_borrow: int = 0
    sifir_tables: tuple[int, ...] = (2, 3, 4, 5)
    sifir_n: int = 12
    div_digits: int = 2
    div_divisors: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8, 9)
    div_rem: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.t, tuple):
            object.__setattr__(self, "t", tuple(self.t))
        if not isinstance(self.count_shapes, tuple):
            object.__setattr__(self, "count_shapes", tuple(self.count_shapes))
        if not isinstance(self.sifir_tables, tuple):
            object.__setattr__(self, "sifir_tables", tuple(self.sifir_tables))
        if not isinstance(self.div_divisors, tuple):
            object.__setattr__(self, "div_divisors", tuple(self.div_divisors))

        # Reset options of unselected topics to canonical defaults
        if "grid" not in self.t:
            object.__setattr__(self, "grid_start", 1)
            object.__setattr__(self, "grid_blanks", 30)
        if "count" not in self.t:
            object.__setattr__(self, "count_max", 10)
            object.__setattr__(self, "count_shapes", ("star", "circle", "apple", "fish", "flower"))
        if "add" not in self.t:
            object.__setattr__(self, "add_digits", 1)
            object.__setattr__(self, "add_regroup", 0)
        if "sub" not in self.t:
            object.__setattr__(self, "sub_digits", 1)
            object.__setattr__(self, "sub_borrow", 0)
        if "sifir_ref" not in self.t and "sifir" not in self.t:
            object.__setattr__(self, "sifir_tables", (2, 3, 4, 5))
        if "sifir" not in self.t:
            object.__setattr__(self, "sifir_n", 12)
        if "div" not in self.t:
            object.__setattr__(self, "div_digits", 2)
            object.__setattr__(self, "div_divisors", (2, 3, 4, 5, 6, 7, 8, 9))
            object.__setattr__(self, "div_rem", 0)

    @property
    def topics(self) -> tuple[str, ...]:
        return self.t


def _normalize_input(data: Any) -> dict[str, list[str]]:
    """Normalize Werkzeug MultiDict, plain dict, or query string to dict[str, list[str]]."""
    if data is None:
        return {}
    if isinstance(data, str):
        query = data.lstrip("?")
        parsed = urllib.parse.parse_qs(query, keep_blank_values=True)
        return {k: list(v) for k, v in parsed.items()}
    if hasattr(data, "getlist") and callable(data.getlist):
        return {k: [str(x) for x in data.getlist(k)] for k in set(data.keys())}
    if isinstance(data, dict):
        result: dict[str, list[str]] = {}
        for k, v in data.items():
            if isinstance(v, (list, tuple)):
                result[k] = [str(x) for x in v]
            else:
                result[k] = [str(v)]
        return result
    return {}


def parse_spec(data: Any) -> tuple[Spec | None, list[tuple[str, str]]]:
    """Parse and validate worksheet spec from multidict, dict, or query string.

    Returns (spec, errors) where errors is a list of (field, message_key) tuples.
    If errors is non-empty, spec is None.
    """
    raw_map = _normalize_input(data)
    errors: list[tuple[str, str]] = []

    # Check for repeated scalar keys
    for key in SCALAR_KEYS:
        if key in raw_map and len(raw_map[key]) > 1:
            errors.append((key, "repeated"))

    # Preset expansion
    preset_dict: dict[str, Any] = {}
    if "preset" in raw_map:
        if len(raw_map["preset"]) == 1:
            preset_name = raw_map["preset"][0].strip()
            if not preset_name:
                errors.append(("preset", "empty"))
            elif preset_name not in PRESETS:
                errors.append(("preset", "invalid_preset"))
            else:
                preset_dict = expand_preset(preset_name)

    # 1. Topics (t)
    resolved_topics: tuple[str, ...] | None = None
    if "t" in raw_map:
        raw_items = raw_map["t"]
        raw_topics: list[str] = []
        for item in raw_items:
            for part in item.split(","):
                raw_topics.append(part.strip())
        if len(raw_topics) == 0:
            errors.append(("t", "empty"))
        else:
            has_topic_error = False
            for topic in raw_topics:
                if topic == "":
                    errors.append(("t", "empty_topic"))
                    has_topic_error = True
                    break
                if topic not in VALID_TOPICS:
                    errors.append(("t", "unknown_topic"))
                    has_topic_error = True
                    break
            if not has_topic_error:
                unique_set = set(raw_topics)
                ordered = tuple(t for t in VALID_TOPICS if t in unique_set)
                if len(ordered) == 0:
                    errors.append(("t", "empty"))
                else:
                    resolved_topics = ordered
    elif "t" in preset_dict:
        resolved_topics = tuple(t for t in VALID_TOPICS if t in preset_dict["t"])
    else:
        errors.append(("t", "required"))

    selected_topics: tuple[str, ...] = resolved_topics if resolved_topics is not None else ()

    # 2. Pages
    pages: int = 4
    pages_valid = True
    if "pages" in raw_map:
        if len(raw_map["pages"]) == 1:
            val_str = raw_map["pages"][0].strip()
            try:
                p_val = int(val_str)
                if p_val < 1 or p_val > 20:
                    errors.append(("pages", "out_of_range"))
                    pages_valid = False
                else:
                    pages = p_val
            except ValueError:
                errors.append(("pages", "invalid_integer"))
                pages_valid = False
        else:
            pages_valid = False
    elif "pages" in preset_dict:
        pages = int(preset_dict["pages"])

    # 3. Lang
    lang: str = "ms"
    if "lang" in raw_map:
        if len(raw_map["lang"]) == 1:
            val_str = raw_map["lang"][0].strip()
            if val_str not in VALID_LANGUAGES:
                errors.append(("lang", "invalid_choice"))
            else:
                lang = val_str
    elif "lang" in preset_dict:
        lang = str(preset_dict["lang"])

    # 4. Ans
    ans: int = 1
    if "ans" in raw_map:
        if len(raw_map["ans"]) == 1:
            val_str = raw_map["ans"][0].strip()
            if val_str in ("0", "1"):
                ans = int(val_str)
            else:
                errors.append(("ans", "invalid_boolean"))
    elif "ans" in preset_dict:
        ans = int(preset_dict["ans"])

    # 5. Seed
    seed: int | None = None
    if "seed" in raw_map:
        if len(raw_map["seed"]) == 1:
            val_str = raw_map["seed"][0].strip()
            if val_str != "":
                try:
                    s_val = int(val_str)
                    if s_val < MIN_SEED or s_val > MAX_SEED:
                        errors.append(("seed", "out_of_range"))
                    else:
                        seed = s_val
                except ValueError:
                    errors.append(("seed", "invalid_integer"))
    elif "seed" in preset_dict and preset_dict["seed"] is not None:
        seed = int(preset_dict["seed"])

    # 6. Grid options
    grid_start: int = 1
    grid_blanks: int = 30
    if "grid" in selected_topics:
        if "grid_start" in raw_map:
            if len(raw_map["grid_start"]) == 1:
                val_str = raw_map["grid_start"][0].strip()
                try:
                    g_val = int(val_str)
                    if g_val not in VALID_GRID_STARTS:
                        errors.append(("grid_start", "out_of_range"))
                    else:
                        grid_start = g_val
                except ValueError:
                    errors.append(("grid_start", "invalid_integer"))
        elif "grid_start" in preset_dict:
            grid_start = int(preset_dict["grid_start"])

        if "grid_blanks" in raw_map:
            if len(raw_map["grid_blanks"]) == 1:
                val_str = raw_map["grid_blanks"][0].strip()
                try:
                    b_val = int(val_str)
                    if b_val < 15 or b_val > 60:
                        errors.append(("grid_blanks", "out_of_range"))
                    else:
                        grid_blanks = b_val
                except ValueError:
                    errors.append(("grid_blanks", "invalid_integer"))
        elif "grid_blanks" in preset_dict:
            grid_blanks = int(preset_dict["grid_blanks"])

    # 6b. Count options
    count_max: int = 10
    count_shapes: tuple[str, ...] = VALID_SHAPES
    if "count" in selected_topics:
        if "count_max" in raw_map:
            if len(raw_map["count_max"]) == 1:
                val_str = raw_map["count_max"][0].strip()
                try:
                    c_val = int(val_str)
                    if c_val not in VALID_COUNT_MAX:
                        errors.append(("count_max", "out_of_range"))
                    else:
                        count_max = c_val
                except ValueError:
                    errors.append(("count_max", "invalid_integer"))
        elif "count_max" in preset_dict:
            count_max = int(preset_dict["count_max"])

        if "count_shapes" in raw_map:
            raw_items = raw_map["count_shapes"]
            parsed_shapes: list[str] = []
            has_error = False
            for item in raw_items:
                for part in item.split(","):
                    p = part.strip()
                    if not p:
                        continue
                    if p not in VALID_SHAPES:
                        errors.append(("count_shapes", "invalid_choice"))
                        has_error = True
                        break
                    parsed_shapes.append(p)
                if has_error:
                    break
            if not has_error:
                unique_set = set(parsed_shapes)
                ordered_shapes = tuple(s for s in VALID_SHAPES if s in unique_set)
                if len(ordered_shapes) == 0:
                    errors.append(("count_shapes", "empty_shapes"))
                else:
                    count_shapes = ordered_shapes
        elif "count_shapes" in preset_dict:
            unique_set = set(preset_dict["count_shapes"])
            count_shapes = tuple(s for s in VALID_SHAPES if s in unique_set)

    # 7. Add options
    add_digits: int = 1
    add_regroup: int = 0
    if "add" in selected_topics:
        if "add_digits" in raw_map:
            if len(raw_map["add_digits"]) == 1:
                val_str = raw_map["add_digits"][0].strip()
                try:
                    d_val = int(val_str)
                    if d_val not in (1, 2, 3):
                        errors.append(("add_digits", "out_of_range"))
                    else:
                        add_digits = d_val
                except ValueError:
                    errors.append(("add_digits", "invalid_integer"))
        elif "add_digits" in preset_dict:
            add_digits = int(preset_dict["add_digits"])

        if "add_regroup" in raw_map:
            if len(raw_map["add_regroup"]) == 1:
                val_str = raw_map["add_regroup"][0].strip()
                if val_str in ("0", "1"):
                    add_regroup = int(val_str)
                else:
                    errors.append(("add_regroup", "invalid_boolean"))
        elif "add_regroup" in preset_dict:
            add_regroup = int(preset_dict["add_regroup"])

    # 8. Sub options
    sub_digits: int = 1
    sub_borrow: int = 0
    if "sub" in selected_topics:
        if "sub_digits" in raw_map:
            if len(raw_map["sub_digits"]) == 1:
                val_str = raw_map["sub_digits"][0].strip()
                try:
                    d_val = int(val_str)
                    if d_val not in (1, 2, 3):
                        errors.append(("sub_digits", "out_of_range"))
                    else:
                        sub_digits = d_val
                except ValueError:
                    errors.append(("sub_digits", "invalid_integer"))
        elif "sub_digits" in preset_dict:
            sub_digits = int(preset_dict["sub_digits"])

        if "sub_borrow" in raw_map:
            if len(raw_map["sub_borrow"]) == 1:
                val_str = raw_map["sub_borrow"][0].strip()
                if val_str in ("0", "1"):
                    sub_borrow = int(val_str)
                else:
                    errors.append(("sub_borrow", "invalid_boolean"))
        elif "sub_borrow" in preset_dict:
            sub_borrow = int(preset_dict["sub_borrow"])

        # Cross-field: sub_borrow=1 requires sub_digits >= 2
        if sub_borrow == 1 and sub_digits < 2:
            errors.append(("sub_borrow", "borrow_requires_two_digits"))

    # 9. Sifir tables (used by sifir_ref and sifir)
    sifir_tables: tuple[int, ...] = (2, 3, 4, 5)
    sifir_tables_valid = True
    if "sifir_ref" in selected_topics or "sifir" in selected_topics:
        if "sifir_tables" in raw_map:
            raw_items = raw_map["sifir_tables"]
            parsed_tables: list[int] = []
            has_error = False
            for item in raw_items:
                for part in item.split(","):
                    p = part.strip()
                    if not p:
                        continue
                    try:
                        val = int(p)
                        if val < 1 or val > 12:
                            errors.append(("sifir_tables", "out_of_range"))
                            has_error = True
                            sifir_tables_valid = False
                            break
                        parsed_tables.append(val)
                    except ValueError:
                        errors.append(("sifir_tables", "invalid_integer"))
                        has_error = True
                        sifir_tables_valid = False
                        break
                if has_error:
                    break
            if not has_error:
                unique_tables = tuple(sorted(set(parsed_tables)))
                if len(unique_tables) == 0:
                    errors.append(("sifir_tables", "empty_tables"))
                    sifir_tables_valid = False
                else:
                    sifir_tables = unique_tables
        elif "sifir_tables" in preset_dict:
            sifir_tables = tuple(sorted(set(preset_dict["sifir_tables"])))

    # 10. Sifir N (questions per sifir practice page)
    sifir_n: int = 12
    if "sifir" in selected_topics:
        capacity = min(24, 12 * len(sifir_tables)) if sifir_tables_valid else 24
        if "sifir_n" in raw_map:
            if len(raw_map["sifir_n"]) == 1:
                val_str = raw_map["sifir_n"][0].strip()
                try:
                    n_val = int(val_str)
                    if n_val < 1 or n_val > capacity:
                        errors.append(("sifir_n", "out_of_range"))
                    else:
                        sifir_n = n_val
                except ValueError:
                    errors.append(("sifir_n", "invalid_integer"))
        elif "sifir_n" in preset_dict:
            sifir_n = int(preset_dict["sifir_n"])
        else:
            sifir_n = min(12, capacity)

    # 11. Div options
    div_digits: int = 2
    div_divisors: tuple[int, ...] = (2, 3, 4, 5, 6, 7, 8, 9)
    div_rem: int = 0
    if "div" in selected_topics:
        if "div_digits" in raw_map:
            if len(raw_map["div_digits"]) == 1:
                val_str = raw_map["div_digits"][0].strip()
                try:
                    d_val = int(val_str)
                    if d_val not in (2, 3):
                        errors.append(("div_digits", "out_of_range"))
                    else:
                        div_digits = d_val
                except ValueError:
                    errors.append(("div_digits", "invalid_integer"))
        elif "div_digits" in preset_dict:
            div_digits = int(preset_dict["div_digits"])

        if "div_divisors" in raw_map:
            raw_items = raw_map["div_divisors"]
            parsed_divs: list[int] = []
            has_error = False
            for item in raw_items:
                for part in item.split(","):
                    p = part.strip()
                    if not p:
                        continue
                    try:
                        val = int(p)
                        if val < 2 or val > 9:
                            errors.append(("div_divisors", "out_of_range"))
                            has_error = True
                            break
                        parsed_divs.append(val)
                    except ValueError:
                        errors.append(("div_divisors", "invalid_integer"))
                        has_error = True
                        break
                if has_error:
                    break
            if not has_error:
                unique_divs = tuple(sorted(set(parsed_divs)))
                if len(unique_divs) == 0:
                    errors.append(("div_divisors", "empty_divisors"))
                else:
                    div_divisors = unique_divs
        elif "div_divisors" in preset_dict:
            div_divisors = tuple(sorted(set(preset_dict["div_divisors"])))

        if "div_rem" in raw_map:
            if len(raw_map["div_rem"]) == 1:
                val_str = raw_map["div_rem"][0].strip()
                if val_str in ("0", "1"):
                    div_rem = int(val_str)
                else:
                    errors.append(("div_rem", "invalid_boolean"))
        elif "div_rem" in preset_dict:
            div_rem = int(preset_dict["div_rem"])

    # 12. Cross-field: pages >= min_pages for selected topics
    if resolved_topics is not None and pages_valid:
        ref_count = math.ceil(len(sifir_tables) / 6) if "sifir_ref" in selected_topics else 0
        practice_count = len([t for t in selected_topics if t != "sifir_ref"])
        min_pages = ref_count + practice_count
        if pages < min_pages:
            errors.append(("pages", "below_minimum"))
        elif practice_count == 0 and pages != ref_count:
            errors.append(("pages", "reference_pages_mismatch"))

    if errors:
        return None, errors

    spec = Spec(
        t=selected_topics,
        pages=pages,
        lang=lang,
        ans=ans,
        seed=seed,
        grid_start=grid_start,
        grid_blanks=grid_blanks,
        count_max=count_max,
        count_shapes=count_shapes,
        add_digits=add_digits,
        add_regroup=add_regroup,
        sub_digits=sub_digits,
        sub_borrow=sub_borrow,
        sifir_tables=sifir_tables,
        sifir_n=sifir_n,
        div_digits=div_digits,
        div_divisors=div_divisors,
        div_rem=div_rem,
    )
    return spec, []


def spec_to_query(spec: Spec) -> str:
    """Serialize a Spec to canonical URL query string, omitting inactive options."""
    params: list[tuple[str, str]] = [
        ("t", ",".join(spec.t)),
        ("pages", str(spec.pages)),
        ("lang", spec.lang),
        ("ans", str(spec.ans)),
    ]
    if spec.seed is not None:
        params.append(("seed", str(spec.seed)))

    if "grid" in spec.t:
        params.append(("grid_start", str(spec.grid_start)))
        params.append(("grid_blanks", str(spec.grid_blanks)))

    if "count" in spec.t:
        params.append(("count_max", str(spec.count_max)))
        params.append(("count_shapes", ",".join(spec.count_shapes)))

    if "add" in spec.t:
        params.append(("add_digits", str(spec.add_digits)))
        params.append(("add_regroup", str(spec.add_regroup)))

    if "sub" in spec.t:
        params.append(("sub_digits", str(spec.sub_digits)))
        params.append(("sub_borrow", str(spec.sub_borrow)))

    if "sifir_ref" in spec.t or "sifir" in spec.t:
        params.append(("sifir_tables", ",".join(str(x) for x in sorted(spec.sifir_tables))))

    if "sifir" in spec.t:
        params.append(("sifir_n", str(spec.sifir_n)))

    if "div" in spec.t:
        params.append(("div_digits", str(spec.div_digits)))
        params.append(("div_divisors", ",".join(str(x) for x in sorted(spec.div_divisors))))
        params.append(("div_rem", str(spec.div_rem)))

    return "&".join(f"{k}={v}" for k, v in params)
