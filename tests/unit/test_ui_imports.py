import os
import subprocess
import sys
from pathlib import Path


def test_game_logic_and_controller_import_without_tkinter():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-c", """
import sys
sys.modules['tkinter'] = None
import logic_search.ui
from logic_search.ui.game_logic import initial_play_state
from logic_search.ui.controller import SearchController
assert 'MainWindow' not in vars(logic_search.ui)
assert not SearchController().state.running
"""],
        env={**os.environ, "PYTHONPATH": str(root / "src")},
        cwd=root, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
