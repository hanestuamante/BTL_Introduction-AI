import json

import pytest

from logic_search.cli import main


@pytest.mark.parametrize("bad_value", [[], {}, None, 7, True, "UNKNOWN"])
@pytest.mark.parametrize("puzzle", ["pipes", "futoshiki"])
def test_solve_reports_wrong_field_types_as_input_errors(tmp_path, capsys, puzzle, bad_value):
    if puzzle == "pipes":
        data = {
            "schema_version": 1, "puzzle": puzzle, "id": "invalid-tile",
            "rows": 2, "cols": 2,
            "tiles": [[bad_value, "CORNER"], ["END", "CORNER"]],
            "initial_rotations": [[0, 0], [0, 0]],
        }
        field = "tiles[0][0]"
    else:
        data = {
            "schema_version": 1, "puzzle": puzzle, "id": "invalid-relation",
            "size": 2, "givens": [[0, 0], [0, 0]],
            "inequalities": [{"left": [0, 0], "right": [0, 1], "op": bad_value}],
        }
        field = "inequalities[0].op"
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    output = tmp_path / "solution.json"

    assert main(["solve", "--puzzle", puzzle, "--input", str(path), "--output", str(output)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Input error:" in captured.err and field in captured.err
    assert "Traceback" not in captured.err
    assert not output.exists()
