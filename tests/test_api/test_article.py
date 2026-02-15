"""Tests for article retrieval."""

from __future__ import annotations

import logging

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus import get_article, get_article_async, get_articles, get_articles_async
from wikipediacorpus.exceptions import APIError, HTTPError, PageNotFoundError
from wikipediacorpus.models import ArticleBatch


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
                    "length": 200,
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_a), Response(200, json=fixture_b)]
    )

    result = await get_articles_async(
        ["Python (programming language)", "JavaScript"],
        rate_limiter=no_rate_limit,
    )
    assert isinstance(result, ArticleBatch)
    assert len(result.articles) == 2
    titles = {a.title for a in result.articles}
    assert "Python (programming language)" in titles
    assert "JavaScript" in titles
    assert result.missing == []


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
                    "length": 200,
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_a), Response(200, json=fixture_b)]
    )

    result = get_articles(
        ["Python (programming language)", "JavaScript"],
        rate_limiter=no_rate_limit,
    )
    assert isinstance(result, ArticleBatch)
    assert len(result.articles) == 2
    titles = {a.title for a in result.articles}
    assert "Python (programming language)" in titles
    assert "JavaScript" in titles
    assert result.missing == []


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_async_skips_missing_page(no_rate_limit):
    fixture_good = load_fixture("article_response.json")
    fixture_missing = load_fixture("missing_page.json")

    def _dispatch(request):
        title = request.url.params.get("titles", "")
        if "Nonexistent" in title:
            return Response(200, json=fixture_missing)
        return Response(200, json=fixture_good)

    respx.get("https://en.wikipedia.org/w/api.php").mock(side_effect=_dispatch)

    result = await get_articles_async(
        ["Python (programming language)", "Nonexistent page qwerty12345"],
        rate_limiter=no_rate_limit,
    )
    assert len(result.articles) == 1
    assert result.articles[0].title == "Python (programming language)"
    assert set(result.missing) == {"Nonexistent page qwerty12345"}


@respx.mock
def test_get_articles_sync_skips_missing_page(no_rate_limit):
    fixture_good = load_fixture("article_response.json")
    fixture_missing = load_fixture("missing_page.json")

    def _dispatch(request):
        title = request.url.params.get("titles", "")
        if "Nonexistent" in title:
            return Response(200, json=fixture_missing)
        return Response(200, json=fixture_good)

    respx.get("https://en.wikipedia.org/w/api.php").mock(side_effect=_dispatch)

    result = get_articles(
        ["Python (programming language)", "Nonexistent page qwerty12345"],
        rate_limiter=no_rate_limit,
    )
    assert len(result.articles) == 1
    assert result.articles[0].title == "Python (programming language)"
    assert set(result.missing) == {"Nonexistent page qwerty12345"}


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_all_missing(no_rate_limit):
    fixture_missing = load_fixture("missing_page.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=fixture_missing), Response(200, json=fixture_missing)]
    )

    result = await get_articles_async(
        ["Nonexistent page qwerty12345", "Another missing page"],
        rate_limiter=no_rate_limit,
    )
    assert result.articles == []
    assert set(result.missing) == {"Nonexistent page qwerty12345", "Another missing page"}


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_single_title(no_rate_limit):
    fixture = load_fixture("article_response.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    result = await get_articles_async(
        ["Python (programming language)"],
        rate_limiter=no_rate_limit,
    )
    assert isinstance(result, ArticleBatch)
    assert len(result.articles) == 1
    assert result.articles[0].title == "Python (programming language)"
    assert result.missing == []


@respx.mock
@pytest.mark.asyncio
async def test_get_articles_empty_list(no_rate_limit):
    result = await get_articles_async([], rate_limiter=no_rate_limit)
    assert result.articles == []
    assert result.missing == []
    assert respx.calls.call_count == 0


@respx.mock
def test_get_articles_logs_warning_on_missing(no_rate_limit, caplog):
    fixture_good = load_fixture("article_response.json")
    fixture_missing = load_fixture("missing_page.json")

    def _dispatch(request):
        title = request.url.params.get("titles", "")
        if "Nonexistent" in title:
            return Response(200, json=fixture_missing)
        return Response(200, json=fixture_good)

    respx.get("https://en.wikipedia.org/w/api.php").mock(side_effect=_dispatch)

    with caplog.at_level(logging.WARNING, logger="wikipediacorpus.api._article"):
        result = get_articles(
            ["Python (programming language)", "Nonexistent page qwerty12345"],
            rate_limiter=no_rate_limit,
        )

    assert len(result.articles) == 1
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
                    "length": 200,
                }
            }
        },
    }
    fixture_missing = load_fixture("missing_page.json")

    def _dispatch(request):
        title = request.url.params.get("titles", "")
        if "Missing" in title:
            return Response(200, json=fixture_missing)
        if "JavaScript" in title:
            return Response(200, json=fixture_js)
        return Response(200, json=fixture_good)

    respx.get("https://en.wikipedia.org/w/api.php").mock(side_effect=_dispatch)

    result = await get_articles_async(
        ["Python (programming language)", "JavaScript", "Missing1", "Missing2"],
        rate_limiter=no_rate_limit,
    )
    assert len(result.articles) == 2
    titles = {a.title for a in result.articles}
    assert "Python (programming language)" in titles
    assert "JavaScript" in titles
    assert set(result.missing) == {"Missing1", "Missing2"}


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


# ── Wikitext length and empty extract ────────────────────────────────────────


@respx.mock
def test_get_article_wikitext_length_populated(no_rate_limit):
    fixture = load_fixture("article_response.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    article = get_article(
        "Python (programming language)", rate_limiter=no_rate_limit
    )
    assert article.wikitext_length is not None
    assert article.wikitext_length == 350


@respx.mock
def test_get_article_wikitext_length_none_without_info(no_rate_limit):
    fixture = {
        "batchcomplete": "",
        "query": {
            "pages": {
                "11111": {
                    "pageid": 11111,
                    "ns": 0,
                    "title": "No Length",
                    "extract": "Some text here.",
                }
            }
        },
    }
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    article = get_article("No Length", rate_limiter=no_rate_limit)
    assert article.wikitext_length is None


@respx.mock
def test_get_article_warns_on_empty_extract(no_rate_limit, caplog):
    fixture = load_fixture("article_empty_extract.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    with caplog.at_level(logging.WARNING, logger="wikipediacorpus.api._article"):
        article = get_article("Empty Extract Article", rate_limiter=no_rate_limit)

    assert article.text == ""
    warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("empty extract" in m for m in warning_messages)
