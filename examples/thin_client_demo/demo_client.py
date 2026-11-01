"""Source-checkout entry point for the bundled simulated Maya client."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from handler_server.demo_client import DemoClientController, main


if __name__ == "__main__":
    raise SystemExit(main())
