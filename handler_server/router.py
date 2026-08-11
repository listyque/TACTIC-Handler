from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from .protocol import structured_error


@dataclass
class PendingRequest:
    request_id: str
    sender: str
    target: str
    action: str
    deadline: float


class RequestRouter:
    def __init__(self, send_to, log):
        self._send_to = send_to
        self._log = log
        self._pending: dict[str, PendingRequest] = {}
        self._lock = threading.RLock()

    def route_command(self, sender: str, command: dict) -> None:
        request_id = str(command["request_id"])
        target = str(command["target_client"])
        with self._lock:
            if request_id in self._pending:
                self._send_to(sender, structured_error(
                    request_id, "duplicate_request", "Request id is already active"
                ))
                return
            self._pending[request_id] = PendingRequest(
                request_id, sender, target, str(command["action"]),
                time.monotonic() + float(command["timeout"]),
            )
        routed = dict(command)
        routed["sender"] = sender
        if not self._send_to(target, routed):
            with self._lock:
                self._pending.pop(request_id, None)
            self._send_to(sender, structured_error(
                request_id, "client_unavailable",
                f"Target client is not connected: {target}",
            ))
            return
        self._log("COMMAND", sender, target, command["action"], request_id)

    def route_response(self, client_id: str, response: dict) -> None:
        request_id = str(response.get("request_id") or "")
        with self._lock:
            pending = self._pending.get(request_id)
            if not pending or pending.target != client_id:
                return
            self._pending.pop(request_id, None)
        self._send_to(pending.sender, response)
        self._log(
            "RESULT" if response.get("type") == "result" else "ERROR",
            pending.sender, pending.target, pending.action, request_id,
        )

    def route_cancel(self, sender: str, request_id: str) -> None:
        with self._lock:
            pending = self._pending.get(request_id)
            if not pending or pending.sender != sender:
                return
        self._send_to(pending.target, {
            "type": "cancel", "protocol_version": 1,
            "request_id": request_id, "sender": sender,
        })
        self._log(
            "CANCEL", pending.sender, pending.target,
            pending.action, pending.request_id,
        )

    def client_disconnected(self, client_id: str) -> None:
        failed = []
        with self._lock:
            for request_id, pending in list(self._pending.items()):
                if client_id in {pending.sender, pending.target}:
                    failed.append(pending)
                    self._pending.pop(request_id, None)
        for pending in failed:
            if pending.target == client_id:
                self._send_to(pending.sender, structured_error(
                    pending.request_id, "client_disconnected",
                    f"Client disconnected: {client_id}",
                ))
            self._log(
                "DISCONNECTED", pending.sender, pending.target,
                pending.action, pending.request_id,
            )

    def expire(self) -> None:
        now = time.monotonic()
        expired = []
        with self._lock:
            for request_id, pending in list(self._pending.items()):
                if pending.deadline <= now:
                    expired.append(pending)
                    self._pending.pop(request_id, None)
        for pending in expired:
            self._send_to(pending.target, {
                "type": "cancel", "protocol_version": 1,
                "request_id": pending.request_id,
                "sender": "handler-server",
            })
            self._send_to(pending.sender, structured_error(
                pending.request_id, "timeout", "Command timed out"
            ))
            self._log(
                "TIMEOUT", pending.sender, pending.target,
                pending.action, pending.request_id,
            )
