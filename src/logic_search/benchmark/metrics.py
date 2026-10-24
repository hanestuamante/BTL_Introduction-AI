from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parents[1]


def environment_metadata() -> dict[str, str]:
    commit = dirty = "unknown"
    try:
        def git(*args: str) -> str:
            return subprocess.run(
                ["git", "-C", str(PROJECT_ROOT), *args],
                capture_output=True, text=True, timeout=2, check=True,
            ).stdout.strip()

        if Path(git("rev-parse", "--show-toplevel")).resolve() == PROJECT_ROOT:
            commit = git("rev-parse", "HEAD")
            dirty = "true" if git("status", "--porcelain", "--untracked-files=normal") else "false"
    except (OSError, subprocess.SubprocessError):
        pass
    source = hashlib.sha256()
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        source.update(path.relative_to(PACKAGE_ROOT).as_posix().encode("utf-8") + b"\0")
        source.update(path.read_bytes() + b"\0")
    return {
        "python_version": platform.python_version(),
        "os": platform.platform(),
        "cpu_model": platform.processor() or platform.machine(),
        "git_commit": commit,
        "git_worktree_dirty": dirty,
        "source_sha256": source.hexdigest(),
        "python_executable": sys.executable,
    }

