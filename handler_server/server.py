from __future__ import annotations

import hmac
import logging
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field

from .protocol import (
    PROTOCOL_VERSION,
    ProtocolError,
    message,
    receive_message,
    send_message,
    structured_error,
)
from .router import RequestRouter


@dataclass
class ClientConnection:
    client_id: str
    application_type: str
    process_id: int
    capabilities: list[str]
    socket: socket.socket
    address: tuple
    send_lock: threading.Lock = field(default_factory=threading.Lock)
    last_heartbeat: float = field(default_factory=time.monotonic)

    def send(self, payload: dict) -> None:
        with self.send_lock:
            send_message(self.socket, payload)

    def public_record(self) -> dict:
        return {
            "client_id": self.client_id,
            "application_type": self.application_type,
            "process_id": self.process_id,
            "capabilities": list(self.capabilities),
        }


class HandlerServer:
    def __init__(self, host="127.0.0.1", port=0, token="",
                 heartbeat_timeout=12.0, logger=None):
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Handler Server listens on localhost only")
        self.host = "127.0.0.1" if host == "localhost" else host
        self.port = int(port)
        self.token = str(token or uuid.uuid4().hex + uuid.uuid4().hex)
        self.heartbeat_timeout = max(5.0, float(heartbeat_timeout))
        self.logger = logger or logging.getLogger("handler_server")
        self._listener = None
        self._clients: dict[str, ClientConnection] = {}
        self._lock = threading.RLock()
        self._running = threading.Event()
        self.shutdown_requested = threading.Event()
        self._threads = set()
        self.router = RequestRouter(self._send_to, self._log_command)

    @property
    def clients(self) -> list[dict]:
        with self._lock:
            return [client.public_record() for client in self._clients.values()]

    def start(self) -> int:
        if self._running.is_set():
            return self.port
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self.port))
        listener.listen(32)
        listener.settimeout(0.5)
        self._listener = listener
        self.port = int(listener.getsockname()[1])
        self._running.set()
        self._spawn(self._accept_loop, "handler-accept")
        self._spawn(self._monitor_loop, "handler-monitor")
        return self.port

    def stop(self) -> None:
        self._running.clear()
        if self._listener:
            try:
                self._listener.close()
            except OSError:
                pass
            self._listener = None
        with self._lock:
            clients = list(self._clients.values())
            self._clients.clear()
        for client in clients:
            self._close_socket(client.socket)
        with self._lock:
            threads = list(self._threads)
        deadline = time.monotonic() + 2.0
        for thread in threads:
            if thread is not threading.current_thread():
                thread.join(timeout=max(0.0, deadline - time.monotonic()))
        with self._lock:
            self._threads = {
                thread for thread in self._threads if thread.is_alive()
            }

    def _spawn(self, callback, name):
        def run():
            try:
                callback()
            finally:
                with self._lock:
                    self._threads.discard(threading.current_thread())

        thread = threading.Thread(target=run, name=name, daemon=True)
        with self._lock:
            self._threads.add(thread)
        thread.start()

    def _accept_loop(self):
        while self._running.is_set():
            try:
                sock, address = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            sock.settimeout(5.0)
            self._spawn(
                lambda current=sock, peer=address: self._client_loop(current, peer),
                "handler-client",
            )

    def _client_loop(self, sock, address):
        client_id = ""
        try:
            hello = receive_message(sock)
            if hello["type"] != "hello":
                raise ProtocolError("First message must be hello")
            supplied = str(hello.get("session_token") or "")
            if not hmac.compare_digest(supplied, self.token):
                send_message(sock, structured_error(
                    "", "authentication_failed", "Invalid session token"
                ))
                return
            send_message(sock, message("hello", accepted=True))
            registration = receive_message(sock)
            if registration["type"] != "register_client":
                raise ProtocolError("Second message must register the client")
            client_id = str(registration.get("client_id") or uuid.uuid4().hex)
            application_type = str(
                registration.get("application_type") or "unknown"
            )
            capabilities = sorted({
                str(value) for value in registration.get("capabilities") or []
                if str(value)
            })
            client = ClientConnection(
                client_id, application_type,
                int(registration.get("process_id") or 0), capabilities,
                sock, address,
            )
            self._register(client)
            sock.settimeout(1.0)
            client.send(message(
                "capabilities", client_id=client_id,
                capabilities=capabilities, clients=self.clients,
            ))
            self._broadcast_capabilities()
            while self._running.is_set():
                try:
                    payload = receive_message(sock)
                except socket.timeout:
                    continue
                self._handle(client, payload)
        except (ConnectionError, OSError):
            pass
        except Exception as error:
            self.logger.warning("Client protocol error: %s", error)
            try:
                send_message(sock, structured_error(
                    "", "protocol_error", str(error)
                ))
            except OSError:
                pass
        finally:
            if client_id:
                self._remove(client_id, "connection_closed", sock)
            else:
                self._close_socket(sock)

    def _handle(self, client, payload):
        message_type = payload["type"]
        client.last_heartbeat = time.monotonic()
        if message_type == "heartbeat":
            client.send(message("heartbeat", timestamp=time.time()))
        elif message_type == "capabilities":
            capabilities = sorted({
                str(value) for value in payload.get("capabilities") or []
                if str(value)
            })
            with self._lock:
                client.capabilities = capabilities
            self._broadcast_capabilities()
            self.logger.info(
                "Client capabilities updated: %s", client.client_id
            )
        elif message_type == "command":
            payload = self._normalize_command(payload)
            payload = self._resolve_target(payload)
            self.router.route_command(client.client_id, payload)
        elif message_type in {"result", "error"}:
            self.router.route_response(client.client_id, payload)
        elif message_type == "cancel":
            self.router.route_cancel(
                client.client_id, str(payload.get("request_id") or "")
            )
        elif message_type == "client_disconnected":
            target = str(payload.get("client_id") or "")
            if client.application_type not in {"tactic_handler", "operator"}:
                client.send(structured_error(
                    str(payload.get("request_id") or ""),
                    "permission_denied", "Client cannot disconnect peers",
                ))
            elif target and target != client.client_id:
                self._remove(target, "operator_request")
        elif message_type == "server_shutdown":
            if client.application_type not in {"tactic_handler", "operator"}:
                client.send(structured_error(
                    str(payload.get("request_id") or ""),
                    "permission_denied", "Client cannot stop Handler Server",
                ))
            else:
                self.shutdown_requested.set()
        elif message_type == "client_event":
            event = dict(payload)
            event["client_id"] = client.client_id
            event["application_type"] = client.application_type
            self._broadcast_operators(event)

    @staticmethod
    def _normalize_command(payload):
        aliases = {
            "open_snapshot": "open_scene",
            "import_snapshot": "import_file",
            "reference_snapshot": "reference_file",
        }
        action = str(payload.get("action") or "")
        if action not in aliases:
            return payload
        routed = dict(payload)
        routed["action"] = aliases[action]
        source = dict(routed.get("payload") or {})
        source["path"] = str(
            source.get("path") or source.get("local_path") or ""
        )
        routed["payload"] = source
        return routed

    def _resolve_target(self, payload):
        target = str(payload.get("target_client") or "")
        if not target.startswith("@"):
            return payload
        application_type = target[1:]
        action = str(payload.get("action") or "")
        with self._lock:
            candidates = sorted(
                (
                    client for client in self._clients.values()
                    if client.application_type == application_type
                    and action in client.capabilities
                ),
                key=lambda client: client.client_id,
            )
        routed = dict(payload)
        routed["target_client"] = (
            candidates[0].client_id if candidates else target
        )
        return routed

    def _register(self, client):
        previous = None
        with self._lock:
            previous = self._clients.get(client.client_id)
            self._clients[client.client_id] = client
        if previous:
            self._close_socket(previous.socket)
        self.logger.info(
            "Client connected: %s (%s, pid=%s)", client.client_id,
            client.application_type, client.process_id,
        )

    def _remove(self, client_id, reason, expected_socket=None):
        with self._lock:
            client = self._clients.get(client_id)
            if client and expected_socket is not None and client.socket is not expected_socket:
                client = None
            elif client:
                self._clients.pop(client_id, None)
        if not client:
            return
        self._close_socket(client.socket)
        self.router.client_disconnected(client_id)
        self._broadcast(message(
            "client_disconnected", client_id=client_id, reason=reason
        ))
        self._broadcast_capabilities()
        self.logger.info("Client disconnected: %s", client_id)

    def _send_to(self, client_id, payload):
        with self._lock:
            client = self._clients.get(client_id)
        if not client:
            return False
        try:
            client.send(payload)
            return True
        except OSError:
            self._remove(client_id, "send_failed")
            return False

    def _broadcast(self, payload):
        with self._lock:
            client_ids = list(self._clients)
        for client_id in client_ids:
            self._send_to(client_id, payload)

    def _broadcast_operators(self, payload):
        with self._lock:
            client_ids = [
                client.client_id for client in self._clients.values()
                if client.application_type in {"tactic_handler", "operator"}
            ]
        for client_id in client_ids:
            self._send_to(client_id, payload)

    def _broadcast_capabilities(self):
        self._broadcast(message("capabilities", clients=self.clients))

    def _monitor_loop(self):
        while self._running.is_set():
            time.sleep(0.25)
            if not self._running.is_set():
                break
            self.router.expire()
            now = time.monotonic()
            with self._lock:
                expired = [
                    client_id for client_id, client in self._clients.items()
                    if now - client.last_heartbeat > self.heartbeat_timeout
                ]
            for client_id in expired:
                self._remove(client_id, "heartbeat_timeout")

    def _log_command(self, level, sender, target, action, request_id):
        self.logger.info(
            "%s sender=%s target=%s action=%s request=%s",
            level, sender, target, action, request_id,
        )

    @staticmethod
    def _close_socket(sock):
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass
