from __future__ import annotations

import json
import socket
import struct
import uuid


PROTOCOL_VERSION = 1
MAX_MESSAGE_SIZE = 1024 * 1024
MESSAGE_TYPES = {
    "hello", "register_client", "capabilities", "command", "result",
    "error", "cancel", "heartbeat", "client_disconnected",
    "server_shutdown", "client_event",
}


class ProtocolError(ValueError):
    pass


def request_id() -> str:
    return uuid.uuid4().hex


def encode_message(message: dict) -> bytes:
    validate_message(message)
    payload = json.dumps(
        message, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    if len(payload) > MAX_MESSAGE_SIZE:
        raise ProtocolError("Message exceeds the 1 MiB protocol limit")
    return struct.pack("!I", len(payload)) + payload


def send_message(sock: socket.socket, message: dict) -> None:
    sock.sendall(encode_message(message))


def _receive_exact(sock: socket.socket, length: int) -> bytes:
    chunks = []
    remaining = length
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("Connection closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def receive_message(sock: socket.socket) -> dict:
    size = struct.unpack("!I", _receive_exact(sock, 4))[0]
    if size <= 0 or size > MAX_MESSAGE_SIZE:
        raise ProtocolError("Invalid message size")
    try:
        message = json.loads(_receive_exact(sock, size).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError("Invalid JSON payload") from error
    validate_message(message)
    return message


def validate_message(message: dict) -> None:
    if not isinstance(message, dict):
        raise ProtocolError("Protocol message must be an object")
    message_type = message.get("type")
    if message_type not in MESSAGE_TYPES:
        raise ProtocolError(f"Unsupported message type: {message_type}")
    version = message.get("protocol_version")
    if version != PROTOCOL_VERSION:
        raise ProtocolError(f"Unsupported protocol version: {version}")
    if message_type == "command":
        required = {
            "request_id", "target_client", "action", "payload",
            "timeout", "sender",
        }
        missing = sorted(required.difference(message))
        if missing:
            raise ProtocolError(
                "Command is missing fields: " + ", ".join(missing)
            )
        if not isinstance(message.get("payload"), dict):
            raise ProtocolError("Command payload must be an object")
        timeout = message.get("timeout")
        if not isinstance(timeout, (int, float)) or not 0 < timeout <= 300:
            raise ProtocolError("Command timeout must be between 0 and 300 seconds")
    elif message_type == "client_event":
        if not isinstance(message.get("payload"), dict):
            raise ProtocolError("Client event payload must be an object")
    elif message_type == "capabilities" and "capabilities" in message:
        if not isinstance(message.get("capabilities"), list):
            raise ProtocolError("Capabilities must be a list")


def message(message_type: str, **fields) -> dict:
    value = {"type": message_type, "protocol_version": PROTOCOL_VERSION}
    value.update(fields)
    validate_message(value)
    return value


def command(target_client: str, action: str, payload=None, timeout=30.0,
            sender="", current_request_id="") -> dict:
    return message(
        "command",
        request_id=current_request_id or request_id(),
        target_client=str(target_client or ""),
        action=str(action or ""),
        payload=dict(payload or {}),
        timeout=float(timeout),
        sender=str(sender or ""),
    )


def structured_error(request: str, code: str, text: str, traceback_text="",
                     sender="handler-server") -> dict:
    return message(
        "error",
        request_id=str(request or ""),
        code=str(code or "command_error"),
        message=str(text or "Command failed"),
        traceback=str(traceback_text or ""),
        sender=sender,
    )
