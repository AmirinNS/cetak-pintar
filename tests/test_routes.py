"""Tests for CetakKira Flask web routes, templates, rate limiter, and PDF determinism."""

from __future__ import annotations

import tempfile
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

from flask.testing import FlaskClient

import cli
from cetak_kira import limiter
from modules.render.pdf import render
from modules.spec import parse_spec


def test_index_status_and_seed(client: FlaskClient) -> None:
    """GET / renders 200 with a resolved integer seed in a hidden field."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Document language follows default 'ms'
    assert '<html lang="ms">' in html

    # Hidden seed input present with an integer value
    assert 'name="seed"' in html
    assert 'id="input-seed"' in html

    # Presets, mascot, and topics present
    assert "t1" in html
    assert "t2" in html
    assert "t3" in html
    assert "mascot.webp" in html
    assert "topic-grid.webp" in html
    assert "topic-add.webp" in html
    assert "topic-sub.webp" in html


def test_index_prefills_preset_and_query(client: FlaskClient) -> None:
    """Query parameters prefill form controls, presets, and language toggle."""
    # Preset t2 (Year 2: grid 101-200, add 2-digit, sub 2-digit, sifir 2,3,4,5,10)
    resp_t2 = client.get("/?preset=t2")
    assert resp_t2.status_code == 200
    html_t2 = resp_t2.data.decode("utf-8")
    assert 'id="topic-check-grid"' in html_t2
    assert 'value="101"' in html_t2

    # Language toggle to English
    resp_en = client.get("/?lang=en")
    assert resp_en.status_code == 200
    html_en = resp_en.data.decode("utf-8")
    assert '<html lang="en">' in html_en
    assert "Generate Printable A4 Math Worksheets" in html_en

    # Explicit query prefill
    resp_custom = client.get("/?t=div&div_digits=3&div_rem=1&seed=98765&pages=2")
    assert resp_custom.status_code == 200
    html_custom = resp_custom.data.decode("utf-8")
    assert 'value="98765"' in html_custom
    assert 'value="3"' in html_custom


def test_seedless_cetak_redirects(client: FlaskClient) -> None:
    """GET /cetak without a seed triggers a 302 redirect to canonical query with a new seed."""
    # Seedless with preset
    resp = client.get("/cetak?preset=t1")
    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert location.startswith("/cetak?")
    assert "seed=" in location
    assert "t=grid%2Ccount%2Cadd%2Csub" in location or "t=grid,count,add,sub" in location

    # Seedless bare request
    resp_bare = client.get("/cetak")
    assert resp_bare.status_code == 302
    assert "seed=" in resp_bare.headers["Location"]

    # Seedless explicit topic
    resp_topic = client.get("/cetak?t=add")
    assert resp_topic.status_code == 302
    assert "t=add" in resp_topic.headers["Location"]
    assert "seed=" in resp_topic.headers["Location"]


def test_valid_spec_pdf_and_cli_determinism(client: FlaskClient) -> None:
    """Valid spec returns inline PDF matching CLI output byte-for-byte."""
    query = "t=add&pages=4&lang=ms&ans=1&seed=42&add_digits=1&add_regroup=0"
    spec, errors = parse_spec(query)
    assert errors == []
    assert spec is not None

    # Web route response
    response = client.get(f"/cetak?{query}")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.headers["Content-Disposition"] == 'inline; filename="cetakkira-add-42.pdf"'
    web_bytes = response.data

    # Modules direct render
    direct_bytes = render(spec)
    assert web_bytes == direct_bytes

    # CLI render output comparison
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "cli_out.pdf"
        cli_argv = [
            "--topics", "add",
            "--pages", "4",
            "--lang", "ms",
            "--seed", "42",
            "--add-digits", "1",
            "--no-add-regroup",
            "-o", str(out_path),
        ]
        exit_code = cli.main(cli_argv)
        assert exit_code == 0
        cli_bytes = out_path.read_bytes()
        assert web_bytes == cli_bytes


def test_invalid_input_returns_400_and_localized_messages(client: FlaskClient) -> None:
    """Invalid options return 400 with localized messages and error summary in ms and en."""
    # 21 pages rejected (Malay)
    resp_ms = client.get("/cetak?t=add&pages=21&seed=100&lang=ms")
    assert resp_ms.status_code == 400
    html_ms = resp_ms.data.decode("utf-8")
    assert '<html lang="ms">' in html_ms
    assert "Nilai di luar julat yang dibenarkan." in html_ms
    assert 'id="error-summary"' in html_ms
    # User's submitted value is kept in the input
    assert 'value="21"' in html_ms

    # 21 pages rejected (English)
    resp_en = client.get("/cetak?t=add&pages=21&seed=100&lang=en")
    assert resp_en.status_code == 400
    html_en = resp_en.data.decode("utf-8")
    assert '<html lang="en">' in html_en
    assert "Value is out of the allowed range." in html_en
    assert 'id="error-summary"' in html_en

    # Impossible borrow with 1 digit (Malay & English)
    resp_borrow_ms = client.get("/cetak?t=sub&sub_digits=1&sub_borrow=1&seed=100&lang=ms")
    assert resp_borrow_ms.status_code == 400
    assert (
        "Operasi tolak dengan kumpul semula memerlukan sekurang-kurangnya 2 digit."
        in resp_borrow_ms.data.decode("utf-8")
    )

    resp_borrow_en = client.get("/cetak?t=sub&sub_digits=1&sub_borrow=1&seed=100&lang=en")
    assert resp_borrow_en.status_code == 400
    assert (
        "Subtraction with regrouping requires at least 2 digits."
        in resp_borrow_en.data.decode("utf-8")
    )


def test_rate_limiter_and_proxy_trust(client: FlaskClient) -> None:
    """30 requests per minute succeed; 31st returns 429 with Retry-After and localized page."""
    limiter.reset()

    # Perform 30 requests to /cetak
    for i in range(30):
        r = client.get(f"/cetak?t=add&seed={1000 + i}")
        assert r.status_code == 200, f"Request {i+1} failed"

    # 31st request triggers rate limit
    r_31 = client.get("/cetak?t=add&seed=9999&lang=en")
    assert r_31.status_code == 429
    assert r_31.headers.get("Retry-After") == "60"
    html_429 = r_31.data.decode("utf-8")
    assert "Too Many Requests" in html_429
    assert '<html lang="en">' in html_429

    # Spoofed X-Forwarded-For is ignored when TRUSTED_PROXY_HOPS=0
    # Even with a different forwarded IP, it is still blocked under the same remote_addr
    r_spoof = client.get(
        "/cetak?t=add&seed=10000",
        headers={"X-Forwarded-For": "203.0.113.195"},
    )
    assert r_spoof.status_code == 429

    # Reset limiter for subsequent tests
    limiter.reset()


def test_health_and_static_routes(client: FlaskClient) -> None:
    """Health check, robots.txt, and sitemap.xml respond correctly."""
    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.is_json
    assert resp_health.json["status"] == "ok"

    resp_robots = client.get("/robots.txt")
    assert resp_robots.status_code == 200
    assert "User-agent: *" in resp_robots.data.decode("utf-8")

    resp_sitemap = client.get("/sitemap.xml")
    assert resp_sitemap.status_code == 200
    assert "urlset" in resp_sitemap.data.decode("utf-8")


def test_no_js_form_submission(client: FlaskClient) -> None:
    """Derive submitted values directly from rendered HTML controls with JS disabled."""
    index_resp = client.get("/")
    assert index_resp.status_code == 200
    html = index_resp.data.decode("utf-8")

    class HTMLControlParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.inputs: list[dict[str, str]] = []
            self.selects: list[dict[str, str]] = []
            self.select_options: dict[str, list[dict[str, str]]] = {}
            self._current_select: str | None = None

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            attr_dict = {k: v or "" for k, v in attrs}
            if tag == "input":
                self.inputs.append(attr_dict)
            elif tag == "select":
                name = attr_dict.get("name", "")
                self._current_select = name
                self.selects.append(attr_dict)
                self.select_options[name] = []
            elif tag == "option" and self._current_select is not None:
                self.select_options[self._current_select].append(attr_dict)

        def handle_endtag(self, tag: str) -> None:
            if tag == "select":
                self._current_select = None

    parser = HTMLControlParser()
    parser.feed(html)

    # Derive GET submission parameters exactly as a browser without JS would:
    # Enabled inputs + enabled selects with selected/first option
    params: list[tuple[str, str]] = []

    for inp in parser.inputs:
        if "disabled" in inp:
            continue
        name = inp.get("name")
        if not name:
            continue
        inp_type = inp.get("type", "text")
        val = inp.get("value", "")
        if inp_type in ("text", "number", "hidden"):
            params.append((name, val))
        elif inp_type == "checkbox":
            if "checked" in inp:
                params.append((name, val))

    for sel in parser.selects:
        if "disabled" in sel:
            continue
        name = sel.get("name")
        if not name:
            continue
        options = parser.select_options.get(name, [])
        selected_val = ""
        for opt in options:
            if "selected" in opt:
                selected_val = opt.get("value", "")
                break
        else:
            if options:
                selected_val = options[0].get("value", "")
        params.append((name, selected_val))

    query_str = urllib.parse.urlencode(params)
    resp = client.get(f"/cetak?{query_str}")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"
    assert resp.data.startswith(b"%PDF")


def test_localized_404_error_page(client: FlaskClient) -> None:
    """Non-existent page renders 404 in Malay and English."""
    resp_ms = client.get("/halaman-tiada?lang=ms")
    assert resp_ms.status_code == 404
    assert '<html lang="ms">' in resp_ms.data.decode("utf-8")
    assert "Halaman Tidak Dijumpai" in resp_ms.data.decode("utf-8")

    resp_en = client.get("/nonexistent-page?lang=en")
    assert resp_en.status_code == 404
    assert '<html lang="en">' in resp_en.data.decode("utf-8")
    assert "Page Not Found" in resp_en.data.decode("utf-8")
