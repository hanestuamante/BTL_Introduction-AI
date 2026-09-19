from .model import FutoshikiProblem, FutoshikiState


def validate_solution(problem: FutoshikiProblem, state: FutoshikiState) -> bool:
    return len(state) == problem.size * problem.size and problem.is_goal(state)

