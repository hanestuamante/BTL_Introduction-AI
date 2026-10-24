import hashlib
import subprocess

from logic_search.benchmark import metrics


def test_metadata_tracks_source_changes_and_uses_source_repository(tmp_path, monkeypatch):
    package = tmp_path / "src" / "logic_search"
    package.mkdir(parents=True)
    source = package / "sample.py"
    source.write_text("VALUE = 1\n")

    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()

    git("init", "--quiet")
    git("add", "src")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-m", "fixture")
    monkeypatch.setattr(metrics, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(metrics, "PACKAGE_ROOT", package)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    clean = metrics.environment_metadata()
    assert clean["git_commit"] == git("rev-parse", "HEAD")
    assert clean["git_worktree_dirty"] == "false"
    expected = hashlib.sha256(b"sample.py\0VALUE = 1\n\0").hexdigest()
    assert clean["source_sha256"] == expected

    source.write_text("VALUE = 2\n")
    dirty = metrics.environment_metadata()
    assert dirty["git_worktree_dirty"] == "true"
    assert dirty["git_commit"] == clean["git_commit"]
    assert dirty["source_sha256"] != clean["source_sha256"]
