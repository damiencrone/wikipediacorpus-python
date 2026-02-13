"""Redirect overwriting utilities."""

from __future__ import annotations


def overwrite_redirects(titles: list[str], redirect_map: dict[str, str]) -> list[str]:
    """Replace redirect origins with their destinations and deduplicate.

    Parameters
    ----------
    titles : list[str]
        Page titles, some of which may be redirect origins.
    redirect_map : dict[str, str]
        Mapping from redirect origin to destination title.

    Returns
    -------
    list[str]
        Titles with redirects replaced and duplicates removed,
        preserving original order.
    """
    seen: set[str] = set()
    result: list[str] = []
    for title in titles:
        resolved = redirect_map.get(title, title)
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result
