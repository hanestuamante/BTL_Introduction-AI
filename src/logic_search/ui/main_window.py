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
        self.conflicts: set[int] = set()
        self.solution: tuple[int, ...] | None = None
        self.solved = False
        self.speed = tk.DoubleVar(value=1.0)
        self.algorithm = tk.StringVar(value="dfs")
        self.input_path = tk.StringVar(value=str(DEFAULT_INPUT))
        self.status = tk.StringVar(value="Chọn ô trống và nhập số 1–N.")
        self._build()
        self.root.bind("<Key>", self._on_key)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(30, self._poll)
        self.load()

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
        ttk.Combobox(search, textvariable=self.algorithm, values=("dfs", "gbfs"), state="readonly", width=7).pack(side="left", padx=5)
        for text, command in (("▶ Chạy", self.run), ("⏸ Dừng", self.controller.pause), ("▷ Tiếp tục", self.controller.resume), ("→ Từng bước", self.step), ("⏹ Hủy", self.cancel_search)):
            ttk.Button(search, text=text, command=command).pack(side="left", padx=2)
        ttk.Label(search, text="Tốc độ:").pack(side="left", padx=(12, 2))
        ttk.Scale(search, from_=0.25, to=4.0, variable=self.speed, orient="horizontal", length=140).pack(side="left")

        status_bar = ttk.Frame(self.root, padding=(12, 5, 12, 10))
        status_bar.pack(fill="x")
        ttk.Label(status_bar, textvariable=self.status, anchor="w").pack(fill="x")

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
        self.conflicts = set()
        self.solution = None
        self.solved = False
        self._replace_canvas()
        if hasattr(self.problem, "size"):
            self._build_number_pad(self.problem.size)
            self.help_label.configure(text="• Bấm ô trắng rồi nhập 1–N\n• Mỗi hàng/cột không trùng số\n• Thỏa dấu <, >, ∧, ∨\n• Backspace để xóa ô")
            self.status.set(f"Futoshiki {self.problem.size}×{self.problem.size}: chọn ô trắng để bắt đầu.")
        else:
            self._build_number_pad(0)
            self.help_label.configure(text="• Bấm trái để xoay 90°\n• Bấm phải để xoay ngược\n• Mọi đầu ống phải khớp\n• Mạng ống là một cây liên thông\n• Viền cam đứt nét: ô khóa\n• Vòng tròn đỏ: nguồn nước\n• Ống xanh dương: có nước")
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
        if self.problem is None or self.current_state is None or not hasattr(self.canvas, "draw"):
            return
        if isinstance(self.canvas, PipesCanvas):
            water = pipes_water(self.problem, self.current_state)
            self.canvas.draw(self.problem, self.current_state, solved=self.solved, selected=self.selected, conflicts=self.conflicts, water=water)
        else:
            self.canvas.draw(self.problem, self.current_state, solved=self.solved, selected=self.selected, conflicts=self.conflicts)

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
        self.selected = index
        if hasattr(self.problem, "size"):
            if self.problem.givens[index]:
                self.status.set("Ô màu xám là số cho sẵn, không thể sửa.")
            else:
                self.status.set(f"Ô hàng {index // self.problem.size + 1}, cột {index % self.problem.size + 1}: nhập số 1–{self.problem.size}.")
                self._draw()
        else:
            if self.problem.is_locked(index):
                self.status.set("Ô này đã khóa, không thể xoay.")
                self._draw()
                return
            self._remember(rotate_pipe(self.problem, self.current_state, index, -1 if reverse else 1))
            self.status.set("Đã xoay ống. Nhấn ‘Kiểm tra’ khi mạng đã nối hoàn chỉnh.")

    def _on_key(self, event) -> None:
        if self.problem is None or self.current_state is None or self.selected is None or not hasattr(self.problem, "size"):
            return
        if event.keysym in {"BackSpace", "Delete", "0"}:
            value = 0
        elif event.char.isdigit() and 1 <= int(event.char) <= self.problem.size:
            value = int(event.char)
        else:
            return
        self._enter_value(value)

    def _enter_value(self, value: int) -> None:
        if self.problem is None or self.current_state is None or self.selected is None or not hasattr(self.problem, "size"):
            self.status.set("Hãy chọn một ô trắng trước khi nhập số.")
            return
        updated = set_futoshiki_value(self.problem, self.current_state, self.selected, value)
        self._remember(updated)
        self.conflicts = futoshiki_conflicts(self.problem, updated)
        self.status.set("Có xung đột ở các ô đỏ." if self.conflicts else "Hợp lệ đến hiện tại. Tiếp tục điền các ô còn trống.")
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
            self.status.set("🎉 Chính xác! Bạn đã giải xong puzzle.")
            messagebox.showinfo("Hoàn thành", "Chúc mừng! Bạn đã giải đúng puzzle.")
        elif self.conflicts:
            self.status.set(f"Chưa đúng: có {len(self.conflicts)} ô xung đột (tô đỏ).")
        elif incomplete:
            self.status.set("Chưa hoàn thành: vẫn còn ô trống nhưng chưa có xung đột trực tiếp.")
        else:
            self.status.set("Chưa đúng: mạng ống chưa liên thông hoặc đang có chu trình.")
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
            self.status.set("Không tìm được gợi ý trong thời gian cho phép.")
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
            self.status.set(f"Gợi ý: ô hàng {index // self.problem.size + 1}, cột {index % self.problem.size + 1}.")
        else:
            self.status.set(f"Gợi ý: hướng đúng cho ô hàng {index // self.problem.cols + 1}, cột {index % self.problem.cols + 1}.")

    def run(self) -> None:
        if self.problem is None:
            return
        self.history = []
        self.conflicts = set()
        self.solved = False
        self.status.set(f"Đang chạy {self.algorithm.get().upper()}…")
        self.controller.start(self.problem, self.algorithm.get())

    def step(self) -> None:
        if self.problem is None:
            return
        if not self.controller.state.running:
            self.history = []
            self.conflicts = set()
            self.solved = False
            self.controller.start(self.problem, self.algorithm.get(), paused=True)
        self.controller.step()
        self.status.set("Step mode: mở rộng thêm một node.")

    def cancel_search(self) -> None:
        self.controller.cancel()
        self.status.set("Đã hủy quá trình tìm kiếm.")

    def back(self) -> None:
        if len(self.history) > 1:
            self.history.pop()
            self.current_state = self.history[-1]
            self.conflicts = set()
            self.solved = False
            self._draw()
            self.status.set("Đã quay lại trạng thái trước.")

    def reset(self) -> None:
        self.controller.cancel()
        if self.problem is not None:
            self.current_state = initial_play_state(self.problem)
            self.history = [self.current_state]
            self.selected = None
            self.conflicts = set()
            self.solved = False
            self._draw()
            self.status.set("Đã khôi phục đề ban đầu.")

    def _handle_event(self, event) -> None:
        self.metrics.update_event(event)
        if event.state is not None and event.type in {EventType.STARTED, EventType.NODE_EXPANDED, EventType.GOAL_FOUND}:
            self.current_state = event.state
            self.history.append(event.state)
            self.solved = event.type == EventType.GOAL_FOUND
            self._draw()
        if event.type == EventType.GOAL_FOUND:
            self.status.set("Thuật toán đã tìm thấy nghiệm.")
        elif event.type == EventType.FINISHED and event.message != "solved":
            self.status.set(f"Tìm kiếm kết thúc: {event.message}.")
        elif event.type == EventType.ERROR:
            messagebox.showerror("Lỗi tìm kiếm", event.message)

    def _poll(self) -> None:
        self.controller.poll(self._handle_event, max(1, int(self.speed.get())))
        self.root.after(max(20, int(140 / self.speed.get())), self._poll)

    def close(self) -> None:
        self.controller.cancel()
        self.root.destroy()
