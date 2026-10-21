from dataclasses import replace
from types import SimpleNamespace

import pytest

from logic_search.puzzles.futoshiki.model import FutoshikiProblem
from logic_search.puzzles.pipes.model import E, N, S, W, PipesProblem
from logic_search.ui.controller import SearchController
from logic_search.ui.futoshiki_canvas import FutoshikiCanvas
from logic_search.ui.game_logic import initial_play_state
from logic_search.ui.main_window import BUTTON_SHORTCUTS, MainWindow, action_label
from logic_search.ui.pipes_canvas import PipesCanvas
from logic_search.ui.player_flags import FLAG_COLOR


class Variable:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


@pytest.fixture
def window():
    instance = object.__new__(MainWindow)
    instance.problem = PipesProblem('flags', 2, 2, ('END', 'CORNER', 'END', 'CORNER'), (1, 2, 1, 3))
    instance.current_state = initial_play_state(instance.problem)
    instance.history = [instance.current_state]
    instance.flags = set()
    instance.flag_history = [set()]
    instance.selected = 0
    instance.flag_target = 0
    instance.solved = False
    instance.conflicts = set()
    instance.cell_domains, instance.cell_rejected = {}, {}
    instance._clear_domain_state()
    instance.controller = SearchController()
    instance.algorithm = Variable('dfs')
    instance.speed = Variable(1.0)
    instance.messages = []
    instance._set_status = lambda message, **kwargs: instance.messages.append(message)
    instance._draw = lambda: None
    instance.canvas = object.__new__(PipesCanvas)
    instance.canvas.focus_set = lambda: None
    instance.canvas.cell_at = lambda x, y: 0
    return instance


def test_flags_are_player_notes_even_for_an_incorrect_orientation(window):
    window.current_state = (S, S | W, E, N | W)
    window.history = [window.current_state]
    before = window.current_state
    assert not window.problem.is_goal(before)
    window.toggle_flag()
    assert window.flags == {0} and window.current_state == before
    assert 'not a verified answer' in window.messages[-1]
    window.toggle_flag()
    assert not window.flags and window.current_state == before


def test_undo_restores_flag_edits_and_clear_all(window):
    window.toggle_flag()
    window.flag_target = 2
    window.toggle_flag()
    window.clear_flags()
    assert not window.flags
    window.back()
    assert window.flags == {0, 2}
    window.back()
    assert window.flags == {0}
    window.back()
    assert not window.flags


def test_rotation_clears_only_the_changed_flag_and_undo_restores_it(window):
    window.toggle_flag()
    window.flag_target = 2
    window.toggle_flag()
    window.selected = 0
    before = window.current_state
    window.rotate_selected_pipe(1)
    assert window.flags == {2} and window.current_state != before
    window.back()
    assert window.current_state == before and window.flags == {0, 2}


def test_hint_clears_changed_flag_and_keeps_other_notes(window):
    solution = window.current_state
    window._remember((S, S | W, E, N | W))
    window.toggle_flag()
    window.flag_target = 2
    window.toggle_flag()
    window.solution = solution
    window.hint()
    assert window.current_state == solution and window.flags == {2}


def test_futoshiki_keeps_original_input_and_has_no_new_flags_or_shortcuts(window):
    window.problem = FutoshikiProblem('f2', 2, (0, 0, 0, 0))
    window.current_state = window.problem.initial_state
    window.history, window.flag_history = [window.current_state], [set()]
    window.canvas = object.__new__(FutoshikiCanvas)
    window.canvas.focus_set = lambda: None
    window.canvas.cell_at = lambda x, y: 0
    window._on_click(SimpleNamespace(x=0, y=0, state=1))
    assert window.selected == 0 and not window.flags
    for key, modifiers in [('f', 0), ('F', 5), ('c', 0), ('h', 0), ('z', 4), ('e', 0)]:
        event = SimpleNamespace(keysym=key, state=modifiers, char=key, widget=object())
        assert window._on_key(event) is None
        window._on_futoshiki_key(event)
    window.toggle_flag()
    assert not window.flags and len(window.history) == 1
    window._on_futoshiki_key(SimpleNamespace(keysym='1', char='1', widget=object()))
    assert window.current_state[0] == 1 and len(window.history) == 2
    window._on_futoshiki_key(SimpleNamespace(keysym='Delete', char='', widget=object()))
    assert window.current_state[0] == 0
    window.back()
    assert window.current_state[0] == 1 and not window.flags


def test_shift_click_flags_and_control_click_selects_without_rotating(window):
    before = window.current_state
    window._on_click(SimpleNamespace(x=0, y=0, state=1))
    assert window.flags == {0} and window.current_state == before
    window._on_click(SimpleNamespace(x=0, y=0, state=4))
    assert window.selected == 0 and window.flags == {0} and window.current_state == before
    window._on_click(SimpleNamespace(x=0, y=0, state=1))
    assert not window.flags and window.current_state == before


def test_f_flags_the_pipe_under_the_pointer_without_changing_the_selected_pipe(window):
    before = window.current_state
    window.canvas.winfo_pointerxy = lambda: (150, 250)
    window.canvas.winfo_rootx = lambda: 100
    window.canvas.winfo_rooty = lambda: 200
    window.canvas.cell_at = lambda x, y: 2 if (x, y) == (50, 50) else None
    window.active_cell = 1
    event = SimpleNamespace(keysym='f', state=0, widget=object(), char='f')
    assert window._on_key(event) == 'break'
    assert window.flags == {2} and window.selected == 0 and window.active_cell == 1
    assert window.current_state == before
    window.flag_under_pointer()
    assert not window.flags and window.selected == 0


def test_f_can_flag_a_hovered_pipe_before_any_cell_is_selected(window):
    window.selected = None
    window.canvas.winfo_pointerxy = lambda: (50, 50)
    window.canvas.winfo_rootx = window.canvas.winfo_rooty = lambda: 0
    window.canvas.cell_at = lambda x, y: 1
    window.flag_under_pointer()
    assert window.flags == {1} and window.selected is None


def test_f_outside_the_board_does_not_fall_back_to_a_previous_target(window):
    before = len(window.history)
    window.canvas.winfo_pointerxy = lambda: (-10, -10)
    window.canvas.winfo_rootx = window.canvas.winfo_rooty = lambda: 0
    window.canvas.cell_at = lambda x, y: None
    window.flag_under_pointer()
    assert not window.flags and len(window.history) == before


def test_flag_button_uses_the_last_hovered_pipe_when_the_pointer_leaves_the_board(window):
    window.canvas.cell_at = lambda x, y: 2 if x >= 0 else None
    window._on_pipe_hover(SimpleNamespace(x=20, y=20))
    window._on_pipe_hover(SimpleNamespace(x=-10, y=20))
    window.toggle_flag()
    assert window.flags == {2} and window.selected == 0


def test_shift_click_flags_without_changing_the_selected_pipe(window):
    window.canvas.cell_at = lambda x, y: 2
    window._on_click(SimpleNamespace(x=20, y=20, state=1))
    assert window.flags == {2} and window.selected == 0


def test_flags_do_not_override_puzzle_locks(window):
    window.problem = replace(window.problem, locked_mask=(E, 0, 0, 0))
    window.toggle_flag()
    before = window.current_state
    window.rotate_selected_pipe(1)
    assert window.current_state == before and window.flags == {0}


def test_running_search_blocks_flag_edits_and_manual_rotations(window):
    before = window.current_state
    window.controller.state.running = True
    window.toggle_flag()
    window.rotate_selected_pipe(1)
    window.hint()
    assert not window.flags and window.current_state == before


def test_new_search_and_reset_clear_notes(window):
    window.toggle_flag()
    starts = []
    window.controller.start = lambda *args, **kwargs: starts.append((args, kwargs))
    window.run()
    assert starts and not window.flags and not window.flag_history
    window.history, window.flag_history = [window.current_state], [set()]
    window.selected = 0
    window.toggle_flag()
    window.reset()
    assert not window.flags and window.flag_history == [set()]


def test_pipes_canvas_draws_vector_flag_without_a_unicode_glyph(window):
    canvas = object.__new__(PipesCanvas)
    calls = []
    canvas.winfo_width = canvas.winfo_height = lambda: 500
    for name in ('delete', 'create_text', 'create_rectangle', 'create_polygon', 'create_line', 'create_oval'):
        setattr(canvas, name, lambda *args, _name=name, **kwargs: calls.append((_name, kwargs)))
    problem = window.problem
    state = initial_play_state(problem)
    canvas.draw(problem, state, flags={0})
    assert sum(name == 'create_polygon' and options.get('fill') == FLAG_COLOR for name, options in calls) == 1
    assert all(str(options.get('text', '')).isascii() for _, options in calls)


@pytest.mark.parametrize('key,modifiers,expected', [
    ('c', 0, 'check'), ('h', 0, 'hint'), ('f', 0, 'flag_under_pointer'),
    ('F', 5, 'clear_flags'), ('z', 4, 'back'), ('r', 4, 'reset'),
    ('o', 4, 'browse'), ('l', 4, 'load'), ('Return', 0, 'run'),
    ('space', 0, 'toggle_pause'), ('Right', 0, 'step'), ('s', 0, 'step'),
    ('Escape', 0, 'cancel_search'), ('q', 0, 'rotate_selected_pipe'),
    ('e', 0, 'rotate_selected_pipe'), ('a', 0, 'cycle_algorithm'),
    ('plus', 1, 'change_speed'), ('minus', 0, 'change_speed'),
])
def test_shortcuts_dispatch_exactly_once(window, key, modifiers, expected):
    calls = []
    actions = set(BUTTON_SHORTCUTS) | {'toggle_pause', 'rotate_selected_pipe', 'cycle_algorithm', 'change_speed', 'flag_under_pointer'}
    for name in actions:
        setattr(window, name, lambda *args, _name=name: calls.append((_name, args)))
    event = SimpleNamespace(keysym=key, state=modifiers, widget=object(), char='')
    assert window._on_key(event) == 'break'
    assert len(calls) == 1 and calls[0][0] == expected
    assert window._on_key_release(event) == 'break'


def test_shortcuts_preserve_typing_and_native_undo_in_entries(window):
    from tkinter import ttk
    entry = object.__new__(ttk.Entry)
    for key, modifiers in [('c', 0), ('f', 0), ('space', 0), ('Return', 0), ('z', 4), ('r', 4), ('F', 5)]:
        assert window._on_key(SimpleNamespace(keysym=key, state=modifiers, widget=entry, char=key)) is None
    assert not window.flags


def test_speed_shortcut_respects_the_slider_limits(window):
    window.change_speed(100)
    assert window.speed.get() == 4.0
    window.change_speed(-100)
    assert window.speed.get() == 0.25


def test_labels_show_shortcuts_and_remain_ascii():
    for action, shortcut in BUTTON_SHORTCUTS.items():
        label = action_label('Button', action)
        assert label.endswith(f'({shortcut})') and label.isascii()
