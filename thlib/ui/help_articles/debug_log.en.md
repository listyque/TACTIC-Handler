---
group: Reference
icon: bug-report
order: 22
---
# Debug Log

> Debug Log collects the enabled diagnostic event levels and keeps each application run as a
> searchable session.

## Main controls

Use level filters, the group tree, text search, event details, runtime-command copy, the session
selector, Open Session, Return to Live Session, Copy Session Path, and Clear Session.

## Usage notes

- Each run writes one compact versioned JSONL session.
- Compact disk keys are expanded to descriptive fields in the viewer.
- Messages, details, runtime commands, script bodies, payloads, and stacktraces are stored without
  length or nesting truncation so a recorded operation can be reproduced; credential fields remain
  redacted.
- Successful local API setup calls such as set_server are omitted, while their failures keep the
  runtime command and stacktrace.
- Only the current session schema is listed and accepted; replaced formats are not loaded.

## Filter an investigation

Level buttons combine with the selected group and text search. The group tree counts matching events
by module and slash-separated subsystem. Search matches message, group, module, function, runtime
command and stacktrace. Clearing one filter does not reset the others.

Select an event to inspect its timestamp, level, source module, function, line, duration, message,
detail, runtime command and stacktrace. The detail splitter and group-panel width are remembered.

## Live and saved sessions

**Live session** continues receiving events from the current process. Choosing a session from history
or **Open saved debug session** loads a read-only `.jsonl` file. **Return to live session** restores the
in-memory stream; it does not merge old events into the current run.

**Clear Session** clears the current visible live entries. While a saved file is open it returns to
the live session instead of modifying that historical file.

## Reproduce and report

1. Reproduce the operation once.
2. Filter by Error/Exception and the relevant group.
3. Select the event with the matching object, action or request ID.
4. Copy the complete event and, when useful, its runtime command.
5. Copy the session path so the original structured log can be attached.

For DCC work, match Handler's request ID with Handler Server and the DCC console. Native Maya output
is not rewritten as a TACTIC error, but routed DCC tracebacks are retained.

## Privacy and retention

Passwords, tickets, tokens, cookies and known credential fields are redacted before display and disk
serialization. Do not paste secrets into ordinary untyped message fields. Session retention is
bounded, but a single diagnostic event is not silently truncated.

Long request and stacktrace lines wrap to the viewport in the error window and Debug Log.
This avoids rendering one enormous off-screen line after a large group check-in fails.
Wrapping changes only the display: keyboard selection/copy, Copy stacktrace, Copy runtime command
and the structured session log retain the complete original diagnostic text.

## Server RPC request log

JSON calls to `/admin/rpc` and XML-RPC calls to `/tactic/{project}/Api/` use the same `tactic_stream.server.api` logger at **INFO** level and the original TACTIC block format. Each call reaching the API dispatcher writes one block, including failed calls:

- `request_id`, `timestamp`, `user`, `simple method` and the legacy `ticket` header;
- arguments in method-signature order, including arguments received through JSON `kwargs`;
- `error` with the exception class when the call fails;
- `Duration`, `Memory`, `Increment` and `Total Duration`.

`Duration` measures the method after API initialization and authentication. `Total Duration` measures the whole API dispatch; HTTP body decoding and response serialization are outside this timer. Passwords and known secret fields in arguments are redacted. The `ticket` header retains the legacy representation; this server log is separate from the client JSONL log that redacts tickets. Argument display remains bounded by the existing logger.

Other browser endpoints, such as `/admin/search-configuration/query`, do not pass through `/admin/rpc`. Their HTTP access records are separate. Requests rejected before API dispatch also do not have a method block.

Handler selects XML-RPC or JSON separately for each connection preset in Configuration → Server → API transport. XML-RPC remains the default and supports Legacy TACTIC. Both paths use this same request log.


## Shared support window

Debug Log is available from sign-in as well as the application menu. Level buttons filter the view; recording levels remain in Configuration. Use Arrow Up/Down or Home/End in the event list: off-screen records are revealed before focus moves. Open Event Details to inspect the complete message, command and traceback; inspecting a stored event does not repeat its operation. Escape closes this child before Debug Log.

Open a JSONL session, search it, return to the live session and export it without changing the saved file. Handler copies a local session path; Stream downloads JSONL and stores history in this browser. Signing out in Stream closes owned details, clears local history and rejects an import still completing for the previous session. Long commands and results remain complete and can scroll horizontally.
