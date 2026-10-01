from __future__ import annotations

from time import perf_counter
from typing import Any, Callable, Literal

from logic_search.core.cancellation import CancellationToken
from logic_search.core.events import EventEmitter, EventType, SearchEvent
from logic_search.core.node import SearchNode
from logic_search.core.problem import SearchProblem
from logic_search.core.result import SearchMetrics, SearchResult

from .frontier import PriorityFrontier, StackFrontier

Algorithm = Literal["dfs", "gbfs"]


def _reconstruct(nodes: list[SearchNode], node_id: int) -> tuple[list[Any], list[Any]]:
    states: list[Any] = []
    actions: list[Any] = []
    seen: set[int] = set()
    while node_id is not None:
        if node_id in seen:
            raise RuntimeError("Parent cycle detected")
        seen.add(node_id)
        node = nodes[node_id]
        states.append(node.state)
        if node.action is not None:
            actions.append(node.action)
        node_id = node.parent_id
    states.reverse()
    actions.reverse()
    return states, actions


def solve(
    problem: SearchProblem,
    algorithm: Algorithm = "dfs",
    *,
    timeout: float | None = 60.0,
    cancellation: CancellationToken | None = None,
    on_event: Callable[[SearchEvent], None] | None = None,
    detailed_events: bool = True,
) -> SearchResult:
    if algorithm not in {"dfs", "gbfs"}:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    started = perf_counter()
    metrics = SearchMetrics(nodes_generated=1)
    emitter = EventEmitter(on_event, detailed=detailed_events)
    token = cancellation or CancellationToken()
    initial_h = float(problem.heuristic(problem.initial_state)) if algorithm == "gbfs" else 0.0
    metrics.heuristic_evaluations = int(algorithm == "gbfs")
    nodes = [SearchNode(problem.initial_state, None, None, 0, initial_h)]
    visited: set[Any] = set()
    frontier_keys: set[Any] = {problem.state_key(problem.initial_state)}
    if algorithm == "dfs":
        frontier: Any = StackFrontier[int]()
        frontier.push(0)
    else:
        frontier = PriorityFrontier[int]()
        frontier.push(0, initial_h, 0)
    metrics.max_frontier_size = 1
    emitter.emit(EventType.STARTED, node_id=0, state=problem.initial_state, nodes_generated=1, frontier_size=1, h=initial_h)

    def finish(status: str, message: str = "", node_id: int | None = None) -> SearchResult:
        metrics.runtime_ms = (perf_counter() - started) * 1000
        path: list[Any] = []
        actions: list[Any] = []
        if node_id is not None:
            path, actions = _reconstruct(nodes, node_id)
            metrics.solution_depth = nodes[node_id].depth
            metrics.solution_action_count = len(actions)
        emitter.emit(
            EventType.FINISHED,
            state=path[-1] if path else None,
            nodes_generated=metrics.nodes_generated,
            nodes_expanded=metrics.nodes_expanded,
            nodes_pruned=metrics.nodes_pruned,
            frontier_size=len(frontier),
            message=status,
        )
        return SearchResult(status, path, actions, metrics, message)

    try:
        while len(frontier):
            if token.cancelled:
                return finish("cancelled", "Search cancelled")
            if timeout is not None and perf_counter() - started >= timeout:
                return finish("timeout", f"Timeout after {timeout:g} seconds")
            if algorithm == "dfs":
                node_id = frontier.pop()
            else:
                _priority, node_id = frontier.pop()
            node = nodes[node_id]
            key = problem.state_key(node.state)
            frontier_keys.discard(key)
            if key in visited:
                metrics.duplicate_states += 1
                continue
            visited.add(key)
            metrics.nodes_expanded += 1
            emitter.emit(
                EventType.NODE_EXPANDED,
                node_id=node_id,
                parent_id=node.parent_id,
                state_key=key,
                state=node.state,
                action=node.action,
                depth=node.depth,
                h=node.h,
                nodes_generated=metrics.nodes_generated,
                nodes_expanded=metrics.nodes_expanded,
                nodes_pruned=metrics.nodes_pruned,
                frontier_size=len(frontier),
            )
            if problem.is_goal(node.state):
                emitter.emit(EventType.GOAL_FOUND, node_id=node_id, parent_id=node.parent_id, state_key=key, state=node.state, depth=node.depth, h=node.h)
                return finish("solved", node_id=node_id)
            child_ids: list[int] = []
            valid_actions = list(problem.actions(node.state))
            for action in valid_actions:
                child_state = problem.result(node.state, action)
                child_key = problem.state_key(child_state)
                if child_key in visited or child_key in frontier_keys:
                    metrics.duplicate_states += 1
                    continue
                h = float(problem.heuristic(child_state)) if algorithm == "gbfs" else 0.0
                metrics.heuristic_evaluations += int(algorithm == "gbfs")
                child_id = len(nodes)
                nodes.append(SearchNode(child_state, node_id, action, node.depth + 1, h))
                frontier_keys.add(child_key)
                child_ids.append(child_id)
                metrics.nodes_generated += 1
                emitter.emit(EventType.NODE_GENERATED, node_id=child_id, parent_id=node_id, state_key=child_key, state=child_state, action=action, depth=node.depth + 1, h=h)
            if not child_ids:
                metrics.nodes_pruned += 1
                emitter.emit(
                    EventType.NODE_PRUNED,
                    node_id=node_id,
                    parent_id=node.parent_id,
                    state_key=key,
                    state=node.state,
                    depth=node.depth,
                    h=node.h,
                    nodes_generated=metrics.nodes_generated,
                    nodes_expanded=metrics.nodes_expanded,
                    nodes_pruned=metrics.nodes_pruned,
                    frontier_size=len(frontier),
                    message="All children already discovered" if valid_actions else "No valid actions",
                )
            if algorithm == "dfs":
                for child_id in reversed(child_ids):
                    frontier.push(child_id)
            else:
                for child_id in child_ids:
                    child = nodes[child_id]
                    frontier.push(child_id, child.h, child.depth)
            metrics.max_frontier_size = max(metrics.max_frontier_size, len(frontier))
        return finish("unsolved", "Frontier exhausted")
    except Exception as exc:
        emitter.emit(EventType.ERROR, message=str(exc))
        result = finish("error", str(exc))
        return result
