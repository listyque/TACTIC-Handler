---
group: Workflows
icon: security
order: 38
---
# Administration

> Administration manages project structure and server accounts. Every edit remains a local draft
> until you explicitly confirm Save to server.

## Window sections

| Section | What it configures |
| --- | --- |
| **Search Types** | Object types, fields, presentation, naming, and linked workflows. |
| **Project schema** | Relationships, key columns, and many-to-many link tables. |
| **Workflow** | Pipelines, processes, statuses, dependencies, triggers, and notifications. |
| **Users** | Profiles, account fields, passwords, retirement, and group membership. |
| **Groups** | Group members and server descriptions. |
| **Access rules** | Group access to projects, types, processes, statuses, and interface actions. |

## Project, access, and drafts

Choose the project in the left panel. The list includes system, template, and archived projects
regardless of Project Chooser filters. Users and groups belong to the whole server; Search Types,
schema, workflows, and some access rules belong to the selected project.

Administration is available only to TACTIC administrators, not supervisors. Permission is checked
at sign-in. An unsaved or busy editor temporarily locks project selection so its draft cannot be
applied to another context. Save or discard the edit before switching.

## Search Types

Search Types has a searchable table and a separate editor for the selected row. Details controls the
title, description and color; Fields lists existing columns and stages additions or deletions.

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
never deletes a Search Type table. Ctrl+S opens the server-save confirmation for a changed document.

F centers the selected group, Home resets the view, +/− zoom, and arrow keys move selected nodes by
10 units. Esc first cancels a connection or drag, otherwise clears selection.

These keys work while the canvas has focus; inspector fields and XML keep their normal text-editing
keys. Both node editors smooth connection lines, arrowheads and node/port outlines.

Canvas labels scale with the zoom; the rest of the application keeps its usual text rendering. No
separate smoothing setting is needed.

## Project schema

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

The top-left New Search Type action on the schema opens a separate modal editor for the title,
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

Workflow keeps the canvas visible while you edit a selected node in the right inspector. Pipeline
settings, beside the canvas tabs and zoom controls, opens the same inspector for the whole pipeline.

The linked Search Type is shown above the canvas and cannot be reassigned; create a workflow from
the required Search Type. Each process can use its own task status workflow, selected from pipelines
for sthpw/task.

This does not change the parent Search Object workflow. Groups and users come from server catalogs,
process codes are generated by TACTIC, and colors use a picker.

Advanced JSON retains custom native parameters and XML attributes. Shared or unbound pipelines are
read-only; used processes cannot be removed.

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
- Switching sections keeps your draft.
- If another administrator changed the document, reload before saving; your draft is kept on
  failure.
- If a registered project no longer has its database, Administration marks it unavailable and keeps
  the project selector enabled so you can leave it.
- Unsaved drafts still block switching.
- The original server fault remains in Debug Log.
