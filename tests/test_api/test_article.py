"""Tests for article retrieval."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus import get_article, get_article_async
from wikipediacorpus.exceptions import PageNotFoundError


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
