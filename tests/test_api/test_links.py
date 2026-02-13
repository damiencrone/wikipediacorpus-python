"""Tests for link retrieval."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus import get_links, get_links_async
from wikipediacorpus.models import LinkDirection


@respx.mock
def test_get_links_outgoing(no_rate_limit):
    fixture = load_fixture("links_outgoing.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    links = get_links(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(links) == 3
    assert links[0].title == "Guido van Rossum"
    assert links[0].ns == 0


@respx.mock
def test_get_links_incoming(no_rate_limit):
    fixture = load_fixture("links_incoming.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    links = get_links(
        "Python (programming language)",
        direction=LinkDirection.INCOMING,
        rate_limiter=no_rate_limit,
    )
    assert len(links) == 2
    assert links[0].pageid == 500


@respx.mock
def test_get_links_uses_page_variable(no_rate_limit):
    """Verify the R bug is fixed: titles param uses the page variable."""
    fixture = load_fixture("links_outgoing.json")
    route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    get_links("Psychology", rate_limiter=no_rate_limit)

    # The request URL should contain "Psychology", not the literal "page"
    url = str(route.calls[0].request.url)
    assert "Psychology" in url
    assert "titles=page" not in url.replace("titles=Psychology", "")


@respx.mock
def test_get_links_outgoing_params(no_rate_limit):
    """Outgoing links use 'links' prop and pl* params."""
    fixture = load_fixture("links_outgoing.json")
    route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    get_links("Test", rate_limiter=no_rate_limit)

    url = str(route.calls[0].request.url)
    assert "prop=links" in url
    assert "pllimit=max" in url


@respx.mock
def test_get_links_incoming_params(no_rate_limit):
    """Incoming links use 'linkshere' prop and lh* params."""
    fixture = load_fixture("links_incoming.json")
    route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    get_links("Test", direction=LinkDirection.INCOMING, rate_limiter=no_rate_limit)

    url = str(route.calls[0].request.url)
    assert "prop=linkshere" in url
    assert "lhlimit=max" in url


@respx.mock
@pytest.mark.asyncio
async def test_get_links_async(no_rate_limit):
    fixture = load_fixture("links_outgoing.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    links = await get_links_async(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(links) == 3


# ── Pagination ────────────────────────────────────────────────────────────────


@respx.mock
def test_get_links_outgoing_pagination(no_rate_limit):
    page1 = load_fixture("links_outgoing_continue.json")
    page2 = load_fixture("links_outgoing.json")

    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    links = get_links(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    # 2 from first page (continue) + 3 from second page (complete)
    assert len(links) == 5


@respx.mock
def test_get_links_incoming_pagination(no_rate_limit):
    page1 = load_fixture("links_incoming_continue.json")
    page2 = load_fixture("links_incoming.json")

    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    links = get_links(
        "Python (programming language)",
        direction=LinkDirection.INCOMING,
        rate_limiter=no_rate_limit,
    )
    # 1 from first page (continue) + 2 from second page (complete)
    assert len(links) == 3


# ── Edge cases ────────────────────────────────────────────────────────────────


@respx.mock
def test_get_links_empty_result(no_rate_limit):
    fixture = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "123": {
                    "pageid": 123,
                    "ns": 0,
                    "title": "Empty Page",
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    links = get_links("Empty Page", rate_limiter=no_rate_limit)
    assert links == []


@respx.mock
def test_get_links_custom_namespaces(no_rate_limit):
    fixture = load_fixture("links_outgoing.json")
    route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    get_links("Test", namespaces=[0, 14], rate_limiter=no_rate_limit)

    url = str(route.calls[0].request.url)
    assert "plnamespace=0%7C14" in url or "plnamespace=0|14" in url
