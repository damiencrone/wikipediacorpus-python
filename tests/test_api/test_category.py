"""Tests for category member retrieval and page categories."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus import get_category_members, get_category_members_async
from wikipediacorpus.api._category import (
    _cmtype_for_namespace,
    get_page_categories,
    get_page_categories_async,
)
from wikipediacorpus.models import Namespace


@respx.mock
def test_get_category_members(no_rate_limit):
    fixture = load_fixture("category_members.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    members = get_category_members(
        "Programming languages", rate_limiter=no_rate_limit
    )
    assert len(members) == 3
    assert members[0].title == "Category:Functional languages"
    assert members[0].ns == 14


@respx.mock
def test_get_category_members_auto_prefix(no_rate_limit):
    """Category: prefix is auto-prepended if missing."""
    fixture = load_fixture("category_members.json")
    route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    get_category_members("Animals", rate_limiter=no_rate_limit)
    assert "Category%3AAnimals" in str(route.calls[0].request.url)


@respx.mock
def test_get_category_members_already_prefixed(no_rate_limit):
    fixture = load_fixture("category_members.json")
    route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    get_category_members("Category:Animals", rate_limiter=no_rate_limit)
    # Should not double-prefix
    url = str(route.calls[0].request.url)
    assert "Category%3ACategory" not in url


@respx.mock
def test_get_category_members_pagination(no_rate_limit):
    """Handles cmcontinue pagination."""
    page1 = load_fixture("category_continue.json")
    page2 = load_fixture("category_members.json")

    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    members = get_category_members(
        "Programming languages", rate_limiter=no_rate_limit
    )
    # 2 from first page + 3 from second page
    assert len(members) == 5


@respx.mock
def test_get_category_members_page_namespace(no_rate_limit):
    fixture = {
        "batchcomplete": "",
        "query": {
            "categorymembers": [
                {"pageid": 300, "ns": 0, "title": "Python (programming language)"}
            ]
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    members = get_category_members(
        "Programming languages", namespace=Namespace.MAIN, rate_limiter=no_rate_limit
    )
    assert len(members) == 1
    assert members[0].ns == 0


@respx.mock
@pytest.mark.asyncio
async def test_get_category_members_async(no_rate_limit):
    fixture = load_fixture("category_members.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    members = await get_category_members_async(
        "Programming languages", rate_limiter=no_rate_limit
    )
    assert len(members) == 3


# ── Page categories tests ────────────────────────────────────────────────────


@respx.mock
def test_get_page_categories(no_rate_limit):
    fixture = load_fixture("page_categories.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    categories = get_page_categories(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(categories) == 3
    assert "Category:Programming languages" in categories
    assert "Category:Object-oriented programming languages" in categories


@respx.mock
def test_get_page_categories_hidden(no_rate_limit):
    """When hidden=True, clshow param should not be set."""
    fixture = load_fixture("page_categories.json")
    route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    get_page_categories(
        "Test", hidden=True, rate_limiter=no_rate_limit
    )

    url = str(route.calls[0].request.url)
    assert "clshow" not in url


@respx.mock
def test_get_page_categories_not_hidden(no_rate_limit):
    """When hidden=False (default), clshow=!hidden should be set."""
    fixture = load_fixture("page_categories.json")
    route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    get_page_categories("Test", rate_limiter=no_rate_limit)

    url = str(route.calls[0].request.url)
    assert "clshow" in url


@respx.mock
def test_get_page_categories_empty(no_rate_limit):
    fixture = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "123": {"pageid": 123, "ns": 0, "title": "No Categories"}
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    categories = get_page_categories("No Categories", rate_limiter=no_rate_limit)
    assert categories == []


@respx.mock
def test_get_page_categories_pagination(no_rate_limit):
    page1 = {
        "continue": {"clcontinue": "23862|Category:Next", "continue": "||"},
        "query": {
            "pages": {
                "23862": {
                    "pageid": 23862, "ns": 0,
                    "title": "Python (programming language)",
                    "categories": [
                        {"ns": 14, "title": "Category:First"},
                    ],
                }
            }
        },
    }
    page2 = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "23862": {
                    "pageid": 23862, "ns": 0,
                    "title": "Python (programming language)",
                    "categories": [
                        {"ns": 14, "title": "Category:Second"},
                    ],
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    categories = get_page_categories(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(categories) == 2
    assert "Category:First" in categories
    assert "Category:Second" in categories


@respx.mock
@pytest.mark.asyncio
async def test_get_page_categories_async(no_rate_limit):
    fixture = load_fixture("page_categories.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    categories = await get_page_categories_async(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(categories) == 3


# ── Validation ────────────────────────────────────────────────────────────────


def test_cmtype_for_invalid_namespace():
    """_cmtype_for_namespace should raise ValueError for unsupported namespaces."""
    from enum import Enum

    class FakeNamespace(Enum):
        TALK = 1

    with pytest.raises(ValueError, match="Unsupported namespace"):
        _cmtype_for_namespace(FakeNamespace.TALK)


# ── Async pagination ─────────────────────────────────────────────────────────


@respx.mock
@pytest.mark.asyncio
async def test_get_category_members_async_pagination(no_rate_limit):
    page1 = load_fixture("category_continue.json")
    page2 = load_fixture("category_members.json")

    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    members = await get_category_members_async(
        "Programming languages", rate_limiter=no_rate_limit
    )
    # 2 from first page + 3 from second page
    assert len(members) == 5


@respx.mock
def test_get_category_members_continue_without_cmcontinue(no_rate_limit):
    """Response with 'continue' but no 'cmcontinue' should stop, not KeyError."""
    fixture = {
        "continue": {"continue": "-||"},
        "query": {
            "categorymembers": [
                {"pageid": 300, "ns": 14, "title": "Category:Test"}
            ]
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    members = get_category_members(
        "Programming languages", rate_limiter=no_rate_limit
    )
    assert len(members) == 1
    assert members[0].title == "Category:Test"


@respx.mock
@pytest.mark.asyncio
async def test_get_page_categories_async_pagination(no_rate_limit):
    page1 = {
        "continue": {"clcontinue": "23862|Category:Next", "continue": "||"},
        "query": {
            "pages": {
                "23862": {
                    "pageid": 23862, "ns": 0,
                    "title": "Python (programming language)",
                    "categories": [
                        {"ns": 14, "title": "Category:First"},
                    ],
                }
            }
        },
    }
    page2 = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "23862": {
                    "pageid": 23862, "ns": 0,
                    "title": "Python (programming language)",
                    "categories": [
                        {"ns": 14, "title": "Category:Second"},
                    ],
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    categories = await get_page_categories_async(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(categories) == 2
    assert "Category:First" in categories
    assert "Category:Second" in categories
