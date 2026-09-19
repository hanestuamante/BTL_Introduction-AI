"""Search-based solvers for Pipes and Futoshiki."""

from .core.result import SearchMetrics, SearchResult
from .search.solver import solve

__all__ = ["SearchMetrics", "SearchResult", "solve"]
__version__ = "1.0.0"

