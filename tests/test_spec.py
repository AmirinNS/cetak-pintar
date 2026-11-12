from __future__ import annotations

import pytest
from werkzeug.datastructures import MultiDict

from modules.spec import (
    PRESETS,
    Spec,
    expand_preset,
    parse_spec,
    spec_to_query,
)


def test_preset_expansion():
    t1 = expand_preset("t1")
    assert t1["t"] == ("grid", "count", "add", "sub")
    assert t1["count_max"] == 10
    assert t1["count_shapes"] == ("star", "circle", "apple", "fish", "flower")
    assert t1["add_digits"] == 1
    assert t1["add_regroup"] == 0
    assert t1["sub_digits"] == 1
    assert t1["sub_borrow"] == 0

    t2 = expand_preset("t2")
    assert t2["t"] == ("grid", "add", "sub", "sifir")
    assert t2["grid_start"] == 101
    assert t2["add_digits"] == 2
    assert t2["add_regroup"] == 1
    assert t2["sub_digits"] == 2
    assert t2["sub_borrow"] == 1
    assert t2["sifir_tables"] == (2, 3, 4, 5, 10)

    t3 = expand_preset("t3")
    assert t3["t"] == ("add", "sub", "sifir", "div")
    assert t3["add_digits"] == 3
    assert t3["add_regroup"] == 1
    assert t3["sub_digits"] == 3
    assert t3["sub_borrow"] == 1
    assert t3["sifir_tables"] == (6, 7, 8, 9)
    assert t3["div_digits"] == 2
    assert t3["div_rem"] == 0

    with pytest.raises(KeyError):
        expand_preset("unknown_preset")


def test_round_trip_presets():
    for name in PRESETS:
        spec, errors = parse_spec({"preset": name})
        assert errors == [], f"Preset {name} had errors: {errors}"
        assert spec is not None
        query = spec_to_query(spec)
        round_trip_spec, round_trip_errors = parse_spec(query)
        assert round_trip_errors == []
        assert round_trip_spec == spec


def test_round_trip_various_specs():
    specs = [
        Spec(t=("grid",), pages=2, seed=12345, grid_start=201, grid_blanks=45),
        Spec(
            t=("add", "sub"),
            pages=5,
            lang="en",
            ans=0,
            seed=0,
            add_digits=2,
            add_regroup=1,
            sub_digits=2,
            sub_borrow=1,
        ),
        Spec(t=("sifir_ref", "sifir"), pages=6, sifir_tables=(2, 3, 5, 7), sifir_n=15),
        Spec(t=("div",), pages=4, div_digits=3, div_divisors=(3, 4, 5), div_rem=1),
        Spec(
            t=("count",),
            pages=2,
            count_max=5,
            count_shapes=("apple", "fish"),
        ),
        Spec(
            t=("grid", "count", "add", "sub", "sifir_ref", "sifir", "div"),
            pages=10,
            seed=2147483647,
        ),
    ]
    for s in specs:
        q = spec_to_query(s)
        parsed, errors = parse_spec(q)
        assert errors == [], f"Errors for {s}: {errors}"
        assert parsed == s


def test_input_formats():
    # MultiDict
    md = MultiDict([("t", "add"), ("t", "sub"), ("pages", "4"), ("add_digits", "2")])
    spec1, err1 = parse_spec(md)
    assert err1 == []
    assert spec1 is not None
    assert spec1.t == ("add", "sub")
    assert spec1.pages == 4
    assert spec1.add_digits == 2

    # Plain dict of lists
    d_lists = {"t": ["add", "sub"], "pages": ["4"], "add_digits": ["2"]}
    spec2, err2 = parse_spec(d_lists)
    assert err2 == []
    assert spec2 == spec1

    # Plain dict of scalar values
    d_scalars = {"t": "add,sub", "pages": 4, "add_digits": 2}
    spec3, err3 = parse_spec(d_scalars)
    assert err3 == []
    assert spec3 == spec1

    # Query string
    qs = "t=add,sub&pages=4&add_digits=2"
    spec4, err4 = parse_spec(qs)
    assert err4 == []
    assert spec4 == spec1


def test_seed_handling():
    # Absent seed
    spec, err = parse_spec({"t": "grid"})
    assert err == []
    assert spec is not None
    assert spec.seed is None

    # Blank seed
    spec, err = parse_spec({"t": "grid", "seed": ""})
    assert err == []
    assert spec is not None
    assert spec.seed is None

    # Seed 0
    spec, err = parse_spec({"t": "grid", "seed": "0"})
    assert err == []
    assert spec is not None
    assert spec.seed == 0

    # Seed 2147483647 (max 31-bit signed int)
    spec, err = parse_spec({"t": "grid", "seed": "2147483647"})
    assert err == []
    assert spec is not None
    assert spec.seed == 2147483647

    # Seed negative
    spec, err = parse_spec({"t": "grid", "seed": "-1"})
    assert any(f == "seed" for f, _ in err)
    assert spec is None

    # Seed 2147483648
    spec, err = parse_spec({"t": "grid", "seed": "2147483648"})
    assert any(f == "seed" for f, _ in err)
    assert spec is None

    # Huge numeric string
    spec, err = parse_spec({"t": "grid", "seed": "999999999999999999999999999999"})
    assert any(f == "seed" for f, _ in err)
    assert spec is None

    # Non-integer seed
    spec, err = parse_spec({"t": "grid", "seed": "abc"})
    assert any(f == "seed" for f, _ in err)
    assert spec is None


def test_topics_validation():
    # Missing topic
    spec, err = parse_spec({})
    assert any(f == "t" for f, _ in err)
    assert spec is None

    # Empty topic
    spec, err = parse_spec({"t": ""})
    assert any(f == "t" for f, _ in err)
    assert spec is None

    # Empty item in comma-separated topic
    spec, err = parse_spec({"t": "add,"})
    assert any(f == "t" for f, _ in err)
    assert spec is None

    # Unknown topic
    spec, err = parse_spec({"t": "unknown_topic"})
    assert any(f == "t" for f, _ in err)
    assert spec is None

    # Duplicate topic collapses without error
    spec, err = parse_spec({"t": "add,add"})
    assert err == []
    assert spec is not None
    assert spec.t == ("add",)

    # MultiDict repeated key collapses without error
    md = MultiDict([("t", "sub"), ("t", "add"), ("t", "sub")])
    spec, err = parse_spec(md)
    assert err == []
    assert spec is not None
    assert spec.t == ("add", "sub")  # canonical order preserved


def test_repeated_scalar_keys():
    md = MultiDict([("t", "add"), ("pages", "4"), ("pages", "5")])
    spec, err = parse_spec(md)
    assert any(f == "pages" and m == "repeated" for f, m in err)
    assert spec is None

    md = MultiDict([("t", "add"), ("lang", "ms"), ("lang", "en")])
    _, err = parse_spec(md)
    assert any(f == "lang" and m == "repeated" for f, m in err)

    md = MultiDict([("t", "add"), ("ans", "0"), ("ans", "1")])
    _, err = parse_spec(md)
    assert any(f == "ans" and m == "repeated" for f, m in err)

    md = MultiDict([("t", "add"), ("seed", "123"), ("seed", "456")])
    _, err = parse_spec(md)
    assert any(f == "seed" and m == "repeated" for f, m in err)

    md = MultiDict([("t", "add"), ("add_digits", "1"), ("add_digits", "2")])
    _, err = parse_spec(md)
    assert any(f == "add_digits" and m == "repeated" for f, m in err)


def test_invalid_booleans_and_language():
    # Invalid lang
    _, err = parse_spec({"t": "add", "lang": "fr"})
    assert any(f == "lang" for f, _ in err)

    # Invalid ans
    _, err = parse_spec({"t": "add", "ans": "2"})
    assert any(f == "ans" for f, _ in err)

    _, err = parse_spec({"t": "add", "ans": "true"})
    assert any(f == "ans" for f, _ in err)

    # Invalid add_regroup
    _, err = parse_spec({"t": "add", "add_regroup": "2"})
    assert any(f == "add_regroup" for f, _ in err)

    # Invalid sub_borrow
    _, err = parse_spec({"t": "sub", "sub_digits": 2, "sub_borrow": "yes"})
    assert any(f == "sub_borrow" for f, _ in err)

    # Invalid div_rem
    _, err = parse_spec({"t": "div", "div_rem": "-1"})
    assert any(f == "div_rem" for f, _ in err)


def test_empty_lists():
    # Empty sifir_tables
    _, err = parse_spec({"t": "sifir", "sifir_tables": ""})
    assert any(f == "sifir_tables" for f, _ in err)

    # Empty div_divisors
    _, err = parse_spec({"t": "div", "div_divisors": ""})
    assert any(f == "div_divisors" for f, _ in err)


def test_out_of_range_values():
    # Pages: 1..20
    _, err = parse_spec({"t": "add", "pages": 0})
    assert any(f == "pages" for f, _ in err)

    _, err = parse_spec({"t": "add", "pages": 21})
    assert any(f == "pages" for f, _ in err)

    # Grid start: 1, 101, 201, ..., 901
    _, err = parse_spec({"t": "grid", "grid_start": 50})
    assert any(f == "grid_start" for f, _ in err)

    # Grid blanks: 15..60
    _, err = parse_spec({"t": "grid", "grid_blanks": 14})
    assert any(f == "grid_blanks" for f, _ in err)
    _, err = parse_spec({"t": "grid", "grid_blanks": 61})
    assert any(f == "grid_blanks" for f, _ in err)

    # Add digits: 1, 2, 3
    _, err = parse_spec({"t": "add", "add_digits": 4})
    assert any(f == "add_digits" for f, _ in err)

    # Sub digits: 1, 2, 3
    _, err = parse_spec({"t": "sub", "sub_digits": 0})
    assert any(f == "sub_digits" for f, _ in err)

    # Div digits: 2, 3
    _, err = parse_spec({"t": "div", "div_digits": 1})
    assert any(f == "div_digits" for f, _ in err)

    # Sifir tables: 1..12
    _, err = parse_spec({"t": "sifir", "sifir_tables": "0,5"})
    assert any(f == "sifir_tables" for f, _ in err)
    _, err = parse_spec({"t": "sifir", "sifir_tables": "13"})
    assert any(f == "sifir_tables" for f, _ in err)

    # Div divisors: 2..9
    _, err = parse_spec({"t": "div", "div_divisors": "1,3"})
    assert any(f == "div_divisors" for f, _ in err)
    _, err = parse_spec({"t": "div", "div_divisors": "10"})
    assert any(f == "div_divisors" for f, _ in err)


def test_cross_field_rules():
    # sub_borrow=1 with sub_digits=1 rejected
    _, err = parse_spec({"t": "sub", "sub_digits": 1, "sub_borrow": 1})
    assert any(f == "sub_borrow" for f, _ in err)

    # sub_borrow=1 with sub_digits=2 accepted
    spec, err = parse_spec({"t": "sub", "sub_digits": 2, "sub_borrow": 1})
    assert err == []
    assert spec is not None
    assert spec.sub_borrow == 1
    assert spec.sub_digits == 2

    # sifir_n capacity: 1 table has capacity min(24, 12*1) = 12
    _, err = parse_spec({"t": "sifir", "sifir_tables": "2", "sifir_n": 13})
    assert any(f == "sifir_n" for f, _ in err)

    spec, err = parse_spec({"t": "sifir", "sifir_tables": "2", "sifir_n": 12})
    assert err == []
    assert spec is not None

    # sifir_n capacity: 2 tables has capacity 24
    _, err = parse_spec({"t": "sifir", "sifir_tables": "2,3", "sifir_n": 25})
    assert any(f == "sifir_n" for f, _ in err)

    spec, err = parse_spec({"t": "sifir", "sifir_tables": "2,3", "sifir_n": 24})
    assert err == []
    assert spec is not None

    # pages below minimum rejected:
    # 5 practice topics + sifir_ref (1 sheet) requires min 6 pages
    _, err = parse_spec({"t": "grid,add,sub,sifir_ref,sifir,div", "pages": 5})
    assert any(f == "pages" and m == "below_minimum" for f, m in err)

    spec, err = parse_spec({"t": "grid,add,sub,sifir_ref,sifir,div", "pages": 6})
    assert err == []
    assert spec is not None


@pytest.mark.parametrize("pages", [1, 2, 4, 20])
@pytest.mark.parametrize("table_count", [1, 12])
def test_reference_only_page_budget(pages, table_count):
    tables = ",".join(str(n) for n in range(1, table_count + 1))
    spec, errors = parse_spec({"t": "sifir_ref", "pages": pages, "sifir_tables": tables})
    required_pages = (table_count + 5) // 6
    if pages == required_pages:
        assert errors == []
        assert spec is not None
    else:
        assert spec is None
        expected = "below_minimum" if pages < required_pages else "reference_pages_mismatch"
        assert errors == [("pages", expected)]


def test_preset_override_and_inactive_options():
    # Preset then override
    spec, err = parse_spec({"preset": "t1", "add_regroup": 1, "pages": 5})
    assert err == []
    assert spec is not None
    assert spec.t == ("grid", "count", "add", "sub")
    assert spec.add_regroup == 1
    assert spec.pages == 5

    # Override topics from preset
    spec, err = parse_spec({"preset": "t2", "t": "add"})
    assert err == []
    assert spec is not None
    assert spec.t == ("add",)
    # Inactive options dropped and reset to canonical defaults
    assert spec.grid_start == 1
    assert spec.sifir_tables == (2, 3, 4, 5)

    # Inactive options with invalid values are ignored and do not produce errors
    spec, err = parse_spec({
        "t": "add",
        "grid_start": 9999,  # invalid if grid were active
        "div_digits": 99,    # invalid if div were active
        "sifir_n": 999,      # invalid if sifir were active
    })
    assert err == []
    assert spec is not None
    assert spec.t == ("add",)

    # Canonical query drops inactive options
    q = spec_to_query(spec)
    assert "grid_start" not in q
    assert "count_max" not in q
    assert "count_shapes" not in q
    assert "div_digits" not in q
    assert "sifir_n" not in q
    assert "add_digits" in q


def test_count_validation():
    # Valid count options
    for c_max in (5, 10, 20):
        spec, err = parse_spec({"t": "count", "count_max": str(c_max), "pages": 1})
        assert err == []
        assert spec is not None
        assert spec.count_max == c_max
        assert spec.count_shapes == ("star", "circle", "apple", "fish", "flower")

    # Invalid count_max
    for bad_max in (0, 1, 15, 25, -5):
        _, err = parse_spec({"t": "count", "count_max": str(bad_max), "pages": 1})
        assert any(f == "count_max" and m == "out_of_range" for f, m in err)

    _, err = parse_spec({"t": "count", "count_max": "ten", "pages": 1})
    assert any(f == "count_max" and m == "invalid_integer" for f, m in err)

    # Repeated count_max
    md = MultiDict([("t", "count"), ("count_max", "5"), ("count_max", "10"), ("pages", "1")])
    _, err = parse_spec(md)
    assert any(f == "count_max" and m == "repeated" for f, m in err)

    # Valid shapes subset stored in canonical order
    spec, err = parse_spec({"t": "count", "count_shapes": "flower,star,circle", "pages": 1})
    assert err == []
    assert spec is not None
    assert spec.count_shapes == ("star", "circle", "flower")

    # Duplicate shapes collapse
    spec, err = parse_spec({"t": "count", "count_shapes": "apple,apple,fish", "pages": 1})
    assert err == []
    assert spec is not None
    assert spec.count_shapes == ("apple", "fish")

    # Invalid shape choice
    _, err = parse_spec({"t": "count", "count_shapes": "star,triangle", "pages": 1})
    assert any(f == "count_shapes" and m == "invalid_choice" for f, m in err)

    # Empty shapes
    _, err = parse_spec({"t": "count", "count_shapes": "", "pages": 1})
    assert any(f == "count_shapes" and m == "empty_shapes" for f, m in err)

    # Round trip with count
    spec_full, err = parse_spec({
        "t": "count,add",
        "count_max": 20,
        "count_shapes": "fish,apple",
        "pages": 2,
    })
    assert err == []
    assert spec_full is not None
    query = spec_to_query(spec_full)
    rt_spec, rt_err = parse_spec(query)
    assert rt_err == []
    assert rt_spec == spec_full


def test_alphabet_topics_in_canonical_order():
    spec, errors = parse_spec({
        "t": "match,missing,trace,div,sifir,add,count,grid,sub,sifir_ref,trace",
        "pages": 10,
    })
    assert errors == []
    assert spec.t == (
        "grid", "count", "add", "sub", "sifir_ref", "sifir", "div",
        "trace", "missing", "match",
    )


def test_abc_preset_expansion_and_overrides():
    assert expand_preset("abc") == {
        "t": ("trace", "missing", "match"),
        "abc_case": "upper",
        "missing_blanks": 1,
    }
    spec, errors = parse_spec({"preset": "abc"})
    assert errors == []
    assert spec.t == ("trace", "missing", "match")
    assert spec.abc_case == "upper"
    assert spec.missing_blanks == 1

    spec, errors = parse_spec({
        "preset": "abc", "t": "missing", "abc_case": "lower", "missing_blanks": 3,
    })
    assert errors == []
    assert spec.t == ("missing",)
    assert spec.abc_case == "lower"
    assert spec.missing_blanks == 3


@pytest.mark.parametrize("topics", ["trace", "missing", "trace,missing"])
@pytest.mark.parametrize("case", ["upper", "lower"])
def test_abc_case_valid(topics, case):
    spec, errors = parse_spec({"t": topics, "abc_case": case})
    assert errors == []
    assert spec.abc_case == case


@pytest.mark.parametrize("case", ["", "UPPER", "mixed"])
def test_abc_case_invalid(case):
    spec, errors = parse_spec({"t": "trace", "abc_case": case})
    assert spec is None
    assert errors == [("abc_case", "invalid_choice")]


@pytest.mark.parametrize("blanks", [1, 2, 3])
def test_missing_blanks_valid(blanks):
    spec, errors = parse_spec({"t": "missing", "missing_blanks": blanks})
    assert errors == []
    assert spec.missing_blanks == blanks


@pytest.mark.parametrize("value, message", [
    (0, "out_of_range"), (4, "out_of_range"), (-1, "out_of_range"),
    ("", "invalid_integer"), ("two", "invalid_integer"), ("1.5", "invalid_integer"),
])
def test_missing_blanks_invalid(value, message):
    spec, errors = parse_spec({"t": "missing", "missing_blanks": value})
    assert spec is None
    assert errors == [("missing_blanks", message)]


@pytest.mark.parametrize("topics", ["missing", "add"])
@pytest.mark.parametrize("field, values", [
    ("abc_case", ["upper", "lower"]), ("missing_blanks", ["1", "2"]),
])
def test_alphabet_repeated_scalars(topics, field, values):
    spec, errors = parse_spec({"t": topics, field: values})
    assert spec is None
    assert errors == [(field, "repeated")]


@pytest.mark.parametrize("topics", [("add",), ("match",), ("trace",), ("missing",)])
def test_alphabet_inactive_options_reset_and_drop(topics):
    spec = Spec(t=topics, abc_case="lower", missing_blanks=3)
    uses_case = "trace" in topics or "missing" in topics
    assert spec.abc_case == ("lower" if uses_case else "upper")
    assert spec.missing_blanks == (3 if "missing" in topics else 1)
    query = spec_to_query(spec)
    assert ("abc_case=" in query) == uses_case
    assert ("missing_blanks=" in query) == ("missing" in topics)
    assert parse_spec(query) == (spec, [])


def test_inactive_alphabet_invalid_values_ignored():
    spec, errors = parse_spec({
        "t": "match", "abc_case": "mixed", "missing_blanks": "many",
    })
    assert errors == []
    assert spec.abc_case == "upper"
    assert spec.missing_blanks == 1
    spec, errors = parse_spec({"t": "trace", "missing_blanks": "many"})
    assert errors == []
    assert spec.missing_blanks == 1


@pytest.mark.parametrize("case", ["upper", "lower"])
@pytest.mark.parametrize("blanks", [1, 2, 3])
def test_alphabet_round_trip(case, blanks):
    spec = Spec(
        t=("add", "trace", "missing", "match"), pages=7, lang="en", ans=0,
        seed=42, add_digits=2, abc_case=case, missing_blanks=blanks,
    )
    assert parse_spec(spec_to_query(spec)) == (spec, [])


def test_existing_math_query_unchanged():
    spec, errors = parse_spec("preset=t1&seed=42")
    assert errors == []
    assert spec_to_query(spec) == (
        "t=grid,count,add,sub&pages=4&lang=ms&ans=1&seed=42"
        "&grid_start=1&grid_blanks=30&count_max=10"
        "&count_shapes=star,circle,apple,fish,flower"
        "&add_digits=1&add_regroup=0&sub_digits=1&sub_borrow=0"
    )
