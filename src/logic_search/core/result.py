from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SearchStatus = Literal["solved", "unsolved", "timeout", "cancelled", "error"]


@dataclass(slots=True)
class SearchMetrics:
    runtime_ms: float = 0.0
    peak_python_memory_kib: float | None = None
    nodes_generated: int = 0
    nodes_expanded: int = 0
    nodes_pruned: int = 0
    duplicate_states: int = 0
    max_frontier_size: int = 0
    solution_depth: int | None = None
    solution_action_count: int | None = None
    heuristic_evaluations: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SearchResult:
    status: SearchStatus
    path: list[Any] = field(default_factory=list)
    actions: list[Any] = field(default_factory=list)
    metrics: SearchMetrics = field(default_factory=SearchMetrics)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "path": [list(s) if isinstance(s, tuple) else s for s in self.path],
            "actions": self.actions,
            "metrics": self.metrics.to_dict(),
            "message": self.message,
        }

