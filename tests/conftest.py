"""Test fixtures for cetak-pintar."""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from cetak_pintar import app as flask_app


@pytest.fixture
def app() -> Flask:
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
