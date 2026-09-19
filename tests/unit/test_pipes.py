from logic_search.puzzles.pipes.model import E, N, S, W, orientations, rotate_mask
from logic_search.puzzles.pipes.parser import parse_pipes
from logic_search.puzzles.pipes.rules import validate_solution


def test_rotate_mask_clockwise():
    assert rotate_mask(N) == E
    assert rotate_mask(E) == S
    assert rotate_mask(S) == W
    assert rotate_mask(W) == N


def test_unique_orientation_counts():
    assert len(orientations("END")) == 4
    assert len(orientations("STRAIGHT")) == 2
    assert len(orientations("CORNER")) == 4
    assert len(orientations("TEE")) == 4
    assert len(orientations("CROSS")) == 1


def test_border_filter_and_tree_goal():
    problem = parse_pipes({
        "schema_version": 1, "puzzle": "pipes", "id": "p2", "rows": 2, "cols": 2, "wrap": False,
        "tiles": [["END", "CORNER"], ["END", "CORNER"]], "initial_rotations": [[0, 0], [0, 0]], "metadata": {},
    })
    assert N not in problem.domain(problem.initial_state, 0)
    assert problem.is_goal((E, S | W, E, N | W))
    assert validate_solution(problem, (E, S | W, E, N | W))
