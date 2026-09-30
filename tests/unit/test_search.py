from dataclasses import dataclass

from logic_search.core.cancellation import CancellationToken
from logic_search.core.events import EventType
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


def test_dfs_emits_intermediate_backtrack_unwind_events():
    # Tree structure:
    # Root (0) -> (1, 1) -> (2, 1) [dead end]
    # Root (0) -> (1, 2) -> (2, 2) [goal]
    # When (2, 1) dead ends, (1, 1) is a sibling of (1, 2) (both under Root for cell 1).
    # It must unwind (1, 1) with reason="dead_end", value=1, keeping value 2 available.
    @dataclass
    class TreeProblem:
        initial_state: tuple[int, int, int] = (0, 0, 0)
        size: int = 3

        def state_key(self, state): return state
        def is_goal(self, state): return state == (0, 2, 2)
        def actions(self, state):
            if state == (0, 0, 0):
                return [(1, 1), (1, 2)]
            elif state == (0, 1, 0):
                return [(2, 1), ] # only choice, leading to dead end
            elif state == (0, 2, 0):
                return [(2, 2), ]
            return ()
        def result(self, state, action):
            lst = list(state)
            lst[action[0]] = action[1]
            return tuple(lst)
        def domain(self, state, cell):
            return (1, 2)
        def heuristic(self, state): return 0

    events = []
    result = solve(TreeProblem(), "dfs", detailed_events=True, on_event=lambda e: events.append(e))
    assert result.status == "solved"

    # Check for dead_end rejection of value 1 on cell 1
    rejected_events = [e for e in events if e.type.name == "VALUE_REJECTED"]
    cell_1_rejections = [e for e in rejected_events if e.cell == 1]
    assert len(cell_1_rejections) >= 1
    # Value 1 was rejected, but reason was dead_end (not all_failed, since value 2 was still untried)
    assert any(e.value == 1 and getattr(e, "reason", None) == "dead_end" for e in cell_1_rejections)


def test_dfs_emits_all_failed_when_all_branches_exhausted():
    # Tree structure:
    # Root (0) -> (1, 1) -> (2, 1) [dead end]
    # Root (0) -> (1, 2) -> (2, 2) [dead end]
    # All branches under Root for cell 1 fail, so cell 1 must eventually be all_failed
    @dataclass
    class ExhaustedTreeProblem:
        initial_state: tuple[int, int, int] = (0, 0, 0)
        size: int = 3

        def state_key(self, state): return state
        def is_goal(self, state): return False
        def actions(self, state):
            if state == (0, 0, 0):
                return [(1, 1), (1, 2)]
            elif state == (0, 1, 0):
                return [(2, 1), ]
            elif state == (0, 2, 0):
                return [(2, 2), ]
            return ()
        def result(self, state, action):
            lst = list(state)
            lst[action[0]] = action[1]
            return tuple(lst)
        def domain(self, state, cell):
            return (1, 2)
        def heuristic(self, state): return 0

    events = []
    result = solve(ExhaustedTreeProblem(), "dfs", detailed_events=True, on_event=lambda e: events.append(e))
    assert result.status == "unsolved"

    all_failed_events = [e for e in events if e.type.name == "VALUE_REJECTED" and getattr(e, "reason", None) == "all_failed"]
    assert any(e.cell == 1 for e in all_failed_events)


def test_dfs_accumulates_rejected_values_for_multi_value_domain():
    # Domain: {1, 2, 3}.
    # 1 is tried -> fails -> rejected {1}
    # 2 is tried -> fails -> rejected {1, 2}
    # 3 is tried -> goal
    @dataclass
    class MultiValueProblem:
        initial_state: tuple[int, int] = (0, 0)
        size: int = 2
        def state_key(self, s): return s
        def is_goal(self, s): return s == (3, 3)
        def actions(self, s):
            if s == (0, 0): return [(0, 1), (0, 2), (0, 3)]
            if s == (1, 0): return [(1, 1), ]
            if s == (2, 0): return [(1, 2), ]
            if s == (3, 0): return [(1, 3), ]
            return ()
        def result(self, s, a):
            l = list(s)
            l[a[0]] = a[1]
            return tuple(l)
        def domain(self, s, c): return (1, 2, 3)
        def heuristic(self, s): return 0

    accumulated_rejected: dict[int, set[int]] = {}
    history_after_second_rejection: set[int] = set()

    def handle(e):
        if e.type == EventType.VALUE_REJECTED:
            if e.reason == "dead_end" and e.value is not None:
                accumulated_rejected.setdefault(e.cell, set()).add(e.value)
                if e.cell == 0 and e.value == 2:
                    history_after_second_rejection.update(accumulated_rejected[0])

    result = solve(MultiValueProblem(), "dfs", detailed_events=True, on_event=handle)
    assert result.status == "solved"
    # When value 2 failed on cell 0, both 1 and 2 were in the accumulated rejected set!
    assert history_after_second_rejection == {1, 2}


def test_controller_step_and_pause():
    from logic_search.ui.controller import SearchController
    import time

    problem = GraphProblem({"A": ("B", "C"), "B": ("D",), "C": ("G",), "D": ("G",)}, "G", {})
    controller = SearchController()
    controller.start(problem, "dfs", paused=True)

    # Initial state should be running and paused
    assert controller.state.running
    assert controller.state.paused

    # Step once
    controller.step()
    time.sleep(0.1)
    polled = []
    controller.poll(lambda e: polled.append(e))
    assert len(polled) >= 1

    # Cancel
    controller.cancel()
    time.sleep(0.1)
    assert not controller.state.running


def test_pure_compute_time_excludes_callback_wait() -> None:
    import time
    from logic_search.core.events import EventType

    problem = GraphProblem({"A": ("B", "C"), "B": ("D",), "C": ("G",), "D": ("G",)}, "G", {})
    last_event_elapsed = 0.0

    def slow_callback(e) -> None:
        nonlocal last_event_elapsed
        last_event_elapsed = e.elapsed_ms
        # Simulate GUI animation / wait delay
        time.sleep(0.04)

    start_wall = time.perf_counter()
    result = solve(problem, "dfs", on_event=slow_callback, detailed_events=True)
    wall_duration_ms = (time.perf_counter() - start_wall) * 1000

    # There are multiple events, each sleeping 40ms -> wall time > 150ms
    assert wall_duration_ms >= 120.0
    # But measured compute time (Option 1) must exclude callback wait
    assert result.metrics.runtime_ms < 50.0
    assert last_event_elapsed < 50.0


