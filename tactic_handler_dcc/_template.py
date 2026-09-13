"""Copy this file to ``tactic_handler_dcc/<dcc>.py`` without editing it."""

from __future__ import annotations

import atexit

from .runtime import DccEntrypoint, DccRuntime


class Runtime(DccRuntime):
    pass


_module_id = __name__.rsplit(".", 1)[-1]
_connector_module = f"{__package__}.connectors.{_module_id}"


_entrypoint = globals().get("_entrypoint")
if not isinstance(_entrypoint, DccEntrypoint):
    _entrypoint = DccEntrypoint(
        _connector_module,
        "Connector",
        Runtime,
    )
else:
    _entrypoint.configure(Runtime)


def startup(handler_path, **kwargs):
    _entrypoint.configure(Runtime)
    return _entrypoint.startup(handler_path, **kwargs)


def stop():
    _entrypoint.stop()


def runtime():
    return _entrypoint.current


def status():
    return _entrypoint.status()


def show_handler():
    return _entrypoint.show_handler()


def execute_custom_script(
    script_path, project=None, kwargs=None, refresh_scripts=False
):
    return _entrypoint.execute_custom_script(
        script_path,
        project=project,
        kwargs=kwargs,
        refresh_scripts=refresh_scripts,
    )


if not globals().get("_atexit_registered", False):
    atexit.register(stop)
    _atexit_registered = True
