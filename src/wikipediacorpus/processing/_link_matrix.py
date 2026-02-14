"""Build page-link matrices and compute seed-page similarity."""

from __future__ import annotations

import logging

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from ..models import LinkMatrix, SeedSimilarity

logger = logging.getLogger(__name__)


def make_link_matrix(links: dict[str, list[str]]) -> LinkMatrix:
    """Convert a dict-of-lists into a sparse binary link matrix.

    Parameters
    ----------
    links : dict[str, list[str]]
        Mapping from source page titles to lists of target page titles.

    Returns
    -------
    LinkMatrix
        Sparse binary matrix where rows are source pages and columns
        are all target pages.
    """
    row_labels = list(links.keys())
    col_set: set[str] = set()
    for targets in links.values():
        col_set.update(targets)
    col_labels = sorted(col_set)
    col_index = {name: i for i, name in enumerate(col_labels)}

    rows: list[int] = []
    cols: list[int] = []
    for i, source in enumerate(row_labels):
        for target in links[source]:
            if target in col_index:
                rows.append(i)
                cols.append(col_index[target])

    data = [1] * len(rows)
    mat = coo_matrix(
        (data, (rows, cols)),
        shape=(len(row_labels), len(col_labels)),
    ).tocsr()

    return LinkMatrix(matrix=mat, row_labels=row_labels, col_labels=col_labels)


def compute_seed_similarity(
    seeds: list[str],
    link_matrix: LinkMatrix,
    in_degree_all: dict[str, int],
    in_degree_from_seeds: dict[str, int],
) -> SeedSimilarity:
    """Compute cosine similarity of page link profiles to a seed target vector.

    This implements the algorithm from ``computeSeedSimilarity.R``, vectorized
    for performance.

    Parameters
    ----------
    seeds : list[str]
        Titles of seed pages (must be rows in *link_matrix*).
    link_matrix : LinkMatrix
        Sparse binary page-link matrix.
    in_degree_all : dict[str, int]
        Total in-degree for each target page (column).
    in_degree_from_seeds : dict[str, int]
        In-degree from seed pages for each target page (column).

    Returns
    -------
    SeedSimilarity
        Cosine similarity scores for each source page, plus the
        weight and target vectors used in the computation.
    """
    mat = link_matrix.matrix.copy().astype(np.float64)
    col_labels = link_matrix.col_labels
    row_labels = link_matrix.row_labels

    # Build per-column arrays aligned with col_labels
    in_all = np.array([in_degree_all.get(c, 0) for c in col_labels], dtype=np.float64)
    in_seeds = np.array([in_degree_from_seeds.get(c, 0) for c in col_labels], dtype=np.float64)

    # Remove columns with zero in-degree
    nonzero = in_all > 0
    n_removed = int(np.sum(~nonzero))
    if n_removed > 0:
        logger.info("Removing %d pages with zero in-degree", n_removed)
        keep_idx = np.where(nonzero)[0]
        mat = mat[:, keep_idx]
        in_all = in_all[keep_idx]
        in_seeds = in_seeds[keep_idx]

    # page_weight = in_degree_from_seeds / in_degree_all
    page_weight = in_seeds / in_all
    target_vec = page_weight.copy()

    # Vectorized: weighted_mat = link_mat * diag(page_weight)
    # For each row, multiply element-wise by page_weight
    # csr_matrix.multiply broadcasts a 1D array column-wise
    weighted_mat: csr_matrix = mat.multiply(page_weight)

    # Cosine similarity: sim(target_vec, weighted_row) for each row
    target_norm = np.sqrt(np.dot(target_vec, target_vec))
    if target_norm == 0:
        scores = {r: 0.0 for r in row_labels}
        return SeedSimilarity(
            scores=scores, page_weight=page_weight, target_vec=target_vec,
            n_columns_removed=n_removed, n_columns_used=mat.shape[1],
        )

    # For sparse weighted_mat: dot product with target_vec per row
    dot_products = np.asarray(weighted_mat.dot(target_vec)).ravel()

    # Row norms: sqrt of sum of squares of weighted rows
    row_norms = np.sqrt(np.asarray(weighted_mat.multiply(weighted_mat).sum(axis=1)).ravel())

    # Avoid division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        similarities = dot_products / (row_norms * target_norm)
    similarities = np.nan_to_num(similarities, nan=0.0)

    scores = {row_labels[i]: float(similarities[i]) for i in range(len(row_labels))}

    return SeedSimilarity(
        scores=scores, page_weight=page_weight, target_vec=target_vec,
        n_columns_removed=n_removed, n_columns_used=mat.shape[1],
    )
