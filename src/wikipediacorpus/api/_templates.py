"""Retrieve templates transcluded on a Wikipedia page."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .._http import api_get, api_get_async
from .._rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


def _make_params(page: str) -> dict[str, str]:
    return {
        "action": "query",
        "format": "json",
        "prop": "templates",
        "titles": page,
        "tlnamespace": "10",
        "tllimit": "max",
    }


def _parse_templates(data: dict[str, Any]) -> list[str]:
    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()))
    return [tl["title"] for tl in page.get("templates", [])]


def get_templates(
    page: str,
    lang: str = "en",
    *,
    client: httpx.Client | None = None,
    rate_limiter: RateLimiter | None = None,
) -> list[str]:
    """Retrieve templates transcluded on a Wikipedia page.

    Only returns templates in namespace 10 (``Template:``).

    Parameters
    ----------
    page : str
        Title of the Wikipedia page.
    lang : str
        Language code (default ``"en"``).
    client : httpx.Client, optional
        Reusable HTTP client.
    rate_limiter : RateLimiter, optional
        Custom rate limiter.

    Returns
    -------
    list[str]
        Template titles (with ``Template:`` prefix).
    """
    logger.info("Retrieving templates for: %s", page)

    params = _make_params(page)
    templates: list[str] = []

    data = api_get(params, lang, client=client, rate_limiter=rate_limiter)
    templates.extend(_parse_templates(data))

    while "continue" in data and "tlcontinue" in data["continue"]:
        params["tlcontinue"] = data["continue"]["tlcontinue"]
        data = api_get(params, lang, client=client, rate_limiter=rate_limiter)
        templates.extend(_parse_templates(data))

    return templates


async def get_templates_async(
    page: str,
    lang: str = "en",
    *,
    client: httpx.AsyncClient | None = None,
    rate_limiter: RateLimiter | None = None,
) -> list[str]:
    """Async version of :func:`get_templates`."""
    logger.info("Retrieving templates for: %s", page)

    params = _make_params(page)
    templates: list[str] = []

    data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
    templates.extend(_parse_templates(data))

    while "continue" in data and "tlcontinue" in data["continue"]:
        params["tlcontinue"] = data["continue"]["tlcontinue"]
        data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
        templates.extend(_parse_templates(data))

    return templates
