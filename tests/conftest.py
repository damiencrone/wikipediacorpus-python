"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from wikipediacorpus._rate_limiter import RateLimiter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, Any]:
    """Load a JSON fixture file."""
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture()
def no_rate_limit() -> RateLimiter:
    """A rate limiter that effectively doesn't limit."""
    return RateLimiter(rate=10_000, burst=10_000)


@pytest.fixture()
def article_response() -> dict[str, Any]:
    return load_fixture("article_response.json")


@pytest.fixture()
def missing_page_response() -> dict[str, Any]:
    return load_fixture("missing_page.json")


@pytest.fixture()
def category_members_response() -> dict[str, Any]:
    return load_fixture("category_members.json")


@pytest.fixture()
def category_continue_response() -> dict[str, Any]:
    return load_fixture("category_continue.json")


@pytest.fixture()
def links_outgoing_response() -> dict[str, Any]:
    return load_fixture("links_outgoing.json")


@pytest.fixture()
def links_incoming_response() -> dict[str, Any]:
    return load_fixture("links_incoming.json")
