"""Create a temporary environment and smoke-test the standalone launchers."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"


def _run(command: list[str], *, timeout: int) -> None:
    print("[clean-environment] " + " ".join(command), flush=True)
    subprocess.run(
        command,
        cwd=ROOT,
        timeout=timeout,
        check=True,
    )


def _environment_python(folder: Path) -> Path:
    if sys.platform == "win32":
        return folder / "Scripts" / "python.exe"
    return folder / "bin" / "python"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-python",
        default=sys.executable,
        help="Python executable used to create the temporary environment",
    )
    parser.add_argument(
        "--wheelhouse",
        type=Path,
        help="optional offline folder containing the pinned dependency wheels",
    )
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument(
        "--keep",
        type=Path,
        help="keep the environment at this path instead of using a temporary folder",
    )
    arguments = parser.parse_args(argv)

    if not REQUIREMENTS.is_file():
        parser.error(f"missing dependency file: {REQUIREMENTS}")
    if arguments.wheelhouse and not arguments.wheelhouse.is_dir():
        parser.error(f"wheelhouse is not a directory: {arguments.wheelhouse}")

    temporary = None
    if arguments.keep:
        environment = arguments.keep.resolve()
        if environment.exists():
            parser.error(f"target already exists: {environment}")
        environment.parent.mkdir(parents=True, exist_ok=True)
    else:
        temporary = tempfile.TemporaryDirectory(prefix="tactic-handler-release-")
        environment = Path(temporary.name) / "venv"

    try:
        _run(
            [arguments.base_python, "-m", "venv", str(environment)],
            timeout=arguments.timeout,
        )
        python = _environment_python(environment)
        install = [
            str(python), "-m", "pip", "install",
            "--disable-pip-version-check",
        ]
        if arguments.wheelhouse:
            install.extend([
                "--no-index", "--find-links", str(arguments.wheelhouse.resolve()),
            ])
        install.extend(["-r", str(REQUIREMENTS)])
        _run(install, timeout=arguments.timeout)
        _run(
            [str(python), "tests/run_entrypoint_smoke.py"],
            timeout=arguments.timeout,
        )
        _run(
            [
                str(python), "-c",
                "import PySide6, thlib.tactic_classes; "
                "print('PySide6', PySide6.__version__)",
            ],
            timeout=arguments.timeout,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"[clean-environment] failed: {error}", file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.cleanup()

    print("[clean-environment] passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
