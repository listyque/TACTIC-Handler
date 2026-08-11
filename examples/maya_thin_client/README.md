# Maya thin client

Add the repository root to Maya's Python path, then run in Maya's Script Editor:

```python
from examples.maya_thin_client import maya_client
maya_client.start()
```

No endpoint or token is configured in Maya. The modern TACTIC-Handler application
starts its local Handler Server automatically and publishes a per-user discovery
record. Every Maya process calls `start()`, receives a unique client id, and appears
separately in the connected DCC list. Start TACTIC-Handler before the client; a
missing local server produces a clear connection error after the discovery timeout.

Explicit `host`, `port`, and `token` arguments remain available together for
transport diagnostics only.

The module imports only `handler_server` and Maya's own API. It does not import
TACTIC-Handler, its UI, TACTIC API, or repository models. `MayaAdapter` registers:

- `get_application_info`;
- `get_current_scene`;
- `prepare_scene`;
- `validate_scene`;
- `save_current_scene`;
- `prepare_checkin` (saved scene plus optional Maya playblast);
- `open_scene`;
- `import_file`;
- `reference_file`.

Maya calls are dispatched through `maya.utils.executeInMainThreadWithResult`.
Stopping or reloading the shelf tool should call `maya_client.stop()`. The client
reconnects automatically while it is running. Maya must be tested manually because
its Python runtime is not available in the standalone test environment.

## TACTIC object API

`maya_client.start()` also configures the thin SDK. Project scripts only replace
their environment import:

```python
import tactic_handler_dcc.environment as thenv

sobjects, info = thenv.tc().get_sobjects_new(
    search_type="dolly3d/assets?project=niki_friends",
    filters=[("code", "ASSETS00001")],
)
asset = next(iter(sobjects.values()))
print(asset.get_title())
print(asset.get_related_sobjects(asset.get_stype()))
```

Function, class, attribute, and object method names are resolved from the native
TACTIC-Handler API in the standalone process. Returned `SObject`, `SType`,
`Process`, `Contexts`, `Snapshot`, `File`, `FileObject`, `Schema`, and server stub
instances are typed remote handles; method chaining keeps the original names.
See `tactic_api_example.py` for snapshots and file objects.

The original UI shortcuts remain available by name, but now address the running
modern application instead of returning QWidget instances. For example,
`env_inst.ui_main.create_project_dock()` opens a project workspace and
`env_inst.get_check_tree(..., "checkin_out", ...)` returns the modern check-in
workflow handle. The DCC sends scene or file data; naming, repository handling,
the commit queue, and the server operation stay in standalone TACTIC-Handler.

`checkin_current_scene.py` shows the original script shape. Running it restores
the TACTIC-Handler window, opens Check-in/Out, prepares the current Maya scene,
and places the operation in Commit Queue. The user starts the commit from the
queue, matching the original non-silent workflow.
