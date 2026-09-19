from dataclasses import dataclass

from logic_search.core.cancellation import CancellationToken
from logic_search.search.frontier import PriorityFrontier
from logic_search.search.solver import solve


@dataclass
class GraphProblem:
    graph: dict[str, tuple[str, ...]]
    goal: str
    scores: dict[str, int]
    initial_state: str = "A"

    def state_key(self, state): return state
    def is_goal(self, state): return state == self.goal
    def actions(self, state): return self.graph.get(state, ())
    def result(self, state, action): return action
    def heuristic(self, state): return self.scores.get(state, 0)


def test_dfs_is_deterministic_and_preserves_action_order():
    problem = GraphProblem({"A": ("B", "C"), "B": ("D",), "C": ("G",), "D": ("G",)}, "G", {})
    result = solve(problem, "dfs")
    assert result.status == "solved"
    assert result.path == ["A", "B", "D", "G"]


def test_gbfs_uses_lowest_heuristic():
    problem = GraphProblem({"A": ("B", "C"), "B": ("G",), "C": ("G",)}, "G", {"B": 9, "C": 1})
    result = solve(problem, "gbfs")
    assert result.path == ["A", "C", "G"]


def test_priority_frontier_ties_are_stable():
    frontier = PriorityFrontier()
    frontier.push("first", 1)
    frontier.push("second", 1)
    assert frontier.pop()[1] == "first"
    assert frontier.pop()[1] == "second"


def test_cancelled_before_search():
    token = CancellationToken()
    token.cancel()
    result = solve(GraphProblem({}, "Z", {}), cancellation=token)
    assert result.status == "cancelled"

