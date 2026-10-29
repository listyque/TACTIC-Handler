---
reference: Handler
group: Workflows
icon: security
order: 38
---
# Administration

> Administration manages project structure and server accounts. Server
> edits remain local drafts until you choose Save to server.

## Window sections

| Section | What it configures |
| --- | --- |
| **Search Types** | Object types, fields, presentation, naming, and linked workflows. |
| **Project schema** | Relationships, key columns, and many-to-many link tables. |
| **Workflow** | Pipelines, processes, statuses, dependencies, triggers, and notifications. |
| **Columns Editor** | Table views and their columns. |
| **Layout Editor** | Custom views and configurable SObject items. |
| **Sidebar Editor** | Project navigation items, visibility, and access. |
| **Users** | Profiles, account fields, passwords, retirement, and group membership. |
| **Groups** | Group members and server descriptions. |
| **Access rules** | Group access to projects, types, processes, statuses, and interface actions. |

## Workflow navigation and colors

Workflow keeps the same labelled Administration menu as the other sections. Its
own searchable library sits inside the editor beside the canvas. Collapse or
resize that library independently; at narrow widths use the Workflows, Canvas
and Properties tabs. Library and inspector controls have an inner margin.

Workflow group markers and the current-type context use the Search Type color
from its registry settings. Workflow rows use their own pipeline color when set,
otherwise the type accent. Process colors retain their own meaning. Set type
colors in Search Types; they are project data, not a hardcoded UI palette.

## Project, access, and drafts

The window follows Configuration's header and navigation layout: project and sections stay in the
left panel, while the current section title, Save to server, Discard, and Help stay above its editor.
Create and Reload also live in this header when the section supports them; there is no separate
one-button action row above the editor. Actions share the top row; the section description sits below them.
Configuration and Administration use one full-width window header. Minimize,
maximize/restore and the single Close button stay in that header; dragging its
free area moves the window. Embedded Layout Editor uses the header Help button.
Save and Discard act only on the open editor; a save that required confirmation still asks for it.
Choose the project in the left panel. The list includes system, template, and archived projects
regardless of Project Chooser filters. Users and groups belong to the whole server; Search Types,
schema, workflows, and some access rules belong to the selected project.
Columns Editor also uses this project. It lists every saved definition in that project by default;
use its Search Type selector only when you want to narrow the list. It does not follow the active
search tab or offer a separate "current" mode.
Opening Configure columns from a result table selects that table's project, Search Type, saved
view and, when invoked for a column, that column. Opening Columns Editor directly keeps the full
project catalog.
Opening a result table loads its saved column definition automatically, including
the first table opened after launch. Reopening or refreshing the tab is not needed.
Repeated activation during that load shares the same pending definition request.
The Search Type filter shows both the registry title and code; if they match, it shows the value once.
The Columns Editor uses the same two-panel layout and header Save/Discard actions as the other
administration pages. Refresh sits in the header; the Wizard/XML switch stays with the
selected definition.


From a table header, **Edit Column Definition** opens the column's display declaration in the current saved view or its `definition`, and selects that column. It does not open form inputs (`edit_definition`). The menu shows the widget identifier; unavailable cells also expose it on hover. The Wizard shows the exact configured widget name, including unsupported classes. **Filter saved views** searches the XML as well as view names, so you can find a widget by its class. Custom named table views use the same Wizard. If no saved declaration exists, the editor reports that explicitly.

The header arrow collapses Administration navigation from 250 px to a 56 px icon rail.
Section buttons keep their names as tooltips. Each visited section retains its own draft until
the window closes. Switching sections does not discard edits. Save/Discard applies to the visible
section; a dot marks sections with pending work. Closing returns to an unfinished editor before
asking you to discard it. Project selection remains locked while any section is dirty or busy.
In Workflow, the Administration menu keeps its section names. The workflow library sits
inside the editor; its arrow, search and width divider are independent of the main navigation.
The library remains available beside Technical XML in wide windows. Narrow windows use the
editor's labelled panel tabs. Search and expanded groups survive navigation/panel changes.

Administration requires the administrator authority confirmed by the current TACTIC session. Group names and cached profile labels do not grant administrative access. Permission is checked
at sign-in. An unsaved or busy editor temporarily locks project selection so its draft cannot be
applied to another context. Save or discard the edit before switching.

## Search Types

Search Types has a searchable table and a separate editor for the selected row. Details controls the
title, description and color; Fields lists existing columns and stages additions or deletions.
The Search Type list remains visible on the Naming tab, so you can select another type without
leaving Naming. Save or discard an unfinished naming edit before switching types.

Existing column types cannot be changed, and Search Types cannot be archived here. Delete beside an
existing field only marks it in the draft.

Undo or Discard cancels the mark. Save asks you to confirm the exact columns: their values will be
permanently deleted.

Protected fields show why they cannot be deleted. Review scripts, naming rules and saved searches
that use the fields before confirming.

### Catalog, filters, and summary

Only current project filters the catalog locally by the native database owner, not the type's
namespace. Turn it off to include shared system types.

M:N marks many-to-many relationships; link tables are marked separately. Summary explains the
related types, key fields and source schemas.

Summary also shows a read-only node map centered on the selected Search Type. It contains only
direct schema relationships, including an explicit link-table node for many-to-many connections.

Use the wheel to zoom and hold the middle mouse button to pan; the text explanation remains below
the map. Hide config types excludes Search Types in the config namespace.

It works together with the project filter and text search, without reloading data or discarding your
draft. Only current project and Hide config types are enabled by default.

Uncheck either filter when you need a broader catalog. Some registered Search Types have no database
table.

They remain visible but open read-only with an explanation; unavailable counters show a dash. No
table is created automatically.

### Fields

Reload after the server schema is corrected. Fields explains each data type with an example name and
value.

Enter a technical field name, choose its type, then Add to draft. For example, duration_minutes with
Whole number stores values such as 3.

Save to server creates the staged fields; examples do not fill object data. Invalid or duplicate
names stay in the input for correction.

Existing fields can be searched by name. New Search Types get their standard columns automatically.

Fields lists them separately from your additions; pipeline_code is created only when Objects use a
pipeline is enabled. You can create a type without adding any extra fields.

### Details, naming, and type workflows

Summary shows total, active and retired Search Objects, fields, pipelines and processes. System and
config Search Types are included, also for administrative projects.

Details uses a color picker with a theme-color reset. Workflow lists pipelines linked to the
selected type and opens their existing editor without discarding your type draft.

Details also lets you choose a Search Type preview, including during creation. Save first creates or
updates the type, then adds an icon snapshot of its registry record to Commit Queue.

Image uploads finish through the queue. Create workflow in the Search Type editor opens a new
pipeline draft with that Search Type already selected.

Save a new Search Type first. Existing type edits remain in their draft; finish any other workflow
draft before creating another.

## Shared graph controls

The pipeline is written to the server only when you save it in Workflow. Project schema and Workflow
use colored nodes with round input and output ports.

Click either port, then the opposite port on another node to connect them. Click selects one node;
Shift-click adds and Ctrl-click toggles nodes.

Drag a frame across empty canvas space to select every intersecting node; Shift adds the framed
nodes and Ctrl toggles them. Drag any selected node to move the whole group in one draft change.

Ports never move nodes. The wheel zooms around the pointer, and holding the middle button pans in
every direction.

The canvas expands automatically, including while dragging near an edge. Arrows show connection
direction; lines follow nodes during dragging.

Schema connections run from child to parent using the configured key columns. Arrange nodes offers
Directed flow, Network clusters and Alphabetical grid.

Directed flow places connected nodes in readable left-to-right layers and wraps unconnected nodes
into name-sorted rows. Network clusters build compact webs for connected components and use the same
rows for unconnected nodes.

Alphabetical grid ignores connections and produces balanced name-sorted rows. Every layout is staged
locally and is written only by Save.

Canvas shortcuts: Delete confirms removal of the selected nodes or connection from the draft; it
never deletes a Search Type table. Ctrl+S uses the same Save operation as the header. Schema asks
for confirmation when new instance tables or missing key columns will be created; Workflow saves
the current draft directly. A failed or uncertain save keeps its existing protection against retry.

F centers the selected group, Home resets the view, +/− zoom, and arrow keys move selected nodes by
10 units. Esc first cancels a connection or drag, otherwise clears selection.

These keys work while the canvas has focus; inspector fields and XML keep their normal text-editing
keys. Both node editors smooth connection lines, arrowheads and node/port outlines.

Canvas labels scale with the zoom; the rest of the application keeps its usual text rendering. No
separate smoothing setting is needed.

## Project schema

Projects `admin` and `sthpw` show TACTIC's built-in system schema, not an empty
database document. This schema is read-only: inspect nodes, connections and
Technical XML, select and copy values, and pan or zoom the canvas. Creating,
moving or deleting nodes, editing connections/XML and saving are unavailable.
TACTIC does not support overriding this predefined schema with a database record.

On the project schema, selecting a node or connection immediately shows its JSON attributes beside
the canvas. Apply updates the draft; Save sends it to the server.

Read-only attributes can still be selected and copied. Native XML remains under Technical; process
triggers are in Process dependencies.

### Connection inspector and key columns

Schema connections have a right-hand inspector with child and parent column lists, a direction
switch and Create missing columns. Selecting many_to_many replaces the direct link with a draft
instance node and two code connections.

Select either link to choose its columns. The table name is editable.

Restore direct connection reverses the draft conversion; Discard cancels it. Save confirms and
creates the instance table and required keys together with the schema.

Existing tables are never overwritten. Reload columns refreshes only the selected endpoints.

If a schema connection references a missing database table, its inspector shows the database and
table name while keeping the other endpoint's columns available. No table is created and no
connection is removed automatically.

Correct the server table or the connection, then reload columns. Saving still validates endpoint
tables before changing the schema.

Clicking a port attaches a connection preview to the cursor. Choose the opposite port on another
node to finish.

Esc or clicking the starting port again cancels it. The preview follows zoom and pan; no connection
is added until you choose the second port.

### Creating, adding, and deleting a Search Type

The inspector's Add node page searches the registered type catalog. Selecting a type already
present changes its action to Show on canvas: it selects and centers that node without adding a
duplicate or changing the schema draft. A type not on this schema is added only to the local
diagram until Save. The same page offers New Search Type for creating a table.

The header's New Search Type action on the schema opens a separate modal editor for the title,
description, color, optional preview, pipeline support and additional fields. The table name is
generated automatically from the title.

Confirming Save to server creates the type and its schema node, then sends the selected preview
through Commit Queue. The node appears in the current canvas view, and your other unsaved
connections and positions are kept.

Save the schema separately to apply those edits. Add node in the inspector adds an already
registered type instead.

Removing a node from the canvas does not delete its table. Add node places new nodes in the current
canvas view.

Types already on the schema are marked; Show on canvas selects and centers the existing node without
creating a duplicate. The Add or Show button stays below the scrollable form.
The Search Type list fills the available inspector height below its search field, including when filtered.

Save to server saves your schema changes. The schema creation wizard has Details, Fields and Review
steps.

Back is hidden on Details and Next is hidden on Review. Save is enabled on Review, which presents
the colored title, description, preview and workflow state before listing standard and additional
fields.

The selected node's inspector header opens its pipelines in the grouped Workflow editor, or a new
type-bound draft if none exist. Delete Search Type is separate from Remove from canvas: save the
schema first, review dependencies, and enter the complete type identifier.

Only unused tables and empty local pipelines can be deleted; system/config types and types with
objects (including retired) are protected. Shared registrations remain available to other projects.

Removing a node from the canvas never deletes its table. The schema follows the selected
administration project and includes inherited parent and system relationships.

## Workflow

**Parameters** contains the process form and its native node-type choices. Node
coordinates are under **Advanced JSON**. **Pipeline settings** in the command
bar clears the node/connection selection and opens settings for the whole
pipeline; finish or discard pending inspector edits before switching.

Workflow keeps the canvas visible while you edit a selected node in the right inspector. Pipeline
settings, beside the canvas tabs and zoom controls, opens the same inspector for the whole pipeline.

The linked Search Type is shown above the canvas and cannot be reassigned; create a workflow from
the required Search Type. Each process can use its own task status workflow, selected from pipelines
for sthpw/task.

This does not change the parent Search Object workflow. Groups and users come from server catalogs,
process codes are generated by TACTIC, and colors use a picker.

Advanced JSON retains custom native parameters and XML attributes. Shared or unbound pipelines are
read-only; used processes cannot be removed.

In the JSON inspector, a saved process's identifier cannot be renamed. Change its display label
instead. New, unsaved processes can still be renamed with their connections.

Create workflow is available only on a Search Type's Workflow tab. A new pipeline appears
immediately as a selected draft under that Search Type in the workflow tree.

Enter its title and settings; TACTIC generates the pipeline code when you save. Create, Reload,
Discard, and Save to server are in the editor command bar.

## Workflow list and process dependencies

- The workflow list on the left is grouped by Search Type, with task status workflows in a separate
  group.
- Click a pipeline to open it, a group heading to collapse it, or the group's plus button to create
  a workflow for that Search Type.
- Colors and names come from the server.
- Unsaved changes must be saved or discarded before switching.
- Discarding a new pipeline keeps the top-left Create action ready for another pipeline of the same
  Search Type.
- If the XML refers to a missing process, the graph still opens and marks the missing node.
- Add that process or remove its connection before saving; opening the graph never deletes links or
  creates processes.
- Process dependencies opens a separate modal editor for a saved node: triggers, notifications,
  matching naming rules and paged pipeline objects.
- Rules can apply to this pipeline or all same-name processes in the project.
- Choose an event, source status and action; destination statuses follow each process's task
  workflow.
- Existing destination statuses and output references are preserved when editing other rule fields,
  even if they have disappeared from the current workflow. New references must be valid; preserving
  an old reference does not repair it.
- Notifications support native templates, recipients, body and conditions.
- Save applies the draft without test-running actions or sending mail; Remove takes effect on Save
  and keeps scripts.
- Generated action/progress triggers are edited through node parameters.
- Progress nodes are circular and have their own related-workflow settings.
- Task-status pipelines use status behavior forms, not ordinary Task Setup.
- Edit task status workflow opens the selected process's configured status pipeline after you save
  parent changes.

## Users and groups

- Users has a searchable directory with avatars and a separate profile editor.
- Show retired users includes archived accounts; turn it off to hide them again.
- Account settings can reactivate a retired user.
- Password changes, profile edits and retirement apply only after Save.
- Selecting someone never changes the signed-in account.
- Groups uses the same avatars and separates Members from Group details.
- In Users, the group button beside the selected user's avatar opens membership checkboxes from the
  profile editor.
- Add or remove groups, then Save to server; Discard cancels the changes.
- This also works for new and retired accounts.

## Access rules

### Effective user permissions and AI tools

Open **Access rules → Effective permissions** and choose a user. The report
reads saved native rights, including direct groups, inherited groups and the combined
system defaults. Each resolved rule lists the groups that supplied it. Refresh reads
current server state without changing the selected user's identity or issuing a ticket.
Save or discard your draft before changing the inspected user. Search filters the
membership, rule and tool rows. Record restrictions and operation-specific checks
still apply: a rule entry is not blanket authorization to every record or field.

**AI tools** and **MCP tools** configure separate group allowlists. Choose **Inherit**,
**Selected tools** or **All tools**; **Read tools** selects read-only catalogue entries,
and **Clear** selects none. These are ordinary access-rule drafts: **Save** checks the
revision and commits all group changes together. Group project binding still applies.
All inherited groups participate; a deny does not veto another group's grant for the
same key. An exact tool rule is checked before the wildcard. The group-only list is
not the user's final tool list: inspect the user report to see the combined result.

Group settings only restrict tools. Existing native administrator requirements for
agent/MCP connections and administrative operations remain in force. On Stream,
configured provider hosts, Codex adapters and MCP gateways recheck saved group rights
before each tool call; an existing connection loses revoked tools on its next call.
MCP additionally intersects the granted project's tool list, lifetime and revocation.
Handler connected to an original server without these agent endpoints still supports
the native user-rights report, but shows no agent-tool catalogue.

The wide Access rules editor has grouped navigation with action icons. On smaller
windows the same sections are available in a selector. The section header explains
what is being controlled. Matrix rows identify permissions and columns identify
groups; cells show readable Allowed/Denied labels or a custom native access level.
The legend distinguishes inheritance and grants controlled by another rule. Matrix
cells use square surfaces and row dividers. Group and record names remain server data.

Use Up/Down in the section list, arrow keys inside the matrix and Space to toggle
an editable cell. Icon-only rule shortcuts retain their named tooltips and keyboard
access. Technical views have a back button to the group defaults; unapplied source
text continues to block navigation. Save and Reset still operate on the same draft.


Open **Group inheritance**, select a group, and choose its native access level,
project scope and the groups whose permissions it inherits. Selected groups are
sources of permissions, not users added to the group. Self-inheritance is omitted;
choices that would introduce a cycle are disabled. The server validates the complete
graph again when saving. Existing inheritance entries outside the editable catalog
remain visible and preserved; use the native XML editor for those entries.

For the same native rule key, TACTIC combines groups using the highest access level.
A deny does not cancel another grant for that key. Ordered specific/wildcard lookups
still apply. The group matrix is not an effective-user permission report: other
memberships can grant access. A high access level does not make a user administrator.
Group, account and permission administration requires native administrator authority.
The same rule applies through Handler procedures and Stream endpoints.


- Group-wide access levels remain in Access rules.
- Access rules uses checkbox matrices for projects, sidebar links, menu actions, Search Types,
  processes and task statuses: find a row and a group column, then tick to allow access.
- Search filters permissions or groups.
- Headers remain visible while scrolling.
- All edits are drafts and Save to server applies changed groups together.
- The All row controls the native wildcard rule.
- A lock means access comes from group defaults, a subgroup or a higher-priority rule; change that
  grant first.
- Use inherited rule removes the selected cell's explicit permission.
- Custom access levels are preserved in Advanced rules, along with group defaults and native XML.
- Other group memberships can still grant a user access.

## Saving, conflicts, and errors

- Save or discard before changing a document or project.
- Switch sections freely: each section keeps its draft, including a user's pending password and
  nested Naming edits. Changing a document within a section still checks that editor's leave guard.
- If another administrator changed the document, reload before saving; your draft is kept on
  failure.
- If a registered project no longer has its database, Administration marks it unavailable and keeps
  the project selector enabled so you can leave it.
- Unsaved drafts block project switching and window closing, including edits in hidden sections.
- The original server fault remains in Debug Log.

## Internal structure and less visible capabilities

The administration forms edit native TACTIC objects. The browser owns the draft; the server
validates the original revision and applies the supported operation through its existing Command.
Technical XML/JSON exposes data that a compact form may not show. A field present in an original
document does not establish that its widget, callback or operation is supported by Stream.

| Editor | Native data and behavior |
| --- | --- |
| Search Types | `sthpw/search_object` registers the type; its actual database/table owns the columns. A registry entry alone does not create a missing table. Project-local classification uses database ownership, not the namespace prefix. |
| Project schema | `sthpw/schema.schema` stores relationship XML. Native Schema also resolves inherited and predefined system relationships. A diagram edge describes keys/relationship type; it is not itself an object link. |
| Workflow | `sthpw/pipeline.pipeline` stores graph XML; process settings and rules use their related native records. The object's pipeline and a process's task-status pipeline have different purposes. Saving a graph is not a test run of its actions. |
| Naming | `config/naming` provides conditions, paths and versionless rules to native Naming/FileNaming/DirNaming. The result depends on the real object, snapshot and File, not just the text visible in the editor. |
| Columns and sidebar | `config/widget_config` stores named XML definitions. Search Type, view, login and category distinguish definitions. Sidebar folders can reference other named views; flattening every XML element would lose that hierarchy. |
| Users, groups and access | `sthpw/login`, `sthpw/login_group` and memberships provide identity and native access-rule XML. A matrix cell is one explicit rule; defaults, inherited rules and other memberships can still determine effective access. |

### Naming includes more than a directory pattern

The editor's advanced fields include condition, snapshot type, repository/sandbox aliases,
sandbox naming, ingest rule code, script path and class name. Native naming evaluates expressions
against the object/snapshot/File; installed scripts or classes can affect the result. A displayed
class name does not install or migrate that class. Treat an executable naming preview as execution
of configured server code, not an isolated sandbox. Use private sample data for unknown scripts.

Latest/current are separate naming rules and alias snapshots. Distinct file types and levels need
distinct physical destinations. For supported versionless behavior and remaining deletion/replay
limits, see Help → Check-in and Core model.

### Sidebar entries can configure the workspace

Beyond title, icon and Search Type, an entry can reference a predefined search, result view,
workspace layout preset and Script Shelf. These are named definitions, not embedded copies of the
whole application. The Sidebar Editor also exposes widget type/class and group visibility; a native
class path is not a guarantee that the browser implements that widget. See Help → Sidebar Editor,
Script Shelf and Workspace layouts for the individual operation limits.

### Technical documents and scope

Advanced JSON/XML preserves native attributes outside a form's common fields. Editing such an
attribute still requires the corresponding native implementation and permissions. System schemas
remain read-only; deleting a schema node is different from deleting a table or its data.
Automatic graph layouts are a visible Stream addition: they change the local diagram draft until
Save and do not rewrite relationships or object data.

## Source map and verification — 0.112.28

The source paths below are relative to Handler's `thlib/ui`; browser editors live in
`frontend/src/features/administration`. Native commands are under `tactic.ui.panel` unless
specified otherwise. The map identifies the implementation, not a promise that every configured
server class has been migrated.

| Section | Current Handler source → Stream | Native operation / verified scenario |
| --- | --- | --- |
| Shell | `qml/features/administration/AdministrationView.qml`, `administration.py` → Administration shell in `App.vue`, `AdminSaveBar` | All eight sections, 250/56 px navigation, independent drafts, project lock, closing and workspace restoration in Chromium. |
| Search Types | `qml/features/administration/search_types/AdminSearchTypesView.qml`, `admin/search_types.py` → `SearchTypes`, `SearchTypeSummary`, `SearchTypeFields`, `NamingEditor` | `SearchTypesCmd`, `NamingCmd`: create registry/table/default views, field changes, revision conflicts and native Naming preview; Chromium creation and editing. |
| Project schema | `qml/features/administration/workflow/AdminGraphView.qml`, `admin/schema_api.py`, `admin/schema_connections.py` → `SchemaEditor`, `SchemaTypeDeletion` | `SchemaCmd`, `SchemaDeleteCmd`: keys, direct/M:N conversion, instance tables, creation/deletion review, late usage recheck, lost response protection and rollback. |
| Workflow | `qml/features/administration/workflow/AdminGraphView.qml`, `qml/features/administration/workflow/AdminProcessSettings.qml`, `admin/workflow_api.py` → `WorkflowEditor`, `WorkflowProcessSettings`, `ProcessRules` | `WorkflowCmd`, `ProcessRulesCmd` and core process commands: process/status settings, native rule records, dependencies, preservation of packages; save/readback and circular Progress/input-output ports in Chromium. |
| Columns | `qml/features/administration/columns/ColumnsEditorView.qml`, `columns_editor.py` → `ColumnsEditor` | `/admin/columns-editor` → `server/columns_editor.py`, native Command and WidgetDbConfig: saved definition catalog, Wizard/XML, unknown XML retention, revision conflicts and save/reopen. Column list and properties have a vertical splitter. |
| Sidebar | `qml/features/administration/sidebar/SidebarEditorView.qml`, `sidebar_editor.py` → `SidebarEditor` | `/admin/sidebar` → `server/sidebar_editor.py`, native Command and WidgetDbConfig: TH/TACTIC documents, nesting/reordering, item/access/technical pages, native group visibility, exact XML, saved search/filter preview and save/reopen. |
| Users / Groups | `qml/features/administration/users/AdminUsersView.qml`, `qml/AdminUserDetails.qml`, `admin/users.py` → `SecurityUsers`, `SecurityGroups` | `/admin/security-users` / `/admin/security-groups` → server adapters and native Command/SearchType: account/profile, password, memberships, create/edit/retire, conflict and rollback checks. These accounts remain server-wide. |
| Access rules | `qml/features/administration/security/AdminSecurityView.qml`, `qml/features/administration/security/AdminSecurityMatrix.qml`, `admin/security.py` → `SecurityRules` | `/admin/security-rules` → `server/security_rules.py`, native Command and access rules: project/type/process/status/action matrix, inherited/locked/custom rules, native XML preservation and permission denials. |

### Graph ports and Progress

Click an output and then an input to connect different nodes. Starting at an input also works;
the direction still runs from output to input. The pending line follows the cursor; Esc cancels
it. Ports work with Enter/Space. Selection, node movement and connections change the local draft.
Progress keeps its native circular shape. Its native default listener now saves the current
process when no related process is supplied, rather than passing `None` into a trigger record.
Configure the related Search Type/process/scope before expecting a progress count; merely adding
the node does not create related objects or run a workflow.

### Evidence and boundaries

Current Qt/QML and Chromium screenshots cover all eight pages at 1400×940 and 900×620, plus
Summary/Fields/Naming/Details/Workflow, account/membership pages, Sidebar tabs, XML and graph
inspector states. Screens use isolated fixtures, not production project data. Source/controller
and native command tests check persistence, conflicts, rights and rollback independently of the
screenshots. This Administration run uses SQLite; it is not a new MySQL/PostgreSQL acceptance run.

Useful visible Stream additions remain available: automatic layouts, direct connection tools,
technical XML/JSON, definition filters and browser maximize/restore. Schema's Add node page includes
the searchable native catalog; direct connection tools follow it. Remaining visual differences
include the additional direct connection tools; browser and Qt font rendering
also differ. Workflow's plus opens the native name/type grid and returns to selection after adding
a process; its back arrow returns without creating one. The screenshots do not establish complete
pixel parity. Configuration and working
panels are separate blocks; this work does not establish full legacy API parity. Repository Sync
and S3 remain excluded.


Schema nodes sharing one position are displayed in a local grid without changing server XML or creating a dirty draft. Technical XML is indented while preserving custom XML and comments. The Canvas toolbar contains Arrange nodes: Directed flow, Network clusters and Alphabetical grid. Save persists an arranged draft. Administrators can browse managed Search Types through bounded native read commands declared by the server. File changes remain in changelists; security errors show their original reason.


The file workspace has independent left Depot/Workspace trees and right configurable work tabs. Use View to open or restore Files, Pending, Submitted, History, Shelved, Reverted, Conflicts or Transfers. Tabs use icons, can be closed, renamed or moved, and are saved for the current user/project. New view tab and Edit view tab configure the source and path filter. Files follows the selected tree by default; fixed sources retain their own filter. Clicking a folder does not replace changelists. Pending includes shelves. Copy changelist number provides a project-local #number for native unshelve/move commands. Workspace in Stream shows indexed server Have; local filesystem scanning remains a Handler operation. Editors open from their operation menus.

## Raw database

Large integer cells and row keys pass through the native XML-RPC response without truncation or conversion to floating point. Handler and Stream return the same raw values; integers beyond JavaScript’s exact range remain strings. If a write returned a transport error, reload before retrying: the database may already have committed the change.

The sticky table heading reserves its 40px space before the first server response, keeping the first row below it on initial load and after returning to the top.

Right-click a cell for Cut, Copy, Paste or Select all; read-only fields offer Copy and Select all. Handler creates this menu only when it is opened, so page changes do not build hidden menus for every cell. The grid and editing actions are unchanged.

Handler creates editors only for visible rows, so page changes no longer build every cell at once. Scrolling a drafted cell out of view and back retains its current value. Page size and all editing actions remain the same in Stream and Handler.

Administration → Raw database lists physical tables in the system and registered project databases, including tables without a Search Type. Use Filter tables and the table selector; the selected table remains visible while filtering. The toolbar contains New row, Export CSV and DROP TABLE. On narrower windows, these actions move below the filter. Stream and Handler use the same continuous square grid, sticky headings, row actions and page ranges. The opaque headings stay above row text and actions during scrolling.

Click a cell, or focus it with Tab and press Enter/F2, to open Cell editor. The grid displays ordinary text without serialization quotes. Edit the value in the separate multiline window; the physical column type determines conversion for text, integers, decimals, floating-point numbers and booleans. JSON columns require valid JSON and preserve its exact text, including scalar values and large integers. Choose Value, NULL or, for a new row, Database default. Value with empty text stores an empty text string; the word NULL in Value mode remains literal text. Untouched new cells use database defaults. Apply or Ctrl+Enter changes the table draft; Cancel, Escape or closing the window discards the cell edit. Save to server writes the table. Read-only cells open a selectable viewer. Secret, binary and generated fields remain protected; nested JSON credentials remain redacted and read-only. Delete row and Restore row keep their staged behavior.

Save to server sends only changed rows and cells, new rows and rows marked for deletion as one atomic batch with row conflict checks. Background changes to untouched rows do not block saving; a change to an edited or deleted row still requires a reload. Discard opens an inline confirmation. Table selection, pagination, reload and export require a clean draft. If a server write fails, discard and reload before continuing because its outcome may be unknown. Reload retains the selected table when it still exists.

Export CSV includes the saved table, up to 50000 rows, rather than only the current page. SQL NULL and empty text both become empty fields, so CSV is not a lossless database backup. Handler uses a native file dialog; Stream uses the browser download. DROP TABLE requires the displayed full `database / table` name in an inline confirmation and permanently removes all its rows without CASCADE.

Raw SQL bypasses SObject validation, object triggers and undo history; database triggers and constraints still run. It does not repair Search Type definitions, references or repository files. Editing system tables or dropping registered tables can break the application. Back up the database before destructive maintenance. SQLite checks cover both interfaces; this change was not tested against a live PostgreSQL database.

After an interface update, save drafts, refresh Stream and restart Handler to load the new components. Reload from server refreshes data only.


## Background sessions and maintenance

Background file and check-in workers reuse a session ticket for each account within the executor. They recheck ticket validity, account status and current permissions before running another job. An expired or revoked service ticket is replaced before the next job. This also works for ordinary accounts; each job uses its submitting account’s current permissions. An inactive account or denied permissions prevent execution. Signing out of a client does not cancel already submitted server jobs. Updated workers need a server restart to load this behavior.

Journal indexes are created for new databases and added to existing databases by the normal server upgrade. They improve object-change lookups, history, editor revision checks and activity paging. Both Handler and Stream use the same server services and indexes. Additional indexes cover user preferences, global-search objects, publication versions, file paths, object links and group membership. Pure key parsing is reused only within one request; user, group and permission checks remain fresh. Load the new engine code by restarting server workers.

Schema relationship lookup reuses an index of connections within the current request; schema edits and column changes clear it. TEL prepares its object-cache key once per result batch, reducing repeated work when traversing wide object trees. Handler and Stream use these same engine changes on SQLite and PostgreSQL; permissions, relationship order and returned files are preserved. Restart server workers to load the update. PostgreSQL performance and complete desktop sync over a real repository have not been measured for this change.

Expired-ticket cleanup is planned and is not automatic yet. Expired authentication alone is not permission to erase unfinished transaction state, upload files or Undo history. The sobject_log journal remains necessary for history and revision checks; its own change markers require a separate dependency review before removal.

## Shared Administration behaviour

The ten sections use the same Tactic Frame structure and interaction rules in
Handler and Stream. Switching sections keeps each editor's draft, including
Naming and pending XML/JSON text. A hidden dirty editor, an active child editor,
a pending write or an unknown write result blocks changing the project. Close
returns to an unfinished section; save or discard its changes first.

Search Types and schema workflow buttons open the main **Workflow** section.
An existing pipeline keeps its identity and loaded draft. Returning to the section
does not reload it. **Manage groups and members** in Sidebar opens **Groups**.
The usual server permissions and revision checks still apply to every write.
A Save confirmation alone is not evidence that a write succeeded. After an unknown
result, reload the server state before attempting another write.

The XML source editor has undo/redo, search/replace, clipboard actions, font size
and document history. The native Handler editor uses QML controls; it does not
embed a browser. Its Layout **Open view in browser** action opens the system
browser without passing the Handler ticket in the address. Sign in there normally.
In Stream, **Open view** uses the existing workspace. Layout validation and saving
require the server's layout-authoring API.

Creating a Search Type from the schema is a separate owned editor. Closing that
creator cancels its unsaved draft; it does not undo a type already created on the
server. Canvas changes remain separate and require saving the schema.

The configuration forms use the common compact settings rows. Search Type filters
**Only current project** and **Hide config types** have visible clickable captions.
In **Columns Editor → Wizard**, **Move up/Move down** change the native element
order and keep the moved column selected. Save and confirm, then reload to read
the server result; comments and custom XML options are retained. Column width,
visibility and widget edits use the same draft. An unknown save result still
requires reloading before another write.

Complete a numeric, coordinate or instance-table-name edit with **Enter** or **Tab**.
Invalid buffered values remain available for correction. Advanced XML/JSON has its
own **Apply** action; Save does not silently replace an unapplied source draft.

## Custom page links

Project `config/url` records open pages at `/projects/<project>/<path>`. Existing
`/tactic/<project>/<path>` and `#/path` page links use the same definitions.
Sign in normally; the link does not grant access. Project, URL, Search Type and
object permissions still apply. Never include a login ticket in the address.

A URL such as `/review/{code}` can supply `{code}` to a configured search_key.
It opens the existing table/view filtered to that object. Exact paths take
precedence; ambiguous patterns fail. Retired definitions are ignored.
CustomLayoutWdg references open using the existing layout tools and their
supported markup/administrator restrictions. This does not restore arbitrary
Python widgets. Authenticated configured REST/Python handlers use normal API and
PythonCmd permissions and Command rollback. Handler resolves links to its own
server into native tables/layouts; foreign links open the system browser.

## Dashboards and external MCP agents

A dashboard can also include the existing expandable item view, with its previews, relationship/process branches, counters and object actions. Ask the agent to add an item workspace for a root Search Type; no custom tree or scripts are needed. One item workspace is supported per dashboard.

The agent can compose native dashboards from text, Markdown, counts, tables,
links and responsive rows/columns, and group/reorder existing navigation entries,
hide duplicates, or set icons and colors. Saved dashboards run in both clients.
Ordinary legacy HTML/JavaScript pages still have separate compatibility limits.

Open a dashboard from project navigation or its configured URL: it occupies the
workspace as a page, without the general search/results shell or a popup. Each
table widget keeps its own filters and actions. Refresh updates the page and
counts. Object-specific custom layouts still open as document windows.

Open **External agent → Agent permissions → MCP connections**. Choose a connection
name, instructions, allowed tools and lifetime. Access remains limited to this
project; existing connections can be revoked. Enable **Server configuration →
Security → Enable external MCP connections** and restart first; it is off by default.
The internal agent can also issue access from an authorized chat. Open this window
and select **Copy agent link** once on the pending connection. Give the complete
link to the intended external agent: it includes scoped access in its fragment;
startup instructions arrive through authenticated discovery and MCP initialization.
Standard URL/Authorization configuration remains available for MCP applications. The page
URL alone grants no access. Closing the window clears the displayed token.
Revoking a connection stops new calls; it does not undo earlier changes. External
clients log their work through native project tools; automatic third-party chat
history import is not provided by the connection itself.


Application features uses a named feature selector, an explanation and Allow/Deny access. These are individual native builtin rules, not record creation/deletion permissions. Private-note access is checked by the server. Legacy interface rules are explicitly marked and do not control the modern TH/TS screens or grant administrator privileges. Existing non-binary levels are preserved; edit them under Advanced rules. Use inherited access removes only the selected group rule from the draft; other groups and native defaults remain. Save applies the draft. Inspect Effective permissions for the combined user result.


Administration project selection opens a compact searchable list. Search by project title, code or category; the list shows a cached preview or initials, the title, code and project kind. The current project has a check mark. System projects, templates and archived projects stay available independently of the main project chooser filters. Type to filter, press Down/Up and Enter to select, or click/tap a row. Escape closes the list. Unsaved or uncertain editor changes keep project switching locked.


Collapsed Administration navigation uses centered square section buttons. When all sections fit, no scrollbar gutter is reserved. Short windows retain the scrollbar and its own gutter. Only the current section is highlighted; hover/focus shows the section title. Expanding restores the full labels.

Administration uses consistent 12 px content margins. Access rules categories use compact 30 px navigation rows with unchanged text size and a separate scrollbar when needed.

The Cell editor uses one window title. Its column context, value mode and Apply/Cancel actions stay inside the window when resized; long values scroll inside the text field. Applying changes the table draft only; Save to server still commits the draft.
