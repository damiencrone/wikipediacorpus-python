"""Retrieve Wikipedia category members."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .._http import api_get, api_get_async
from .._rate_limiter import RateLimiter
from ..models import CategoryMember, Namespace

logger = logging.getLogger(__name__)


def _normalize_category(category: str) -> str:
    """Ensure category title has the ``Category:`` prefix."""
    if not category.startswith("Category:"):
        return f"Category:{category}"
    return category


def _cmtype_for_namespace(namespace: Namespace) -> str:
    if namespace == Namespace.MAIN:
        return "page"
    if namespace == Namespace.CATEGORY:
        return "subcat"
    raise ValueError(f"Unsupported namespace: {namespace}")


def _make_params(category: str, namespace: Namespace) -> dict[str, str]:
    cmtitle = _normalize_category(category)
    return {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": cmtitle,
        "cmtype": _cmtype_for_namespace(namespace),
        "cmlimit": "max",
        "cmnamespace": str(namespace.value),
    }


def _parse_members(data: dict[str, Any]) -> list[CategoryMember]:
    raw = data.get("query", {}).get("categorymembers", [])
    return [
        CategoryMember(pageid=m["pageid"], ns=m["ns"], title=m["title"])
        for m in raw
    ]


def get_category_members(
    category: str,
    lang: str = "en",
    namespace: Namespace = Namespace.CATEGORY,
    *,
    client: httpx.Client | None = None,
    rate_limiter: RateLimiter | None = None,
) -> list[CategoryMember]:
    """Retrieve pages or subcategories within a category.

    Parameters
    ----------
    category : str
        Category name (with or without ``Category:`` prefix).
    lang : str
        Language code (default ``"en"``).
    namespace : Namespace
        Namespace to filter (default ``Namespace.CATEGORY``).
    client : httpx.Client, optional
        Reusable HTTP client.
    rate_limiter : RateLimiter, optional
        Custom rate limiter.

    Returns
    -------
    list[CategoryMember]
        Members of the category.
    """
    cmtitle = _normalize_category(category)
    logger.info("Retrieving %ss for %s", _cmtype_for_namespace(namespace), cmtitle)

    params = _make_params(category, namespace)
    members: list[CategoryMember] = []

    data = api_get(params, lang, client=client, rate_limiter=rate_limiter)
    members.extend(_parse_members(data))

    while "continue" in data:
        params["cmcontinue"] = data["continue"]["cmcontinue"]
        data = api_get(params, lang, client=client, rate_limiter=rate_limiter)
        members.extend(_parse_members(data))

    return members


async def get_category_members_async(
    category: str,
    lang: str = "en",
    namespace: Namespace = Namespace.CATEGORY,
    *,
    client: httpx.AsyncClient | None = None,
    rate_limiter: RateLimiter | None = None,
) -> list[CategoryMember]:
    """Async version of :func:`get_category_members`."""
    cmtitle = _normalize_category(category)
    logger.info("Retrieving %ss for %s", _cmtype_for_namespace(namespace), cmtitle)

    params = _make_params(category, namespace)
    members: list[CategoryMember] = []

    data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
    members.extend(_parse_members(data))

    while "continue" in data:
        params["cmcontinue"] = data["continue"]["cmcontinue"]
        data = await api_get_async(params, lang, client=client, rate_limiter=rate_limiter)
        members.extend(_parse_members(data))

    return members
