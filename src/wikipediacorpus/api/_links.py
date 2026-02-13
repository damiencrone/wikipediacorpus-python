"""Retrieve incoming or outgoing links for a Wikipedia page."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .._http import api_get, api_get_async
from .._rate_limiter import RateLimiter
from ..models import LinkDirection, WikiLink

logger = logging.getLogger(__name__)


def _make_params(page: str, direction: LinkDirection, namespaces: list[int]) -> dict[str, str]:
    base: dict[str, str] = {
        "action": "query",
        "format": "json",
        "titles": page,  # Fixed: R bug used the literal string "page"
    }
    ns_str = "|".join(str(ns) for ns in namespaces)

    if direction == LinkDirection.INCOMING:
        base["prop"] = "linkshere"
        base["lhprop"] = "pageid|title"
        base["lhlimit"] = "max"
        base["lhnamespace"] = ns_str
    else:
        base["prop"] = "links"
        base["plnamespace"] = ns_str
        base["pllimit"] = "max"

    return base


def _parse_links(data: dict[str, Any], direction: LinkDirection) -> list[WikiLink]:
    page = next(iter(data["query"]["pages"].values()))
    key = "linkshere" if direction == LinkDirection.INCOMING else "links"
    raw = page.get(key, [])
    return [
        WikiLink(pageid=link.get("pageid", 0), ns=link["ns"], title=link["title"])
        for link in raw
    ]


def get_links(
    page: str,
    direction: LinkDirection = LinkDirection.OUTGOING,
    lang: str = "en",
    namespaces: list[int] | None = None,
    *,
    client: httpx.Client | None = None,
    rate_limiter: RateLimiter | None = None,
) -> list[WikiLink]:
    """Retrieve incoming or outgoing links for a Wikipedia page.

    Parameters
    ----------
    page : str
        Title of the Wikipedia page.
    direction : LinkDirection
        ``INCOMING`` or ``OUTGOING`` (default).
    lang : str
        Language code (default ``"en"``).
    namespaces : list[int], optional
        Namespace IDs to filter (default ``[0]``).
    client : httpx.Client, optional
        Reusable HTTP client.
    rate_limiter : RateLimiter, optional
        Custom rate limiter.

    Returns
    -------
    list[WikiLink]
        The retrieved links.
    """
    if namespaces is None:
        namespaces = [0]
    logger.info("Retrieving %s links for: %s", direction.value, page)

    params = _make_params(page, direction, namespaces)
    links: list[WikiLink] = []

    data = api_get(params, lang, client=client, rate_limiter=rate_limiter)
    links.extend(_parse_links(data, direction))

    continue_key = "lhcontinue" if direction == LinkDirection.INCOMING else "plcontinue"
    while "continue" in data and continue_key in data["continue"]:
        params[continue_key] = data["continue"][continue_key]
        data = api_get(params, lang, client=client, rate_limiter=rate_limiter)
        links.extend(_parse_links(data, direction))

    return links


async def get_links_async(
    page: str,
    direction: LinkDirection = LinkDirection.OUTGOING,
    lang: str = "en",
    namespaces: list[int] | None = None,
    *,
    client: httpx.AsyncClient | None = None,
    rate_limiter: RateLimiter | None = None,
) -> list[WikiLink]:
    """Async version of :func:`get_links`."""
    if namespaces is None:
        namespaces = [0]
    logger.info("Retrieving %s links for: %s", direction.value, page)

    params = _make_params(page, direction, namespaces)
    links: list[WikiLink] = []

    data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
    links.extend(_parse_links(data, direction))

    continue_key = "lhcontinue" if direction == LinkDirection.INCOMING else "plcontinue"
    while "continue" in data and continue_key in data["continue"]:
        params[continue_key] = data["continue"][continue_key]
        data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
        links.extend(_parse_links(data, direction))

    return links
