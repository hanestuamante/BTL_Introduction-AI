from .solver import solve


def depth_first_search(problem, **kwargs):
    return solve(problem, "dfs", **kwargs)

