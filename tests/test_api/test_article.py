"""Tests for article retrieval."""

from __future__ import annotations

import logging

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus import get_article, get_article_async, get_articles, get_articles_async
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


@respx.mock
def test_get_articles_sync_batch(no_rate_limit):
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

    articles = get_articles(
        ["Python (programming language)", "JavaScript"],
        rate_limiter=no_rate_limit,
    )
    assert len(articles) == 2
    titles = {a.title for a in articles}
    assert "Python (programming language)" in titles
    assert "JavaScript" in titles


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_async_skips_missing_page(no_rate_limit):
    fixture_good = load_fixture("article_response.json")
    fixture_missing = load_fixture("missing_page.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_good), Response(200, json=fixture_missing)]
    )

    articles = await get_articles_async(
        ["Python (programming language)", "Nonexistent page qwerty12345"],
        rate_limiter=no_rate_limit,
    )
    assert len(articles) == 1
    assert articles[0].title == "Python (programming language)"


@respx.mock
def test_get_articles_sync_skips_missing_page(no_rate_limit):
    fixture_good = load_fixture("article_response.json")
    fixture_missing = load_fixture("missing_page.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_good), Response(200, json=fixture_missing)]
    )

    articles = get_articles(
        ["Python (programming language)", "Nonexistent page qwerty12345"],
        rate_limiter=no_rate_limit,
    )
    assert len(articles) == 1
    assert articles[0].title == "Python (programming language)"


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_all_missing(no_rate_limit):
    fixture_missing = load_fixture("missing_page.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_missing), Response(200, json=fixture_missing)]
    )

    articles = await get_articles_async(
        ["Nonexistent page qwerty12345", "Another missing page"],
        rate_limiter=no_rate_limit,
    )
    assert articles == []


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_single_title(no_rate_limit):
    fixture = load_fixture("article_response.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    articles = await get_articles_async(
        ["Python (programming language)"],
        rate_limiter=no_rate_limit,
    )
    assert len(articles) == 1
    assert articles[0].title == "Python (programming language)"


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_empty_list(no_rate_limit):
    articles = await get_articles_async([], rate_limiter=no_rate_limit)
    assert articles == []
    assert respx.calls.call_count == 0


@respx.mock
def test_get_articles_logs_warning_on_missing(no_rate_limit, caplog):
    fixture_good = load_fixture("article_response.json")
    fixture_missing = load_fixture("missing_page.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_good), Response(200, json=fixture_missing)]
    )

    with caplog.at_level(logging.WARNING, logger="wikipediacorpus.api._article"):
        articles = get_articles(
            ["Python (programming language)", "Nonexistent page qwerty12345"],
            rate_limiter=no_rate_limit,
        )

    assert len(articles) == 1
    warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("Skipping missing page" in m for m in warning_messages)
    assert any("Skipped 1 missing page(s) out of 2 requested" in m for m in warning_messages)


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_multiple_missing_in_larger_batch(no_rate_limit):
    fixture_good = load_fixture("article_response.json")
    fixture_js = {
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
    fixture_missing = load_fixture("missing_page.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[
            Response(200, json=fixture_good),
            Response(200, json=fixture_js),
            Response(200, json=fixture_missing),
            Response(200, json=fixture_missing),
        ]
    )

    articles = await get_articles_async(
        ["Python (programming language)", "JavaScript", "Missing1", "Missing2"],
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


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_api_error_still_propagates(no_rate_limit):
    error_data = load_fixture("api_error.json")
    fixture_good = load_fixture("article_response.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_good), Response(200, json=error_data)]
    )

    with pytest.raises(APIError) as exc_info:
        await get_articles_async(
            ["Python (programming language)", "Bad"],
            rate_limiter=no_rate_limit,
        )
    assert exc_info.value.code == "badvalue"


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_http_error_still_propagates(no_rate_limit):
    fixture_good = load_fixture("article_response.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_good), Response(500)]
    )

    with pytest.raises(HTTPError) as exc_info:
        await get_articles_async(
            ["Python (programming language)", "ServerError"],
            rate_limiter=no_rate_limit,
        )
    assert exc_info.value.status_code == 500
