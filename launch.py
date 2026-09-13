"""Launch TACTIC-Handler."""

from __future__ import annotations

import sys


def main(arguments: list[str] | None = None) -> int:
    sys.argv[:] = list(arguments or sys.argv)
    try:
        from thlib.ui.application import main as start
        result = start()
        return int(result or 0)
    except SystemExit as error:
        return int(error.code or 0)
    except Exception as error:
        sys.stderr.write(
            "TACTIC-Handler startup failed: {}: {}\n".format(
                type(error).__name__,
                error,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
