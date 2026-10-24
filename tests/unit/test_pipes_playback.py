from dataclasses import replace
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from logic_search.core.events import EventEmitter, EventType, SearchEvent
from logic_search.io import load_problem
from logic_search.puzzles.pipes.model import E, N, S, W, PipesProblem
from logic_search.search.solver import solve
from logic_search.ui.controller import SearchController
from logic_search.ui.game_logic import initial_play_state
from logic_search.ui.main_window import MainWindow
from logic_search.ui.pipes_canvas import PipesCanvas, SEARCH_STYLES, WATER_FILL


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def problem():
    return PipesProblem("playback", 2, 2, ("END", "CORNER", "END", "CORNER"), (0, 0, 0, 0))


@pytest.fixture
def window(problem):
    instance = object.__new__(MainWindow)
    instance.problem = problem
    instance.current_state = initial_play_state(problem)
    instance.history = [instance.current_state]
    instance.flags, instance.flag_history = set(), [set()]
    instance.flag_target = instance.selected = None
    instance.cell_domains, instance.cell_rejected = {}, {}
    instance.conflicts = set()
    instance.solved = False
    instance._clear_domain_state()
    instance.controller = SearchController()
    instance.algorithm = SimpleNamespace(get=lambda: "dfs")
    instance.metrics = SimpleNamespace(update_event=lambda event: None)
    messages = []
    instance._set_status = lambda message, **kwargs: messages.append(message)
    instance.messages = messages
    instance.draws = []
    instance.canvas = object.__new__(PipesCanvas)
    instance.canvas.draw = lambda p, s, **kw: instance.draws.append((s, kw))
    return instance


def test_candidate_order_and_rejection_reasons(problem):
    events = []
    actions = list(problem.actions_with_events(problem.initial_state, EventEmitter(events.append)))
    assert actions == list(problem.actions(problem.initial_state)) == [(0, E)]
    trials = [event for event in events if event.type == EventType.VALUE_TRIED]
    assert [event.value for event in trials] == [N, E, S, W]
    rejected = {event.value: event for event in events if event.type == EventType.VALUE_REJECTED}
    assert rejected[N].reason == rejected[W].reason == "boundary"
    assert rejected[S].reason == "empty_domain"
    assert "row 1, column 2" in rejected[S].message
    assert [e.value for e in events if e.type == EventType.VALUE_ACCEPTED] == [E]
    assert all(e.state_key == e.state for e in events)


def test_rejections_explain_mismatched_edges_and_cycles(problem):
    events = []
    state = (E, S | W, 0, 0)
    list(problem.actions_with_events(state, EventEmitter(events.append)))
    assert any(e.type == EventType.VALUE_REJECTED and e.reason == "edge_mismatch" for e in events)
    cycle = replace(problem, tiles=("CORNER",) * 4)
    state = (E | S, S | W, N | E, 0)
    events = []
    assert not list(cycle.actions_with_events(state, EventEmitter(events.append)))
    assert any(e.reason == "cycle" and e.value == N | W for e in events)


@pytest.mark.parametrize("algorithm", ["dfs", "gbfs"])
def test_solver_replay_restores_each_branch_and_finishes_green(window, algorithm):
    window.algorithm = SimpleNamespace(get=lambda: algorithm)
    events = []
    result = solve(window.problem, algorithm, on_event=events.append)
    for event in events:
        window._handle_event(event)
        if event.type == EventType.VALUE_REJECTED:
            assert window.active_kind == "rejected"
            assert window.active_value == event.value
        if event.type == EventType.CELL_DOMAIN:
            assert window.current_state == event.state
            assert window.active_value is None
        if event.type == EventType.NODE_GENERATED:
            continue
        if event.type == EventType.NODE_EXPANDED:
            assert window.current_state == event.state
    assert result.status == "solved"
    assert window.solved and window.current_state == result.path[-1]
    assert window.active_cell is None and window.active_kind is None
    assert window.draws[-1][1]["solved"]


@pytest.mark.parametrize("algorithm", ["dfs", "gbfs"])
def test_branch_switches_never_reject_a_gbfs_pending_branch(window, algorithm):
    window.problem = load_problem(ROOT / "data/pipes/pipes-5x5-hard-wrap-seed-503.json")
    window.algorithm = SimpleNamespace(get=lambda: algorithm)
    events = []
    solve(window.problem, algorithm, on_event=events.append)
    backtracks = [event for event in events if event.type == EventType.BACKTRACK]
    assert bool(backtracks) == (algorithm == "dfs")
    for event in events:
        window._handle_event(event)
        if event.type == EventType.BACKTRACK:
            assert window.current_state == event.state
            assert not window.current_state[event.cell]
            assert window.active_kind == "rejected"
        if event.type == EventType.NODE_EXPANDED and "Switching branches" in window.messages[-1]:
            assert window.active_kind != "rejected"


@pytest.mark.parametrize("kind", ["domain", "trial", "accepted", "rejected"])
def test_canvas_colors_cells_without_overwriting_water_or_markers(problem, kind):
    canvas = object.__new__(PipesCanvas)
    canvas.winfo_width = canvas.winfo_height = lambda: 400
    calls = []
    for name in ("delete", "create_rectangle", "create_line", "create_oval", "create_polygon"):
        setattr(canvas, name, lambda *args, _name=name, **kw: calls.append((_name, kw)))
    locked = replace(problem, locked_mask=(E, 0, 0, 0))
    canvas.draw(locked, (E, 0, 0, 0), water={0}, flags={0}, search_view=True,
                active_cell=1, active_kind=kind, active_value=S | W)
    cells = {options["tags"][1]: options for _, options in calls if "tags" in options}
    assert cells["cell-0"]["fill"] == SEARCH_STYLES["assigned"][0]
    assert cells["cell-1"]["fill"] == SEARCH_STYLES[kind][0]
    assert cells["cell-2"]["fill"] == SEARCH_STYLES["unassigned"][0]
    assert any(name == "create_polygon" and options.get("fill") == WATER_FILL for name, options in calls)
    assert any(options.get("dash") == (3, 3) for _, options in calls)  # Puzzle lock.
    assert any(name == "create_oval" and options.get("fill") == "#dc2626" for name, options in calls)


def test_cancel_discards_invalid_preview_and_reset_clears_search_colors(window):
    original = initial_play_state(window.problem)
    window._handle_event(SearchEvent(EventType.STARTED, 0, state=window.problem.initial_state))
    window._handle_event(SearchEvent(EventType.VALUE_REJECTED, 0, state=(N, 0, 0, 0), cell=0, value=N))
    window.cancel_search()
    assert window.current_state == original
    assert not window.pipes_search_view and window.active_cell is None
    assert not window.draws[-1][1]["search_view"]
    window.reset()
    assert window.current_state == original and not window.pipes_search_view


def test_new_run_clears_old_highlights_and_manual_edits_cannot_hide_active_search(window):
    starts = []
    window.controller.start = lambda *a, **kw: starts.append(kw)
    window.active_cell, window.active_kind = 0, "rejected"
    window.run()
    assert starts and window.current_state == window.problem.initial_state
    assert window._pipe_branch_state == window.problem.initial_state
    assert window.pipes_search_view and window.active_cell is None
    window.controller.state.running = True
    window._on_click(SimpleNamespace(x=1, y=1, state=0))
    assert window.pipes_search_view and window.current_state == window.problem.initial_state
    window.controller.cancel()


@pytest.mark.parametrize("status", ["timeout", "error", "unsolved"])
def test_failed_finish_never_presents_a_rejected_preview_as_an_assigned_branch(window, status):
    branch = (E, 0, 0, 0)
    window._handle_event(SearchEvent(EventType.STARTED, 0, state=window.problem.initial_state))
    window._handle_event(SearchEvent(EventType.NODE_EXPANDED, 0, state=branch, node_id=1, action=(0, E)))
    window._handle_event(SearchEvent(EventType.VALUE_REJECTED, 0, state=(E, N | E, 0, 0), cell=1, value=N | E))
    window._handle_event(SearchEvent(EventType.FINISHED, 0, message=status))
    assert window.current_state == branch
    assert window.active_cell is None and window.active_kind is None
    assert not window.solved


def test_controller_steps_each_orientation_action_and_cancels_while_paused(problem):
    controller = SearchController()
    received = []

    def next_event():
        deadline = time.monotonic() + 2
        count = len(received)
        while len(received) == count and time.monotonic() < deadline:
            controller.poll(received.append)
            time.sleep(0.002)
        assert len(received) == count + 1
        return received[-1].type

    try:
        controller.start(problem, "dfs", paused=True)
        assert next_event() == EventType.STARTED
        for expected in (EventType.NODE_EXPANDED, EventType.CELL_DOMAIN, EventType.VALUE_TRIED,
                         EventType.VALUE_REJECTED, EventType.VALUE_TRIED, EventType.VALUE_ACCEPTED):
            assert controller.events.empty()
            controller.step()
            assert next_event() == expected
            assert controller.state.paused
        controller.cancel()
        controller._thread.join(timeout=2)
        assert not controller._thread.is_alive()
        assert controller.events.empty()
    finally:
        controller.cancel()
