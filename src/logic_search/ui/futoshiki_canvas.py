from __future__ import annotations

import tkinter as tk


class FutoshikiCanvas(tk.Canvas):
    def cell_at(self, x: float, y: float) -> int | None:
        if not hasattr(self, "_geometry"):
            return None
        ox, oy, cell, size = self._geometry
        col, row = int((x - ox) // cell), int((y - oy) // cell)
        return row * size + col if 0 <= row < size and 0 <= col < size else None

    def draw(self, problem, state, *, solved: bool = False, selected: int | None = None, conflicts: set[int] | None = None) -> None:
        self.delete("all")
        conflicts = conflicts or set()
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        margin = 28
        cell = min((width - 2 * margin) / problem.size, (height - 2 * margin) / problem.size)
        ox = (width - cell * problem.size) / 2
        oy = (height - cell * problem.size) / 2
        self._geometry = (ox, oy, cell, problem.size)
        for index, value in enumerate(state):
            row, col = divmod(index, problem.size)
            x0, y0 = ox + col * cell, oy + row * cell
            x1, y1 = x0 + cell, y0 + cell
            given = problem.givens[index] != 0
            fill = "#dcfce7" if solved else ("#fee2e2" if index in conflicts else ("#e5e7eb" if given else ("#dbeafe" if index == selected else "#ffffff")))
            outline = "#dc2626" if index in conflicts else ("#2563eb" if index == selected else "#64748b")
            self.create_rectangle(x0, y0, x1, y1, fill=fill, outline=outline, width=3 if index == selected or index in conflicts else 2)
            if value:
                self.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=str(value), font=("TkDefaultFont", max(12, int(cell * .35)), "bold" if given else "normal"), fill="#166534" if solved else "#111827")
        for left, op, right in problem.inequalities:
            lr, lc = divmod(left, problem.size)
            rr, rc = divmod(right, problem.size)
            x = ox + (lc + rc + 1) * cell / 2
            y = oy + (lr + rr + 1) * cell / 2
            self.create_oval(x - 11, y - 11, x + 11, y + 11, fill="white", outline="")
            vertical = lc == rc
            symbol = ("∧" if op == "<" else "∨") if vertical and left < right else (("∨" if op == "<" else "∧") if vertical else op)
            self.create_text(x, y, text=symbol, font=("TkDefaultFont", 13, "bold"), fill="#b45309")
