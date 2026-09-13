# Administration

Administration is a native modal window, separate from Configuration preferences.
Open it from the application menu or **Manage groups and members** in Sidebar
Editor. The latter always selects Groups and uses Sidebar Editor as its native
modal parent. `FloatingWindowModel` and `WindowHost` own that transient relation.

Both entry points are hidden for non-administrators, including supervisors.
The normal bootstrap returns the authenticated session's native
`Environment.get_security().is_admin()` result. `ApplicationController` owns the
in-memory permission and server/login identity; cached login metadata cannot grant
access. Menu opening does not query TACTIC. Signing out, losing the connection or
changing identity removes access and closes/cancels the administration editors.
Direct entry-point calls are guarded as well; server checks remain authoritative.
The main menu refreshes on session-state changes: its initial signed-out snapshot
must not survive a completed administrator login. `test_administration_menu_qml`
checks this transition in the actual application shell, including sign-out and a
subsequent non-admin session.

The administration project selector uses `ProjectModel.allProjects`, the complete
loaded catalog, including builtin, template and retired projects. It is independent
of the main Project Chooser's visibility filters. Only titles and stable project
codes are projected; opening the selector performs no RPC or preview discovery.
Catalog replacement updates the selector and preserves its selected project by
code, even if the project order changes.

Errors remain visible with their complete traceback. The shared window model
parents errors (and their Debug Log/Help tools) to the topmost open modal, instead
of creating a sibling modal that Windows can block. Dismissing an error leaves
the editor usable and retains its draft.

## Sections and native storage

| Section | Operations | TACTIC owner |
| --- | --- | --- |
| Search Types | Create a project entity type, edit title/description/color, add or delete fields, inspect counts and linked pipelines, queue a preview | `sthpw/search_object`, native `create_search_type`, `add_column_to_search_type`, `AlterSearchTypeCbk`, registry `icon` snapshots |
| Project schema | Create Search Types, add registered nodes, connect child to parent, edit connection attributes and XML | `sthpw/schema.schema`, native `Schema` |
| Workflow | Create project pipelines, edit nodes, dependencies, action scripts, command classes and subpipelines | `sthpw/pipeline.pipeline`, `config/process.workflow`, `config/trigger`, `config/custom_script` |
| Search Types / Naming | Create/duplicate/edit the selected type's rules and preview file/directory templates in the existing embedded editor | Selected project's `config/naming`, filtered by `search_type` |
| Users | Create accounts, edit profile/contact/account fields and passwords, add/remove group memberships, retire/reactivate | `sthpw/login`, native `Login.create`, `set_password`, `add_to_group`, `remove_from_group`, `retire`, `reactivate` |
| Groups | Create groups, edit descriptions, add/remove members | `sthpw/login_group`, native Login membership operations |
| Access rules | Group access level, project scope, subgroups, native XML rules | `sthpw/login_group.access_rules`, native `AccessManager` |

## Search Type naming

Select a Search Type in Administration, then its Naming tab. This embeds the
existing `NamingEditorView` and `NamingEditorController`; it does not open a
native child window or introduce a second editor/cache/save path. The editor
receives both project code and Search Type from that selection. Rules are loaded
from the selected project's `config/naming`, filtered by `search_type`. The type
remains the owner even when its rules list is empty or it has no Search Objects.
The first rule is created for that type; its Search Type field is read-only.

The type preview labels its object values as examples. Entry from an object
or Commit Queue retains the object-based preview. Save uses the existing
`insert`/`insert_update(..., triggers=True)` path for the captured project, not
whichever project is active elsewhere. Busy or dirty sessions are kept in their
original context; Reset also discards a newly created local rule. Server identity
changes cancel/disconnect in-flight work and clear the session.

Selecting the Naming tab initializes the captured type only once. Reopening it
keeps the draft and does not query again. QML construction never starts a naming
request. The existing standalone object/queue window uses the window model's
visibility event instead and is not restored open with stale prepared context.
Administration hides its type catalog on the Naming tab to give the embedded
editor space; return to Summary/Details to choose another type. Rules and fields
stack vertically in narrow geometry. Type/project selection stays locked while
a naming request or draft is pending.

`tests/test_admin_naming.py` exercises type selection, empty-type first-rule
creation, inline presentation without a child window, project/object scope,
existing save route, dirty reopen, stale completions, keyboard action and
narrow/wide scrollbar gutters. Tests use isolated settings
and substitute transport only; they do not mutate a live TACTIC server.

Verification on 2026-08-28: 76 focused administration, naming, localization and
QML smoke/structure checks passed; all 12 naming checks also passed at 150% DPI.
The separate application-runtime binding-count assertion still expects 161
bindings while the existing composition exports 164. Naming integration adds
no root QML bindings; that unrelated count assertion was not changed here.

## Editor presentation

### Search Type scope, schema roles and fields

**Only current project** filters the already-loaded catalog; toggling it does
not query the server, select another type or discard a draft. It starts on;
turn it off to include shared system types. Membership compares native
`SearchType.get_database()` with `Project.get_database_name()`, not namespaces:
a reusable `{project}` type belongs to the selected database, and `admin` resolves
to `sthpw`. Project-local `config/*` tables match this scope filter; the separate
config filter can exclude them.

**Hide config types** independently excludes rows with the native namespace
`config`. It starts on and combines with project scope and text search. It
does not hide objects merely because their name contains "config", reload the
catalog, change selection or discard a draft.

Details offers optional preview selection for both existing types and new drafts,
including the schema's modal type creator. `SearchTypesEditor` validates the local
image before saving, excludes its path from the server document, and queues the
`icon` snapshot only after receiving the registry Search Key. Discarding a new
draft never uploads its image. A failed type save retains the draft; a failed
queue preparation retains the newly created identity and image for retry.
`SchemaTypeEditor` applies the returned schema node once and stays open on a
queue preparation failure; retry updates the existing type without recreating
it or its node. Upload completion and transfer errors belong to Commit Queue.
The real catalog/modal QML routes, confirmation, cancellation, retry and image
selection are covered by `test_admin_search_types` and `test_schema_type_creation`.

The catalog and Summary use the selected native `Schema.get()` plus parent and
system schema documents. Explicit many-to-many/instance relationships mark both
endpoints; `instance_type` (or the native instance `path`) and explicit instance
nodes identify link tables separately. No suffix such as `_in_` is used as a
heuristic. Summary retains the schema's relationship, key columns and document
origin. These are declared relationships, not an inferred SQL cardinality.

`AdminSearchTypeFields` owns the additive field form, using the shared section,
settings row, input and action controls. Human-readable type choices show SQL
types and illustrative names/values; they do not set defaults or object data.
For a new type, a separate **Default fields** section explains the native
`create_search_type` result: `id`, `code`, `name`, `description`, `keywords`,
`login`, `timestamp`, `data`, `s_status` and `relative_dir`. The pipeline note
tracks **Objects use a pipeline** and includes `pipeline_code` only when enabled.
These are informational, not staged additions or existing columns; an empty
additional-fields list still creates a complete native table. Details points to
this explanation, and the existing-fields list appears only after creation.
The list follows TACTIC's `SearchTypeCreatorCmd.create_table` and `add_naming`
under the native API's creation arguments (no custom naming or collection flag).
`test_creation_explains_automatic_fields_separately_from_additions` exercises
both pipeline settings, real mouse/keyboard input, and narrow/wide layout.
Adding stages a validated lowercase identifier and supported type. Invalid or
duplicate names are retained for correction. The server independently validates
the entire addition list before any registry write. Staged fields can be removed;
existing fields are searchable and show native type/length/nullability where
supplied. Their types remain read-only. Save uses native
`add_column_to_search_type` for additions.

Existing fields have a Delete / Undo action owned by the Search Types draft.
Marking a field does not change the server. Save confirmation names the Search
Type and every marked column and warns that their values will be lost. Long
lists scroll inside the bounded confirmation without moving its buttons.
Discard clears the marks; cancelling confirmation keeps them in the draft.
Deletion uses TACTIC's `AlterSearchTypeCbk` with `Remove Column`, the original
Search Type Manager workflow: `ColumnDropCmd` and removal of the corresponding
`definition` widget configuration. It does not use custom SQL or `CASCADE`.

The server validates the entire removal list against fresh column metadata,
the loaded revision and the project's declared/inherited schema relationships
before issuing any removal command. `id`, `code`, the native identity column,
`s_status`, `pipeline_code`, and resolved schema keys are protected. Columns of
system (`sthpw`) and configuration (`config`) types cannot be deleted here.
Other standard fields can be removed after creation, just like additional fields.
The UI displays each protected field's reason, but the server independently
enforces it. Database dependency failures remain errors; scripts, naming rules
and saved searches are not rewritten automatically and must be reviewed by the
administrator. TACTIC's schema undo does not restore dropped column values.
`tests/test_search_type_columns.py` exercises draft/confirmation input, native
command arguments, actual isolated SQL deletion, dependency/conflict rejection,
error preservation and bounded narrow/wide confirmation layout.

`tests/test_admin_search_types.py` covers scope across namespaces/databases,
schema roles and inheritance, no name-based guessing, field validation, actual
mouse/keyboard/touch input and narrow/wide layout. RPC serialization and native
write boundaries remain covered by `tests/test_administration_api.py`.

Verification on 2026-08-28: 158 focused administration, naming, localization
and QML smoke tests passed. Column deletion and localization also passed
23 checks at 150% DPI; the earlier 11 editor/creation checks passed at that scale.
The shared-control, theme, motion and scrollbar structure checks passed. The
tests use isolated settings and native-contract fixtures, not a live server.

### Shared editor layout

Administration uses the same themed panels, section descriptions, selection
surfaces and action controls as Sidebar Editor and Project Editor. Shared
`EditorPanel` and `EditorListItem` own the panel/list styling; `AdminSaveBar` owns
the common draft, read-only and busy footer. Each scrollable area reserves space
for the shared scrollbar. Russian interface terminology uses “Серч-тайп” and
“Серч-объект”; native project titles and identifiers are never translated.

- Search Types has a searchable, non-editable catalog table beside its editor.
  Summary shows object totals and keeps the textual schema relationship details.
  Above those details, a read-only node map projects only the selected Search Type's
  immediate schema neighborhood from the already-loaded catalog: direct connections,
  direction arrows and explicit many-to-many link-table nodes. It never loads or
  edits the complete project schema. The shared canvas still supports wheel zoom,
  middle-button pan and view reset. Workflow lists associated pipelines and opens
  their existing editor. Naming embeds the existing rule editor
  for the selected type. Details edits presentation metadata
  with the shared color picker, a theme-color reset and the existing image
  selection/undo/queue controls in `AdminSearchTypePreview`; Fields shows existing columns and stages
  additions and deletions. Compact catalogs hide the separate technical table-name column,
  retaining the native identity below the title. Creating a type opens the
  identifier section at the top, even when Fields was previously selected.
- Groups has a full-height group list and separate Members / Group details tabs.
  Membership is a searchable checkbox list with the shared avatar, initials and
  login-derived color. Retired members remain identifiable and can be unlinked.
  Identifiers and descriptions do not
  compete with it for height. Creation opens Group details, then Members can be
  used to choose the initial participants.
- Users has an avatar directory beside a Profile / Account / Groups editor.
  Search matches names, logins and email. **Show retired users** starts off and
  includes/excludes retired accounts locally without another RPC.
  Retired identities are dimmed consistently in the directory, profile heading
  and membership list. Dimming does not disable selection, reactivation or
  removal from a group. The server catalog explicitly uses
  `Search.set_show_retired(True)`; it never sends login
  passwords, hashes or arbitrary account data. Only columns present in the native
  Login schema are offered. Group names remain native server data.
- Schema and Workflow keep a right inspector beside the Canvas.
  Schema has Selection / Add node modes; Workflow puts Add node and Remove
  actions in the inspector heading so its form remains usable in short windows.
  Add node passes the current viewport's insertion point to `GraphEditor`; native
  coordinates are validated before mutation and published once. Registered types
  already present locally are marked and use Show on canvas: select and center
  the existing node without moving it, duplicating XML or making the draft dirty.
  Reference-only endpoints can still become explicit local nodes while retaining
  their connections. Workflow process names remain unique and validation errors
  are localized. The Add / Show action stays below the inspector's scrollable
  form so it remains reachable in narrow windows.
  `tests/test_admin_graph_forms.py` covers these pointer paths,
  off-screen insertion, duplicate selection and correction after a naming error.
  In Schema, selecting a node or connection shows native JSON attributes at the top of
  the inspector immediately, including custom attributes. Apply validates and
  updates the existing draft; Save persists it. Read-only and inherited elements
  remain selectable and copyable but cannot be edited. The bounded JSON editor
  and inspector both reserve a shared scrollbar gutter.
  In Workflow, selecting a node shows its typed process parameters directly in
  the right inspector. With no selection, or after Pipeline settings, that same
  inspector edits the pipeline name, description and color. Neither form has a
  top-level tab. Its Search Type is always shown above the canvas as read-only
  context. Native XML lives in Technical; process rules use the separate
  Process dependencies editor. The
  process inspector's Advanced JSON view retains workflow JSON and XML attributes;
  no alternate format is introduced. Registered schema types and hierarchy
  subpipelines remain searchable lists. Scrollable forms reserve shared gutters.
  Canvas/inspector navigation finishes the focused field before changing the
  selected process or unloading its form, so estimates entered without Tab/Enter
  stay with the original node. A real pointer-input regression covers this.
- Access rules has category tabs and a permission table. A checkbox chooses one
  native access level, not an independent permission flag. Higher native levels
  include lower levels. Row details offer server targets and the full native
  access values; compact layouts open the same editor in place with a Back action.
  Search restrictions do not gain an `access` attribute. Group defaults, inherited
  defaults, subgroups, custom scopes and XML remain available in Technical.

Node cards, ports and connections use native colors, with the theme as a fallback.
Round ports have full-sized mouse/touch targets: click either port, then the
opposite port on another node. Body drag handlers exclude the port hit areas.
Cubic connections carry a directional arrow, which also selects the connection.
Choosing the first port attaches a transient connection to the cursor using the
same curve, color and arrow renderer. The fixed endpoint stays on that port;
the free endpoint follows viewport coordinates through zoom, pan and scrolling.
Pointer movement updates only preview geometry, not the edge model or XML.
Choosing the opposite port completes the connection through the existing
controller command. Escape, clicking the starting port again, hiding the canvas,
reloading the nodes or becoming read-only cancels the preview without a mutation.
`tests/test_node_graph_navigation.py` verifies both connection directions,
mouse/touch input, cancellation, transforms and narrow/wide viewport clipping.
During dragging, endpoints bind to the live delegate position; only release
publishes final coordinates to `GraphEditor`. Escape or hiding the canvas cancels
an uncommitted drag and restores the delegate to its native coordinates.

The shared `NodeGraph` owns the world rectangle and view transform. Wheel zoom
keeps the world point under the cursor fixed; toolbar zoom uses the viewport
center. Middle-button dragging pans over both empty space and nodes, without
selecting or moving them. The world rectangle expands in all directions as
needed, adjusting the content offset atomically so the picture does not jump.
Native node coordinates, including negative positions, remain independent of
that offset and round-trip through schema/workflow XML unchanged. Existing shared
scrollbars remain reachable in their gutters as secondary navigation.

Dragging a node near the viewport edge pans the view automatically. The frame
callback runs only during an active, visible node drag; model replacement, hiding
or cancelling stops it. Pointer coordinates come from the stable scene space,
not the moving/scaled graph. No navigation gesture performs server work.

Permission edits preserve the current table position across synchronous rule-list
publication. Section switching retains the already-created views and their drafts;
it does not reconstruct the editor or issue an extra request for the selected row.

## Native document behavior

The Search Type editor's **Create workflow** action opens the existing Workflow
editor on a new pipeline draft with `searchType` set to the current native type
identity. It is disabled until a new type is saved. Type edits are retained, and
an existing workflow draft or request blocks replacement with an actionable
message. Navigation itself does not save either document. Warm workflow catalogs
are reused; first use fetches catalogs through the read-only `workflow_request`
`new` operation, without loading an arbitrary existing pipeline or creating one
on the server. The graph editor owns this pending preparation and cancels it on
failure, project reset or shutdown. Save uses the existing native pipeline path.
Create inside Workflow inherits the displayed pipeline's Search Type. Discarding
a new pipeline keeps that Search Type as the clean creation context, so the
top-left Create action remains available for another attempt. It is not
offered without that context; the controller also rejects context-free creation.
Both the draft controller and server save reject Search Type reassignment.
Existing native pipelines without a Search Type remain inspectable, read-only;
no association is inferred or silently written.
API and real-QML regressions cover preparation, preselection, draft protection,
new-type guidance and narrow/wide layout.

### Search Type discovery, summary and preview

`search_types_request` uses native `Project.get_search_types` with
`include_multi_project`, `include_sthpw` and `include_config` enabled. The original
multi-project discovery explicitly excludes the last two namespaces unless enabled,
even when the selected project is `admin` or `sthpw`. Physical project-table
discovery remains native; no namespace is inferred from a translated display name.
Workflow's Search Type catalog uses the same inclusion policy.

Registry presence does not guarantee a physical table. Native
`Project.get_search_types` admits `sthpw` records without `has_table`: for example,
the PostgreSQL bootstrap registry contains `sthpw/command` without creating a
`command` table. Before loading columns, counting objects or saving an existing
type, the editor checks `Sql.table_exists` through
`SearchType.get_sql_by_search_type` in that type's owning database. This uses
the native table/view catalog, never a failing `SELECT ... LIMIT 0` probe.
An absent table leaves its registry entry visible and read-only, with an explicit
explanation and unavailable object/field counters (`—`, not a fabricated zero).
No table is created or registry entry deleted automatically. A real `command`
table remains usable; there is no type-name blacklist. Connection, permission
and catalog-query errors still propagate as errors, not as missing-table states.
`tests/test_admin_type_availability.py` covers absent tables, real tables/views,
write rejection, actual catalog-row selection, recovery and narrow/wide layout.
Verification: 111 focused administration, localization and QML smoke tests
passed; the availability UI test also passed at 150% DPI. These checks use
isolated database/catalog fixtures, not live server schema changes.

Only loading the selected type counts Search Objects. Native `Search.get_count`
runs with retired records included, plus a retired-only count when `s_status`
exists. No full object list is downloaded to compute statistics. The selected
project determines project-table resolution; shared system types retain their
native database scope. Fields come from native column metadata. Related pipelines
are matched by `search_type`, limited to the selected project and shared pipelines;
process counts come from their native XML. These counters are not part of the
editable document or its optimistic revision. Refresh re-reads them from the server.

`AdministrationController.open_type_workflow` opens the exact pipeline by code,
preserving the Search Type draft. Another dirty/busy workflow is not overwritten.
Editing process properties, task pipelines, groups and scripts remains owned by
`GraphEditor` and the Workflow API.

After the type exists, a local image can be staged in Summary and undone before
saving. Its path stays in the local draft and is removed before RPC serialization.
The save worker verifies that it is a readable image before mutating metadata.
On success `SearchTypesEditor` sends the registry's native Search Key and an
`SObject` to `CheckinOutController.prepare_external_checkin`, context `icon`,
versionless update enabled, through the ordinary Commit Queue. This follows
`SearchTypeCreatorCmd.checkin_preview` in the pinned TACTIC source: the snapshot
belongs to `sthpw/search_object`, never an arbitrary object of the new type.
Queue progress/failure stays in Commit Queue. An immediate queue rejection retains
the image draft and explains that metadata has already been saved.
The queued image is labelled as pending delivery, so an older preview response
cannot visually undo the choice. The queue's matching `operationCompleted` signal
refreshes the native preview without replacing metadata or other unsaved edits.

Existing previews use `SearchKeyPreviewResolver` and native File/repository
preparation, injected by the composition root. Hidden editors do not request or
publish previews. Results are read from the resolver's current server/login cache,
not from a stale descriptor belonging to another connection. The preview uses
the shared image control without a shader mask so it also renders with the
software graphics backend. Narrow/wide QML, pointer, keyboard, touch, scrolling,
the real image pixels and native RPC contracts are covered in
`tests/test_admin_search_types.py`.

### Creating a Search Type from the schema

The schema's top-left **New Search Type** action opens the owned `schema_search_type`
native modal. It reuses `AdminSearchTypesView` without its catalog and the same
`SearchTypesEditor` / `search_types_request` validation and creation path. Opening
the form does not query the server or replace the separate Search Types draft.
The form includes name, title, description, color, pipeline support and staged
columns. Closing or discarding before confirmation creates nothing.

Native `SearchTypeCreatorCmd.execute()` adds a schema node while creating the
table. A schema-originated creation therefore supplies the current schema
revision, checked before any writes, and receives the native schema XML and new
revision. `SchemaTypeEditor` owns this request and its cancellation; `GraphEditor`
accepts the created node at the viewport center and advances its saved baseline
without replacing the local graph. Existing connections, attributes, comments,
positions and unsaved removals stay in the local draft. Saving that draft uses
the new revision; discarding it retains the already-created server node/table.
The confirmation explicitly distinguishes these two operations. Close is blocked
while the save is running; server/session changes cancel the request and reject
late results. Project metadata and the Search Type catalog refresh after creation.

**Add node** in the inspector continues to add an existing registered Search Type.
Creation targets only the selected project's own schema. Removing a node is
still a canvas edit, not deletion of the Search Type or its physical table.

The schema creation modal uses the existing Search Types form and persistence
owner, with three steps: Details (title, description, color, preview and pipeline
support), Fields, and Review. Users never enter the physical table name. The
server derives a bounded lowercase snake-case identifier from the title,
including Cyrillic transliteration and guards for leading digits, SQL keywords
and titles without Latin/Cyrillic characters. The review presents the actual
colored title, description, preview and workflow state as a Search Type card,
then summarizes native and additional columns. Only the final step enables
server save. Back is absent on the first step and Next is absent on the final
step; Cancel keeps discarding the same local draft.

The selected node's inspector header exposes **Edit pipelines** and **Delete
Search Type**. Pipeline navigation resolves the selected native Search Type,
opens its first pipeline in the existing grouped workflow list, or prepares a
type-bound draft if none exists. It does not save/discard the schema, and refuses
to replace an unfinished workflow or process-rule draft.

Deletion is deliberately separate from **Remove from canvas**. Save/discard the
schema first. `SchemaTypeDeletion` owns a pinned, asynchronous confirmation;
project/server changes invalidate its results. `schema_delete_request` checks
admin access, project database, the registry/table, all objects (including
retired), aliases, native object references, pipeline processes and references
from other schemas. Used types and system/config types are blocked; there is no
cascade through user objects or repository files. The user must enter the full
type identity. Review/revision checks run again at confirmation. PostgreSQL
table locking (bounded to 3 seconds) prevents a concurrent insert between the
empty-table check and deletion. Other database vendors are rejected by this
path, not deleted without equivalent transaction protection.

The native `DeleteSearchTypeCmd` owns table undo/deletion. Because it catches
some SQL errors internally, the endpoint verifies that the table and (for a
project-specific registration) registry row are gone before saving the schema;
failure escapes to TACTIC's outer PythonCmd transaction. Empty local pipelines
are removed; the selected node/connections are removed only from this project's
schema. As in native TACTIC, `{project}` registrations are kept for other
projects. Scripts, naming rules and saved searches are not inferred or rewritten;
the confirmation explicitly asks the administrator to review them. Tests use
native-contract fixtures, not a live database.

`tests.test_schema_node_actions` exercises the real RPC source envelope, native
command arguments, transaction/lock guards, stale reviews and swallowed native
failures. `tests.test_schema_node_actions_qml` and
`tests.test_schema_type_creation` exercise mouse, keyboard and touch, cancellation,
late completions, preserved drafts and narrow/wide layouts at 100% and 150% DPI.
The deletion state's notify signal is local to its QObject subclass: reusing
the base signal for this new property caused a native PySide 6.11 QML lookup
crash, reproduced by opening the real confirmation. Shared modal dialogs use
`PopupScrim` so the confirmation darkens, rather than whitens, the owner window.

### Native schema capability audit (2026-08-28)

This audit follows the source revision cited below, specifically reachable
`SchemaToolWdg` / `SchemaToolCanvasWdg` actions, `SchemaConnectorWdg`,
`SchemaConnectorCbk`, `SearchTypeCreatorCmd`, and `pyasm.biz.Schema`. It distinguishes
current Handler support from upstream functionality not exposed here:

| Native capability | Handler state |
| --- | --- |
| Register a type, create its table and schema node | Available from the canvas's new modal and the Search Types section. |
| Sketch an unregistered node, then register/rename it | Many-to-many creates a renameable draft instance node, registered only on schema save. General Search Type creation still uses the separate modal. |
| Distinguish registered, missing-table and system types | The Search Types editor explains missing physical tables and opens them read-only. No canvas health badges yet; native metadata supplies names/colors. |
| Edit registry properties and physical columns | Separate Search Types editor; add fields or confirm deletion of unprotected fields. No node shortcut to existing-type details yet. |
| Create a direct relation and choose source/target key columns | Right inspector with actual child/parent column lists, editable keys and reverse direction. Lists load asynchronously for the selected endpoints only. |
| Create missing key columns while connecting | Explicit checkbox, applied on schema save through native `add_column_to_search_type`. Types and varchar lengths follow the opposite existing key. Unlike the web `SchemaConnectorCbk`, this does not rewrite web list/edit widget configurations with a hardcoded parent `.code` expression. |
| Many-to-many relationship wizard | Selecting `many_to_many` creates a draft instance Search Type and two `code` parent connections. Edit the table name and each connection's keys. Schema save creates its table via native `create_search_type`/`SearchTypeCreatorCmd`, then key columns, then the final XML in the enclosing native PythonCmd transaction. |
| Native relation modes and routing | `code`, `id`, `search_type`, `search_code`, `search_id`, `instance`, `type`, `path`, `prefix` and custom attributes can be retained/edited through attributes/XML; no dedicated guided forms. `many_to_many` is a wizard mode, not a substitute for its intermediate-table structure. |
| Multiple relationships between the same pair | Native `path` distinguishes routes. Imported XML is retained; the current port action rejects an additional same-direction pair, so adding a second path requires XML. |
| Inherited and system schemas | The canvas edits the selected project's own schema without a schema picker. Native `parent` / `__NONE__` remain XML settings; parent documents are not separate choices or flattened into the project XML. Extra `sthpw/schema` records selected by `project_code` are not offered as additional canvas layers. |
| Node `display` expression | Retained in XML/attributes and consumed by native Search Object display logic; no dedicated expression field. The old upstream display form is unreachable after `SchemaPropertyWdg`'s early return. |
| Open pipelines from a node | Inspector shortcut opens the existing grouped Workflow editor for that Search Type; missing pipelines open a type-bound creation draft. |
| Open raw records, CSV import, View Manager and naming from a node | Upstream has context actions. Handler has some separate tools, but not these schema-node entry points. |
| Delete a registered Search Type/table | Separate inspector action with server review and typed confirmation, restricted to unused tables/empty local pipelines on PostgreSQL. System/config types and types with objects or dependencies are blocked. Remove from canvas remains a local schema-only edit. |
| Creation wizard options beyond basic fields | Upstream also offers collections, template-table copy, project-specific registration, layout/sidebar setup, initial processes and naming rules. These wizard options are not exposed. Details supports preview selection for both new and existing types; upload is queued after saving the type. |

Upstream's Show Triggers and Show Triggers/Notifications context entries are
commented out (`menu.add` disabled), so they are not counted as working features
missing from Handler. No unrelated schema changes or bulk migration are enabled.

Project Schema and Workflow share one node-canvas interaction contract. A plain
click replaces selection, Shift-click adds, Ctrl-click toggles, and dragging a
frame over empty canvas space selects every intersecting node. Shift and Ctrl
apply the same add/toggle rules to a framed selection. Dragging any selected
node stages one atomic position update for the whole selected group; arrow keys
move that group by ten canvas units. Arrange nodes provides three deterministic
local layouts: Directed flow layers connected nodes from left to right, Network
clusters places connected components in compact radial webs, and Alphabetical
grid ignores edges. Flow and Network both place unconnected nodes in bounded,
alphabetically sorted rows instead of an unbounded line. Arrangement never
writes to TACTIC until the document's normal Save action is confirmed.

The schema draft owns `newTypes` and `createColumns`; these are save intentions,
not XML attributes or user configuration. Removing a pending node, applying XML
without it, or discarding the draft removes its creation intention. Restoring a
direct connection removes the pending instance and restores the original edge's
attributes. The server validates the revision, registry/table name collisions,
both instance edges, existing endpoint tables, key names and types before any
writes. Failures propagate to the native command transaction; no local exception
handler accepts a partial save. A saved response contains only native XML, so a
subsequent save cannot repeat instance creation. A stale retry is rejected by the
schema revision. Existing tables/data are never replaced or deleted by this path.

`SchemaConnectionEditor` owns the endpoint-column request/cache, while
`GraphEditor.document` remains the sole draft owner. Selection generations reject
late responses; reset/shutdown disconnect workers. Node movement does not request
columns. Reload columns bypasses that catalog, and save re-reads native SQL column
metadata. Column discovery reports table availability separately for each
endpoint: a registered type without a physical table remains visible with its
resolved database/table name and an explanation, while the other endpoint still
loads. It never probes missing tables, treats them as successful empty tables,
creates replacements, or drops schema references. Reload columns rechecks that
state; database/permission failures remain errors. Native Search Type resolution
selects the current database for `{project}` registrations and the owning database
for fixed/shared registrations; the inspector does not force `?project` onto
both kinds. Save still rejects missing endpoint tables before any schema or
column writes. The inspector uses paired column lists at wide sizes and stacks them
when narrow; every list and the inspector reserve the shared scrollbar gutter.
Regression coverage is in `test_schema_connections.py` and
`test_schema_connection_qml.py`, including native API fixtures and real mouse,
keyboard, touch, confirmation, resize and DPI paths. Tests do not change a live
project or claim to emulate a production database transaction.

Search Type creation uses the generated bare table name; TACTIC assigns the project namespace
and creates its physical table and supporting configuration. Column types are
allowlisted before calling the native API. Existing columns can be marked for
deletion but not retyped here. The registry `sthpw/search_object` has no `s_status` column; Search
Types cannot be retired/reactivated through the generic sObject lifecycle. The
editor offers no archive switch and never adds this column to the server. Its
catalog uses `Project.get().get_search_types(include_multi_project=True)` directly,
preserving native namespace and shared-type discovery; selected types receive a
separate native physical-table check. Individual
project objects and projects retain their own native retirement behavior.

Schema connections use existing `from_col` / `to_col` keys. New code/id connections
must identify both key columns. Many-to-many relationships use an instance Search
Type and two parent connections, as in TACTIC's editor. The schema document follows
the administration project selection; only Workflow offers a document (pipeline)
picker. `schema_request` exposes one project entry and rejects loading or saving
parent/other-project documents. Native inheritance stays intact. API regression
tests cover the catalog, project boundary and parent XML preservation; QML tests
switch Schema/Workflow in narrow and wide windows to verify the header.
Implicit/inherited endpoints are displayed without inserting artificial
definitions into XML. Registered types can be added to position them locally.

Workflow node kinds are native engine kinds plus installed workflow widget types.
Project-defined labels remain server data. `NewProcessInfoCmd` owns changed process
settings and their trigger/script side effects. Standard settings are typed forms;
Advanced JSON exposes installed custom parameters and event handlers.
Action code is hydrated from its
`config/custom_script` record, including scripts absent from workflow JSON.
Pipeline XML is committed before clearing the native graph cache and updating
dependencies: `Pipeline.set_pipeline()` alone does not persist that database field.

The form contract follows `PipelinePropertyWdg`, `NewProcessInfoCmd` and the native
task/workflow consumers:

| Form | Native storage |
| --- | --- |
| Label, color, groups, task pipeline, duration, effort, completion, creation flags | `workflow.properties`; matching XML presentation attributes stay in sync |
| Number of tasks | `workflow.task_number`, read by native `TaskGenerator` |
| Approval assignee, action script/class and execution mode | `workflow.default` |
| Related type/pipeline/process, scope, signal and wait | `workflow.default` for dependency; `workflow.progress` for progress |
| Subpipeline | `workflow.hierarchy.subpipeline`; native command writes `config/process.subpipeline_code`, while `default.subpipeline_code` serves task generation |
| Hierarchy task creation | `workflow.default.task_creation` |
| Status mapping or direction/status | `workflow.default`, with native top-level status fields updated or cleared together |

Login groups, active users and project/shared pipelines are fetched with the
workflow catalog. Task-pipeline choices contain only `search_type=sthpw/task`.
The process inspector exposes this as a separate **Task status workflow** section.
Its picker and edit action use a spaced vertical layout inside the section's
existing padding, rather than touching edges. Canvas tabs, pipeline settings and
zoom controls share one toolbar, so the pipeline-settings action does not reserve
another row above the canvas. `tests.test_admin_graph_forms` exercises both
actions and checks their geometry in narrow/wide Russian layouts.
`sthpw/pipeline.search_type` owns the parent Search Object workflow;
`config/process.workflow.properties.task_pipeline` belongs only to that process.
Choosing one does not reassign the parent pipeline. An empty choice uses TACTIC's
native default. A workflow already for
`sthpw/task` does not offer another task-status workflow inside its status nodes.
This follows upstream `PipelinePropertyWdg`, `Process.get_task_pipeline` and
`TaskGenerator`, including explicit custom task workflows on approval processes.
QML input tests switch between processes with different choices and assert no RPC
on selection; native API fixtures verify independent round trips and reject a
non-task pipeline as a task workflow.
Dependent process choices use native names for dependency nodes and native
process codes for progress listeners, matching the respective handlers.
No field queries the server on selection. A dedicated catalog notification
prevents field edits from resetting unchanged dropdown models. Unknown saved
choices remain visible until explicitly changed; server validation rejects new
nonexistent groups and inappropriate task pipelines.
After native process creation, the returned catalog includes the new server codes
immediately. QML numeric values are normalized to integers before writing native
XML estimates; optional estimates can be cleared without leaving the old value.

`config/process.code` belongs to TACTIC's creation lifecycle: it is not an input,
and fabricated XML process codes are rejected before writing. `Controls.ColorField`
is shared by node and pipeline forms; cancel leaves the draft unchanged and accept
updates the owner. `Controls.ColorPickerDialog` uses the shared dialog, input,
slider and gesture controls for HSV/HEX selection. It supports pointer dragging,
arrow keys and touch; narrow windows retain a scrollbar, and the modal scrim
darkens rather than whitens the owner. No Qt private dialog implementation or
process-wide palette mutation is used. A field creates the picker only on first
use and retains it for reopening. Nodes receive keyboard
focus only through input, not merely because a selected delegate is recreated.

Shared/global pipelines are inspectable but read-only in a project editor.
Existing task, snapshot or trigger references
block process deletion/renaming. Native dependency synchronization may assign a
new pipeline to objects whose pipeline is empty; the workflow view warns about
this before saving. Saving does not explicitly execute an action script, but
installed native save handlers and database triggers retain their normal behavior.

### Workflow navigation and repairable source documents

`AdminWorkflowList` presents the existing pipeline catalog as a persistent list
in the administration rail, grouped by native Search Type identity. Server names
and colors are retained. `sthpw/task` workflows form a separate group at the end;
its plus button creates a task-status workflow rather than an object workflow.
Group collapse and selection do not fetch another catalog. Row activation calls
the existing document selection path; unsaved/busy documents cannot be replaced.
While Workflow is open, administration sections use compact labeled-by-tooltip
icon actions above the list, leaving the canvas and right inspector usable at
the existing minimum window size. The workflow document combo was removed.

Native TACTIC can load XML containing stale connections to removed processes.
`GraphDocument` preserves these connections and projects their absent endpoints
as non-editable missing-process markers instead of rejecting the entire graph.
Opening is side-effect free. The inspector explains how to add a real process
with that name or remove the selected connection. No automatic cleanup occurs.
Both the client save boundary and server workflow endpoint reject unrepaired
connections; the server error identifies the exact source and destination.
Regression tests cover lossless load, explicit repair, server validation and
real graph/inspector input (`test_administration_documents`,
`test_administration_api`, `test_admin_graph_forms`).

### Node-specific forms and process dependencies

The native `ProcessInfoWdg` dispatch determines which form is shown. Manual and
approval nodes expose Task Setup; action/condition nodes expose their action;
hierarchy nodes expose subworkflow/task-generation settings; dependency and
progress nodes expose related-workflow settings. Appearance remains shared.
Progress nodes are circular, with connectors anchored to their actual diameter.
Every node in a `search_type=sthpw/task` pipeline uses the status form even when
its existing XML omits `type`. Editing/saving normalizes that native type to
`status`. Status mapping and direction/target status are mutually exclusive;
status nodes do not offer another Task Setup or node-type selector.
The explicit task-workflow edit link never discards an unsaved parent draft.

**Process dependencies** opens a context-owned native modal window for a saved
process. `ProcessRulesEditor` owns the rule draft and cancellable request, not the
graph or QML. It lists both local (`config/process.code`) and project-wide
same-name (`process`) triggers and notifications. Source/destination status
choices come from each process's actual task workflow, honoring explicit approval
overrides as `TaskGenerator` does. Native defaults use `Process.get_task_pipeline`.

`process_rules_request` rechecks admin access, project ownership, scope, rule
identity and a revision covering the process, pipeline and dependency records.
All rules are validated before writing. It calls the native commands in
`tactic.ui.tools.trigger_wdg`:

| Action | Native save command |
| --- | --- |
| Set task statuses | `StatusTriggerEditCbk` |
| Set parent status | `TriggerParentStatusEditCbk` |
| Create output tasks | `TriggerCreateCbk` |
| Set actual start/end date | `TriggerDateCbk` |
| Existing server script / installed class | `PythonScriptTriggerEditCbk` / `PythonClassTriggerEditCbk` |
| Notification | `NotificationTriggerEditCbk` |

Notifications include native event templates, subject/body, expression-capable
recipients/CC, temporary-ticket generation and rules XML. Status conditions are
XML-escaped, and clearing a generated condition retains other authored clauses.
Save configures rules; it does not test-run the configured script or send a test
message. The enclosing native `PythonCmd` supplies the save transaction.
Removal is confirmed and staged until Save; it never deletes a referenced script.
An existing execution mode is not silently reset by the native callback.

Generated `process|action` triggers and progress listeners remain owned by node
parameters and are read-only in the rule list. The old global read-only trigger
JSON page was removed. The graph revision covers its generated triggers, while
the dependency editor owns revisions of ordinary rules; saving ordinary rules
does not invalidate an unchanged graph draft.

Naming shows native `config/naming` contexts matching `process/%`; the existing
Search Type Naming Editor remains the authoring owner. Objects are counted by
the parent pipeline and browsed in pages of 50, not confused with process tasks.
Paging is disabled while a rule draft is dirty and never discards it. Script
choices load paths only, not script bodies. No dependency request runs merely
because a node was selected.

Verification: `test_process_rules` exercises the actual callback class bodies
from the audited TACTIC checkout in `.cache/tactic-source` against isolated native
object fixtures (skipped if that checkout is absent). It covers every action,
scope, create/update/delete, conflicts before writes, generated-rule ownership,
notification conditions, approval overrides and object pagination.
`test_process_rules_qml`, `test_admin_graph_forms` and
`test_node_graph_navigation` exercise real native-window input, status choices,
circle ports, confirmations, dirty drafts and narrow/wide layouts without a live
server. Installed custom node parameters remain available through Advanced JSON;
their third-party web widgets are not embedded or reimplemented.

Projects, sidebar links, menu actions, Search Types, processes and task statuses
use object-by-group checkbox matrices. Both headers stay visible while the grid
scrolls. Search filters rows and group columns locally; TableView creates only
visible cells, and a permission edit emits cell data changes without resetting
scroll or focus. The sidebar catalog is traversed through native
`SideBarBookmarkMenuWdg.get_config`; gear actions come from
`GearMenuSecurityWdg.get_all_menu_names`. Configured names are never translated.

Native Process Security keys are project/process scoped, so the same process in
several pipelines has one row. Task statuses are a separate tab and use
`group="process"` with the task pipeline, without inventing a task rule scope.
The All row edits a real wildcard rule, not every currently visible row.

Checked cells indicate a grant. Unchecking writes an explicit native deny;
Use inherited rule removes that cell's explicit binary rules. A locked cell
means the native key precedence or a group default/subgroup still grants access:
change the granting rule first. Partial native levels remain intact and are
marked as custom, rather than silently promoted to allow. This is a projection
of a group's rules, not a complete user's permission simulator: other group
memberships, administrator privileges and additional builtin checks still apply.
`test_admin_security_matrix` compares the lookup against the actual audited
AccessManager class, including duplicate-key priority and wildcard ordering.

One SecurityRulesEditor owns all group drafts. Loading/reloading reads one
project matrix; saving sends the batch in one server procedure. All revisions,
native rules and subgroup graphs are validated before the first group commit;
only changed groups are written. A concurrent edit rejects the whole batch.
Changing category or inspecting another group's advanced rules does not discard
pending cells. Advanced XML/JSON and the object, field, builtin and search-filter
editors remain available. Unknown XML, comments and custom attributes survive
binary edits. Search restrictions may legitimately omit `access`.

`sthpw/access_rule` and its group join are deprecated in the inspected native
security path; this editor does not create unused records there. `sthpw/wdg_settings`
remains the owner of repository-sync presets, not schemas or access rules.

## Ownership, concurrency and safety

`AdministrationController` owns section/project selection, group membership and
post-save metadata publication. `admin/*` owns independently staged native
documents. `AdminDocumentEditor` owns each RPC worker, draft, revision and request
generation. QML only edits those drafts; pointer movement never issues an RPC.
The shared `Controls.NodeGraph` has no feature-controller dependency.

Schema and Workflow share canvas-scoped keyboard commands:

| Key | Action |
| --- | --- |
| Delete | Open the existing **Remove from canvas** confirmation for the selected node or connection. Only the draft changes; a Search Type table is never deleted. |
| Ctrl+S | Open the existing server-save confirmation, only for a writable, changed, idle document. |
| F | Center the selected node, including circular progress nodes. |
| Home | Reset the viewport and zoom. |
| + / − | Zoom in/out around the viewport center, within the same limits as the mouse wheel. |
| Arrow keys | Move the selected editable node by 10 native coordinate units. |
| Esc | Cancel a pending connection/drag first; otherwise clear selection. |

`NodeGraph` is the keyboard focus scope, retaining focus when a draft mutation
replaces its delegates. Signals route removal to `AdminGraphProperties` and save
to `AdminDocumentShell`, sharing the buttons' guards and confirmation dialogs.
There are no window/application-wide shortcuts: inspector text, native XML and
other administration sections retain their own input. Delete and save ignore
autorepeat and cannot interrupt a drag, pan or pending connection; busy/read-only
documents and reference-only nodes retain their existing protections.
`tests.test_node_graph_shortcuts` exercises real key events in both editors,
confirmation/cancellation, repeated movement, text-input isolation and navigation.
The removal confirmation is centered on the window overlay, not the narrow
inspector; its actions are checked at 900px and 1400px window widths.

`NodeGraph` requests `Shape.CurveRenderer` for connection curves and arrowheads,
including the transient connection preview. Its analytic antialiasing avoids
per-edge MSAA layers or changes to application/window rendering preferences.
Qt selects its native `SoftwareRenderer` when the software backend is active.
Node/port rectangles retain antialiasing and allow fractional border widths;
only the zoomable node labels override native text with `Text.QtRendering`.
The choice follows [Qt's Shape renderer contract](https://doc.qt.io/qt-6/qml-qtquick-shapes-shape.html#rendererType-prop).

`tests.test_node_graph_rendering` checks actual edge-coverage pixels at 65%, 100%
and 160% canvas zoom, pointer-driven connection previews, renderer selection and
absence of added layers. The old OpenGL geometry renderer fails the pixel checks
with binary stair-step edges. Run software tests with `QT_QPA_PLATFORM=offscreen`
and `QT_QUICK_BACKEND=software`. On Windows, RHI pixel tests use the native window
platform (`QT_QPA_PLATFORM=windows`, `QT_QUICK_BACKEND=rhi`,
`QSG_RHI_BACKEND=opengl` or `d3d11`); the offscreen platform cannot present the RHI
test window here. Tests isolate settings and never contact TACTIC.

`AdminUsersEditor` owns an independent selected-login draft, not the profile
window or authenticated session. It reuses the profile mutation procedures with
`require_admin=True`, checked on the server for every write. It sends changed
fields only, preserving untouched fields; unlike XML documents, Login fields do
not use revision conflict detection (concurrent edits to the same field are last
writer wins). Creation uses native `Login.create`, including its UPN and default
group behavior. Existing retired logins still block duplicate creation. Retirement
and reactivation use native object methods, and self-retirement is rejected.
Account passwords are never read from the server or persisted locally; the draft
password is cleared after save/discard, window close and session reset.

The group button beside the selected avatar opens membership checkboxes in the
user card. `UserGroupMembershipEditor.qml` is shared with the profile editor;
administration edits membership only, leaving group-wide access levels in Access
rules. The directory request includes available native groups, so opening this
section and toggling checkboxes do not query the server or select a profile.
Membership belongs to the same user draft as account fields, including new and
retired users. Discard restores it, and Save confirms and writes it through the
existing native profile/create procedures. An untouched membership list is not
sent during profile-only edits. After save, the fresh membership catalog updates
both native membership directions and Groups counts without losing other drafts.
`test_admin_users_ui`, `test_admin_users_api` and `test_user_profile_qml` exercise
the shared input path, saving, reset, authority, identity isolation and scrolling.
The membership follow-up passed 30 focused user UI/native API tests and all 16
user UI tests at 150% scale. The broader 102-test run passed QML window smoke,
localization, groups and access checks; its only failure was the existing
oversized-file debt check (23 unrelated files). The separate profile-directory
gutter test also still fails on its existing 15px gutter versus a 16px assertion;
the membership editor and its own scrollbar are tested independently. No live
server data was changed by these checks.

`UserController.identity_record` owns the common native avatar-file selection and
repository queue path; `UserIdentity.qml` renders it in the admin list, selected
profile and group membership rows. User-row selection uses the already loaded
directory, without RPC or changing the profile window. Committed Login changes
are published on the Qt thread into the existing directory and membership links.

Document saves require confirmation; membership changes use the explicit group
Save action. Every administrative write checks native
`Environment.get_security().is_admin()` on the server; a UI supervisor flag or a
group name containing “admin” is not authorization. The existing server procedure
transaction wraps native commands. XML rejects DTD/entities, validates identities
and endpoints, and preserves unknown elements/attributes. A loaded revision is
compared before updates, including action scripts and linked triggers for a
workflow. Conflicts require reload; errors retain the local draft and traceback.
This is optimistic conflict detection, not a database row-lock guarantee.

Save or Discard is required before switching documents/projects. Section switches
retain drafts and already-created views. Closing retains drafts for the same
server; server/login changes and shutdown disconnect workers and reject stale
completions. Group membership writes send deltas, preserving concurrent unrelated
members; retrying a completed membership change is idempotent.

Successful writes invalidate the relevant persistent reference/search/relation/task
caches. Project metadata is rebuilt in a worker on a separate native Project and
published on the Qt thread. Existing Search Type identities are retained, so open
search tabs are not recreated or reset. Membership publication updates both
directions of native Login/Group links and notifies Sidebar Editor. Other active
TACTIC sessions may need reauthentication to pick up changed security caches.

No live project schema, workflow or security writes are performed by automated
tests. The implementation was checked against Southpaw TACTIC 5.0 source commit
`17c78e0dfb20a6fef16d70df6aa7b0c9bf20a596`, notably:

- `pyasm/biz/schema.py`, `pyasm/biz/pipeline.py`
- `pyasm/biz/project.py`, `pyasm/search/search.py`,
  `pyasm/search/upgrade/postgresql/bootstrap_schema.sql`
- `tactic/ui/tools/pipeline_wdg.py`, `tactic/ui/tools/schema_wdg.py`
- `tactic/ui/app/search_type_creator_wdg.py`, `pyasm/prod/service/api_xmlrpc.py`
- `pyasm/security/security.py`, `access_manager.py`, `access_rule.py`

## Verification

The process-parameters follow-up passed 81 administration form, QML, document,
API and localization checks, plus 16 graph-form checks at 150% scale. The latter
use the offscreen software renderer and real mouse, keyboard, drag and touch
events; light/dark and narrow/wide picker layouts are covered. The shared smoke,
theme and structure run passed 60 of 61 checks: the architecture-size gate still
reports existing oversized files outside this change. No live server was edited.

The new-process catalog and optional-estimate clearing regressions failed before
their fixes. Form tests also assert integer XML values (not QML double strings),
stable dropdown focus, cancellation without draft mutation, lazy picker creation
and native generated process identities.

`test_administration_documents` exercises native XML preservation, local draft
updates, invalid input and lifecycle cancellation. `test_administration_api`
uses native-object contract fixtures to verify authorization, conflicts,
additive field changes, schema keys, pipeline persistence and process-handler
calls. The Search Type registry fixture executes SQL against the native column
contract, so an invalid `s_status` query or write fails instead of passing an
unrestricted mock. List/load/save also execute through the real RPC serializer:
`identity` is the document key; `code` is reserved for serialized server script
source. QML tests cover existing/new type fields and pipeline selection.

`test_administration_qml` creates the actual window with Russian translations,
changes sections, edits fields, selects and drags nodes, exercises keyboard input
and checks narrow/wide geometry. Its live-drag regression checks the connection
before mouse release, verifies zero model publications while dragging and exactly
one at release. It also checks round-port geometry/colors at the canvas origin,
keyboard connection/cancellation, Search Type catalog selection and creation from
the Fields tab. `test_editor_windows_qml` and
`test_security_groups` cover group membership and its modal entry point. The QML
smoke harness verifies creation/teardown without production configuration or
network access. Native-server round-trip acceptance remains separate from these
isolated tests and must use a disposable project before rollout.

`test_administration_access` verifies native session authority, denied entry points,
cache isolation, revocation and diagnostic ownership. `test_administration_qml`
also delivers an actual worker permission error, copies the traceback, dismisses
with mouse and keyboard, opens Debug Log, and resumes using the editor.

`test_admin_groups_ui`, `test_admin_graph_forms` and `test_admin_security_ui`
exercise the redesigned forms through mouse, keyboard and touch. They cover
native JSON round trips, group-column checkbox matrices, target selection, group
membership, scroll-position retention, scrollbar gutters and read-only/busy/error
states. Their fixtures redirect configuration and never write to a live server.

`test_admin_users_api` covers native administrator checks, safe column projection,
retired selection/duplicates, retirement/reactivation, native account creation and
RPC serialization. `test_admin_users_ui` creates the actual Russian QML window,
uses mouse, keyboard and touch, checks hide/show retired, field focus retention,
independent profile/session identity, save confirmation, errors, password cleanup
and narrow/wide scrollbar gutters. These checks use isolated account fixtures,
not live server edits.

The final Users/Groups follow-up ran 42 controller, QML, shared-control and test
bootstrap checks successfully in one process. Four focused native Windows checks
at 150% scale also passed: retired-user selection, member unlinking, and both
narrow/wide editor layouts. Retired dimming regressions failed before the visual
change and pass through real keyboard/mouse input afterward.

Verified for the redesign on 2026-08-28:

- 130 focused administration, access/menu, editor-window, membership,
  localization and offline smoke checks passed (73 QML/editor checks, 54
  API/document/access/catalog/localization checks, and three menu/smoke checks).
- 40 actual Windows administration-window tests at 150% scale passed, including
  mouse drag, round connection ports, keyboard confirmation, touch selection,
  non-admin entry visibility and an interactive permission-error dialog.
- Narrow/wide screenshots were inspected with the Russian catalog in both
  offscreen and native Windows runs.
- 60 of 62 shared theme/structure/typography checks passed; the two existing
  repository-wide debt failures are described below.

The live-connection regression was reproduced before its fix: the endpoint stayed
at x=220 while the dragged node's output moved to x=305. The origin-port check
also failed before adding the inset (18 logical pixels of its hit target were
outside the clipped canvas). The permission-table regression reproduced a
scroll jump from 432 to zero. All three now pass through actual pointer input.
No live server data or schema was changed.

QML fixtures set the Material style before Qt Quick initialization, matching
production startup. Administration lifecycle, sidebar/editor-window and shared
control fixtures obtain their application from `tests.qt_application`:
controller tests can run first without creating a non-GUI application. An
existing `QCoreApplication` is rejected with a Python error before QML creation;
it cannot be promoted into a `QGuiApplication`. Other core-only suites must run
in a separate process. `test_qt_application` verifies both initialization orders
in isolated subprocesses; it does not disable Windows crash reporting.

The user-editor QML creation regression also exposed an invalid inherited
PySide notify-signal binding. Derived properties use the editor's own declared
signal, forwarded from the base state signal. The real window tests cover both
initial creation and subsequent property updates.

The broader typography/architecture-size gates still report existing violations
outside these editors (including `ActivityCalendarPopup`, `ConfigurationSection`,
`SettingsRow` and older oversized views/controllers). Their baselines were not
relaxed and unrelated files were not refactored for this task.

The canvas-navigation follow-up passed 95 graph, administration QML, native API,
document, localization and smoke checks, plus 14 focused pointer/keyboard/touch
checks at 150% scale. `test_node_graph_navigation` reproduces the original wheel,
middle-button, port-drag and negative-coordinate failures and verifies anchored
zoom, all-direction panning, edge autopan, cancellation and narrow/wide gutters.
The native API fixture verifies negative coordinates survive schema and workflow
XML saves. These runs used offscreen software rendering and isolated settings;
no live server data was changed.

The schema-type creation follow-up passed 106 administration/QML/API/document/
localization/smoke checks. A separate 150%-scale run passed 47 focused checks,
including the seven real-window creation tests and shared scrollbar/control
contracts. Narrow/wide screenshots were inspected after Russian localization.
The API tests first failed without the schema revision/response contract, then
passed with native creator side effects represented in the fixture. Coverage
includes creation followed by schema save, missing-schema bootstrap through the
real RPC serializer, conflicts before DDL, permission checks, zero-request form
opening, mouse/keyboard/touch activation, preserving independent drafts, busy
close, failed saves, session cancellation and stale completions. All runs used
isolated settings and offscreen software rendering; no live TACTIC data changed.

The Search Type summary/preview follow-up passed 124 administration, native API,
document, input, check-in, localization and QML smoke checks. Another 54 focused
checks passed at 150% scale, including shared scrollbar/control contracts. Tests
cover system-project discovery, total/retired counts, correct pipeline targeting,
the real color picker and reset, image pixels in the software renderer, FileDialog
acceptance, the actual check-in preparation path, queue completion, preserved
drafts, hidden native windows and server/login-scoped preview reads. The image
pixel regression failed with a shader mask and passed with the shared direct-image
path. Russian narrow/wide screenshots were inspected. These checks used isolated
settings, offscreen software rendering and no live TACTIC writes.
