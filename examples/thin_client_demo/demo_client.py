from __future__ import annotations

import argparse
import json
import queue
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Property, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from handler_server.client import ThinClient
from handler_server.demo_maya_adapter import DemoMayaAdapter


class DemoClientController(QObject):
    stateChanged = Signal()
    _eventsReady = Signal()

    def __init__(self, client, adapter, registry, endpoint, events, parent=None):
        super().__init__(parent)
        self._client = client
        self._adapter = adapter
        self._registry = registry
        self._endpoint = endpoint
        self._events = events
        self._connected = client.connected
        self._scene_path = str(adapter.current_path)
        self._result = "Ready"
        self._show_request = ""
        self._eventsReady.connect(
            self._refresh, Qt.ConnectionType.QueuedConnection
        )
        self._refresh()

    def enqueue_event(self, event):
        self._events.put(event)
        self._eventsReady.emit()

    @Property(bool, notify=stateChanged)
    def connected(self):
        return self._connected

    @Property(str, constant=True)
    def clientId(self):
        return self._client.client_id

    @Property(str, constant=True)
    def endpoint(self):
        return self._endpoint

    @Property(str, notify=stateChanged)
    def currentScene(self):
        return str(self._adapter.current_path)

    @Property(str, notify=stateChanged)
    def resultText(self):
        return self._result

    @Property("QVariantList", constant=True)
    def scripts(self):
        return [
            {
                "title": "Inspect current scene",
                "description": "Returns the scene path and workspace.",
                "icon": "description",
                "action": "get_current_scene",
            },
            {
                "title": "Validate scene",
                "description": "Runs registered pre-save validation.",
                "icon": "fact_check",
                "action": "validate_scene",
            },
            {
                "title": "Prepare scene",
                "description": "Builds the normalized scene payload.",
                "icon": "build",
                "action": "prepare_scene",
            },
            {
                "title": "Save current scene",
                "description": "Runs the registered Maya-style save action.",
                "icon": "save",
                "action": "save_current_scene",
            },
            {
                "title": "Prepare scene check-in",
                "description": "Saves the scene and returns a simulated playblast.",
                "icon": "movie",
                "action": "prepare_checkin",
            },
        ]

    @Slot(str)
    def run_action(self, action):
        if action not in {record["action"] for record in self.scripts}:
            self._result = "Action is not available in this client"
            self.stateChanged.emit()
            return
        try:
            options = {"generate_previews": True} if action == "prepare_checkin" else {}
            result = self._registry.execute(action, options)
            self._result = json.dumps(result, ensure_ascii=False, indent=2)
            if self._client.connected:
                self._client.publish_event(action, "completed", result)
        except Exception as error:
            self._result = str(error)
            if self._client.connected:
                self._client.publish_event(
                    action, "error", {"message": str(error)}
                )
        self.stateChanged.emit()

    @Slot()
    def reconnect(self):
        if not self._client.connected:
            self._client.start()

    @Slot()
    def show_handler_window(self):
        if not self._client.connected:
            self._result = "Handler Server is not connected"
            self.stateChanged.emit()
            return
        try:
            self._show_request = self._client.send_command(
                "@tactic_handler", "show_handler_window", {}, timeout=5.0
            )
            self._result = "Requesting TACTIC Handler window..."
        except (ConnectionError, OSError) as error:
            self._result = str(error)
        self.stateChanged.emit()

    def _refresh(self):
        event_changed = False
        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            if event.get("type") != "command_activity":
                if (
                    self._show_request
                    and event.get("request_id") == self._show_request
                    and event.get("type") in {"result", "error"}
                ):
                    event_changed = True
                    if event.get("type") == "result" and event.get("success"):
                        self._result = "TACTIC Handler window restored"
                    else:
                        self._result = str(
                            event.get("message")
                            or "Could not restore TACTIC Handler"
                        )
                    self._show_request = ""
                continue
            event_changed = True
            action = str(event.get("action") or "command")
            status = str(event.get("status") or "unknown")
            data = event.get("payload") or {
                "message": str(event.get("message") or "")
            }
            self._result = (
                f"Remote command: {action}\nStatus: {status}\n"
                + json.dumps(data, ensure_ascii=False, indent=2)
            )
        connected = self._client.connected
        scene_path = str(self._adapter.current_path)
        if event_changed or connected != self._connected or scene_path != self._scene_path:
            self._connected = connected
            self._scene_path = scene_path
            self.stateChanged.emit()

    def shutdown(self):
        self._client.stop()


def main(argv=None):
    parser = argparse.ArgumentParser(description="TACTIC Handler demo Maya client")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--token")
    parser.add_argument("--client-id", default="")
    args = parser.parse_args(argv)

    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    app.setOrganizationName("TACTIC-Handler")
    adapter = DemoMayaAdapter()
    registry = adapter.registry()
    events = queue.Queue()
    if args.host is None and args.port is None and args.token is None:
        client = ThinClient.local(
            "maya", registry=registry, client_id=args.client_id,
            on_event=events.put,
        )
    else:
        if args.host is None or args.port is None or args.token is None:
            parser.error("manual connection requires --host, --port, and --token")
        client = ThinClient(
            args.host, args.port, args.token, "maya",
            registry=registry, client_id=args.client_id,
            on_event=events.put,
        )
    client.start()
    if not client.wait_connected(5.0):
        client.stop()
        raise SystemExit("Could not connect to Handler Server")
    controller = DemoClientController(
        client, adapter, registry, f"{client.host}:{client.port}", events,
        parent=app,
    )
    client.on_event = controller.enqueue_event
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("thinClientController", controller)
    qml_path = PROJECT_ROOT / "thlib" / "ui" / "qml" / "DemoThinClientWindow.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        controller.shutdown()
        raise SystemExit(f"Demo client UI failed to load: {qml_path}")
    app.aboutToQuit.connect(controller.shutdown)
    print(f"DEMO_CLIENT_READY {client.client_id}", flush=True)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
