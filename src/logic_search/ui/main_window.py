from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from logic_search.core.events import EventType
from logic_search.io import load_problem
from logic_search.puzzles.pipes.model import orientation_label
from logic_search.search.solver import solve

from .controller import SearchController
from .futoshiki_canvas import FutoshikiCanvas
from .game_logic import futoshiki_conflicts, initial_play_state, pipes_conflicts, pipes_water, rotate_pipe, set_futoshiki_value
from .metrics_panel import MetricsPanel
from .pipes_canvas import SEARCH_LEGEND, SEARCH_STYLES, PipesCanvas

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = ROOT / "data/futoshiki/futoshiki-4x4-easy-seed-201.json"

FUTOSHIKI_BOTTOM_HINT = "Shortcuts: [Enter] Run - [Space] Pause/Resume - [Right / S] Step - [Esc] Cancel - Click a cell and enter 1-N"

BUTTON_SHORTCUTS = {
    "browse": "Ctrl+O", "load": "Ctrl+L", "check": "C", "hint": "H",
    "back": "Ctrl+Z", "reset": "Ctrl+R", "toggle_flag": "F", "clear_flags": "Ctrl+Shift+F",
    "run": "Enter", "pause_search": "Space", "resume_search": "Space",
    "step": "S / Right", "cancel_search": "Esc",
}


def action_label(text: str, action: str) -> str:
    return f"{text} ({BUTTON_SHORTCUTS[action]})"

CARD_THEMES = {
    "domain": {
        "bg": "#f0f9ff",
        "border": "#0284c7",
        "badge_bg": "#e0f2fe",
        "badge_fg": "#0369a1",
        "text_fg": "#0c4a6e",
        "badge_text": "CHECK DOMAIN",
    },
    "trial": {
        "bg": "#fffbeb",
        "border": "#d97706",
        "badge_bg": "#fef3c7",
        "badge_fg": "#b45309",
        "text_fg": "#78350f",
        "badge_text": "TRYING VALUE",
    },
    "rejected": {
        "bg": "#fef2f2",
        "border": "#dc2626",
        "badge_bg": "#fee2e2",
        "badge_fg": "#b91c1c",
        "text_fg": "#7f1d1d",
        "badge_text": "REJECTED",
    },
    "solved": {
        "bg": "#f0fdf4",
        "border": "#16a34a",
        "badge_bg": "#dcfce7",
        "badge_fg": "#15803d",
        "text_fg": "#14532d",
        "badge_text": "SOLVED",
    },
    "warning": {
        "bg": "#fff7ed",
        "border": "#f97316",
        "badge_bg": "#ffedd5",
        "badge_fg": "#c2410c",
        "text_fg": "#7c2d12",
        "badge_text": "NOTICE",
    },
    "info": {
        "bg": "#f8fafc",
        "border": "#3b82f6",
        "badge_bg": "#eff6ff",
        "badge_fg": "#1d4ed8",
        "text_fg": "#1e293b",
        "badge_text": "ACTIVITY",
    },
    "default": {
        "bg": "#f8fafc",
        "border": "#94a3b8",
        "badge_bg": "#f1f5f9",
        "badge_fg": "#475569",
        "text_fg": "#334155",
        "badge_text": "INSTRUCTIONS",
    },
}


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Logic Puzzle Search - Play & Visualize")
        self.root.geometry("1080x760")
        self.root.minsize(850, 620)
        self.controller = SearchController()
        self.problem = None
        self.current_state: tuple[int, ...] | None = None
        self.history: list[tuple[int, ...]] = []
        self.flags: set[int] = set()
        self.flag_history: list[set[int]] = []
        self.flag_target: int | None = None
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
        self.status = tk.StringVar(value="Select an empty cell and enter a number from 1 to N.")
        self.futoshiki_step_text = tk.StringVar(value="Ready: select a white cell to begin.")
        self.queue_text = tk.StringVar(value="[Empty]")
        self._build()
        self._shortcut_tag = f"LogicSearchShortcuts{id(self)}"
        self._shortcut_keys_down: set[str] = set()
        self.root.bind_class(self._shortcut_tag, "<KeyPress>", self._on_key)
        self.root.bind_class(self._shortcut_tag, "<KeyRelease>", self._on_key_release)
        self._install_shortcuts(self.root)
        self.root.bind("<Key>", self._on_futoshiki_key)
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
            self.step_right_frame.configure(
                bg=theme["bg"],
                highlightbackground=theme["border"],
                highlightcolor=theme["border"],
            )
            is_dfs = self.algorithm.get() == "dfs"
            q_badge_title = "STACK (LIFO)" if is_dfs else "PRIORITY QUEUE"
            self.queue_badge.configure(
                text=q_badge_title,
                bg=theme["badge_bg"],
                fg=theme["badge_fg"],
            )
            self.queue_label.configure(bg=theme["bg"], fg=theme["text_fg"])
            if hasattr(self, "queue_items_frame"):
                self.queue_items_frame.configure(bg=theme["bg"])
            if hasattr(self, "queue_top_indicator"):
                self.queue_top_indicator.configure(
                    text="TOP" if is_dfs else "- QUEUE TAIL -",
                    bg=theme["bg"],
                    fg=theme["border"] if is_dfs else "#94a3b8",
                )
            if hasattr(self, "queue_bottom_indicator"):
                self.queue_bottom_indicator.configure(
                    text="- STACK BOTTOM -" if is_dfs else "HEAD (MIN H - NEXT POP)",
                    bg=theme["bg"],
                    fg="#94a3b8" if is_dfs else theme["border"],
                )
            if frontier_items is not None:
                if frontier_items:
                    self.queue_text.set("  ".join(frontier_items))
                    self._render_vertical_frontier(frontier_items, is_dfs, theme)
                else:
                    self.queue_text.set("[Empty]")
                    self._render_vertical_frontier((), is_dfs, theme)

    def _render_vertical_frontier(self, items: tuple[str, ...], is_dfs: bool, theme: dict) -> None:
        if not hasattr(self, "queue_items_frame"):
            return
        for child in self.queue_items_frame.winfo_children():
            if child != self.queue_label:
                child.destroy()
        if not items:
            self.queue_label.configure(text="[Empty]", fg="#94a3b8", bg=theme["bg"])
            self.queue_label.pack(side="top", fill="x", pady=20)
            return

        self.queue_label.pack_forget()

        display_items = list(items)
        if not is_dfs:
            display_items.reverse()

        max_show = 10
        if len(display_items) > max_show:
            truncated = len(display_items) - max_show
            if is_dfs:
                visible = display_items[:max_show]
                extra_note = f"(+ {truncated} more items at the bottom)"
                extra_at_bottom = True
            else:
                visible = display_items[-max_show:]
                extra_note = f"(+ {truncated} more items above)"
                extra_at_bottom = False
        else:
            visible = display_items
            extra_note = None
            extra_at_bottom = False

        if extra_note and not extra_at_bottom:
            lbl = tk.Label(self.queue_items_frame, text=extra_note, font=("Segoe UI", 7, "italic"), bg=theme["bg"], fg="#94a3b8")
            lbl.pack(side="top", fill="x", pady=(0, 2))

        for idx, item in enumerate(visible):
            is_active_end = (idx == 0 if is_dfs else idx == len(visible) - 1)
            card = tk.Frame(
                self.queue_items_frame,
                bg="#ffffff" if is_active_end else "#f1f5f9",
                highlightthickness=1,
                highlightbackground=theme["border"] if is_active_end else "#cbd5e1",
                padx=4,
                pady=2,
            )
            card.pack(side="top", fill="x", padx=2, pady=2)
            prefix = "* " if is_active_end else "  "
            item_lbl = tk.Label(
                card,
                text=f"{prefix}{item}",
                font=("Segoe UI", 8, "bold" if is_active_end else "normal"),
                bg="#ffffff" if is_active_end else "#f1f5f9",
                fg=theme["text_fg"] if is_active_end else "#475569",
                anchor="center",
            )
            item_lbl.pack(fill="x")

        if extra_note and extra_at_bottom:
            lbl = tk.Label(self.queue_items_frame, text=extra_note, font=("Segoe UI", 7, "italic"), bg=theme["bg"], fg="#94a3b8")
            lbl.pack(side="top", fill="x", pady=(2, 0))

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
        self.pipes_search_view = False
        self._previous_pipe_node_id = None
        self._pipe_branch_state = None

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
        self.browse_button = ttk.Button(top, text="Browse...", command=self.browse)
        self.browse_button.pack(side="left")
        self.load_button = ttk.Button(top, text="Load", command=self.load)
        self.load_button.pack(side="left", padx=(6, 0))

        body = ttk.Frame(self.root, padding=(10, 5))
        body.pack(fill="both", expand=True)
        self.canvas_host = ttk.Frame(body)
        self.canvas_host.pack(side="left", fill="both", expand=True)

        # Futoshiki Step Card (top of game board - instruction only)
        self.step_card = tk.Frame(
            self.canvas_host,
            bg="#f8fafc",
            highlightthickness=2,
            highlightbackground="#94a3b8",
            padx=10,
            pady=6,
        )

        # Instructional step (full width across top)
        self.step_left_frame = tk.Frame(self.step_card, bg="#f8fafc")
        self.step_left_frame.pack(side="left", fill="both", expand=True)

        self.step_badge = tk.Label(
            self.step_left_frame,
            text="INSTRUCTIONS",
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
            wraplength=640,
        )
        self.step_label.pack(side="left", fill="both", expand=True)

        # Keep step_divider for backwards compatibility
        self.step_divider = tk.Frame(self.step_card, bg="#cbd5e1", width=1)

        def _on_step_card_resize(event):
            self.step_label.configure(wraplength=max(200, event.width - 150))

        self.step_card.bind("<Configure>", _on_step_card_resize)

        self.pipes_legend = ttk.Frame(self.canvas_host)
        for column, (kind, label) in enumerate(SEARCH_LEGEND):
            bg, border = SEARCH_STYLES[kind]
            tk.Label(
                self.pipes_legend, text=label, bg=bg, fg="#1f2937", padx=4, pady=3,
                highlightthickness=1, highlightbackground=border,
            ).grid(row=0, column=column, padx=2, sticky="ew")
        ttk.Label(
            self.pipes_legend,
            text="Purple = assigned in this branch, not confirmed. Blue tubes = water.\n"
                 "N / E / S / W = North / East / South / West. Step pauses at each search action.",
            wraplength=520,
        ).grid(row=1, column=0, columnspan=len(SEARCH_LEGEND), sticky="w", pady=(4, 0))

        # Board row: horizontal container for Canvas and Vertical Stack/Priority Queue Frame
        self.board_row = ttk.Frame(self.canvas_host)
        self.board_row.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(self.board_row, background="white", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Vertical Frame for Stack / Priority Queue (right of game board)
        self.step_right_frame = tk.Frame(
            self.board_row,
            bg="#f8fafc",
            highlightthickness=2,
            highlightbackground="#94a3b8",
            padx=8,
            pady=8,
            width=210,
        )
        self.step_right_frame.pack_propagate(False)
        self.step_right_frame.pack(side="right", fill="y", padx=(8, 0))

        self.queue_badge = tk.Label(
            self.step_right_frame,
            text="STACK (LIFO)",
            font=("Segoe UI", 9, "bold"),
            bg="#f1f5f9",
            fg="#475569",
            padx=8,
            pady=3,
        )
        self.queue_badge.pack(side="top", fill="x", pady=(0, 4))

        self.queue_top_indicator = tk.Label(
            self.step_right_frame,
            text="TOP",
            font=("Segoe UI", 8, "bold"),
            bg="#f8fafc",
            fg="#0284c7",
        )
        self.queue_top_indicator.pack(side="top", fill="x", pady=(0, 4))

        self.queue_items_frame = tk.Frame(self.step_right_frame, bg="#f8fafc")
        self.queue_items_frame.pack(side="top", fill="both", expand=True)

        self.queue_label = tk.Label(
            self.queue_items_frame,
            textvariable=self.queue_text,
            font=("Segoe UI", 9, "bold"),
            bg="#f8fafc",
            fg="#334155",
            anchor="center",
            justify="center",
            wraplength=190,
        )
        self.queue_label.pack(side="top", fill="x", pady=10)

        self.queue_bottom_indicator = tk.Label(
            self.step_right_frame,
            text="- STACK BOTTOM -",
            font=("Segoe UI", 8, "bold"),
            bg="#f8fafc",
            fg="#94a3b8",
        )
        self.queue_bottom_indicator.pack(side="bottom", fill="x", pady=(4, 0))
        side = ttk.Frame(body)
        side.pack(side="right", fill="y", padx=(10, 0))
        self.metrics = MetricsPanel(side)
        self.metrics.pack(fill="x")
        help_box = ttk.LabelFrame(side, text="How to play", padding=8)
        help_box.pack(fill="x", pady=(10, 0))
        self.help_label = ttk.Label(help_box, text="", justify="left", wraplength=220)
        self.help_label.pack(anchor="w")

        self.play_controls = ttk.LabelFrame(self.root, text="Play", padding=8)
        self.play_controls.pack(fill="x", padx=10, pady=5)
        self.search_controls = ttk.LabelFrame(self.root, text="Search visualization", padding=8)
        self.search_controls.pack(fill="x", padx=10, pady=5)
        self._build_controls()

        status_bar = ttk.Frame(self.root, padding=(12, 5, 12, 10))
        status_bar.pack(fill="x")
        ttk.Label(status_bar, textvariable=self.status, anchor="w").pack(fill="x")

    def _is_pipes(self) -> bool:
        return self.problem is not None and not hasattr(self.problem, "size")

    def _build_controls(self) -> None:
        for panel in (self.play_controls, self.search_controls):
            for child in panel.winfo_children():
                child.destroy()
        play, search = self.play_controls, self.search_controls
        pipes = self._is_pipes()
        self.browse_button.configure(text=action_label("Browse", "browse") if pipes else "Browse...")
        self.load_button.configure(text=action_label("Load", "load") if pipes else "Load")
        if not pipes:
            for text, command in (("Check", self.check), ("Hint", self.hint), ("Undo", self.back), ("Reset", self.reset)):
                ttk.Button(play, text=text, command=command).pack(side="left", padx=3)
            ttk.Separator(play, orient="vertical").pack(side="left", fill="y", padx=10)
            ttk.Label(play, text="Number:").pack(side="left")
            self.number_pad = ttk.Frame(play)
            self.number_pad.pack(side="left", padx=4)

            ttk.Label(search, text="Algorithm:").pack(side="left")
            combo = ttk.Combobox(search, textvariable=self.algorithm, values=("dfs", "gbfs"), state="readonly", width=7)
            combo.pack(side="left", padx=5)
            combo.bind("<<ComboboxSelected>>", lambda _e: self._on_algorithm_change())
            for text, command in (
                ("Run", self.run),
                ("Pause", self.pause_search),
                ("Resume", self.resume_search),
                ("Step", self.step),
                ("Cancel", self.cancel_search),
            ):
                ttk.Button(search, text=text, command=command).pack(side="left", padx=2)
            ttk.Label(search, text="Speed:").pack(side="left", padx=(12, 2))
            ttk.Scale(search, from_=0.25, to=4.0, variable=self.speed, orient="horizontal", length=140).pack(side="left")

            return
        actions = ttk.Frame(play)
        actions.pack(fill="x")
        for text, command in (("Check", self.check), ("Hint", self.hint), ("Undo", self.back), ("Reset", self.reset)):
            ttk.Button(actions, text=action_label(text, command.__name__), command=command).pack(side="left", padx=3)
        self.flag_button = ttk.Button(actions, text=action_label("Flag", "toggle_flag"), command=self.toggle_flag)
        self.flag_button.pack(side="left", padx=3)
        self.clear_flags_button = ttk.Button(actions, text=action_label("Clear flags", "clear_flags"), command=self.clear_flags)
        self.clear_flags_button.pack(side="left", padx=3)
        inputs = ttk.Frame(play)
        inputs.pack(fill="x", pady=(5, 0))
        self.input_label = ttk.Label(inputs, text="Number:")
        self.input_label.pack(side="left")
        self.number_pad = ttk.Frame(inputs)
        self.number_pad.pack(side="left", padx=4)
        self.flag_count = tk.StringVar(value="Flags: 0 (your notes)")
        ttk.Label(inputs, textvariable=self.flag_count).pack(side="right", padx=4)

        settings = ttk.Frame(search)
        settings.pack(fill="x")
        ttk.Label(settings, text="Algorithm (A):").pack(side="left")
        combo = ttk.Combobox(settings, textvariable=self.algorithm, values=("dfs", "gbfs"), state="readonly", width=7)
        self.algorithm_combo = combo
        combo.pack(side="left", padx=5)
        combo.bind("<<ComboboxSelected>>", lambda _e: self._on_algorithm_change())
        ttk.Label(settings, text="Speed (+/-):").pack(side="left", padx=(12, 2))
        ttk.Scale(settings, from_=0.25, to=4.0, variable=self.speed, orient="horizontal", length=140).pack(side="left")
        controls = ttk.Frame(search)
        controls.pack(fill="x", pady=(5, 0))
        for text, command in (
            ("Run", self.run),
            ("Pause", self.pause_search),
            ("Resume", self.resume_search),
            ("Step", self.step),
            ("Cancel", self.cancel_search),
        ):
            ttk.Button(controls, text=action_label(text, command.__name__), command=command).pack(side="left", padx=2)

        self._install_shortcuts(play)
        self._install_shortcuts(search)

    def _on_algorithm_change(self) -> None:
        if hasattr(self, "queue_badge") and hasattr(self, "problem") and self.problem is not None and hasattr(self.problem, "size"):
            is_dfs = self.algorithm.get() == "dfs"
            self.queue_badge.configure(text="STACK (LIFO)" if is_dfs else "PRIORITY QUEUE")
            if hasattr(self, "queue_top_indicator"):
                self.queue_top_indicator.configure(text="TOP" if is_dfs else "- QUEUE TAIL -")
            if hasattr(self, "queue_bottom_indicator"):
                self.queue_bottom_indicator.configure(text="- STACK BOTTOM -" if is_dfs else "HEAD (MIN H - NEXT POP)")

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
            messagebox.showerror("Invalid input", str(exc))
            return
        self.current_state = initial_play_state(self.problem)
        self.history = [self.current_state]
        self.flags = set()
        self.flag_history = [set()]
        self.flag_target = None
        self.selected = None
        self._clear_domain_state()
        self.conflicts = set()
        self.solution = None
        self.solved = False
        self._shortcut_keys_down.clear()
        self._build_controls()
        self._replace_canvas()
        if hasattr(self.problem, "size"):
            self.pipes_legend.pack_forget()
            if hasattr(self, "board_row"):
                self.step_card.pack(side="top", fill="x", padx=4, pady=(2, 6), before=self.board_row)
            else:
                self.step_card.pack(side="top", fill="x", padx=4, pady=(2, 6), before=self.canvas)
            if hasattr(self, "step_right_frame"):
                self.step_right_frame.pack(side="right", fill="y", padx=(8, 0))
            self._update_futoshiki_card("default", f"Futoshiki {self.problem.size}x{self.problem.size}: select a white cell to begin.", frontier_items=())
            self._build_number_pad(self.problem.size)
            self.help_label.configure(
                text="- [Space]: Pause/Resume  - [Right / S]: Step\n"
                     "- [Enter]: Run  - [Esc]: Cancel search\n"
                     "- Click a white cell and enter 1-N\n"
                     "- Backspace/0 clears the cell"
            )
            self.status.set(FUTOSHIKI_BOTTOM_HINT)
        else:
            self.step_card.pack_forget()
            self.pipes_legend.pack(side="top", fill="x", padx=4, pady=(2, 6), before=self.board_row)
            if hasattr(self, "step_right_frame"):
                self.step_right_frame.pack_forget()
            self._build_number_pad(0)
            self.help_label.configure(
                text="- [Space]: Pause/Resume  - [Right / S]: Step\n"
                     "- [Enter]: Run  - [Esc]: Cancel search\n"
                     "- Left-click to rotate 90 degrees; right-click to reverse\n"
                     "- Match every pipe end; the network must be a tree\n"
                     "- Dashed orange border: locked cell\n"
                     "- Red dot: source; blue pipes: water\n"
                     "- Hover + Q/E: rotate pipe\n"
                     "- Hover + F or Shift+click: flag/unflag\n"
                     "- Ctrl+click: select without rotating\n"
                     "- Purple flags are your notes"
            )
            wrap_note = " - wrap-around (dashed purple border)" if self.problem.wrap else ""
            self.status.set(f"Pipes {self.problem.rows}x{self.problem.cols}{wrap_note}: click a cell to rotate its pipe.")
        self._draw()

    def _build_number_pad(self, size: int) -> None:
        for child in self.number_pad.winfo_children():
            child.destroy()
        for value in range(1, size + 1):
            ttk.Button(self.number_pad, text=str(value), width=2, command=lambda v=value: self._enter_value(v)).pack(side="left", padx=1)
        if size:
            ttk.Button(self.number_pad, text="Clear", command=lambda: self._enter_value(0)).pack(side="left", padx=(4, 1))
        else:
            self.input_label.configure(text="Pipe:")
            ttk.Button(self.number_pad, text="Rotate CCW (Q)", command=lambda: self.rotate_selected_pipe(-1)).pack(side="left", padx=2)
            ttk.Button(self.number_pad, text="Rotate CW (E)", command=lambda: self.rotate_selected_pipe(1)).pack(side="left", padx=2)
        self._install_shortcuts(self.number_pad)

    def _replace_canvas(self) -> None:
        self.canvas.destroy()
        cls = FutoshikiCanvas if hasattr(self.problem, "size") else PipesCanvas
        parent = self.board_row if hasattr(self, "board_row") else self.canvas_host
        self.canvas = cls(parent, background="white", highlightthickness=0, takefocus=True)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._draw())
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-2>", lambda event: self._on_click(event, reverse=True))
        self.canvas.bind("<Button-3>", lambda event: self._on_click(event, reverse=True))
        if self._is_pipes():
            self.canvas.bind("<Motion>", self._on_pipe_hover)
            self.canvas.bind("<Enter>", self._on_pipe_hover)
        self._install_shortcuts(self.canvas)

    def _draw(self) -> None:
        if self.problem is not None and self.current_state is not None and hasattr(self.canvas, "draw"):
            kwargs = {
                "solved": self.solved,
                "selected": self.selected,
                "conflicts": self.conflicts,
            }
            if isinstance(self.canvas, PipesCanvas):
                kwargs["flags"] = getattr(self, "flags", set())
                kwargs["water"] = pipes_water(self.problem, self.current_state)
                kwargs["search_view"] = getattr(self, "pipes_search_view", False)
                kwargs["active_cell"] = self.active_cell
                kwargs["active_kind"] = self.active_kind
                kwargs["active_value"] = self.active_value
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
        self._update_flag_controls()

    def _search_busy(self) -> bool:
        controller = getattr(self, "controller", None)
        if controller is None:
            return False
        events = getattr(controller, "events", None)
        return controller.state.running or (events is not None and not events.empty())

    def _update_flag_controls(self) -> None:
        if not self._is_pipes() or not hasattr(self, "flag_button"):
            return
        flags = getattr(self, "flags", set())
        busy = self._search_busy()
        target = self.flag_target
        can_flag = target is not None and self.current_state is not None and bool(self.current_state[target])
        self.flag_button.configure(
            text=action_label("Unflag" if target in flags else "Flag", "toggle_flag"),
            state="normal" if can_flag and not busy else "disabled",
        )
        self.clear_flags_button.configure(state="normal" if flags and not busy else "disabled")
        self.flag_count.set(f"Flags: {len(flags)} (your notes)")
        self.algorithm_combo.configure(state="disabled" if busy else "readonly")

    def _append_history(self, state: tuple[int, ...]) -> None:
        if not self._is_pipes():
            self.history.append(state)
            return
        if not hasattr(self, "flag_history") or len(self.flag_history) != len(self.history):
            self.flag_history = [set() for _ in self.history]
        self.history.append(state)
        self.flag_history.append(set(getattr(self, "flags", set())))

    def _on_pipe_hover(self, event) -> None:
        if self._is_pipes():
            index = self.canvas.cell_at(event.x, event.y)
            if index is not None:
                self.flag_target = index
                self._update_flag_controls()

    def _pipe_under_pointer(self) -> int | None:
        if not self._is_pipes():
            return None
        x, y = self.canvas.winfo_pointerxy()
        return self.canvas.cell_at(x - self.canvas.winfo_rootx(), y - self.canvas.winfo_rooty())

    def flag_under_pointer(self) -> None:
        if not self._is_pipes():
            return
        index = self._pipe_under_pointer()
        if index is None:
            self._set_status("Move the pointer over a pipe and press F to flag it.", kind="warning")
            return
        self.flag_target = index
        self.toggle_flag(index)

    def toggle_flag(self, index: int | None = None) -> None:
        if not self._is_pipes():
            return
        if self._search_busy():
            self._set_status("Cancel the search before editing player flags.", kind="warning")
            return
        # The toolbar uses the last hovered pipe when the pointer moves onto it.
        if index is None:
            index = self.flag_target
        if self.current_state is None or index is None:
            self._set_status("Hover over a pipe first. Press F or Shift+click to flag it.", kind="warning")
            return
        if not self.current_state[index]:
            self._set_status("Reset the board before flagging an unassigned pipe.", kind="warning")
            self._draw()
            return
        if index in self.flags:
            self.flags.remove(index)
            message = "Player flag removed."
        else:
            self.flags.add(index)
            message = "Player flag added. This is your note, not a verified answer."
        self._append_history(self.current_state)
        self._set_status(message, kind="info")
        self._draw()

    def clear_flags(self) -> None:
        if not self._is_pipes():
            return
        if self._search_busy() or not self.flags:
            return
        self.flags = set()
        self._append_history(self.current_state)
        self._set_status("All player flags cleared.", kind="info")
        self._draw()

    def rotate_selected_pipe(self, turns: int) -> None:
        self._rotate_pipe_at(self.selected, turns)

    def rotate_pipe_under_pointer(self, turns: int) -> None:
        if not self._is_pipes():
            return
        index = self._pipe_under_pointer()
        if index is None:
            self._set_status("Move the pointer over a pipe and press Q/E to rotate it.", kind="warning")
            return
        self._rotate_pipe_at(index, turns)

    def _rotate_pipe_at(self, index: int | None, turns: int) -> None:
        if self.problem is None or hasattr(self.problem, "size") or self.current_state is None:
            return
        if self._search_busy():
            self._set_status("Cancel the search before rotating pipes manually.", kind="warning")
            return
        if index is None:
            self._set_status("Select a pipe with Ctrl+click before rotating it.", kind="warning")
            return
        if self.problem.is_locked(index):
            self._set_status("This cell is locked and cannot be rotated.", kind="warning")
            self._draw()
            return
        self._clear_domain_state()
        self._remember(rotate_pipe(self.problem, self.current_state, index, turns))
        self._set_status("Pipe rotated. Press 'Check (C)' when the network is fully connected.", kind="info")

    def _remember(self, new_state: tuple[int, ...]) -> None:
        if new_state != self.current_state:
            if self._is_pipes():
                self.flags = {index for index in getattr(self, "flags", set()) if new_state[index] == self.current_state[index]}
            self.current_state = new_state
            self._append_history(new_state)
            self.conflicts = set()
            self.solved = False
            self._draw()

    def _on_click(self, event, reverse: bool = False) -> None:
        if self.problem is None or self.current_state is None:
            return
        if self._is_pipes() and self._search_busy():
            self._set_status("Cancel the search before editing pipes or player notes.", kind="warning")
            return
        self.canvas.focus_set()
        index = self.canvas.cell_at(event.x, event.y)
        if index is None:
            return
        modifiers = getattr(event, "state", 0)
        if self._is_pipes():
            self.flag_target = index
            if modifiers & 0x0001:
                self.toggle_flag(index)
                return
        self._clear_domain_state()
        self.selected = index
        if self._is_pipes() and modifiers & 0x0004:
            self._draw()
            return
        if hasattr(self.problem, "size"):
            if self.problem.givens[index]:
                self._set_status("Gray cells contain given numbers and cannot be edited.", kind="warning")
            else:
                self._set_status(f"Cell at row {index // self.problem.size + 1}, column {index % self.problem.size + 1}: enter 1-{self.problem.size}.", kind="info")
                self._draw()
        else:
            self.rotate_selected_pipe(-1 if reverse else 1)

    def _on_futoshiki_key(self, event) -> None:
        if self._is_pipes():
            return
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

    def _install_shortcuts(self, widget) -> None:
        tag = getattr(self, "_shortcut_tag", None)
        if tag is None:
            return
        widget.bindtags((tag, *(name for name in widget.bindtags() if name != tag)))
        for child in widget.winfo_children():
            self._install_shortcuts(child)

    def _on_key_release(self, event):
        if not self._is_pipes():
            return
        key = event.keysym.lower()
        if key in self._shortcut_keys_down:
            self._shortcut_keys_down.discard(key)
            return "break"

    def _on_key(self, event):
        if not self._is_pipes():
            return
        key = event.keysym.lower()
        modifiers = getattr(event, "state", 0)
        ctrl, shift = bool(modifiers & 0x0004), bool(modifiers & 0x0001)
        editor = isinstance(event.widget, (ttk.Entry, tk.Entry, tk.Text))
        action = None
        if ctrl and key in {"o", "l"}:
            action = self.browse if key == "o" else self.load
        elif editor or modifiers & 0x0008:
            return
        elif ctrl:
            if key == "f" and shift:
                action = self.clear_flags
            elif key == "z":
                action = self.back
            elif key == "r":
                action = self.reset
        else:
            action = {
                "space": self.toggle_pause, "right": self.step, "s": self.step,
                "return": self.run, "kp_enter": self.run, "escape": self.cancel_search,
                "c": self.check, "h": self.hint, "f": self.flag_under_pointer,
                "q": lambda: self.rotate_pipe_under_pointer(-1), "e": lambda: self.rotate_pipe_under_pointer(1),
                "a": self.cycle_algorithm,
                "plus": lambda: self.change_speed(0.25), "equal": lambda: self.change_speed(0.25),
                "kp_add": lambda: self.change_speed(0.25), "minus": lambda: self.change_speed(-0.25),
                "kp_subtract": lambda: self.change_speed(-0.25),
            }.get(key)
        if action is not None:
            if not hasattr(self, "_shortcut_keys_down"):
                self._shortcut_keys_down = set()
            self._shortcut_keys_down.add(key)
            action()
            return "break"

    def cycle_algorithm(self) -> None:
        if not self._search_busy():
            self.algorithm.set("gbfs" if self.algorithm.get() == "dfs" else "dfs")
            self._on_algorithm_change()

    def change_speed(self, amount: float) -> None:
        self.speed.set(min(4.0, max(0.25, self.speed.get() + amount)))

    def _enter_value(self, value: int) -> None:
        if self.problem is None or self.current_state is None or self.selected is None or not hasattr(self.problem, "size"):
            self._set_status("Select a white cell before entering a number.", kind="warning")
            return
        self._clear_domain_state()
        updated = set_futoshiki_value(self.problem, self.current_state, self.selected, value)
        self._remember(updated)
        self.conflicts = futoshiki_conflicts(self.problem, updated)
        self._set_status("Conflicts are highlighted in red." if self.conflicts else "Valid so far. Continue filling the empty cells.", kind="rejected" if self.conflicts else "info")
        self._draw()

    def check(self) -> None:
        if self.problem is None or self.current_state is None:
            return
        if self._is_pipes() and self._search_busy():
            self._set_status("Pause or step to inspect the search; cancel it before checking your board.", kind="warning")
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
            self._set_status("Correct! You have solved the puzzle.", kind="solved")
            messagebox.showinfo("Complete", "Congratulations! You have solved the puzzle correctly.")
        elif self.conflicts:
            self._set_status(f"Incorrect: {len(self.conflicts)} conflicting cells (highlighted in red).", kind="rejected")
        elif incomplete:
            self._set_status("Incomplete: empty cells remain, but there are no direct conflicts.", kind="warning")
        else:
            self._set_status("Incorrect: the pipe network is disconnected or contains a cycle.", kind="rejected")
        self._draw()

    def _get_solution(self) -> tuple[int, ...] | None:
        if self.solution is not None:
            return self.solution
        if self.solution is None and self.problem is not None:
            result = solve(self.problem, "gbfs", timeout=10, detailed_events=False)
            if result.status == "solved":
                self.solution = result.path[-1]
            return self.solution

    def hint(self) -> None:
        if self.problem is None or self.current_state is None:
            return
        if self._is_pipes() and self._search_busy():
            self._set_status("Cancel the search before applying a hint.", kind="warning")
            return
        solution = self._get_solution()
        if solution is None:
            self._set_status("No hint found within the time limit.", kind="warning")
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
            self._set_status(f"Hint: cell at row {index // self.problem.size + 1}, column {index % self.problem.size + 1}.", kind="trial")
        else:
            self._set_status(f"Hint: correct orientation for the cell at row {index // self.problem.cols + 1}, column {index % self.problem.cols + 1}.", kind="trial")

    def pause_search(self) -> None:
        if self.controller.state.running and not self.controller.state.paused:
            self.controller.pause()
            self._set_status("Search paused. Press 'Resume' or [Space] to continue.", kind="warning")

    def resume_search(self) -> None:
        if self.controller.state.running and self.controller.state.paused:
            self.controller.resume()
            self._set_status(f"Resuming {self.algorithm.get().upper()} search...", kind="info")
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
        self.flags = set()
        self.flag_history = []
        self.conflicts = set()
        self._clear_domain_state()
        self.solved = False
        if self._is_pipes():
            self.current_state = self.problem.initial_state
            self._pipe_branch_state = self.current_state
            self.selected = None
            self.pipes_search_view = True
            self._draw()
        self._set_status(f"Running {self.algorithm.get().upper()}...", kind="info")
        self.controller.start(self.problem, self.algorithm.get())

    def step(self) -> None:
        if self.problem is None:
            return
        if not self.controller.state.running:
            self.history = []
            self.flags = set()
            self.flag_history = []
            self.conflicts = set()
            self._clear_domain_state()
            self.solved = False
            if self._is_pipes():
                self.current_state = self.problem.initial_state
                self._pipe_branch_state = self.current_state
                self.selected = None
                self.pipes_search_view = True
                self._draw()
            self.controller.start(self.problem, self.algorithm.get(), paused=True)
        self.controller.step()

    def cancel_search(self) -> None:
        self.controller.cancel()
        if self._is_pipes() and getattr(self, "pipes_search_view", False):
            # Discard a transient trial, then make undecided pipes playable again.
            branch = getattr(self, "_pipe_branch_state", None) or self.problem.initial_state
            initial = initial_play_state(self.problem)
            self.current_state = tuple(mask or initial[i] for i, mask in enumerate(branch))
            self.history = [self.current_state]
            self.flag_history = [set()]
        self._clear_domain_state()
        self._set_status("Search cancelled.", kind="default", frontier_items=())
        self._draw()

    def back(self) -> None:
        if self._is_pipes() and self._search_busy():
            self._set_status("Cancel the search before undoing player actions.", kind="warning")
            return
        if len(self.history) > 1:
            if self._is_pipes():
                if len(getattr(self, "flag_history", [])) != len(self.history):
                    self.flag_history = [set() for _ in self.history]
                self.flag_history.pop()
                self.flags = set(self.flag_history[-1])
            self.history.pop()
            self.current_state = self.history[-1]
            self.conflicts = set()
            self.solved = False
            self._clear_domain_state()
            self._draw()
            self._set_status("Returned to the previous state.", kind="default")

    def reset(self) -> None:
        self.controller.cancel()
        if self.problem is not None:
            self.current_state = initial_play_state(self.problem)
            self.history = [self.current_state]
            self.flags = set()
            self.flag_history = [set()]
            self.flag_target = None
            self.selected = None
            self._clear_domain_state()
            self.conflicts = set()
            self.solved = False
            self._draw()
            self._set_status("Original puzzle restored.", kind="default", frontier_items=())

    def _handle_event(self, event) -> None:
        self.metrics.update_event(event)
        if self._is_pipes():
            self._handle_pipes_event(event)
            return
        if event.frontier_items is not None and hasattr(self, "queue_text"):
            if event.frontier_items:
                self.queue_text.set("  ".join(event.frontier_items))
            else:
                self.queue_text.set("[Empty]")

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
            self._append_history(event.state)
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
            self._set_status("The algorithm has found a solution.", kind="solved", frontier_items=event.frontier_items)
        elif event.type == EventType.FINISHED and event.message != "solved":
            finish_map = {
                "Frontier exhausted": "Frontier exhausted (no solution found)",
                "Search cancelled": "Search cancelled",
                "timeout": "Search timed out",
            }
            msg = finish_map.get(event.message, event.message)
            self._set_status(f"Search finished: {msg}.", kind="default", frontier_items=event.frontier_items)
        elif event.type == EventType.ERROR:
            messagebox.showerror("Search error", event.message)

    def _handle_pipes_event(self, event) -> None:
        """Display candidate previews separately from the expanded search path."""
        if event.type == EventType.NODE_GENERATED:
            return
        if event.type == EventType.STARTED:
            self._clear_domain_state()
            self.pipes_search_view = True
        if event.state is not None:
            self.current_state = event.state
        self.active_cell = event.cell
        self.active_value = event.value
        self.active_kind = None
        message = event.message
        if event.type == EventType.CELL_DOMAIN:
            self.active_kind = "domain"
        elif event.type == EventType.VALUE_TRIED:
            self.active_kind = "trial"
        elif event.type == EventType.VALUE_ACCEPTED:
            self.active_kind = "accepted"
        elif event.type == EventType.VALUE_REJECTED:
            self.active_kind = "rejected"
        elif event.type in {EventType.STARTED, EventType.NODE_EXPANDED}:
            self._pipe_branch_state = self.current_state
            self._append_history(self.current_state)
            switched = (event.type == EventType.NODE_EXPANDED
                        and self._previous_pipe_node_id is not None
                        and event.parent_id != self._previous_pipe_node_id)
            if event.type == EventType.NODE_EXPANDED:
                self._previous_pipe_node_id = event.node_id
            if event.action is not None:
                self.active_cell, self.active_value = event.action
                self.active_kind = "accepted"
                row, col = divmod(self.active_cell, self.problem.cols)
                action = f"{orientation_label(self.active_value)} at row {row + 1}, column {col + 1}"
                message = f"{'Switching branches; expanding' if switched else 'Expanding'} {action}"
                if self.algorithm.get() == "gbfs":
                    message += f" (h={event.h:g})"
            else:
                message = "Starting from the puzzle's locked pipes; other orientations are unassigned."
        elif event.type in {EventType.NODE_PRUNED, EventType.BACKTRACK}:
            if event.action is not None:
                self.active_cell, self.active_value = event.action
            self.active_kind = "rejected"
            if event.type == EventType.BACKTRACK:
                row, col = divmod(self.active_cell, self.problem.cols)
                message = f"Backtracking: branch exhausted; undoing the pipe at row {row + 1}, column {col + 1}"
            else:
                message = f"Dead end: {event.message.lower()}"
                if self.active_cell is None and 0 in self.current_state:
                    self.active_cell = self.current_state.index(0)
        elif event.type == EventType.GOAL_FOUND:
            self.solved = True
            self._append_history(self.current_state)
            message = "Solution found: all pipes form one connected tree."
        elif event.type == EventType.FINISHED:
            if event.message != "solved":
                self.current_state = self._pipe_branch_state or self.problem.initial_state
            message = {"solved": "Solved: all pipes form one connected tree.",
                       "unsolved": "Search finished: no solution found.",
                       "timeout": "Search timed out.", "cancelled": "Search cancelled.",
                       "error": "Search stopped after an error."}.get(event.message, event.message)
        elif event.type == EventType.ERROR:
            messagebox.showerror("Search error", event.message)
        if message:
            self._set_status(message)
        self._draw()

    def _poll(self) -> None:
        self.controller.poll(self._handle_event, limit=1)
        self._update_flag_controls()
        delay = max(20, int(150 / max(0.1, self.speed.get())))
        self.root.after(delay, self._poll)

    def close(self) -> None:
        self.controller.cancel()
        self.root.destroy()
