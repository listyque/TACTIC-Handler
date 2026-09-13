from __future__ import annotations

import atexit
from typing import Optional

from .connectors.maya import MayaConnector
from .runtime import DccEntrypoint, DccRuntime, ScriptJob


class MayaRuntime(DccRuntime):
    """Maya defaults for the shared thin-client runtime."""

    def __init__(
        self,
        handler_path,
        *,
        application_type="maya",
        application_title="Maya",
        connector=None,
        notifier=None,
        **kwargs,
    ) -> None:
        super().__init__(
            handler_path,
            application_type=application_type,
            application_title=application_title,
            connector=connector or MayaConnector.instance(handler_path),
            notifier=notifier or self._maya_notification,
            **kwargs,
        )

    @staticmethod
    def _maya_notification(message, level="info") -> None:
        try:
            import maya.cmds as cmds
            import maya.utils as maya_utils

            colors = {
                "success": 0x315B3A,
                "warning": 0x665A2D,
                "error": 0x6B3030,
                "info": 0x354A5E,
            }
            maya_utils.executeDeferred(
                lambda: cmds.inViewMessage(
                    assistMessage=str(message),
                    position="topCenter",
                    fade=True,
                    fadeStayTime=3000,
                    backColor=colors.get(level, colors["info"]),
                )
            )
        except Exception:
            print(f"TACTIC Handler [{level}]: {message}")


_entrypoint = globals().get("_entrypoint")
if not isinstance(_entrypoint, DccEntrypoint):
    _entrypoint = DccEntrypoint(
        "tactic_handler_dcc.connectors.maya",
        "MayaConnector",
        MayaRuntime,
    )
else:
    _entrypoint.configure(MayaRuntime)


def startup(handler_path, **kwargs):
    """Start or reuse the connector and return immediately."""
    global MayaConnector
    _entrypoint.configure(MayaRuntime)
    runtime_object = _entrypoint.startup(handler_path, **kwargs)
    MayaConnector = _entrypoint.connector_type
    return runtime_object


def stop() -> None:
    _entrypoint.stop()


def runtime():
    return _entrypoint.current


def status() -> dict:
    return _entrypoint.status()


def show_handler():
    return _entrypoint.show_handler()


def _maya_connector() -> MayaConnector:
    return _entrypoint.connector()


def get_maya_window() -> Optional[object]:
    return _maya_connector().get_maya_window()


def get_current_scene_format() -> str:
    return _maya_connector().get_current_scene_format()


def get_skey_from_scene() -> Optional[str]:
    return _maya_connector().get_skey_from_scene()


def set_info_to_scene(search_key: str, context: str) -> None:
    return _maya_connector().set_info_to_scene(search_key, context)


def execute_custom_script(
    script_path,
    project=None,
    kwargs=None,
    refresh_scripts=False,
):
    return _entrypoint.execute_custom_script(
        script_path,
        project=project,
        kwargs=kwargs,
        refresh_scripts=refresh_scripts,
    )


if not globals().get("_atexit_registered", False):
    atexit.register(_entrypoint.stop)
    _atexit_registered = True


__all__ = [
    "MayaRuntime",
    "ScriptJob",
    "execute_custom_script",
    "get_current_scene_format",
    "get_maya_window",
    "get_skey_from_scene",
    "runtime",
    "set_info_to_scene",
    "show_handler",
    "startup",
    "status",
    "stop",
]
