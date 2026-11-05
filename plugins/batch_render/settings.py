"""Batch settings owner."""
from __future__ import annotations

from copy import deepcopy
from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication
from thlib.ui.window_geometry import (
    current_screens,
    resolve_window_state,
    screen_for_window_rect,
)
from .queue_state import _TERMINAL, _ACTIVE


class SettingsMixin:
    def initialize(self):
        if self._offline:
            self.stateChanged.emit()
            return
        self._submit(
            self._load_saved_state,
            self._state_loaded,
            self._state_load_failed,
        )

    def _load_saved_state(self):
        from thlib.environment import env_read_config, env_server
        from thlib.ui.server_address import normalize_tactic_server_url

        endpoint = normalize_tactic_server_url(env_server.get_server())
        scope = f"{env_server.get_user()} | {endpoint} | {self._project_code}"
        settings = env_read_config(filename="batch_render", sub_id=scope) or {}
        window_state = env_read_config(filename="batch_render_window", sub_id=scope) or {}
        queue = env_read_config(filename="batch_render_queue", sub_id=scope) or {}
        return settings, window_state, queue, scope

    def _state_loaded(self, payload):
        settings, window_state, queue, self._scope = payload
        previous_web = (
            self._config.get("web_enabled", True),
            self._config.get("web_port", 92),
            self._config.get("web_security", True),
        )
        self._config.update(
            {key: value for key, value in settings.items() if key in self._config}
        )
        if (
            self._window is not None
            and (
                self._config.get("web_enabled", True),
                self._config.get("web_port", 92),
                self._config.get("web_security", True),
            ) != previous_web
        ):
            self._restart_web_server()
        self._filter_preferences = set(window_state["episodeStatuses"]) if "episodeStatuses" in window_state else None
        self._window_state = self._resolved_window_state(window_state)
        visible_statuses = set(self._window_state["episodeStatuses"])
        self.episode_filters.replace([
            {**row, "active": row["value"] in visible_statuses}
            for row in self.episode_filters.records()
        ])
        self.episodeFiltersChanged.emit()
        if queue and queue.get("version") != 1:
            raise ValueError(
                "Unknown batch queue format; saved queue has not been overwritten"
            )
        self._entries = queue.get("entries", [])
        for entry in self._entries:
            if entry["state"] not in _TERMINAL:
                entry.update(
                    state="held",
                    restored=True,
                    stage="Restored · resume or retry explicitly",
                )
            for job in entry["jobs"]:
                if job["state"] in _ACTIVE:
                    job.update(
                        state="failed",
                        stage="Interrupted session",
                        pid="",
                        error="Interrupted session; verify output before retrying",
                    )
            entry["prepared"] = False
        self._server_seen = set(queue.get("serverSeen", []))
        self._ready = True
        self._publish_queue()
        self.settingsChanged.emit()
        self.windowStateChanged.emit()
        self.stateChanged.emit()
        self.refresh()

    def _state_load_failed(self, error):
        self._write_blocked = True
        self._error_message(error)

    def _persist(self):
        if self._offline or not self._ready or self._write_blocked:
            return
        self._pending_save = {
            "version": 1,
            "entries": deepcopy(self._entries),
            "serverSeen": sorted(self._server_seen),
        }
        self._save_next()

    def _flush_queue(self):
        self._publish_queue()
        self._persist()

    def _save_next(self):
        if self._saving or self._pending_save is None:
            return
        from thlib.environment import env_write_config

        payload, self._pending_save = self._pending_save, None
        self._saving = True
        self._submit(
            lambda: env_write_config(
                payload,
                filename="batch_render_queue",
                sub_id=self._scope,
                update_file=True,
            ),
            self._queue_saved,
            self._queue_save_failed,
        )

    def _queue_saved(self, _value):
        self._saving = False
        self._save_next()
        self._maybe_close()

    def _queue_save_failed(self, error):
        self._saving = False
        self._paused = True
        self._error_message(error)
        self._maybe_close()

    def _resolved_window_state(self, values):
        state = {**self._window_state, **(values or {})}
        state["width"] = max(950, int(state["width"]))
        state["height"] = max(650, int(state["height"]))
        saved_statuses = state.get("episodeStatuses")
        if not isinstance(saved_statuses, (list, tuple)):
            saved_statuses = self.visibleEpisodeStatuses
        selected_statuses = {
            status for status in saved_statuses if isinstance(status, str)
        }
        screens, primary = current_screens()
        geometry = resolve_window_state(state, screens, primary)
        geometry.update(
            episodeWidth=max(250, int(state.get("episodeWidth", 350))),
            detailHeight=max(120, int(state.get("detailHeight", 235))),
            logPanelVisible=bool(state.get("logPanelVisible", True)),
            detailPage=(
                state.get("detailPage")
                if state.get("detailPage") in {"log", "preview", "details"}
                else "log"
            ),
            followLog=bool(state.get("followLog", True)),
            freezeLog=bool(state.get("freezeLog", False)),
            episodeStatuses=sorted(selected_statuses),
        )
        return geometry

    @Slot("QVariantMap")
    def saveWindowState(self, values):
        values = dict(values or {})
        maximized = bool(values.get("maximized", False))
        state = dict(self._window_state)
        if not maximized:
            state.update(values)
        for key in (
            "episodeWidth",
            "detailHeight",
            "logPanelVisible",
            "detailPage",
            "followLog",
            "freezeLog",
            "episodeStatuses",
        ):
            if key in values:
                state[key] = values[key]
        state["maximized"] = maximized
        screen = screen_for_window_rect(
            int(state["x"]),
            int(state["y"]),
            int(state["width"]),
            int(state["height"]),
        )
        if screen:
            state.update(
                screen_identity=screen.identity,
                screen_name=screen.name,
                screen_x=screen.x,
                screen_y=screen.y,
                screen_width=screen.width,
                screen_height=screen.height,
            )
        self._window_state = self._resolved_window_state(state)
        if self._offline or not self._scope:
            return
        from thlib.environment import env_write_config

        self._submit(
            lambda: env_write_config(
                self._window_state,
                filename="batch_render_window",
                sub_id=self._scope,
                update_file=True,
            ),
            lambda _value: None,
        )

    @Slot(str, str, str, bool, int, str, bool, int, bool, int, bool)
    def saveSettings(
        self,
        maya_path,
        save_path,
        camera,
        stop_on_error,
        timeout,
        log_checkin,
        skip_dependency_errors,
        update_interval,
        web_enabled,
        web_port,
        web_security,
    ):
        if self.running:
            self._error_message(
                ValueError(
                    "Pause the queue and wait for the current shot before changing render settings"
                )
            )
            return
        values = {
            "maya_render_executable": maya_path.strip(),
            "output_directory": save_path.strip(),
            "camera": camera.strip(),
            "stop_on_error": bool(stop_on_error),
            "render_timeout_minutes": max(0, timeout),
            "log_checkin": str(log_checkin),
            "skip_dependency_errors": bool(skip_dependency_errors),
            "update_interval": max(5, int(update_interval)),
            "web_enabled": bool(web_enabled),
            "web_port": int(web_port),
            "web_security": bool(web_security),
        }
        if not values["maya_render_executable"] or not values["output_directory"]:
            self._error_message(
                ValueError("Render executable and output directory are required")
            )
            return
        if values["log_checkin"] not in {"always", "failed", "never"}:
            self._error_message(ValueError("Unknown log check-in mode"))
            return
        if not 1 <= values["web_port"] <= 65535:
            self._error_message(
                ValueError("Web control port must be between 1 and 65535")
            )
            return
        from thlib.environment import env_write_config

        self._submit(
            lambda: env_write_config(
                values,
                filename="batch_render",
                sub_id=self._scope,
                update_file=True,
            ),
            lambda _value: self._settings_saved(values),
        )

    def _settings_saved(self, values):
        restart_web = any(
            values[key] != self._config.get(key)
            for key in ("web_enabled", "web_port", "web_security")
        )
        restart_poll = values["update_interval"] != self._config.get(
            "update_interval"
        )
        self._config.update(values)
        if restart_web:
            self._restart_web_server()
        if restart_poll:
            self._schedule_poll()
        self.settingsChanged.emit()

    @Slot(str)
    def openPath(self, path):
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    @Slot()
    def openSelectedLog(self):
        detail = self.selectedDetail
        if detail.get("logPath"):
            self.openPath(detail["logPath"])
            return
        self._status = (
            "Render log is available after the shot starts"
            if detail.get("child")
            else "Select a shot to open its render log"
        )
        self.stateChanged.emit()

    @Slot(QUrl, result=str)
    def localPath(self, url):
        return url.toLocalFile()

    @Slot()
    def showDestination(self):
        self.openPath(self._config["output_directory"])

    @Slot(str)
    def showQueueDestination(self, identity):
        entry, job = self._find(identity)
        if entry is self._active_entry and self._active_job is not None:
            job = self._active_job
        elif entry is not None and job is None:
            job = next(
                (row for row in reversed(entry["jobs"]) if row.get("renderOutput")),
                None,
            )
        self.openPath(
            (job or {}).get("renderOutput")
            or (job or {}).get("output")
            or self._config["output_directory"]
        )

    def attach_window(self, window) -> None:
        self._window = window
        self._create_tray()
        self._restart_web_server()

    def _create_tray(self) -> None:
        try:
            from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

            if not isinstance(QApplication.instance(), QApplication):
                return
            tray = QSystemTrayIcon(QGuiApplication.windowIcon(), self)
            menu = QMenu()
            start = QAction("Start Scheduler", menu)
            stop = QAction("Stop Scheduler", menu)
            show = QAction("Show Dispatcher", menu)
            hide = QAction("Hide Dispatcher", menu)
            close = QAction("Exit", menu)
            start.triggered.connect(self.startScheduler)
            stop.triggered.connect(self.stopScheduler)
            show.triggered.connect(self.showWindow)
            hide.triggered.connect(self.hideWindow)
            close.triggered.connect(self.closeWindow)
            menu.addActions((start, stop))
            menu.addSeparator()
            menu.addActions((show, hide))
            menu.addSeparator()
            menu.addAction(close)
            tray.setContextMenu(menu)
            tray.activated.connect(
                lambda reason: (
                    self.showWindow()
                    if reason
                    in {
                        QSystemTrayIcon.ActivationReason.Trigger,
                        QSystemTrayIcon.ActivationReason.DoubleClick,
                    }
                    else None
                )
            )
            tray.show()
            self._tray = tray
            self._tray_menu = menu
        except (ImportError, RuntimeError):
            self._tray = None

    @Slot()
    def showWindow(self) -> None:
        if self._window:
            self._window.show()
            self._window.requestActivate()

    @Slot()
    def hideWindow(self) -> None:
        if self._window:
            self._window.hide()

    @Slot()
    def closeWindow(self):
        self._close_requested = True
        self._paused = True
        self._watch_server = False
        self._poll_timer.stop()
        if self._active_entry:
            self.interruptRender()
        self.stateChanged.emit()
        self._maybe_close()

    def _maybe_close(self):
        if (
            not self._close_requested
            or self._stage_operation is not None
            or self._saving
        ):
            return
        # Finish discovery and persist the queue before disposing its owner.
        if self._operations:
            return
        self.shutdown()
        self.windowCloseRequested.emit()

    def shutdown(self):
        if self._closing:
            return
        self._closing = True
        with self._web_lock:
            for reply in self._web_pending:
                if not reply.done():
                    reply.set_exception(RuntimeError('Batch Render is closing'))
            self._web_pending.clear()
        self._cancel.set()
        if self._web_server:
            self._web_server.stop()
            self._web_server = None
            self.webChanged.emit()
        self._poll_timer.stop()
        self._clock.stop()
        self._progress_timer.stop()
        for operation, subscriptions in self._operations.values():
            operation.cancel()
            for subscription in subscriptions:
                subscription.close()
        self._operations.clear()
        if self._tray:
            self._tray.hide()
