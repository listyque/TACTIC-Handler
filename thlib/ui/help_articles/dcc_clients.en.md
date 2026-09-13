---
group: DCC
icon: deployed-code
order: 60
---
# DCC clients

> A DCC client connects Maya or another content application to the standalone TACTIC Handler.
> Handler owns TACTIC, repositories and check-in; the selected DCC client performs only native scene actions.

## The important boundary

There are two cooperating processes:

| Owner | Responsibilities |
| --- | --- |
| **TACTIC Handler** | Server queries, Search Types, repositories, local synchronization, version selection, Commit Queue, check-in and user-visible errors. |
| **DCC client** | Current-scene information, validation, save, playblast preparation, open, import, reference, native script execution and returning focus to the content application. |

A DCC save result is preparation data. It is not a TACTIC check-in. Handler receives the prepared
files, places them in Commit Queue and remains the only process that creates and uploads snapshots.

The connector accepts a fixed list of registered actions. Handler never sends generated Python,
`eval` or `exec` text to a DCC client.

## Connect Maya

Run the installed launcher or use the same public entry point from Maya:

```python
import importlib
import sys

HANDLER_PATH = "D:/TACTIC-Handler"
if HANDLER_PATH not in sys.path:
    sys.path.insert(0, HANDLER_PATH)

from tactic_handler_dcc import maya
maya = importlib.reload(maya)
maya.startup(HANDLER_PATH)
```

`startup()` returns immediately. It behaves as follows:

1. Reuses the live Maya connection when one already exists.
2. Reloads current connector and public API code without deliberately stopping the live client.
3. Finds the running Handler or starts the standalone application when it is absent.
4. Registers this Maya process and advertises its native capabilities.
5. Requests the existing Handler window to come to the foreground.

Useful lifecycle calls:

```python
maya.status()        # state, message and connected flag
maya.show_handler()  # ask the connected Handler to show its window
maya.stop()          # explicitly close this Maya connector
```

Closing Maya unregisters its client. Repeating `startup()` is the normal way to refresh connector
code during development; do not call `stop()` first unless you really want to break the connection.

## Select the correct client

Every connected DCC process is a separate client. The selector in Handler's top bar identifies a
client by application, version, current scene and process ID. Selection matters: file actions,
DCC scripts and DCC triggers are routed to that exact client ID.

Before an operation, check that:

- the expected application and scene are shown;
- the PID belongs to the intended process when several Maya sessions are open;
- the requested command is available for that client;
- the scene prompt, if any, is not waiting behind another Maya window.

Opening the selector refreshes application and scene details. Handler does not continuously poll
every connected DCC while the selector is closed.

## Registered Maya capabilities

The current Maya connector advertises only the operations it can execute:

| Capability | What it returns or does |
| --- | --- |
| `get_application_info` | Maya title, version and process information. |
| `get_current_scene` | Current path, scene type and extension. |
| `focus_application` | Brings the selected Maya process to the foreground. |
| `prepare_scene` | Reads scene identity and preparation metadata without uploading anything. |
| `validate_scene` | Reports scene conditions required by the requested operation. |
| `save_current_scene` | Saves through Maya and returns the prepared result. |
| `prepare_checkin` | Saves to the final prepared path and returns files, optional previews and application metadata. |
| `get_temp_playblast` | Produces an optional temporary preview for Commit Queue. |
| `open_scene` | Opens a local scene in the selected Maya process. |
| `import_file` | Imports a local file through Maya. |
| `reference_file` | Creates a Maya reference to a local file. |
| `execute_script_file` | Executes an explicitly prepared local script file. |
| `execute_custom_script` | Executes a validated synchronized project script. |
| `create_script_shelf` | Creates or replaces a Maya shelf from a Handler script shelf. |

An unavailable action is absent from menus and disabled in the UI. A new DCC does not need fake
implementations of Maya-only commands.

## Open, import and reference

All three operations deliberately use the same boundary:

1. Handler resolves the selected snapshot and file object.
2. Handler verifies the configured repository and obtains the correct local path.
3. A missing or outdated file is synchronized by Handler, outside the DCC.
4. Handler brings the selected Maya process forward when **Return focus after open action** is enabled.
5. Handler sends `open_scene`, `import_file` or `reference_file` with the prepared local path.
6. Maya performs the native action and returns a structured result or traceback.

If Maya asks whether to save a modified scene, that is a Maya-owned prompt. Answer it in Maya. A
prompt does not mean that Handler lost the request, but the request can finish only after Maya does.

## Save and check-in

The normal scene check-in remains a deferred Commit Queue workflow:

1. Handler asks the selected client for `get_current_scene`.
2. Handler prepares the target context, repository path, version and versionless file.
3. The operation appears in Commit Queue, where description, context and files can still be reviewed.
4. When the queue operation runs, Handler calls `prepare_checkin` with the final local path.
5. Maya saves the scene, captures the optional playblast and returns preparation metadata.
6. Handler validates the returned files, transfers them and creates the TACTIC snapshot.

Do not close Maya while a DCC preparation request is pending. If Maya reports success but the queue
fails afterward, inspect the queue error: transfer and snapshot creation happen after the native save.

Maya-specific focus and scene options are on **Configuration → Maya Scene**.

## Common Maya helpers

Saved Maya scripts can use the small native helper surface directly:

```python
from tactic_handler_dcc import maya

window = maya.get_maya_window()
scene_format = maya.get_current_scene_format()
search_key = maya.get_skey_from_scene()
maya.set_info_to_scene(search_key, "publish")
```

These calls inspect or edit Maya state. TACTIC objects must still be obtained through the Handler API.

## Run a saved DCC script

```python
job = maya.execute_custom_script(
    "tools/runners/save_current_scene",
    project="demo",
    kwargs={"search_key": search_key},
)
```

The path is relative to `custom_scripts/<project>` and cannot escape that directory. If the local
script is missing, or `refresh_scripts=True` is requested, the runtime downloads the published
project scripts first. Refresh therefore requires an explicit project code.

The script receives:

```python
TACTIC_PROJECT_CODE   # project selected for this invocation
TACTIC_SCRIPT_KWARGS  # a dict with the supplied values
```

The script itself runs on Maya's native thread. Its `print()` output and traceback stay visible in
the DCC console and are mirrored into Script Editor output. `RESULT` becomes the script job result.

## Use TACTIC data without freezing Maya

Server and repository work must not block Maya's UI thread. Submit it to Handler:

```python
from tactic_handler_api import get_api

th = get_api()

def load_object():
    obj = th.sobject(search_key)
    return obj.get_info()

operation = th.submit(load_object)
```

If the result changes Maya UI, dispatch the callback back to Maya's thread:

```python
import maya.utils

subscription = operation.on_done(
    print,
    dispatch=maya.utils.executeDeferred,
)
```

Do not call blocking object methods or `operation.wait()` on Maya's UI thread. Handler raises
`BlockingCallError` instead of silently freezing the application. Close long-lived callback
subscriptions when their owning tool is destroyed.

## DCC script triggers

DCC actions are labeled with their application in Script Triggers, for example Maya open, Maya save
and Maya reference. A DCC trigger:

- runs only for the matching registered application and action;
- is routed to the selected connected client;
- executes assigned scripts in their saved order;
- receives the action context through `TACTIC_SCRIPT_KWARGS`;
- reports each script's output and traceback through the Script Editor output path.

Standalone snapshot events are different actions. Saving a TACTIC snapshot does not imply that a
Maya save trigger ran, and a native Maya save does not itself create a TACTIC snapshot.

## Script shelves in Maya

**Create in Maya** copies the active Handler shelf into a Maya shelf tab. Handler asks for the tab
name and checks whether it already exists. Updating replaces that tab's generated buttons instead
of creating duplicates.

The first button starts or reveals TACTIC Handler. Following buttons preserve their order, labels,
hints, project script paths and rendered icons. The tab persists through Maya's native shelf system.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| **No DCC clients connected** | Run `maya.startup(HANDLER_PATH)`, inspect `maya.status()` and Maya's Script Editor, and confirm that this Handler installation is on `sys.path`. |
| **Wrong Maya receives the command** | Select the correct application, scene and PID in the top-bar client selector. |
| **Action is disabled or absent** | The selected client did not advertise the capability. Reconnect after updating connector code. |
| **Handler starts but its window does not appear** | Call `maya.show_handler()` and ensure the standalone process is not blocked by a modal dialog. |
| **Opening waits forever** | Look for a Maya save, replace or reference prompt, including behind the main window. Check the request ID in Debug Log. |
| **File is missing in Maya** | Synchronize the snapshot in Handler and verify repository configuration. DCC clients do not download files. |
| **Save succeeded but check-in failed** | Inspect the Commit Queue transfer or TACTIC error after the DCC preparation result. |
| **`BlockingCallError`** | Move TACTIC work into `th.submit(...)`; do not wait on Maya's UI thread. |
| **Custom script is not found** | Verify project code, published server copy and relative path. |
| **Connection was lost** | The active runtime reconnects. If it reaches `failed`, rerun `startup()` and inspect Handler Server and Debug Log. |

## Diagnostic checklist

When reporting a DCC issue, capture:

1. `maya.status()` output.
2. Selected client label and PID.
3. Action name and whether it appears in the client's capability list.
4. Handler Debug Log event and request ID.
5. Full Maya Script Editor output and traceback.
6. Local source and destination paths, with credentials removed.
7. Whether Maya showed a native modal prompt.

The **TACTIC Handler Server** window provides low-level client, capability and request inspection. It
is a diagnostic tool; normal open, save, script and check-in workflows should use their regular UI.

## Adding another DCC

Copy the ready boilerplate instead of starting from an empty module:

```text
tactic_handler_dcc/connectors/_template.py -> tactic_handler_dcc/connectors/nuke.py
tactic_handler_dcc/_template.py            -> tactic_handler_dcc/nuke.py
```

The underscore keeps both source templates out of discovery. Give both copies the same filename.
The copied root module needs no edits: it finds the connector from its own module name. In the
connector, replace the `template` application id, visible labels and native method bodies. Keep the
DCC's own Python package import inside the connector constructor or native methods.

Restart Handler after adding the files. The `DCC_MANIFEST` then creates the DCC Configuration page.
Once the client connects, the same manifest supplies context-menu actions, quick item buttons,
Tools-menu actions, action-option forms, focus preferences, and Script Trigger events. No QML,
shared menu, Handler Server, or check-in controller edit is needed.

The boilerplate contains all supported declarations and safe placeholder native methods. Keep only
the standard actions the DCC really supports, register their fixed capabilities, and replace each
placeholder body with the host application's native API. `file` actions receive a local synchronized
path, `item` actions receive object context, and `scene_checkin` enters Handler's shared Commit Queue
flow. Configuration and action-option fields support `boolean`, `choice`, `integer`, and `text`.

For the complete manifest contract and a Nuke example, open `docs/dcc_api.md` in the installation.
