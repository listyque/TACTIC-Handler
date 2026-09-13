from __future__ import annotations

import os
import tempfile
import traceback
from pathlib import Path

from PySide6.QtCore import QPoint, QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication

from thlib.ui.workspace_models.records import RecordListModel


class ServerPresetsController(QObject):
    stateChanged = Signal()
    sessionStarted = Signal()

    def __init__(self, workspace_state, parent=None) -> None:
        super().__init__(parent)
        self._workspace_state = workspace_state
        self.model = RecordListModel((
            "name", "isProtected", "isActive", "selected",
        ))
        self._original_names: list[str] = []
        self._original_presets: dict[str, dict] = {}
        self._drafts: dict[str, dict] = {}
        self._active_name = ""
        self._selected_row = -1
        self._error = ""

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(int, notify=stateChanged)
    def selected_row(self) -> int:
        return self._selected_row

    @Property(str, notify=stateChanged)
    def selected_name(self) -> str:
        if not 0 <= self._selected_row < len(self.model._records):
            return ""
        return str(self.model._records[self._selected_row].get("name") or "")

    @Property("QVariantMap", notify=stateChanged)
    def selected_values(self) -> dict:
        payload = dict(self._drafts.get(self.selected_name) or {})
        site = dict(payload.get("site") or {})
        proxy = dict(payload.get("proxy") or {})
        return {
            "serverUrl": str(payload.get("server") or ""),
            "storedUser": str(payload.get("user") or ""),
            "hasTicket": bool(payload.get("ticket")),
            "siteEnabled": bool(site.get("enabled")),
            "siteName": str(site.get("site_name") or ""),
            "proxyEnabled": bool(proxy.get("enabled")),
            "proxyLogin": str(proxy.get("login") or ""),
            "proxyServer": str(proxy.get("server") or ""),
            "proxyPassword": "",
            "hasProxyPassword": bool(proxy.get("pass")),
        }

    @staticmethod
    def _normalized_payload(payload: dict, defaults: dict) -> dict:
        result = dict(defaults or {})
        result.update(dict(payload or {}))
        default_site = dict((defaults or {}).get("site") or {})
        default_site.update(dict(result.get("site") or {}))
        result["site"] = default_site
        default_proxy = dict((defaults or {}).get("proxy") or {})
        default_proxy.update(dict(result.get("proxy") or {}))
        result["proxy"] = default_proxy
        return result

    def _replace(self, names, selected_name="") -> None:
        names = [str(name) for name in names]
        if not selected_name and 0 <= self._selected_row < len(
            self.model._records
        ):
            selected_name = str(
                self.model._records[self._selected_row].get("name") or ""
            )
        if selected_name not in names:
            selected_name = names[0] if names else ""
        self._selected_row = (
            names.index(selected_name) if selected_name in names else -1
        )
        self.model.replace([
            {
                "name": name,
                "isProtected": name == "default",
                "isActive": name == self._active_name,
                "selected": index == self._selected_row,
            }
            for index, name in enumerate(names)
        ])
        self._error = ""
        self.stateChanged.emit()

    @Slot()
    def reload(self):
        from copy import deepcopy
        from thlib.environment import env_server

        env_server.server_presets = None
        env_server.get_server_presets_defaults()
        values = env_server.get_server_presets() or {}
        names = list(values.get("presets_list") or ["default"])
        defaults = env_server.get_default_preset()
        drafts = {
            name: self._normalized_payload(
                env_server.get_server_preset(name) or {},
                defaults,
            )
            for name in names
        }
        self._original_names = list(names)
        self._original_presets = deepcopy(drafts)
        self._drafts = drafts
        current = str(values.get("current") or "")
        if current not in names:
            current = "default" if "default" in names else names[0]
        self._active_name = current
        self._replace(names, current)

    @Slot()
    def begin_session(self) -> None:
        self.reload()
        self.sessionStarted.emit()

    @Slot(int)
    def select(self, row: int) -> None:
        if not 0 <= row < len(self.model._records):
            return
        name = str(self.model._records[row].get("name") or "")
        self._selected_row = row
        self._replace(
            [record["name"] for record in self.model._records],
            name,
        )

    @Slot(str, result=bool)
    def add(self, name):
        name = str(name or "").strip()
        names = [row["name"] for row in self.model._records]
        if not name or name == "environment_config" or name in names:
            self._error = "Choose a unique preset name"
            self.stateChanged.emit()
            return False
        from thlib.environment import env_server

        payload = self._normalized_payload(
            env_server.get_default_preset(), {}
        )
        payload["server"] = str(env_server.get_server() or "")
        payload["user"] = ""
        payload["ticket"] = None
        self._drafts[name] = payload
        self._replace(names + [name], name)
        return True

    @Slot(int)
    def remove(self, row):
        if not 0 <= row < len(self.model._records):
            return
        record = self.model._records[row]
        if record["isProtected"]:
            self._error = "The default preset cannot be removed"
            self.stateChanged.emit()
            return
        name = str(record.get("name") or "")
        if name == self._active_name:
            self._error = (
                "Switch to another server preset before deleting the active "
                "preset"
            )
            self.stateChanged.emit()
            return
        names = [
            item["name"] for index, item in enumerate(self.model._records)
            if index != row
        ]
        self._drafts.pop(name, None)
        selected_name = names[min(row, len(names) - 1)] if names else ""
        self._replace(names, selected_name)

    @Slot("QVariantMap")
    def update_selected(self, values: dict) -> None:
        name = self.selected_name
        if not name:
            return
        payload = dict(self._drafts.get(name) or {})
        site = dict(payload.get("site") or {})
        proxy = dict(payload.get("proxy") or {})
        payload["server"] = str(values.get("serverUrl") or "").strip()
        site.update({
            "enabled": bool(values.get("siteEnabled")),
            "site_name": str(values.get("siteName") or "").strip(),
        })
        proxy.update({
            "enabled": bool(values.get("proxyEnabled")),
            "login": str(values.get("proxyLogin") or "").strip(),
            "server": str(values.get("proxyServer") or "").strip(),
        })
        replacement_password = str(values.get("proxyPassword") or "")
        if replacement_password:
            proxy["pass"] = replacement_password
        payload["site"] = site
        payload["proxy"] = proxy
        self._drafts[name] = payload
        self._error = ""
        self.stateChanged.emit()

    def _validation_error(self) -> str:
        from thlib.ui.server_address import (
            is_valid_tactic_server_url,
        )

        for name in (
            str(record.get("name") or "") for record in self.model._records
        ):
            payload = dict(self._drafts.get(name) or {})
            server_url = str(payload.get("server") or "").strip()
            if not is_valid_tactic_server_url(server_url):
                return "Enter a valid server address for every preset"
            site = dict(payload.get("site") or {})
            if site.get("enabled") and not str(
                site.get("site_name") or ""
            ).strip():
                return "Enter a portal site name or disable portal site"
            proxy = dict(payload.get("proxy") or {})
            if proxy.get("enabled") and not str(
                proxy.get("server") or ""
            ).strip():
                return "Enter a proxy server or disable the proxy"
        return ""

    @Slot()
    def cancel(self):
        from copy import deepcopy

        self._drafts = deepcopy(self._original_presets)
        self._replace(self._original_names)

    @Slot(result=bool)
    def save(self):
        from copy import deepcopy
        from thlib.environment import (
            env_mode,
            env_server,
            env_write_config,
        )
        from thlib.ui.server_address import normalize_tactic_server_url

        self._error = self._validation_error()
        if self._error:
            self.stateChanged.emit()
            return False
        names = [row["name"] for row in self.model._records]
        current = env_server.get_cur_srv_preset()
        unique_id = (
            f"{env_mode.node}/environment_config/server_presets"
        )
        for name in names:
            payload = deepcopy(self._drafts[name])
            payload["server"] = normalize_tactic_server_url(
                payload.get("server")
            )
            self._drafts[name] = payload
            env_write_config(
                deepcopy(payload),
                filename=name,
                unique_id=unique_id,
            )
        env_server.server_presets["presets_list"] = names
        if current not in names:
            env_server.server_presets["current"] = "default"
        env_server.server_presets_defaults["server_presets"] = dict(
            env_server.server_presets
        )
        env_server.save_server_presets_defaults()
        self._workspace_state.server_preset_model.replace([
            {"label": name} for name in names
        ])
        self._original_names = list(names)
        self._original_presets = deepcopy(self._drafts)
        self._error = ""
        self.stateChanged.emit()
        return True


class ScreenshotController(QObject):
    stateChanged = Signal()
    targetChanged = Signal()
    operationCaptured = Signal(str, str)

    def __init__(
        self, debug_log, commit_queue=None, parent=None
    ):
        super().__init__(parent)
        self._commit_queue = commit_queue
        self._debug_log = debug_log
        self._busy = False
        self._selecting = False
        self._error = ""
        self._target_operation_id = ""
        self._hidden_windows = []
        self._active_window = None
        self._pending_capture = None
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.dataChanged.connect(self.stateChanged)

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(bool, notify=stateChanged)
    def selecting(self):
        return self._selecting

    @Property(bool, notify=stateChanged)
    def clipboardHasImage(self):
        clipboard = QGuiApplication.clipboard()
        mime_data = clipboard.mimeData() if clipboard else None
        return bool(mime_data and mime_data.hasImage())

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(str, notify=targetChanged)
    def targetOperationId(self):
        return self._target_operation_id

    @Slot(str)
    def prepare_for_operation(self, operation_id):
        operation_id = str(operation_id or "")
        if operation_id == self._target_operation_id:
            return
        self._target_operation_id = operation_id
        self.targetChanged.emit()

    @Slot()
    def clear_operation_target(self):
        if not self._target_operation_id:
            return
        self._target_operation_id = ""
        self.targetChanged.emit()

    @Slot()
    @Slot(QObject)
    def begin_capture(self, return_window=None):
        if self._busy or self._selecting:
            return
        if not self._target_operation_id:
            self._error = (
                "Select a Commit Queue operation before capturing a preview"
            )
            self.stateChanged.emit()
            return
        self._active_window = return_window or QGuiApplication.focusWindow()
        self._hidden_windows = [
            (window, window.visibility())
            for window in QGuiApplication.allWindows()
            if window.isVisible()
        ]
        for window, _visibility in self._hidden_windows:
            window.hide()
        self._error = ""
        self._selecting = True
        self.stateChanged.emit()

    @Slot()
    def cancel_capture(self):
        if not self._selecting:
            self.clear_operation_target()
            return
        self._selecting = False
        self._error = ""
        self.clear_operation_target()
        self._restore_windows()
        self.stateChanged.emit()

    def _restore_windows(self):
        windows, self._hidden_windows = self._hidden_windows, []
        for window, visibility in windows:
            window.setVisibility(visibility)
        if any(window is self._active_window for window, _state in windows):
            self._active_window.requestActivate()
        self._active_window = None

    @Slot(int, int, int, int)
    def capture(self, x, y, width, height):
        if self._busy or width < 8 or height < 8:
            return
        operation_id = self._target_operation_id
        if not operation_id:
            self._selecting = False
            self._error = (
                "Select a Commit Queue operation before capturing a preview"
            )
            self._restore_windows()
            self.stateChanged.emit()
            return
        self._busy = True
        self._selecting = False
        self._error = ""
        self._pending_capture = (x, y, width, height, operation_id)
        self.stateChanged.emit()

    @Slot()
    def finish_capture(self):
        """Capture after QML confirms that the selection overlay is hidden."""
        pending, self._pending_capture = self._pending_capture, None
        if not self._busy or pending is None:
            return
        self._capture(*pending)

    def _capture(self, x, y, width, height, operation_id=""):
        path = ""
        transferred_to_queue = False
        try:
            screen = QGuiApplication.screenAt(QPoint(x, y))
            screen = screen or QGuiApplication.primaryScreen()
            if screen is None:
                raise RuntimeError("No screen is available for capture")
            geometry = screen.geometry()
            local_x = max(0, x - geometry.x())
            local_y = max(0, y - geometry.y())
            capture_width = min(width, geometry.width() - local_x)
            capture_height = min(height, geometry.height() - local_y)
            if capture_width < 1 or capture_height < 1:
                raise RuntimeError("The selected area is outside the screen")
            pixmap = screen.grabWindow(
                0, local_x, local_y, capture_width, capture_height
            )
            if pixmap.isNull():
                raise RuntimeError("Desktop capture returned an empty image")
            handle, path = tempfile.mkstemp(prefix="th_screenshot_", suffix=".png")
            os.close(handle)
            if not pixmap.save(path, "PNG"):
                raise RuntimeError("Could not save the captured image")
            url = QUrl.fromLocalFile(path)
            if not operation_id:
                raise RuntimeError(
                    "No Commit Queue operation was selected for the preview"
                )
            if (
                self._commit_queue is None
                or not self._commit_queue.add_preview_paths(
                    operation_id, [url]
                )
            ):
                raise RuntimeError(
                    "The selected commit operation is no longer editable"
                )
            transferred_to_queue = True
            self.operationCaptured.emit(url.toString(), operation_id)
        except Exception as error:
            if path and not transferred_to_queue:
                Path(path).unlink(missing_ok=True)
            self._error = str(error)
            stack = traceback.format_exc()
            self._debug_log.raise_error(
                error, stacktrace=stack, group="screenshot/capture"
            )
        finally:
            self._busy = False
            self.clear_operation_target()
            self._restore_windows()
            self.stateChanged.emit()

    @Slot(str, result=bool)
    def paste_preview_from_clipboard(self, operation_id):
        if self._busy or self._commit_queue is None:
            return False
        operation_id = str(operation_id or "")
        image = QGuiApplication.clipboard().image()
        if image.isNull():
            self._error = "The clipboard does not contain an image"
            self.stateChanged.emit()
            return False
        handle, path = tempfile.mkstemp(
            prefix="th_preview_clipboard_", suffix=".png"
        )
        os.close(handle)
        try:
            if not image.save(path, "PNG"):
                raise RuntimeError("Could not save the clipboard image")
            if not self._commit_queue.add_preview_paths(
                operation_id, [QUrl.fromLocalFile(path)]
            ):
                raise RuntimeError(
                    "The selected commit operation is no longer editable"
                )
        except Exception as error:
            Path(path).unlink(missing_ok=True)
            self._error = str(error)
            self._debug_log.raise_error(
                error,
                stacktrace=traceback.format_exc(),
                group="screenshot/clipboard",
            )
            self.stateChanged.emit()
            return False
        self._error = ""
        self.operationCaptured.emit(
            QUrl.fromLocalFile(path).toString(), operation_id
        )
        self.stateChanged.emit()
        return True

    def shutdown(self):
        if self._selecting:
            self._selecting = False
            self._restore_windows()
        self.clear_operation_target()


from thlib.ui.script_editor import ScriptEditorController


__all__ = [
    "ScreenshotController", "ScriptEditorController",
    "ServerPresetsController",
]
