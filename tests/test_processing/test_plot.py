"""Tests for heading frequency plotting."""

from __future__ import annotations

import tempfile
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for testing

from wikipediacorpus.models import HeadingFrequency
from wikipediacorpus.processing._plot import plot_heading_frequency


def test_plot_from_dict():
    counts = {"See also": 50, "References": 100, "History": 30}
    fig = plot_heading_frequency(counts, n=3)
    assert fig is not None
    # Top heading should be "References" (highest count)


def test_plot_from_counter():
    counts = Counter({"A": 5, "B": 10, "C": 3})
    fig = plot_heading_frequency(counts, n=2)
    assert fig is not None


def test_plot_from_heading_frequency_list():
    counts = [
        HeadingFrequency("See also", 50),
        HeadingFrequency("References", 100),
    ]
    fig = plot_heading_frequency(counts)
    assert fig is not None


def test_plot_save_to_file():
    counts = {"A": 10, "B": 20}
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    plot_heading_frequency(counts, save_path=path)
    assert Path(path).stat().st_size > 0


def test_plot_with_title():
    counts = {"A": 10}
    fig = plot_heading_frequency(counts, title="Test Title")
    assert fig is not None


def test_plot_n_limits_bars():
    counts = {f"H{i}": i for i in range(50)}
    fig = plot_heading_frequency(counts, n=5)
    # Should only have 5 bars
    ax = fig.axes[0]
    assert len(ax.patches) == 5
