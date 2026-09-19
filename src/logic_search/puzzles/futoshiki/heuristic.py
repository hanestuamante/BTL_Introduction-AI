from .model import FutoshikiProblem, FutoshikiState


def futoshiki_heuristic(problem: FutoshikiProblem, state: FutoshikiState) -> float:
    return problem.heuristic(state)

