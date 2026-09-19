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
