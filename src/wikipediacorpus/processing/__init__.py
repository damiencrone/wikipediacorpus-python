"""Text processing, visualization, and link analysis for Wikipedia articles."""

from ._link_matrix import compute_seed_similarity, make_link_matrix
from ._redirects import overwrite_redirects

__all__ = [
    "compute_seed_similarity",
    "make_link_matrix",
    "overwrite_redirects",
]
