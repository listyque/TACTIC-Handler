---
group: DCC
icon: hub
order: 61
---
# TACTIC Handler Server

> Handler Server is the local authenticated command router between standalone Handler and thin DCC
> clients. Its window is an operator and diagnostic console, not the normal way to open or save scenes.

## What the server does

Handler starts the router as a separate local process bound to `127.0.0.1` on an available port. A
fresh random access token is passed to that process for the current session. DCC runtime discovery
finds the live Handler session and uses its endpoint and token; users do not enter either value.

The server:

- authenticates each local client;
- tracks client IDs, application types, PIDs and registered capabilities;
- routes a request to one exact client;
- returns structured results, errors and request IDs;
- broadcasts client connection, disconnection and script events;
- fails pending requests when a client or server disappears.

TACTIC credentials are not DCC credentials and are never part of the command payload shown here.
Handler Server does not expose a LAN web interface.

## Header and lifecycle

| Control | Meaning |
| --- | --- |
| Endpoint | Current loopback host and dynamically selected port. `localhost` is shown before startup completes. |
| State | `STOPPED`, `STARTING`, `RUNNING` or `STOPPING`. |
| **Start** | Starts the router process and connects Handler's own operator client. Startup completes after capabilities arrive. |
| **Stop** | Requests graceful shutdown. Connected clients and unfinished requests disconnect; a stuck process is terminated after the bounded shutdown period. |

Stopping the router does not close Handler, but DCC actions are unavailable until clients reconnect.

## Connected clients

Every row represents one process, not merely one application type:

- **client ID** is the exact routing target;
- **application** identifies Maya or another registered DCC;
- **PID** distinguishes concurrent sessions;
- **capabilities** list exactly what this client accepts;
- **ACTIVE** marks the target used by the manual command panel.

Select a row to populate the command list. **Disconnect selected** breaks only that connection and
causes its pending requests to fail explicitly. The DCC runtime may reconnect while it remains active.

The cube control starts or stops a simulated Maya client. It tests transport and does not launch
Maya or validate native scene behavior.

## Send a diagnostic command

The right side is a low-level command console:

1. Select a connected client.
2. Choose one of that client's advertised capabilities.
3. Enter a JSON **object** as the payload; arrays and scalar values are rejected.
4. Choose a timeout from 1 to 300 seconds.
5. Press **Send**.

Use `{}` for commands with no arguments. A path action normally requires a prepared local path:

```json
{
  "path": "D:/project/scenes/example.ma",
  "focus_application": true
}
```

Manual commands bypass normal snapshot, repository and Commit Queue preparation. Use them only to
diagnose a known capability, never as an alternative check-in workflow.

## Results and logging

Each card contains timestamp, target, action and status. Pending requests show the sanitized payload;
completed requests show a summary and structured result; errors retain the remote traceback.
**Clear results** clears only this on-screen list.

The complete event also goes to Debug Log with its request ID. Passwords, tickets, tokens, cookies
and other sensitive fields are redacted before logging.

## Requests from the normal UI

Open, import, reference, save, check-in preparation, DCC scripts and triggers use the same router but
do not require this window to be open. They use the top-bar selected client and validate capabilities.

For Maya scene actions, Handler applies **Maya Scene** focus preferences. On Windows it
grants the target PID foreground permission; opening may send `focus_application` before
`open_scene` so a Maya save prompt is not hidden.

## Failure states

| Message or state | Meaning and response |
| --- | --- |
| **Handler Server is not connected** | The router has not reached `RUNNING`, or Handler's operator client disconnected. Start it and inspect startup output. |
| **Select a target client** | Select one connected process before sending. |
| **The selected client does not register this action** | Reconnect an updated connector or select a client that advertises the capability. |
| **Invalid JSON payload** | Correct JSON syntax; names and strings require double quotes. |
| **Command payload must be a JSON object** | Replace a list, scalar or `null` with an object such as `{}`. |
| **Timeout** | Check for a native modal prompt or a blocked DCC UI thread. |
| **Client disconnected** | The exact target exited or lost transport; work is not silently reassigned. |
| **Startup timeout** | The process did not publish a valid ready response and capabilities in time. Inspect Debug Log and process output. |

## Safe diagnostic sequence

1. Verify `RUNNING` and note the endpoint.
2. Confirm application, scene and PID.
3. Select it and verify the required capability.
4. Try a read-only command such as `get_application_info` with `{}`.
5. Match the result with the same request ID in Debug Log.
6. Reproduce the native action from its normal UI.

For setup, scripts, check-in and Maya troubleshooting, open the **DCC clients** topic.
