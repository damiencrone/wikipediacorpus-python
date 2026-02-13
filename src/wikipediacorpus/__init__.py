"""wikipediacorpus - Retrieve and process Wikipedia article text."""

from ._version import __version__
from .api._article import get_article, get_article_async, get_articles, get_articles_async
from .api._category import (
    get_category_members,
    get_category_members_async,
    get_page_categories,
    get_page_categories_async,
)
from .api._links import get_links, get_links_async
from .api._matrix import get_category_members_matrix, get_category_members_matrix_async
from .api._redirects import (
    get_redirects_to,
    get_redirects_to_async,
    resolve_redirect,
    resolve_redirect_async,
    resolve_redirects,
    resolve_redirects_async,
)
from .api._templates import get_templates, get_templates_async
from .exceptions import APIError, HTTPError, PageNotFoundError, WikipediaCorpusError
from .models import (
    Article,
    CategoryMatrix,
    CategoryMember,
    HeadingFrequency,
    LinkDirection,
    LinkMatrix,
    Namespace,
    Section,
    SeedSimilarity,
    WikiLink,
)
from .processing._plot import plot_heading_frequency
from .processing._text import (
    cut_articles_at_headings,
    cut_at_headings,
    get_headings,
    split_text,
)

__all__ = [
    "__version__",
    # API - Articles
    "get_article",
    "get_article_async",
    "get_articles",
    "get_articles_async",
    # API - Categories
    "get_category_members",
    "get_category_members_async",
    "get_page_categories",
    "get_page_categories_async",
    # API - Links
    "get_links",
    "get_links_async",
    # API - Matrix
    "get_category_members_matrix",
    "get_category_members_matrix_async",
    # API - Redirects
    "resolve_redirect",
    "resolve_redirect_async",
    "resolve_redirects",
    "resolve_redirects_async",
    "get_redirects_to",
    "get_redirects_to_async",
    # API - Templates
    "get_templates",
    "get_templates_async",
    # Processing
    "get_headings",
    "split_text",
    "cut_at_headings",
    "cut_articles_at_headings",
    "plot_heading_frequency",
    # Models
    "Article",
    "CategoryMatrix",
    "CategoryMember",
    "HeadingFrequency",
    "LinkDirection",
    "LinkMatrix",
    "Namespace",
    "Section",
    "SeedSimilarity",
    "WikiLink",
    # Exceptions
    "WikipediaCorpusError",
    "APIError",
    "PageNotFoundError",
    "HTTPError",
]
