"""Batch web control owner."""
from __future__ import annotations

from concurrent.futures import Future
from pathlib import Path
from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication
from .web import BatchWebServer


class WebControlMixin:
    def _web_dispatch(self, request):
        reply = Future()
        with self._web_lock:
            if self._closing:
                raise RuntimeError('Batch Render is closing')
            self._web_pending.add(reply)
        def handle():
            if not reply.set_running_or_notify_cancel():
                return
            try:
                result = self._handle_web_request(request)
            except Exception as error:
                if not reply.done():
                    reply.set_exception(error)
            else:
                if not reply.done():
                    reply.set_result(result)
        self._dispatchRequested.emit(handle)
        try:
            return reply.result(timeout=10)
        finally:
            with self._web_lock:
                self._web_pending.discard(reply)
                reply.cancel()

    def _handle_web_request(self, request):
        request_type = request.get("type")
        if request_type == "state":
            return self._web_state(str(request.get("selected") or ""))
        if request_type == "preview":
            return self._web_preview(
                str(request.get("job") or ""), int(request.get("index", -1))
            )
        if request_type == "thumb":
            return self._web_thumb(str(request.get("identity") or ""))
        if request_type != "action":
            raise ValueError("Unknown web request")
        return self._web_action(request)

    def _web_state(self, identity):
        frame_seconds = self._frame_seconds()
        queue = [
            {
                "episode": self._episode_record(entry, frame_seconds),
                "shots": [
                    self._shot_record(entry, job, frame_seconds)
                    for job in entry["jobs"]
                ],
            }
            for entry in self._entries
        ]
        job = self._preview_job(identity)
        previews = [
            {"jobId": job["id"], "title": Path(path).name}
            for path in (job or {}).get("renderFiles", [])
        ]
        return {
            "ready": self._ready,
            "busy": self._busy,
            "running": self.running,
            "paused": self._paused,
            "watchServer": self._watch_server,
            "autoClear": self._auto_clear_finished,
            "status": self.statusText,
            "error": self._error,
            "summary": self.summary,
            "settings": self.settings,
            "theme": self._web_theme,
            "filters": self.episode_filters.records(),
            "episodes": self.episodes.records(),
            "queue": queue,
            "selected": self._detail(identity),
            "log": self._log_text(identity),
            "previews": previews,
        }

    def _web_preview(self, identity, index):
        job = self._preview_job(identity)
        files = (job or {}).get("renderFiles", [])
        if not 0 <= index < len(files):
            raise ValueError("Preview is no longer available")
        return files[index]

    def _web_thumb(self, identity):
        entry, job = self._find(identity)
        row = job or entry
        if row is None:
            row = self.episodes.lookup("searchKey", identity)
        url = str((row or {}).get("previewUrl") or "")
        if url.startswith(("http://", "https://")):
            return url
        path = QUrl(url).toLocalFile()
        if not path or not Path(path).is_file():
            raise ValueError("Preview is no longer available")
        return path

    def _web_action(self, request):
        action = str(request.get("action") or "")
        simple = {
            "toggle": self.toggleScheduler,
            "stop": self.interruptRender,
            "refresh": self.refresh,
            "clear": self.clearCompleted,
            "open-root-output": self.showDestination,
        }
        if action in simple:
            simple[action]()
            return {"ok": True}
        if action == "watch":
            self.watchServer(not self._watch_server)
            return {"ok": True}
        if action == "auto":
            self.setAutoClearFinished(not self._auto_clear_finished)
            return {"ok": True}
        if action == "filter":
            status = str(request.get("value") or "")
            if status not in {row["value"] for row in self.episode_filters.records()}:
                raise ValueError("Unknown episode status")
            self.toggleEpisodeStatusFilter(status)
            return {"ok": True}
        if action == "settings":
            values = request.get("values") or {}
            if not isinstance(values, dict):
                raise ValueError("Invalid render settings")
            web_security = values.get(
                "webSecurity", self._config.get("web_security", True)
            )
            self.saveSettings(
                str(values.get("mayaPath") or ""),
                str(values.get("savePath") or ""),
                str(values.get("camera") or ""),
                bool(values.get("stopOnError")),
                int(values.get("timeout") or 0),
                str(values.get("logCheckin") or "always"),
                bool(values.get("skipDependencyErrors")),
                int(values.get("pollInterval") or 10),
                bool(values.get("webEnabled", True)),
                int(values.get("webPort") or 92),
                bool(web_security),
            )
            return {"ok": True}

        identity = str(request.get("id") or "")
        if action == "add":
            row = next(
                (
                    index
                    for index, episode in enumerate(self.episodes.records())
                    if episode["searchKey"] == identity
                ),
                -1,
            )
            if row < 0:
                raise ValueError("Episode is no longer available")
            self.renderEpisode(row, False)
            return {"ok": True}
        if action == "status":
            row = next(
                (
                    index
                    for index, episode in enumerate(self.episodes.records())
                    if episode["searchKey"] == identity
                ),
                -1,
            )
            if row < 0:
                raise ValueError("Episode is no longer available")
            status = str(request.get("value") or "")
            allowed = {
                choice.get("title") for choice in self.episodeStatusChoices(row)
            }
            if status not in allowed:
                raise ValueError("Unknown episode status")
            self.setEpisodeStatus(row, status)
            return {"ok": True}
        if action == "open-output":
            self.showQueueDestination(identity)
            return {"ok": True}
        if action == "open-log":
            path = self._detail(identity).get("logPath")
            if not path:
                raise ValueError("Render log is not available yet")
            self.openPath(path)
            return {"ok": True}

        commands = {
            "test": self.testQueue,
            "only": self.runOnly,
            "hold": self.holdQueue,
            "retry": self.retryQueue,
            "cancel": self.cancelQueue,
            "remove": self.removeEpisode,
            "include": self.toggleIncluded,
        }
        if action in commands:
            commands[action](identity)
        elif action in {"top", "up", "down", "bottom"}:
            delta = {"top": -1000000, "up": -1, "down": 1, "bottom": 1000000}
            self.moveQueue(identity, delta[action])
        elif action == "move-to":
            self.moveQueueTo(identity, str(request.get("target") or ""))
        elif action == "frames":
            if not self.setFrameSpec(identity, str(request.get("value") or "")):
                raise ValueError(self._error or "Cannot change frame selection")
        else:
            raise ValueError("Unknown batch action")
        return {"ok": True}

    @Slot("QVariantMap")
    def setWebTheme(self, values):
        self._web_theme = dict(values or {})

    @Slot()
    def openWeb(self):
        if self.webUrl:
            QDesktopServices.openUrl(QUrl(self.webUrl))

    @Slot()
    def copyWebUrl(self):
        if not self.webUrl:
            return
        QGuiApplication.clipboard().setText(self.webUrl)
        self._status = "LAN-ссылка скопирована"
        self.stateChanged.emit()

    def _restart_web_server(self):
        if self._web_server:
            self._web_server.stop()
            self._web_server = None
        self._web_error = ""
        if not self._config.get("web_enabled", True):
            self.webChanged.emit()
            return
        try:
            from thlib.environment import env_mode
            port = int(self._config.get("web_port", 92))
            self._web_server = BatchWebServer(
                self._web_dispatch,
                port=port,
                require_token=self._config.get("web_security", True),
                fonts_root=Path(env_mode.get_current_path()) / "thlib/ui/assets/fonts",
            )
            self._web_server.start()
        except OSError as error:
            self._web_server = None
            self._web_error = self._text("Web control could not start: %1").replace("%1", str(error))
        self.webChanged.emit()
