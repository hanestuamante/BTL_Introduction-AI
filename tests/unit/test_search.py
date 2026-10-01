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



def test_gbfs_switching_from_solution_ancestor_does_not_prune_it():
    from logic_search.core.events import EventType

    problem = GraphProblem({"A": ("B", "C"), "B": ("D",), "C": ("E",), "D": ("G",)}, "G", {"B": 0, "C": 1, "D": 3, "E": 2})
    events = []
    result = solve(problem, "gbfs", on_event=events.append)
    assert result.path == ["A", "B", "D", "G"]
    expanded = [event for event in events if event.type == EventType.NODE_EXPANDED]
    assert [event.state for event in expanded] == ["A", "B", "C", "E", "D", "G"]
    assert not any(event.state in result.path for event in events if event.type == EventType.NODE_PRUNED)
    assert expanded[4].parent_id == expanded[1].node_id


def test_pruning_duplicate_children_has_a_distinct_reason():
    from logic_search.core.events import EventType

    events = []
    solve(GraphProblem({"A": ("B",), "B": ("A",)}, "G", {}), on_event=events.append)
    pruned = [event for event in events if event.type == EventType.NODE_PRUNED]
    assert pruned[0].message == "All children already discovered"
