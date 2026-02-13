"""Build a category-member sparse matrix."""

from __future__ import annotations

import asyncio
import logging

import httpx
from scipy.sparse import coo_matrix
from tqdm import tqdm

from .._http import get_async_client
from .._rate_limiter import RateLimiter
from ..models import CategoryMatrix, Namespace
from ._category import get_category_members, get_category_members_async

logger = logging.getLogger(__name__)


def _strip_category_prefix(title: str) -> str:
    if title.startswith("Category:"):
        return title[len("Category:"):]
    return title


def _build_matrix(member_map: dict[str, list[str]]) -> CategoryMatrix:
    """Construct a CSR sparse matrix from a category -> members mapping."""
    logger.info("Constructing category member matrix")
    row_labels = list(member_map.keys())
    all_members = sorted({m for members in member_map.values() for m in members})
    col_index = {name: i for i, name in enumerate(all_members)}

    rows: list[int] = []
    cols: list[int] = []
    for i, category in enumerate(row_labels):
        for member in member_map[category]:
            if member in col_index:
                rows.append(i)
                cols.append(col_index[member])

    data = [1] * len(rows)
    mat = coo_matrix(
        (data, (rows, cols)),
        shape=(len(row_labels), len(all_members)),
    ).tocsr()

    return CategoryMatrix(matrix=mat, row_labels=row_labels, col_labels=all_members)


def get_category_members_matrix(
    categories: list[str],
    depth: int = 1,
    lang: str = "en",
    namespace: Namespace = Namespace.CATEGORY,
    *,
    client: httpx.Client | None = None,
    rate_limiter: RateLimiter | None = None,
) -> CategoryMatrix:
    """Build a binary sparse matrix of category-member relationships.

    Parameters
    ----------
    categories : list[str]
        Category names to query.
    depth : int
        Levels of subcategory hierarchy to traverse (default 1).
    lang : str
        Language code (default ``"en"``).
    namespace : Namespace
        Namespace to retrieve (default ``Namespace.CATEGORY``).
    client : httpx.Client, optional
        Reusable HTTP client.
    rate_limiter : RateLimiter, optional
        Custom rate limiter.

    Returns
    -------
    CategoryMatrix
        Sparse matrix with category rows and member columns.
    """
    if depth > 1 and namespace != Namespace.CATEGORY:
        raise ValueError("depth > 1 only applies to namespace CATEGORY (14)")
    if depth > 3:
        logger.warning("depth > 3 may return too many results to be useful")

    member_map: dict[str, list[str]] = {}

    # Depth 1: fetch initial categories
    for cat in tqdm(categories, desc="Fetching categories (depth 1)", disable=len(categories) < 3):
        members = get_category_members(
            cat, lang, namespace, client=client, rate_limiter=rate_limiter,
        )
        member_map[_strip_category_prefix(cat)] = [
            _strip_category_prefix(m.title) for m in members
        ]

    # BFS for deeper levels
    for d in range(2, depth + 1):
        # Find categories we haven't fetched yet
        all_members = {m for members in member_map.values() for m in members}
        to_fetch = [m for m in all_members if m not in member_map]
        if not to_fetch:
            break

        logger.info("Retrieving members at depth %d (%d categories)", d, len(to_fetch))
        for cat in tqdm(to_fetch, desc=f"Fetching categories (depth {d})"):
            members = get_category_members(
                cat, lang, namespace, client=client, rate_limiter=rate_limiter,
            )
            member_map[cat] = [
                _strip_category_prefix(m.title) for m in members
            ]

    return _build_matrix(member_map)


async def get_category_members_matrix_async(
    categories: list[str],
    depth: int = 1,
    lang: str = "en",
    namespace: Namespace = Namespace.CATEGORY,
    *,
    max_concurrency: int = 4,
    rate_limiter: RateLimiter | None = None,
) -> CategoryMatrix:
    """Async version of :func:`get_category_members_matrix`.

    Fetches categories at each depth level concurrently.
    """
    if depth > 1 and namespace != Namespace.CATEGORY:
        raise ValueError("depth > 1 only applies to namespace CATEGORY (14)")
    if depth > 3:
        logger.warning("depth > 3 may return too many results to be useful")

    member_map: dict[str, list[str]] = {}
    sem = asyncio.Semaphore(max_concurrency)

    async def _fetch(cat: str, client: httpx.AsyncClient) -> tuple[str, list[str]]:
        async with sem:
            members = await get_category_members_async(
                cat, lang, namespace, client=client, rate_limiter=rate_limiter,
            )
            return _strip_category_prefix(cat), [
                _strip_category_prefix(m.title) for m in members
            ]

    async with get_async_client() as client:
        # Depth 1
        tasks = [_fetch(cat, client) for cat in categories]
        for result in await asyncio.gather(*tasks):
            cat_name, members = result
            member_map[cat_name] = members

        # BFS deeper levels
        for d in range(2, depth + 1):
            all_members = {m for members in member_map.values() for m in members}
            to_fetch = [m for m in all_members if m not in member_map]
            if not to_fetch:
                break

            logger.info("Retrieving members at depth %d (%d categories)", d, len(to_fetch))
            tasks = [_fetch(cat, client) for cat in to_fetch]
            for result in await asyncio.gather(*tasks):
                cat_name, members = result
                member_map[cat_name] = members

    return _build_matrix(member_map)
