"""Tests for category member matrix construction."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from tests.conftest import load_fixture
from wikipediacorpus import get_category_members_matrix, get_category_members_matrix_async
from wikipediacorpus.models import Namespace


def _make_category_response(members: list[dict]) -> dict:
    return {"batchcomplete": "", "query": {"categorymembers": members}}


@respx.mock
def test_matrix_single_category(no_rate_limit):
    fixture = load_fixture("category_members.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    result = get_category_members_matrix(
        ["Programming languages"], rate_limiter=no_rate_limit
    )

    assert result.matrix.shape[0] == 1  # 1 category
    assert result.matrix.shape[1] == 3  # 3 members
    assert result.row_labels == ["Programming languages"]
    assert len(result.col_labels) == 3
    assert result.matrix.nnz == 3  # 3 non-zero entries


@respx.mock
def test_matrix_multiple_categories(no_rate_limit):
    members_a = _make_category_response([
        {"pageid": 1, "ns": 14, "title": "Category:Sub A"},
        {"pageid": 2, "ns": 14, "title": "Category:Sub B"},
    ])
    members_b = _make_category_response([
        {"pageid": 2, "ns": 14, "title": "Category:Sub B"},
        {"pageid": 3, "ns": 14, "title": "Category:Sub C"},
    ])

    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[Response(200, json=members_a), Response(200, json=members_b)]
    )

    result = get_category_members_matrix(
        ["Cat A", "Cat B"], rate_limiter=no_rate_limit
    )

    assert result.matrix.shape == (2, 3)  # 2 categories, 3 unique members
    assert "Cat A" in result.row_labels
    assert "Cat B" in result.row_labels
    # Sub B appears in both -> shared column
    assert "Sub B" in result.col_labels


@respx.mock
def test_matrix_depth_2(no_rate_limit):
    # Depth 1: Cat A has Sub X, Sub Y
    depth1 = _make_category_response([
        {"pageid": 10, "ns": 14, "title": "Category:Sub X"},
        {"pageid": 11, "ns": 14, "title": "Category:Sub Y"},
    ])
    # Depth 2: Sub X has Sub Z
    depth2_x = _make_category_response([
        {"pageid": 20, "ns": 14, "title": "Category:Sub Z"},
    ])
    # Depth 2: Sub Y is empty
    depth2_y = _make_category_response([])

    respx.get("https://en.wikipedia.org/w/api.php").mock(
        side_effect=[
            Response(200, json=depth1),
            Response(200, json=depth2_x),
            Response(200, json=depth2_y),
        ]
    )

    result = get_category_members_matrix(
        ["Cat A"], depth=2, rate_limiter=no_rate_limit
    )

    # 3 rows: Cat A, Sub X, Sub Y
    assert result.matrix.shape[0] == 3
    assert "Sub Z" in result.col_labels


def test_matrix_depth_gt1_requires_category_namespace():
    with pytest.raises(ValueError, match="depth > 1"):
        get_category_members_matrix(
            ["Test"], depth=2, namespace=Namespace.MAIN
        )


@respx.mock
@pytest.mark.asyncio
async def test_matrix_async(no_rate_limit):
    fixture = load_fixture("category_members.json")
    respx.get("https://en.wikipedia.org/w/api.php").mock(
        return_value=Response(200, json=fixture)
    )

    result = await get_category_members_matrix_async(
        ["Programming languages"], rate_limiter=no_rate_limit
    )

    assert result.matrix.shape[0] == 1
    assert result.matrix.shape[1] == 3
