---
group: Configuration
icon: tune
order: 34
---
# Global configuration

> Global configuration controls application lifetime, notifications, worker limits, diagnostic
> event categories, and shows the active configuration directory.

## Application and notifications

| Setting | What it controls |
| --- | --- |
| **Close to system tray** | Keeps TACTIC Handler running when the main window close button is pressed. Disable it when closing the main window should exit the process. |
| **Activity feed notifications** | Shows a bottom-right notification when another user creates an activity event. It applies immediately and does not disable Activity Feed updates. |
| **Message notifications** | Shows a bottom-right notification for a new message when that conversation is not open. It applies immediately and does not stop message refresh. |

## Background workers

| Setting | Range and effect |
| --- | --- |
| **TACTIC request threads** | From 1 to 32 simultaneous XML-RPC requests. Repository Sync may send this many different discovery or transfer chunks at once. Higher values increase server load. |
| **Local worker threads** | From 1 to 32 simultaneous local background operations. This does not change Repository Sync's separate download limit. |

## Diagnostics

Each switch decides whether that event category is written to the Debug Log: **Log** for general
runtime detail, **Information** for normal lifecycle and completions, **Warning** for recoverable
conditions, **Missing files** for unresolved paths, **Exception** for caught Python and QML
exceptions, **Error** for failed requested operations, **Critical** for subsystem-level failures,
and **API** for TACTIC API runtime diagnostics. Disabling a category reduces future log volume; it
does not delete existing events.

## Configuration location

**Active configuration root** is read-only. It shows the directory used by the shared configuration
API so support and diagnostics can identify the active profile; change the environment owner rather
than typing a path here.
