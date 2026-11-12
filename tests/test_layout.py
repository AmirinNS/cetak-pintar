from __future__ import annotations

import io

import pytest
from pypdf import PdfReader

from cetak_pintar import limiter
from modules.layout import cards_per_sheet, plan_sheets, sifir_ref_sheets
from modules.spec import Spec, parse_spec


@pytest.mark.parametrize("pages", [1, 2, 4, 20])
@pytest.mark.parametrize("table_count", [1, 12])
def test_reference_only_web_and_layout(client, pages, table_count):
    limiter.reset()
    params = {
        "t": "sifir_ref", "pages": pages, "seed": 42,
        "sifir_tables": ",".join(str(n) for n in range(1, table_count + 1)),
    }
    response = client.get("/cetak", query_string=params)
    required_pages = (table_count + 5) // 6
    if pages == required_pages:
        assert response.status_code == 200
        spec, errors = parse_spec(params)
        assert errors == []
        assert len(plan_sheets(spec)) == required_pages
        assert len(PdfReader(io.BytesIO(response.data)).pages) == required_pages
    else:
        assert response.status_code == 400
        assert 'id="error-pages"' in response.text


def test_reference_only_layout_guard_remains():
    with pytest.raises(ValueError, match="must match ref count"):
        plan_sheets(Spec(t=("sifir_ref",), pages=4, sifir_tables=(2,)))


def test_worked_example_exact_order():
    """Worked example (pages=4, t=add,sifir_ref,sifir, sifir_tables=2,3).

    sifir_ref takes 1. The remaining 3 go round-robin: add, sifir, add.
    PDF order: add, sifir_ref, sifir, add, then answers for add, sifir, add.
    Exact order is a binding test fixture.
    """
    spec, errors = parse_spec({
        "pages": 4,
        "t": "add,sifir_ref,sifir",
        "sifir_tables": "2,3",
        "ans": 1,
    })
    assert errors == []
    assert spec is not None

    sheets = plan_sheets(spec)
    expected = [
        ("content", "add", 0),
        ("content", "sifir_ref", 0),
        ("content", "sifir", 0),
        ("content", "add", 1),
        ("answer", "add", 0),
        ("answer", "sifir", 0),
        ("answer", "add", 1),
    ]
    assert sheets == expected


def test_worked_example_without_answers():
    spec, errors = parse_spec({
        "pages": 4,
        "t": "add,sifir_ref,sifir",
        "sifir_tables": "2,3",
        "ans": 0,
    })
    assert errors == []
    assert spec is not None

    sheets = plan_sheets(spec)
    expected = [
        ("content", "add", 0),
        ("content", "sifir_ref", 0),
        ("content", "sifir", 0),
        ("content", "add", 1),
    ]
    assert sheets == expected


def test_sifir_ref_pagination():
    # 1 table -> 1 sheet
    assert sifir_ref_sheets(1) == 1
    assert sifir_ref_sheets([2]) == 1

    # 6 tables -> 1 sheet
    assert sifir_ref_sheets(6) == 1
    assert sifir_ref_sheets([1, 2, 3, 4, 5, 6]) == 1

    # 7 tables -> 2 sheets
    assert sifir_ref_sheets(7) == 2
    assert sifir_ref_sheets([1, 2, 3, 4, 5, 6, 7]) == 2

    # 12 tables -> 2 sheets
    assert sifir_ref_sheets(12) == 2
    assert sifir_ref_sheets(list(range(1, 13))) == 2

    # Verification in plan_sheets
    spec_7, _ = parse_spec({
        "pages": 3,
        "t": "sifir_ref,sifir",
        "sifir_tables": "1,2,3,4,5,6,7",
        "ans": 0,
    })
    assert spec_7 is not None
    sheets_7 = plan_sheets(spec_7)
    # 2 ref sheets and 1 practice sheet
    assert sheets_7 == [
        ("content", "sifir_ref", 0),
        ("content", "sifir_ref", 1),
        ("content", "sifir", 0),
    ]

    spec_12, _ = parse_spec({
        "pages": 3,
        "t": "sifir_ref,sifir",
        "sifir_tables": "1,2,3,4,5,6,7,8,9,10,11,12",
        "ans": 0,
    })
    assert spec_12 is not None
    sheets_12 = plan_sheets(spec_12)
    assert sheets_12 == [
        ("content", "sifir_ref", 0),
        ("content", "sifir_ref", 1),
        ("content", "sifir", 0),
    ]


def test_maximum_40_pages():
    # 20 practice content pages with ans=1 produces exactly 40 pages
    spec, errors = parse_spec({"pages": 20, "t": "add", "ans": 1})
    assert errors == []
    assert spec is not None

    sheets = plan_sheets(spec)
    assert len(sheets) == 40
    # First 20 are content
    assert all(k == "content" for k, _, _ in sheets[:20])
    # Next 20 are answers
    assert all(k == "answer" for k, _, _ in sheets[20:])

    # Direct instantiation with pages > 20 raises ValueError in plan_sheets
    spec_invalid = Spec(t=("add",), pages=21, ans=1)
    with pytest.raises(ValueError, match="pages must be between 1 and 20"):
        plan_sheets(spec_invalid)


def test_cards_per_sheet():
    s1 = Spec(
        t=("grid", "count", "add", "sub", "sifir", "div"),
        add_digits=1,
        sub_digits=1,
        div_digits=2,
        sifir_n=15,
    )
    assert cards_per_sheet(s1, "grid") == 1
    assert cards_per_sheet(s1, "count") == 12
    assert cards_per_sheet(s1, "add") == 20
    assert cards_per_sheet(s1, "sub") == 20
    assert cards_per_sheet(s1, "sifir") == 15
    assert cards_per_sheet(s1, "div") == 12

    # 3-digit add, sub, div
    s3 = Spec(t=("add", "sub", "div"), add_digits=3, sub_digits=3, div_digits=3)
    assert cards_per_sheet(s3, "add") == 16
    assert cards_per_sheet(s3, "sub") == 16
    assert cards_per_sheet(s3, "div") == 8


def test_trace_round_robin_without_answers():
    spec, errors = parse_spec({"t": "add,trace", "pages": 4})
    assert errors == []
    assert plan_sheets(spec) == [
        ("content", "add", 0),
        ("content", "trace", 0),
        ("content", "add", 1),
        ("content", "trace", 1),
        ("answer", "add", 0),
        ("answer", "add", 1),
    ]


@pytest.mark.parametrize("ans", [0, 1])
def test_trace_only_uses_all_content_pages(ans):
    spec, errors = parse_spec({"t": "trace", "pages": 20, "ans": ans})
    assert errors == []
    assert plan_sheets(spec) == [("content", "trace", index) for index in range(20)]


def test_alphabet_with_fixed_reference_sheets():
    spec, errors = parse_spec({
        "t": "sifir_ref,trace,missing,match", "pages": 6,
        "sifir_tables": "1,2,3,4,5,6,7",
    })
    assert errors == []
    assert plan_sheets(spec) == [
        ("content", "sifir_ref", 0),
        ("content", "sifir_ref", 1),
        ("content", "trace", 0),
        ("content", "missing", 0),
        ("content", "match", 0),
        ("content", "trace", 1),
        ("answer", "missing", 0),
        ("answer", "match", 0),
    ]


@pytest.mark.parametrize("topic, count", [("trace", 4), ("missing", 12), ("match", 3)])
def test_alphabet_cards_per_sheet(topic, count):
    assert cards_per_sheet(Spec(t=(topic,)), topic) == count
