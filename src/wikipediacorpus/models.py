"""Data models for wikipediacorpus."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
from scipy.sparse import csr_matrix


class LinkDirection(Enum):
    """Direction of Wikipedia page links."""

    INCOMING = "incoming"
    OUTGOING = "outgoing"


class Namespace(Enum):
    """MediaWiki namespace identifiers."""

    MAIN = 0
    CATEGORY = 14


@dataclass(frozen=True)
class Article:
    """A Wikipedia article."""

    title: str
    text: str
    pageid: int
    lang: str


@dataclass(frozen=True)
class Section:
    """A section within a Wikipedia article."""

    heading: str
    text: str


@dataclass(frozen=True)
class CategoryMember:
    """A member of a Wikipedia category."""

    pageid: int
    ns: int
    title: str


@dataclass(frozen=True)
class WikiLink:
    """A link to or from a Wikipedia page."""

    pageid: int
    ns: int
    title: str


@dataclass(frozen=True)
class HeadingFrequency:
    """A heading and its frequency count."""

    heading: str
    count: int


@dataclass
class CategoryMatrix:
    """A binary sparse matrix of category-member relationships.

    Rows are categories, columns are members.
    """

    matrix: csr_matrix
    row_labels: list[str]
    col_labels: list[str]


@dataclass
class LinkMatrix:
    """A binary sparse matrix of page-link adjacency.

    Rows are source pages, columns are target pages.
    """

    matrix: csr_matrix
    row_labels: list[str]
    col_labels: list[str]


@dataclass(frozen=True)
class SeedSimilarity:
    """Results of seed-page similarity computation."""

    scores: dict[str, float]
    page_weight: np.ndarray
    target_vec: np.ndarray
