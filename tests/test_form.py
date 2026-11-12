"""Tests for form rendering, HTML controls, progressive enhancement, and error attributes."""

from __future__ import annotations

import urllib.parse
from html.parser import HTMLParser

from flask.testing import FlaskClient

from modules.i18n import t


class FormParser(HTMLParser):
    """Parse HTML form controls and attributes using the standard library."""

    def __init__(self) -> None:
        super().__init__()
        self.inputs: list[dict[str, str]] = []
        self.selects: list[dict[str, str]] = []
        self.select_options: dict[str, list[dict[str, str]]] = {}
        self.links: list[dict[str, str]] = []
        self.elements_with_id: dict[str, dict[str, str]] = {}
        self._current_select: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k: v or "" for k, v in attrs}
        if "id" in attr_dict:
            self.elements_with_id[attr_dict["id"]] = attr_dict

        if tag == "input":
            self.inputs.append(attr_dict)
        elif tag == "select":
            name = attr_dict.get("name", "")
            self._current_select = name
            self.selects.append(attr_dict)
            self.select_options[name] = []
        elif tag == "option" and self._current_select is not None:
            self.select_options[self._current_select].append(attr_dict)
        elif tag == "a":
            self.links.append(attr_dict)

    def handle_endtag(self, tag: str) -> None:
        if tag == "select":
            self._current_select = None

    def get_input(self, input_id: str) -> dict[str, str] | None:
        for inp in self.inputs:
            if inp.get("id") == input_id:
                return inp
        return None

    def get_inputs_by_name(self, name: str) -> list[dict[str, str]]:
        return [inp for inp in self.inputs if inp.get("name") == name]


def parse_html(html_str: str) -> FormParser:
    parser = FormParser()
    parser.feed(html_str)
    return parser


def test_baseline_html_division_controls_enabled(client: FlaskClient) -> None:
    """In baseline HTML (JS disabled), division controls arrive enabled and without d-none."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    parser = parse_html(html)

    # Fieldset does not have d-none in baseline server HTML
    fieldset_div = parser.elements_with_id.get("group-topic-div")
    assert fieldset_div is not None
    classes = fieldset_div.get("class", "").split()
    assert "d-none" not in classes

    # Division select and inputs are enabled (do not have disabled attribute)
    div_digits = [s for s in parser.selects if s.get("name") == "div_digits"]
    assert len(div_digits) == 1
    assert "disabled" not in div_digits[0]

    div_rem = [s for s in parser.selects if s.get("name") == "div_rem"]
    assert len(div_rem) == 1
    assert "disabled" not in div_rem[0]

    div_divisors = parser.get_inputs_by_name("div_divisors")
    # 1 sentinel + 8 checkboxes (divisors 2-9)
    assert len(div_divisors) == 9
    for inp in div_divisors:
        assert "disabled" not in inp

    # Selecting Division without JS and submitting returns 200 with valid PDF
    # Simulate selecting topic 'div'
    query_params: list[tuple[str, str]] = [
        ("t", "div"),
        ("pages", "2"),
        ("ans", "1"),
        ("seed", "555"),
        ("div_digits", "3"),
        ("div_rem", "1"),
    ]
    for d in (2, 3, 4, 5):
        query_params.append(("div_divisors", str(d)))

    sub_resp = client.get(f"/cetak?{urllib.parse.urlencode(query_params)}")
    assert sub_resp.status_code == 200
    assert sub_resp.headers["Content-Type"] == "application/pdf"
    assert sub_resp.data.startswith(b"%PDF")


def test_single_named_seed_control(client: FlaskClient) -> None:
    """Only one named seed control exists and it directly submits the seed value."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    parser = parse_html(html)

    seed_inputs = parser.get_inputs_by_name("seed")
    assert len(seed_inputs) == 1
    seed_input = seed_inputs[0]
    assert seed_input.get("id") == "input-seed"
    assert seed_input.get("type") == "text"
    assert seed_input.get("value", "").isdigit()


def test_language_links_preserve_seed_and_normalized_settings(client: FlaskClient) -> None:
    """Language switcher links keep the resolved seed and every normalized setting except lang."""
    # 1. Initial seedless visit to /
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    parser = parse_html(html)

    seed_val = parser.get_input("input-seed")["value"]
    assert seed_val.isdigit()

    # Find the English link
    en_links = [link for link in parser.links if link.get("data-lang") == "en"]
    assert len(en_links) == 1
    href_en = en_links[0]["href"]
    assert href_en.startswith("/?")

    parsed_url = urllib.parse.urlparse(href_en)
    qs = urllib.parse.parse_qs(parsed_url.query)

    assert qs.get("lang") == ["en"]
    assert qs.get("seed") == [seed_val]
    assert qs.get("pages") == ["4"]
    assert qs.get("ans") == ["1"]
    assert "t" in qs
    assert "grid" in qs["t"][0]
    assert "count" in qs["t"][0]
    assert "add" in qs["t"][0]
    assert "sub" in qs["t"][0]

    # Follow the English link: questions and settings survive
    resp_en = client.get(href_en)
    assert resp_en.status_code == 200
    html_en = resp_en.data.decode("utf-8")
    parser_en = parse_html(html_en)

    assert parser_en.get_input("input-seed")["value"] == seed_val
    assert '<html lang="en">' in html_en

    # 2. Custom edited form: /?t=div&div_digits=3&div_rem=1&seed=998877&pages=2
    custom_query = "t=div&div_digits=3&div_rem=1&seed=998877&pages=2"
    resp_custom = client.get(f"/?{custom_query}")
    assert resp_custom.status_code == 200
    html_custom = resp_custom.data.decode("utf-8")
    parser_custom = parse_html(html_custom)

    en_link_custom = [
        link for link in parser_custom.links if link.get("data-lang") == "en"
    ][0]["href"]
    qs_custom = urllib.parse.parse_qs(urllib.parse.urlparse(en_link_custom).query)

    assert qs_custom.get("lang") == ["en"]
    assert qs_custom.get("seed") == ["998877"]
    assert qs_custom.get("pages") == ["2"]
    assert qs_custom.get("t") == ["div"]
    assert qs_custom.get("div_digits") == ["3"]
    assert qs_custom.get("div_rem") == ["1"]


def test_invalid_seed_remains_visible_with_error(client: FlaskClient) -> None:
    """Invalid submitted seed stays in the visible control with its error message."""
    # Malformed non-integer seed
    resp_bad = client.get("/cetak?t=add&seed=bad&lang=en")
    assert resp_bad.status_code == 400
    html_bad = resp_bad.data.decode("utf-8")
    parser_bad = parse_html(html_bad)

    seed_inp_bad = parser_bad.get_input("input-seed")
    assert seed_inp_bad is not None
    assert seed_inp_bad.get("value") == "bad"
    assert seed_inp_bad.get("aria-invalid") == "true"
    assert seed_inp_bad.get("aria-describedby") == "error-seed"
    assert "Please enter a valid integer." in html_bad

    # Out of range negative seed
    resp_neg = client.get("/cetak?t=add&seed=-5&lang=ms")
    assert resp_neg.status_code == 400
    html_neg = resp_neg.data.decode("utf-8")
    parser_neg = parse_html(html_neg)
    assert parser_neg.get_input("input-seed").get("value") == "-5"
    assert "Nilai di luar julat yang dibenarkan." in html_neg

    # Out of range large seed
    resp_large = client.get("/cetak?t=add&seed=9999999999&lang=en")
    assert resp_large.status_code == 400
    html_large = resp_large.data.decode("utf-8")
    parser_large = parse_html(html_large)
    assert parser_large.get_input("input-seed").get("value") == "9999999999"
    assert "Value is out of the allowed range." in html_large


def test_all_unchecked_groups_produce_errors(client: FlaskClient) -> None:
    """All-unchecked groups produce field errors via submit and share links."""
    # 1. Unchecked shapes with topic count
    # Direct submit via sentinel (empty value)
    resp_shapes_submit = client.get("/cetak?t=count&count_shapes=&seed=42")
    assert resp_shapes_submit.status_code == 400
    html_shapes = resp_shapes_submit.data.decode("utf-8")
    assert (
        "error_empty_shapes" in html_shapes
        or "Sila pilih sekurang-kurangnya satu bentuk." in html_shapes
    )
    parser_shapes = parse_html(html_shapes)
    shape_boxes = [
        inp for inp in parser_shapes.get_inputs_by_name("count_shapes")
        if inp.get("type") == "checkbox"
    ]
    for box in shape_boxes:
        assert "checked" not in box

    # 2. Unchecked sifir tables with topic sifir
    # Direct submit via sentinel (empty value)
    resp_tables_submit = client.get("/cetak?t=sifir&sifir_tables=&seed=42")
    assert resp_tables_submit.status_code == 400
    html_tables = resp_tables_submit.data.decode("utf-8")
    assert "Sila pilih sekurang-kurangnya satu sifir." in html_tables
    parser_tables = parse_html(html_tables)
    table_boxes = [
        inp for inp in parser_tables.get_inputs_by_name("sifir_tables")
        if inp.get("type") == "checkbox"
    ]
    for box in table_boxes:
        assert "checked" not in box

    # 3. Unchecked divisors with topic div
    # Direct submit via sentinel (empty value)
    resp_div_submit = client.get("/cetak?t=div&div_divisors=&seed=42")
    assert resp_div_submit.status_code == 400
    html_div = resp_div_submit.data.decode("utf-8")
    assert "Sila pilih sekurang-kurangnya satu pembahagi." in html_div
    parser_div = parse_html(html_div)
    div_boxes = [
        inp for inp in parser_div.get_inputs_by_name("div_divisors")
        if inp.get("type") == "checkbox"
    ]
    for box in div_boxes:
        assert "checked" not in box


def test_error_attributes_on_tables_and_divisors(client: FlaskClient) -> None:
    """Table and divisor controls receive aria-invalid and aria-describedby on validation errors."""
    # Sifir tables error
    resp_tables = client.get("/cetak?t=sifir&sifir_tables=&seed=42")
    assert resp_tables.status_code == 400
    html_tables = resp_tables.data.decode("utf-8")
    parser_tables = parse_html(html_tables)
    table_checkboxes = [
        inp for inp in parser_tables.get_inputs_by_name("sifir_tables")
        if inp.get("type") == "checkbox"
    ]
    assert len(table_checkboxes) == 12
    for box in table_checkboxes:
        assert box.get("aria-invalid") == "true"
        assert box.get("aria-describedby") == "error-sifir_tables"

    # Divisor error
    resp_div = client.get("/cetak?t=div&div_divisors=&seed=42")
    assert resp_div.status_code == 400
    html_div = resp_div.data.decode("utf-8")
    parser_div = parse_html(html_div)
    div_checkboxes = [
        inp for inp in parser_div.get_inputs_by_name("div_divisors")
        if inp.get("type") == "checkbox"
    ]
    assert len(div_checkboxes) == 8
    for box in div_checkboxes:
        assert box.get("aria-invalid") == "true"
        assert box.get("aria-describedby") == "error-div_divisors"


def test_error_summary_targets_exist(client: FlaskClient) -> None:
    """Error summary link targets like #field-preset and #field-lang exist in the DOM."""
    resp = client.get("/")
    assert resp.status_code == 200
    parser = parse_html(resp.data.decode("utf-8"))

    assert "field-preset" in parser.elements_with_id
    assert "field-lang" in parser.elements_with_id


def test_i18n_ref_pages_mismatch_message() -> None:
    """ref_pages_mismatch key is defined in ms and en."""
    ms_msg = t("ref_pages_mismatch", lang="ms")
    assert ms_msg == (
        "Halaman mesti sama dengan bilangan helaian jadual sifir apabila hanya jadual dipilih."
    )

    en_msg = t("ref_pages_mismatch", lang="en")
    assert en_msg == (
        "Pages must equal the number of sifir table sheets when only tables are selected."
    )

    # Also lookup via error prefix
    err_ms = t("error_ref_pages_mismatch", lang="ms")
    assert err_ms == ms_msg
    err_en = t("error_ref_pages_mismatch", lang="en")
    assert err_en == en_msg


def test_alphabet_options_rendered_form_controls(client: FlaskClient) -> None:
    """The rendered form with trace and missing checked has exactly one enabled abc_case control."""
    resp = client.get("/?t=trace,missing&seed=1")
    assert resp.status_code == 200
    parser = parse_html(resp.data.decode("utf-8"))

    # Exactly one enabled abc_case select control
    abc_case_selects = [s for s in parser.selects if s.get("name") == "abc_case"]
    assert len(abc_case_selects) == 1
    assert "disabled" not in abc_case_selects[0]

    # Exactly one enabled missing_blanks select control
    missing_selects = [s for s in parser.selects if s.get("name") == "missing_blanks"]
    assert len(missing_selects) == 1
    assert "disabled" not in missing_selects[0]


def test_preset_abc_prechecks_topics(client: FlaskClient) -> None:
    """preset=abc pre-checks the alphabet and picture topics in the form."""
    resp = client.get("/?preset=abc")
    assert resp.status_code == 200
    parser = parse_html(resp.data.decode("utf-8"))

    topic_checkboxes = [inp for inp in parser.inputs if inp.get("name") == "t"]
    checked_topics = {inp.get("value") for inp in topic_checkboxes if "checked" in inp}
    assert checked_topics == {"trace", "missing", "match", "first_letter"}


def test_baseline_html_picture_theme_controls_enabled(client: FlaskClient) -> None:
    """In baseline HTML (JS disabled), picture themes and guess_hint arrive enabled."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    parser = parse_html(html)

    fieldset_themes = parser.elements_with_id.get("group-topic-themes")
    assert fieldset_themes is not None
    classes = fieldset_themes.get("class", "").split()
    assert "d-none" not in classes

    # 1 sentinel + 4 checkboxes
    theme_inputs = parser.get_inputs_by_name("themes")
    assert len(theme_inputs) == 5
    for inp in theme_inputs:
        assert "disabled" not in inp

    guess_hint_selects = [s for s in parser.selects if s.get("name") == "guess_hint"]
    assert len(guess_hint_selects) == 1
    assert "disabled" not in guess_hint_selects[0]


def test_empty_themes_renders_error(client: FlaskClient) -> None:
    """Unchecking all themes submits empty sentinel and renders error with aria attributes."""
    # Malay
    resp_ms = client.get("/cetak?t=first_letter&themes=&seed=42&lang=ms")
    assert resp_ms.status_code == 400
    html_ms = resp_ms.data.decode("utf-8")
    assert "Sila pilih sekurang-kurangnya satu tema." in html_ms
    assert 'href="#field-themes"' in html_ms
    parser_ms = parse_html(html_ms)
    theme_boxes_ms = [
        inp for inp in parser_ms.get_inputs_by_name("themes")
        if inp.get("type") == "checkbox"
    ]
    assert len(theme_boxes_ms) == 4
    for box in theme_boxes_ms:
        assert "checked" not in box
        assert box.get("aria-invalid") == "true"
        assert box.get("aria-describedby") == "error-themes"

    # English
    resp_en = client.get("/cetak?t=guess_word&themes=&seed=42&lang=en")
    assert resp_en.status_code == 400
    html_en = resp_en.data.decode("utf-8")
    assert "Please select at least one theme." in html_en
    assert 'href="#field-themes"' in html_en


def test_guess_hint_control_rendered_and_prefilled(client: FlaskClient) -> None:
    """The guess_hint select control is rendered and correctly prefilled."""
    resp = client.get("/?t=guess_word&guess_hint=0&seed=123")
    assert resp.status_code == 200
    parser = parse_html(resp.data.decode("utf-8"))

    options = parser.select_options.get("guess_hint", [])
    assert len(options) == 2
    selected = [opt for opt in options if "selected" in opt]
    assert len(selected) == 1
    assert selected[0].get("value") == "0"
