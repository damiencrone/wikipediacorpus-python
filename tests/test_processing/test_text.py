"""Tests for text processing functions."""

from __future__ import annotations

from wikipediacorpus.processing._text import (
    cut_articles_at_headings,
    cut_at_headings,
    get_headings,
    split_text,
)

SAMPLE_TEXT = (
    "This is the lead section.\n"
    "\n== History ==\n"
    "Some history text.\n"
    "\n== Design philosophy ==\n"
    "Design text here.\n"
    "\n== See also ==\n"
    "Related links.\n"
    "\n== References ==\n"
    "Some references."
)


def test_get_headings():
    headings = get_headings(SAMPLE_TEXT)
    assert headings == ["History", "Design philosophy", "See also", "References"]


def test_get_headings_empty():
    assert get_headings("No headings here.") == []


def test_get_headings_with_spaces():
    text = "\n==  Spaced heading  ==\nContent"
    headings = get_headings(text)
    assert headings == ["Spaced heading"]


def test_split_text():
    sections = split_text(SAMPLE_TEXT)
    assert sections[0].heading == "Lead"
    assert "lead section" in sections[0].text
    assert sections[1].heading == "History"
    assert "history text" in sections[1].text
    assert len(sections) == 5


def test_split_text_no_headings():
    sections = split_text("Just a lead.")
    assert len(sections) == 1
    assert sections[0].heading == "Lead"
    assert sections[0].text == "Just a lead."


def test_cut_at_headings():
    result = cut_at_headings(SAMPLE_TEXT, ["See also"])
    assert "History" in result
    assert "Design philosophy" in result
    assert "See also" not in result
    assert "References" not in result


def test_cut_at_headings_multiple():
    result = cut_at_headings(SAMPLE_TEXT, ["Design philosophy"])
    assert "History" in result
    assert "Design philosophy" not in result


def test_cut_at_headings_not_found():
    result = cut_at_headings(SAMPLE_TEXT, ["Nonexistent"])
    assert result == SAMPLE_TEXT


def test_cut_at_headings_regex_safety():
    """Heading names with regex metacharacters should be escaped."""
    text = "\n== C++ ==\nContent after\n== Other ==\nMore"
    result = cut_at_headings(text, ["C++"])
    assert "C++" not in result
    assert "Other" not in result


def test_cut_articles_at_headings():
    articles = [SAMPLE_TEXT, SAMPLE_TEXT]
    results = cut_articles_at_headings(articles, ["See also"])
    assert len(results) == 2
    for r in results:
        assert "See also" not in r
        assert "History" in r


# ── Edge cases ────────────────────────────────────────────────────────────────


def test_get_headings_ignores_level3():
    """Level-3 headings (=== ... ===) should not be captured."""
    text = "\n=== Level 3 ===\nContent\n== Level 2 ==\nMore content"
    headings = get_headings(text)
    assert headings == ["Level 2"]
    assert "Level 3" not in headings


def test_split_text_leading_heading():
    """Text starting with a heading should have an empty lead section."""
    text = "\n== Heading ==\nBody text"
    sections = split_text(text)
    assert sections[0].heading == "Lead"
    assert sections[0].text.strip() == ""
    assert sections[1].heading == "Heading"
    assert "Body text" in sections[1].text


def test_cut_at_headings_empty_text():
    result = cut_at_headings("", ["See also"])
    assert result == ""


def test_cut_articles_at_headings_empty_list():
    result = cut_articles_at_headings([], ["See also"])
    assert result == []
