"""Select the standalone UI without importing both Qt stacks."""

from __future__ import annotations

import os
import sys


UI_ENVIRONMENT_VARIABLE = "TACTIC_HANDLER_UI"
SUPPORTED_UIS = {"legacy", "qml"}


def _selected_ui(arguments: list[str]) -> tuple[str, list[str]]:
    selected = os.environ.get(UI_ENVIRONMENT_VARIABLE, "qml").strip().lower()
    forwarded = [arguments[0]]
    index = 1
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--ui":
            if index + 1 >= len(arguments):
                raise ValueError("--ui requires either 'legacy' or 'qml'")
            selected = arguments[index + 1].strip().lower()
            index += 2
            continue
        if argument.startswith("--ui="):
            selected = argument.partition("=")[2].strip().lower()
            index += 1
            continue
        forwarded.append(argument)
        index += 1
    if selected not in SUPPORTED_UIS:
        raise ValueError(
            "Unsupported UI {!r}; expected 'legacy' or 'qml'".format(selected)
        )
    return selected, forwarded


def main(arguments: list[str] | None = None) -> int:
    try:
        selected, forwarded = _selected_ui(list(arguments or sys.argv))
    except ValueError as error:
        sys.stderr.write("TACTIC-Handler launcher: {}\n".format(error))
        return 2

    sys.argv[:] = forwarded
    try:
        if selected == "qml":
            from main_qml import main as start
        else:
            from main_standalone import startup as start
        result = start()
        return int(result or 0)
    except SystemExit as error:
        return int(error.code or 0)
    except Exception as error:
        sys.stderr.write(
            "TACTIC-Handler {} startup failed in {}: {}: {}\n".format(
                selected,
                os.path.abspath(__file__),
                type(error).__name__,
                error,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
