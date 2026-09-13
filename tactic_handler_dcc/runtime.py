from __future__ import annotations

import importlib
import importlib.util
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from handler_server.client import ThinClient
from handler_server.discovery import current_session as discovered_session
from handler_server.registry import CommandRegistry

import tactic_handler_api
from tactic_handler_api.operations import allow_blocking_calls
from .connectors import dcc_manifest


_API_MODULES = (
    "errors", "identity", "operations", "objects", "api", "contract",
    "wire", "remote",
)


class ScriptJob:
    """Non-blocking custom-script execution started from a DCC."""

    def __init__(self, application_title: str = "DCC") -> None:
        self._application_title = str(application_title or "DCC")
        self._done = threading.Event()
        self.result = None
        self.error = None

    @property
    def done(self) -> bool:
        return self._done.is_set()

    def wait(self, timeout=None):
        if not self._done.wait(timeout):
            raise TimeoutError(
                f"The {self._application_title} custom script is still running"
            )
        if self.error is not None:
            raise self.error
        return self.result


class DccRuntime:
    """Own one thin-client connection for a DCC process."""

    def __init__(
        self,
        handler_path,
        *,
        application_type: str,
        application_title: str,
        connector,
        python_executable=None,
        client_id="",
        startup_timeout=45.0,
        client_factory=None,
        session_finder=None,
        handler_launcher=None,
        notifier=None,
        register_exit=True,
    ) -> None:
        self.handler_path = self._handler_root(handler_path)
        self.application_type = str(application_type or "").strip().lower()
        if not self.application_type:
            raise ValueError("A DCC application type is required")
        self.application_title = str(
            application_title or self.application_type.title()
        )
        self.python_executable = str(python_executable or "")
        self.client_id = str(
            client_id or f"{self.application_type}-{os.getpid()}"
        )
        self.startup_timeout = max(5.0, float(startup_timeout))
        self.connector = connector
        self._client_factory = client_factory or ThinClient.local
        self._session_finder = session_finder or discovered_session
        self._handler_launcher = handler_launcher or self._launch_handler
        self._notifier = notifier or self._console_notification
        self._register_exit_enabled = bool(register_exit)
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._bootstrap_thread = None
        self._remove_exit_callback = None
        self._client = None
        self._api = None
        self._state = "stopped"
        self._message = ""
        self._launched_process_id = 0
        self._connected_announced = False

    @property
    def client(self):
        return self._client

    @property
    def connected(self) -> bool:
        return bool(self._client and self._client.connected)

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    @property
    def status(self) -> dict:
        with self._lock:
            return {
                "state": self._state,
                "message": self._message,
                "connected": self.connected,
                "client_id": self.client_id,
                "handler_path": str(self.handler_path),
                "launched_process_id": self._launched_process_id,
            }

    def start(self):
        with self._lock:
            if self._state not in {"stopped", "failed"}:
                return self
            self._stop_event.clear()
            self._ready_event.clear()
            self._connected_announced = False
            registry = self.connector.register(CommandRegistry())
            self._client = self._client_factory(
                self.application_type,
                registry=registry,
                client_id=self.client_id,
                dispatch=self.connector.dispatch,
                on_event=self._on_client_event,
            )
            self._api = tactic_handler_api.from_client(self._client)
            self._client.start()
            tactic_handler_api._bind_current(self._api)
            self._set_state(
                "connecting",
                f"Connecting {self.application_title} to TACTIC Handler",
            )
            if self._register_exit_enabled:
                self._install_exit_callback()
        return self.reconnect()

    def reconnect(self):
        with self._lock:
            thread = self._bootstrap_thread
            if self.connected or (thread and thread.is_alive()):
                return self
            self._stop_event.clear()
            self._ready_event.clear()
            self._connected_announced = False
            self._set_state(
                "connecting",
                f"Connecting {self.application_title} to TACTIC Handler",
            )
            self._bootstrap_thread = threading.Thread(
                target=self._bootstrap,
                name=(
                    f"tactic-handler-{self.application_type}-startup-"
                    f"{os.getpid()}"
                ),
                daemon=True,
            )
            self._bootstrap_thread.start()
        self._notify(
            f"Connecting {self.application_title} to TACTIC Handler…", "info"
        )
        return self

    def replace_connector(self, connector) -> None:
        """Hot-reload native actions without reconnecting the DCC client."""
        self.connector = connector
        client = self.client
        if client is None:
            return
        client.registry = connector.register(CommandRegistry())
        client.dispatch = connector.dispatch
        if self._api is not None:
            self._api.close(wait=False)
        self._api = tactic_handler_api.from_client(client)
        tactic_handler_api._bind_current(self._api)
        if self.connected:
            client.refresh_capabilities()

    def stop(self) -> None:
        with self._lock:
            if self._state == "stopped" and self._client is None:
                return
            self._stop_event.set()
            client, self._client = self._client, None
            api, self._api = self._api, None
            remove_callback, self._remove_exit_callback = (
                self._remove_exit_callback,
                None,
            )
            self._ready_event.clear()
            self._set_state(
                "stopped", f"{self.application_title} connector stopped"
            )
        if api is not None:
            tactic_handler_api._unbind_current(api)
        if remove_callback:
            try:
                remove_callback()
            except Exception:
                pass
        if client:
            try:
                if client.connected:
                    client.publish_event(
                        f"{self.application_type}_connector",
                        "stopped",
                        {"process_id": os.getpid()},
                    )
            except (ConnectionError, OSError):
                pass

            def disconnect():
                try:
                    if api is not None:
                        api.close(wait=True)
                finally:
                    client.stop(wait=False)

            # Drain submitted domain operations before closing their transport;
            # a DCC UI thread must never wait for uploads or remote responses.
            threading.Thread(
                target=disconnect,
                name=f"handler-{self.application_type}-stop",
                daemon=True,
            ).start()

    def wait_until_connected(self, timeout=None) -> bool:
        timeout = self.startup_timeout if timeout is None else float(timeout)
        return self._ready_event.wait(timeout) and self.connected

    def show_handler(self):
        return self._request_async("show_handler_window", {})

    def execute_custom_script(
        self,
        script_path,
        *,
        project=None,
        kwargs=None,
        refresh_scripts=False,
    ) -> ScriptJob:
        job = ScriptJob(self.application_title)
        threading.Thread(
            target=self._run_custom_script,
            args=(job, script_path, project, kwargs, refresh_scripts),
            name=(
                f"tactic-handler-{self.application_type}-script-"
                f"{uuid.uuid4().hex[:8]}"
            ),
            daemon=True,
        ).start()
        return job

    def _bootstrap(self) -> None:
        try:
            if not self._session_finder():
                self._set_state("starting_handler", "Starting TACTIC Handler")
                self._notify(
                    "TACTIC Handler was not found. Starting it now…", "info"
                )
                process = self._handler_launcher(
                    self.handler_path, self.python_executable
                )
                self._launched_process_id = int(
                    getattr(process, "pid", process or 0) or 0
                )
            deadline = time.monotonic() + self.startup_timeout
            while not self._stop_event.is_set() and time.monotonic() < deadline:
                client = self._client
                if client and client.wait_connected(0.2):
                    self._announce_connected()
                    return
            if self._stop_event.is_set():
                return
            raise ConnectionError(
                "TACTIC Handler did not become available within "
                f"{self.startup_timeout:.0f} seconds"
            )
        except Exception as error:
            self._set_state("failed", str(error))
            self._notify(
                f"{self.application_title} connector: {error}", "error"
            )
            client = self._client
            if client:
                try:
                    client.stop(wait=False)
                except TypeError:
                    client.stop()

    def _announce_connected(self) -> None:
        with self._lock:
            if self._connected_announced or self._stop_event.is_set():
                return
            self._connected_announced = True
            self._ready_event.set()
            message = (
                f"{self.application_title} is connected to TACTIC Handler"
            )
            self._set_state("connected", message)
        self._notify(message, "success")
        client = self._client
        if not client:
            return
        try:
            client.publish_event(
                f"{self.application_type}_connector",
                "connected",
                {"process_id": os.getpid()},
            )
            threading.Thread(
                target=self._show_after_connection,
                name=(
                    f"tactic-handler-{self.application_type}-show-window"
                ),
                daemon=True,
            ).start()
        except Exception as error:
            self._notify(
                "Connected, but the Handler window did not open: "
                f"{error}",
                "warning",
            )

    def _show_after_connection(self) -> None:
        deadline = time.monotonic() + 15.0
        last_error = None
        while not self._stop_event.is_set() and time.monotonic() < deadline:
            client = self._client
            if not client or not client.connected:
                return
            try:
                client.request(
                    "@tactic_handler", "show_handler_window", {}, timeout=3.0
                )
                return
            except Exception as error:
                last_error = error
                self._stop_event.wait(0.25)
        if last_error is not None and not self._stop_event.is_set():
            self._notify(
                "Connected, but the Handler window did not open: "
                f"{last_error}",
                "warning",
            )

    def _on_client_event(self, event) -> None:
        event_type = str((event or {}).get("type") or "")
        if event_type == "capabilities":
            self._announce_connected()
        elif event_type == "client_disconnected" and not self._stop_event.is_set():
            with self._lock:
                self._connected_announced = False
                self._ready_event.clear()
                self._set_state(
                    "reconnecting", "TACTIC Handler connection was lost"
                )
            self._notify(
                "TACTIC Handler connection was lost. Reconnecting…",
                "warning",
            )

    def _request_async(self, action, payload):
        def request():
            try:
                if not self.wait_until_connected(self.startup_timeout):
                    raise ConnectionError("TACTIC Handler is not connected")
                return self._client.request(
                    "@tactic_handler",
                    action,
                    dict(payload or {}),
                    timeout=30.0,
                )
            except Exception as error:
                self._notify(f"TACTIC Handler: {error}", "error")
                return None

        thread = threading.Thread(target=request, daemon=True)
        thread.start()
        return thread

    def _run_custom_script(
        self, job, script_path, project, kwargs, refresh_scripts
    ) -> None:
        try:
            if not self.wait_until_connected(self.startup_timeout):
                raise ConnectionError("TACTIC Handler is not connected")
            project_code = str(project or "")
            relative = str(script_path or "").strip().replace("\\", "/").strip("/")
            if not relative or ".." in Path(relative).parts:
                raise ValueError("A safe custom script path is required")
            root = self.handler_path / "custom_scripts"
            script = (
                root / project_code / f"{relative}.py"
                if project_code
                else root / f"{relative}.py"
            )
            if refresh_scripts or not script.is_file():
                if not project_code:
                    raise ValueError(
                        "A project code is required to download scripts"
                    )
                self._api.project(project_code).download_scripts()
            script = script.resolve()
            if not script.is_relative_to(root.resolve()) or not script.is_file():
                raise FileNotFoundError(
                    f"Custom script was not found: {script}"
                )
            self._notify(
                f"Running {self.application_title} script: {relative}", "info"
            )
            job.result = self.connector.dispatch(
                lambda: self._load_script(
                    script, kwargs or {}, project=project_code
                )
            )
            self._notify(
                f"{self.application_title} script completed: {relative}",
                "success",
            )
            if self._client and self._client.connected:
                self._client.publish_event(
                    "custom_script",
                    "completed",
                    {"path": relative, "project": project_code},
                )
        except Exception as error:
            job.error = error
            self._notify(
                f"{self.application_title} script failed: {error}", "error"
            )
        finally:
            job._done.set()

    @staticmethod
    def _load_script(path, kwargs, *, project=""):
        module_name = f"_tactic_handler_custom_{uuid.uuid4().hex}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if not spec or not spec.loader:
            raise ImportError(f"Unable to load custom script: {path}")
        module = importlib.util.module_from_spec(spec)
        module.TACTIC_SCRIPT_KWARGS = dict(kwargs or {})
        module.TACTIC_PROJECT_CODE = project
        sys.modules[module_name] = module
        try:
            # Saved DCC scripts are explicit user actions and historically run
            # synchronously. Keep blocking data access scoped to that action.
            with allow_blocking_calls():
                spec.loader.exec_module(module)
                return getattr(module, "RESULT", None)
        finally:
            sys.modules.pop(module_name, None)

    def _install_exit_callback(self) -> None:
        install = getattr(self.connector, "install_exit_callback", None)
        if not callable(install):
            return
        try:
            self._remove_exit_callback = install(self.stop)
        except Exception:
            self._remove_exit_callback = None

    def _set_state(self, state, message) -> None:
        self._state = str(state)
        self._message = str(message)

    def _notify(self, message, level) -> None:
        try:
            self._notifier(str(message), str(level))
        except Exception:
            pass

    @staticmethod
    def _handler_root(path) -> Path:
        root = Path(str(path or "")).expanduser().resolve()
        if not (root / "launch.pyw").is_file():
            raise FileNotFoundError(f"TACTIC Handler was not found in {root}")
        return root

    @staticmethod
    def _console_notification(message, level="info") -> None:
        sys.stdout.write(f"TACTIC Handler [{level}]: {message}\n")

    @staticmethod
    def _launch_handler(root, python_executable=""):
        executable = DccRuntime._python_executable(root, python_executable)
        entry = root / "launch.pyw"
        if executable:
            flags = 0
            if os.name == "nt":
                flags = (
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    | subprocess.DETACHED_PROCESS
                )
            return subprocess.Popen(
                [executable, str(entry)],
                cwd=str(root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=flags,
            )
        if os.name == "nt" and hasattr(os, "startfile"):
            os.startfile(str(entry))
            return 0
        raise FileNotFoundError(
            "Python for standalone TACTIC Handler was not found. Set "
            "TACTIC_HANDLER_PYTHON or pass python_executable to startup()."
        )

    @staticmethod
    def _python_executable(root, explicit="") -> str:
        candidates = [
            explicit,
            os.environ.get("TACTIC_HANDLER_PYTHON", ""),
            root / ".venv" / "Scripts" / "pythonw.exe",
            root / ".venv" / "Scripts" / "python.exe",
            root / "venv" / "Scripts" / "pythonw.exe",
            root / "venv" / "Scripts" / "python.exe",
        ]
        current = Path(sys.executable)
        if current.name.lower() in {"python.exe", "pythonw.exe", "python"}:
            candidates.append(current)
        candidates.extend(
            shutil.which(name) or ""
            for name in ("pythonw.exe", "pyw.exe", "python.exe", "python3")
        )
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return str(Path(candidate).resolve())
        return ""


class DccEntrypoint:
    """Reusable module lifecycle for one import-safe DCC connector."""

    def __init__(
        self,
        connector_module: str,
        connector_type: str,
        runtime_type=DccRuntime,
    ) -> None:
        self.connector_module = str(connector_module)
        self.connector_type_name = str(connector_type)
        self.runtime_type = runtime_type
        self._runtime = None
        self._lock = threading.RLock()
        self.connector_type = None
        self.application_type = ""
        self.application_title = "DCC"
        self._load_connector()

    def configure(self, runtime_type) -> None:
        self.runtime_type = runtime_type

    @property
    def current(self):
        return self._runtime

    def startup(self, handler_path, **kwargs):
        with self._lock:
            previous = self._runtime
            connector = kwargs.get("connector")
            if connector is None:
                connector = self._reload_connector(
                    previous.handler_path if self._active(previous)
                    else handler_path
                )
                kwargs["connector"] = connector
                if self._active(previous):
                    DccRuntime.replace_connector(previous, connector)
            if self._active(previous):
                if previous.connected:
                    previous.show_handler()
                else:
                    self.runtime_type.reconnect(previous)
                return previous
            if previous:
                previous.stop()
            self._runtime = self.runtime_type(
                handler_path,
                application_type=self.application_type,
                application_title=self.application_title,
                **kwargs,
            ).start()
            return self._runtime

    def stop(self) -> None:
        with self._lock:
            runtime, self._runtime = self._runtime, None
        if runtime:
            runtime.stop()

    def status(self) -> dict:
        if self._runtime:
            return self._runtime.status
        return {
            "state": "stopped",
            "message": f"{self.application_title} connector is not running",
            "connected": False,
        }

    def show_handler(self):
        if not self._runtime:
            raise RuntimeError("Call the DCC startup() function first")
        return self._runtime.show_handler()

    def execute_custom_script(
        self, script_path, project=None, kwargs=None, refresh_scripts=False
    ) -> ScriptJob:
        if not self._runtime:
            raise RuntimeError("Call the DCC startup() function first")
        return self._runtime.execute_custom_script(
            script_path,
            project=project,
            kwargs=kwargs,
            refresh_scripts=refresh_scripts,
        )

    def connector(self):
        if self._runtime:
            return self._runtime.connector
        if self.connector_type is None:
            self._load_connector()
        return self.connector_type.instance()

    def _reload_connector(self, handler_path):
        for module_name in _API_MODULES:
            importlib.reload(
                importlib.import_module(f"tactic_handler_api.{module_name}")
            )
        importlib.reload(tactic_handler_api)
        module = importlib.reload(self._load_connector())
        self._read_manifest(module)
        self.connector_type = getattr(module, self.connector_type_name)
        return self.connector_type.instance(handler_path)

    def _load_connector(self):
        module = importlib.import_module(self.connector_module)
        self._read_manifest(module)
        self.connector_type = getattr(module, self.connector_type_name)
        return module

    def _read_manifest(self, module) -> None:
        manifest = dcc_manifest(module)
        self.application_type = manifest["application"]
        self.application_title = manifest["title"]

    @staticmethod
    def _active(runtime) -> bool:
        return bool(runtime and runtime.state not in {"stopped", "failed"})


__all__ = ["DccEntrypoint", "DccRuntime", "ScriptJob"]
