"""HTTP client utilities for the MediaWiki API."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from ._rate_limiter import RateLimiter, _default_limiter
from .exceptions import APIError, HTTPError, PageNotFoundError

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BASE_DELAY = 1.0  # seconds

_TRANSIENT_EXC = (
    httpx.ReadError,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
)

_USER_AGENT = "wikipediacorpus/0.1.0 (https://github.com/wikipediacorpus; Python httpx)"


def _base_url(lang: str) -> str:
    return f"https://{lang}.wikipedia.org/w/api.php"


def get_client(**kwargs: Any) -> httpx.Client:
    """Create a sync httpx client with default headers."""
    kwargs.setdefault("headers", {"User-Agent": _USER_AGENT})
    kwargs.setdefault("timeout", 30.0)
    return httpx.Client(**kwargs)


def get_async_client(**kwargs: Any) -> httpx.AsyncClient:
    """Create an async httpx client with default headers."""
    kwargs.setdefault("headers", {"User-Agent": _USER_AGENT})
    kwargs.setdefault("timeout", 30.0)
    return httpx.AsyncClient(**kwargs)


def _check_http_response(response: httpx.Response) -> None:
    """Raise HTTPError for non-2xx status codes."""
    if response.status_code >= 400:
        raise HTTPError(
            f"HTTP {response.status_code}: {response.reason_phrase}",
            status_code=response.status_code,
        )


def _check_api_response(
    data: dict[str, Any],
    *,
    check_missing: bool = False,
    title: str | None = None,
    lang: str = "en",
) -> None:
    """Check a MediaWiki API JSON response for errors."""
    if "error" in data:
        err = data["error"]
        raise APIError(
            message=err.get("info", "Unknown API error"),
            code=err.get("code", "unknown"),
            info=err.get("info", ""),
        )
    if check_missing and "query" in data and "pages" in data["query"]:
        pages = data["query"]["pages"]
        if isinstance(pages, dict):
            page = next(iter(pages.values()))
            if "missing" in page:
                raise PageNotFoundError(title=title or "", lang=lang)


def api_get(
    params: dict[str, Any],
    lang: str = "en",
    *,
    client: httpx.Client | None = None,
    rate_limiter: RateLimiter | None = None,
    check_missing: bool = False,
    title: str | None = None,
) -> dict[str, Any]:
    """Sync GET request to the MediaWiki API with retry on 429 / transient errors."""
    limiter = rate_limiter or _default_limiter

    url = _base_url(lang)
    close_client = client is None
    if client is None:
        client = get_client()
    try:
        for attempt in range(_MAX_RETRIES + 1):
            limiter.acquire()
            try:
                response = client.get(url, params=params)
            except _TRANSIENT_EXC as exc:
                if attempt == _MAX_RETRIES:
                    raise HTTPError(str(exc), status_code=0) from exc
                delay = _BASE_DELAY * (2 ** attempt)
                logger.warning("Transient error (attempt %d/%d), retrying in %.1fs: %s",
                               attempt + 1, _MAX_RETRIES, delay, exc)
                time.sleep(delay)
                continue

            if response.status_code == 429:
                if attempt == _MAX_RETRIES:
                    _check_http_response(response)
                retry_after = response.headers.get("retry-after")
                delay = float(retry_after) if retry_after else _BASE_DELAY * (2 ** attempt)
                logger.warning("Rate limited (attempt %d/%d), retrying in %.1fs",
                               attempt + 1, _MAX_RETRIES, delay)
                time.sleep(delay)
                continue

            _check_http_response(response)
            data: dict[str, Any] = response.json()
            _check_api_response(data, check_missing=check_missing, title=title, lang=lang)
            return data
        raise HTTPError("Unexpected retry loop exit", status_code=0)  # unreachable
    finally:
        if close_client:
            client.close()


async def api_get_async(
    params: dict[str, Any],
    lang: str = "en",
    *,
    client: httpx.AsyncClient | None = None,
    rate_limiter: RateLimiter | None = None,
    check_missing: bool = False,
    title: str | None = None,
) -> dict[str, Any]:
    """Async GET request to the MediaWiki API with retry on 429 / transient errors."""
    limiter = rate_limiter or _default_limiter

    url = _base_url(lang)
    close_client = client is None
    if client is None:
        client = get_async_client()
    try:
        for attempt in range(_MAX_RETRIES + 1):
            await limiter.acquire_async()
            try:
                response = await client.get(url, params=params)
            except _TRANSIENT_EXC as exc:
                if attempt == _MAX_RETRIES:
                    raise HTTPError(str(exc), status_code=0) from exc
                delay = _BASE_DELAY * (2 ** attempt)
                logger.warning("Transient error (attempt %d/%d), retrying in %.1fs: %s",
                               attempt + 1, _MAX_RETRIES, delay, exc)
                await asyncio.sleep(delay)
                continue

            if response.status_code == 429:
                if attempt == _MAX_RETRIES:
                    _check_http_response(response)
                retry_after = response.headers.get("retry-after")
                delay = float(retry_after) if retry_after else _BASE_DELAY * (2 ** attempt)
                logger.warning("Rate limited (attempt %d/%d), retrying in %.1fs",
                               attempt + 1, _MAX_RETRIES, delay)
                await asyncio.sleep(delay)
                continue

            _check_http_response(response)
            data: dict[str, Any] = response.json()
            _check_api_response(data, check_missing=check_missing, title=title, lang=lang)
            return data
        raise HTTPError("Unexpected retry loop exit", status_code=0)  # unreachable
    finally:
        if close_client:
            await client.aclose()
