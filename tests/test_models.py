"""Tests for data models."""

import dataclasses

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from wikipediacorpus.models import (
    Article,
    CategoryMember,
    HeadingFrequency,
    LinkDirection,
    LinkMatrix,
    Namespace,
    Section,
    SeedSimilarity,
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


def test_link_matrix():
    mat = csr_matrix([[1, 0], [1, 1]])
    lm = LinkMatrix(matrix=mat, row_labels=["A", "B"], col_labels=["X", "Y"])
    assert lm.row_labels == ["A", "B"]
    assert lm.col_labels == ["X", "Y"]
    assert lm.matrix.nnz == 3


def test_seed_similarity():
    ss = SeedSimilarity(
        scores={"A": 0.5, "B": 0.8},
        page_weight=np.array([1.0, 2.0]),
        target_vec=np.array([1.0, 2.0]),
    )
    assert ss.scores["A"] == 0.5
    assert len(ss.page_weight) == 2


# ── Frozen enforcement ────────────────────────────────────────────────────────


def test_article_is_frozen():
    a = Article(title="Test", text="body", pageid=1, lang="en")
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.title = "x"


def test_section_is_frozen():
    s = Section(heading="Intro", text="text")
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.heading = "x"


def test_category_member_is_frozen():
    cm = CategoryMember(pageid=1, ns=14, title="Category:Foo")
    with pytest.raises(dataclasses.FrozenInstanceError):
        cm.title = "x"


def test_wiki_link_is_frozen():
    wl = WikiLink(pageid=2, ns=0, title="Bar")
    with pytest.raises(dataclasses.FrozenInstanceError):
        wl.title = "x"


def test_heading_frequency_is_frozen():
    hf = HeadingFrequency(heading="See also", count=42)
    with pytest.raises(dataclasses.FrozenInstanceError):
        hf.count = 99


def test_seed_similarity_is_frozen():
    ss = SeedSimilarity(
        scores={"A": 0.5},
        page_weight=np.array([1.0]),
        target_vec=np.array([1.0]),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        ss.scores = {}
