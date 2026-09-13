# DCC startup and the unified Handler API

Use [`tactic_handler_api`](handler_api.md) for TACTIC objects, repository files
and check-in. These operations execute in standalone Handler; native scene
actions execute in the selected DCC.

## Start and reuse Maya's connection

The installer shelf calls the existing startup entry point:

```python
import importlib
import sys

HANDLER_PATH = "D:/TACTIC-Handler"  # Your installed root.
if HANDLER_PATH not in sys.path:
    sys.path.insert(0, HANDLER_PATH)

from tactic_handler_dcc import maya
maya = importlib.reload(maya)
maya.startup(HANDLER_PATH)
```

Startup returns immediately. It reuses an existing connected client and asks
Handler to show its window. It reloads current API/connector code and refreshes
fixed native capabilities without stopping and reconnecting the existing
ThinClient. `maya.status()` reports startup/connection state;
`maya.show_handler()` requests the window; `maya.stop()` drains submitted API
work off the UI thread, releases its handles, then stops the client.

Once connected:

```python
from tactic_handler_api import get_api

th = get_api()

def find_objects():
    stype = th.project("demo").stype("types/object")
    return [obj.get_info() for obj in stype.query(limit=20).items]

operation = th.submit(find_objects)
# In a subsequent command, after completion:
if operation.done:
    print(operation.result())
```

Do not call blocking data methods or `operation.wait()` on Maya's UI thread.
An unfinished result raises `NotReady`, and synchronous UI-thread I/O raises
`BlockingCallError`. Callbacks touching Maya must be dispatched explicitly:

```python
import maya.utils
subscription = operation.on_done(print, dispatch=maya.utils.executeDeferred)
# subscription.close() when the callback's owner is destroyed.
```

The runtime closes its own API. If a plugin needs a separate lifecycle, create
`from_client(maya.runtime().client)` and close that API, not the shared client.

## Native Maya operations

Use `maya.cmds`/`maya.mel` for Maya-native scripting on Maya's thread. The
connector still registers fixed actions including `get_application_info`,
`get_current_scene`, `prepare_scene`, `validate_scene`, `save_current_scene`,
`prepare_checkin`, `get_temp_playblast`, `open_scene`, `import_file`,
`reference_file`, `execute_script_file`, and `create_script_shelf`.
Saved project scripts also expose `execute_custom_script`; it accepts only a
validated project code and relative path beneath the synchronized
`custom_scripts/<project>` tree.

`create_script_shelf` receives the requested Maya tab name and active Handler
shelf as structured data. Maya creates the shelf or replaces an existing tab
with the same visible name through Maya's persistent `addNewShelfTab` path,
beginning with the Handler launcher. The remaining
buttons keep their labels, hints, rendered Font Awesome icons, order, and
validated project script paths; an unavailable glyph uses a labeled native
Python icon. Every icon displays the first six characters of its button name
on Maya's dark overlay strip.

Common scene helpers are available directly to Maya scripts:

```python
maya.get_maya_window()
maya.get_current_scene_format()
maya.get_skey_from_scene()
maya.set_info_to_scene(search_key, context)
```

Handler's file menus route scene actions to the selected client, prepare
playblasts and submit files through Commit Queue. A Maya save result is
preparation data, not a completed
TACTIC check-in; only standalone Handler creates/uploads snapshots.

`th.commit_queue().add(...)` and `th.repositories.sync(...)` operate on files.
Save the Maya scene before submitting it. See the [API guide](handler_api.md).

## Adding another DCC

Start from the two checked-in boilerplate files. They begin with `_`, so Handler
ignores them until copied under a real application id:

```text
tactic_handler_dcc/connectors/_template.py -> tactic_handler_dcc/connectors/nuke.py
tactic_handler_dcc/_template.py            -> tactic_handler_dcc/nuke.py
```

Give both copies the same module name. The root `nuke.py` needs no edits: it
finds `connectors/nuke.py` from its own filename. In the connector, replace the
manifest's `application`, title and visible labels, then implement the native
method bodies. Keep the host SDK import inside the connector constructor or
methods so the module remains import-safe in standalone Handler.

After restarting Handler, the configuration page appears automatically. After
`nuke.startup(HANDLER_PATH)` connects the client, registered capabilities enable
the matching item buttons, context-menu commands, Tools-menu commands, trigger
events, focus behavior, and shelf export. Adding a standard integration does
not require editing QML, `menu_schema.py`, `configuration.py`, Handler Server,
or check-in controllers.

### Manifest-owned UI

`DCC_MANIFEST["ui"]` is the single declaration for integration UI:

```python
from . import STANDARD_ITEM_ACTIONS

DCC_MANIFEST = {
    "application": "nuke",
    "title": "Nuke",
    "script_triggers": (
        ("scene.open", "Open script", "folder_open"),
        ("scene.save", "Save script", "save"),
    ),
    "ui": {
        "item_actions": (
            *STANDARD_ITEM_ACTIONS,
            {
                "id": "show_in_node_graph",
                "capability": "show_in_node_graph",
                "title": "Show in Node Graph",
                "icon": "account_tree",
                "target": "item",
                "scopes": ("sobject", "snapshot"),
            },
        ),
        "tool_actions": ({
            "id": "show_viewer",
            "capability": "show_viewer",
            "title": "Show Viewer",
            "icon": "visibility",
        },),
        "configuration": {
            "title": "Nuke",
            "description": "Nuke scene integration",
            "icon": "deployed_code",
            "help_topic": "dcc_clients",
            "sections": ({
                "title": "Scripts",
                "fields": ({
                    "key": "script_format",
                    "type": "choice",
                    "title": "Script format",
                    "default": "nk",
                    "choices": ({"label": "Nuke (.nk)", "value": "nk"},),
                },),
            },),
        },
        "focus_preferences": {
            "open_scene": "focus_after_open",
            "prepare_checkin": "focus_after_save",
        },
    },
}
```

An item action `target` is one of:

- `file`: Handler resolves and synchronizes the published file, then supplies `path`.
- `scene_checkin`: Handler starts the shared scene preparation and Commit Queue flow.
- `item`: Handler supplies structured sObject/snapshot context to a native command.

Set `quick=True` to show the action directly on result cards. Optional action
fields use the same `boolean`, `choice`, `integer`, and `text` schema as the DCC
configuration page. Handler persists those values and renders the editor with
shared controls; connector code validates the final payload at its boundary.

The connector implements `instance(handler_path)`, exposes a native-thread
`dispatch`, and registers only fixed methods in `register(registry)`. A command
appears only while the selected client advertises its declared `capability`.
Delete unsupported standard actions from the manifest instead of registering
dummy native methods.

Use the canonical capability names `open_scene`, `import_file`,
`reference_file`, `get_current_scene`, `prepare_checkin`,
`execute_custom_script`, and `execute_script_file` where those operations make
sense. Unsupported actions are not registered and do not appear in the UI.
`prepare_checkin` returns local preparation data (`files`, optional `previews`,
and optional `application_info`); standalone Handler remains the only owner of
repository transfer and TACTIC check-in. DCC-specific options are declared by
the manifest and validated again by the native connector. An optional
`install_exit_callback(callback)` returns its cleanup callable.

When `get_current_scene` and `prepare_checkin` are both registered, Handler uses
the deferred Commit Queue flow: `get_current_scene` returns `path`, `scene_type`,
and `extension`; Commit later calls `prepare_checkin` with the final repository
path. Register optional `get_temp_playblast` to add a queue preview and return
its `preview_path` plus `preview_type`. A connector with only `prepare_checkin`
uses the simpler immediate-preparation flow.

## New custom scripts

The shelf/runtime can execute a script under the configured Handler tree:

```python
job = maya.execute_custom_script(
    "tools/runner", project="demo", kwargs={"search_key": search_key},
)
```

This starts the existing native script job and returns immediately. The script
receives two invocation values:

- `TACTIC_PROJECT_CODE`: the requested project code; not a global current-project mutation.
- `TACTIC_SCRIPT_KWARGS`: the supplied parameters.

Example `custom_scripts/demo/tools/runner.py`:

```python
from tactic_handler_api import get_api

th = get_api()
search_key = TACTIC_SCRIPT_KWARGS["search_key"]

def edit_description():
    obj = th.sobject(search_key)
    obj.set_value("description", "Updated by a custom script")
    obj.commit()
    return obj.get_info()

RESULT = th.submit(edit_description)
```

Script execution itself runs on Maya's native thread; submit data work to `th`.
A script may deliberately return an Operation as `RESULT`; completion of the
script job does not imply completion of that returned operation.

If the requested script is missing or `refresh_scripts=True`, the runtime uses
`th.project(project_code).download_scripts()` to fetch published scripts through
Handler. Refresh requires an explicit project. Relative paths cannot escape the
custom-script root. Bundled project-specific scripts require adaptation before use.

## Protocol and tests

The data service registers only `handler.call`, `handler.release` and
`handler.close`. `handler.call` accepts only methods/properties listed for its
domain type in `tactic_handler_api/contract.py`. Handles are API-session-owned;
ordinary mapping values cannot forge object references. Exceptions preserve the
remote traceback and known error type. Writes are never automatically retried.

Regression suites:

```console
python -m unittest tests.test_tactic_dcc_sdk tests.test_maya_runtime tests.test_handler_api_desktop tests.test_script_editor
```

The transport tests use real local TCP clients with isolated TACTIC operations;
the queue tests use the actual Qt queue owner. They do not launch Maya or write
to a production TACTIC server.
