from __future__ import annotations

import argparse
import json
import logging
import os
import secrets
import signal
import threading

from .discovery import publish_session, remove_session
from .server import HandlerServer


def main(argv=None):
    parser = argparse.ArgumentParser(description="TACTIC Handler local command server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args(argv)
    token = os.environ.get("TACTIC_HANDLER_TOKEN", "") or secrets.token_urlsafe(32)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    server = HandlerServer(args.host, args.port, token)
    port = server.start()
    discovery_path = publish_session(server.host, port, server.token)
    print("HANDLER_SERVER_READY " + json.dumps({
        "host": server.host, "port": port, "protocol_version": 1,
    }), flush=True)
    stopped = threading.Event()

    def stop(_signum=None, _frame=None):
        stopped.set()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        while not stopped.wait(0.25):
            if server.shutdown_requested.is_set():
                break
    finally:
        remove_session(discovery_path)
        server.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
