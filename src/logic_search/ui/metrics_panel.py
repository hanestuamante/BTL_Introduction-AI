from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from logic_search.core.events import EventType


class MetricsPanel(ttk.LabelFrame):
    FIELDS = ("status", "transition", "elapsed", "generated", "expanded", "pruned", "frontier", "depth", "heuristic")

    def __init__(self, master) -> None:
        super().__init__(master, text="Search metrics", padding=8)
        self.variables = {name: tk.StringVar(value="-") for name in self.FIELDS}
        self._previous_node_id = None
        for row, name in enumerate(self.FIELDS):
            label = "No new children" if name == "pruned" else name.replace("_", " ").title()
            ttk.Label(self, text=label + ":").grid(row=row, column=0, sticky="w", padx=(0, 8))
            ttk.Label(self, textvariable=self.variables[name], width=24, wraplength=190).grid(row=row, column=1, sticky="w")

    def update_event(self, event) -> None:
        finish_map = {
            "solved": "Solution found",
            "Frontier exhausted": "Frontier exhausted",
            "Search cancelled": "Search cancelled",
            "timeout": "Timed out",
        }
        finish_text = finish_map.get(event.message, event.message)
        labels = {
            EventType.STARTED: "Searching",
            EventType.NODE_GENERATED: "Node generated for exploration",
            EventType.NODE_EXPANDED: "Expanding node",
            EventType.NODE_PRUNED: "No new children generated",
            EventType.GOAL_FOUND: "Solution found",
            EventType.FINISHED: f"Finished: {finish_text}",
            EventType.ERROR: "Search error",
            EventType.CELL_DOMAIN: "Checking domain",
            EventType.VALUE_TRIED: "Trying value",
            EventType.VALUE_ACCEPTED: "Candidate kept (not confirmed)",
            EventType.VALUE_REJECTED: "Value rejected",
            EventType.BACKTRACK: "Backtracking",
        }
        self.variables["status"].set(labels[event.type])
        elapsed = (f"{event.elapsed_ms / 1000.0:.2f} s" if event.elapsed_ms >= 1000.0
                   else f"{event.elapsed_ms:.2f} ms")
        self.variables["elapsed"].set(elapsed)
        if event.type == EventType.STARTED:
            self._previous_node_id = None
            for name in self.FIELDS[3:]:
                self.variables[name].set("0")
            self.variables["transition"].set("Root node")
        if event.type == EventType.NODE_EXPANDED:
            switched = self._previous_node_id is not None and event.parent_id != self._previous_node_id
            self.variables["transition"].set("Switching branches" if switched else "Continuing expansion")
            self._previous_node_id = event.node_id
        if event.type == EventType.NODE_PRUNED:
            self.variables["transition"].set("Dead end" if event.message == "No valid actions" else "Child branches already discovered")
        if event.type in {EventType.STARTED, EventType.NODE_EXPANDED, EventType.NODE_PRUNED, EventType.FINISHED}:
            for field, value in (("generated", event.nodes_generated), ("expanded", event.nodes_expanded), ("pruned", event.nodes_pruned), ("frontier", event.frontier_size)):
                self.variables[field].set(str(value))
        if event.type in {EventType.STARTED, EventType.NODE_EXPANDED, EventType.NODE_PRUNED, EventType.GOAL_FOUND}:
            self.variables["depth"].set(str(event.depth))
            self.variables["heuristic"].set(f"{event.h:g}")
