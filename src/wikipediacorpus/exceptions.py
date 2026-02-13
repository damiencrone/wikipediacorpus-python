"""Exception hierarchy for wikipediacorpus."""

from __future__ import annotations


class WikipediaCorpusError(Exception):
    """Base exception for wikipediacorpus."""


class APIError(WikipediaCorpusError):
    """MediaWiki API returned an error response."""

    def __init__(self, message: str, code: str, info: str) -> None:
        self.code = code
        self.info = info
        super().__init__(message)


class PageNotFoundError(WikipediaCorpusError):
    """The requested Wikipedia page does not exist."""

    def __init__(self, title: str, lang: str) -> None:
        self.title = title
        self.lang = lang
        super().__init__(f"Page not found: '{title}' (lang={lang})")


class HTTPError(WikipediaCorpusError):
    """HTTP request failed."""

    def __init__(self, message: str, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(message)
