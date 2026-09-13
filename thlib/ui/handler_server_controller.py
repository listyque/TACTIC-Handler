from __future__ import annotations

import json
import queue
import secrets
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    QObject, Property, QProcess, QProcessEnvironment, QTimer, Qt, Signal, Slot,
)

from handler_server.client import ThinClient
from handler_server.registry import CommandRegistry
from tactic_handler_dcc.connectors import dcc_focus_preference
from thlib.ui.tactic_rpc import HandlerApiService
from thlib.ui.workspace_models.records import RecordListModel


class HandlerServerController(QObject):
    stateChanged = Signal()
    commandFinished = Signal(str, bool, "QVariantMap", str)
    clientActionReported = Signal(str, str, str)
    showWindowRequested = Signal()
    _eventQueued = Signal()
    _SENSITIVE_LOG_KEYS = {
        "authorization", "cookie", "password", "passwd", "proxy_password",
        "secret", "session_token", "ticket", "token",
    }
    def __init__(
        self, root_path, debug_log, parent=None, *, dcc_preferences=None
    ):
        super().__init__(parent)
        self._root = Path(root_path)
        self._debug_log = debug_log
        self._dcc_preferences = dcc_preferences or (lambda _application: {})
        self.clients = RecordListModel((
            "clientId", "applicationType", "processId", "capabilities",
            "capabilityText", "applicationVersion", "sceneName", "selected",
        ))
        self.capabilities = RecordListModel(("name",))
        self.results = RecordListModel((
            "timestamp", "requestId", "target", "action", "status",
            "summary", "detail",
        ))
        self._server = QProcess(self)
        self._demo = QProcess(self)
        self._configure_process(self._server)
        self._configure_process(self._demo)
        self._server.readyReadStandardOutput.connect(self._read_server_output)
        self._server.finished.connect(self._server_finished)
        self._server.errorOccurred.connect(self._server_error)
        self._demo.readyReadStandardOutput.connect(self._read_demo_output)
        self._demo.finished.connect(self._demo_finished)
        self._demo.errorOccurred.connect(self._demo_error)
        self._token = ""
        self._host = "127.0.0.1"
        self._port = 0
        self._client = None
        self._events = queue.Queue()
        self._pending = {}
        self._selected_client = ""
        self._error = ""
        self._stopping = False
        self._server_buffer = ""
        self._demo_buffer = ""
        self._eventQueued.connect(
            self._drain_events, Qt.ConnectionType.QueuedConnection
        )
        self._startup_timer = QTimer(self)
        self._startup_timer.setSingleShot(True)
        self._startup_timer.setInterval(8000)
        self._startup_timer.timeout.connect(self._startup_failed)
        self._stop_timer = QTimer(self)
        self._stop_timer.setSingleShot(True)
        self._stop_timer.setInterval(2500)
        self._stop_timer.timeout.connect(self._force_stop_server)
        self._demo_stop_timer = QTimer(self)
        self._demo_stop_timer.setSingleShot(True)
        self._demo_stop_timer.setInterval(1500)
        self._demo_stop_timer.timeout.connect(self._force_stop_demo)
        self._last_connection_error = ""
        self._tactic_service = HandlerApiService(
            gui_dispatch=self._dispatch_gui
        )

    def attach_application(self, application, checkin_controller):
        self._tactic_service.attach_application(
            application, checkin_controller, self._request_show_window
        )

    def get_api(self):
        """Borrow the application-owned high-level API, including its live queue."""
        return self._tactic_service._public_api()

    def _dispatch_gui(self, callback, *args):
        request = {
            "type": "gui_api_call",
            "callback": callback,
            "args": args,
            "done": threading.Event(),
            "result": None,
            "error": None,
        }
        self._queue_event(request)
        if not request["done"].wait(30.0):
            raise TimeoutError("Application UI command timed out")
        if request["error"] is not None:
            raise request["error"]
        return request["result"]

    @staticmethod
    def _configure_process(process):
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

    def _queue_event(self, event):
        self._events.put(event)
        self._eventQueued.emit()

    @Property(str, notify=stateChanged)
    def state(self):
        if self._stopping:
            return "stopping"
        if self._client and self._client.connected:
            return "running"
        return {
            QProcess.ProcessState.NotRunning: "stopped",
            QProcess.ProcessState.Starting: "starting",
            QProcess.ProcessState.Running: "starting",
        }[self._server.state()]

    @Property(str, notify=stateChanged)
    def endpoint(self):
        return f"{self._host}:{self._port}" if self._port else "localhost"

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(str, notify=stateChanged)
    def selectedClient(self):
        return self._selected_client

    @Property(int, notify=stateChanged)
    def connectedClientCount(self):
        return len(self.clients._records)

    @Property(str, notify=stateChanged)
    def selectedApplicationType(self):
        record = self._selected_record()
        return str(record.get("applicationType") or "standalone")

    @Property(str, notify=stateChanged)
    def activeEnvironment(self):
        application_type = self.selectedApplicationType.lower()
        return application_type if application_type not in {"", "unknown"} else "standalone"

    @Property(str, notify=stateChanged)
    def selectedClientLabel(self):
        record = self._selected_record()
        if not record:
            return "Standalone"
        application_type = str(record.get("applicationType") or "DCC")
        version = str(record.get("applicationVersion") or "")
        parts = [f"{application_type.title()} {version}".strip()]
        if record.get("sceneName"):
            parts.append(str(record["sceneName"]))
        parts.append(f"PID {record.get('processId') or 0}")
        return " · ".join(parts)

    @Property("QVariantList", notify=stateChanged)
    def clientMenuActions(self):
        actions = [{"title": "DCC clients", "header": True}]
        if not self.clients._records:
            actions.append({
                "title": "No DCC clients connected", "icon": "link_off",
                "enabled": False, "status": self.endpoint,
            })
            return actions
        for record in self.clients._records:
            application_type = str(record.get("applicationType") or "DCC")
            version = str(record.get("applicationVersion") or "")
            status = []
            if record.get("sceneName"):
                status.append(str(record["sceneName"]))
            status.append(f"PID {record.get('processId') or 0}")
            actions.append({
                "title": f"{application_type.title()} {version}".strip(),
                "translate": False,
                "icon": "deployed_code",
                "command": f"dcc_client:{record.get('clientId') or ''}",
                "checked": record.get("clientId") == self._selected_client,
                "status": " · ".join(status),
                "statusTranslate": False,
            })
        return actions

    @Property(bool, notify=stateChanged)
    def demoRunning(self):
        return self._demo.state() != QProcess.ProcessState.NotRunning

    @Slot()
    def start_server(self):
        if self._server.state() != QProcess.ProcessState.NotRunning:
            return
        self._token = secrets.token_urlsafe(32)
        self._port = 0
        self._error = ""
        self._stopping = False
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("TACTIC_HANDLER_TOKEN", self._token)
        self._server.setProcessEnvironment(environment)
        self._server.setWorkingDirectory(str(self._root))
        self._server.setProgram(sys.executable)
        self._server.setArguments([
            "-m", "handler_server.launcher", "--host", self._host,
            "--port", "0",
        ])
        self._append_result("", "handler-server", "start", "starting",
                            "Starting local Handler Server", "")
        self._server.start()
        self._startup_timer.start()
        self.stateChanged.emit()

    @Slot()
    def stop_server(self):
        if self._stopping:
            return
        self._stopping = True
        self._startup_timer.stop()
        self.stop_demo()
        graceful_requested = False
        if self._client:
            try:
                self._client.shutdown_server()
                graceful_requested = True
            except (ConnectionError, OSError):
                pass
            self._client.stop(wait=False)
            self._client = None
        self._fail_pending_commands(
            "Handler Server stopped before the DCC command completed"
        )
        if self._server.state() != QProcess.ProcessState.NotRunning:
            if not graceful_requested:
                self._server.terminate()
            self._stop_timer.start()
        else:
            self._stopping = False
        self.clients.clear()
        self.capabilities.clear()
        self._selected_client = ""
        self.stateChanged.emit()

    @Slot()
    def start_demo(self):
        if self.state != "running" or self.demoRunning:
            return
        script = self._root / "examples" / "thin_client_demo" / "demo_client.py"
        environment = QProcessEnvironment.systemEnvironment()
        self._demo.setProcessEnvironment(environment)
        self._demo.setWorkingDirectory(str(self._root))
        self._demo.setProgram(sys.executable)
        self._demo.setArguments([
            str(script), "--client-id", "demo-maya"
        ])
        self._append_result(
            "", "demo-maya", "start", "starting",
            "Starting simulated Maya client", "",
        )
        self._demo.start()
        self.stateChanged.emit()

    @Slot()
    def stop_demo(self):
        if self._demo.state() != QProcess.ProcessState.NotRunning:
            self._append_result(
                "", "demo-maya", "stop", "info",
                "Stopping simulated Maya client", "",
            )
            self._demo.terminate()
            self._demo_stop_timer.start()
        self.stateChanged.emit()

    @Slot()
    def _force_stop_server(self):
        if self._server.state() != QProcess.ProcessState.NotRunning:
            self._append_result(
                "", "handler-server", "stop", "warning",
                "Handler Server did not stop gracefully; terminating process", "",
            )
            self._server.kill()

    @Slot()
    def _force_stop_demo(self):
        if self._demo.state() != QProcess.ProcessState.NotRunning:
            self._demo.kill()

    @Slot(int)
    def select_client(self, row):
        record = self.clients.get(row)
        client_id = str(record.get("clientId") or "")
        if not client_id:
            return
        self._selected_client = client_id
        self.clients.select_row(row)
        self.capabilities.replace([
            {"name": str(value)} for value in record.get("capabilities") or []
        ])
        self._append_result(
            "", client_id, "select", "info",
            f"Active DCC client: {client_id}",
            f"Application: {record.get('applicationType') or 'unknown'}\n"
            f"Capabilities: {record.get('capabilityText') or ''}",
        )
        self.stateChanged.emit()

    @Slot(str)
    def select_client_id(self, client_id):
        client_id = str(client_id or "")
        for row, record in enumerate(self.clients._records):
            if record.get("clientId") == client_id:
                self.select_client(row)
                return

    @Slot()
    def disconnect_selected(self):
        if self._client and self._selected_client:
            self._append_result(
                "", self._selected_client, "disconnect", "pending",
                "DCC client disconnect requested", "",
            )
            self._client.disconnect_client(self._selected_client)

    @Slot(str, str, float, result=str)
    def send_command(self, action, payload_text, timeout):
        action = str(action or "").strip()
        if not self._client or not self._client.connected:
            self._set_error("Handler Server is not connected")
            return ""
        if not self._selected_client:
            self._set_error("Select a target client")
            return ""
        if action not in {
            record.get("name") for record in self.capabilities._records
        }:
            self._set_error("The selected client does not register this action")
            return ""
        try:
            payload = json.loads(str(payload_text or "{}"))
        except json.JSONDecodeError as error:
            self._set_error(f"Invalid JSON payload: {error.msg}")
            return ""
        if not isinstance(payload, dict):
            self._set_error("Command payload must be a JSON object")
            return ""
        try:
            request_id = self._client.send_command(
                self._selected_client, action, payload,
                max(0.1, min(float(timeout), 300.0)),
            )
        except Exception as error:
            self._set_error(error)
            return ""
        self._pending[request_id] = {
            "target": self._selected_client, "action": action,
            "startedAt": time.monotonic(),
        }
        self._append_result(
            request_id, self._selected_client, action, "pending",
            "Command sent", self._payload_detail(payload),
        )
        self._error = ""
        self.stateChanged.emit()
        return request_id

    def send_dcc_action(self, action, path, options=None, timeout=60.0):
        action_map = {
            "open": "open_scene",
            "import": "import_file",
            "reference": "reference_file",
        }
        capability = action_map.get(action, str(action or ""))
        payload = dict(options or {})
        payload["path"] = str(path or "")
        return self.send_active_command(capability, payload, timeout)

    @Slot(str, "QVariantMap", float, result=str)
    def send_active_command(self, action, payload=None, timeout=60.0):
        return self.send_client_command(
            self._selected_client, action, payload, timeout
        )

    def send_client_command(
        self,
        client_id: str,
        action: str,
        payload: dict | None = None,
        timeout: float = 60.0,
    ) -> str:
        record = next((
            item for item in self.clients._records
            if item.get("clientId") == str(client_id or "")
        ), {})
        if not record or not self._client or not self._client.connected:
            self._set_error("The requested DCC client is not connected")
            return ""
        action = str(action or "")
        if action not in (record.get("capabilities") or []):
            self._set_error("The selected client does not register this action")
            return ""
        target = str(record.get("clientId") or "")
        command_payload = dict(payload or {})
        application_type = str(
            record.get("applicationType") or ""
        ).lower()
        focus_preference = dcc_focus_preference(application_type, action)
        if focus_preference:
            focus_application = bool(
                self._dcc_preferences(application_type).get(
                    focus_preference, True
                )
            )
            command_payload["focus_application"] = focus_application
            if focus_application:
                self._allow_client_foreground(record.get("processId"))
        try:
            if (
                action == "open_scene"
                and command_payload.get("focus_application")
                and "focus_application" in (record.get("capabilities") or [])
            ):
                self._client.send_command(
                    target, "focus_application", {}, 5.0
                )
                command_payload["focus_application"] = False
            request_id = self._client.send_command(
                target, action, command_payload,
                max(0.1, min(float(timeout), 300.0)),
            )
        except Exception as error:
            self._set_error(error)
            return ""
        self._pending[request_id] = {
            "target": target, "action": action,
            "startedAt": time.monotonic(),
        }
        self._append_result(
            request_id, target, action, "pending", "DCC command sent",
            self._payload_detail(command_payload),
        )
        self._error = ""
        self.stateChanged.emit()
        return request_id

    @staticmethod
    def _allow_client_foreground(process_id) -> None:
        if sys.platform != "win32":
            return
        try:
            import ctypes

            ctypes.windll.user32.AllowSetForegroundWindow(int(process_id))
        except (AttributeError, OSError, TypeError, ValueError):
            pass

    @Slot()
    def refresh_client_details(self):
        pending = {
            (str(item.get("target") or ""), str(item.get("action") or ""))
            for item in self._pending.values()
        }
        for record in self.clients._records:
            client_id = str(record.get("clientId") or "")
            capabilities = record.get("capabilities") or []
            actions = ["get_current_scene"]
            if not record.get("applicationVersion"):
                actions.insert(0, "get_application_info")
            for action in actions:
                if action in capabilities and (client_id, action) not in pending:
                    self.send_client_command(client_id, action, {}, 10.0)

    def has_dcc_capability(self, action):
        capability = {
            "open": "open_scene", "import": "import_file",
            "reference": "reference_file",
        }.get(action, action)
        record = self._selected_record()
        return bool(record and capability in (record.get("capabilities") or []))

    def _selected_record(self):
        return next((
            record for record in self.clients._records
            if record.get("clientId") == self._selected_client
        ), {})

    def cancel_request(self, request_id):
        if self._client and request_id:
            pending = self._pending.get(request_id, {})
            self._append_result(
                request_id, str(pending.get("target") or ""),
                str(pending.get("action") or "command"), "pending",
                "Command cancellation requested", "",
            )
            self._client.cancel(request_id)

    def _connect_operator(self):
        if self._client:
            self._client.stop(wait=False)
        registry = CommandRegistry()
        registry.register("show_handler_window", self._request_show_window)
        self._tactic_service.register(registry)
        self._client = ThinClient(
            self._host, self._port, self._token, "tactic_handler",
            registry=registry, client_id=f"tactic-handler-{id(self):x}",
            on_event=self._queue_event,
        )
        self._client.start()

    def _request_show_window(self, _payload):
        self._queue_event({"type": "show_handler_window"})
        return {"accepted": True}

    def _read_server_output(self):
        data = bytes(self._server.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        self._server_buffer += data
        lines = self._server_buffer.split("\n")
        self._server_buffer = lines.pop()
        for line in lines:
            line = line.strip()
            if line.startswith("HANDLER_SERVER_READY "):
                try:
                    ready = json.loads(line.split(" ", 1)[1])
                    self._host = str(ready["host"])
                    self._port = int(ready["port"])
                    self._append_result(
                        "", "handler-server", "ready", "info",
                        f"Handler Server ready at {self.endpoint}", "",
                    )
                    self._connect_operator()
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                    self._set_error(f"Invalid Handler Server startup response: {error}")
            elif line:
                self._append_result(
                    "", "handler-server", "log", "info", line, ""
                )

    def _read_demo_output(self):
        data = bytes(self._demo.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        self._demo_buffer += data
        lines = self._demo_buffer.split("\n")
        self._demo_buffer = lines.pop()
        for line in lines:
            if line.strip():
                self._append_result(
                    "", "demo-maya", "log", "info", line.strip(), ""
                )

    @Slot()
    def _drain_events(self):
        changed = False
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            changed = True
            event_type = event.get("type")
            if event_type == "capabilities":
                self._startup_timer.stop()
                self._last_connection_error = ""
                self._replace_clients(event.get("clients") or [])
            elif event_type in {"result", "error"}:
                self._handle_response(event)
            elif event_type == "client_event":
                self._handle_client_event(event)
            elif event_type == "show_handler_window":
                self.showWindowRequested.emit()
            elif event_type == "gui_api_call":
                try:
                    event["result"] = event["callback"](*event["args"])
                except Exception as error:
                    event["error"] = error
                finally:
                    event["done"].set()
            elif event_type == "client_disconnected":
                self._remove_client(str(event.get("client_id") or ""))
        if changed:
            self.stateChanged.emit()

    def _handle_client_event(self, event):
        client_id = str(event.get("client_id") or "DCC client")
        action = str(event.get("action") or "action")
        status = str(event.get("status") or "info")
        payload = dict(event.get("payload") or {})
        self._append_result(
            "", client_id, action, status,
            f"Action executed by {client_id}", self._payload_detail(payload),
        )
        kind = {
            "completed": "complete", "success": "complete",
            "failed": "error", "error": "error", "warning": "warning",
        }.get(status.casefold(), "info")
        detail = ""
        if action == "custom_script" and payload.get("path"):
            message = self.tr("Custom script completed")
            detail = self.tr("Script: %1").replace(
                "%1", str(payload["path"])
            )
            context = [
                self.tr("Project: %1").replace(
                    "%1", str(payload.get("project") or "—")
                ),
                self.tr("Client: %1").replace("%1", client_id),
            ]
            detail += "\n" + " · ".join(context)
        else:
            action_title = action.replace("_", " ").strip().title()
            message = f"{client_id}: {action_title} · {status.title()}"
        self.clientActionReported.emit(kind, message, detail)

    def _replace_clients(self, clients):
        records = []
        previous = {
            str(record.get("clientId") or ""): record
            for record in self.clients._records
        }
        own_id = self._client.client_id if self._client else ""
        for client in clients:
            client_id = str(client.get("client_id") or "")
            if not client_id or client_id == own_id:
                continue
            capabilities = [str(value) for value in client.get("capabilities") or []]
            records.append({
                "clientId": client_id,
                "applicationType": str(client.get("application_type") or "unknown"),
                "processId": int(client.get("process_id") or 0),
                "capabilities": capabilities,
                "capabilityText": ", ".join(capabilities),
                "applicationVersion": str(
                    previous.get(client_id, {}).get("applicationVersion") or ""
                ),
                "sceneName": str(
                    previous.get(client_id, {}).get("sceneName") or ""
                ),
                "selected": client_id == self._selected_client,
            })
        self.clients.replace(records)
        if self._selected_client and not any(
            record["clientId"] == self._selected_client for record in records
        ):
            self._selected_client = ""
            self.capabilities.clear()
        if not self._selected_client and records:
            self.select_client(0)

    def _remove_client(self, client_id):
        records = [
            record for record in self.clients._records
            if record.get("clientId") != client_id
        ]
        self._replace_clients([{
            "client_id": record["clientId"],
            "application_type": record["applicationType"],
            "process_id": record["processId"],
            "capabilities": record["capabilities"],
        } for record in records])

    def _handle_response(self, event):
        request_id = str(event.get("request_id") or "")
        if request_id and request_id not in self._pending:
            return
        pending = self._pending.pop(request_id, {})
        success = event.get("type") == "result" and bool(event.get("success"))
        cancelled = bool(event.get("cancelled"))
        payload = dict(event.get("payload") or {})
        if success:
            self._store_client_details(
                str(pending.get("target") or ""),
                str(pending.get("action") or ""),
                payload,
            )
        error = "" if success else str(
            event.get("message") or ("Cancelled" if cancelled else "Command failed")
        )
        if not request_id and error:
            if error == self._last_connection_error:
                return
            self._last_connection_error = error
            self._error = error
        status = "completed" if success else "cancelled" if cancelled else "error"
        detail = self._payload_detail(payload) if payload else error
        duration = max(
            0.0,
            time.monotonic() - float(pending.get("startedAt") or 0.0),
        ) if pending.get("startedAt") else 0.0
        self._append_result(
            request_id, str(pending.get("target") or event.get("sender") or ""),
            str(pending.get("action") or "command"), status,
            "Command completed" if success else error, detail, duration,
        )
        if event.get("type") == "error" and event.get("traceback"):
            self._debug_log.raise_error(
                RuntimeError(error), stacktrace=str(event["traceback"]),
                group="handler-server/command",
            )
        self.commandFinished.emit(request_id, success, payload, error)

    def _store_client_details(self, client_id, action, payload):
        record = next((
            item for item in self.clients._records
            if item.get("clientId") == client_id
        ), None)
        if record is None:
            return
        updated = dict(record)
        if action == "get_application_info":
            updated["applicationVersion"] = str(payload.get("version") or "")
        elif action == "get_current_scene":
            path = str(payload.get("path") or "")
            updated["sceneName"] = (
                path.replace("\\", "/").rsplit("/", 1)[-1]
                if path else "Untitled"
            )
        else:
            return
        self.clients.replace([
            updated if item is record else item
            for item in self.clients._records
        ])

    def _fail_pending_commands(self, error):
        error = str(error or "DCC command was interrupted")
        pending_commands = self._pending
        self._pending = {}
        for request_id, pending in pending_commands.items():
            started_at = float(pending.get("startedAt") or 0.0)
            duration = (
                max(0.0, time.monotonic() - started_at)
                if started_at else 0.0
            )
            self._append_result(
                request_id, str(pending.get("target") or ""),
                str(pending.get("action") or "command"), "error",
                error, error, duration,
            )
            self.commandFinished.emit(request_id, False, {}, error)

    def _append_result(
        self, request_id, target, action, status, summary, detail,
        duration=0.0,
    ):
        records = list(self.results._records)
        records.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "requestId": str(request_id or ""), "target": str(target or ""),
            "action": str(action or ""), "status": str(status or ""),
            "summary": str(summary or ""), "detail": str(detail or ""),
        })
        self.results.replace(records[-500:])
        self._write_debug_event(
            request_id, target, action, status, summary, detail, duration
        )

    @classmethod
    def _safe_log_value(cls, value, active=None):
        if active is None:
            active = set()
        if isinstance(value, dict):
            identity = id(value)
            if identity in active:
                return "<recursive reference>"
            active.add(identity)
            try:
                result = {}
                for key, item in value.items():
                    key_text = str(key)
                    normalized = key_text.lower().replace("-", "_")
                    sensitive = (
                        normalized in cls._SENSITIVE_LOG_KEYS
                        or any(
                            marker in normalized
                            for marker in (
                                "authorization", "cookie", "password",
                                "passwd", "secret", "ticket", "token",
                            )
                        )
                    )
                    result[key_text] = (
                        "<redacted>"
                        if sensitive
                        else cls._safe_log_value(item, active)
                    )
                return result
            finally:
                active.remove(identity)
        if isinstance(value, (list, tuple)):
            identity = id(value)
            if identity in active:
                return "<recursive reference>"
            active.add(identity)
            try:
                return [cls._safe_log_value(item, active) for item in value]
            finally:
                active.remove(identity)
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    @classmethod
    def _payload_detail(cls, payload):
        if not payload:
            return ""
        return json.dumps(
            cls._safe_log_value(payload), ensure_ascii=False, indent=2,
        )

    def _write_debug_event(
        self, request_id, target, action, status, summary, detail, duration,
    ):
        if not self._debug_log or not hasattr(self._debug_log, "log"):
            return
        level = {
            "error": "ERROR", "warning": "WARNING",
            "pending": "API", "starting": "INFO",
        }.get(str(status), "INFO")
        summary_lower = str(summary or "").lower()
        if action == "log" and " sender=" in summary_lower:
            group = "handler_server/transport"
        elif request_id:
            group = "handler_server/command"
        elif action in {"select", "disconnect"} or target == "demo-maya" or any(
            marker in summary_lower
            for marker in ("client connected:", "client disconnected:")
        ):
            group = "handler_server/client"
        else:
            group = "handler_server/lifecycle"
        if " warning " in summary_lower:
            level = "WARNING"
        elif " error " in summary_lower or " timeout " in summary_lower:
            level = "ERROR"
        command = " ".join(
            value for value in (
                f"target={target}" if target else "",
                f"action={action}" if action else "",
                f"request={request_id}" if request_id else "",
            ) if value
        )
        self._debug_log.log(
            level, str(summary or status), group=group,
            source="Handler Server", command=command,
            duration=float(duration or 0.0), details=str(detail or ""),
            caller=2,
        )

    def _server_finished(self, exit_code, _status):
        self._startup_timer.stop()
        self._stop_timer.stop()
        expected = self._stopping
        self._stopping = False
        if self._client:
            self._client.stop(wait=False)
            self._client = None
        failure = (
            f"Handler Server exited with code {exit_code}"
            if not expected and exit_code
            else "Handler Server stopped before the DCC command completed"
        )
        self._fail_pending_commands(failure)
        self.clients.clear()
        self.capabilities.clear()
        self._selected_client = ""
        if not expected and exit_code:
            self._set_error(failure)
        else:
            self._append_result(
                "", "handler-server", "stop", "completed",
                "Handler Server stopped", f"Exit code: {exit_code}",
            )
        self.stateChanged.emit()

    def _server_error(self, _error):
        self._set_error(self._server.errorString() or "Handler Server process failed")

    def _startup_failed(self):
        if self.state == "running":
            return
        self._set_error("Handler Server did not become ready within 8 seconds")
        self.stop_server()

    def _demo_finished(self, _exit_code, _status):
        self._demo_stop_timer.stop()
        self._append_result(
            "", "demo-maya", "stop", "completed",
            "Simulated Maya client stopped", f"Exit code: {_exit_code}",
        )
        self.stateChanged.emit()

    def _demo_error(self, _error):
        self._set_error(self._demo.errorString() or "Demo client process failed")

    def _set_error(self, value):
        self._error = str(value or "")
        if self._error:
            self._debug_log.raise_error(
                RuntimeError(self._error), stacktrace="",
                group="handler-server/controller",
            )
        self.stateChanged.emit()

    @Slot()
    def clear_results(self):
        self.results.clear()

    def shutdown(self):
        self._startup_timer.stop()
        self._tactic_service.close_api()
        self.stop_server()
        if self._server.state() != QProcess.ProcessState.NotRunning:
            if not self._server.waitForFinished(1500):
                self._server.kill()
                self._server.waitForFinished(1000)
        if self._demo.state() != QProcess.ProcessState.NotRunning:
            if not self._demo.waitForFinished(1000):
                self._demo.kill()
                self._demo.waitForFinished(500)
        self._stop_timer.stop()
        self._demo_stop_timer.stop()
