from __future__ import annotations

import tkinter as tk

from logic_search.puzzles.pipes.model import E, N, S, W, BASE_MASKS, rotate_mask


class PipesCanvas(tk.Canvas):
    def cell_at(self, x: float, y: float) -> int | None:
        if not hasattr(self, "_geometry"):
            return None
        ox, oy, cell, rows, cols = self._geometry
        col, row = int((x - ox) // cell), int((y - oy) // cell)
        return row * cols + col if 0 <= row < rows and 0 <= col < cols else None

    def draw(self, problem, state, *, solved: bool = False, selected: int | None = None, conflicts: set[int] | None = None) -> None:
        self.delete("all")
        conflicts = conflicts or set()
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        cell = min(width / problem.cols, height / problem.rows)
        ox = (width - cell * problem.cols) / 2
        oy = (height - cell * problem.rows) / 2
        self._geometry = (ox, oy, cell, problem.rows, problem.cols)
        for index, assigned in enumerate(state):
            row, col = divmod(index, problem.cols)
            x0, y0 = ox + col * cell, oy + row * cell
            x1, y1 = x0 + cell, y0 + cell
            mask = assigned or rotate_mask(BASE_MASKS[problem.tiles[index]], problem.initial_rotations[index])
            fill = "#dcfce7" if solved else ("#fee2e2" if index in conflicts else ("#dbeafe" if index == selected else "#ffedd5"))
            outline = "#dc2626" if index in conflicts else ("#2563eb" if index == selected else "#94a3b8")
            self.create_rectangle(x0, y0, x1, y1, fill=fill, outline=outline, width=3 if index == selected or index in conflicts else 1)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            color = "#15803d" if solved else "#1d4ed8"
            line = max(3, int(cell / 9))
            endpoints = {N: (cx, y0), E: (x1, cy), S: (cx, y1), W: (x0, cy)}
            for bit, point in endpoints.items():
                if mask & bit:
                    self.create_line(cx, cy, *point, width=line, fill=color, capstyle=tk.ROUND)
            self.create_oval(cx - line / 2, cy - line / 2, cx + line / 2, cy + line / 2, fill=color, outline=color)
