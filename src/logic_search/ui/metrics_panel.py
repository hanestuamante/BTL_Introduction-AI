from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class MetricsPanel(ttk.LabelFrame):
    FIELDS = ("status", "elapsed", "generated", "expanded", "pruned", "frontier", "depth", "heuristic")

    def __init__(self, master) -> None:
        super().__init__(master, text="Search metrics", padding=8)
        self.variables = {name: tk.StringVar(value="-") for name in self.FIELDS}
        for row, name in enumerate(self.FIELDS):
            ttk.Label(self, text=name.replace("_", " ").title() + ":").grid(row=row, column=0, sticky="w", padx=(0, 8))
            ttk.Label(self, textvariable=self.variables[name], width=16).grid(row=row, column=1, sticky="w")

    def update_event(self, event) -> None:
        self.variables["status"].set(event.type.value)
        if event.elapsed_ms >= 1000.0:
            self.variables["elapsed"].set(f"{event.elapsed_ms / 1000.0:.2f} s")
        else:
            self.variables["elapsed"].set(f"{event.elapsed_ms:.2f} ms")
        if event.nodes_generated > 0 or event.type not in {"CELL_DOMAIN", "VALUE_TRIED", "VALUE_REJECTED"}:
            self.variables["generated"].set(str(event.nodes_generated))
            self.variables["expanded"].set(str(event.nodes_expanded))
            self.variables["pruned"].set(str(event.nodes_pruned))
            self.variables["frontier"].set(str(event.frontier_size))
            self.variables["depth"].set(str(event.depth))
            self.variables["heuristic"].set(f"{event.h:g}")

