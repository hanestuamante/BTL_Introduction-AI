from dataclasses import dataclass
from pathlib import Path

import pytest

from logic_search.core.events import EventType, SearchEvent
from logic_search.io import load_problem
from logic_search.search.solver import solve
from logic_search.ui.futoshiki_canvas import FutoshikiCanvas
from logic_search.ui.game_logic import initial_play_state, pipes_water, rotate_pipe
from logic_search.ui.main_window import MainWindow
from logic_search.ui.metrics_panel import MetricsPanel
from logic_search.ui.pipes_canvas import PipesCanvas

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class AssignmentGraph:
    initial_state: tuple[int, ...] = (0, 0, 0)
    size: int = 3

    def state_key(self, state):
        return state

    def is_goal(self, state):
        return state == (1, 1, 1)

    def domain(self, state, cell):
        return (1, 2)

    def actions(self, state):
        return {
            (0, 0, 0): ((0, 1), (0, 2)),
            (1, 0, 0): ((1, 1),),
            (2, 0, 0): ((1, 1),),
            (1, 1, 0): ((2, 1),),
        }.get(state, ())

    def result(self, state, action):
        values = list(state)
        values[action[0]] = action[1]
        return tuple(values)

    def heuristic(self, state):
        return {(1, 0, 0): 0, (2, 0, 0): 1, (1, 1, 0): 3, (2, 1, 0): 2}.get(state, 0)


def test_gbfs_domain_visualization_does_not_reject_pending_solution_branch():
    events = []
    result = solve(AssignmentGraph(), "gbfs", on_event=events.append)
    assert result.status == "solved"
    assert [e.state for e in events if e.type == EventType.NODE_EXPANDED] == [
        (0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0), (1, 1, 0), (1, 1, 1),
    ]
    assert not any(e.type == EventType.BACKTRACK for e in events)
    assert not any(e.type == EventType.VALUE_REJECTED and e.cell == 0 and e.value == 1 for e in events)
    assert all(e.state_key == e.state for e in events if e.type == EventType.NODE_PRUNED)
    assert sum(e.type == EventType.NODE_PRUNED for e in events) == result.metrics.nodes_pruned


def test_dfs_unwind_events_are_separate_from_prune_metrics():
    problem = AssignmentGraph()
    problem.actions = lambda state: {
        (0, 0, 0): ((0, 2), (0, 1)),
        (2, 0, 0): ((1, 1),),
        (1, 0, 0): ((1, 1),),
        (1, 1, 0): ((2, 1),),
    }.get(state, ())
    events = []
    result = solve(problem, "dfs", on_event=events.append)
    assert result.status == "solved"
    assert any(e.type == EventType.BACKTRACK for e in events)
    assert sum(e.type == EventType.NODE_PRUNED for e in events) == result.metrics.nodes_pruned == 1
    plain = solve(problem, "dfs", detailed_events=False)
    for field in ("nodes_expanded", "nodes_generated", "nodes_pruned", "duplicate_states"):
        assert getattr(result.metrics, field) == getattr(plain.metrics, field)


@pytest.mark.parametrize("algorithm", ["dfs", "gbfs"])
@pytest.mark.parametrize("relative,has_locks", [
    ("pipes/pipes-6x6-hard-wrap-seed-601.json", False),
    ("generated-pipes-wrap/pipes/pipes-6x6-hard-wrap-locks-0.15-seed-242.json", True),
])
def test_wrapped_locked_pipes_keep_events_and_solution(algorithm, relative, has_locks):
    problem = load_problem(ROOT / "data" / relative)
    events = []
    result = solve(problem, algorithm, on_event=events.append)
    assert result.status == "solved"
    assert problem.wrap
    assert any(problem.is_locked(i) for i in range(len(problem.tiles))) == has_locks
    assert problem.is_goal(result.path[-1])
    assert not any(e.type in {
        EventType.CELL_DOMAIN, EventType.VALUE_TRIED, EventType.VALUE_REJECTED, EventType.BACKTRACK,
    } for e in events)
    assert sum(e.type == EventType.NODE_PRUNED for e in events) == result.metrics.nodes_pruned
    assert all(e.state_key == e.state for e in events if e.type == EventType.NODE_PRUNED)
    state = initial_play_state(problem)
    for index in range(len(state)):
        if problem.is_locked(index):
            assert rotate_pipe(problem, state, index) == state


@pytest.mark.parametrize("algorithm", ["dfs", "gbfs"])
def test_futoshiki_solver_micro_events_preserve_search_results(algorithm):
    problem = load_problem(ROOT / "data/futoshiki/futoshiki-4x4-easy-seed-201.json")
    events = []
    visual = solve(problem, algorithm, on_event=events.append)
    plain_events = []
    plain = solve(problem, algorithm, on_event=plain_events.append, detailed_events=False)
    assert visual.status == plain.status == "solved"
    assert visual.path == plain.path and visual.actions == plain.actions
    assert any(e.type == EventType.CELL_DOMAIN for e in events)
    assert any(e.type == EventType.VALUE_TRIED for e in events)
    assert [e.type for e in plain_events] == [EventType.STARTED, EventType.GOAL_FOUND, EventType.FINISHED]
    for field in ("nodes_expanded", "nodes_generated", "nodes_pruned", "duplicate_states"):
        assert getattr(visual.metrics, field) == getattr(plain.metrics, field)


def test_timeout_excludes_gui_callback_wait(monkeypatch):
    import importlib

    events_module = importlib.import_module("logic_search.core.events")
    solver_module = importlib.import_module("logic_search.search.solver")
    clock = [0.0]
    monkeypatch.setattr(events_module, "perf_counter", lambda: clock[0])
    monkeypatch.setattr(solver_module, "perf_counter", lambda: clock[0])

    def callback(event):
        clock[0] += 1.0

    result = solve(AssignmentGraph(), "gbfs", timeout=0.05, on_event=callback)
    assert clock[0] > 1.0
    assert result.status == "solved"
    assert result.metrics.runtime_ms == 0.0


class Variable:
    def __init__(self):
        self.value = "-"

    def set(self, value):
        self.value = value


def test_metrics_accept_domain_events_without_resetting_totals_or_solution_depth():
    panel = object.__new__(MetricsPanel)
    panel.variables = {name: Variable() for name in MetricsPanel.FIELDS}
    panel._previous_node_id = None
    panel.update_event(SearchEvent(EventType.NODE_EXPANDED, 10, node_id=1, nodes_generated=9,
                                   nodes_expanded=4, nodes_pruned=2, frontier_size=5, depth=3))
    for event_type in (EventType.CELL_DOMAIN, EventType.VALUE_TRIED, EventType.VALUE_REJECTED,
                       EventType.BACKTRACK, EventType.NODE_GENERATED):
        panel.update_event(SearchEvent(event_type, 1100, cell=0, value=1, domain=(1, 2)))
        assert panel.variables["generated"].value == "9"
        assert panel.variables["expanded"].value == "4"
        assert panel.variables["pruned"].value == "2"
        assert panel.variables["depth"].value == "3"
    assert panel.variables["elapsed"].value == "1.10 s"
    panel.update_event(SearchEvent(EventType.GOAL_FOUND, 1110, depth=4))
    panel.update_event(SearchEvent(EventType.FINISHED, 1111, nodes_generated=10, nodes_expanded=5,
                                   nodes_pruned=2, message="solved"))
    assert panel.variables["depth"].value == "4"


@pytest.mark.parametrize("puzzle,canvas_class", [("pipes", PipesCanvas), ("futoshiki", FutoshikiCanvas)])
def test_window_draw_preserves_water_and_domain_visualization(puzzle, canvas_class):
    window = object.__new__(MainWindow)
    relative = ("pipes/pipes-6x6-hard-wrap-seed-601.json" if puzzle == "pipes"
                else "futoshiki/futoshiki-4x4-easy-seed-201.json")
    window.problem = load_problem(ROOT / "data" / relative)
    window.current_state = initial_play_state(window.problem)
    window.canvas = object.__new__(canvas_class)
    drawn = []
    window.canvas.draw = lambda problem, state, **kwargs: drawn.append((problem, state, kwargs))
    window.solved = False
    window.selected = None
    window.conflicts = set()
    window.active_cell = 0
    window.active_kind = "rejected"
    window.active_value = 1
    window.domain_values = (1, 2)
    window.cell_rejected = {0: {1}}
    window._draw()
    problem, state, options = drawn[0]
    assert problem is window.problem and state == window.current_state
    if puzzle == "pipes":
        assert options["water"] == pipes_water(problem, state)
        assert problem.source_index in options["water"]
    else:
        assert options["active_cell"] == 0
        assert options["domain_values"] == (1, 2)
        assert options["rejected_values"] == {1}
