---
group: Reference
icon: window-restore
order: 25
---
# Windows and modal editors

> Functional tools open in native windows with themed content. Ordinary utility windows can stay
> beside the workspace; modal editors block their owner until their prepared operation is applied or cancelled.

## Common window behavior

Every functional window uses the operating system frame for moving, resizing, minimizing and closing.
Its content follows the current Handler theme. Size and position are saved after movement and clamped
to a usable minimum when restored.

**Reset layout** restores safe default geometry for the main workspace, docks and native windows. It
does not close currently open tools or delete their project data.

Menus, combo lists, calendars, suggestions and context panels are transient popups, not entries in
this window catalog. They close after a choice or outside click and remain within the active monitor's
available work area.

## Modal versus nonmodal

| Type | Behavior |
| --- | --- |
| Nonmodal utility | Can stay open while the main workspace remains interactive. Reopening brings the existing window forward. |
| Modal editor | Blocks its owner while a prepared, potentially destructive or context-sensitive change is resolved. |
| Child modal | Belongs to the window that opened it, so an error or confirmation does not appear behind its active parent. |

Context-sensitive editors restore geometry but never reopen automatically after restart. Their old
selection, relation or prepared payload could no longer be valid.

Closing a window is not always equivalent to Cancel. Configuration asks its controller to resolve
unsaved changes; filter, repository-sync and watch-folder editors explicitly cancel their draft;
schema and dependency editors discard or request closure through their own owner.

## Configuration and project setup

| Window | Purpose and close behavior |
| --- | --- |
| **Configuration** | Navigates Server, Repository, Project, Check-in, Global, Appearance, Cache, Tasks and Maya pages in one settings session. Closing resolves unapplied settings. |
| **Server Settings** | Opens the server connection page directly: URL, proxy, ticket, test and server updates. |
| **Project Settings** | Opens the active project's server-provided configuration page. |
| **Create Project** · modal | Collects project identity, type and initial setup, validates them, then creates through TACTIC. |
| **Edit Project** · modal | Edits the prepared project only; closing does not silently apply changes. |
| **Check-in Options** | Opens check-in/check-out, naming, transfer, preview and sequence options directly. |
| **Global Settings** | Opens account-wide behavior, communication, update and notification options. |
| **Maya Scene** | Controls focus after open/save and Maya-specific preparation behavior. |
| **Server Presets** | Edits stored server login presets; opening starts a draft session, Cancel restores it. |

Appearance, Cache and Task Settings are pages inside Configuration rather than separate registered
native windows.

## Search and object windows

| Window | Purpose |
| --- | --- |
| **SObject Report** | Readable report for the selected object's values, relations, tasks and snapshots. It refreshes when opened. |
| **Filter Processes** · modal | Selects processes for the prepared Search or sidebar context; Apply returns the selection, Cancel restores the incoming one. |
| **Quick filters** · modal | Creates, orders and edits reusable filters for one Search Type. Its script/tree selector uses the prepared Search context. |
| **Columns Editor** | Chooses and orders result columns for the current Search Type and view. |
| **Advanced Search** | Builds field, relation, AND/OR and TEL rules for the active Search tab. |
| **Sidebar Editor** · modal | Builds shared sidebar tabs, links, saved searches, scripts and workspace layouts, with an explicit XML apply path. |
| **Search preview** · modal | Runs a sidebar saved-search draft without replacing the user's real Search tabs. |
| **Add SObject** | Creates an object of the prepared Search Type from server-defined fields. It requires fresh context and does not reopen on restart. |
| **Duplicate SObject** | Reviews target name, related data and options before creating a distinct copy. |
| **Delete SObject** · modal | Shows the selected objects and deletion plan, checks dependencies and requires explicit confirmation. |
| **Link SObjects** | Loads one schema-declared instance relation and transfers selected objects between available and linked panes. |
| **Database Editor dock** | Batch field editing lives in a dock rather than a registered native window. |

## Tasks and planning windows

| Window | Purpose |
| --- | --- |
| **Task Editor** · modal | Creates or edits the exact prepared task with project workflow fields; Save applies, Cancel keeps server data unchanged. |
| **Project Milestones** | Creates and edits project milestones used by planning views. |
| **Tasks workspace** | The full Cards/List/Table/Gantt/Calendar task surface is opened from the Tasks dock and kept warm while hidden. |

Task Inspector, Task Calendar, Timesheet and report surfaces are docks. They have their own help topics.

## Files, repositories and check-in

| Window | Purpose |
| --- | --- |
| **Naming Editor** | Builds and tests reusable naming rules against prepared objects and file values. |
| **Screenshot Maker** | Captures, crops or reviews a screenshot for the current prepared check-in. |
| **Matching Templates** | Configures reusable file-matching templates used by Drop Plate and preparation workflows. |
| **Repository Editor** | Creates and edits repository roots, platform paths and enabled state. |
| **Repository Sync** · modal | Discovers files for an explicitly prepared object/preset scope and adds transfers to the sync queue. Cancel abandons discovery, not existing files. |
| **Repository Sync Queue** | Shows application-owned transfers, progress, conflicts, cancellation and retry. Closing it does not stop the queue. |
| **Commit Queue** | Final review and execution of prepared check-ins. Closing it does not cancel queued work. |
| **Add files** | Reviews files added for ingest/check-in. It is context-sensitive and does not restore stale input after restart. |
| **Watch Folders** · modal | Lists configured local watchers and their status. |
| **Watch Folder** · modal | Creates or edits one exact watched directory and its project/matching rules. Cancel removes only the draft. |

## DCC and scripting windows

| Window | Purpose |
| --- | --- |
| **Script Editor** | Browses synchronized project scripts, edits source, runs locally or in the selected DCC, and shows real output and tracebacks. |
| **Script Shelf** | Creates shared or personal shelves, per-project or per-sidebar-tab scope, labels, hints, icons and ordered buttons. |
| **Script Triggers** | Assigns any ordered number of scripts to standalone or application-labeled DCC pre/post actions. |
| **DCC Action Options** | Shows the option fields declared by the selected DCC for the prepared native action. |
| **TACTIC Handler Server** | Local clients, capabilities, manual JSON commands, request results and transport diagnostics. |

The options window is generated from the selected DCC manifest. It does not change the process-wide
application environment. DCC actions always target the explicitly selected client ID.

## Communication and users

| Window | Purpose |
| --- | --- |
| **Messages** | Conversations, replies, forwarding, reactions and attachments. It remains prepared while hidden for fast reopening. |
| **Notifications** | Unread and recent application notifications with links back to their source. |
| **Activity Feed** | Auditable project activity with category, user, date and continuous-history filters. |
| **User Profile** | The selected user's profile, project task summary and permitted weekly work totals. |
| **Users** | Searchable user directory using the same profile surface in directory mode. |

Opening another user's profile never replaces the signed-in identity in the main top bar. Chat
messages remain in Messages; Activity Feed shows non-chat audit events.

## Administration

| Window | Purpose |
| --- | --- |
| **Administration** · modal | Project Search Types, schema, workflow, users, groups and permissions in one explicit admin draft. |
| **New Search Type** · modal | Creates or edits one schema Search Type with validation and an explicit save. |
| **Process dependencies** · modal | Edits workflow dependency rules for the prepared process graph. Closing requests resolution of changes. |

These windows expose only data and actions authorized by TACTIC. Server-defined project, Search Type,
process, status, group and role labels are displayed without reinterpretation.

## Maintenance and diagnostics

| Window | Purpose |
| --- | --- |
| **Help** | Searches and reads the installed English or Russian Markdown articles. |
| **Debug Log** | Full structured events, request IDs, details, commands and tracebacks with secrets redacted. |
| **UI responsiveness** | Measures UI stalls and request timing for diagnosis; it does not optimize the application by itself. |
| **Application Error** · modal | Shows the actionable exception, details and complete traceback; dismissal acknowledges this report only. |
| **Update** | Checks and applies an available Handler update through the supported update flow. |
| **Create Update** | Packages a controlled application update for authorized maintainers. |

Errors and Help are attached to the active modal owner when needed, so diagnostics remain usable
without appearing behind the window that triggered them.

## If a window appears lost or blocked

1. Check the taskbar and the monitor that last contained the window.
2. Finish the active modal editor or native DCC prompt before interacting with its owner.
3. Reopen the same command; nonmodal tools reuse and activate their existing window.
4. Use **Reset layout** to restore safe geometry when a monitor arrangement changed.
5. Open Debug Log if the content failed to initialize; a blank window is not a successful operation.

## Keyboard and pointer behavior

- Standard system keys move, maximize and close native windows.
- Escape closes transient popups; a modal editor decides whether Escape can cancel its draft.
- Right-click moves a shared context menu to the current pointer and current item.
- Long popup menus scroll inside a bounded surface with a visible shared scrollbar.
- A selector opened inside a popup replaces only the previous child selector, not its parent panel.
