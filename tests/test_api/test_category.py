"""Tests for category member retrieval."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus import get_category_members, get_category_members_async
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
