import pytest

from logic_search.puzzles.futoshiki.parser import FutoshikiInputError, parse_futoshiki
from logic_search.puzzles.futoshiki.rules import validate_solution


def fixture():
    return {
        "schema_version": 1, "puzzle": "futoshiki", "id": "test-4", "size": 4,
        "givens": [[1, 0, 0, 4], [0, 4, 1, 0], [0, 1, 4, 0], [4, 0, 0, 1]],
        "inequalities": [{"left": [0, 0], "op": "<", "right": [0, 1]}], "metadata": {},
    }


def test_domain_respects_row_column_and_inequality():
    problem = parse_futoshiki(fixture())
    assert problem.domain(problem.initial_state, 1) == (2, 3)


def test_parser_rejects_duplicate_given():
    data = fixture()
    data["givens"][0][1] = 1
    with pytest.raises(FutoshikiInputError, match="givens"):
        parse_futoshiki(data)


def test_goal_validation():
    problem = parse_futoshiki(fixture())
    solution = (1, 2, 3, 4, 2, 4, 1, 3, 3, 1, 4, 2, 4, 3, 2, 1)
    assert problem.is_goal(solution)
    assert validate_solution(problem, solution)


def test_actions_emits_micro_events():
    from logic_search.core.events import EventEmitter, EventType

    problem = parse_futoshiki(fixture())
    events = []
    emitter = EventEmitter(callback=events.append, detailed=True)
    actions = list(problem.actions(problem.initial_state, emitter=emitter))
    assert actions
    event_types = [e.type for e in events]
    assert EventType.CELL_DOMAIN in event_types
    assert EventType.VALUE_TRIED in event_types
    domain_event = next(e for e in events if e.type == EventType.CELL_DOMAIN)
    assert domain_event.domain is not None and len(domain_event.domain) > 0
    tried_event = next(e for e in events if e.type == EventType.VALUE_TRIED)
    assert tried_event.domain is not None and len(tried_event.domain) > 0
