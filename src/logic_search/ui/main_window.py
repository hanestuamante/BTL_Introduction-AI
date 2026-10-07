from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from logic_search.core.events import EventType
from logic_search.io import load_problem
from logic_search.search.solver import solve

from .controller import SearchController
from .futoshiki_canvas import FutoshikiCanvas
from .game_logic import futoshiki_conflicts, initial_play_state, pipes_conflicts, pipes_water, rotate_pipe, set_futoshiki_value
from .metrics_panel import MetricsPanel
from .pipes_canvas import PipesCanvas

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = ROOT / "data/futoshiki/futoshiki-4x4-easy-seed-201.json"

FUTOSHIKI_BOTTOM_HINT = "Phím tắt: [Enter] Chạy • [Space] Dừng/Tiếp tục • [→ / S] Bước • [Esc] Hủy • Click ô rồi nhập 1–N"

CARD_THEMES = {
    "domain": {
        "bg": "#f0f9ff",
        "border": "#0284c7",
        "badge_bg": "#e0f2fe",
        "badge_fg": "#0369a1",
        "text_fg": "#0c4a6e",
        "badge_text": "🔍 XÉT GIÁ TRỊ THOẢ",
    },
    "trial": {
        "bg": "#fffbeb",
        "border": "#d97706",
        "badge_bg": "#fef3c7",
        "badge_fg": "#b45309",
        "text_fg": "#78350f",
        "badge_text": "⚡ ĐANG THỬ",
    },
    "rejected": {
        "bg": "#fef2f2",
        "border": "#dc2626",
        "badge_bg": "#fee2e2",
        "badge_fg": "#b91c1c",
        "text_fg": "#7f1d1d",
        "badge_text": "❌ LOẠI BỎ",
    },
    "solved": {
        "bg": "#f0fdf4",
        "border": "#16a34a",
        "badge_bg": "#dcfce7",
        "badge_fg": "#15803d",
        "text_fg": "#14532d",
        "badge_text": "🎉 THÀNH CÔNG",
    },
    "warning": {
        "bg": "#fff7ed",
        "border": "#f97316",
        "badge_bg": "#ffedd5",
        "badge_fg": "#c2410c",
        "text_fg": "#7c2d12",
        "badge_text": "⚠️ LƯU Ý",
    },
    "info": {
        "bg": "#f8fafc",
        "border": "#3b82f6",
        "badge_bg": "#eff6ff",
        "badge_fg": "#1d4ed8",
        "text_fg": "#1e293b",
        "badge_text": "ℹ️ HOẠT ĐỘNG",
    },
    "default": {
        "bg": "#f8fafc",
        "border": "#94a3b8",
        "badge_bg": "#f1f5f9",
        "badge_fg": "#475569",
        "text_fg": "#334155",
        "badge_text": "💡 HƯỚNG DẪN",
    },
}


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Logic Puzzle Search — Play & Visualize")
        self.root.geometry("1080x760")
        self.root.minsize(850, 620)
        self.controller = SearchController()
        self.problem = None
        self.current_state: tuple[int, ...] | None = None
        self.history: list[tuple[int, ...]] = []
        self.selected: int | None = None
        self.active_cell: int | None = None
        self.active_kind: str | None = None
        self.domain_values: tuple[int, ...] | None = None
        self.active_value: int | None = None
        self.cell_domains: dict[int, tuple[int, ...]] = {}
        self.cell_rejected: dict[int, set[int]] = {}
        self.conflicts: set[int] = set()
        self.solution: tuple[int, ...] | None = None
        self.solved = False
        self.speed = tk.DoubleVar(value=1.0)
        self.algorithm = tk.StringVar(value="dfs")
        self.input_path = tk.StringVar(value=str(DEFAULT_INPUT))
        self.status = tk.StringVar(value="Chọn ô trống và nhập số 1–N.")
        self.futoshiki_step_text = tk.StringVar(value="Sẵn sàng: chọn ô trắng để bắt đầu.")
        self.queue_text = tk.StringVar(value="[Trống]")
        self._build()
        self.root.bind("<Key>", self._on_key)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(30, self._poll)
        self.load()

    def _update_futoshiki_card(self, kind: str, message: str, frontier_items: tuple[str, ...] | None = None) -> None:
        if not hasattr(self, "step_card"):
            return
        theme = CARD_THEMES.get(kind, CARD_THEMES["default"])
        self.step_card.configure(
            bg=theme["bg"],
            highlightbackground=theme["border"],
            highlightcolor=theme["border"],
        )
        if hasattr(self, "step_left_frame"):
            self.step_left_frame.configure(bg=theme["bg"])
        self.step_badge.configure(
            text=theme["badge_text"],
            bg=theme["badge_bg"],
            fg=theme["badge_fg"],
        )
        self.step_label.configure(bg=theme["bg"], fg=theme["text_fg"])
        self.futoshiki_step_text.set(message)

        if hasattr(self, "step_divider"):
            self.step_divider.configure(bg=theme["border"])
        if hasattr(self, "step_right_frame"):
            self.step_right_frame.configure(bg=theme["bg"])
            is_dfs = self.algorithm.get() == "dfs"
            q_badge_title = "📚 STACK (LIFO)" if is_dfs else "⚡ PRIORITY QUEUE"
            self.queue_badge.configure(
                text=q_badge_title,
                bg=theme["badge_bg"],
                fg=theme["badge_fg"],
            )
            self.queue_label.configure(bg=theme["bg"], fg=theme["text_fg"])
            if frontier_items is not None:
                if frontier_items:
                    self.queue_text.set("  ".join(frontier_items))
                else:
                    self.queue_text.set("[Trống]")

    def _set_status(self, message: str, kind: str = "default", frontier_items: tuple[str, ...] | None = None) -> None:
        if self.problem is not None and hasattr(self.problem, "size"):
            self._update_futoshiki_card(kind, message, frontier_items=frontier_items)
        else:
            self.status.set(message)

    def _clear_domain_state(self) -> None:
        self.active_cell = None
        self.active_kind = None
        self.domain_values = None
        self.active_value = None
        self.cell_domains.clear()
        self.cell_rejected.clear()

    def _prune_inactive_cells(self, state: tuple[int, ...] | None, keep_cell: int | None = None) -> None:
        if state is None:
            return
        for idx, val in enumerate(state):
            if val == 0 and idx != keep_cell:
                self.cell_rejected.pop(idx, None)
                self.cell_domains.pop(idx, None)

    def _build(self) -> None:
        top = ttk.LabelFrame(self.root, text="Puzzle", padding=8)
        top.pack(fill="x", padx=10, pady=(10, 5))
        ttk.Entry(top, textvariable=self.input_path).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(top, text="Browse…", command=self.browse).pack(side="left")
        ttk.Button(top, text="Load", command=self.load).pack(side="left", padx=(6, 0))

        body = ttk.Frame(self.root, padding=(10, 5))
        body.pack(fill="both", expand=True)
        self.canvas_host = ttk.Frame(body)
        self.canvas_host.pack(side="left", fill="both", expand=True)

        # Futoshiki Step Card (top of game board)
        self.step_card = tk.Frame(
            self.canvas_host,
            bg="#f8fafc",
            highlightthickness=2,
            highlightbackground="#94a3b8",
            padx=10,
            pady=6,
        )

        # Left side: Instructional step
        self.step_left_frame = tk.Frame(self.step_card, bg="#f8fafc")
        self.step_left_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self.step_badge = tk.Label(
            self.step_left_frame,
            text="💡 HƯỚNG DẪN",
            font=("Segoe UI", 9, "bold"),
            bg="#f1f5f9",
            fg="#475569",
            padx=8,
            pady=3,
        )
        self.step_badge.pack(side="left", anchor="n", padx=(0, 8))

        self.step_label = tk.Label(
            self.step_left_frame,
            textvariable=self.futoshiki_step_text,
            font=("Segoe UI", 10, "bold"),
            bg="#f8fafc",
            fg="#334155",
            anchor="w",
            justify="left",
            wraplength=320,
        )
        self.step_label.pack(side="left", fill="both", expand=True)

        # Vertical divider
        self.step_divider = tk.Frame(self.step_card, bg="#cbd5e1", width=1)
        self.step_divider.pack(side="left", fill="y", padx=8)

        # Right side: Queue/Stack status
        self.step_right_frame = tk.Frame(self.step_card, bg="#f8fafc")
        self.step_right_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))

        self.queue_badge = tk.Label(
            self.step_right_frame,
            text="📚 STACK (LIFO)",
            font=("Segoe UI", 9, "bold"),
            bg="#f1f5f9",
            fg="#475569",
            padx=8,
            pady=3,
        )
        self.queue_badge.pack(side="left", anchor="n", padx=(0, 8))

        self.queue_label = tk.Label(
            self.step_right_frame,
            textvariable=self.queue_text,
            font=("Segoe UI", 9, "bold"),
            bg="#f8fafc",
            fg="#334155",
            anchor="w",
            justify="left",
            wraplength=320,
        )
        self.queue_label.pack(side="left", fill="both", expand=True)

        def _on_queue_frame_resize(event):
            half = max(140, int(event.width / 2) - 40)
            self.step_label.configure(wraplength=half)
            self.queue_label.configure(wraplength=half)

        self.step_card.bind("<Configure>", _on_queue_frame_resize)

        self.canvas = tk.Canvas(self.canvas_host, background="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        side = ttk.Frame(body)
        side.pack(side="right", fill="y", padx=(10, 0))
        self.metrics = MetricsPanel(side)
        self.metrics.pack(fill="x")
        help_box = ttk.LabelFrame(side, text="Cách chơi", padding=8)
        help_box.pack(fill="x", pady=(10, 0))
        self.help_label = ttk.Label(help_box, text="", justify="left", wraplength=220)
        self.help_label.pack(anchor="w")

        play = ttk.LabelFrame(self.root, text="Chơi trực tiếp", padding=8)
        play.pack(fill="x", padx=10, pady=5)
        for text, command in (("✓ Kiểm tra", self.check), ("💡 Gợi ý", self.hint), ("↶ Hoàn tác", self.back), ("↺ Chơi lại", self.reset)):
            ttk.Button(play, text=text, command=command).pack(side="left", padx=3)
        ttk.Separator(play, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Label(play, text="Nhập số:").pack(side="left")
        self.number_pad = ttk.Frame(play)
        self.number_pad.pack(side="left", padx=4)

        search = ttk.LabelFrame(self.root, text="Xem thuật toán giải", padding=8)
        search.pack(fill="x", padx=10, pady=5)
        ttk.Label(search, text="Thuật toán:").pack(side="left")
        combo = ttk.Combobox(search, textvariable=self.algorithm, values=("dfs", "gbfs"), state="readonly", width=7)
        combo.pack(side="left", padx=5)
        combo.bind("<<ComboboxSelected>>", lambda _e: self._on_algorithm_change())
        for text, command in (
            ("▶ Chạy", self.run),
            ("⏸ Dừng", self.pause_search),
            ("▷ Tiếp tục", self.resume_search),
            ("→ Từng bước", self.step),
            ("⏹ Hủy", self.cancel_search),
        ):
            ttk.Button(search, text=text, command=command).pack(side="left", padx=2)
        ttk.Label(search, text="Tốc độ:").pack(side="left", padx=(12, 2))
        ttk.Scale(search, from_=0.25, to=4.0, variable=self.speed, orient="horizontal", length=140).pack(side="left")

        status_bar = ttk.Frame(self.root, padding=(12, 5, 12, 10))
        status_bar.pack(fill="x")
        ttk.Label(status_bar, textvariable=self.status, anchor="w").pack(fill="x")

    def _on_algorithm_change(self) -> None:
        if hasattr(self, "queue_badge") and hasattr(self, "problem") and self.problem is not None and hasattr(self.problem, "size"):
            is_dfs = self.algorithm.get() == "dfs"
            self.queue_badge.configure(text="📚 STACK (LIFO)" if is_dfs else "⚡ PRIORITY QUEUE")

    def browse(self) -> None:
        path = filedialog.askopenfilename(initialdir=ROOT / "data", filetypes=(("JSON puzzle", "*.json"), ("All files", "*")))
        if path:
            self.input_path.set(path)
            self.load()

    def load(self) -> None:
        self.controller.cancel()
        try:
            self.problem = load_problem(self.input_path.get())
        except ValueError as exc:
            messagebox.showerror("Input không hợp lệ", str(exc))
            return
        self.current_state = initial_play_state(self.problem)
        self.history = [self.current_state]
        self.selected = None
        self._clear_domain_state()
        self.conflicts = set()
        self.solution = None
        self.solved = False
        self._replace_canvas()
        if hasattr(self.problem, "size"):
            self.step_card.pack(side="top", fill="x", padx=4, pady=(2, 6), before=self.canvas)
            self._update_futoshiki_card("default", f"Futoshiki {self.problem.size}×{self.problem.size}: chọn ô trắng để bắt đầu.", frontier_items=())
            self._build_number_pad(self.problem.size)
            self.help_label.configure(
                text="• [Space]: Dừng/Tiếp tục  • [→ / S]: Từng bước\n"
                     "• [Enter]: Chạy  • [Esc]: Hủy tìm kiếm\n"
                     "• Bấm ô trắng rồi nhập 1–N\n"
                     "• Backspace/0 để xóa ô"
            )
            self.status.set(FUTOSHIKI_BOTTOM_HINT)
        else:
            self.step_card.pack_forget()
            self._build_number_pad(0)
            self.help_label.configure(
                text="• [Space]: Dừng/Tiếp tục  • [→ / S]: Từng bước\n"
                     "• [Enter]: Chạy  • [Esc]: Hủy tìm kiếm\n"
                     "• Bấm trái để xoay 90°; bấm phải để xoay ngược\n"
                     "• Mọi đầu ống phải khớp; mạng là cây liên thông\n"
                     "• Viền cam đứt nét: ô khóa\n"
                     "• Vòng tròn đỏ: nguồn nước; ống xanh: có nước"
            )
            wrap_note = " — nối biên (viền tím đứt nét)" if self.problem.wrap else ""
            self.status.set(f"Pipes {self.problem.rows}×{self.problem.cols}{wrap_note}: bấm vào ô để xoay ống.")
        self._draw()

    def _build_number_pad(self, size: int) -> None:
        for child in self.number_pad.winfo_children():
            child.destroy()
        for value in range(1, size + 1):
            ttk.Button(self.number_pad, text=str(value), width=2, command=lambda v=value: self._enter_value(v)).pack(side="left", padx=1)
        if size:
            ttk.Button(self.number_pad, text="Xóa", command=lambda: self._enter_value(0)).pack(side="left", padx=(4, 1))

    def _replace_canvas(self) -> None:
        self.canvas.destroy()
        cls = FutoshikiCanvas if hasattr(self.problem, "size") else PipesCanvas
        self.canvas = cls(self.canvas_host, background="white", highlightthickness=0, takefocus=True)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._draw())
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-2>", lambda event: self._on_click(event, reverse=True))
        self.canvas.bind("<Button-3>", lambda event: self._on_click(event, reverse=True))

    def _draw(self) -> None:
        if self.problem is not None and self.current_state is not None and hasattr(self.canvas, "draw"):
            kwargs = {
                "solved": self.solved,
                "selected": self.selected,
                "conflicts": self.conflicts,
            }
            if isinstance(self.canvas, PipesCanvas):
                kwargs["water"] = pipes_water(self.problem, self.current_state)
            else:
                kwargs["active_cell"] = self.active_cell
                kwargs["active_kind"] = self.active_kind
                kwargs["domain_values"] = self.domain_values
                kwargs["active_value"] = self.active_value
                kwargs["rejected_values"] = (
                    self.cell_rejected.get(self.active_cell, set())
                    if self.active_cell is not None
                    else set()
                )
            self.canvas.draw(self.problem, self.current_state, **kwargs)

    def _remember(self, new_state: tuple[int, ...]) -> None:
        if new_state != self.current_state:
            self.current_state = new_state
            self.history.append(new_state)
            self.conflicts = set()
            self.solved = False
            self._draw()

    def _on_click(self, event, reverse: bool = False) -> None:
        if self.problem is None or self.current_state is None:
            return
        self.canvas.focus_set()
        index = self.canvas.cell_at(event.x, event.y)
        if index is None:
            return
        self._clear_domain_state()
        self.selected = index
        if hasattr(self.problem, "size"):
            if self.problem.givens[index]:
                self._set_status("Ô màu xám là số cho sẵn, không thể sửa.", kind="warning")
            else:
                self._set_status(f"Ô hàng {index // self.problem.size + 1}, cột {index % self.problem.size + 1}: nhập số 1–{self.problem.size}.", kind="info")
                self._draw()
        else:
            if self.problem.is_locked(index):
                self._set_status("Ô này đã khóa, không thể xoay.", kind="warning")
                self._draw()
                return
            self._remember(rotate_pipe(self.problem, self.current_state, index, -1 if reverse else 1))
            self._set_status("Đã xoay ống. Nhấn ‘Kiểm tra’ khi mạng đã nối hoàn chỉnh.", kind="info")

    def _on_key(self, event) -> None:
        if isinstance(event.widget, (ttk.Entry, tk.Entry)):
            return

        key = event.keysym
        char = event.char

        if key == "space":
            self.toggle_pause()
            return
        if key in {"Right", "s", "S"}:
            self.step()
            return
        if key == "Return":
            self.run()
            return
        if key == "Escape":
            self.cancel_search()
            return

        if self.problem is None or self.current_state is None or self.selected is None or not hasattr(self.problem, "size"):
            return
        if key in {"BackSpace", "Delete", "0"}:
            value = 0
        elif char.isdigit() and 1 <= int(char) <= self.problem.size:
            value = int(char)
        else:
            return
        self._enter_value(value)

    def _enter_value(self, value: int) -> None:
        if self.problem is None or self.current_state is None or self.selected is None or not hasattr(self.problem, "size"):
            self._set_status("Hãy chọn một ô trắng trước khi nhập số.", kind="warning")
            return
        self._clear_domain_state()
        updated = set_futoshiki_value(self.problem, self.current_state, self.selected, value)
        self._remember(updated)
        self.conflicts = futoshiki_conflicts(self.problem, updated)
        self._set_status("Có xung đột ở các ô đỏ." if self.conflicts else "Hợp lệ đến hiện tại. Tiếp tục điền các ô còn trống.", kind="rejected" if self.conflicts else "info")
        self._draw()

    def check(self) -> None:
        if self.problem is None or self.current_state is None:
            return
        if hasattr(self.problem, "size"):
            self.conflicts = futoshiki_conflicts(self.problem, self.current_state)
            incomplete = 0 in self.current_state
        else:
            self.conflicts = pipes_conflicts(self.problem, self.current_state)
            incomplete = False
        self.solved = self.problem.is_goal(self.current_state)
        if self.solved:
            self.conflicts.clear()
            self._set_status("🎉 Chính xác! Bạn đã giải xong puzzle.", kind="solved")
            messagebox.showinfo("Hoàn thành", "Chúc mừng! Bạn đã giải đúng puzzle.")
        elif self.conflicts:
            self._set_status(f"Chưa đúng: có {len(self.conflicts)} ô xung đột (tô đỏ).", kind="rejected")
        elif incomplete:
            self._set_status("Chưa hoàn thành: vẫn còn ô trống nhưng chưa có xung đột trực tiếp.", kind="warning")
        else:
            self._set_status("Chưa đúng: mạng ống chưa liên thông hoặc đang có chu trình.", kind="rejected")
        self._draw()

    def _get_solution(self) -> tuple[int, ...] | None:
        if self.solution is None and self.problem is not None:
            result = solve(self.problem, "gbfs", timeout=10, detailed_events=False)
            if result.status == "solved":
                self.solution = result.path[-1]
            return self.solution

    def hint(self) -> None:
        if self.problem is None or self.current_state is None:
            return
        solution = self._get_solution()
        if solution is None:
            self._set_status("Không tìm được gợi ý trong thời gian cho phép.", kind="warning")
            return
        candidates = [i for i, (current, target) in enumerate(zip(self.current_state, solution)) if current != target]
        if not candidates:
            self.check()
            return
        index = candidates[0]
        values = list(self.current_state)
        values[index] = solution[index]
        self.selected = index
        self._remember(tuple(values))
        if hasattr(self.problem, "size"):
            self._set_status(f"Gợi ý: ô hàng {index // self.problem.size + 1}, cột {index % self.problem.size + 1}.", kind="trial")
        else:
            self._set_status(f"Gợi ý: hướng đúng cho ô hàng {index // self.problem.cols + 1}, cột {index % self.problem.cols + 1}.", kind="trial")

    def pause_search(self) -> None:
        if self.controller.state.running and not self.controller.state.paused:
            self.controller.pause()
            self._set_status("Đã tạm dừng tìm kiếm. Nhấn ‘Tiếp tục’ hoặc [Space] để tiếp tục.", kind="warning")

    def resume_search(self) -> None:
        if self.controller.state.running and self.controller.state.paused:
            self.controller.resume()
            self._set_status(f"Đang tiếp tục tìm kiếm {self.algorithm.get().upper()}…", kind="info")
        elif not self.controller.state.running:
            self.run()

    def toggle_pause(self) -> None:
        if not self.controller.state.running:
            self.run()
        elif self.controller.state.paused:
            self.resume_search()
        else:
            self.pause_search()

    def run(self) -> None:
        if self.problem is None:
            return
        if self.controller.state.running and self.controller.state.paused:
            self.resume_search()
            return
        self.history = []
        self.conflicts = set()
        self._clear_domain_state()
        self.solved = False
        self._set_status(f"Đang chạy {self.algorithm.get().upper()}…", kind="info")
        self.controller.start(self.problem, self.algorithm.get())

    def step(self) -> None:
        if self.problem is None:
            return
        if not self.controller.state.running:
            self.history = []
            self.conflicts = set()
            self._clear_domain_state()
            self.solved = False
            self.controller.start(self.problem, self.algorithm.get(), paused=True)
        self.controller.step()

    def cancel_search(self) -> None:
        self.controller.cancel()
        self._clear_domain_state()
        self._set_status("Đã hủy quá trình tìm kiếm.", kind="default", frontier_items=())
        self._draw()

    def back(self) -> None:
        if len(self.history) > 1:
            self.history.pop()
            self.current_state = self.history[-1]
            self.conflicts = set()
            self.solved = False
            self._clear_domain_state()
            self._draw()
            self._set_status("Đã quay lại trạng thái trước.", kind="default")

    def reset(self) -> None:
        self.controller.cancel()
        if self.problem is not None:
            self.current_state = initial_play_state(self.problem)
            self.history = [self.current_state]
            self.selected = None
            self._clear_domain_state()
            self.conflicts = set()
            self.solved = False
            self._draw()
            self._set_status("Đã khôi phục đề ban đầu.", kind="default", frontier_items=())

    def _handle_event(self, event) -> None:
        self.metrics.update_event(event)
        if event.frontier_items is not None and hasattr(self, "queue_text"):
            if event.frontier_items:
                self.queue_text.set("  ".join(event.frontier_items))
            else:
                self.queue_text.set("[Trống]")

        if event.type == EventType.CELL_DOMAIN:
            self.active_cell = event.cell
            self.active_kind = "domain"
            self.domain_values = event.domain
            self.active_value = None
            if event.cell is not None:
                if event.domain is not None:
                    self.cell_domains[event.cell] = event.domain
                self.cell_rejected[event.cell] = set()
            self._prune_inactive_cells(self.current_state, keep_cell=event.cell)
            if event.message:
                self._set_status(event.message, kind="domain", frontier_items=event.frontier_items)
            self._draw()
        elif event.type == EventType.VALUE_TRIED:
            if event.state is not None:
                self.current_state = event.state
            self.active_cell = event.cell
            self.active_kind = "trial"
            self.active_value = event.value
            self.domain_values = event.domain or self.cell_domains.get(event.cell)
            if event.cell is not None and event.domain is not None:
                self.cell_domains[event.cell] = event.domain
            if event.message:
                self._set_status(event.message, kind="trial", frontier_items=event.frontier_items)
            self._draw()
        elif event.type == EventType.VALUE_REJECTED:
            if event.state is not None:
                self.current_state = event.state
            self.active_cell = event.cell
            self.active_kind = "rejected"
            self.domain_values = event.domain or self.cell_domains.get(event.cell)
            if event.cell is not None:
                if event.domain is not None:
                    self.cell_domains[event.cell] = event.domain
                if event.reason in {"all_failed", "empty_domain"} or (event.value is None and event.domain is not None):
                    self.cell_rejected[event.cell] = set(event.domain or ())
                    self.active_value = None
                elif event.value is not None:
                    self.active_value = event.value
                    self.cell_rejected.setdefault(event.cell, set()).add(event.value)
            self._prune_inactive_cells(self.current_state, keep_cell=event.cell)
            if event.message:
                self._set_status(event.message, kind="rejected", frontier_items=event.frontier_items)
            self._draw()
        elif event.state is not None and event.type in {EventType.STARTED, EventType.NODE_EXPANDED, EventType.GOAL_FOUND}:
            self.current_state = event.state
            self.history.append(event.state)
            self.solved = event.type == EventType.GOAL_FOUND
            self.active_kind = None
            if event.type == EventType.NODE_EXPANDED and event.action is not None and hasattr(event.action, "__getitem__"):
                self.active_cell = event.action[0]
                self.active_value = event.action[1]
                self.domain_values = self.cell_domains.get(self.active_cell)
                self._prune_inactive_cells(self.current_state, keep_cell=self.active_cell)
            elif event.type == EventType.GOAL_FOUND:
                self._clear_domain_state()
            self._draw()
        elif event.type == EventType.BACKTRACK:
            if event.state is not None:
                self.current_state = event.state
            self.active_kind = "rejected"
            if event.action is not None and hasattr(event.action, "__getitem__"):
                self.active_cell = event.action[0]
                self.active_value = event.action[1]
                self.domain_values = self.cell_domains.get(self.active_cell)
                if self.active_cell is not None and self.active_value is not None:
                    self.cell_rejected.setdefault(self.active_cell, set()).add(self.active_value)
            self._prune_inactive_cells(self.current_state, keep_cell=self.active_cell)
            if event.message:
                self._set_status(event.message, kind="rejected", frontier_items=event.frontier_items)
            self._draw()

        if event.type == EventType.GOAL_FOUND:
            self._set_status("🎉 Thuật toán đã tìm thấy nghiệm.", kind="solved", frontier_items=event.frontier_items)
        elif event.type == EventType.FINISHED and event.message != "solved":
            finish_map = {
                "Frontier exhausted": "Hàng đợi rỗng (không tìm thấy nghiệm)",
                "Search cancelled": "Đã hủy tìm kiếm",
                "timeout": "Hết thời gian tìm kiếm",
            }
            msg = finish_map.get(event.message, event.message)
            self._set_status(f"Tìm kiếm kết thúc: {msg}.", kind="default", frontier_items=event.frontier_items)
        elif event.type == EventType.ERROR:
            messagebox.showerror("Lỗi tìm kiếm", event.message)

    def _poll(self) -> None:
        self.controller.poll(self._handle_event, limit=1)
        delay = max(20, int(150 / max(0.1, self.speed.get())))
        self.root.after(delay, self._poll)

    def close(self) -> None:
        self.controller.cancel()
        self.root.destroy()
