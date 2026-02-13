"""Resolve Wikipedia page redirects."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from tqdm.asyncio import tqdm as atqdm

from .._http import api_get, api_get_async, get_async_client
from .._rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

_BATCH_SIZE = 50  # MediaWiki API accepts up to 50 titles per request


# ── Single redirect resolution ───────────────────────────────────────────────


def _make_redirect_params(title: str) -> dict[str, str]:
    return {
        "action": "query",
        "format": "json",
        "titles": title,
        "redirects": "",
    }


def _parse_redirect(data: dict[str, Any]) -> str | None:
    redirects = data.get("query", {}).get("redirects")
    if redirects:
        return redirects[-1]["to"]
    return None


def resolve_redirect(
    title: str,
    lang: str = "en",
    *,
    client: httpx.Client | None = None,
    rate_limiter: RateLimiter | None = None,
) -> str | None:
    """Check if a title is a redirect and return the destination.

    Parameters
    ----------
    title : str
        Wikipedia page title to check.
    lang : str
        Language code (default ``"en"``).
    client : httpx.Client, optional
        Reusable HTTP client.
    rate_limiter : RateLimiter, optional
        Custom rate limiter.

    Returns
    -------
    str or None
        Destination title if *title* is a redirect, else ``None``.
    """
    logger.info("Checking redirect status for: %s", title)
    params = _make_redirect_params(title)
    data = api_get(params, lang, client=client, rate_limiter=rate_limiter)
    return _parse_redirect(data)


async def resolve_redirect_async(
    title: str,
    lang: str = "en",
    *,
    client: httpx.AsyncClient | None = None,
    rate_limiter: RateLimiter | None = None,
) -> str | None:
    """Async version of :func:`resolve_redirect`."""
    logger.info("Checking redirect status for: %s", title)
    params = _make_redirect_params(title)
    data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
    return _parse_redirect(data)


# ── Batch redirect resolution ────────────────────────────────────────────────


def _make_batch_redirect_params(titles: list[str]) -> dict[str, str]:
    return {
        "action": "query",
        "format": "json",
        "titles": "|".join(titles),
        "redirects": "",
    }


def _parse_batch_redirects(
    data: dict[str, Any], titles: list[str],
) -> dict[str, str | None]:
    """Parse batch redirect response into a title -> destination mapping."""
    redirect_map: dict[str, str] = {}
    for rd in data.get("query", {}).get("redirects", []):
        redirect_map[rd["from"]] = rd["to"]

    # Also handle normalized titles (e.g. lowercase -> canonical)
    normalize_map: dict[str, str] = {}
    for norm in data.get("query", {}).get("normalized", []):
        normalize_map[norm["from"]] = norm["to"]

    result: dict[str, str | None] = {}
    for title in titles:
        canonical = normalize_map.get(title, title)
        destination = redirect_map.get(canonical)
        # Chase redirect chains: A→B→C should resolve to C
        while destination in redirect_map:
            destination = redirect_map[destination]
        result[title] = destination
    return result


async def _resolve_redirects_async_impl(
    titles: list[str],
    lang: str = "en",
    *,
    max_concurrency: int = 4,
    rate_limiter: RateLimiter | None = None,
) -> dict[str, str | None]:
    """Resolve redirects for many titles concurrently."""
    # Split into batches of _BATCH_SIZE
    batches = [titles[i:i + _BATCH_SIZE] for i in range(0, len(titles), _BATCH_SIZE)]
    sem = asyncio.Semaphore(max_concurrency)

    async def _fetch_batch(
        batch: list[str], client: httpx.AsyncClient,
    ) -> dict[str, str | None]:
        async with sem:
            params = _make_batch_redirect_params(batch)
            data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
            return _parse_batch_redirects(data, batch)

    result: dict[str, str | None] = {}
    async with get_async_client() as client:
        tasks = [_fetch_batch(batch, client) for batch in batches]
        for coro in atqdm(
            asyncio.as_completed(tasks), total=len(tasks),
            desc="Resolving redirects", disable=len(batches) < 3,
        ):
            batch_result = await coro
            result.update(batch_result)

    return result


def resolve_redirects(
    titles: list[str],
    lang: str = "en",
    *,
    max_concurrency: int = 4,
    rate_limiter: RateLimiter | None = None,
) -> dict[str, str | None]:
    """Resolve redirects for multiple titles (sync wrapper).

    Batches titles into groups of 50 (the MediaWiki API limit) and
    resolves them concurrently. The API automatically chases redirect
    chains, so multi-hop redirects are resolved in a single request.

    Parameters
    ----------
    titles : list[str]
        Page titles to check.
    lang : str
        Language code (default ``"en"``).
    max_concurrency : int
        Maximum concurrent API requests (default 4).
    rate_limiter : RateLimiter, optional
        Custom rate limiter.

    Returns
    -------
    dict[str, str | None]
        Mapping from each input title to its redirect destination,
        or ``None`` if the title is not a redirect.
    """
    return asyncio.run(
        _resolve_redirects_async_impl(
            titles, lang, max_concurrency=max_concurrency, rate_limiter=rate_limiter,
        )
    )


async def resolve_redirects_async(
    titles: list[str],
    lang: str = "en",
    *,
    max_concurrency: int = 4,
    rate_limiter: RateLimiter | None = None,
) -> dict[str, str | None]:
    """Async version of :func:`resolve_redirects`."""
    return await _resolve_redirects_async_impl(
        titles, lang, max_concurrency=max_concurrency, rate_limiter=rate_limiter,
    )


# ── Pages that redirect TO a given page ──────────────────────────────────────


def _make_redirects_to_params(page: str) -> dict[str, str]:
    return {
        "action": "query",
        "format": "json",
        "prop": "redirects",
        "titles": page,
        "rdlimit": "max",
    }


def _parse_redirects_to(data: dict[str, Any]) -> list[str]:
    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()))
    return [rd["title"] for rd in page.get("redirects", [])]


def get_redirects_to(
    page: str,
    lang: str = "en",
    *,
    client: httpx.Client | None = None,
    rate_limiter: RateLimiter | None = None,
) -> list[str]:
    """Find all pages that redirect to a given page.

    Parameters
    ----------
    page : str
        Title of the target page.
    lang : str
        Language code (default ``"en"``).
    client : httpx.Client, optional
        Reusable HTTP client.
    rate_limiter : RateLimiter, optional
        Custom rate limiter.

    Returns
    -------
    list[str]
        Titles of pages that redirect to *page*.
    """
    logger.info("Retrieving redirects to: %s", page)

    params = _make_redirects_to_params(page)
    redirects: list[str] = []

    data = api_get(params, lang, client=client, rate_limiter=rate_limiter)
    redirects.extend(_parse_redirects_to(data))

    while "continue" in data and "rdcontinue" in data["continue"]:
        params["rdcontinue"] = data["continue"]["rdcontinue"]
        data = api_get(params, lang, client=client, rate_limiter=rate_limiter)
        redirects.extend(_parse_redirects_to(data))

    return redirects


async def get_redirects_to_async(
    page: str,
    lang: str = "en",
    *,
    client: httpx.AsyncClient | None = None,
    rate_limiter: RateLimiter | None = None,
) -> list[str]:
    """Async version of :func:`get_redirects_to`."""
    logger.info("Retrieving redirects to: %s", page)

    params = _make_redirects_to_params(page)
    redirects: list[str] = []

    data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
    redirects.extend(_parse_redirects_to(data))

    while "continue" in data and "rdcontinue" in data["continue"]:
        params["rdcontinue"] = data["continue"]["rdcontinue"]
        data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
        redirects.extend(_parse_redirects_to(data))

    return redirects
