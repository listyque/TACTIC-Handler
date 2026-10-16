---
group: Reference
icon: error
order: 20
---
# Application errors

> The resizable modal error window identifies the failure category instead of presenting every failure
> as an unexpected error.

## Main controls

Expand the stacktrace to use the remaining window height, select its text, or copy the complete
stacktrace with one action.

The request is shown as Python with syntax highlighting and separate lines for arguments.
Multiline values (including server-side scripts) appear in their own code blocks with real
line breaks; `request_text_N` in the call identifies the corresponding block, not a modified
server argument. Scroll long code vertically or horizontally, or select and copy its text.
The original complete request remains unchanged in Debug Log.

## Usage notes

- Connection failures explain that the TACTIC server is unreachable and suggest checking its
  address, the network, VPN or proxy, and whether the server is running.
- The technical transport error remains in the stacktrace and Debug Log.
- Retry a retryable operation, open the relevant settings, or dismiss the error from the footer.

## What the category means

The title distinguishes connection timeout/refusal, expired ticket, login failure, database or
protocol failure, missing project or file, permission, import, value/type/key/index, operating-system,
runtime, assertion and QML interface errors. The readable title is guidance; the original exception
type and traceback remain unchanged in Debug Log.

## Read the window in order

1. Read the summary and the operation that failed.
2. Follow the actionable suggestion when one is available.
3. Expand the technical detail only when the summary is insufficient.
4. Copy the complete traceback before dismissing an issue that must be reported.
5. Find the same timestamp or request ID in Debug Log for payload and command context.

## Expected states that are not errors

Cancellation, an empty search result, no connected DCC, a missing optional preview and an offline
feature are shown in their owning views. They should not open an unrelated Application Error window.

## DCC failures

A native DCC prompt, render diagnostic or scene-load message remains in that application. Handler
shows an error when routing fails, a command times out, the client disconnects, a local file cannot
be prepared, or the DCC returns a structured failure. Check both consoles for a complete report.

## Before retrying

Retry read-only refresh or discovery after fixing connectivity. Before retrying a write, confirm that
the first attempt did not already create a snapshot, relation, object or file. Commit Queue preserves
failed rows so their exact state can be inspected instead of blindly repeated.

## Unresponsive window

If the Qt event loop stops responding for 15 seconds, Handler writes a Python thread report and,
on Windows, a native process dump into the local `log` directory. The files start with `ui_hang_`
and can be inspected after the process ends. Handler then starts a separate native system message
with the dump path and closes the unrecoverable process. Knowledge Base article edits are checkpointed
separately, so reopening the project restores the latest local article draft.

Long request and stacktrace lines wrap to the viewport in the error window and Debug Log.
This avoids rendering one enormous off-screen line after a large group check-in fails.
Wrapping changes only the display: keyboard selection/copy, Copy stacktrace, Copy runtime command
and the structured session log retain the complete original diagnostic text.


## Error inspection and retry ownership

Expand and copy the full traceback, inspect the complete runtime request and open contextual Help or Debug Log. Connection errors explain address/network/proxy checks. A selected historical log event is read-only: it never inherits a retry command from an earlier live failure. Handler offers Retry only when the existing error owner supplies a retryable operation. Stream keeps existing HTTP error notifications and provides the shared details view from Debug Log.
