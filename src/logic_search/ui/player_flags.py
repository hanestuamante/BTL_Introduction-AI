from __future__ import annotations

FLAG_COLOR = "#7c3aed"


def draw_player_flag(canvas, x0: float, y0: float, cell: float) -> None:
    """Draw a player's note with canvas shapes, independently of installed fonts."""
    size = min(18.0, max(5.0, cell * 0.25))
    x, y = x0 + cell - size - cell * 0.06, y0 + cell - size - cell * 0.06
    width = max(1, round(size / 8))
    canvas.create_line(x, y, x, y + size, fill=FLAG_COLOR, width=width)
    canvas.create_polygon(x, y, x + size * 0.8, y + size * 0.28, x, y + size * 0.56, fill=FLAG_COLOR, outline=FLAG_COLOR)
    canvas.create_line(x - size * 0.2, y + size, x + size * 0.25, y + size, fill=FLAG_COLOR, width=width)
