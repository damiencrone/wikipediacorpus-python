"""Tests for HTTP infrastructure and exception classes."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus._http import (
    _check_api_response,
    _check_http_response,
    api_get,
)
from wikipediacorpus.exceptions import APIError, HTTPError, PageNotFoundError

# ── _check_http_response ─────────────────────────────────────────────────────


def test_check_http_response_raises_on_500():
    response = Response(500, text="Internal Server Error")
    with pytest.raises(HTTPError) as exc_info:
        _check_http_response(response)
    assert exc_info.value.status_code == 500


def test_check_http_response_raises_on_403():
    response = Response(403, text="Forbidden")
    with pytest.raises(HTTPError) as exc_info:
        _check_http_response(response)
    assert exc_info.value.status_code == 403


def test_check_http_response_passes_on_200():
    response = Response(200, text="OK")
    _check_http_response(response)  # Should not raise


# ── _check_api_response ──────────────────────────────────────────────────────


def test_check_api_response_raises_api_error():
    data = load_fixture("api_error.json")
    with pytest.raises(APIError) as exc_info:
        _check_api_response(data)
    assert exc_info.value.code == "badvalue"
    assert "Unrecognized value" in exc_info.value.info


def test_check_api_response_raises_page_not_found():
    data = load_fixture("missing_page.json")
    with pytest.raises(PageNotFoundError) as exc_info:
        _check_api_response(data, check_missing=True, title="Test Page", lang="en")
    assert exc_info.value.title == "Test Page"
    assert exc_info.value.lang == "en"


def test_check_api_response_passes_on_valid_data():
    data = load_fixture("article_response.json")
    _check_api_response(data)  # Should not raise


# ── Exception attributes ─────────────────────────────────────────────────────


def test_api_error_attributes():
    err = APIError(message="Bad request", code="badvalue", info="Invalid param")
    assert err.code == "badvalue"
    assert err.info == "Invalid param"
    assert "Bad request" in str(err)


def test_http_error_attributes():
    err = HTTPError(message="HTTP 500: Internal Server Error", status_code=500)
    assert err.status_code == 500
    assert "500" in str(err)


def test_page_not_found_attributes():
    err = PageNotFoundError(title="Missing Page", lang="de")
    assert err.title == "Missing Page"
    assert err.lang == "de"
    assert "Missing Page" in str(err)
    assert "de" in str(err)


# ── End-to-end: api_get raises errors ────────────────────────────────────────


@respx.mock
def test_api_get_raises_http_error(no_rate_limit):
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(500)
    )

    with pytest.raises(HTTPError) as exc_info:
        api_get({"action": "query", "format": "json"}, rate_limiter=no_rate_limit)
    assert exc_info.value.status_code == 500


@respx.mock
def test_api_get_raises_api_error(no_rate_limit):
    error_data = load_fixture("api_error.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=error_data)
    )

    with pytest.raises(APIError) as exc_info:
        api_get({"action": "query", "format": "json"}, rate_limiter=no_rate_limit)
    assert exc_info.value.code == "badvalue"
