# Thin client protocol v1

## Transport and framing

The server listens on `127.0.0.1`. Each message is UTF-8 JSON preceded by a four-byte
unsigned network-order payload length. Payloads larger than 1 MiB are rejected.
Every message contains `type` and `protocol_version: 1`.

## Handshake

Normal clients do not receive connection settings from the user. The localhost
server publishes an atomic per-user discovery record containing protocol version,
process id, endpoint, creation time, and a random session token. Clients ignore
invalid, incompatible, and stale records, then use the token only for the initial
handshake. The record is removed during graceful server shutdown.

Client to server:

```json
{"type":"hello","protocol_version":1,"session_token":"…","client_id":"maya-main"}
```

Server replies with `hello` and `accepted: true`, then the client registers:

```json
{"type":"register_client","protocol_version":1,"client_id":"maya-main","application_type":"maya","process_id":1234,"capabilities":["open_scene","import_file","reference_file","save_current_scene","get_current_scene"]}
```

The server replies and broadcasts `capabilities` with safe connected-client records.
A connected client may also send its current capability list after replacing a
hot-reloaded registry; the server updates only that authenticated client's record
and rebroadcasts the list.
The session token is never included in later messages or logs.

## Command

```json
{
  "type": "command",
  "protocol_version": 1,
  "request_id": "0f…",
  "target_client": "maya-main",
  "action": "open_scene",
  "payload": {"path": "D:/work/scene.ma", "force": false},
  "timeout": 60,
  "sender": "tactic-handler-a1"
}
```

Required command fields are protocol version, request id, target client, action,
object payload, timeout, and sender. The server replaces `sender` with the identity
of the authenticated connection. The main UI uses an explicit client id so switching
between Maya, Blender, or multiple running Maya sessions is deterministic.
Application aliases remain a protocol-level fallback for non-interactive callers.

## Results and errors

Successful or cancelled action:

```json
{"type":"result","protocol_version":1,"request_id":"0f…","success":true,"cancelled":false,"payload":{"opened_path":"D:/work/scene.ma"},"sender":"maya-main"}
```

Structured error:

```json
{"type":"error","protocol_version":1,"request_id":"0f…","code":"action_failed","message":"Scene file does not exist","traceback":"…","sender":"maya-main"}
```

Known error codes include `authentication_failed`, `protocol_error`,
`duplicate_request`, `client_unavailable`, `client_disconnected`, `timeout`,
`permission_denied`, and `action_failed`. Tracebacks are returned to the initiating
client and stored in Debug Log rather than displayed as the main user message.

## Other messages

| Type | Direction | Purpose |
|---|---|---|
| `hello` | both | token handshake and acceptance |
| `register_client` | client → server | identity and capabilities |
| `capabilities` | both | registration acknowledgement/client list, or the sender's refreshed allow-list |
| `command` | sender → server → target | allow-listed action request |
| `result` | target → server → sender | success or cancellation payload |
| `error` | either direction | structured failure |
| `cancel` | sender/server → target | cooperative cancellation by request id |
| `heartbeat` | both | liveness and disconnect detection |
| `client_disconnected` | server → clients | disconnect event; operator may request peer disconnect |
| `server_shutdown` | operator → server | graceful local server shutdown |

## Registered v1 actions

Demo: `ping`, `get_application_info`, `open_file`, `save_current_file`,
`get_current_file`, plus test-only `fail` and `sleep`.

DCC file actions use the standard capability names `get_current_scene`,
`prepare_checkin`, `open_scene`, `import_file`, and `reference_file`; each
connector registers only the actions it supports. Registering both scene
capabilities enables the deferred Commit Queue flow. Optional
`get_temp_playblast` adds a preview to that flow.

Maya also registers `get_application_info`, `prepare_scene`, `validate_scene`,
`save_current_scene`, `execute_custom_script`, `execute_script_file`, and
`create_script_shelf`. An unnamed scene is saved only after standalone supplies
the TACTIC-reserved `path` and optional `preview_path`.
Snapshot aliases are normalized
by the server. No action accepts Python source, module names, or callable
expressions. `execute_script_file` accepts only a `.py` path under the Script
Editor's application-owned temporary directory. `execute_custom_script`
accepts only a project code and relative path resolving beneath the local
synchronized custom-script tree.
`create_script_shelf` accepts a tab name, structured presentation data, and
validated project-relative script paths. Maya creates or updates the matching
native shelf and reports which operation occurred.
