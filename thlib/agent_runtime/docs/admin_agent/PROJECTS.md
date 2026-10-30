# Projects and reusable templates through an external agent

TS owns these operations. TH consumes the resulting native registry, schema,
pipelines, naming and widget configurations; this is not a TH scripting API.
Read [MODEL](MODEL.md), then this recipe. Use [SOURCES](SOURCES.md) for the separate
TS server, TH client and original database references.

## Describe the outcome, then compose native inputs

Translate the user's description into entities with stable codes, fields,
relationships, process graphs and naming rules. Ask about business ambiguities
(for example whether assets can appear in several shots), not implementation
details the native catalogue already answers. Show the concrete composition
before a write. The model never receives a generic SQL, Python or RPC executor.

Requires TS 0.112.206 and the host flag `--allow-project-create`. Without that
flag only preview/read/operation tools are present. Server administrator checks
remain mandatory. The host-selected existing `--project` is the authorization
and receipt scope; this tool family explicitly accepts a **new target code**.
Other naming/page tools stay bound to the original host project. Rebind the host
to the created project for subsequent page or naming edits.

Example argument to `ts_project_preview(document=...)`:

```json
{
  "code": "studio",
  "title": "Animated short",
  "entities": [
    {"code": "sequence", "title": "Sequences"},
    {"code": "shot", "title": "Shots", "columns": [{"name": "frames", "type": "integer"}]},
    {"code": "asset", "title": "Assets"}
  ],
  "relations": [
    {"source": "shot", "target": "sequence", "source_column": "sequence_code"},
    {"source": "shot", "target": "asset", "instance": "shot_asset", "source_column": "shot_code", "target_column": "asset_code"}
  ],
  "pipelines": [{
    "entity": "shot", "processes": ["layout", "animation", "compositing"],
    "connections": [["layout", "animation"], ["animation", "compositing"]],
    "statuses": ["Waiting", "Working", "Approved"]
  }],
  "naming": [{
    "entity": "shot", "context": "publish",
    "dir_naming": "{project.code}/shots/{code}",
    "file_naming": "{code}_v{version}.{ext}", "checkin_type": "strict"
  }]
}
```

`source` is the child for an ordinary relationship; its named key references
the target's `code`. An `instance` creates a native link SearchType with two
code connections. It does not store a list of foreign IDs in a text field.
Standard columns (`id`, `code`, `name`, `description`, etc.) are supplied by
TACTIC; `columns` contains additions only. Supported types: `varchar(256)`,
`text`, `integer`, `numeric`, `boolean`, `timestamp`. Codes are lowercase ASCII
identifiers, at most 30 characters. Up to 32 entities, 61 extra fields per
entity, 64 relationships, 32 pipelines and 64 naming rules are accepted.

Each entity pipeline uses native manual processes and explicit graph edges.
Optional statuses create a native task pipeline referenced by every process;
they do not create operational tasks. Empty `connections` means independent
processes. Conditional/action scripts and custom process kinds require the
native Workflow editor; this composition input does not authorize code.

Naming uses the existing Naming engine. This input accepts declarative tokens
for native fields (also `sobject.field`), linked parent fields (`parent.field`),
project code/title, snapshot version/context/process,
`version`, `context`, `process`, `ext`, `basefile`, `file_type` and `{###}` padding.
Braces are required: `{code}_v{version}.{ext}` resolves to `SH010_v001.exr`;
bare `###` stays literal and does not increment. Before exporting a populated
project, preview representative naming paths; after installation check a real
file in the destination project before describing the template as verified.
Expressions, custom classes/scripts and conditions are deliberately absent.
Preview validates structure and namespace availability, **not resolved paths**:
an empty project has no representative objects. Before production check-in,
use the ordinary naming preview with real objects and verify collisions.

## Create, inspect, export, install

1. `ts_project_preview(document)` returns the normalized draft and `revision`.
2. `ts_project_create(document, expected_revision, operation_id)` uses that
   exact draft/revision and a fresh canonical UUID. It first creates the native
   database/project, then configures entities, schema, workflows, naming and
   ordinary editable table pages/navigation. It does not populate demo records.
3. `ts_project_read(target)` returns registration/database state, schema XML,
   fields, workflows, naming, navigation and a configuration revision. Check
   the result against the user's description; do not stop at a successful code.
4. `ts_project_export(target, expected_revision, operation_id)` uses the fresh
   read revision. It runs the native template creator and returns a versioned
   ZIP location **on the server**, SHA-256, size and `template_id`. This is a
   configuration template, not a database/repository backup or a download URL.
5. `ts_project_install(template_id, target, title, operation_id)` accepts an
   export receipt belonging to this administrator and host project. It checks
   the saved archive hash and uses the native template installer. Target must
   be new; import into an existing project and arbitrary filesystem paths are
   not exposed. Templates retain their SearchType namespace while project,
   pipeline and repository naming references follow the destination project.

The ZIP can also be used by the ordinary template manager. A project is not
marked as a template merely because its configuration was exported. Explicit
export does not modify the working project's records.

## Failure and retry contract

Use `ts_project_operation(target, operation_id)` after a timeout, lost response
or restart. A completed receipt is historical success and is returned unchanged
for the same request. A different request with that UUID is rejected. Read
current state separately: a receipt does not undo later edits or recreate a
deleted project. Operations are scoped by administrator, host project and UUID.

Creation, configuration and template operations touch multiple databases and
files. **They are not one atomic transaction.** The server journals the stage
before invoking native Commands and marks completion only after they return
from commit. `started` or `needs_inspection` can mean a partial operation or a
completed native commit whose receipt was interrupted. Automatic replay is
refused. Inspect the current project, native transaction logs and artifact;
resolve it through normal administration before planning another operation.
Do not delete receipts or change UUIDs to bypass this check. An empty project
may remain after a configuration failure. Export failures can leave an archive
which must not be used until inspected.

Receipts live under the server data root's `agent_operations/`, survive process
restart, have no automatic expiry and must be included in server-data backups.
They contain no session ticket. A shared writer lock serializes these agent
operations; a bounded wait may return HTTP 409 `writer_busy`. Inspect the UUID
before retrying with the same arguments. Ordinary administrator edits remain independent. Export checks
configuration revisions before and after writing; coordinate simultaneous
schema/workflow editing rather than claiming distributed snapshot isolation.
Installed server extensions and native package code remain trusted runtime
dependencies. These tools provide no isolated execution environment.

## HTTP boundary

MCP maps these tools to `POST /admin/agent-project/{action}`, where action is
`preview`, `create`, `read`, `export`, `install` or `operation`. Send JSON with
host-provided `ticket` and existing authorization `project`, plus `target` and
that tool's arguments (`document`, `expected_revision`, `operation_id`,
`template_id`, `title` as applicable). A successful response is `{ "result": ... }`.
Unknown fields/actions are rejected. Never put the session ticket in a URL.
This route uses the same authentication/request context as native administration.

## Owners and verification

- Input contract: [project_plan.py](../../src/tactic_stream/project_plan.py).
- Server lifecycle/receipts: [project_agent.py](../../src/tactic_stream/server/project_agent.py).
- Native creation: [CreateProjectCmd](../../src/tactic/command/create_project_cmd.py).
- Entities/DDL: [SearchTypeCreatorCmd](../../src/tactic/core/schema_commands.py).
- Relations: [SchemaCmd](../../src/tactic/ui/panel/schema_cmd.py).
- Processes/statuses: [WorkflowCmd](../../src/tactic/ui/panel/workflow_cmd.py).
- Naming: [NamingCmd](../../src/tactic/ui/panel/naming_cmd.py).
- Table pages: [PageCmd](../../src/tactic/ui/panel/page_cmd.py), [recipe](PAGES.md).
- Export/install: [project_template_cmd.py](../../src/tactic/command/project_template_cmd.py).
- Independent TH consumer knowledge: [client API](../../../../TH/docs/handler_api.md).

[test_agent_projects.py](../../tests/test_agent_projects.py) exercises actual
MCP/HTTP, native creation, replay/restart, revision rejection, interrupted
configuration, concurrency, archive tampering, template reinstall and actual
file check-in. Run `python -m unittest test_agent_projects -v` with `src;tests`
on `PYTHONPATH`; `python tests/test_agent_projects.py --postgres` uses owned
disposable PostgreSQL containers. This does not claim a fresh paired TH/TS GUI
comparison or a conversation with an external language model.
