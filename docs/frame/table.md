# Tactic Frame table contract

Shared table descriptions do not certify complete legacy compatibility. A
registered adapter must still preserve applicable original options, editor/action
behavior, permissions and errors. Discover current support from the installed
server and catalogue; do not reuse historical class counts as a completion claim.

## Portable descriptions

| Module | Responsibility |
| --- | --- |
| `features/table/columns.mjs` | Width priority, hide order and auto-fit |
| `features/table/host.ui.mjs` | Row/header/selection/action geometry, paint and drag targets |
| `features/table/menus.ui.mjs` | Column and saved-view actions/availability |
| `features/table/cells.ui.mjs` | Typed labels, safe links, task cards, summaries and field scenes |
| `features/table/nested.ui.mjs` | Expanded-table presentation with host-owned requests/writes |
| `features/table/time.ui.mjs` | Schedule/daily-hours projections; existing owners retain writes |
| `features/table/inline.ui.mjs` | Typed editors, explicit-save and uncertain-write states |
| `features/table/widgets.json` | Registered server classes/aliases and adapter/editor categories |
| `features/table/dependencies.state.mjs` / `dependencies.ui.mjs` | Snapshot tree, expansion cache, cycles, paging and presentation |

TS ships `src/tactic_stream/shared_ui`; TH ships `thlib/ui/qml/tactic_frame`.
Each product builds independently. The server's admitted Python classes remain
explicit; catalogue data cannot authorize importing arbitrary plugin code.

## Owners

Qt ListView and browser virtualization retain delegates, scrolling and actual
input. Application search sessions/ConfiguredView retain queries/selection.
ColumnsEditorController and server widget-configuration operations retain
XML definitions, source revisions and saved views. Existing EditSObject,
TableCellEditCmd and task controllers retain writes, ACL, rollback and uncertain
outcomes. Do not add a second database/query engine or an embedded browser.
Configured JavaScript uses the existing SDK through its bounded bridge (browser
Worker or isolated QJSEngine process); do not execute it on the native UI thread.
A separate process alone is not an OS sandbox for untrusted code.

Native ValueEditor.qml and Vue TableInlineEditor render the same scene. Enter
commits a single-line value; multiline Enter inserts a newline. Dates, datetimes,
colors and multiple values require explicit Save. Escape cancels; outside clicks
preserve explicit-save drafts. Keywords/tags share suggestions, deduplicated tokens,
pending-input flush and explicit Save/Cancel. Store raw values, not display text.
Ordinary cells render plain text, including strings containing markup. Use the
shared pixel size, centered avatars and actual track/scrollbar geometry.

<a id="legacy-checklist"></a>
## Legacy scenario requirements

These stable IDs identify contracts, not a current development queue or proof of
completion. Preserve source XML, inherited options and concrete embedded scopes.
The local agent archive retains previous checklists and dated evidence.

<a id="l01"></a>
### L01: relationships and nested rows

Expand the configured child table, create/link a record, collapse/reopen and
retain state. Verify filters, direction, ACL, empty results, grouping and totals.
Each nested scope owns queries, selection and pagination; a generic Inspector
cannot substitute for that embedded table. Parent scope is mandatory even when
saved filters are applied. Preserve search_view/edit_view/insert_view and stored
ordering until the user changes it. Capture parent/project before creation;
ordinary edits must not receive creation-only parent context.

Group parents by canonical search key, not visible code. Keep broken references
visible. Parent changes use native relationships with captured source identity,
row/configuration/target revisions and reject retired, cyclic or foreign-project
targets. Preserve computed display text while editing the relationship. Save is
explicit; uncertain outcomes require readback rather than automatic replay.
Exclude credentials, tickets and private-message targets from parent projections.

<a id="l02"></a>
### L02: notes, messages and tasks

Open the configured thread, read/add notes/messages, edit its associated task
and refresh counts without losing table position. Verify parent, process,
privacy and nested forms. Reuse Messages, Inspector and task owners. For task
and note actions, distinguish the record itself from its real parent.

<a id="l03"></a>
### L03: configured actions and layouts

Execute the original XML action with row/selection context. Verify authorized
script/layout results, errors, cancellation and rollback. Provide explicit file
selection as an alternative to drop. Preserve unknown XML/options, comments and
revisions; never silently ignore unsupported parameters or callbacks. Old HTML
layout editor exclusion does not remove saved layouts or redefine DOM callbacks
as generic Inspector actions.

<a id="l04"></a>
### L04: file actions

Use existing file/Commit Queue owners for append, publish, checkout, load and
submission with the configured snapshot/version/context/naming. Verify actual
bytes, retries, ACL and FileUndo. RenderLink does not imply a render-farm service.
Local/DCC operations remain native capabilities; show explicit browser limits.
Full Check-in on task/note rows must resolve parent/self targets and normal,
numeric-suffixed or empty contexts consistently in server and native projections.

Dependency trees use captured concrete snapshot/file identities and revisions,
paged frame/sequence expansion, caching and cycle guards. Do not expand an entire
sequence just to obtain its first frame. Preview/download selects the requested
file. Close, refresh, project change and sign-out invalidate reads; late results
must not reopen a closed window or replace another document.

<a id="l05"></a>
### L05: statuses, processes and assignment

Verify process/status/assignee changes, parallel statuses, empty values, parent
scope, legal transitions, revisions, ACL and conflicts. Reuse Task Manager and
current picker behavior rather than implementing another task editor.

<a id="l06"></a>
### L06: schedules and time

Verify time scale, weeks, date boundaries, hours, cell edits, Save/Cancel and
summary recalculation. Reuse Gantt/Timesheet owners; a working standalone Gantt
does not certify legacy embedded-table options. Overtime must be counted once;
minute/hour conversion and shared date ranges stay explicit. The VFX bidding
bid_cost/color fields are optional template extensions, not original standard
task columns. Computed display overlays must not mutate stored values or drafts.
Use configured currency conventions; only a locale without monetary conventions
may use the documented fallback.

<a id="l07"></a>
### L07: service cells and complete table behavior

Exercise configured login/group/project/preferences/naming/notification actions,
including Security, template/update, recipients/triggers and summaries. Verify
ordinary users and admins, revisions and cancellation. A notification cell does
not certify email delivery. Include existing adapters, inherited options,
forms/inline editors, keywords/tags and bottom/group_bottom/total_summary.

An alias with `pass` may inherit a working implementation; inspect inheritance
before classifying it as unfinished. Deliberately empty infrastructure is distinct
from unimplemented functionality. Preserve explicitly agreed prod/Maya/applet
exclusions; do not silently expand those exclusions to other public contracts.

## Verification

Use Stream's `tools/frame_table` inventory/capture/report harness, corresponding
frontend scenarios and native TH table suites. Pass the actual Handler checkout
to tools whose defaults still point to an old path. Use temporary data and real
HTTP/XML-RPC where transport or native procedure execution matters.

A verified class needs original config/options, a reproducible XML/data example,
unchanged-script behavior, ACL/revision/failure/rollback checks and fresh paired
Qt/browser capture for corresponding capabilities. Update the existing EN/RU
Widget Database with the relevant example and limitations. Compare current source
fingerprints and actual input/geometry; historical totals and static registration
counts are not release evidence. Independent Windows packages, PostgreSQL and
real-device input need their own qualification.


## Configured VFX composition

CustomLayout compiles declarative rows, fields, read-only snapshot previews and referenced ViewPanel/TableLayout elements to Frame nodes. Each embedded table uses the existing nested-table owner; project-wide panels explicitly request project scope, while an explicit search key retains object scope. Configured SelectFilterElement fields retain their relationship targets and read guards. Unsupported widgets/options and executable Mako fail explicitly.

Configured JavaScript runs in the existing isolated table-action worker. Logical form values and root data are JSON state; no HTML or browser engine enters QML. Retained document tabs, picker changes and shared geometry are described in `features/table/layout.ui.mjs`. Review uses Stream's transactional ReviewSubmissionCmd with authoritative actor, captured version/context and duplicate protection. Printing uses CustomLayoutReportCmd for a complete scoped data snapshot; Qt prints a native QTextDocument and the browser invokes its own printer. These commands require the corresponding Stream server and do not restore old production Submission/Bin or applet execution.

Regression entry points: Stream `test_vfx_composition` and `test_vfx_browser.VfxBrowser`, frontend `vfx_composition.mjs`, and Handler `tests.test_custom_layout` plus sidebar target, table-script and nested-table suites. Existing project configurations require explicit reviewed repair; installing a prepared template never rewrites another project.
