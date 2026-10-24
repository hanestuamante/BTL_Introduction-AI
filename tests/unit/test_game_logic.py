from logic_search.puzzles.futoshiki.parser import parse_futoshiki
from logic_search.puzzles.pipes.model import E, N, S, W
from logic_search.puzzles.pipes.parser import parse_pipes
from logic_search.ui.game_logic import (
    futoshiki_conflicts,
    initial_play_state,
    pipes_conflicts,
    rotate_pipe,
    set_futoshiki_value,
)


def futoshiki():
    return parse_futoshiki({
        "schema_version": 1, "puzzle": "futoshiki", "id": "game-f4", "size": 4,
        "givens": [[1, 0, 0, 4], [0, 4, 1, 0], [0, 1, 4, 0], [4, 0, 0, 1]],
        "inequalities": [{"left": [0, 0], "op": "<", "right": [0, 1]}], "metadata": {},
    })


def pipes():
    return parse_pipes({
        "schema_version": 1, "puzzle": "pipes", "id": "game-p2", "rows": 2, "cols": 2, "wrap": False,
        "tiles": [["END", "CORNER"], ["END", "CORNER"]], "initial_rotations": [[1, 2], [1, 3]], "metadata": {},
    })


def test_futoshiki_player_input_preserves_givens_and_finds_conflicts():
    problem = futoshiki()
    state = initial_play_state(problem)
    assert set_futoshiki_value(problem, state, 0, 2) == state
    state = set_futoshiki_value(problem, state, 1, 1)
    assert futoshiki_conflicts(problem, state) == {0, 1, 9}
    state = set_futoshiki_value(problem, state, 1, 2)
    assert not futoshiki_conflicts(problem, state)


def test_pipes_player_rotation_and_conflict_detection():
    problem = pipes()
    state = initial_play_state(problem)
    assert state == (E, S | W, E, N | W)
    assert not pipes_conflicts(problem, state)
    broken = rotate_pipe(problem, state, 0)
    assert pipes_conflicts(problem, broken)


def test_futoshiki_hints_reuse_solution_after_repeated_hints_and_reset(monkeypatch):
    from types import SimpleNamespace
    from logic_search.ui import main_window

    window = object.__new__(main_window.MainWindow)
    window.problem = futoshiki()
    original = initial_play_state(window.problem)
    window.current_state = original
    window.history = [original]
    window.solution = None
    window.controller = SimpleNamespace(cancel=lambda: None)
    window._clear_domain_state = lambda: None
    window._draw = lambda: None
    messages = []
    window._set_status = lambda message, **kwargs: messages.append(message)
    real_solve = main_window.solve
    calls = []

    def counted_solve(*args, **kwargs):
        calls.append(1)
        return real_solve(*args, **kwargs)

    monkeypatch.setattr(main_window, "solve", counted_solve)
    window.hint()
    first = window.current_state
    window.hint()
    assert sum(a != b for a, b in zip(original, first)) == 1
    assert sum(a != b for a, b in zip(first, window.current_state)) == 1
    assert messages[-1].startswith("Hint:")
    window.reset()
    window.hint()
    assert window.current_state == first
    assert len(calls) == 1
