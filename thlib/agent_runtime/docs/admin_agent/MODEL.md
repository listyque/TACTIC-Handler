# TACTIC domain model

This is the vocabulary needed to design a project. Values in examples are
illustrative; discover the actual installation's identifiers through OPERATIONS.
This describes server entities; TH wrappers have their own API and lifecycle.
Deeper reference: [TS structures](SOURCES.md#ts-server-structures) and
[current core guide](../../frontend/public/help/core_model.en.md).

## Project, namespace and database

`sthpw/project` registers a project: its `code`, human `title`, `type`, template
flag and database resource. `type` selects a reusable project type/namespace.
Project code, namespace and database name are related but not interchangeable.
A template can supply `vfx/shot` to several projects, each with its own rows.
Do not rename every `vfx/*` type when creating another VFX project.

`sthpw/search_object` is the SearchType registry. A definition describes a
namespace/type, table, database mapping and SObject class. A database mapping
of `{project}` resolves through the active project; a fixed/shared mapping does
not. `config/*` names resolve configuration in the selected project. `sthpw/*`
holds shared/system records, many with explicit `project_code` ownership.
Project selection is not permission to query every row in a shared table.

The built-in `admin` and `sthpw` projects are special. Their system schema is
read-only in the schema editor. Use ordinary project/type commands to create
business projects. `classic` and `file_project` are distinct project modes;
the latter has a dedicated file workspace/schema, not an arbitrary VFX schema.

## SearchType, SObject and identity

Field references: [original core tables](../../../../TH/docs/tactic_database/02_CORE_TABLE_CATALOG.md)
and [project config tables](../../../../TH/docs/tactic_database/03_CONFIG_TABLE_CATALOG.md).

A SearchType is an object definition; an SObject is one record of that type.
The registry, actual table columns and schema relationships are separate facts.
A registry entry does not prove that a table exists in this project.

| Identity | Meaning |
| --- | --- |
| `vfx/shot` | Base SearchType; it does not identify a row. |
| `vfx/shot?project=city` | Project-bound type/query scope. |
| `vfx/shot?project=city&code=SH010` | A record identified by its code. |
| `vfx/shot?project=city&id=42` | A record identified by its database ID. |
| `sthpw/task?code=TASK00000001` | Shared task record; inspect its parent/project fields. |

Prefer the exact `__search_key__` returned by the server. An ID is local to its
own table/database; a code is not globally interchangeable across SearchTypes.
Do not parse search keys with hand-written splitting: codes can contain special
characters. A display label is not an identity.

Read actual columns/defaults/types before writing. Common business fields are
`code`, `name`, `description`, `pipeline_code` and `s_status`, but their presence
is not universal. `s_status='retired'` concerns retirement; it is not the task's
workflow `status`. Retired rows may be hidden by default queries.

## Relationships and shared work records

Reference: [relationships and flows](../../../../TH/docs/tactic_database/04_RELATIONSHIPS_AND_FLOWS.md).

`sthpw/schema` stores XML relationships and type nodes. It can inherit another
schema and system relationships. A code relationship may connect a child field
such as `sequence_code` to its parent's `code`. Its actual `from`, `to`,
`from_col`, `to_col`, relationship kind and path determine traversal. Read those
attributes; never infer a foreign key solely from a column or table name.

An instance/link SearchType represents many-to-many membership with references
to both ends. A graph's layout coordinates are presentation, not relationships.
Creating a field alone does not register a relationship, and drawing a link
without its required field is incomplete. Schema editor operations coordinate
the corresponding schema/DDL changes.

| Record | Meaning and connection |
| --- | --- |
| `sthpw/task` | Work on a parent SObject, with process/context, status, assignment and dates. Parent references use the native search-type/ID/code conventions. Use `create_task` rather than guessing them. |
| `sthpw/note` | Discussion attached to an object and context/process. |
| `sthpw/work_hour` | Logged work; it is not inferred from a task's start/end dates. |
| `sthpw/snapshot` | A publication/version for a parent object and context, optionally level-scoped. |
| `sthpw/file` | A physical file or file-group record belonging to a snapshot. Snapshot membership matters; not every file with the same parent belongs to every version. |

A task's own details and its parent object's details answer different questions.
For task headings use process and resolved parent identity, while retaining the
task code as metadata. Check-in on a task can target its parent or the task
itself depending on the configured action. Preserve that configured behavior.

## Pipelines, task statuses and automation

Guide: [Workflow](../../frontend/public/help/administration.en.md#workflow).

`sthpw/pipeline` stores pipeline XML and scope; business objects can reference
its code through `pipeline_code`. Processes such as `model`, `light`, `review`
are work stages. Task statuses such as `In Progress` are a different level of
configuration; do not substitute process names for statuses or hardcode a status
list. Discover the project and relevant task pipeline definitions.

Pipeline XML contains process nodes and connections. `config/process` and its
settings describe node behavior and bindings. A node can be manual, conditional,
an action or another supported kind. Read the workflow editor's `metadata`
before choosing node kinds or settings. A shared pipeline may be read-only in
the selected project. One saved pipeline does not automatically assign every
object to it or guarantee tasks were created.

`config/trigger`, `config/client_trigger`, saved scripts and notification records
can cause execution or external effects. Workflow save may create/update managed
bindings. Preserve them when editing an existing document; do not remove a
managed trigger to resolve a validation error. Distinguish a declarative manual
workflow from one that executes Python/JavaScript or sends notifications.

## Definitions, views, layouts and navigation

Reference: [view semantics](../../../../TH/docs/tactic_compatibility/table_views.md)
and [widget catalogue](../../src/tactic_stream/shared_ui/features/table/widgets.json).

`config/widget_config` contains XML by SearchType/view and optional user/scope.
Several records and built-in configurations can contribute to the effective
result. Priorities, inheritance and `ALL` definitions matter. Read both source
layers and the resolved interface. One source's XML is not the whole view.

| Term | Role |
| --- | --- |
| `definition` | Reusable element definitions: display/editor handlers and options. |
| `edit_definition` | Form/editor definitions used in the original configuration system. |
| `table` or another named table view | Ordered elements, presentation and view options; elements can reference definitions. |
| `insert`, `edit`, named forms | Configured creation/editing, defaults and actions. A table column does not guarantee the form includes it. |
| Nested view | A child/related table with its own search, insert and edit views. Keep its parent scope and filters. |
| `SideBarWdg` | Navigation definitions and named views, including project and Handler navigation. Folder contents can live in another named view. |
| `sobject-layout` | Bounded declarative object layout, distinct from the classic table view and arbitrary legacy HTML/Mako layouts. |

Minimal named table source, for fields that actually exist:

```xml
<config>
  <review_table>
    <element name="code"/>
    <element name="name"/>
    <element name="description"/>
  </review_table>
</config>
```

This alone does not make `review_table` the navigation/default view. Update the
relevant navigation/view setting only when that is part of the request. For an
existing document, preserve its comments, unknown XML, options and source scope;
do not rebuild it from an incomplete simplified projection.

Stored field values, computed/display cells and unsaved drafts are different.
For example, `0`, `false` and `null` must not all become blank. Never write a
currency-formatted string back into a numeric field. The modern clients consume
typed interface descriptions; they do not execute every historical HTML widget.
Check exact handler/options support and exercise the actual table/form.

## Naming, files and versions

`config/naming` defines repository/file/sandbox naming for a SearchType and
context. Native Naming resolves fields against SObject, parent, Snapshot, File,
version, extension and other runtime input. For example, `{sobject.code}` refers
to the object code; it is not a literal folder name. TSQL expressions, custom
classes and saved scripts can participate in evaluation.

Use the server's naming preview and inspect matching rule, paths and reported
collisions. Custom execution needs its separate execution permission; current
editor preview is not an OS sandbox. Preview does not reserve a future path.
The real check-in must compute/check it again. Versioned, latest and current
publications are distinct; do not equate the highest ordinary version with all
versionless aliases. Let snapshot/check-in APIs own file membership and aliases.

## Templates, plugins and export scope

A native template is a package with `manifest.xml`, schema/configuration and
SPT records. Installation can create a project or import into an existing one;
these have different risks. Template instantiation can retain the template's
SearchType namespace while adapting project-specific schema/pipeline references.
Re-read the installed catalogue instead of applying global text replacements.

The default template exporter includes type definitions, widget configs, naming,
scripts, processes/triggers, URLs/settings and relevant project groups, pipelines
and notifications. It does not automatically export every business row, uploaded
file, login or extension. Treat lookup/demo data as an explicit export requirement.
A template ZIP is not a database/repository backup.

SPT and plugin includes can execute Python. A plugin is trusted server code, not
just passive XML. Keep imported unknown content intact and report unsupported
dependencies. The `pyasm.prod` subsystem and Maya/applets are excluded here;
ordinary VFX project types are still valid. Use `pyasm.web.api_xmlrpc` and
`pyasm.biz.ProjectSetting`; `config/prod_setting` remains a valid settings type.

## Writes and failures

Native Command/Search/SObject paths own permissions, transactions, triggers and
journals. A raw SQL edit bypasses important behavior. Read responses can include
`revision` and `canWrite`; respect both. Revisions belong to that exact operation
and scope. Do not compare or synthesize hashes across different editors.

A failed command is not automatically proof of zero effects across multiple
databases/files. A lost response may follow a successful write. Re-read the target
and report ambiguity; do not blindly repeat project creation/import. Current
project creation is not undoable through generic journal undo. Existing editor
revisions do not constitute a global, durable project-plan transaction.
