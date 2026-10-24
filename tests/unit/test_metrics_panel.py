from logic_search.core.events import EventType, SearchEvent
from logic_search.ui.metrics_panel import MetricsPanel


class Variable:
    def __init__(self):
        self.value = "-"

    def set(self, value):
        self.value = value


def panel():
    instance = object.__new__(MetricsPanel)
    instance.variables = {name: Variable() for name in MetricsPanel.FIELDS}
    instance._previous_node_id = None
    return instance


def test_generated_and_goal_events_do_not_reset_search_totals():
    instance = panel()
    instance.update_event(SearchEvent(EventType.NODE_EXPANDED, 1, node_id=1, parent_id=0, nodes_generated=9, nodes_expanded=4, nodes_pruned=2, frontier_size=5, depth=3))
    instance.update_event(SearchEvent(EventType.NODE_GENERATED, 2, node_id=9, parent_id=1))
    instance.update_event(SearchEvent(EventType.GOAL_FOUND, 3, node_id=9, depth=4))
    instance.update_event(SearchEvent(EventType.FINISHED, 4, nodes_generated=10, nodes_expanded=5, nodes_pruned=2, message="solved"))
    assert instance.variables["depth"].value == "4"
    assert instance.variables["pruned"].value == "2"
    assert instance.variables["status"].value == "Finished: Solution found"


def test_branch_switch_is_not_displayed_as_failure():
    instance = panel()
    instance.update_event(SearchEvent(EventType.NODE_EXPANDED, 1, node_id=1, parent_id=0))
    instance.update_event(SearchEvent(EventType.NODE_EXPANDED, 2, node_id=2, parent_id=0))
    assert instance.variables["transition"].value == "Switching branches"
    assert instance.variables["status"].value == "Expanding node"
