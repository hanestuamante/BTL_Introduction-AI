from .solver import solve


def greedy_best_first_search(problem, **kwargs):
    return solve(problem, "gbfs", **kwargs)

