"""TACTIC-Handler desktop application entry point."""

from __future__ import annotations

import sys
import os
import re
import threading
import traceback
from pathlib import Path

UI_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = UI_ROOT.parents[1]

# The application and TACTIC core must share one Qt runtime. Prevent a host environment from making thlib.side.Qt load PySide2
# or PyQt alongside the PySide6 QML engine.
os.environ["QT_PREFERRED_BINDING"] = "PySide6"

# Keep rendering away from the GUI thread during interactive window resizing.
# The old forced "basic" loop rendered synchronously and made every complex
# QML layout visibly stall while the native resize gesture was in progress.
os.environ.setdefault("QSG_RENDER_LOOP", "threaded")

from PySide6.QtCore import (
    QEvent,
    QObject,
    QTimer,
    QUrl,
    Qt,
    QtMsgType,
    Signal,
    qInstallMessageHandler,
)
from PySide6.QtGui import QFont, QGuiApplication, QIcon, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid

from thlib.ui.application_composition import build_application_runtime
from thlib.ui.hang_diagnostics import UiHangWatchdog
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.single_instance import (
    SingleInstanceGuard,
    instance_server_name,
)


def _destroy_transient_windows(owner: QWindow) -> None:
    """Release owned native windows before Windows destroys them itself."""
    windows = QGuiApplication.allWindows()
    owned: list[tuple[int, QWindow]] = []
    for candidate in windows:
        parent = candidate.transientParent()
        for depth in range(1, len(windows) + 1):
            if parent is owner:
                owned.append((depth, candidate))
                break
            if parent is None:
                break
            parent = parent.transientParent()
    for _depth, candidate in sorted(
        owned, key=lambda entry: entry[0], reverse=True
    ):
        candidate.destroy()


def _is_fixedsys_directwrite_warning(message: str) -> bool:
    lowered = str(message or "").lower()
    return (
        "directwrite: createfontfacefromhdc() failed" in lowered
        and 'family="fixedsys"' in lowered
    )


def _write_stderr(message: str) -> bool:
    """Write a diagnostic when the process still owns a stderr stream."""
    stream = getattr(sys, "stderr", None)
    if stream is None:
        stream = getattr(sys, "__stderr__", None)
    writer = getattr(stream, "write", None)
    if not callable(writer):
        return False
    try:
        writer(str(message or "") + "\n")
        flush = getattr(stream, "flush", None)
        if callable(flush):
            flush()
    except (AttributeError, OSError, TypeError, ValueError):
        return False
    return True


def _bootstrap_message_handler(_message_type, _context, message) -> None:
    if _is_fixedsys_directwrite_warning(message):
        return
    _write_stderr(message)


class FixedsysFontGuard(QObject):
    def eventFilter(self, watched, event) -> bool:
        if event.type() not in {
            QEvent.Type.Polish,
            QEvent.Type.Show,
            QEvent.Type.FontChange,
        } or not hasattr(watched, "font"):
            return False
        font = watched.font()
        if font.family().strip().lower() != "fixedsys":
            return False
        replacement = QFont(font)
        replacement.setFamily("Consolas")
        watched.setFont(replacement)
        return False


class QtRuntimeLogBridge(QObject):
    message_received = Signal(str)
    flush_requested = Signal()

    _IMAGE_NOT_FOUND_KEY = "qml/image-not-found"

    def __init__(self) -> None:
        super().__init__()
        self._pending_lock = threading.Lock()
        self._pending = {}
        self._flush_pending = False
        self._image_not_found_reported = False
        self.flush_requested.connect(
            self._schedule_flush,
            Qt.ConnectionType.QueuedConnection,
        )

    def enqueue(self, message: str) -> None:
        """Coalesce renderer/network diagnostics before touching GUI models."""
        message = str(message or "").strip()
        if not message:
            return
        lowered = message.lower()
        image_not_found = (
            "qquickimage" in lowered
            and "server replied: not found" in lowered
        )
        key = self._IMAGE_NOT_FOUND_KEY if image_not_found else message
        wake = False
        with self._pending_lock:
            bucket = self._pending.setdefault(
                key,
                {"message": message, "count": 0, "samples": []},
            )
            bucket["count"] += 1
            if image_not_found and len(bucket["samples"]) < 5:
                match = re.search(
                    r"Error transferring\s+(.+?)\s+-\s+server replied",
                    message,
                    flags=re.IGNORECASE,
                )
                sample = match.group(1) if match else message
                if sample not in bucket["samples"]:
                    bucket["samples"].append(sample)
            if not self._flush_pending:
                self._flush_pending = True
                wake = True
        if wake:
            self.flush_requested.emit()

    def _schedule_flush(self) -> None:
        QTimer.singleShot(500, self._flush)

    def _flush(self) -> None:
        with self._pending_lock:
            pending = self._pending
            self._pending = {}
            self._flush_pending = False
        for key, bucket in pending.items():
            count = int(bucket["count"])
            if key == self._IMAGE_NOT_FOUND_KEY:
                if self._image_not_found_reported:
                    continue
                samples = bucket["samples"]
                details = "; ".join(samples)
                suffix = f" Examples: {details}" if details else ""
                message = (
                    "MISSING · QML · QQuickImage: "
                    f"{count} image request{'s' if count != 1 else ''} "
                    f"returned Not Found.{suffix}"
                )
            else:
                message = bucket["message"]
                if count > 1:
                    message += f" (repeated {count} times)"
            self.message_received.emit(message)
            if key == self._IMAGE_NOT_FOUND_KEY:
                self._image_not_found_reported = True


def main() -> int:
    if sys.platform == "win32":
        import ctypes

        # Identify the hosted application before Qt creates any native windows;
        # otherwise the taskbar can group it under the Python launcher/icon.
        set_app_id = ctypes.OleDLL("shell32").SetCurrentProcessExplicitAppUserModelID
        set_app_id.argtypes = (ctypes.c_wchar_p,)
        # OleDLL checks HRESULT and raises OSError if Windows rejects the ID.
        set_app_id("TACTIC.Handler.Desktop")

    smoke_offline = os.environ.get("TACTIC_QML_SMOKE_OFFLINE", "") == "1"
    test_settings_dir = os.environ.get("TACTIC_QML_TEST_SETTINGS_DIR", "")
    if test_settings_dir:
        settings_path = Path(test_settings_dir).resolve()
        settings_path.mkdir(parents=True, exist_ok=True)
        from thlib.environment import env_mode
        env_mode.set_current_path(str(settings_path))
    # QSG selects its graphics API when the first application/scene graph is
    # created, so the persisted preference must be applied before QApplication.
    # An explicit process environment value remains the developer/test override.
    from thlib.environment import env_read_config
    from thlib.ui.rendering import apply_render_backend

    render_settings = dict(env_read_config(
        filename="ui_settings",
        unique_id="ui_main",
        long_abs_path=True,
    ) or {})
    apply_render_backend(
        render_settings.get("appearance/renderBackend", "automatic"),
        environment=os.environ,
    )
    QQuickStyle.setStyle("Material")
    # Native glyph bitmaps become pixelated when Qt Quick moves or scales an
    # item on a fractional-DPI screen. Keep text scalable across the whole UI.
    QQuickWindow.setTextRenderType(
        QQuickWindow.TextRenderType.QtTextRendering
    )
    # Qt 6 can resolve the Windows fixed-pitch fallback to the bitmap-only
    # Fixedsys face, which DirectWrite cannot instantiate.
    QFont.insertSubstitution("Fixedsys", "Consolas")
    original_message_handler = qInstallMessageHandler(
        _bootstrap_message_handler
    )
    # QApplication is a strict superset of QGuiApplication.  The QML shell
    # uses it normally, while QWidget-based schema editors remain available.
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("TacticHandler_Client")
    single_instance = SingleInstanceGuard(
        instance_server_name(app.applicationName(), test_settings_dir),
        app,
    )
    if not single_instance.start():
        qInstallMessageHandler(original_message_handler)
        return 0
    from thlib.environment import env_inst

    # Both launchers share the same pools; QML must start them before any
    # controller can enqueue validation, repository or check-in work.
    env_inst.ui_super = app
    env_inst.start_pools()
    app.styleHints().setWheelScrollLines(6)
    application_font = QFont("Segoe UI")
    application_font.setPointSizeF(9.75)
    app.setFont(application_font)
    fixedsys_font_guard = FixedsysFontGuard(app)
    app.installEventFilter(fixedsys_font_guard)
    application_icon_path = (
        UI_ROOT / "assets" / "tactic_favicon.ico"
    )
    if application_icon_path.is_file():
        app.setWindowIcon(QIcon(str(application_icon_path)))
    app.setQuitOnLastWindowClosed(False)
    runtime = build_application_runtime(
        app,
        PROJECT_ROOT,
        application_icon_path,
        diagnostics_root=settings_path if test_settings_dir else PROJECT_ROOT,
        server_pool=env_inst.server_pool,
    )
    controller = runtime.controller
    controller.ui_performance.install()
    localization_controller = runtime.localization
    debug_log = runtime.debug_log
    runtime_log_bridge = QtRuntimeLogBridge()
    runtime_log_bridge.message_received.connect(
        controller.log_runtime_message
    )

    previous_message_handler = None

    def runtime_message_handler(message_type, context, message) -> None:
        message_text = str(message or "").strip()
        lowered = message_text.lower()
        if _is_fixedsys_directwrite_warning(message_text):
            return
        # Windows temporarily locks the system clipboard while another
        # process owns it. Qt retries automatically; this line is not an
        # application failure and otherwise floods both diagnostics surfaces.
        if lowered == "retrying to obtain clipboard.":
            return
        if message_type in {
            QtMsgType.QtWarningMsg,
            QtMsgType.QtCriticalMsg,
            QtMsgType.QtFatalMsg,
        }:
            is_error = (
                message_type
                in {QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg}
                or "error" in lowered
                or "failed" in lowered
                or "cannot " in lowered
            )
            level = "ERROR" if is_error else "WARNING"
            category = str(getattr(context, "category", "") or "")
            source = "QML" if ".qml" in lowered or "qquick" in lowered else "Qt"
            if category and category != "default":
                source = f"{source}/{category}"
            runtime_log_bridge.enqueue(
                f"{level} · {source} · {message_text}"
            )
            # A failed preview may produce hundreds of renderer warnings.
            # The bridge writes one aggregated terminal/log entry instead.
            if (
                "qquickimage" in lowered
                and "server replied: not found" in lowered
            ):
                return

        # Installing a handler must not make diagnostics disappear from the
        # terminal where developers traditionally inspect TACTIC-Handler.
        if previous_message_handler:
            previous_message_handler(message_type, context, message)
        elif message_text:
            _write_stderr(message_text)

    previous_message_handler = qInstallMessageHandler(
        runtime_message_handler
    )

    message_handler_restored = False

    def shutdown() -> None:
        nonlocal message_handler_restored
        try:
            runtime.shutdown()
        finally:
            try:
                single_instance.close()
            finally:
                if not message_handler_restored:
                    qInstallMessageHandler(original_message_handler)
                    message_handler_restored = True
    engine = QQmlApplicationEngine()
    localization_controller.attach_engine(engine)
    qml_errors = []

    def destroy_qml() -> None:
        # Shutdown persists the session after QML teardown. Capture live
        # viewport coordinates while the retained views can still answer.
        controller._capture_current_tree_state()
        for root_object in engine.rootObjects():
            if not isValid(root_object):
                continue
            if isinstance(root_object, QWindow):
                _destroy_transient_windows(root_object)
            if not isValid(root_object):
                continue
            root_object.deleteLater()
        QApplication.sendPostedEvents(
            None, QEvent.Type.DeferredDelete
        )
        engine.deleteLater()
        QApplication.sendPostedEvents(
            None, QEvent.Type.DeferredDelete
        )

    def collect_qml_warnings(warnings) -> None:
        qml_errors.extend(str(warning.toString()) for warning in warnings)

    engine.warnings.connect(collect_qml_warnings)
    runtime.bindings.add_group(
        "application",
        {
            **qml_icon_bindings(PROJECT_ROOT, controller),
            "qmlSmokeMode": bool(smoke_offline),
            "applicationIconUrl": (
                QUrl.fromLocalFile(str(application_icon_path))
                if application_icon_path.is_file()
                else QUrl()
            ),
        },
    )
    runtime.publish_qml_bindings(engine.rootContext())
    qml_path = UI_ROOT / "qml" / "Main.qml"
    if not qml_path.is_file():
        message = f"QML startup failed: {qml_path}: file does not exist"
        _write_stderr(message)
        destroy_qml()
        shutdown()
        return 1
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        reason = "; ".join(qml_errors) or "QQmlApplicationEngine created no root object"
        _write_stderr(f"QML startup failed: {qml_path}: {reason}")
        destroy_qml()
        shutdown()
        return 1
    root_window = engine.rootObjects()[0]
    env_inst.ui_main = root_window
    env_inst.ui_script_editor = runtime.script_editor
    runtime.tray.attach_window(root_window)
    single_instance.set_activation_handler(runtime.tray.show_window)
    runtime.handler_server.showWindowRequested.connect(
        runtime.tray.show_window
    )
    if not smoke_offline:
        # Let the first frame reach the screen before disk or server work.
        controller.authentication_changed.connect(
            runtime.server_updates.sync_authentication
        )
        controller.project_changed.connect(runtime.watch_folders.reload)

        def start_after_first_frame() -> None:
            controller.restore_cached_workspace()
            controller.bootstrap_server()
            runtime.handler_server.start_server()

        root_window.frameSwapped.connect(
            start_after_first_frame,
            Qt.ConnectionType.SingleShotConnection,
        )


    startup_hook_pending = {"value": True}

    def run_after_ui_started(_project_code="", _title="") -> None:
        if not startup_hook_pending["value"]:
            return
        if not controller.current_project_code:
            return
        startup_hook_pending["value"] = False
        try:
            from execute_after_start import execute
            execute()
        except Exception as error:
            debug_log.raise_error(
                error,
                stacktrace=traceback.format_exc(),
                group="startup/custom-scripts",
            )

    runtime.script_editor.scriptsLoaded.connect(run_after_ui_started)
    smoke_windows = os.environ.get("TACTIC_QML_SMOKE_WINDOWS", "") == "1"
    if smoke_windows:
        original_windows = list(controller.window_model._windows)
        original_z_counter = controller.window_model._z_counter
        window_ids = [
            window.window_id for window in controller.window_model._windows
        ]
        smoke_steps = [
            (window_id, visible)
            for _pass in range(2)
            for window_id in window_ids
            for visible in (True, False)
        ]

        def advance_window_smoke() -> None:
            if not smoke_steps:
                controller.window_model._windows = original_windows
                controller.window_model._z_counter = original_z_counter
                controller.window_model._save()
                app.quit()
                return
            window_id, visible = smoke_steps.pop(0)
            if visible:
                controller.window_model.show_window(window_id)
            else:
                controller.window_model.close_window(window_id)

            def verify_and_continue() -> None:
                for window in QGuiApplication.allWindows():
                    if not window.isVisible():
                        continue
                    minimum_width = int(window.minimumWidth())
                    minimum_height = int(window.minimumHeight())
                    if window.width() < minimum_width:
                        qml_errors.append(
                            f"{window.title()}: width below minimum"
                        )
                    if window.height() < minimum_height:
                        qml_errors.append(
                            f"{window.title()}: height below minimum"
                        )
                advance_window_smoke()

            QTimer.singleShot(35, verify_and_continue)

        advance_window_smoke()
    smoke_exit_ms = int(os.environ.get("TACTIC_QML_SMOKE_EXIT_MS", "0") or 0)
    if smoke_exit_ms and not smoke_windows:
        QTimer.singleShot(smoke_exit_ms, app.quit)
    ui_hang_watchdog = UiHangWatchdog(
        settings_path if test_settings_dir else PROJECT_ROOT,
        parent=app,
    )
    ui_hang_watchdog.start()
    try:
        exit_code = app.exec()
    finally:
        ui_hang_watchdog.stop()
    if smoke_windows and qml_errors:
        _write_stderr(
            "QML window smoke warnings:\n"
            + "\n".join(qml_errors)
        )
        exit_code = 1
    destroy_qml()
    shutdown()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
