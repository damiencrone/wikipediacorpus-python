"""Tests for redirect resolution."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus.api._redirects import (
    _parse_batch_redirects,
    get_redirects_to,
    get_redirects_to_async,
    resolve_redirect,
    resolve_redirect_async,
    resolve_redirects,
    resolve_redirects_async,
)


@respx.mock
def test_resolve_redirect_found(no_rate_limit):
    fixture = load_fixture("redirects.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    result = resolve_redirect("Morals", rate_limiter=no_rate_limit)
    assert result == "Morality"


@respx.mock
def test_resolve_redirect_not_found(no_rate_limit):
    fixture = load_fixture("redirect_destination.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    result = resolve_redirect("Python (programming language)", rate_limiter=no_rate_limit)
    assert result is None


@respx.mock
@pytest.mark.asyncio
async def test_resolve_redirect_async(no_rate_limit):
    fixture = load_fixture("redirects.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    result = await resolve_redirect_async("Morals", rate_limiter=no_rate_limit)
    assert result == "Morality"


@respx.mock
@pytest.mark.asyncio
async def test_resolve_redirects_batch(no_rate_limit):
    """Batch resolution with multiple titles."""
    response = {
        "batchcomplete": "",
        "query": {
            "redirects": [
                {"from": "Morals", "to": "Morality"},
                {"from": "JS", "to": "JavaScript"},
            ],
            "pages": {
                "1": {"pageid": 1, "ns": 0, "title": "Morality"},
                "2": {"pageid": 2, "ns": 0, "title": "JavaScript"},
                "3": {"pageid": 3, "ns": 0, "title": "Python (programming language)"},
            },
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=response)
    )

    result = await resolve_redirects_async(
        ["Morals", "JS", "Python (programming language)"],
        rate_limiter=no_rate_limit,
    )
    assert result["Morals"] == "Morality"
    assert result["JS"] == "JavaScript"
    assert result["Python (programming language)"] is None


@respx.mock
def test_get_redirects_to(no_rate_limit):
    fixture = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "23862": {
                    "pageid": 23862,
                    "ns": 0,
                    "title": "Python (programming language)",
                    "redirects": [
                        {"pageid": 100, "ns": 0, "title": "Python language"},
                        {"pageid": 101, "ns": 0, "title": "Python programming"},
                    ],
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    redirects = get_redirects_to(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(redirects) == 2
    assert "Python language" in redirects
    assert "Python programming" in redirects


@respx.mock
def test_get_redirects_to_none(no_rate_limit):
    fixture = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "23862": {
                    "pageid": 23862,
                    "ns": 0,
                    "title": "Python (programming language)",
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    redirects = get_redirects_to(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert redirects == []


@respx.mock
def test_get_redirects_to_pagination(no_rate_limit):
    page1 = {
        "continue": {"rdcontinue": "0|next", "continue": "||"},
        "query": {
            "pages": {
                "1": {
                    "pageid": 1, "ns": 0, "title": "Test",
                    "redirects": [
                        {"pageid": 10, "ns": 0, "title": "Redirect A"},
                    ],
                }
            }
        },
    }
    page2 = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "1": {
                    "pageid": 1, "ns": 0, "title": "Test",
                    "redirects": [
                        {"pageid": 11, "ns": 0, "title": "Redirect B"},
                    ],
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    redirects = get_redirects_to("Test", rate_limiter=no_rate_limit)
    assert len(redirects) == 2
    assert "Redirect A" in redirects
    assert "Redirect B" in redirects


@respx.mock
@pytest.mark.asyncio
async def test_get_redirects_to_async(no_rate_limit):
    fixture = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "1": {
                    "pageid": 1, "ns": 0, "title": "Test",
                    "redirects": [
                        {"pageid": 10, "ns": 0, "title": "Redirect X"},
                    ],
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    redirects = await get_redirects_to_async("Test", rate_limiter=no_rate_limit)
    assert redirects == ["Redirect X"]


# ── Sync batch resolve ────────────────────────────────────────────────────────


@respx.mock
def test_resolve_redirects_sync(no_rate_limit):
    """Sync wrapper for batch redirect resolution."""
    response = {
        "batchcomplete": "",
        "query": {
            "redirects": [
                {"from": "Morals", "to": "Morality"},
            ],
            "pages": {
                "1": {"pageid": 1, "ns": 0, "title": "Morality"},
                "2": {"pageid": 2, "ns": 0, "title": "Ethics"},
            },
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=response)
    )

    result = resolve_redirects(
        ["Morals", "Ethics"], rate_limiter=no_rate_limit
    )
    assert result["Morals"] == "Morality"
    assert result["Ethics"] is None


# ── Normalization ─────────────────────────────────────────────────────────────


def test_parse_batch_redirects_with_normalization():
    """Title normalization should be applied before redirect lookup."""
    data = {
        "batchcomplete": "",
        "query": {
            "normalized": [
                {"from": "python (programming language)", "to": "Python (programming language)"}
            ],
            "redirects": [
                {"from": "Python (programming language)", "to": "Python (programming language) v2"}
            ],
            "pages": {
                "1": {"pageid": 1, "ns": 0, "title": "Python (programming language) v2"}
            },
        },
    }
    result = _parse_batch_redirects(data, ["python (programming language)"])
    assert result["python (programming language)"] == "Python (programming language) v2"


def test_parse_batch_redirects_chases_chain():
    """Multi-hop redirects A→B→C should resolve A to C."""
    data = {
        "batchcomplete": "",
        "query": {
            "redirects": [
                {"from": "A", "to": "B"},
                {"from": "B", "to": "C"},
            ],
            "pages": {
                "1": {"pageid": 1, "ns": 0, "title": "C"},
            },
        },
    }
    result = _parse_batch_redirects(data, ["A", "B", "C"])
    assert result["A"] == "C"
    assert result["B"] == "C"
    assert result["C"] is None


@respx.mock
@pytest.mark.asyncio
async def test_resolve_redirects_with_normalization(no_rate_limit):
    """End-to-end normalization + redirect resolution."""
    data = load_fixture("redirects_normalized.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=data)
    )

    result = await resolve_redirects_async(
        ["python (programming language)"], rate_limiter=no_rate_limit
    )
    assert result["python (programming language)"] == "Python (programming language) v2"


# ── Async pagination for get_redirects_to_async ──────────────────────────────


@respx.mock
@pytest.mark.asyncio
async def test_get_redirects_to_async_pagination(no_rate_limit):
    page1 = {
        "continue": {"rdcontinue": "0|next", "continue": "||"},
        "query": {
            "pages": {
                "1": {
                    "pageid": 1, "ns": 0, "title": "Test",
                    "redirects": [
                        {"pageid": 10, "ns": 0, "title": "Redirect A"},
                    ],
                }
            }
        },
    }
    page2 = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "1": {
                    "pageid": 1, "ns": 0, "title": "Test",
                    "redirects": [
                        {"pageid": 11, "ns": 0, "title": "Redirect B"},
                    ],
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    redirects = await get_redirects_to_async("Test", rate_limiter=no_rate_limit)
    assert len(redirects) == 2
    assert "Redirect A" in redirects
    assert "Redirect B" in redirects
