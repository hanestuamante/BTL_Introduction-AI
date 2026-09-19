from .model import PipesProblem, PipesState


def pipes_heuristic(problem: PipesProblem, state: PipesState) -> float:
    return problem.heuristic(state)

