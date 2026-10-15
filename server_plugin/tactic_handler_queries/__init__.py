"""TACTIC-side entry point for TACTIC-Handler procedures."""

from contextvars import ContextVar
from hashlib import sha256
from inspect import isfunction
import os
from threading import Lock

_request_server = ContextVar("tactic_handler_query_server")
_load_lock = Lock()
_loaded = None


class _RequestServer:
    def __getattr__(self, name):
        return getattr(_request_server.get(), name)


def _load_api(expected_sha256):
    path = os.path.join(os.path.dirname(__file__), "api.py")
    try:
        with open(path, "rb") as api_file:
            source = api_file.read()
    except OSError as error:
        raise RuntimeError("TACTIC-Handler query plugin is out of date") from error
    if sha256(source).hexdigest() != expected_sha256:
        raise RuntimeError("TACTIC-Handler query plugin is out of date")

    module_name = __name__ + ".api"
    namespace = {
        "__name__": module_name,
        "__package__": __name__,
        "__file__": path,
        "server": _RequestServer(),
    }
    exec(compile(source, path, "exec"), namespace)
    procedures = {
        name: value for name, value in namespace.items()
        if isfunction(value) and value.__module__ == module_name
        and not name.startswith("_")
    }
    return expected_sha256, procedures


def invoke(name, arguments, server, source_sha256):
    """Run only a bundled procedure under the caller's TACTIC credentials."""
    global _loaded
    loaded = _loaded
    if loaded is None or loaded[0] != source_sha256:
        with _load_lock:
            loaded = _loaded
            if loaded is None or loaded[0] != source_sha256:
                # Swap only after verifying and compiling the new source;
                # in-flight requests keep their original function globals.
                loaded = _load_api(source_sha256)
                _loaded = loaded

    procedures = loaded[1]
    if not isinstance(name, str) or name not in procedures:
        raise ValueError("Unknown TACTIC-Handler procedure: {!r}".format(name))
    if not isinstance(arguments, dict):
        raise TypeError("Procedure arguments must be a dictionary")
    token = _request_server.set(server)
    try:
        return procedures[name](**arguments)
    finally:
        _request_server.reset(token)
