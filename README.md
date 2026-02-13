# wikipediacorpus

A Python package for constructing Wikipedia-based text corpora via the MediaWiki API.

Provides tools for retrieving articles, navigating category hierarchies,
resolving redirects, building link matrices, and computing seed-page similarity
-- everything needed to assemble a topic-specific corpus from Wikipedia.

## Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from wikipediacorpus import get_article, get_articles, split_text

# Single article
article = get_article("Python (programming language)")
sections = split_text(article.text)

# Batch fetch (concurrent)
articles = get_articles(["Python (programming language)", "Java (programming language)"])

# Category members
from wikipediacorpus import get_category_members, Namespace
members = get_category_members("Programming languages", namespace=Namespace.MAIN)

# Resolve redirects (batch, chases chains)
from wikipediacorpus import resolve_redirects
redirects = resolve_redirects(["Py (programming language)", "JS"])

# Build a page-link matrix
from wikipediacorpus.processing import make_link_matrix
link_matrix = make_link_matrix({"PageA": ["PageB", "PageC"], "PageB": ["PageA"]})
```

## Async Support

Every API function has an async variant:

```python
import asyncio
from wikipediacorpus import get_article_async

article = asyncio.run(get_article_async("Python (programming language)"))
```

## API Reference

### Article Retrieval
- `get_article` / `get_article_async` -- single article plaintext extract
- `get_articles` / `get_articles_async` -- batch concurrent fetch

### Category Navigation
- `get_category_members` / `_async` -- pages or subcategories in a category
- `get_page_categories` / `_async` -- categories a page belongs to
- `get_category_members_matrix` / `_async` -- sparse category x member matrix with BFS depth

### Link Retrieval
- `get_links` / `_async` -- incoming or outgoing links for a page

### Redirect Resolution
- `resolve_redirect` / `_async` -- check single title
- `resolve_redirects` / `_async` -- batch resolve with chain chasing
- `get_redirects_to` / `_async` -- all pages redirecting to a given page

### Templates
- `get_templates` / `_async` -- templates transcluded on a page

### Text Processing
- `split_text` -- split article into Section objects by headings
- `get_headings` -- extract heading names
- `cut_at_headings` / `cut_articles_at_headings` -- truncate at specified sections
- `plot_heading_frequency` -- horizontal bar chart of heading counts

### Link Analysis (for corpus construction)
- `make_link_matrix` -- dict-of-lists to sparse binary matrix
- `compute_seed_similarity` -- cosine similarity of weighted link profiles to seed pages
- `overwrite_redirects` -- replace redirect titles with destinations
