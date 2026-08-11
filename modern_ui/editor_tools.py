from __future__ import annotations

import os
import tempfile
import traceback
from pathlib import Path

from PySide6.QtCore import QPoint, QObject, Property, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication

from modern_ui.workspace_models.records import RecordListModel


class ServerPresetsController(QObject):
    stateChanged = Signal()

    def __init__(self, workspace_state, parent=None) -> None:
        super().__init__(parent)
        self._workspace_state = workspace_state
        self.model = RecordListModel(("name", "isProtected", "selected"))
        self._original = []
        self._error = ""
        self.reload()

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Slot()
    def reload(self):
        from thlib.environment import env_server
        env_server.server_presets = None
        env_server.get_server_presets_defaults()
        values = env_server.get_server_presets() or {}
        self._original = list(values.get("presets_list") or ["default"])
        self._replace(self._original)

    def _replace(self, names):
        self.model.replace([
            {"name": name, "isProtected": name == "default", "selected": False}
            for name in names
        ])
        self._error = ""
        self.stateChanged.emit()

    @Slot(str, result=bool)
    def add(self, name):
        name = str(name or "").strip()
        names = [row["name"] for row in self.model._records]
        if not name or name == "environment_config" or name in names:
            self._error = "Choose a unique preset name"
            self.stateChanged.emit()
            return False
        self._replace(names + [name])
        return True

    @Slot(int)
    def remove(self, row):
        if not 0 <= row < len(self.model._records):
            return
        if self.model._records[row]["isProtected"]:
            self._error = "The default preset cannot be removed"
            self.stateChanged.emit()
            return
        names = [item["name"] for index, item in enumerate(self.model._records)
                 if index != row]
        self._replace(names)

    @Slot()
    def cancel(self):
        self._replace(self._original)

    @Slot(result=bool)
    def save(self):
        from thlib.environment import env_server
        names = [row["name"] for row in self.model._records]
        current = env_server.get_cur_srv_preset()
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
        self._original = list(names)
        self._error = ""
        self.stateChanged.emit()
        return True


class ScreenshotController(QObject):
    stateChanged = Signal()
    targetChanged = Signal()
    captured = Signal(str)
    operationCaptured = Signal(str, str)

    def __init__(
        self, checkin_controller, debug_log, commit_queue=None, parent=None
    ):
        super().__init__(parent)
        self._checkin = checkin_controller
        self._commit_queue = commit_queue
        self._debug_log = debug_log
        self._busy = False
        self._selecting = False
        self._error = ""
        self._files = []
        self._target_operation_id = ""
        self._hidden_windows = []
        self._active_window = None
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
    def begin_capture(self):
        if self._busy or self._selecting:
            return
        self._active_window = QGuiApplication.focusWindow()
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
        self._busy = True
        self._selecting = False
        self._error = ""
        self.stateChanged.emit()
        QTimer.singleShot(
            140,
            lambda: self._capture(x, y, width, height, operation_id),
        )

    def _capture(self, x, y, width, height, operation_id=""):
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
            if operation_id:
                if (
                    self._commit_queue is None
                    or not self._commit_queue.add_preview_paths(
                        operation_id, [url]
                    )
                ):
                    raise RuntimeError(
                        "The selected commit operation is no longer editable"
                    )
                self.operationCaptured.emit(url.toString(), operation_id)
            else:
                self._files.append(path)
                self._checkin.add_files([url])
                self.captured.emit(url.toString())
        except Exception as error:
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
        for path in self._files:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
        self._files.clear()


from modern_ui.script_editor import ScriptEditorController


__all__ = [
    "ScreenshotController", "ScriptEditorController",
    "ServerPresetsController",
]
