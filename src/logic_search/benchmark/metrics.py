from __future__ import annotations

import platform
import subprocess
import sys


def environment_metadata() -> dict[str, str]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=2, check=False
        ).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        commit = "unknown"
    return {
        "python_version": platform.python_version(),
        "os": platform.platform(),
        "cpu_model": platform.processor() or platform.machine(),
        "git_commit": commit,
        "python_executable": sys.executable,
    }

