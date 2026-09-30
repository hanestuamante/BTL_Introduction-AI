from __future__ import annotations

import tkinter as tk


class FutoshikiCanvas(tk.Canvas):
    def cell_at(self, x: float, y: float) -> int | None:
        if not hasattr(self, "_geometry"):
            return None
        ox, oy, cell, size = self._geometry
        col, row = int((x - ox) // cell), int((y - oy) // cell)
        return row * size + col if 0 <= row < size and 0 <= col < size else None

    def draw(
        self,
        problem,
        state,
        *,
        solved: bool = False,
        selected: int | None = None,
        conflicts: set[int] | None = None,
        active_cell: int | None = None,
        active_kind: str | None = None,
        domain_values: tuple[int, ...] | None = None,
        active_value: int | None = None,
        rejected_values: set[int] | None = None,
    ) -> None:
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
            is_active = (index == active_cell)

            if solved:
                fill = "#dcfce7"
                outline = "#64748b"
            elif index in conflicts or (is_active and active_kind == "rejected"):
                fill = "#fee2e2"
                outline = "#dc2626"
            elif is_active and active_kind == "trial":
                fill = "#fef3c7"
                outline = "#d97706"
            elif is_active and active_kind == "domain":
                fill = "#e0f2fe"
                outline = "#0284c7"
            elif given:
                fill = "#e5e7eb"
                outline = "#64748b"
            elif index == selected:
                fill = "#dbeafe"
                outline = "#2563eb"
            else:
                fill = "#ffffff"
                outline = "#64748b"

            is_highlighted = index == selected or index in conflicts or is_active
            self.create_rectangle(x0, y0, x1, y1, fill=fill, outline=outline, width=3 if is_highlighted else 2)

            has_badges = bool(is_active and domain_values and len(domain_values) > 0)
            if has_badges:
                badge_h = min(20.0, max(13.0, cell * 0.22))
                by0 = y0 + 3.0
                by1 = by0 + badge_h
                num_items = len(domain_values)  # type: ignore[arg-type]
                avail_w = cell - 8.0
                gap = 2.0 if num_items > 1 else 0.0
                item_w = min(20.0, max(12.0, (avail_w - (num_items - 1) * gap) / max(1, num_items)))
                row_w = num_items * item_w + (num_items - 1) * gap
                bx_start = (x0 + x1 - row_w) / 2.0
                rejected_set = rejected_values or set()

                for idx, v in enumerate(domain_values):  # type: ignore[union-attr]
                    bx0 = bx_start + idx * (item_w + gap)
                    bx1 = bx0 + item_w
                    if v in rejected_set:
                        b_fill = "#fee2e2"
                        b_outline = "#ef4444"
                        b_text = "#dc2626"
                        self.create_rectangle(bx0, by0, bx1, by1, fill=b_fill, outline=b_outline, width=1)
                        self.create_text(
                            (bx0 + bx1) / 2,
                            (by0 + by1) / 2,
                            text=str(v),
                            font=("TkDefaultFont", max(8, int(badge_h * 0.55)), "bold"),
                            fill=b_text,
                        )
                        line_y = (by0 + by1) / 2
                        self.create_line(bx0 + 2, line_y, bx1 - 2, line_y, fill="#dc2626", width=2)
                    elif v == active_value:
                        b_fill = "#fef08a"
                        b_outline = "#d97706"
                        b_text = "#92400e"
                        self.create_rectangle(bx0, by0, bx1, by1, fill=b_fill, outline=b_outline, width=2)
                        self.create_text(
                            (bx0 + bx1) / 2,
                            (by0 + by1) / 2,
                            text=str(v),
                            font=("TkDefaultFont", max(8, int(badge_h * 0.6)), "bold"),
                            fill=b_text,
                        )
                    else:
                        b_fill = "#f1f5f9"
                        b_outline = "#cbd5e1"
                        b_text = "#475569"
                        self.create_rectangle(bx0, by0, bx1, by1, fill=b_fill, outline=b_outline, width=1)
                        self.create_text(
                            (bx0 + bx1) / 2,
                            (by0 + by1) / 2,
                            text=str(v),
                            font=("TkDefaultFont", max(8, int(badge_h * 0.55)), "normal"),
                            fill=b_text,
                        )

            if value:
                if solved:
                    text_fill = "#166534"
                elif is_active and active_kind == "rejected":
                    text_fill = "#b91c1c"
                elif is_active and active_kind == "trial":
                    text_fill = "#b45309"
                elif given:
                    text_fill = "#111827"
                else:
                    text_fill = "#111827"

                center_y = ((by1 + y1) / 2) if has_badges else ((y0 + y1) / 2)
                font_size = max(11, int(cell * (0.30 if has_badges else 0.35)))
                self.create_text(
                    (x0 + x1) / 2,
                    center_y,
                    text=str(value),
                    font=("TkDefaultFont", font_size, "bold" if (given or is_active) else "normal"),
                    fill=text_fill,
                )
        for left, op, right in problem.inequalities:
            lr, lc = divmod(left, problem.size)
            rr, rc = divmod(right, problem.size)
            x = ox + (lc + rc + 1) * cell / 2
            y = oy + (lr + rr + 1) * cell / 2
            self.create_oval(x - 11, y - 11, x + 11, y + 11, fill="white", outline="")
            vertical = lc == rc
            symbol = ("∧" if op == "<" else "∨") if vertical and left < right else (("∨" if op == "<" else "∧") if vertical else op)
            self.create_text(x, y, text=symbol, font=("TkDefaultFont", 13, "bold"), fill="#b45309")
