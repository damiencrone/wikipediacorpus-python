"""Tests for data models."""

from wikipediacorpus.models import (
    Article,
    CategoryMember,
    HeadingFrequency,
    LinkDirection,
    Namespace,
    Section,
    WikiLink,
)


def test_article_frozen():
    a = Article(title="Test", text="body", pageid=1, lang="en")
    assert a.title == "Test"
    assert a.pageid == 1


def test_section_frozen():
    s = Section(heading="Intro", text="text")
    assert s.heading == "Intro"


def test_category_member():
    cm = CategoryMember(pageid=1, ns=14, title="Category:Foo")
    assert cm.ns == 14


def test_wiki_link():
    wl = WikiLink(pageid=2, ns=0, title="Bar")
    assert wl.title == "Bar"


def test_heading_frequency():
    hf = HeadingFrequency(heading="See also", count=42)
    assert hf.count == 42


def test_link_direction_values():
    assert LinkDirection.INCOMING.value == "incoming"
    assert LinkDirection.OUTGOING.value == "outgoing"


def test_namespace_values():
    assert Namespace.MAIN.value == 0
    assert Namespace.CATEGORY.value == 14
