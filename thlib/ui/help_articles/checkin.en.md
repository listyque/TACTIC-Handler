---
group: Workflows
icon: publish
order: 15
---
# Check-in and Commit Queue

> Check-in tools prepare files, metadata, naming, previews, and repository destinations before
> submitting operations to TACTIC.

Ordinary check-ins refresh the destination name before transfer. When earlier queue
items create new versions, the final filename can differ from its preview.
Custom naming scripts receive the current values for each file.

## Main controls

Drop Plate accepts files and matches them to objects. Naming Editor controls templates.

Commit Queue reviews prepared operations, options, dependencies, progress, errors, retry,
cancellation, and final submission. Preview images are added directly to a selected queue operation;
message and note attachments stay in their own drafts.

Dragging files over an object shows a smooth shared target for Publish and Attachment. Add Icon is
offered only when every dragged file is a TACTIC preview image: JPEG, PNG, or TIFF.

When Save Snapshot or an item drop contains multiple files, choose one grouped snapshot or separate
queued check-ins in file order. This choice applies only to the current batch and does not change
the Drop Plate default.

Dragging files onto a child relation creates one child Search Object per file, links it to the
expanded parent, uses the filename without its extension, and checks the file into publish. The new
object, snapshot, and direct or instance relation are committed together.

Before any upload, ingest checks the selected parent's existing children. Matching names pause the
batch and ask whether to update the exact existing items, skip them, explicitly create duplicates,
or cancel.

Add files on the relation opens the batch editor first. The batch editor can use project Ingest
Rules for file filters, path patterns, extra values, update matching, validation scripts, and
process scripts.

Scripts run in TACTIC with path, sobject, parent, and snapshot; the built-in Quick ingest remains
available when the optional rule table is absent. Commit Queue reveals the operation editor only
after an item is selected.

An empty queue shows a short starting hint instead of disabled settings and actions. The selected
object and snapshot preview share one summary.

The optional snapshot context branch is added or edited directly in that summary; an unchanged base
process is not presented as a custom context. Advanced options and the generated filename preview
expand on demand, and secondary preview or batch actions live in overflow menus.

Auto-clean remains in the queue header. The primary footer action submits all ready operations;
current and checked-only submission remain in the overflow menu.

Repository selectors show configured titles such as General while native codes such as base stay
internal. Process pipeline check-in modes control sequence, directory, multi-file, and versionless
behavior.

Files without an extension use the $FILENAME matching template and keep their exact name through
repository staging and TACTIC snapshot creation; no trailing dot or invented FILE extension is added.
When the selected repository resolves to the same path in Handler and TACTIC, Upload registers the
staged files in place instead of uploading and writing them a second time. When Auto-clean is enabled,
the Commit Queue removes each successful operation
and closes itself after the entire visible queue finishes without an error.

A failed or cancelled operation keeps the window open for review and retry. After a successful
check-in created in the current session, the affected branch refreshes while its parent sObject
remains selected. A publish started on the top-level sObject expands it and selects the direct
versionless `latest` snapshot without expanding its versions or the duplicate `publish` process.

Restored queue operations and completions after navigation stay silent. The existing process row
updates its disclosure state and snapshot count in place when that refreshed branch is published;
reopening the tree is not required.

When an attachment check-in creates the first attachment snapshot for an object, the result tree
adds and reveals the Attachment process even if built-in processes are normally hidden; an explicit
process-visibility filter still wins.

Prepared files in a shared repository are saved in one server command. A failed check-in
rolls back its database and repository changes through TACTIC; earlier completed queue entries
stay saved. Fresh naming is still requested before staging. HTTP uploads retain their upload
transaction. Servers using the query plugin need the matching updated plugin package.

## Usage notes

- Review the target object, process, context, repository, and filenames before starting a queued
  operation.
- A DCC scene save prepares data; the standalone application performs the check-in.
- At narrow widths, the queue and operation panels stay inside their split bounds; secondary labeled
  actions become icon buttons with tooltips instead of overlapping the neighboring panel.
- Matching Templates keeps template rows inside their pane, reserves a scrollbar gutter, and moves
  secondary ordering actions into an overflow menu at narrow widths.
- Empty files are valid check-in inputs: their size is saved as 0 for both versioned and latest snapshots. A missing file is still an error.
