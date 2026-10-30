# Existing TS server operations

Read only the sections needed for the current task. This is a reference for the
agent and its host executor, not a list of new MCP tools. The host must bind
allowed actions to these exact server operations and keep the ticket private.
An operation absent from the host's tools cannot be invoked by naming it here.
These calls execute on Stream. TH's `get_api()` / `local()` and native object
methods belong to a different client API: see [TH references](SOURCES.md#th-client-api-and-structures).
Do not send a Handler object or handle as an HTTP payload, or assume a browser
endpoint is a method on a TH object.
References: [TS API source index](SOURCES.md#ts-server-api),
[server methods](../../src/tactic_stream/server/api.py),
[SDK](../../src/tactic_client_lib/tactic_server_stub.py),
[transport guide](../../frontend/public/help/api_compatibility.en.md).

## Transport and discovery

`GET /api/documentation` returns `methods[]` with `name`, `status`, `parameters`,
`signature`, `writes`, examples and compatibility information. Use this for SDK
method arguments. The signature of `execute_cmd` does not describe each command's
payload; use the command contracts below. There is no published `context.get`,
`projects.prepare` or `changes.apply` service in this baseline.

All relative URLs are on the selected TACTIC server. JSON requests use
`Content-Type: application/json` and the server's normal origin/auth rules.

```json
{
  "method": "execute_cmd",
  "args": [
    {"ticket": "<injected by host>", "project": "city", "language": "python"},
    "tactic.ui.panel.search_types_cmd.SearchTypesCmd",
    {"action": "list", "project_code": "city"}
  ],
  "kwargs": {}
}
```

Send this to `POST /admin/rpc`. Its HTTP body wraps the result in `result`.
`execute_cmd` then returns `{status, description, info}`: editor data is in
`result.info`. Other RPC methods have their own result shape. HTTP editor routes
below also wrap their return value in `result` but do not add a Command envelope.
Do not mix the two levels. Handle error responses before reading `result`.

Existing XML-RPC uses `/tactic/{project}/Api/` with the original method contract;
the official SDK handles its encoding. Do not assume raw XML-RPC `query` and
plain JSON `query` have identical wire representations.

In the notation below, **auth** is the host-owned dictionary containing ticket,
project and language. **C(class, args)** means the existing `execute_cmd` with
auth and the fixed class; it returns `info`. It is notation, not an API name.

## Read the selected project

| Need | Existing call | Use the result |
| --- | --- | --- |
| Projects | `POST /admin/project-catalog` with `{ticket, project}` | Project codes, titles, type/mode and visibility. |
| Available templates | `POST /admin/project-creation` with `{ticket, project}` | `templates`, `installedTemplates`, themes and existing codes. This endpoint does not create anything. Resolve returned package references in the host. |
| SearchTypes | `C(SearchTypesCmd, {action:"list", project_code})` | `catalog`: identity, namespace, table/database, project-local flag and relationships. |
| One type/columns | `C(SearchTypesCmd, {action:"load", project_code, identity})` | `document`, `metadata.columns`, `metadata.relationships`, revision, write capability and pipeline references. |
| Schema | `C(SchemaCmd, {action:"load", project_code})` | Current project XML/document and revision; also inspect inherited relations in the type catalogue. |
| Pipelines | `C(WorkflowCmd, {action:"list", project_code})`, then `load` with identity | Current scope, document and metadata. |
| Config sources | `POST /admin/widget-configuration/read` with `{ticket, project, search_type, view}` | `sources`, `layers`, `resolved`, `revision`, views and layout templates. |
| Effective interface | `POST /admin/interface` with `{ticket, project, search_type, view}` | Columns, resolved table/elements, support flags and operations. |
| Form | `POST /admin/form` with `{ticket, project, search_type, view}`; optional `search_key` | Actual insert/edit configuration and values; use the correct named form. |
| Navigation | `POST /admin/navigation` with `{ticket, project}` | Resolved navigation. For editable source layers use widget configuration with `search_type:"SideBarWdg"`. |
| Small data sample | RPC `query(auth, search_type, ...)` using discovered parameters | Explicit allowed columns, stable ordering, limit/offset and project scope. Never use all rows as routine context. |

Full fixed command paths:

Owners: [SearchTypes](../../src/tactic/ui/panel/search_types_cmd.py),
[Schema](../../src/tactic/ui/panel/schema_cmd.py),
[Workflow](../../src/tactic/ui/panel/workflow_cmd.py),
[Naming](../../src/tactic/ui/panel/naming_cmd.py).

```text
SearchTypesCmd = tactic.ui.panel.search_types_cmd.SearchTypesCmd
SchemaCmd      = tactic.ui.panel.schema_cmd.SchemaCmd
WorkflowCmd    = tactic.ui.panel.workflow_cmd.WorkflowCmd
NamingCmd      = tactic.ui.panel.naming_cmd.NamingCmd
```

Suggested retrieval order: project/template choices -> type catalogue -> only
relevant types and schema -> relevant views/forms/navigation -> relevant
pipelines/naming -> bounded sample rows. Store each source's identity and revision.
Fetch scripts or unrelated configuration only when needed and authorized.

## Create or instantiate a project

`C("tactic.command.CreateProjectCmd", args)` accepts, among other existing keys:

```json
{
  "project_code": "review_template",
  "project_title": "Review template",
  "project_type": "review_template",
  "is_template": true
}
```

Codes match `[A-Za-z_][A-Za-z0-9_]{0,29}`; nonempty supplied titles are at most
100 characters. `project_type` is the namespace/type, not a database vendor.
`is_main_project` changes the installation default: omit it unless requested.
To create the dedicated file workspace use `project_mode:"file_project"`;
do not mix that mode with arbitrary project types/themes/search-type lists.

For an existing template:

```json
{
  "project_code": "review_delivery",
  "project_title": "Review delivery",
  "template_code": "review_template",
  "new_project": true,
  "is_template": false
}
```

Call `tactic.command.ProjectTemplateInstallerCmd`. A packaged template may also
require `path` from the server's discovered catalogue, resolved by the host.
Do not let a model guess filesystem paths. With a registered template project
and no explicit path/version, the installer can export that project first.
`new_project:false` imports into an existing project; it is not the default
choice for a create request. `mode:"move"` and the separate
`ProjectTemplateUpdaterCmd` are unsupported here.

After success, switch subsequent requests to the returned/created project and
re-read its catalogue. Do not blindly retry after connection loss. Check whether
the intended project exists and what was actually configured.

## Create/edit types and relationships

SearchTypesCmd `save` takes `project_code`, optional existing `identity`,
`expected_revision`, optional `schema_revision`, and `document`:

```json
{
  "title": "Review Item",
  "description": "An item submitted for review",
  "color": "#668899",
  "hasPipeline": true,
  "columns": [{"name": "priority", "type": "integer"}],
  "removedColumns": []
}
```

For a new type, this editor derives its identifier from the title. Consume
returned `identity`; do not assume the label and code are identical. If the
request requires an exact predefined identifier, use the discovered native
`create_search_type` contract and verify its registered result.

`columns` is a list of **additions**, not all existing columns. Allowed addition
types here are `varchar(256)`, `text`, `integer`, `numeric`, `boolean`, `timestamp`.
Names are unique lowercase identifiers. For edits, start with the returned
document, preserve title/description/color, add only new columns and pass its
revision. Omitting descriptive fields can clear them. Column deletion is a
distinct requested change and may be blocked by schema/identity dependencies.

SchemaCmd `save` takes `project_code`, `document` and `expected_revision`:

```json
{
  "xml": "<schema>...the complete edited current schema...</schema>",
  "createColumns": [{"from":"review/shot","to":"review/sequence","path":""}],
  "newTypes": {}
}
```

The XML must contain the intended connection with correct columns and existing
nodes. `createColumns` explicitly requests missing relationship columns; it is
not a replacement for the XML connection. A typical code edge is:

```xml
<connect from="review/shot" to="review/sequence"
         relationship="code" type="hierarchy"
         from_col="sequence_code" to_col="code"/>
```

Use actual registered types. Preserve the rest of the loaded schema. Instance
types use a corresponding XML node and two links plus `newTypes`; consult the
returned relation metadata before authoring many-to-many structures.

## Configure a pipeline

WorkflowCmd `new` with `identity` set to a SearchType returns a starter document
and metadata; `load` takes a pipeline identity. Save the complete returned
document, not just its visual node names. Main document fields are `name`,
`description`, `color`, `searchType`, `xml`, `processSettings`,
`processDescriptions`. Existing saves require identity and expected revision.

For a simple new manual pipeline, the ordinary RPC `create_pipeline` also
accepts name, SearchType and a list of processes. It returns a pipeline record.
Assign its returned `code` to the intended object's `pipeline_code`; use
`add_initial_tasks`/`create_task` under their discovered contracts if tasks are
requested. These are separate effects. Do not activate generated callbacks as a
side effect of creating a manual workflow.

## Change a view with validation and preview

Read `/admin/widget-configuration/read` first. Select the exact editable source
ID; use `source_id:null` only when deliberately creating a new source. The
payload for `check`, `preview` and `save` is:

```json
{
  "ticket": "<injected by host>",
  "project": "review_template",
  "search_type": "review_template/review_item",
  "view": "agent_review",
  "source_id": null,
  "xml": "<config><agent_review><element name=\"code\"/><element name=\"name\"/></agent_review></config>",
  "revision": "<exact revision from read>"
}
```

Send to `/admin/widget-configuration/check`, then `preview`, then authorized
`save`. Check returns `valid`, revision and diff; preview also returns `interface`.
Inspect its supported elements and present it in the normal client renderer.
The current service accepts a view-sized draft, not a project-wide atomic plan.
Save returns fresh configuration/revision. On conflict re-read and reconcile.

`/admin/columns-editor/read` returns the saved-definition catalogue including XML
that may not be renderable. Its `save` uses `source_id`, `xml`, `revision` plus
ticket/project. That revision is from this catalogue, not widget-configuration.
An unknown column/handler must be diagnosed, not replaced with a generic cell.

## Naming and saved scripts

NamingCmd actions are `load`, `preview`, `save`, with `project_code`, base
`search_type` and optional rule `identity`. `save` uses `expected_revision`.
Release 0.112.204 adds `apply` (same draft, revision, sample, canonical UUID
`operation_id`) and `operation` (read that user's durable receipt). Apply
disallows custom execution. Retry the exact payload/ID; changed payloads fail.
Receipts record historical success, not current state: read naming again.
See [connection/apply contract](CONNECTION.md#save-replay-and-revisions).
Read an existing rule's `document` before editing it; omitted fields default to
empty/false. Available rule fields:

```text
search_type, dir_naming, file_naming, sandbox_dir_naming, snapshot_type,
context, latest_versionless, current_versionless, manual_version,
ingest_rule_code, condition, class_name, script_path, checkin_type,
base_dir_alias, sandbox_dir_alias
```

The three version flags are booleans. `checkin_type` is empty, `auto` or `strict`.
Preview sample fields are `key`, `file`, `version`, `process`, `context`,
`fileType`, `snapshotType`. Use a real permitted object's key from this project.
Inspect `results`, matching rule and collisions. Leave `allow_execution:false`
unless explicitly authorized to execute custom naming in the ordinary server.

`/admin/script-editor/read` returns source/path/language/revision for accessible
scripts. Relevant actions include `analyse`, `save`, `history`, `revision`.
Save fields are `code` (empty for create), `folder`, `title`, `language`, `source`,
`revision`, ticket and project. Current editable languages are `python`,
`javascript`, `server_js`; these run in different environments. Follow actual
script input/binding contracts. Do not infer that saving a script has tested or
activated it. Optional host MCP trials are in `th.trials`; they are not server execution.

## Export and verify

`C("tactic.command.ProjectTemplateCreatorCmd", {project_code})` creates/updates
the native template package. The Python command instance has `get_zip_path()`;
the current RPC Command `info` does **not** promise a download URL/path. Do not
invent one in the user-facing result. Discover the package using the existing
catalogue or let the host return the artifact through an authorized facility.

Install under another project code with ProjectTemplateInstallerCmd, then
compare types/fields, schema, views, pipeline references and naming. Re-query
business rows separately: default configuration export does not populate them.
Keep export/import of executable package content within the authorized scope.

## Failures and freshness

Honor permission denials, `canWrite:false`, missing objects, unsupported
operations and revision conflicts. Do not fall back to unrestricted SQL/Python
or delete/recreate an existing resource. An unknown HTTP outcome needs state
inspection; a validation error needs a corrected proposal. Never silently retry
a write with a new identity. No global idempotency key or distributed atomic
rollback is provided by the current editor APIs.
