"""Retrieve Wikipedia article text."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from tqdm.asyncio import tqdm as atqdm

from .._http import api_get, api_get_async, get_async_client
from .._rate_limiter import RateLimiter
from ..exceptions import PageNotFoundError
from ..models import Article, ArticleBatch

logger = logging.getLogger(__name__)


def _make_params(title: str) -> dict[str, str]:
    return {
        "action": "query",
        "format": "json",
        "prop": "extracts|info",
        "explaintext": "1",
        "titles": title,
    }


def _parse_article(data: dict[str, Any], title: str, lang: str) -> Article:
    page = next(iter(data["query"]["pages"].values()))
    text = page.get("extract", "")
    wikitext_length: int | None = page.get("length")

    if "missing" not in page and not text:
        logger.warning("Page '%s' exists but has an empty extract", page.get("title", title))

    possibly_truncated = False
    if text.endswith("..."):
        possibly_truncated = True
    elif wikitext_length is not None and wikitext_length > 0 and len(text) < wikitext_length * 0.5:
        possibly_truncated = True

    if possibly_truncated:
        logger.warning(
            "Article '%s' may be truncated (extract length=%d, wikitext_length=%s)",
            page.get("title", title), len(text), wikitext_length,
        )

    return Article(
        title=page.get("title", title),
        text=text,
        pageid=page.get("pageid", -1),
        lang=lang,
        possibly_truncated=possibly_truncated,
        wikitext_length=wikitext_length,
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
    max_concurrency: int = 4,
    rate_limiter: RateLimiter | None = None,
) -> ArticleBatch:
    """Fetch multiple articles concurrently."""
    sem = asyncio.Semaphore(max_concurrency)
    missing: list[str] = []

    async def _fetch(title: str, client: httpx.AsyncClient) -> Article | None:
        async with sem:
            try:
                return await get_article_async(
                    title, lang, client=client, rate_limiter=rate_limiter,
                )
            except PageNotFoundError:
                logger.warning("Skipping missing page: '%s' (lang=%s)", title, lang)
                missing.append(title)
                return None

    async with get_async_client() as client:
        tasks = [_fetch(t, client) for t in titles]
        raw_results: list[Article | None] = []
        for coro in atqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching articles"):
            raw_results.append(await coro)

    results = [r for r in raw_results if r is not None]
    skipped = len(raw_results) - len(results)
    if skipped:
        logger.warning(
            "Skipped %d missing page(s) out of %d requested", skipped, len(titles),
        )
    return ArticleBatch(articles=results, missing=missing)


def get_articles(
    titles: list[str],
    lang: str = "en",
    *,
    max_concurrency: int = 4,
    rate_limiter: RateLimiter | None = None,
) -> ArticleBatch:
    """Retrieve multiple articles concurrently (sync wrapper).

    Parameters
    ----------
    titles : list[str]
        Article titles to fetch.
    lang : str
        Language code (default ``"en"``).
    max_concurrency : int
        Maximum number of concurrent requests (default 4).
    rate_limiter : RateLimiter, optional
        Custom rate limiter instance.

    Returns
    -------
    ArticleBatch
        The fetched articles and list of missing page titles.
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
    max_concurrency: int = 4,
    rate_limiter: RateLimiter | None = None,
) -> ArticleBatch:
    """Retrieve multiple articles concurrently (async).

    Parameters
    ----------
    titles : list[str]
        Article titles to fetch.
    lang : str
        Language code (default ``"en"``).
    max_concurrency : int
        Maximum number of concurrent requests (default 4).
    rate_limiter : RateLimiter, optional
        Custom rate limiter instance.

    Returns
    -------
    ArticleBatch
        The fetched articles and list of missing page titles.
    """
    return await _get_articles_async_impl(
        titles, lang, max_concurrency=max_concurrency, rate_limiter=rate_limiter,
    )
