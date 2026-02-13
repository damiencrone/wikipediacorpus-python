"""Text processing functions for Wikipedia article text."""

from __future__ import annotations

import re

from ..models import Section

# Pattern matching level-2 headings: == Heading ==
_HEADING_PATTERN = re.compile(r"\n *={2} *([^=].+?) *={2} *\n")


def get_headings(text: str) -> list[str]:
    """Extract level-2 heading names from Wikipedia article text.

    Parameters
    ----------
    text : str
        Raw article text (plaintext extract from MediaWiki API).

    Returns
    -------
    list[str]
        Heading names with formatting stripped.
    """
    return _HEADING_PATTERN.findall(text)


def split_text(text: str) -> list[Section]:
    """Split article text into sections by level-2 headings.

    Parameters
    ----------
    text : str
        Raw article text.

    Returns
    -------
    list[Section]
        Sections with heading names. The first section is named ``"Lead"``.
    """
    parts = _HEADING_PATTERN.split(text)
    # parts alternates: [text_before, heading1, text1, heading2, text2, ...]
    sections: list[Section] = []
    sections.append(Section(heading="Lead", text=parts[0]))
    for i in range(1, len(parts), 2):
        heading = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        sections.append(Section(heading=heading, text=body))
    return sections


def cut_at_headings(text: str, sections_to_remove: list[str]) -> str:
    """Remove everything from specified headings onward.

    For each heading in *sections_to_remove*, all text from that heading
    to the end of the article is removed. This mirrors the R package's
    ``cut_articles_at_headings`` behaviour for a single article.

    Parameters
    ----------
    text : str
        Raw article text.
    sections_to_remove : list[str]
        Heading names at which to truncate.

    Returns
    -------
    str
        Truncated text.
    """
    for section in sections_to_remove:
        escaped = re.escape(section)
        pattern = re.compile(rf"\n *={{2}} *{escaped} *={{2}} *\n")
        match = pattern.search(text)
        if match:
            text = text[:match.start()]
    return text


def cut_articles_at_headings(articles: list[str], sections_to_remove: list[str]) -> list[str]:
    """Apply :func:`cut_at_headings` to multiple articles.

    Parameters
    ----------
    articles : list[str]
        Article texts.
    sections_to_remove : list[str]
        Heading names at which to truncate.

    Returns
    -------
    list[str]
        Truncated article texts.
    """
    return [cut_at_headings(article, sections_to_remove) for article in articles]
