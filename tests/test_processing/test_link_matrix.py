"""Tests for link matrix construction and seed similarity."""

from __future__ import annotations

import numpy as np

from wikipediacorpus.processing._link_matrix import compute_seed_similarity, make_link_matrix


def test_make_link_matrix_basic():
    links = {
        "PageA": ["PageB", "PageC"],
        "PageB": ["PageA"],
    }
    result = make_link_matrix(links)

    assert result.row_labels == ["PageA", "PageB"]
    assert result.col_labels == ["PageA", "PageB", "PageC"]
    assert result.matrix.shape == (2, 3)
    assert result.matrix.nnz == 3  # PageA->PageB, PageA->PageC, PageB->PageA


def test_make_link_matrix_single_page():
    links = {"Solo": ["Target1", "Target2"]}
    result = make_link_matrix(links)

    assert result.matrix.shape == (1, 2)
    assert result.row_labels == ["Solo"]
    assert set(result.col_labels) == {"Target1", "Target2"}


def test_make_link_matrix_empty():
    links = {"Empty": []}
    result = make_link_matrix(links)

    assert result.matrix.shape == (1, 0)
    assert result.matrix.nnz == 0


def test_make_link_matrix_shared_targets():
    links = {
        "A": ["Shared", "OnlyA"],
        "B": ["Shared", "OnlyB"],
    }
    result = make_link_matrix(links)

    assert result.matrix.shape == (2, 3)
    # "Shared" column should have entries for both rows
    shared_idx = result.col_labels.index("Shared")
    assert result.matrix[0, shared_idx] == 1
    assert result.matrix[1, shared_idx] == 1


def test_make_link_matrix_is_binary():
    links = {"A": ["B", "C"], "B": ["C"]}
    result = make_link_matrix(links)

    # All non-zero entries should be 1
    assert result.matrix.max() == 1


def test_compute_seed_similarity_basic():
    links = {
        "Seed1": ["TargetA", "TargetB"],
        "Seed2": ["TargetA", "TargetC"],
        "Other": ["TargetA"],
    }
    link_matrix = make_link_matrix(links)

    in_degree_all = {"TargetA": 3, "TargetB": 1, "TargetC": 1}
    in_degree_from_seeds = {"TargetA": 2, "TargetB": 1, "TargetC": 1}

    result = compute_seed_similarity(
        seeds=["Seed1", "Seed2"],
        link_matrix=link_matrix,
        in_degree_all=in_degree_all,
        in_degree_from_seeds=in_degree_from_seeds,
    )

    assert set(result.scores.keys()) == {"Seed1", "Seed2", "Other"}
    # All scores should be between 0 and 1
    for score in result.scores.values():
        assert 0.0 <= score <= 1.0
    assert len(result.page_weight) > 0
    assert len(result.target_vec) > 0


def test_compute_seed_similarity_zero_indegree_removed():
    """Pages with zero in-degree should be removed from computation."""
    links = {
        "Seed1": ["TargetA", "TargetB"],
        "Other": ["TargetA"],
    }
    link_matrix = make_link_matrix(links)

    # TargetB has zero in_degree_all
    in_degree_all = {"TargetA": 2, "TargetB": 0}
    in_degree_from_seeds = {"TargetA": 1, "TargetB": 0}

    result = compute_seed_similarity(
        seeds=["Seed1"],
        link_matrix=link_matrix,
        in_degree_all=in_degree_all,
        in_degree_from_seeds=in_degree_from_seeds,
    )

    # Should still compute without error
    assert "Seed1" in result.scores
    assert "Other" in result.scores


def test_compute_seed_similarity_returns_seed_similarity():
    """SeedSimilarity fields should be populated."""
    links = {"A": ["X"], "B": ["X", "Y"]}
    link_matrix = make_link_matrix(links)

    in_degree_all = {"X": 2, "Y": 1}
    in_degree_from_seeds = {"X": 1, "Y": 1}

    result = compute_seed_similarity(
        seeds=["A"],
        link_matrix=link_matrix,
        in_degree_all=in_degree_all,
        in_degree_from_seeds=in_degree_from_seeds,
    )

    assert isinstance(result.scores, dict)
    assert isinstance(result.page_weight, np.ndarray)
    assert isinstance(result.target_vec, np.ndarray)


def test_compute_seed_similarity_all_zero_indegree():
    """When all columns have zero in-degree, target_norm is 0 -> early return."""
    links = {
        "A": ["X", "Y"],
        "B": ["X"],
    }
    link_matrix = make_link_matrix(links)

    # All in-degree values are zero -> all columns removed -> target_norm == 0
    in_degree_all = {"X": 0, "Y": 0}
    in_degree_from_seeds = {"X": 0, "Y": 0}

    result = compute_seed_similarity(
        seeds=["A"],
        link_matrix=link_matrix,
        in_degree_all=in_degree_all,
        in_degree_from_seeds=in_degree_from_seeds,
    )

    # All scores should be 0.0
    assert result.scores["A"] == 0.0
    assert result.scores["B"] == 0.0
