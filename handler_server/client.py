from __future__ import annotations

import os
import queue
import socket
import threading
import time
import traceback
import uuid

from .protocol import command, message, receive_message, send_message, structured_error
from .registry import CommandRegistry


class ThinClient:
    def __init__(
        self, host, port, token, application_type, registry=None,
        client_id="", reconnect=True, heartbeat_interval=3.0,
        dispatch=None, on_event=None, discover_local=False,
    ):
        self.host = str(host or "127.0.0.1")
        self.port = int(port)
        self.token = str(token or "")
        self.application_type = str(application_type or "unknown")
        self.client_id = str(client_id or f"{self.application_type}-{uuid.uuid4().hex[:10]}")
        self.registry = registry or CommandRegistry()
        self.reconnect = bool(reconnect)
        self.heartbeat_interval = max(1.0, float(heartbeat_interval))
        self.dispatch = dispatch or (lambda callback: callback())
        self.on_event = on_event or (lambda _event: None)
        self.discover_local = bool(discover_local)
        self._socket = None
        self._socket_lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._running = threading.Event()
        self._connected = threading.Event()
        self._thread = None
        self._command_thread = None
        self._command_queue = queue.Queue(maxsize=64)
        self._command_lock = threading.Lock()
        self._cancelled = set()
        self._response_lock = threading.Lock()
        self._response_waiters = {}
        self._last_connection_error = ""

    @classmethod
    def local(
        cls, application_type, registry=None, client_id="", reconnect=True,
        heartbeat_interval=3.0, dispatch=None, on_event=None,
    ):
        return cls(
            "127.0.0.1", 0, "", application_type,
            registry=registry, client_id=client_id,
            reconnect=reconnect, heartbeat_interval=heartbeat_interval,
            dispatch=dispatch, on_event=on_event,
            discover_local=True,
        )

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    def start(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        self._command_queue = queue.Queue(maxsize=64)
        self._thread = threading.Thread(
            target=self._connection_loop,
            name=f"thin-client-{self.client_id}",
            daemon=True,
        )
        self._command_thread = threading.Thread(
            target=self._command_loop,
            name=f"thin-commands-{self.client_id}",
            daemon=True,
        )
        self._command_thread.start()
        self._thread.start()

    def stop(self, wait=True) -> None:
        self.reconnect = False
        self._running.clear()
        self._connected.clear()
        self._close_socket()
        try:
            self._command_queue.put_nowait(None)
        except queue.Full:
            pass
        if wait and self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=2.0)
        if (
            wait
            and self._command_thread
            and self._command_thread is not threading.current_thread()
        ):
            self._command_thread.join(timeout=2.0)
        self._thread = None
        self._command_thread = None

    def wait_connected(self, timeout=5.0) -> bool:
        return self._connected.wait(timeout)

    def send_command(self, target_client, action, payload=None, timeout=30.0):
        payload = command(
            target_client, action, payload, timeout,
            sender=self.client_id,
        )
        self._send(payload)
        return payload["request_id"]

    def request(self, target_client, action, payload=None, timeout=30.0):
        command_payload = command(
            target_client, action, payload, timeout,
            sender=self.client_id,
        )
        response_queue = queue.Queue(maxsize=1)
        request_id = command_payload["request_id"]
        with self._response_lock:
            self._response_waiters[request_id] = response_queue
        try:
            self._send(command_payload)
            try:
                response = response_queue.get(timeout=float(timeout) + 1.0)
            except queue.Empty as error:
                self.cancel(request_id)
                raise TimeoutError(
                    f"Command timed out: {action}"
                ) from error
        finally:
            with self._response_lock:
                self._response_waiters.pop(request_id, None)
        if response.get("type") == "error":
            error = RuntimeError(response.get("message") or "Remote command failed")
            error.remote_traceback = str(response.get("traceback") or "")
            error.remote_code = str(response.get("code") or "command_error")
            raise error
        if response.get("cancelled"):
            raise RuntimeError("Remote command was cancelled")
        if not response.get("success", False):
            raise RuntimeError(
                response.get("message") or "Remote command failed"
            )
        return dict(response.get("payload") or {})

    def cancel(self, current_request_id):
        self._send(message(
            "cancel", request_id=str(current_request_id or ""),
            sender=self.client_id,
        ))

    def disconnect_client(self, target_client):
        self._send(message(
            "client_disconnected", client_id=str(target_client or ""),
            request_id=uuid.uuid4().hex, reason="operator_request",
        ))

    def shutdown_server(self):
        self._send(message(
            "server_shutdown", sender=self.client_id,
            request_id=uuid.uuid4().hex,
        ))

    def publish_event(self, action, status, payload=None):
        self._send(message(
            "client_event",
            client_id=self.client_id,
            action=str(action or ""),
            status=str(status or "info"),
            payload=dict(payload or {}),
        ))

    def refresh_capabilities(self):
        self._send(message(
            "capabilities",
            client_id=self.client_id,
            capabilities=self.registry.capabilities(),
        ))

    def _connection_loop(self):
        delay = 0.25
        while self._running.is_set():
            try:
                self._serve_connection()
                delay = 0.25
            except Exception as error:
                error_text = str(error)
                if (
                    self._running.is_set()
                    and error_text != self._last_connection_error
                ):
                    self._last_connection_error = error_text
                    self.on_event({
                        "type": "error", "protocol_version": 1,
                        "request_id": "", "code": "connection_error",
                        "message": str(error),
                        "traceback": traceback.format_exc(),
                        "sender": self.client_id,
                    })
            finally:
                was_connected = self._connected.is_set()
                self._connected.clear()
                self._close_socket()
                if was_connected:
                    self.on_event(message(
                        "client_disconnected", client_id=self.client_id,
                        reason="connection_lost",
                    ))
            if not self._running.is_set() or not self.reconnect:
                break
            time.sleep(delay)
            delay = min(delay * 2.0, 5.0)

    def _serve_connection(self):
        if self.discover_local:
            from .discovery import current_session

            session = current_session()
            if not session:
                raise ConnectionError(
                    "No local TACTIC Handler Server session was found"
                )
            self.host = session["host"]
            self.port = session["port"]
            self.token = session["token"]
        sock = socket.create_connection((self.host, self.port), timeout=5.0)
        sock.settimeout(5.0)
        with self._socket_lock:
            if not self._running.is_set():
                sock.close()
                return
            self._socket = sock
        send_message(sock, message(
            "hello", session_token=self.token,
            client_id=self.client_id,
        ))
        hello = receive_message(sock)
        if hello["type"] == "error" or not hello.get("accepted"):
            raise PermissionError(hello.get("message") or "Handshake rejected")
        send_message(sock, message(
            "register_client",
            client_id=self.client_id,
            application_type=self.application_type,
            process_id=os.getpid(),
            capabilities=self.registry.capabilities(),
        ))
        registration = receive_message(sock)
        if registration["type"] != "capabilities":
            raise ConnectionError("Client registration was not acknowledged")
        self._connected.set()
        self._last_connection_error = ""
        self.on_event(registration)
        sock.settimeout(1.0)
        last_heartbeat = 0.0
        while self._running.is_set():
            now = time.monotonic()
            if now - last_heartbeat >= self.heartbeat_interval:
                self._send(message("heartbeat", timestamp=time.time()))
                last_heartbeat = now
            try:
                payload = receive_message(sock)
            except socket.timeout:
                continue
            self._handle(payload)

    def _handle(self, payload):
        message_type = payload["type"]
        if message_type == "command":
            try:
                self._command_queue.put_nowait(payload)
            except queue.Full:
                self._send_response(structured_error(
                    str(payload.get("request_id") or ""),
                    "client_busy",
                    "The DCC command queue is full",
                    sender=self.client_id,
                ))
        elif message_type == "cancel":
            with self._command_lock:
                self._cancelled.add(str(payload.get("request_id") or ""))
        else:
            if message_type in {"result", "error"}:
                request_id = str(payload.get("request_id") or "")
                with self._response_lock:
                    waiter = self._response_waiters.get(request_id)
                if waiter:
                    try:
                        waiter.put_nowait(payload)
                    except queue.Full:
                        pass
            self.on_event(payload)

    def _command_loop(self):
        while self._running.is_set():
            try:
                payload = self._command_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if payload is None:
                break
            self._execute_command(payload)

    def _execute_command(self, payload):
        request_id = str(payload["request_id"])
        with self._command_lock:
            cancelled = request_id in self._cancelled
            self._cancelled.discard(request_id)
        if cancelled:
            self._send_response(message(
                "result", request_id=request_id, success=False,
                cancelled=True, payload={}, sender=self.client_id,
            ))
            return
        try:
            self.on_event({
                "type": "command_activity",
                "request_id": request_id,
                "action": str(payload["action"]),
                "status": "running",
                "payload": dict(payload.get("payload") or {}),
            })
            result = self.dispatch(
                lambda: self.registry.execute(payload["action"], payload["payload"])
            )
            safe_result = self._safe_result(result)
            with self._command_lock:
                cancelled = request_id in self._cancelled
                self._cancelled.discard(request_id)
            cancelled = cancelled or bool(safe_result.get("cancelled", False))
            success = not cancelled and bool(safe_result.get("success", True))
            self._send_response(message(
                "result", request_id=request_id,
                success=success, cancelled=cancelled, payload=safe_result,
                sender=self.client_id,
            ))
            self.on_event({
                "type": "command_activity",
                "request_id": request_id,
                "action": str(payload["action"]),
                "status": (
                    "cancelled" if cancelled else "completed" if success else "error"
                ),
                "payload": safe_result,
            })
        except Exception as error:
            traceback_text = traceback.format_exc()
            self._send_response(structured_error(
                request_id, "action_failed", str(error), traceback_text,
                sender=self.client_id,
            ))
            self.on_event({
                "type": "command_activity",
                "request_id": request_id,
                "action": str(payload["action"]),
                "status": "error",
                "message": str(error),
                "traceback": traceback_text,
                "payload": {},
            })

    def _send_response(self, payload):
        try:
            self._send(payload)
        except (ConnectionError, OSError):
            return

    @staticmethod
    def _safe_result(result):
        if result is None:
            return {}
        if isinstance(result, dict):
            return result
        return {"value": result}

    def _send(self, payload):
        sock = self._socket
        if not sock or not self._connected.is_set():
            raise ConnectionError("Thin client is not connected")
        with self._send_lock:
            send_message(sock, payload)

    def _close_socket(self):
        with self._socket_lock:
            sock, self._socket = self._socket, None
        if not sock:
            return
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass
