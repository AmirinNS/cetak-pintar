"""Production proxy stack and seed validation regressions."""

import runpy

import pytest
from flask import request
from waitress.adjustments import Adjustments
from waitress.proxy_headers import proxy_headers_middleware
from werkzeug.test import Client

from cetak_kira import limiter
from sources import config


@pytest.mark.parametrize("hops", [0, 1, 2])
def test_production_proxy_stack_client_addresses_and_rate_buckets(monkeypatch, hops):
    captured = {}

    def capture_serve(app, **options):
        captured.update(app=app, adjustments=Adjustments(**options))

    monkeypatch.setattr("waitress.serve", capture_serve)
    monkeypatch.setattr(config, "IS_PRODUCTION", True)
    monkeypatch.setattr(config, "TRUSTED_PROXY_HOPS", hops)
    monkeypatch.setattr(config, "RATELIMIT_ENABLED", True)
    namespace = runpy.run_module("cetak_kira", run_name="__main__")
    app = captured["app"]
    app.add_url_rule(
        "/client-address",
        view_func=lambda: f"{request.remote_addr}|{request.scheme}|{request.host}",
    )
    adjustments = captured["adjustments"]
    # Use the installed Waitress middleware with the real entrypoint's adjustments.
    stack = proxy_headers_middleware(
        app,
        trusted_proxy=adjustments.trusted_proxy,
        trusted_proxy_count=adjustments.trusted_proxy_count,
        trusted_proxy_headers=adjustments.trusted_proxy_headers,
        clear_untrusted=adjustments.clear_untrusted_proxy_headers,
    )
    client = Client(stack)
    namespace["limiter"].reset()

    def get(path, address):
        forwarded = address if hops < 2 else f"{address}, 10.0.0.1"
        return client.get(
            path, headers={
                "X-Forwarded-For": forwarded,
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "spoof.example.com",
            },
            environ_overrides={"REMOTE_ADDR": "10.0.0.2"},
        )

    for address in ("203.0.113.5", "203.0.113.6"):
        expected = address if hops else "10.0.0.2"
        assert get("/client-address", address).text == f"{expected}|http|localhost"

    for _ in range(30):
        assert get("/cetak?t=add&seed=42&pages=1", "203.0.113.5").status_code == 200
    assert get("/cetak?t=add&seed=42&pages=1", "203.0.113.5").status_code == 429
    # Zero hops ignores spoofed addresses. Positive hops gives the second client its own bucket.
    expected_status = 200 if hops else 429
    assert get("/cetak?t=add&seed=42&pages=1", "203.0.113.6").status_code == expected_status


@pytest.mark.parametrize("seeds", [("", "42"), ("42", ""), (" \t ", "42")])
def test_repeated_blank_seed_rejected_before_resolution(client, seeds, monkeypatch):
    resolutions = []
    monkeypatch.setattr("cetak_kira.resolve_seed", lambda raw: resolutions.append(raw) or 7)
    limiter.reset()
    response = client.get("/cetak", query_string=[("t", "add"), *(("seed", s) for s in seeds)])
    assert response.status_code == 400
    assert 'id="error-seed"' in response.text
    assert resolutions == []
