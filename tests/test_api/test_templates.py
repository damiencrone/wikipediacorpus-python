"""Tests for template retrieval."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus.api._templates import get_templates, get_templates_async


@respx.mock
def test_get_templates(no_rate_limit):
    fixture = load_fixture("templates.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    templates = get_templates(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(templates) == 3
    assert "Template:Infobox programming language" in templates
    assert "Template:Cite web" in templates
    assert "Template:Reflist" in templates


@respx.mock
def test_get_templates_empty(no_rate_limit):
    fixture = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "123": {"pageid": 123, "ns": 0, "title": "Empty Page"}
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    templates = get_templates("Empty Page", rate_limiter=no_rate_limit)
    assert templates == []


@respx.mock
def test_get_templates_pagination(no_rate_limit):
    page1 = {
        "continue": {"tlcontinue": "23862|10|next", "continue": "||"},
        "query": {
            "pages": {
                "23862": {
                    "pageid": 23862, "ns": 0,
                    "title": "Python (programming language)",
                    "templates": [
                        {"ns": 10, "title": "Template:Cite web"},
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
                    "templates": [
                        {"ns": 10, "title": "Template:Reflist"},
                    ],
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    templates = get_templates(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(templates) == 2
    assert "Template:Cite web" in templates
    assert "Template:Reflist" in templates


@respx.mock
def test_get_templates_params(no_rate_limit):
    """Verify correct API parameters are sent."""
    fixture = load_fixture("templates.json")
    route = respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    get_templates("Test", rate_limiter=no_rate_limit)

    url = str(route.calls[0].request.url)
    assert "prop=templates" in url
    assert "tlnamespace=10" in url
    assert "tllimit=max" in url


@respx.mock
@pytest.mark.asyncio
async def test_get_templates_async(no_rate_limit):
    fixture = load_fixture("templates.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    templates = await get_templates_async(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert len(templates) == 3


# ── Async pagination ─────────────────────────────────────────────────────────


@respx.mock
@pytest.mark.asyncio
async def test_get_templates_async_pagination(no_rate_limit):
    page1 = load_fixture("templates_continue.json")
    page2 = load_fixture("templates.json")

    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=page1), Response(200, json=page2)]
    )

    templates = await get_templates_async(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    # 2 from first page (continue) + 3 from second page (complete)
    assert len(templates) == 5
    assert "Template:Infobox programming language" in templates
    assert "Template:Cite web" in templates
    assert "Template:Reflist" in templates
