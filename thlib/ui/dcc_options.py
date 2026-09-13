from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Property, Signal, Slot

from tactic_handler_dcc.connectors import (
    dcc_item_action,
    dcc_manifest_for,
    normalize_dcc_values,
)
from thlib.environment import env_read_config, env_write_config
from thlib.ui.configuration import read_dcc_preferences


class DccOptionsController(QObject):
    stateChanged = Signal()

    def __init__(
        self,
        application,
        invoke_action: Callable[[str, str, dict], bool],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._application = application
        self._invoke_action = invoke_action
        self._dcc_bridge = None
        self._application_type = ""
        self._action_id = ""
        self._node_id = ""
        self._target_title = ""
        self._schema = {}
        self._values = {}
        self._error = ""

    def attach_dcc_bridge(self, bridge) -> None:
        if self._dcc_bridge is not None:
            try:
                self._dcc_bridge.stateChanged.disconnect(self.stateChanged)
            except (RuntimeError, TypeError):
                pass
        self._dcc_bridge = bridge
        if bridge is not None:
            bridge.stateChanged.connect(self.stateChanged)
        self.stateChanged.emit()

    @Property(str, notify=stateChanged)
    def title(self) -> str:
        return str(self._schema.get("title") or "DCC action")

    @Property(str, notify=stateChanged)
    def applicationTitle(self) -> str:
        manifest = dcc_manifest_for(self._application_type)
        return str(manifest.get("title") or self._application_type.title())

    @Property(str, notify=stateChanged)
    def targetTitle(self) -> str:
        return self._target_title

    @Property("QVariantMap", notify=stateChanged)
    def schema(self) -> dict:
        return dict(self._schema)

    @Property("QVariantMap", notify=stateChanged)
    def values(self) -> dict:
        return dict(self._values)

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(bool, notify=stateChanged)
    def available(self) -> bool:
        bridge = self._dcc_bridge
        return bool(
            self._node_id
            and bridge
            and bridge.has_dcc_capability(self._schema.get("capability", ""))
        )

    def _settings(self) -> dict:
        return dict(env_read_config(
            filename="ui_dcc_options",
            unique_id="ui_main",
            long_abs_path=True,
        ) or {})

    def _save(self) -> None:
        settings = self._settings()
        settings[f"{self._application_type}/{self._action_id}"] = dict(
            self._values
        )
        env_write_config(
            settings,
            filename="ui_dcc_options",
            unique_id="ui_main",
            long_abs_path=True,
        )

    def prepare_target(
        self, action_id: str, node_id: str, title: str
    ) -> bool:
        bridge = self._dcc_bridge
        application_type = str(
            getattr(bridge, "selectedApplicationType", "") or ""
        ).lower()
        schema = dcc_item_action(application_type, action_id)
        if not schema or not schema.get("options"):
            self._error = "This DCC action has no configurable options"
            self.stateChanged.emit()
            return False
        self._application_type = application_type
        self._action_id = str(schema["id"])
        self._node_id = str(node_id or "")
        self._target_title = str(title or "")
        self._schema = schema
        saved = dict(self._settings().get(
            f"{application_type}/{self._action_id}"
        ) or {})
        preferences = read_dcc_preferences(application_type)
        self._values = normalize_dcc_values(
            schema["options"], {**preferences, **saved}
        )
        self._error = ""
        self.stateChanged.emit()
        return True

    @Slot(str, "QVariant")
    def set_value(self, key: str, value) -> None:
        if not self._schema:
            return
        updated = {**self._values, str(key or ""): value}
        normalized = normalize_dcc_values(
            self._schema.get("options") or (), updated
        )
        if normalized == self._values:
            return
        self._values = normalized
        self.stateChanged.emit()

    @Slot()
    def confirm(self) -> None:
        if not self.available:
            self._error = "The selected DCC client is unavailable"
            self.stateChanged.emit()
            return
        self._save()
        if self._invoke_action(
            self._action_id, self._node_id, dict(self._values)
        ):
            self._application.window_model.close_window("dcc_options")
            return
        self._error = "The DCC action could not be started"
        self.stateChanged.emit()

