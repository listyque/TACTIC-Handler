"""Load both application entry points from outside the repository directory."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
WARNING_MARKERS = (
    "QML startup failed",
    "Binding loop detected",
    "Required property",
    "ReferenceError",
    "TypeError",
    "QUnifiedTimer::stopAnimationDriver",
)


def _run_entrypoint(command: list[str], working_directory: Path) -> None:
    environment = os.environ.copy()
    environment.update({
        "QT_QPA_PLATFORM": "offscreen",
        "QT_QUICK_BACKEND": "software",
        "TACTIC_QML_SMOKE_OFFLINE": "1",
        "TACTIC_QML_SMOKE_EXIT_MS": "500",
    })
    with tempfile.TemporaryDirectory(prefix="tactic-entry-settings-") as settings:
        environment["TACTIC_QML_TEST_SETTINGS_DIR"] = settings
        environment["XDG_CACHE_HOME"] = str(Path(settings) / "cache")
        environment["XDG_CONFIG_HOME"] = str(Path(settings) / "config")
        if os.name == "nt":
            environment["LOCALAPPDATA"] = settings
            environment["APPDATA"] = settings
            environment["QT_QPA_FONTDIR"] = str(
                Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
            )
        completed = subprocess.run(
            command,
            cwd=working_directory,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    diagnostic = "\n".join((completed.stdout, completed.stderr))
    if completed.returncode:
        raise RuntimeError(
            f"entry point returned {completed.returncode}:\n{diagnostic}"
        )
    found = [marker for marker in WARNING_MARKERS if marker in diagnostic]
    if found:
        raise RuntimeError(
            f"entry point emitted QML errors {found}:\n{diagnostic}"
        )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tactic-foreign-cwd-") as directory:
        working_directory = Path(directory)
        _run_entrypoint(
            [sys.executable, str(ROOT / "launch.py")],
            working_directory,
        )
        _run_entrypoint(
            [sys.executable, str(ROOT / "launch.pyw")],
            working_directory,
        )
    print("Foreign working-directory entry points: OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
