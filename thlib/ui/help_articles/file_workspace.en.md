---
group: Workflows
icon: commit_queue
order: 17
---
# Perforce-like file workspace

**Client scope:** the full file workflow described here belongs to the
standalone Handler. Stream provides the shared server/API and browser inspection
and administration. Desktop checkout, local editing, shelving, submit, sync and
mass file transfers are not a browser workflow to duplicate.


Create a project with the **Perforce-like file project** template. Its `file_project` mode selects the separate file workspace in the Commit Queue dock. Classic projects keep Classic Commit Queue and their existing check-in workflow. Changing a Classic project's type does not migrate its data. Ordinary Search tabs remain available; managed file tables use the native file API and administrator inspection rules.

Handler is the desktop client for local files and transfers. Stream provides inspection and administration of the same server data. Browser inspection cannot determine whether a file changed on the desktop. Open local files, Explorer, Trash, Reconcile and large transfers in Handler.

Project mode is preserved through connection notifications, ping and temporary disconnections. Only changing the active project, signing out or switching the server changes/resets the file workspace; a connection-status update never opens Classic Commit Queue.

In Handler, the circular columns icon beside the view tabs opens the **View** menu; its tooltip identifies the menu.

The View button, tabs and toolbar actions share the same vertical center. When the tabs overflow, the horizontal scrollbar occupies a separate strip below them.

## Local-first workflow and following views

New files appear as Added; existing files are compared with Have, or published Head when no Have exists. Added paths are checked out in bounded batches without allocating blobs or upload tasks. Previously uploaded pending content is retained until explicitly reverted; adding other files does not upload them.

Reconcile opens a results tab containing local additions, edits, deletions and rename candidates. Unchanged files are omitted. Review the result table, select the changes to include, and choose **Add to changelist…**. The target dialog offers an existing or new changelist and sends no file contents.

A following **Files** tab shows the immediate files in the selected Depot or Workspace folder. Selecting a file keeps its siblings visible and highlights that file; Ctrl/Shift selection is preserved. Large folders use bounded pages, and selecting a file beyond the first page opens its sibling page. Clicking another file already on the page does not reload the list. Selecting a folder clears the previous file details. Workspace uses the local Reconcile cache, or server Have before a scan. Pending/Submitted and fixed-source Files tabs remain independent. **History** follows the selected file; pinned History tabs retain their file. New unpublished files have no submitted revisions.

Checkout/changelist and shelf target dialogs open modally in the center of the application. Drag their title bar to reposition them; Escape or Cancel closes them. Buttons use the shared Handler controls.


Files and History share one lower inspector with the same metadata fields, copyable values, description, preview and scrolling. Files shows the current file, Have/Head and Checked Out By; History shows the selected published revision and its Integrations. Preview remains lazy and revision-specific; changing files does not upload content.

## Selected-file History in Handler

History shows the selected file path and a collapsible file header above a compact revision table: Revision, Changelist, Date submitted, Submitted by, Type, Size and Description. Action icons distinguish additions, edits, deletions and moves. Type uses a stored file type when present, otherwise the extension; it does not invent a Perforce file-type setting. The table scrolls horizontally in narrow windows and virtualizes its rows.

The lower pane follows the selected revision and has **Details**, **Integrations** and **Preview** tabs. Details shows its exact path/revision, date, author, workspace, action, changelist and description. Integrations shows recorded source stream/change/version, or an explicit empty state. Preview requests only the selected published revision, on demand, and supports text, bounded binary samples and small images; changing the selection never displays old content as the new revision. A hidden History pane does not request previews. There is no Labels tab because the file-project server has no label system yet.

The splitter remembers its height independently from Files. Mouse/keyboard selection and Ctrl/Shift multiselection retain existing revision comparison, Get Revision, Save and Restore actions in the context menu. Following and pinned History tabs keep their existing selection behavior. Restricted changelist descriptions and workspace metadata remain hidden from unauthorized readers. The current API returns at most 1000 latest revisions; a notice identifies truncated history. This is Handler's desktop UI; Stream supplies the same authorized data and Help without a browser file-editing workflow.

## Stream editor and hierarchy

Open **View → Streams** for the stream table. Tree/List switches the presentation; disclosure follows the **Parent** relationship, independently from the stream's depot path. Double-click a row or use **Edit stream** in its context menu. Right-click empty space for **New stream**; right-click a stream for **New child stream**. The same editor opens from Stream Graph nodes. The centered modal editor can be moved by its title bar.

Create a mainline without a parent, or a development/release child of a mainline or the same type. Set its code, name, description, depot and parent. Existing codes, depots and types are fixed; name, description, parent and owner-only settings protection can be edited. Parent changes are cycle-checked (up to 255 ancestors) and serialized per depot. Settings have a separate revision check, so a file submit does not invalidate an otherwise unchanged editor. Native depot write rights, owner/admin protection and transaction triggers apply; failures roll back the edit.

A new real branch shares the parent's immutable published catalog without copying bytes or enumerating all files. Reparenting leaves published files, checkout bases and original branch ancestry intact. Graph parent links after reparenting are distinguished from original branch provenance; graph cursors also detect settings changes.

The tree loads 200 stream records at a time, retaining up to 2000. Filters apply to loaded records; parents outside the current set are shown in the Parent column until loaded. The editor suggests up to 1000 records, and accepts another parent code directly. This enumerates stream metadata, not file contents.

**P4 compatibility boundary:** mainline/development/release currently describe real branches and their parent hierarchy. Automatic merge-down/copy-up policies are not implemented. Virtual/task/sparse streams, inherited Paths/Remapped/Ignored, parent-view conversion, type conversion and P4 merge/copy status hints remain unimplemented. Virtual is explicitly rejected: it must eventually filter a real ancestor and submit there, not create another independent branch. The editor states this boundary and does not offer inert controls for it. Stream's browser remains inspection/administration only.

Reference: [Perforce stream specifications](https://help.perforce.com/helix-core/server-apps/p4v/current/Content/P4V/streams.create.html), [virtual streams](https://help.perforce.com/helix-core/server-apps/p4v/current/Content/P4V/streams.virtual.html), [stream views](https://help.perforce.com/helix-core/server-apps/p4v/current/Content/P4V/streams.views.html).

## Trees and work views

The left side switches between **Depot** and **Workspace**. Directory children load only on disclosure, in bounded pages. Workspace uses the reconciled local cache, including untracked files and empty directories, or server Have before a local scan. **Reconcile** refreshes local state in a worker.

Open right-side views through **View**: Files, Pending, Submitted, History, Shelved, Reverted, Conflicts and Transfers. Add, rename, close, reorder and configure multiple view tabs. Folder selection updates a following Files tab; it does not replace Pending or Submitted. Fixed-source tabs keep their source and prefix. History can follow file selection or pin its file. Unsaved descriptions must be saved or explicitly discarded before leaving.

The selected workspace, numbered changelist and operation context remain visible. Use **Actions**, **Workspace actions**, **Tools**, row context menus and explicit action buttons. Narrow layouts retain commands through menus and horizontal scrolling. Existing dock controls move, detach, maximize and restore the panel.

Expanding a changelist reads its current server revision and updates the displayed metadata. Further pages remain pinned to that revision: if another client edits the change, refresh before continuing. Editing, checkout and submit still require the expected edit revision. Depot folder selection preserves independent Pending/Submitted views; Handler navigation reads do not mark a file transfer as running.

### Desktop layout and changelist details

The right working pane starts at the top of the panel. Workspace selection,
Depot/Workspace navigation and Actions/Tools occupy the left column; View tabs
remain independent on the right. The plus button creates a changelist. Secondary
commands live in menus and row context menus rather than repeated toolbars.

Single-click a changelist to select it; the disclosure arrow expands its files.
Double-click its row, or choose **View changelist** in the context menu,
to open a separate native window. It shows state, workspace, creation date, owner,
access type and stream above the description, followed by collapsible **Files**,
**Shelved files** and **Tasks** tables. Related shelves retain their own numbers;
choose a shelf to inspect it. Files show name, folder, conflict-resolution state,
extension and pending action. The task table shows permitted linked Task Manager
task codes, statuses and descriptions. Restricted changelist metadata remains
owner/admin-only.

Opening sends one bounded native read request. File pages contain up to 200 rows;
Next page reads further contents at the pinned edit revision. Refresh returns to
the first page; if another client changed the list, refresh before paging again.
Each table has shared scrollbars, including horizontal scrolling in narrow windows.
The window keeps the opened changelist identity. **Edit** enables description
editing for the owned pending change; **Save** uses the native API. Submitted,
foreign and shelved lists remain read-only. Closing discards an unsaved draft.
Submit, Shelve and Revert remain in the footer action menu and main context menu.

Drag the horizontal splitter above **Log** to change its height. Hide it with the
header close button or **View → Hide log**; restore it through **View → Show log**
or the terminal button in the footer. Height and visibility survive reopening
the panel and restarting Handler. Hiding the log keeps its records. The compact
footer shows workspace/selection when idle and phase, counts and progress during
an operation. This desktop layout belongs to Handler; Stream retains its separate
inspection/administration interface.

### Refresh and query volume

Handler requests one bounded `workspace_snapshot` for Refresh and dependent
updates after normal file operations. Metadata, tasks, changelist pages and
Head/Have/checkout holders share a native command and its request context;
the selected changelist page is reused by the expanded row. Up to 32 expanded
changelist pages and 16 directory pages are included. Further tree pages and
off-page selections still use bounded reads when needed. A snapshot does not
create changelists, scan the entire depot or upload files. Browser inspection
groups its startup metadata through the same read-only batch API. The desktop file inspector requests details/preview only while its Files view is visible.

The server caches records only within a read request. Each operation retains
project/depot/workspace authorization; the next request reads current records
and grants. Several table and security/schema reads remain inside one command;
one network request does not imply one SQL statement.

Changelists are ordered by number, newest first. State filters precede paging;
remaining visibility filters fill the page with a bounded scan and continuation
cursor. Empty pending changes remain visible. Ownership transfers update the
owner index used by My changes. Create retries with the same `request_id` return
the same changelist; changing the payload under that id is rejected. Existing
empty changes are retained for explicit inspection/deletion.

Details and Preview share one file inspection request. Activating a changelist
view groups its list and selected file page. Reconcile validates rename sources
in native batches of at most 1000 paths. History prefetches bounded indexed
segments; only the selected version's previous links are returned, with submitted
roots checked for every version. Schema/project metadata is reused within the
request and invalidated by native structural writes and rollback.

Transfer status does not reload the workspace. When task progress is unchanged,
polling backs off to at most two seconds; changing progress resets the delay.
Consequently an idle task's completion can appear up to one polling interval
later. Errors, timeouts and retained journals still behave as before.

The desktop confirmation names the operation and explains its effect separately.
Cancel and Escape close it without running the action; the named action button
confirms once. Revert changelist keeps local files by default. Stream's browser remains
read-only for these file actions and does not expose this mutation dialog.

## Selection and file commands

Single click selects; double click opens the relevant file/history. Ctrl toggles, Shift selects a range, arrows and Shift+arrows move/extend selection. Right-click preserves a selected group. Ctrl+A selects loaded rows; Escape clears them. Selection survives refresh, paging and view switches, and clears when a new working context is created.

Explicit selection is bounded to 1000 items. **Select all matching server files** / Ctrl+Shift+A creates a private, pinned server selection instead of loading every file into the client. Handler can export it as a streamed JSON-lines manifest. Whole-query checkout/move/delete jobs belong to the scale stage; an all-query token is not silently converted to loaded-row mutations.

Use the file menu for ordinary/exclusive checkout, history, sync, local comparison, staged rename, move, revert and copy paths. The target picker offers owned pending changelists in the current workspace or explicit creation of a new one. Read-only mappings, exclusive checkouts held by another user and incompatible stream selections explain unavailable commands. Native checks remain authoritative.

**Get latest selected files**, **Get latest folder subtree** and **Get latest workspace** have different scopes. Sync protects modified/untracked local data and updates Have after acknowledged writes. Inline local-vs-Head diff supports UTF-8 text up to 256 KiB; save a revision for external binary/large-file comparison. Staged depot rename preserves version lineage; it does not silently rename or overwrite local copies.

Configure column width, order and visibility. Have/Head and checkout holders come from a bounded native status request. Local status comes from the desktop cache/stat inspection; Reconcile confirms content. Filters and sorting apply to loaded rows. Back, Forward, Parent, address navigation and **Reveal in other tree** locate files without enumerating a large directory. A revealed branch initially shows only the authorized ancestor chain; collapse and expand it to browse siblings.

## Changelists and drag/drop

Changelists have unique project numbers, descriptions, owner/workspace/stream, state, file/byte counts and conflict counts. Expand their files and shelf children. Filter mine, this workspace, this stream or all permitted changes. Other users' published/shelved data is read only according to depot permissions; private pending work is inspectable only by administrators. Editing also requires ownership and the current workspace.

**Go to changelist** opens a numbered, independent view. Copy its number or a Stream inspection link for sharing. Drag a selected group between owned pending lists; drag local Workspace/Files rows to open their paths without transferring contents. Drop a shelf to begin unshelve in the target. Hover expands a valid target, edges scroll, Escape cancels. The command checks source/destination revisions and permissions before changing server metadata.

Drop files/directories from the active workspace onto an owned pending changelist: addition starts without confirmation and keeps workspace-relative paths. Files outside that workspace are refused with one OK notice. A mixed inside/outside root selection is refused as a whole before any server request, upload or copy. Discovery and local comparison stay in the worker; native mappings, permissions and edit revisions remain authoritative.

## Deletion and publication

- **Revert** is a direct file-menu action for owned opened files in the active workspace, including a selected group. The options dialog also opens for **Revert changelist**. By default, local files are kept. **Delete files not in depot** moves only newly added local files absent from the published stream to Trash after the native server revert succeeds. Tracked files and rename lineage are preserved. Current Head, other opens, mappings and local fingerprints are rechecked; blocked/changed files stay with a warning. Whole changelists are read in bounded pages, and selected rename partners are reverted together. **Remove selected from changelist** retains its metadata-only behavior.
- **Mark for depot deletion** stages a deletion in a chosen pending list. Submit publishes it; removing that pending edit undoes it.
- **Move local copies to Trash** affects desktop copies only. It preserves server versions and requires confirmation.
- **Delete changelist / shelf…** works for one or several selected changelist headers (Ctrl/Shift selection, or Delete). Confirmation names the selected numbers. Empty pending lists and owned shelves are retired together through one native transaction; a stale revision, denied permission or trigger error cancels the entire batch. Local files are always kept. Nonempty pending lists require moving or reverting files first. User deletion never directly runs physical GC.
- **Revert unchanged files** in a changelist context menu compares the entire owned pending changelist, including rows not loaded in the UI. The file-menu variant compares only selected paths. Both hash current local contents against the original checkout base, preserving changed, added, missing, deleted, renamed and unmapped files. No contents are uploaded and no local files are removed or overwritten. No matches is an informational log result.
- Comparison runs in the background with progress and cancellation, in pages of up to 1000 files and a temporary disk-backed candidate list. Recheck candidates before releasing checkout. Up to 1000 matches use one native removal; larger sets use the existing files service for one atomic bulk removal. Rights, current revisions and triggers are checked; a late failure rolls back the whole removal. The changelist stays pending, including when empty. Stream's browser does not offer local comparisons.
- In History, select a nondeleted published revision and **Restore revision in changelist**. It stages a new version using existing immutable bytes. An existing pending edit at the target must be moved/reverted first. Native trigger failure rolls back the whole restore.

After Reconcile, select changes and use **Add to changelist…** to choose an existing or new pending changelist. Adding paths, checkout and Reconcile send metadata only. File contents stay local until confirmed Submit or Shelve. Missing files become deletion proposals; they are never deleted from the depot implicitly. Submit publishes the whole changelist atomically through native permissions and triggers.

## Operation log

The bottom **Log** records the time, operation and outcome, with the affected path
when relevant. Its splitter changes height; hide/show, copy and clear use the
compact controls and View menu;
**Debug Log** opens the full diagnostics explicitly. The in-memory panel retains
at most 1000 operation summaries, not one record for every file/progress callback.
Changing project or signing out clears this workspace's panel.

A local modified/untracked file stops sync with a normal `blocked` result. It is
not overwritten and no exception/traceback is generated for this condition.
Preserve or stage your local changes, then retry/resume the same transfer task.
Unexpected failures are logged with their complete traceback in Debug Log rather
than automatically opening an exception dialog. Browser Log covers its server
inspection/administration operations; it cannot detect desktop file changes.

Stopped downloads are now recorded on the server as `blocked`, including local edit conflicts and recoverable download errors. Retrying the same selection resumes its pinned task. Requesting another file, folder or revision in the same workspace and local root replaces the stopped task atomically, keeping local edits, partial files and confirmed Have entries. A download still in progress or belonging to another local root is not replaced implicitly. Stream displays the stopped task in Transfers and can cancel it. Tasks left active by an older client, a killed process or a fully lost connection may need cancellation in Transfers before changing the selection.

## Get Latest and Get Revision

Right-click a file, selected files, any nested folder, stream, depot or workspace.
**Get latest** updates only that selection. **Get Revision…** uses the same scope:
latest, revision number of each file, submitted changelist number, submitted
stream revision, or state as of a date/time. The history menu can get its selected
revision. Folder/depot/workspace operations include their mapped descendants and
respect exclusions; other mapped streams keep their Have and local copies.

File revision #N means #N separately for each path. A missing revision leaves
that path and its Have unchanged and produces a warning in the bottom Log.
Changelist #N means the complete state published by that change, including removal
of previously synced files absent from that state. Changelist/stream numbers are
specific to a stream; select that stream or its folder when mappings span streams.
ISO dates accept a timezone; omitted timezones use UTC. A date without a time
includes the entire UTC day. New submissions retain microsecond timestamps.

**Force overwrite local files** is explicit and off by default. It repairs dirty
or missing local copies even when Have already points at the selected revision,
and removes tracked local copies absent from the selected submitted state.
Preserve local changes before using it. Without Force, a dirty/untracked target
returns a blocked result. If the matching download was blocked, enabling Force
restarts only that same scope; another running selection must be finished/cancelled.
Downloads pin their manifests, verify bytes and acknowledge Have after local writes.

Older projects require a bounded, resumable administrator revision-index upgrade.
Handler performs it before the first historical request, showing index progress;
an ordinary user must ask an administrator to upgrade. Classic is unaffected.
Stream shares the historical inspection API and SDK; desktop sync controls remain
in Handler, because the browser does not own the desktop workspace.

## Dragging Depot folders into a changelist

Drag a Depot file, folder at any depth, or a stream into an owned pending
changelist of that stream. The server opens the contained published files for
ordinary checkout, preserving their paths; this does not move Depot directories
or upload/download file bytes. Folder contents use the target changelist's
immutable base revision. Rebase an older change if newly published files are
needed. Workspace directory drops are resolved through that change's mappings.
Excluded/unmapped paths are skipped; read-only mappings and another user's
exclusive checkout reject the operation. Overlapping folders and explicit files
are deduplicated. Empty folders with no mapped published files produce a concise
error in the operation Log.

The client sends at most 1000 selected roots, not an expanded list of all their
descendants. The native server command visits paths in chunks of at most 1000,
while keeping the entire drop in one transaction: a late lock or trigger failure
rolls back previous chunks as well. The completed operation reports the number
of opened files. Explorer drops open workspace paths and compare local contents without uploading them.
Stream administration uses the same metadata operation; the browser does not
access or discover desktop file contents.

## Show in Explorer before sync

**Show in Explorer** remains available for a mapped file in a changelist even
when the desktop copy has not been synced or is missing. Existing local files
are selected in Explorer. For absent copies, Handler opens the nearest existing
parent folder inside the configured workspace and records an informational
bottom-Log notice with the intended file path. It creates no folders and downloads
no bytes. If the workspace root itself is absent or unset, no Explorer process
is started: choose the local root or use Get Latest, as indicated in the Log.

Source paths are mapped using the actual selected file and workspace, including
when the right-hand Files view shows local rows while a changelist file is
selected. Ordinary open/delete actions also report an absent local copy as a
normal unavailable outcome; they do not launch an editor or attempt Trash.
Unexpected launcher/transport failures still retain complete Debug Log diagnostics.
The browser Stream interface cannot launch desktop Explorer or inspect desktop
folder existence; it retains path copy and Reveal in other tree instead.

## Recovery and limits

Stop waiting keeps the server task and journal; resume with the same root. Cancel server upload restores the original draft. Check a lost Submit/Have response before repeating publication. Changed sources require cancellation and a fresh transfer. Enable the server `files` service and explicitly restart after changing services; configuration saving does not restart the server. Metadata contention marked `file_project_busy` uses bounded backoff; permissions, hooks and checksums are not blindly retried.

History/loaded change branches are bounded to 1000 records and previews to 256 KiB. Server query snapshots are paged. Full lifecycle comparison editors, per-file transfer accounting, whole-query mutations and million-file/TB acceptance remain in the complete three-stage checklist. Source tests do not certify a physical million-file/TB or packaged EXE/Electron installation. The Python 3.14/PySide6 shutdown Property ResourceWarning remains a recorded runtime issue. Installation/backup instructions are in `FILE_PROJECT_DELIVERY.en.md`; back up databases and private blob storage together.

## File lifecycle and the Files inspector

Files has a lower inspector with independent **Details**, **Checked Out By** and
**Preview** tabs. Details shows depot/workspace location, selected/Have/Head
revision, size, author and submitted change. Handler also inspects the local
location and modification date. Checked Out By lists owner, workspace, numbered
change and ordinary/exclusive mode. Preview requests only the selected file:
text is limited to 256 KiB, small supported images are displayed, and binary files
show metadata and a short hexadecimal sample. Browser inspection does not read
the desktop filesystem. Changing inspector tabs does not replace Pending or
Submitted.

On Windows, background directory notifications invalidate local indications;
**Reconcile** computes authoritative content differences in a cancellable worker.
Its last complete local index survives cancellation. The root `.tacticignore`
supports patterns, comments and `!` exceptions. Read-only/excluded mappings stay
explicit. Unique matching added/missing content can be reviewed as a rename;
ambiguous matches remain separate add/delete candidates. Select changes and use
**Add to changelist…** to choose an existing or new pending target. This registers
metadata only; Submit/Shelve compare and upload the current local contents.
Prepared server edits can remain pending after a stopped upload; Resume uses the
same task/outbox. Submit is the atomic publication boundary.

Shelving supports whole changes, selected files, replacement and selected shelf
deletion. Replacement preserves the shelf number and archives the prior contents.
**Compare pending with shelf** includes files present on only one side. Review
the exact pages before submit, shelving or integration; stale revisions reject
approval. Confirmation uploads new/modified files before publication; unresolved integrations block submit.
**Shelve and revert** saves a shelf, then reverts pending server edits; local files
remain on disk. Unshelve copies a shelf into a pending target and can produce
conflicts. Ownership handoff is different: the current owner offers to a named
login and that recipient explicitly accepts into their workspace. Stream rights,
writable mappings and locks remain enforced. Copy a numbered change/link from
its menu to share it only with permitted users.

Conflicts expose real Base/Ours/Theirs. Resolve explicitly selected paths with
Ours/Theirs or a manually merged file; rename pairs resolve together. The Resolved
tab permits undo before integration finishes. Revision history records change,
author, time, action and description. Handler compares local/Have/Head, two
published revisions, pending/shelf and conflict sides. Small text is compared
inline; binary/large files can use an installed comparison application selected
explicitly. Remote comparison copies are verified and kept in the workspace cache
for detached viewers; cache retention is still an open acceptance item.

Transfers lists per-file states and received bytes in bounded pages. Manifested
upload names/checkouts appear before bytes arrive. Clearing completed tasks also
clears completed progress. Rate/ETA are shown only after measurable samples;
verification/staging uses phase counts rather than claiming more upload bytes.
Read-only views remain available during Handler writes. Lost submit replies are
reconciled against the existing change before retrying publication. Full
restart/network recovery and physical million-file/TB acceptance remain open in
the complete three-stage checklist; working controls do not declare those tests
complete. Classic uses its existing interface and workflow.

## Editing and submitting a changelist

Right-click empty Pending space to create a numbered changelist. In Handler,
drop Depot files or folders onto it: missing mapped local copies are downloaded
from the changelist base revision; existing local edits are preserved. Explorer
drops stage existing active-workspace files without confirmation or copying. Double-click a pending file
to open its associated editor. Local modification badges also appear inside the
expanded changelist. Close view tabs with their cross; reopen them from View.

Submit and Shelve inspect opened local files before the review without uploading.
Cancelling review transfers no bytes. Confirmation uploads only the reviewed
changed files, then publishes or shelves them. Files outside the changelist are
excluded. If local content or the changelist revision changes after review,
review again. Missing local copies produce a bottom-Log notice. Interrupted
confirmed transfers retain their journal for explicit resume. Stream provides
inspection and administration; local filesystem work belongs to Handler.

### Submit window

**Submit** opens a centered, modal window that can be dragged by its header.
Edit the description at the top. Check the files to publish in the first list;
the second list displays related shelves, with their own changelist numbers.
Shelves remain separate snapshots and are kept after Submit; this list is read-only.
File, shelf and task lists use bounded pages. Select all applies to the whole
changelist, not just the current page; at most 1000 explicit selection exceptions
are allowed. Unchecked files move to a new pending changelist atomically with
publication; their local contents are neither uploaded nor deleted.

Additional options guard files changed after conflict resolution, reopen
submitted files for checkout, and restrict changelist metadata to its owner and
administrators. Restriction covers the description, contents and linked tasks;
published file access still follows depot rights. Choose whether unchanged files
are submitted as new revisions, reverted from checkout, or left pending. If no
files remain to submit, the command fails without removing or moving anything.

Select existing **Task Manager** tasks (up to 100) and a status after Submit.
The status selector uses the permitted statuses common to the selected tasks'
configured workflows; **Keep current status** only saves links. Tasks are linked
in the changelist metadata. Status changes run through native task commands after
successful file publication. If a task changed concurrently or its update fails,
files stay submitted and Log reports the problem. Use **Update linked task statuses**
on the submitted changelist to retry; a changed task is never silently overwritten.

**Apply** saves the description, access restriction, task links and requested task
statuses without closing; **Save** saves the same metadata and closes. Neither
uploads file contents nor changes task statuses. File selection, unchanged-file
policy, reopen and conflict guard apply to this Submit attempt. **Cancel** closes
without submitting; already applied metadata remains saved. Only confirmed Submit
uploads the selected new/modified contents, then atomically publishes the selected
change and creates any remaining/reopened pending change. Missing local copies
must be restored before review. Classic and the browser inspection interface do
not acquire this desktop workflow.

## Server selections and workspace setup

Selected server query actions queue a pinned server batch for ordinary/exclusive
checkout, move, selected revert or mark-delete. Applying progress precedes a
whole-transaction commit; an error or Cancel rolls back the batch. Stop waiting
keeps the server job. Transfers can refresh, cancel or resume waiting without
loading its complete path list. Long SQLite mutations serialize project writes;
million-file/TB physical throughput is not certified.

Workspace setup edits mappings, exclusions and writable flags in rows; Technical
JSON remains available. Preview shows where a sample depot path maps. Cancel
restores the active workspace root/settings. Switching keeps pending changes
and server tasks in their previous workspace. A free-space check at setup time
does not reserve space for a later download.


Dragging local Workspace/Local Files rows or Explorer files already inside the active workspace quietly opens their paths in the chosen pending changelist without uploading contents. Selected folders are discovered recursively in the worker, with overlapping roots deduplicated. Mappings, exclusions and depot rights remain enforced. Outside Explorer files are never copied into the workspace. Internal pending-file moves, Depot checkout and shelf operations keep their confirmation/review flow. These filesystem operations remain desktop-only; Stream provides server inspection and administration.


## Complete selections and changelist handoff

File checkboxes start a file selection without retaining a selected changelist
header. Ctrl-selection can still explicitly mix objects; incompatible commands
then explain the restriction. File commands validate the complete selection. Folders, other changelists,
read-only mappings, depot write restrictions and conflicting checkouts explain
why a command is unavailable. These cached hints do not replace the server's
permission, revision and lock checks when the command executes.

Dragging files shows the action and selected-file count; a selected folder or
stream is labelled as a root, not an invented descendant count. Invalid stream,
workspace, busy target and same-change drops are rejected. Cancel closes the
confirmation without changing server contents.

Changelist actions → Move all files uses an immutable server selection, ignoring
the Files view's name, path and status filters. Choose another owned pending
changelist in the same stream, or explicitly create one. The files service must
be running for this server batch. A nonempty Delete offers Move files or Revert;
local files are kept. Delete never silently discards pending edits.

Copy a changelist number or link and paste it into Actions → Go to changelist.
Links must identify the current project. Shelves are inspectable under existing
depot read permission; other users' pending changes remain private. Unshelve on a
shelf offers a target picker. Shelf drops and menu Unshelve show the same
integration preview before modifying target files. Cancelling that preview
keeps any explicitly created target empty and preserves the shelf.

## Workspace switching and download space

Save the active changelist description before switching workspace. If pending
changes or server tasks exist, the confirmation keeps them in the previous
workspace; Cancel leaves the active workspace unchanged. Switching preserves tab
configuration and column/filter preferences but clears workspace-bound loaded
rows, selection, inspector, review, navigation and progress. The new workspace
uses its own local comparison cache. Previous local bytes, Have and server jobs
are retained; switch back or use Transfers to inspect their work.

Get Latest/Get Revision checks an absolute directory root and free disk space
before receiving each bounded manifest page. The estimate includes temporary
replacement files and credits resumable large-file partial bytes. Existing target
files are not counted as free space. A shortage returns a normal **Sync stopped**
warning in the bottom Log before that page's payload is requested. The task stores
the required/available byte counts; confirmed earlier pages keep their Have.
Free space and repeat the same selection to resume the same task. This is a
conservative page estimate, not a reservation against other processes consuming
disk space. Mapping exclusions and collision guards still run on the native API.

## Recovery, catalog views and bounded retention

The toolbar shows **Resume interrupted operation** after an interrupted upload,
download or local rename. Journals are scoped to server, login, project, workspace
and local root; they contain no ticket. Resume uses the original selected sources
and native task/receipt. A lost successful Submit response reads the submitted
change instead of publishing again. A pending Submit returns to Review. Keep the
workspace cache and upload journal until recovery completes; do not point a
foreign journal at another workspace. Resume retains the original active-workspace
source selection; outside-workspace Explorer sources are not imported or copied.

Rename moves local dirty bytes after the native rename succeeds. If the local
move is interrupted, **Resume local moves** replays its receipt and completes the
same move; an existing different destination is never overwritten. Reconcile
updates local/Have/Head state and per-change unstaged file/byte counts. After a
watch event or changed server edit revision, unknown counts explicitly request
Reconcile rather than rescanning millions of files on every click.

**View** opens Workspaces, Streams, Depots, storage inspection and **Stream
Graph**. Lists are paged; graph nodes and connections are bounded and pinned to
the current submitted heads. Branch/merge links refer to actual published changes.
Refresh when the graph's heads change. Graph zoom and normal tab/column/splitter
preferences restore; deep expanded folders and selected files outside the first
page are sought directly. Trees retain at most 8192 rows, changelist children
8000 across loaded changes, 1000 per change, and 128 file-page cursors. Reopen a
released branch to reload it; whole queries still run on the server.

The operation footer distinguishes scan, manifest, upload, verification, staging,
download and submit. Rate and ETA use measured byte progress only after a real
sample interval; they reset between phases. The last staging chunk waits more
frequently, without increasing polling throughout a million-file job. File errors
show the path plus overall failure in the Log; Debug Log retains diagnostics.

Stream exposes inspection and administration. Its file-project panel has no
checkout, local edit, shelve, submit or bulk transfer commands. Ordinary Search
tabs and administrator managed-record inspection remain available. No browser
view infers the state of a desktop file.


### Depot editor and storage administration

In **View → Depots**, select a depot and choose **Edit depot**, or use **New
depot**. Code identifies the depot and cannot be changed after creation. Name is
editable; Repository selects a configured server alias or **Project storage**.
Changing Repository affects new uploads only: existing versions retain their
original contents and location. Depot paths are case-sensitive. Configure
`file_depot` read/write access in **Administration → Rules**. Only administrators
may create or edit depots. The form and its unsaved changes survive switching
file-workspace views. **Save** checks the original revision. On conflict, keep your
text, or **Reset → Cancel → Edit depot** to reopen the latest revision.

**View → Storage administration** is administrator-only. It shows allocated
bytes/files and index readiness. For an old project, **Initialize storage**, then
**Continue storage index**. Indexing uses bounded batches outside the UI thread;
**Stop waiting** retains the server cursor, and Continue resumes it. Finish the
index before saving policy or starting cleanup.

Quotas are whole bytes and file counts; zero means unlimited. Parallel transfers
must be 1–16. Retention, quarantine and the automatic cleanup interval are in
seconds. Zero retention disables record expiration; zero automatic interval
disables scheduled cleanup. Quotas and policy revisions remain exact up to
9223372036854775807. **Save storage policy** applies the draft atomically, with a
revision check. Refresh retains edited drafts. After a conflict, **Refresh →
Reset** loads the latest saved policy; entering another view retains the draft.

**GC dry run** counts unused objects without deleting them. **Run safe GC** asks
for confirmation and uses the saved retention/quarantine policy; save policy
changes first. The server's `files` service executes cleanup. The UI explains
when that service is disabled. Status includes phase, scanned objects,
candidates/bytes, expired records, quarantine, purged objects and errors. Active
status refreshes automatically and survives reopening the view or application.
**Cancel GC** stops the active task; already expired or purged records are not
restored. Quarantined objects remain subject to the saved grace period. Native
GC rechecks references before physical deletion. No UI action invokes internal
GC steps or chooses arbitrary filesystem locations.

Save or reset edited Depot and Storage drafts before changing projects.

A task with state **error** has stopped and keeps its diagnostic message. After
fixing the cause, start a new **GC dry run**, then confirm **Run safe GC** if needed.
Failed tasks do not automatically resume or become successful after a server update.

In Handler **Reconcile**, **Ctrl+A** selects up to 1000 currently loaded rows
matching the name/state filters. **Escape** clears the selection. The target
changelist preview is built when **Add to changelist…** opens and is released
when it closes; closing the preview keeps the file selection. Browser Stream
provides inspection and does not run local Reconcile.

## Project tasks without object selection

In full Task Manager, + also works when no object is selected. It creates a task owned only by the current project; no asset, shot or other work object is needed. The task uses the standard task status workflow and initially assigns the current user, so it appears in My tasks. Edit and save it using the existing task controls, then open Task Inspector as usual. In a Perforce-like file project, select it under Link tasks to changelist in the submit dialog. With an object selected, + keeps creating a task for that object.

## Work views and metadata

Work-view tabs keep their natural caption widths. When they do not fit, use the
horizontal scrollbar; closing a tab remains separate from selecting it. The
View menu opens the available file, changelist, history and metadata views.

Select a workspace in its metadata list to inspect its server record. Handler
also provides Switch workspace, Edit workspace and Workspace setup. Stream's
browser view is inspection and administration: local workspace switching,
mappings, checkout and Submit remain Handler operations. Stream Graph supports
inspection and zoom; native stream creation/editing stay in Handler.
