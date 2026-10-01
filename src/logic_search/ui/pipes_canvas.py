from __future__ import annotations

import tkinter as tk
from math import asin, cos, pi, sin

from logic_search.puzzles.pipes.model import E, N, S, W, BASE_MASKS, rotate_mask

BG = "#e9e9ea"
DOT = "#c7c7ca"
TICK = "#b9b9bd"

BASE_OUTLINE = "#1f2937"
BASE_FILL = "#f4f4f5"
WATER_FILL = "#60a5fa"
CONFLICT_OUTLINE = "#dc2626"
CONFLICT_FILL = "#fecaca"
SOLVED_OUTLINE = "#16a34a"
SOLVED_FILL = "#bbf7d0"
SOURCE = "#dc2626"
LOCKED_OUTLINE = "#d97706"
SELECTED_OUTLINE = "#2563eb"


class PipesCanvas(tk.Canvas):
    def cell_at(self, x: float, y: float) -> int | None:
        if not hasattr(self, "_geometry"):
            return None
        ox, oy, cell, rows, cols = self._geometry
        col, row = int((x - ox) // cell), int((y - oy) // cell)
        return row * cols + col if 0 <= row < rows and 0 <= col < cols else None

    def _background(self, width: float, height: float, ox: float, oy: float, cell: float) -> None:
        self.create_rectangle(0, 0, width, height, fill=BG, outline="")
        spacing = max(8.0, cell)
        start_x, start_y = ox % spacing, oy % spacing
        x = start_x
        while x < width:
            y = start_y
            while y < height:
                self.create_oval(x - 1, y - 1, x + 1, y + 1, fill=DOT, outline="")
                y += spacing
            x += spacing
        step = max(10.0, cell / 2)
        pos = 0.0
        while pos < width:
            self.create_line(pos, 2, pos, 6, fill=TICK, width=1)
            self.create_line(pos, height - 6, pos, height - 2, fill=TICK, width=1)
            pos += step
        pos = 0.0
        while pos < height:
            self.create_line(2, pos, 6, pos, fill=TICK, width=1)
            self.create_line(width - 6, pos, width - 2, pos, fill=TICK, width=1)
            pos += step

    def _hub_polygon(self, cx: float, cy: float, x0: float, y0: float, x1: float, y1: float, half: float, mask: int) -> list[float]:
        nw, ne, se, sw = (cx - half, cy - half), (cx + half, cy - half), (cx + half, cy + half), (cx - half, cy + half)
        pts: list[tuple[float, float]] = [nw]
        pts += [(cx - half, y0), (cx + half, y0)] if mask & N else []
        pts.append(ne)
        pts += [(x1, cy - half), (x1, cy + half)] if mask & E else []
        pts.append(se)
        pts += [(cx + half, y1), (cx - half, y1)] if mask & S else []
        pts.append(sw)
        pts += [(x0, cy + half), (x0, cy - half)] if mask & W else []
        flat: list[float] = []
        for px, py in pts:
            flat += [px, py]
        return flat

    def _end_polygon(self, cx, cy, x0, y0, x1, y1, half, mask):
        # One silhouette joins the circular terminal and tube without an internal seam.
        radius = half * 1.65
        angle = {E: 0, S: pi / 2, W: pi, N: -pi / 2}[mask]
        opening = asin(half / radius)
        points = []
        for step in range(49):
            theta = angle + opening + (2 * pi - 2 * opening) * step / 48
            points.extend((cx + radius * cos(theta), cy + radius * sin(theta)))
        reach = (x1 - x0) / 2
        for offset in (-half, half):
            points.extend((cx + reach * cos(angle) - offset * sin(angle),
                           cy + reach * sin(angle) + offset * cos(angle)))
        return points

    def _corner_polygon(self, cx, cy, cell, half, mask):
        radius = cell * 0.22
        reach = cell / 2
        points = [(-half, -reach), (-half, -radius)]
        for step in range(17):
            angle = pi - step * pi / 32
            points.append((radius + (radius + half) * cos(angle),
                           -radius + (radius + half) * sin(angle)))
        points.extend(((reach, half), (reach, -half)))
        for step in range(17):
            angle = pi / 2 + step * pi / 32
            points.append((radius + (radius - half) * cos(angle),
                           -radius + (radius - half) * sin(angle)))
        points.append((half, -reach))
        turns = {N | E: 0, E | S: 1, S | W: 2, W | N: 3}[mask]
        flat = []
        for x, y in points:
            for _ in range(turns):
                x, y = -y, x
            flat.extend((cx + x, cy + y))
        return flat

    def draw(
        self,
        problem,
        state,
        *,
        solved: bool = False,
        selected: int | None = None,
        conflicts: set[int] | None = None,
        water: set[int] | None = None,
    ) -> None:
        self.delete("all")
        conflicts = conflicts or set()
        water = water or set()
        source = getattr(problem, "source_index", 0)
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        cell = max(1, min((width - 36) / problem.cols, (height - 36) / problem.rows))
        ox = (width - cell * problem.cols) / 2
        oy = (height - cell * problem.rows) / 2
        self._geometry = (ox, oy, cell, problem.rows, problem.cols)

        self._background(width, height, ox, oy, cell)

        if getattr(problem, "wrap", False):
            gx0, gy0 = ox, oy
            gx1, gy1 = ox + cell * problem.cols, oy + cell * problem.rows
            self.create_rectangle(gx0 - 4, gy0 - 4, gx1 + 4, gy1 + 4, outline="#7c3aed", width=2, dash=(6, 4))

        tube_half = cell * 0.075
        outline_width = max(1, round(cell / 40))

        for index, assigned in enumerate(state):
            row, col = divmod(index, problem.cols)
            x0, y0 = ox + col * cell, oy + row * cell
            x1, y1 = x0 + cell, y0 + cell
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            mask = assigned or rotate_mask(BASE_MASKS[problem.tiles[index]], problem.initial_rotations[index])
            is_locked = bool(getattr(problem, "is_locked", None)) and problem.is_locked(index)
            has_water = index in water
            is_end = problem.tiles[index] == "END"

            if solved:
                outline, fill = SOLVED_OUTLINE, SOLVED_FILL
            elif index in conflicts:
                outline, fill = CONFLICT_OUTLINE, CONFLICT_FILL
            elif has_water:
                outline, fill = BASE_OUTLINE, WATER_FILL
            else:
                outline, fill = BASE_OUTLINE, BASE_FILL

            if mask:
                if is_end:
                    poly = self._end_polygon(cx, cy, x0, y0, x1, y1, tube_half, mask)
                elif problem.tiles[index] == "CORNER":
                    poly = self._corner_polygon(cx, cy, cell, tube_half, mask)
                else:
                    poly = self._hub_polygon(cx, cy, x0, y0, x1, y1, tube_half, mask)
                self.create_polygon(*poly, fill=fill, outline=outline, width=outline_width, joinstyle=tk.ROUND)

            if is_locked:
                pad = cell * 0.08
                self.create_rectangle(x0 + pad, y0 + pad, x1 - pad, y1 - pad, outline=LOCKED_OUTLINE, width=1, dash=(3, 3))
            if index == selected:
                pad = cell * 0.05
                self.create_rectangle(x0 + pad, y0 + pad, x1 - pad, y1 - pad, outline=SELECTED_OUTLINE, width=2, dash=(4, 2))
            if index == source:
                r = cell * 0.065
                self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=SOURCE, outline="")
