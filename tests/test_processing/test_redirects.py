"""Tests for redirect overwriting utilities."""

from __future__ import annotations

from wikipediacorpus.processing._redirects import overwrite_redirects


def test_overwrite_redirects_basic():
    titles = ["Morals", "Ethics", "Justice"]
    redirect_map = {"Morals": "Morality"}

    result = overwrite_redirects(titles, redirect_map)
    assert result == ["Morality", "Ethics", "Justice"]


def test_overwrite_redirects_dedup():
    """If redirect creates duplicates, they should be removed."""
    titles = ["Morals", "Morality", "Justice"]
    redirect_map = {"Morals": "Morality"}

    result = overwrite_redirects(titles, redirect_map)
    assert result == ["Morality", "Justice"]


def test_overwrite_redirects_no_redirects():
    titles = ["Alpha", "Beta", "Gamma"]
    redirect_map: dict[str, str] = {}

    result = overwrite_redirects(titles, redirect_map)
    assert result == ["Alpha", "Beta", "Gamma"]


def test_overwrite_redirects_all_redirects():
    titles = ["A", "B"]
    redirect_map = {"A": "X", "B": "Y"}

    result = overwrite_redirects(titles, redirect_map)
    assert result == ["X", "Y"]


def test_overwrite_redirects_preserves_order():
    titles = ["C", "A", "B"]
    redirect_map = {"A": "Z"}

    result = overwrite_redirects(titles, redirect_map)
    assert result == ["C", "Z", "B"]


def test_overwrite_redirects_multiple_to_same():
    """Multiple redirects pointing to the same destination."""
    titles = ["Redirect1", "Redirect2", "Other"]
    redirect_map = {"Redirect1": "Same", "Redirect2": "Same"}

    result = overwrite_redirects(titles, redirect_map)
    assert result == ["Same", "Other"]


def test_overwrite_redirects_empty():
    result = overwrite_redirects([], {})
    assert result == []
