# Add, Edit, and Link SObject contract

## Server-defined forms

`SObjectEditorController` and `SObjectFieldModel` are the QML-safe boundary for
Add and Edit. Field structure comes from the server's existing EditWdg
description, not from a locally invented list of database columns.

Schema loading executes asynchronously through the server pool and preserves
the server-provided order, column, title, description, widget class, action
options, defaults/current values, required/read-only state, and option values.
Late schema results are rejected by request identity.

QML receives normalized field descriptors only. Project, Search Type, schema,
SObject, and widget objects remain in Python.

`TacticBaseInputWdg` owns the common field contract. Text and select families
inherit from that base, and password, project, pipeline, process-group, status,
calendar, parent, upload, and thumbnail widgets add only their native semantics.
`SObjectFieldFrame.qml` owns the shared Material surface, label, description,
required/read-only state, validation presentation, spacing, and responsive
reflow. `SObjectFieldDelegate.qml` selects the established shared input control
for the normalized field kind. Feature QML must not recreate those field
surfaces or maintain another widget-class mapping.

The Add/Edit form uses a responsive column layout. It keeps one ordered field
column at narrow widths, then repositions the already-created field cards into
two or three independently packed columns when the window has enough room, so a
tall field does not leave a gap below its shorter neighbor. Resizing does not
reload the server schema or recreate another field model; the shared form
scrollbar continues to own any remaining vertical overflow.

## Supported field semantics

The shared editor delegates cover verified server widget semantics:

- text and plain multiline text;
- boolean;
- date/time in the server format;
- select/enum with separate labels and values;
- user, project, process, pipeline, and task-status option fields;
- read-only parent/relation presentation;
- password update without exposing the current value;
- read-only thumbnail;
- preview selection with real local thumbnails, multiple image picking, and
  drag-and-drop.

Unknown widget classes produce an explicit unsupported-field error. They are
never silently replaced with a checkbox or generic string field.

## Add and Edit lifecycle

- Add uses the active Search Type or explicit related-parent context.
- Add can switch from one object to a batch of 2–100 objects. Numbering is
  optional. The token buttons insert `{n}`, `{n:02}`, `{n:03}`, or `{n:04}` at
  the active text-field caret for expansion during Preview; arbitrary Python
  formatting is never evaluated. Every marked text field receives the same
  object number.
- Batch Preview creates local drafts only. Previous/Next keeps the complete
  field set for each future object, including a distinct description or set of
  preview images. Create sends the reviewed drafts through TACTIC's native
  multiple-insert call; no object is written before that final action.
- A batch refreshes the current result once. Its selected preview images are
  checked in sequentially and silently after object creation. They never enter
  or open the user's global Commit Queue, and existing queue rows are untouched.
- Edit uses the selected object's search key and current values.
- Related Add keeps parent key, schema relationship, instance type, and native
  instance path in Python.
- Required and basic type validation runs before submission; server validation
  remains authoritative.
- Create/update uses the existing TACTIC EditWdg/commit API through
  `env_inst.server_pool`.
- While loading or saving, fields and submit actions are disabled and duplicate
  submit is ignored.
- Failure remains in the window and supports a deliberate retry.
- Success closes the editor and runs the normal targeted refresh.
- Cancel before submission has no server side effect.
- Reopen starts a fresh session and cannot receive a completion from an old
  request.

Generic file attachment/check-in remains a separate workflow; it is not
invented as a database-column delegate.

## Link SObjects ownership

`SObjectLinkController` owns one explicit source object, relation schema/path,
available candidates, linked records, selection, local move plan, and the final
server diff.

The title clearly states which source object is being linked to which target
Search Type/relation.

## Loading and search

- Available and linked objects load asynchronously through the existing TACTIC
  APIs and server pool.
- Instance relations use the original schema path and instance type.
- Child objects opened from an expanded result carry their own source identity;
  the controller never falls back to the top-level selected object.
- Search uses the common application search control, suggestions, tags, and
  supported filter syntax.
- Response identity includes source, relation, query, and generation. Scrolling
  or changing a query cannot apply an old page.
- Candidate paging is continuous and preserves scroll position.
- Stable search key identity prevents duplicates across pages and between the
  two panels.

## Selection, move, and drag/drop

- Click, Ctrl selection, and Shift range selection share one selection model.
- The arrow action moves the selected identities to the opposite local panel.
- Dragging one selected row drags the complete selected set; dragging an
  unselected row first makes it the current selection.
- The drag visual shows the grabbed records and count.
- The destination panel displays a clear accepted drop plate and insertion
  feedback.
- Both directions are supported.
- Dropping does not call the server immediately. It changes the local desired
  set, rejects duplicates, and preserves list scroll.
- Panel surfaces, divider, corners, and scrollbars use the shared dock/control
  styling.

## Save and cancel

Save computes only the difference from the original linked identity set and
uses the native instance-relation mutation API with the original parent key,
instance type, and schema path.

Cancel discards the local diff. Load/save errors remain visible and retryable.
Success triggers the normal targeted refresh so cards, expanded children,
details, and relation indicators agree.

## Verification

Automated tests cover Add/Edit schema generation, validation, stale response,
submit guard, Link source propagation from children, available/linked loading,
paging, duplicate prevention, Shift selection, arrow movement, drag/drop in
both directions, save diff, cancel, and QML loading.

Manual testing is required for server permissions, project-specific EditWdg
classes, instance relations, large linked sets, common-search suggestions, DnD
visuals, narrow/wide layout, and scroll stability.
