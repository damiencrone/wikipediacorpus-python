"""Plotting functions for heading frequency analysis."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from ..models import HeadingFrequency


def plot_heading_frequency(
    heading_counts: Union[dict[str, int], Counter[str], list[HeadingFrequency]],
    *,
    n: int = 25,
    save_path: str | Path | None = None,
    figsize: tuple[float, float] = (4, 6),
    title: str | None = None,
    show: bool = False,
) -> Figure:
    """Plot a horizontal bar chart of heading frequencies.

    Parameters
    ----------
    heading_counts : dict, Counter, or list[HeadingFrequency]
        Heading names mapped to their counts.
    n : int
        Number of top headings to display (default 25).
    save_path : str or Path, optional
        File path to save the figure (format inferred from extension).
    figsize : tuple
        Figure size in inches (width, height).
    title : str, optional
        Plot title.
    show : bool
        Whether to call ``plt.show()`` (default False).

    Returns
    -------
    matplotlib.figure.Figure
        The created figure, for further customization.
    """
    # Normalize input to sorted (heading, count) pairs
    if isinstance(heading_counts, list):
        pairs = [(hf.heading, hf.count) for hf in heading_counts]
    else:
        pairs = list(heading_counts.items())

    # Sort descending by count, take top n
    pairs.sort(key=lambda x: x[1], reverse=True)
    pairs = pairs[:n]

    # Reverse for bottom-to-top bar ordering
    headings = [p[0] for p in reversed(pairs)]
    counts = [p[1] for p in reversed(pairs)]
    total = sum(c for _, c in pairs)

    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(range(len(headings)), counts)
    ax.set_yticks(range(len(headings)))
    ax.set_yticklabels(headings, fontsize=8)
    ax.set_xlabel("Frequency")

    # Add proportion axis on top
    if total > 0:
        ax2 = ax.twiny()
        ax2.set_xlim(ax.get_xlim()[0] / total, ax.get_xlim()[1] / total)
        ax2.set_xlabel("Proportion", fontsize=8)
        ax2.tick_params(labelsize=7)

    if title:
        fig.suptitle(title)

    fig.tight_layout()

    if save_path is not None:
        fig.savefig(str(save_path))
    if show:
        plt.show()

    return fig
