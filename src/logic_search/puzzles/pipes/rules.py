from .model import PipesProblem, PipesState


def validate_solution(problem: PipesProblem, state: PipesState) -> bool:
    return len(state) == problem.rows * problem.cols and problem.is_goal(state)

