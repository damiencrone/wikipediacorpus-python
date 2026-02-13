"""Tests for article retrieval."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus import get_article, get_article_async, get_articles_async
from wikipediacorpus.exceptions import APIError, HTTPError, PageNotFoundError


@respx.mock
def test_get_article(no_rate_limit):
    fixture = load_fixture("article_response.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    article = get_article(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert article.title == "Python (programming language)"
    assert article.pageid == 23862
    assert article.lang == "en"
    assert "high-level" in article.text


@respx.mock
def test_get_article_missing_page(no_rate_limit):
    fixture = load_fixture("missing_page.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    with pytest.raises(PageNotFoundError) as exc_info:
        get_article("Nonexistent page qwerty12345", rate_limiter=no_rate_limit)
    assert "Nonexistent page qwerty12345" in str(exc_info.value)


@respx.mock
@pytest.mark.asyncio
async def test_get_article_async(no_rate_limit):
    fixture = load_fixture("article_response.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    article = await get_article_async(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert article.title == "Python (programming language)"
    assert article.pageid == 23862


@respx.mock
def test_get_article_custom_lang(no_rate_limit):
    fixture = load_fixture("article_response.json")
    respx.get("https://fr.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    article = get_article(
        "Python (programming language)", lang="fr", rate_limiter=no_rate_limit
    )
    assert article.lang == "fr"


# ── Batch functions ───────────────────────────────────────────────────────────


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_async_batch(no_rate_limit):
    fixture_a = load_fixture("article_response.json")
    fixture_b = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "12345": {
                    "pageid": 12345,
                    "ns": 0,
                    "title": "JavaScript",
                    "extract": "JavaScript is a programming language.",
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_a), Response(200, json=fixture_b)]
    )

    articles = await get_articles_async(
        ["Python (programming language)", "JavaScript"],
        rate_limiter=no_rate_limit,
    )
    assert len(articles) == 2
    titles = {a.title for a in articles}
    assert "Python (programming language)" in titles
    assert "JavaScript" in titles


# ── Error paths ───────────────────────────────────────────────────────────────


@respx.mock
def test_get_article_api_error(no_rate_limit):
    error_data = load_fixture("api_error.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=error_data)
    )

    with pytest.raises(APIError) as exc_info:
        get_article("Test", rate_limiter=no_rate_limit)
    assert exc_info.value.code == "badvalue"


@respx.mock
def test_get_article_http_error(no_rate_limit):
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(500)
    )

    with pytest.raises(HTTPError) as exc_info:
        get_article("Test", rate_limiter=no_rate_limit)
    assert exc_info.value.status_code == 500
