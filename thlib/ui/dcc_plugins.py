"""Installation-scoped DCC plugin selection; applied on the next TH start."""

from PySide6.QtCore import QObject, Property, Signal, Slot

from tactic_handler_dcc.connectors import configure_plugins, plugin_catalog
from thlib.environment import env_read_config, env_write_config


def read_disabled_plugins() -> list[str]:
    values = env_read_config(filename="ui_dcc_plugins", unique_id="ui_main",
                             long_abs_path=True, scope="installation") or {}
    disabled = values.get("disabled", [])
    if not isinstance(disabled, list) or any(not isinstance(value, str) for value in disabled):
        raise ValueError("Invalid DCC plugin configuration")
    return disabled


def initialize_plugins() -> None:
    configure_plugins(read_disabled_plugins())


class DccPluginsController(QObject):
    stateChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._disabled = set(read_disabled_plugins())
        self._restart = False
        self._error = ""

    @Property("QVariantList", notify=stateChanged)
    def rows(self):
        return [{**row, "active": row["enabled"], "enabled": row["id"] not in self._disabled}
                for row in plugin_catalog()]

    @Property(bool, notify=stateChanged)
    def restartRequired(self):
        return self._restart

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Slot(str, bool)
    def set_enabled(self, identity, enabled):
        if identity not in {row["id"] for row in plugin_catalog()}:
            return
        disabled = self._disabled - {identity} if enabled else self._disabled | {identity}
        try:
            env_write_config({"disabled": sorted(disabled)}, filename="ui_dcc_plugins",
                             unique_id="ui_main", long_abs_path=True, scope="installation")
        except OSError as error:
            self._error = str(error)
            self.stateChanged.emit()
            return
        self._error = ""
        self._disabled = disabled
        self._restart = any(row["active"] != row["enabled"] for row in self.rows)
        self.stateChanged.emit()

    def shutdown(self):
        pass
