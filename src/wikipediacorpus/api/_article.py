"""Retrieve Wikipedia article text."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from tqdm.asyncio import tqdm as atqdm

from .._http import api_get, api_get_async, get_async_client
from .._rate_limiter import RateLimiter
from ..models import Article

logger = logging.getLogger(__name__)


def _make_params(title: str) -> dict[str, str]:
    return {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": "1",
        "titles": title,
    }


def _parse_article(data: dict[str, Any], title: str, lang: str) -> Article:
    page = next(iter(data["query"]["pages"].values()))
    return Article(
        title=page.get("title", title),
        text=page.get("extract", ""),
        pageid=page.get("pageid", -1),
        lang=lang,
    )


def get_article(
    title: str,
    lang: str = "en",
    *,
    client: httpx.Client | None = None,
    rate_limiter: RateLimiter | None = None,
) -> Article:
    """Retrieve the plaintext of a single Wikipedia article.

    Parameters
    ----------
    title : str
        Title of the Wikipedia article.
    lang : str
        Language code (default ``"en"``).
    client : httpx.Client, optional
        Reusable HTTP client for connection pooling.
    rate_limiter : RateLimiter, optional
        Custom rate limiter instance.

    Returns
    -------
    Article
        The article data.
    """
    logger.info("Retrieving text for article: %s", title)
    params = _make_params(title)
    data = api_get(
        params, lang, client=client, rate_limiter=rate_limiter,
        check_missing=True, title=title,
    )
    return _parse_article(data, title, lang)


async def get_article_async(
    title: str,
    lang: str = "en",
    *,
    client: httpx.AsyncClient | None = None,
    rate_limiter: RateLimiter | None = None,
) -> Article:
    """Async version of :func:`get_article`."""
    logger.info("Retrieving text for article: %s", title)
    params = _make_params(title)
    data = await api_get_async(
        params, lang, client=client, rate_limiter=rate_limiter,
        check_missing=True, title=title,
    )
    return _parse_article(data, title, lang)


async def _get_articles_async_impl(
    titles: list[str],
    lang: str = "en",
    *,
    max_concurrency: int = 10,
    rate_limiter: RateLimiter | None = None,
) -> list[Article]:
    """Fetch multiple articles concurrently."""
    sem = asyncio.Semaphore(max_concurrency)

    async def _fetch(title: str, client: httpx.AsyncClient) -> Article:
        async with sem:
            return await get_article_async(
                title, lang, client=client, rate_limiter=rate_limiter,
            )

    async with get_async_client() as client:
        tasks = [_fetch(t, client) for t in titles]
        results: list[Article] = []
        for coro in atqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching articles"):
            results.append(await coro)
    return results


def get_articles(
    titles: list[str],
    lang: str = "en",
    *,
    max_concurrency: int = 10,
    rate_limiter: RateLimiter | None = None,
) -> list[Article]:
    """Retrieve multiple articles concurrently (sync wrapper).

    Parameters
    ----------
    titles : list[str]
        Article titles to fetch.
    lang : str
        Language code (default ``"en"``).
    max_concurrency : int
        Maximum number of concurrent requests (default 10).
    rate_limiter : RateLimiter, optional
        Custom rate limiter instance.

    Returns
    -------
    list[Article]
        The fetched articles (order may differ from input).
    """
    return asyncio.run(
        _get_articles_async_impl(
            titles, lang, max_concurrency=max_concurrency, rate_limiter=rate_limiter,
        )
    )


async def get_articles_async(
    titles: list[str],
    lang: str = "en",
    *,
    max_concurrency: int = 10,
    rate_limiter: RateLimiter | None = None,
) -> list[Article]:
    """Retrieve multiple articles concurrently (async).

    Parameters
    ----------
    titles : list[str]
        Article titles to fetch.
    lang : str
        Language code (default ``"en"``).
    max_concurrency : int
        Maximum number of concurrent requests (default 10).
    rate_limiter : RateLimiter, optional
        Custom rate limiter instance.

    Returns
    -------
    list[Article]
        The fetched articles (order may differ from input).
    """
    return await _get_articles_async_impl(
        titles, lang, max_concurrency=max_concurrency, rate_limiter=rate_limiter,
    )
