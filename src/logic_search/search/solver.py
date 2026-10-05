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
        now = perf_counter()
        emitter.accumulated_ms += (now - emitter.last_active) * 1000
        emitter.last_active = now
        metrics.runtime_ms = emitter.accumulated_ms
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

    visual_events = detailed_events and on_event is not None
    assignment_problem = hasattr(problem, "size") and hasattr(problem, "domain")
    domain_backtracking = visual_events and algorithm == "dfs" and assignment_problem
    last_expanded_id: int | None = None
    last_had_no_children: bool = False

    try:
        while len(frontier):
            if token.cancelled:
                return finish("cancelled", "Search cancelled")
            if timeout is not None:
                compute_time_s = (emitter.accumulated_ms + (perf_counter() - emitter.last_active) * 1000) / 1000.0 if emitter.callback is not None else (perf_counter() - started)
                if compute_time_s >= timeout:
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

            if domain_backtracking and last_expanded_id is not None:
                start_climb = nodes[last_expanded_id].parent_id if last_had_no_children else last_expanded_id
                target_parent = node.parent_id
                target_ancestors = set()
                curr: int | None = target_parent
                while curr is not None:
                    target_ancestors.add(curr)
                    curr = nodes[curr].parent_id

                curr = start_climb
                climb: list[int] = []
                while curr is not None and curr not in target_ancestors:
                    climb.append(curr)
                    curr = nodes[curr].parent_id

                for anc_id in climb:
                    anc = nodes[anc_id]
                    if anc.parent_id is not None and anc.action is not None:
                        p = nodes[anc.parent_id]
                        cell, value = anc.action if isinstance(anc.action, tuple) and len(anc.action) == 2 else (None, None)
                        if cell is not None:
                            d = problem.domain(p.state, cell) if hasattr(problem, "domain") else None
                            if not d and hasattr(problem, "size"):
                                d = tuple(range(1, problem.size + 1))
                            r = cell // getattr(problem, "size", 1) + 1
                            c = cell % getattr(problem, "size", 1) + 1
                            is_sibling_of_next = (anc.parent_id == node.parent_id)
                            if is_sibling_of_next:
                                emitter.emit(
                                    EventType.VALUE_REJECTED,
                                    state=p.state,
                                    cell=cell,
                                    value=value,
                                    domain=d,
                                    action=anc.action,
                                    depth=anc.depth,
                                    nodes_generated=metrics.nodes_generated,
                                    nodes_expanded=metrics.nodes_expanded,
                                    nodes_pruned=metrics.nodes_pruned,
                                    frontier_size=len(frontier) + 1,
                                    reason="dead_end",
                                    message=f"Lùi lại: giá trị {value} tại ô hàng {r}, cột {c} không dẫn tới nghiệm, thử giá trị tiếp theo",
                                )
                            else:
                                emitter.emit(
                                    EventType.VALUE_REJECTED,
                                    state=p.state,
                                    cell=cell,
                                    value=None,
                                    domain=d,
                                    action=anc.action,
                                    depth=anc.depth,
                                    nodes_generated=metrics.nodes_generated,
                                    nodes_expanded=metrics.nodes_expanded,
                                    nodes_pruned=metrics.nodes_pruned,
                                    frontier_size=len(frontier) + 1,
                                    reason="all_failed",
                                    message=f"Lùi lại: ô hàng {r}, cột {c} đã thử hết các nhánh nhưng đều thất bại",
                                )
                        emitter.emit(
                            EventType.BACKTRACK,
                            node_id=anc_id,
                            parent_id=anc.parent_id,
                            state_key=problem.state_key(p.state),
                            state=p.state,
                            action=anc.action,
                            depth=anc.depth,
                            h=anc.h,
                            nodes_generated=metrics.nodes_generated,
                            nodes_expanded=metrics.nodes_expanded,
                            nodes_pruned=metrics.nodes_pruned,
                            frontier_size=len(frontier) + 1,
                            message="All child branches exhausted",
                        )

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
            action_ctx = {
                "node_id": node_id,
                "parent_id": node.parent_id,
                "depth": node.depth,
                "nodes_generated": metrics.nodes_generated,
                "nodes_expanded": metrics.nodes_expanded,
                "nodes_pruned": metrics.nodes_pruned,
                "frontier_size": len(frontier),
            }
            actions_with_events = getattr(problem, "actions_with_events", None)
            if visual_events and actions_with_events is not None:
                valid_actions = list(actions_with_events(node.state, emitter, **action_ctx))
            else:
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
                if visual_events and not valid_actions and assignment_problem:
                    try:
                        empty_idx = node.state.index(0)
                        exhausted_domain = problem.domain(node.state, empty_idx)
                        if not exhausted_domain and hasattr(problem, "size"):
                            exhausted_domain = tuple(range(1, problem.size + 1))
                        if exhausted_domain:
                            emitter.emit(
                                EventType.VALUE_REJECTED,
                                state=node.state,
                                cell=empty_idx,
                                value=None,
                                domain=exhausted_domain,
                                depth=node.depth,
                                nodes_generated=metrics.nodes_generated,
                                nodes_expanded=metrics.nodes_expanded,
                                nodes_pruned=metrics.nodes_pruned,
                                frontier_size=len(frontier),
                                reason="all_failed",
                                message=f"Ngõ cụt: ô hàng {empty_idx // getattr(problem, 'size', 1) + 1}, cột {empty_idx % getattr(problem, 'size', 1) + 1} đã thử hết domain nhưng đều thất bại",
                            )
                    except (ValueError, AttributeError):
                        pass
                if node.parent_id is not None and node.action is not None and visual_events and not valid_actions and assignment_problem:
                    parent_state = nodes[node.parent_id].state
                    cell, value = node.action if isinstance(node.action, tuple) and len(node.action) == 2 else (None, None)
                    parent_domain = problem.domain(parent_state, cell) if cell is not None and hasattr(problem, "domain") else None
                    emitter.emit(
                        EventType.VALUE_REJECTED,
                        state=parent_state,
                        cell=cell,
                        value=value,
                        domain=parent_domain,
                        action=node.action,
                        depth=node.depth,
                        nodes_generated=metrics.nodes_generated,
                        nodes_expanded=metrics.nodes_expanded,
                        nodes_pruned=metrics.nodes_pruned,
                        frontier_size=len(frontier),
                        reason="dead_end",
                        message=f"Ngõ cụt: quay lui từ độ sâu {node.depth}",
                    )
                emitter.emit(
                    EventType.NODE_PRUNED,
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
            last_expanded_id = node_id
            last_had_no_children = (len(child_ids) == 0)

        if domain_backtracking and last_expanded_id is not None:
            curr = nodes[last_expanded_id].parent_id if last_had_no_children else last_expanded_id
            while curr is not None:
                anc = nodes[curr]
                if anc.parent_id is not None and anc.action is not None:
                    p = nodes[anc.parent_id]
                    cell, value = anc.action if isinstance(anc.action, tuple) and len(anc.action) == 2 else (None, None)
                    if cell is not None:
                        d = problem.domain(p.state, cell) if hasattr(problem, "domain") else None
                        if not d and hasattr(problem, "size"):
                            d = tuple(range(1, problem.size + 1))
                        r = cell // getattr(problem, "size", 1) + 1
                        c = cell % getattr(problem, "size", 1) + 1
                        emitter.emit(
                            EventType.VALUE_REJECTED,
                            state=p.state,
                            cell=cell,
                            value=None,
                            domain=d,
                            action=anc.action,
                            depth=anc.depth,
                            nodes_generated=metrics.nodes_generated,
                            nodes_expanded=metrics.nodes_expanded,
                            nodes_pruned=metrics.nodes_pruned,
                            frontier_size=0,
                            reason="all_failed",
                            message=f"Lùi lại: ô hàng {r}, cột {c} đã thử hết các nhánh nhưng đều thất bại",
                        )
                curr = anc.parent_id

        return finish("unsolved", "Frontier exhausted")
    except Exception as exc:
        emitter.emit(EventType.ERROR, message=str(exc))
        result = finish("error", str(exc))
        return result
