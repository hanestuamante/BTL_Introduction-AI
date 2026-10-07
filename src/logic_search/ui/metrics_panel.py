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
            "solved": "Đã tìm thấy nghiệm",
            "Frontier exhausted": "Hàng đợi rỗng",
            "Search cancelled": "Đã hủy tìm kiếm",
            "timeout": "Hết thời gian",
        }
        finish_text = finish_map.get(event.message, event.message)
        labels = {
            EventType.STARTED: "Đang tìm kiếm",
            EventType.NODE_GENERATED: "Đã tạo node chờ xét",
            EventType.NODE_EXPANDED: "Đang mở rộng node",
            EventType.NODE_PRUNED: "Không sinh nhánh con mới",
            EventType.GOAL_FOUND: "Đã tìm thấy nghiệm",
            EventType.FINISHED: f"Kết thúc: {finish_text}",
            EventType.ERROR: "Lỗi tìm kiếm",
            EventType.CELL_DOMAIN: "Đang xét miền giá trị",
            EventType.VALUE_TRIED: "Đang thử giá trị",
            EventType.VALUE_REJECTED: "Đã loại giá trị",
            EventType.BACKTRACK: "Đang quay lui",
        }
        self.variables["status"].set(labels[event.type])
        elapsed = (f"{event.elapsed_ms / 1000.0:.2f} s" if event.elapsed_ms >= 1000.0
                   else f"{event.elapsed_ms:.2f} ms")
        self.variables["elapsed"].set(elapsed)
        if event.type == EventType.STARTED:
            self._previous_node_id = None
            for name in self.FIELDS[3:]:
                self.variables[name].set("0")
            self.variables["transition"].set("Node gốc")
        if event.type == EventType.NODE_EXPANDED:
            switched = self._previous_node_id is not None and event.parent_id != self._previous_node_id
            self.variables["transition"].set("Chuyển nhánh xét" if switched else "Tiếp tục mở rộng")
            self._previous_node_id = event.node_id
        if event.type == EventType.NODE_PRUNED:
            self.variables["transition"].set("Ngõ cụt" if event.message == "No valid actions" else "Nhánh con đã được khám phá")
        if event.type in {EventType.STARTED, EventType.NODE_EXPANDED, EventType.NODE_PRUNED, EventType.FINISHED}:
            for field, value in (("generated", event.nodes_generated), ("expanded", event.nodes_expanded), ("pruned", event.nodes_pruned), ("frontier", event.frontier_size)):
                self.variables[field].set(str(value))
        if event.type in {EventType.STARTED, EventType.NODE_EXPANDED, EventType.NODE_PRUNED, EventType.GOAL_FOUND}:
            self.variables["depth"].set(str(event.depth))
            self.variables["heuristic"].set(f"{event.h:g}")
