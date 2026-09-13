# Unified Handler API

`tactic_handler_api` provides object access, editing, file transfers, check-in
and optional UI commands from local Python and connected DCC applications.

## Start here

In the Handler Script Editor and a connected DCC, import the running API the
same way. It uses the existing UI and Commit Queue; do not close it. Local
Python runs on the GUI thread, so submit data work and inspect its result in a
subsequent command. UI commands dispatch themselves.

```python
from tactic_handler_api import get_api

th = get_api()
operation = th.submit(lambda: [project.get_code() for project in th.projects()])
# In a later command, when operation.done is True:
print(operation.result())
```

For a standalone script, use the existing configured Handler session. This does
not open windows, connect a DCC, or switch the application's current project:

```python
from tactic_handler_api import local

with local() as th:
    project = th.project("demo")
    stype = project.stype("types/object")
    result = stype.query(limit=50, order_by=["name asc"])
    for sobject in result.items:
        print(sobject.get_code(), sobject.get_value("name"))
```

`demo`, `types/object`, codes, fields, pipelines, processes and contexts below are
examples. Use actual values from your server. The Search Type namespace is not
assumed to equal the project code. The standalone factory borrows Handler's
TACTIC authentication/configuration. Keep one runtime per script/service and
close it at shutdown.

Inside an already connected DCC:

```python
from tactic_handler_api import get_api

th = get_api()
operation = th.submit(lambda: th.project("demo").stype("types/object").get(code="O1"))
# In a later command:
if operation.done:
    print(operation.result().get_info())
# The Maya runtime owns and closes this borrowed API.
```

This reuses the same thin-client connection. TACTIC queries, repository downloads
and uploads run in Handler, not Maya. To own a separate API lifetime, use
`from tactic_handler_api import from_client` then
`th = from_client(maya.runtime().client)` and close it at teardown.
Closing that API closes its executor and remote handles, not the borrowed DCC
connection. Handles are isolated per API session; `release()` frees a specific
remote handle. The service bounds sessions to 64 and handles to 4096 per session,
and expires inactive abandoned sessions after 30 minutes on the next request.

## Object tree and returns

The following surface is available in local Python and the DCC API.
A repeated return type refers to the same subtree below;
`dict`, `list`, `tuple` and scalar values are data, not additional method owners.
`Native*` identifies existing Handler objects exposed through the remote
allowlist. Their common public methods are expanded here;
additional local-only `thlib` internals are not part of this contract.

```text
th
├─ projects() -> list[Project]
├─ project(project_code) -> Project
│  ├─ get_code() -> str
│  ├─ get_info() -> mapping of project fields
│  ├─ stypes() -> list[SType]
│  ├─ stype(search_type) -> SType
│  │  ├─ get_code() -> str
│  │  ├─ get_info() -> mapping of Search Type fields
│  │  ├─ get_project() -> Project
│  │  ├─ get_columns_info() -> {column: metadata dict}
│  │  ├─ get(code=... | id=...) -> SObject
│  │  ├─ new(values, parent=..., relation=..., direction=...) -> unsaved SObject
│  │  ├─ query(filters, order_by=..., limit=50, offset=0,
│  │  │        include_snapshots=False) -> SearchResult
│  │  │  ├─ items -> tuple[SObject, ...] (objects loaded by this query)
│  │  │  ├─ offset, limit -> int
│  │  │  ├─ total -> int | None (total matching count, when available)
│  │  │  ├─ has_more -> bool
│  │  │  └─ next() -> SearchResult (explicitly load the next portion)
│  │  ├─ pipelines() -> list[NativePipeline]
│  │  │  └─ each NativePipeline
│  │  │     ├─ get_info() -> dict (code, search_type, pipeline XML, ...)
│  │  │     ├─ get_all_pipeline_names() -> list[str] (process names)
│  │  │     ├─ get_all_tasks_pipelines_names() -> list[str] (task pipeline codes)
│  │  │     ├─ get_all_pipeline_process() -> list[dict] (config/process records)
│  │  │     ├─ get_pipeline_process(process_code) -> process record dict | None
│  │  │     ├─ get_process_info(process) -> XML node attributes dict | None
│  │  │     ├─ get_processes_info_by_type(type) -> list[node attributes dict]
│  │  │     └─ get_process_label(process) -> str
│  │  ├─ schema() -> NativeSchema | None
│  │  │  ├─ get_info() -> dict (schema search_type node attributes)
│  │  │  ├─ get_parents(), get_children() -> list[connection dict]
│  │  │  ├─ get_child(child_stype, parent_stype) -> connection dict | None
│  │  │  ├─ get_parent(parent_stype, child_stype) -> connection dict | None
│  │  │  ├─ get_child_instance(instance_type, related_type) -> connection dict | None
│  │  │  └─ get_parent_instance(instance_type, related_type) -> connection dict | None
│  │  └─ definitions -> DefinitionCatalog (Search Type scope; expanded below)
│  ├─ workflow() -> NativeWorkflow
│  │  ├─ get_all_pipelines() -> {search_type: {pipeline_code: NativePipeline}}
│  │  ├─ get_by_stype_code(code) -> {pipeline_code: NativePipeline} | None
│  │  ├─ get_by_pipeline_code(stype_code, pipeline_code) -> NativePipeline | None
│  │  ├─ get_by_process_node_type(stype_code, node_type) -> NativePipeline | None
│  │  ├─ get_child_pipeline_by_process_code(parent_pipeline, process)
│  │  │    -> NativePipeline | None (task/child pipeline; same pipeline methods)
│  │  └─ get_pipeline_by_parent(parent_process) -> NativePipeline | None
│  ├─ download_scripts() -> list[dict] (script records; also stores files locally)
│  └─ definitions -> DefinitionCatalog (project scope)
│     ├─ list(search_type=..., view=..., login=..., limit=100, offset=0)
│     │    -> list[Definition]
│     ├─ get(config_code) -> Definition
│     ├─ new(view, xml, search_type=..., login="") -> unsaved Definition
│     │  └─ Definition (same for list/get)
│     │     ├─ code, search_type, view, login, xml -> stored identity and XML
│     │     ├─ set_xml(xml), validate() -> None
│     │     ├─ element(name) -> DefinitionElement
│     │     │  ├─ name -> str
│     │     │  ├─ set_attribute(name, value) -> None
│     │     │  ├─ set_widget(section, class_name) -> None
│     │     │  └─ set_option(section, name, value) -> None
│     │     └─ commit() -> this Definition
│     └─ resolve(view, search_type=...) -> ResolvedDefinition (read-only)
│        └─ search_type, view, xml -> str
├─ sobject(search_key) -> SObject
│  ├─ get_code() -> str | None (new objects may not have a code)
│  ├─ get_search_key() -> str (requires a saved object)
│  ├─ get_project() -> Project
│  ├─ get_stype() -> SType
│  ├─ get_info() -> mapping (including staged changes)
│  ├─ get_value(column) -> field value
│  ├─ changes() -> dict of staged values
│  ├─ set_value(column, value), discard_changes() -> None
│  ├─ commit(), refresh() -> this SObject
│  ├─ related(search_type=..., direction="child", filters=...) -> list[SObject]
│  ├─ tasks(process=None) -> list[SObject] (sthpw/task; same edit/commit methods)
│  ├─ notes(process=None, context=None) -> list[SObject] (sthpw/note)
│  ├─ snapshots(process=None) -> list[Snapshot] (expanded below)
│  ├─ dependencies() -> {search_type: {search_key: NativeSObject}}
│  │  └─ each NativeSObject (read-only remote surface)
│  │     ├─ get_info() -> dict
│  │     ├─ get_code(), get_search_key() -> identity
│  │     └─ get_value(column) -> field value
│  └─ delete(dependencies=...) -> list[dict] of deleted records; immediate server write
├─ snapshot(search_key) -> Snapshot
│  ├─ get_info() -> mapping of snapshot fields
│  ├─ get_code(), get_search_key() -> str
│  ├─ get_version() -> version from TACTIC
│  ├─ is_latest() -> native latest flag
│  ├─ is_versionless() -> bool
│  ├─ get_previewable_files_objects() -> list[NativeFile]
│  └─ get_files_objects() -> list[NativeFile]
│     └─ each NativeFile (also returned by preview accessors)
│        ├─ get_info(), get_dict() -> file record dict
│        ├─ get_code(), get_search_key(), get_unique_id() -> native identity
│        ├─ get_value(column) -> field value
│        ├─ get_type(), get_base_type(), get_ext() -> str
│        ├─ get_filename_with_ext(), get_filename(), get_filename_no_type_prefix() -> str
│        ├─ get_repo_path(), get_abs_path(), get_full_abs_path() -> local path str
│        ├─ get_web_path(), get_full_web_path() -> URL str
│        ├─ get_file_size(check_real_size=False) -> size
│        ├─ get_md5() -> str
│        ├─ get_timestamp(obj=False, pretty=False, simple=False) -> native timestamp
│        ├─ get_metadata() -> decoded metadata or original stored value
│        ├─ is_exists(), is_local_current(timestamp_tolerance=2.0), is_previewable() -> bool
│        ├─ get_web_preview(), get_icon_preview() -> NativeFile | None (not URL)
│        └─ get_meta_file_object() -> NativeFileObject | None (expanded under files)
├─ logins() -> list[NativeLogin]
├─ login(login_name) -> NativeLogin
│  ├─ get_info() -> dict
│  ├─ get_login(), get_code(), get_project_code(), get_display_name() -> str
│  ├─ check_security(group, path, project=None) -> native access value | None
│  ├─ get_login_groups() -> list[NativeLoginGroup] (membership)
│  ├─ get_all_login_groups() -> list[NativeLoginGroup] (all loaded groups)
│  └─ get_login_group(login_group_code) -> NativeLoginGroup | None
│     ├─ get_info() -> dict
│     ├─ get_code(), get_login_group(), get_pretty_name() -> str
│     └─ get_description() -> stored description
├─ files -> FilesAPI
│  ├─ match(paths, templates=None) -> list[NativeFileObject]
│  │  └─ each NativeFileObject (matched file/sequence/UDIM group, not a DB File)
│  │     ├─ get_all_files_list(first=False, filenames=False, no_ext=False) -> list[str] | str
│  │     ├─ get_name_part(), get_file_ext(), get_pretty_file_name(), get_type() -> str
│  │     ├─ get_sizes_list(together=False, files_list=None) -> list[size] | total size | None
│  │     ├─ get_metadata() -> dict (template, frames/tiles, app_info when present, ...)
│  │     └─ is_previewable() -> bool
│  ├─ ensure_local(file, overwrite="cancel", verify_md5=False) -> Path
│  ├─ open(file) -> Path (download if needed, then native opener)
│  └─ reveal(file) -> Path (show folder)
├─ repositories -> RepositoriesAPI
│  ├─ list() -> list[repository dict]
│  ├─ get(repository_code) -> repository dict
│  └─ sync(snapshot_or_files, overwrite="cancel", verify_md5=False) -> list[Path]
├─ commit_queue(project_code=None) -> CommitQueue (no window required)
│  ├─ get(operation_id) -> QueueItem
│  ├─ items(search_key=None, state=None) -> list[QueueItem]
│  ├─ add(target, context=..., files=..., repository=..., description=..., ...)
│  │    -> QueueItem (prepared, not uploaded)
│  │  ├─ id -> str
│  │  ├─ state -> str
│  │  ├─ set_description(text) -> None
│  │  ├─ commit() -> Snapshot (confirmed check-in)
│  │  ├─ submit() -> Operation[Snapshot]
│  │  └─ remove() -> None
│  └─ remove_completed() -> int (removed count)
├─ ui -> UIAPI (optional; no QObjects exposed)
│  ├─ show() -> Operation[UIAPI]
│  ├─ checkin_files(search_key, context, description, paths) -> Operation[UIAPI]
│  ├─ project(project_code) -> ProjectUI
│  │  ├─ project_code -> str
│  │  ├─ show() -> Operation[ProjectUI]
│  │  └─ commit_queue() -> WindowUI
│  ├─ sobject(search_key_or_object) -> SObjectUI
│  │  ├─ identity -> SearchKey
│  │  ├─ show() -> Operation[SObjectUI]
│  │  ├─ snapshots(), notes(), tasks() -> DockUI (with target navigation)
│  │  └─ commit_queue() -> WindowUI (with target navigation)
│  ├─ window(window_id) -> WindowUI
│  │  ├─ id -> str
│  │  └─ show() -> Operation[WindowUI]
│  └─ dock(dock_id) -> DockUI
│     ├─ id -> str
│     └─ show() -> Operation[DockUI]
├─ submit(callable, *args, **kwargs) -> Operation[result type]
│  ├─ id, state -> str
│  ├─ done -> bool
│  ├─ result() -> result (does not wait)
│  ├─ wait(timeout=None) -> result (worker/CLI only while pending)
│  ├─ cancel() -> bool (pending work only)
│  └─ on_done(callback), on_error(callback), on_progress(callback)
│     -> Subscription (each accepts dispatch=...)
│        ├─ close() -> None (disconnect observer)
│        └─ error -> callback exception | None
└─ close(wait=True) -> None
```

`SearchResult` contains the found sObjects, their total count and loading parameters.

Query limits are 1–1000. Loading more is explicit; reading local `items` never
fetches additional records. A final `next()` returns an empty `SearchResult`
without another TACTIC query. The remote call still crosses the DCC transport.
Ordering includes an identity tie-breaker; offset-based loading is not a
transactional snapshot of changing data.

```python
# CLI/worker, or inside th.submit(...):
result = th.project("demo").stype("types/object").query(limit=50)
for sobject in result.items:
    print(sobject.get_code())
if result.has_more:
    result = result.next()
```

SObject field getters read a local copy, including in Maya. Local `get_info()`
returns a read-only mapping with copied values. Other remote handles (including
SearchResult properties) make explicit RPC calls and belong in submitted work.
Native objects returned by `pipelines`, `schema`, `workflow`,
`logins` and file accessors retain their native methods; their remote methods
can perform I/O and should stay inside submitted work. Their remote surface is
the explicit allowlist in `tactic_handler_api/contract.py`, not arbitrary Python
attribute access.

`SearchKey.parse(text)` is an additional import-level helper, not a service on
`th`. It returns `SearchKey` with `search_type`, `project_code`, `column` and
`value`; `str(key)` produces its normalized TACTIC search key.

### Where the nested metadata ends

- **Workflow and pipelines:** lookup methods return native Pipeline objects;
  process lookups return plain dictionaries. `get_all_pipeline_names()` is a
  historical name for **process names**, not pipeline codes.
  `get_pipeline_process(process_code)` matches the process record's `process`
  field (its name), not the record's database `code`. Its result contains native
  `config/process` fields. `get_process_info(process)` instead reads XML node
  attributes such as `name`, `type`, `label`, `color`, `task_pipeline` and the
  connection attributes retained by the native parser. A task pipeline uses
  the same Pipeline API; its process names describe its configured statuses.
  `get_by_process_node_type` treats `None`/`manual` as `task`. Pipeline lookup by
  code/node type requires a known Search Type; native methods can raise for an
  unknown type. These objects do not expose `commit()` or a process/status editor.
- **Schema:** `get_info()` is the schema's `search_type` XML node attributes,
  not an XML document or database column catalog. Relationship methods return
  `connect` attribute dictionaries (`from`, `to`, and server-defined attributes
  such as `relationship`, `from_col`, `to_col`, `instance_type`, `path` when
  present). These are descriptors, not linked sObjects. Obtain actual related
  records through `sobject.related(...)`. Schema absence returns `None`; this
  surface does not provide schema mutation methods.
- **Dependencies:** `dependencies()` preserves the native result grouped by
  related Search Type and then search key. It discovers related children, not
  a recursively expanded dependency graph. Its values are **NativeSObject**,
  not the staged **SObject** wrapper. For editing, resolve the identity with
  `th.sobject(dependency.get_search_key())`, then use `set_value`/`commit`.
  Do not pass the returned object mapping directly to `delete(dependencies=...)`;
  that argument is a collection of related Search Type strings explicitly
  selected for deletion, not individual dependency objects or search keys.
- **Files:** preview accessors return File objects, not image URLs or pixels;
  continue through `get_full_web_path()` or `files.ensure_local(...)`. The matched
  FileObject is a separate native file-group description. With `first=True`,
  `get_all_files_list` returns one path string; with `filenames=True` it returns
  a list regardless of `first`. `get_sizes_list` can return `None` when no sizes
  are found.

The following chain is available in a worker, including over the DCC connection:

```python
project = th.project("demo")
workflow = project.workflow()
pipeline = workflow.get_by_pipeline_code("types/object", "main")
if pipeline is not None:
    for process in pipeline.get_all_pipeline_names():
        print(process, pipeline.get_process_info(process))
        task_pipeline = workflow.get_child_pipeline_by_process_code(pipeline, process)
        if task_pipeline is not None:
            print("Task statuses:", task_pipeline.get_all_pipeline_names())
```

The codes in this example are placeholders. A process does not necessarily have
a child/task pipeline; `None` is a valid result. No labels are translated by the
public API.

## Read, edit, commit

```python
def rename(th, search_key, name):
    sobject = th.sobject(search_key)
    sobject.set_value("name", name)      # Local staged value, no write.
    print(sobject.changes())
    sobject.commit()                    # Waits for server confirmation.
    return sobject

operation = th.submit(rename, th, "types/object?project=demo&code=O1", "New name")
```

Failed commits retain staged changes; they do not publish them into native UI
objects. Refreshing a dirty editor raises `DirtyObject`; commit or discard first.
Concurrent mutation of the same editor during commit/refresh raises
`ConcurrentEdit`. This protects the local editor, not simultaneous edits by other
users on the server. Server permissions, validation and triggers remain native.

```python
def create_child(th, parent_key, pipeline_code):
    stype = th.project("demo").stype("types/object")
    child = stype.new(
        {"name": "New object", "pipeline_code": pipeline_code},
        parent=parent_key,
        relation="types/object_in_object",  # Actual schema instance type.
        direction="child",
    )
    return child.commit()
```

Creation forwards form values, parent and relationship to native
`insert_sobjects`; it does not guess or substitute a pipeline. New objects have
no usable search key until committed. Existing identities cannot be edited.
Deletion is explicit and immediate; inspect `dependencies()` before passing
the native dependency selection to `delete()`.

## Explicit background operations

Data methods are synchronous and return their documented value. `submit()` moves data work
to a worker. UI `.show()` commands always return an `Operation` and own their
dispatch; they are safe to call directly from Qt/Maya's GUI thread.

```python
operation = th.submit(th.sobject, "types/object?project=demo&code=O1")
print(operation.id, operation.state, operation.done)
# Worker/CLI only:
sobject = operation.wait(timeout=30)
```

States: `queued`, `running`, `finished`, `failed`, `cancelled`.
`result()` never waits: before completion it raises `NotReady`; afterward it
returns the value or raises the original exception. `wait()` is forbidden on a
known Qt/Maya UI thread while unfinished. A wait timeout does **not** cancel the
operation or roll back a server write. `cancel()` cancels only work that has not
started and reports whether cancellation succeeded.

Defaults: four workers and at most 64 outstanding operations; overflow raises
`QueueFull`. Chain synchronous calls inside one submitted function. Submitting
again from that executor's own worker is rejected to prevent nested-wait
deadlocks. A UI `.show()` inside an existing API worker uses that worker and
returns a completed `Operation` after its commands are accepted, without nested
submission. Closing cancels pending work; running operations are not forcibly
interrupted: they can finish their remaining synchronous steps before remote
handles are released. Use `close(wait=False)` on a GUI thread. Closing waits for
this runtime's submitted work, not independently managed external threads.
Custom scripts launched by the Maya runtime keep their legacy synchronous flow;
that exception is scoped to the script execution and does not relax other UI calls.

```python
# Maya example: callbacks touching Maya/UI must be explicitly dispatched.
import maya.utils

subscription = operation.on_done(
    lambda obj: print(obj.get_code()),
    dispatch=maya.utils.executeDeferred,
)
# Also available: on_error(callback, dispatch=...), on_progress(...).
# Disconnect during owner/window teardown:
subscription.close()
```

Without `dispatch`, callback thread affinity is unspecified (completion thread,
or registration thread for an already finished operation). Callbacks receive
one argument. Progress is best-effort data, not a delivery-guaranteed event log;
headless transfers/check-in emit progress, while desktop/remote progress remains
in their existing queue views. Observer errors are retained as
`subscription.error` and cannot turn a successful commit into a failed one.
Disconnect callbacks when their UI owner/selection becomes obsolete. No callback
implicitly switches to the Qt thread.

## Snapshots, files and repository sync

```python
def download_snapshot(th, snapshot_key):
    snapshot = th.snapshot(snapshot_key)
    print(snapshot.get_code(), snapshot.get_version())
    return th.repositories.sync(snapshot, overwrite="cancel", verify_md5=True)

operation = th.submit(download_snapshot, th, "sthpw/snapshot?code=SNAPSHOT001")
```

`Snapshot` exposes `get_info`, `get_code`, `get_search_key`, `get_version`,
`is_latest`, `is_versionless`, `get_files_objects`, and
`get_previewable_files_objects`. File accessors return native `File` objects.

- `th.files.match(paths, templates=None)` → native matched FileObjects.
- `th.files.ensure_local(file, overwrite="cancel", verify_md5=False)` → `Path`.
- `th.files.open(file)` → ensure local, then native file opener; `Path`.
- `th.files.reveal(file)` → native folder opener; `Path`.
- `th.repositories.list()` → active native repository records.
- `th.repositories.get(repository_code)` → a configured repository record.
- `th.repositories.sync(snapshot_or_files, ...)` → `list[Path]`.

Overwrite decisions are explicit: `cancel`, `skip`, `overwrite`. `skip` may
return a stale local file. Freshness uses native metadata; received bytes are
validated against HTTP response size, not a potentially stale discovery size.
The downloader is shared with Repository Sync. Each operation owns its staging
path, so one runtime never deletes another runtime's partial transfer. This API
syncs explicitly supplied files/snapshots; it does not yet expose the UI's
recursive scope/preset discovery as a new high-level API.

## Commit Queue without a window

```python
def prepare(th, search_key, source_path, repository_code):
    queue = th.commit_queue("demo")
    return queue.add(
        search_key, context="publish/main", files=[source_path],
        repository=repository_code, description="First version",
        file_type="file", mode="upload", generate_previews=False,
    )

# CLI/worker:
item = prepare(th, "types/object?project=demo&code=O1", source_path, repository_code)
item.set_description("Ready")
snapshot = item.commit()
# Alternatively, outside an already submitted function:
# operation = item.submit()
```

`add()` prepares a queue entry but does not upload. `QueueItem.commit()` returns a
confirmed, file-hydrated `Snapshot`. `QueueItem.submit()` is shorthand for
`th.submit(item.commit)`. Source paths must be readable by the standalone
Handler. The API does not reinterpret Maya paths or invoke DCC scene-save as part
of this file-based operation.

Additional `add` options: `version`, `is_revision`, `update_versionless`,
`keep_file_name`, `generate_previews`; modes `upload`, `copy`, `preallocate`.
Defaults do not change versionless snapshots. `files` is a collection of paths,
not one string. Regular files are matched independently; queue submission of
custom sequence/UDIM templates is not yet exposed.

Inspect `queue.items(search_key=..., state=...)`, `queue.get(operation_id)` and
`item.state`; edit `item.set_description(text)`, remove `item.remove()` or
`queue.remove_completed()`. Project-scoped queues reject foreign-project items.
Duplicate prepared check-ins are rejected. A completed item retains its server
result, so calling `commit()` again on that item does not upload twice.

Ownership differs deliberately:

| Runtime | Queue owner | Lifetime |
|---|---|---|
| `get_api()` in Handler | Existing desktop CommitQueueController | Existing queue persistence and UI |
| `get_api()` in Maya / `from_client(...)` | Same desktop queue through domain RPC commands | Existing Handler application |
| `local()` without a queue gateway | One headless queue | In-memory, owned by that API runtime |

Editing one item by id ignores the UI's
bulk-selection setting. A result remains available after desktop auto-clean
(bounded terminal cache: 1000 items). Application shutdown disconnects the bridge
and fails pending waiters.

Headless execution serializes check-ins and reuses native naming, file staging
and server transactions. It marks an execution error `uncertain` and refuses an
automatic retry: a lost reply may follow a successful server-side write. Verify
the server before making a new check-in. This is not server-side exactly-once
delivery or a persistent headless job service.

Headless data, XML, downloads and file check-in can run without Qt. Generating
image previews still uses the existing Qt image codecs (no windows/event loop);
set `generate_previews=False` when Qt is not installed. Native file/folder
openers naturally require a desktop environment.

## Table and EditSobject definitions

```python
def adjust_edit_definition(th, config_code):
    catalog = th.project("demo").stype("types/object").definitions
    definition = catalog.get(config_code)
    element = definition.element("category_code")
    element.set_widget("display", "SelectWdg")
    element.set_option("display", "values_expr", "@GET(types/category.code)")
    element.set_option("display", "labels_expr", "@GET(types/category.name)")
    element.set_option("display", "empty", "-- Select --")
    definition.validate()
    return definition.commit()
```

`project.definitions.list(search_type=None, view=None, login=None, limit=100,
offset=0)` returns exact saved records across Search Types. An SType catalog adds
its type filter. `get(config_code)` addresses one record, including its login
scope, not all records sharing a view name. New records use
`catalog.new(view, xml, search_type=..., login="")` then `commit()`.

Definitions expose `code`, `search_type`, `view`, `login`, `xml`, `set_xml`,
`validate`, `element` and `commit`. Elements support `set_attribute`,
`set_widget("display" | "edit", class_name)` and `set_option(section, name, value)`.
Expressions remain server expressions; they are not evaluated or flattened.
Unknown elements/attributes and comments survive structural editing, although
XML whitespace/serialization may change. Duplicate element names within a view
are rejected. Ambiguous element names across views require explicit XML editing.

`catalog.resolve(view)` returns a read-only `ResolvedDefinition` from the native
project ViewsConfig lookup. It does not claim to reproduce the server's complete
merged widget-resolution engine. Never save a resolved result over an arbitrary
record. Saving targets the concrete `config/widget_config` and invalidates
reference metadata; definitions should have one editing owner at a time.

## Optional UI

Retrieving a UI handle has no navigation side effect. `.show()` owns scheduling
and returns `Operation[handle]` in every execution context. Call it directly:

```python
th.ui.show()
th.ui.project("demo").show()
th.ui.sobject("types/object?project=demo&code=O1").notes().show()
th.ui.window("commit_queue").show()
```

These are independent examples, not an ordered navigation script. To select a
target and show its queue in order, use one scoped command:

```python
operation = th.ui.project("demo").commit_queue().show()
# In a later GUI command, after operation.done becomes True:
queue_window = operation.result()
print(queue_window.id)  # commit_queue
```

UI commands use the session's executor and desktop dispatcher. Remote commands
use the DCC connection.
Qt objects never leave the UI thread. Errors remain on the operation and are
available through `result()`/`on_error(...)`. Cancellation and session shutdown
use the ordinary Operation contract. Callbacks retain their explicit dispatch
rules; a pending `wait()` still must not run on the GUI thread.

Object handles also have `.snapshots()`, `.tasks()` and `.commit_queue()`;
project handles have `.commit_queue()`. `ui.dock(dock_id)` and
`ui.window(window_id)` use registered Handler identifiers. They are command
handles, not leaked QObjects or arbitrary widget lookups. One scoped operation
issues navigation before its window/dock command; a failed navigation stops the
remaining steps. Completion means native commands were accepted, not that all
asynchronous data loading/rendering has finished.
Object/project queue handles navigate before showing the shared queue; they do
not promise a separate or filtered queue instance. A headless runtime returns an
operation failed with `UIUnavailable`. Business operations never call `.ui`
implicitly.

## Availability and verification

Recursive repository presets, messaging/administration/settings and arbitrary
search-tab/editor controls are not exposed by this API. Use `maya.cmds` for
native Maya scripting and Handler for TACTIC operations.
See [DCC startup and scripts](dcc_api.md).

Bundled project-specific custom scripts require adaptation before use. Import
`get_api()` explicitly; the launcher supplies only `TACTIC_PROJECT_CODE` and
`TACTIC_SCRIPT_KWARGS` and never changes the process-wide current project.

Implementation ownership:

- `tactic_handler_api`: explicit domain façade, staged values, bounded execution.
- `thlib.checkin_operation`, `thlib.repository_download`: shared native execution.
- `thlib.ui.api_bridge`: Qt-thread marshalling to the existing queue owner.
- `thlib.ui.tactic_rpc`: only `handler.call`, `handler.release`, `handler.close`;
  the call target/member must belong to the explicit domain contract. There is
  no module import, arbitrary public getter, or global environment gateway.

The composition root attaches the shared queue/runtime before accepting script
work. Maya shutdown drains submitted API work off its UI thread before stopping
the borrowed transport. The operator currently executes incoming domain commands
serially; multiple submitted DCC calls are not parallel TACTIC transactions.

Run the focused regression suite with the repository Python environment:

```console
python -m unittest tests.test_handler_api tests.test_handler_api_services tests.test_handler_api_headless tests.test_handler_api_desktop tests.test_tactic_dcc_sdk tests.test_script_editor tests.test_environment_import tests.test_checkin_operation tests.test_checkin_vertical tests.test_commit_queue tests.test_repository_sync
```

Tests cover actual native object wrappers, local HTTP transfer, real staged files,
the Qt queue model/dispatcher, direct UI calls from the Qt thread, ordered scoped
commands and cancellation, nested workflow/pipeline/schema/dependency results,
SearchResult continuation, the real thin-client TCP transport, and a subprocess
that rejects Qt/UI imports. TACTIC server mutations and Maya-native execution are
isolated; this suite does not replace acceptance against a live TACTIC/Maya setup.
