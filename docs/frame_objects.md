# Tactic Frame B08: objects and inspector docks

B08 is **delivered** in Stream **0.112.161** and Handler **0.6.0.112**.
Object, operation and Inspector presenters use independent Frame copies. B07's
40 unfinished usable legacy widgets remain B07.

## Source and ownership map

| Portable source under `features/objects` | Presentation | Existing owner |
| --- | --- | --- |
| `description.ui.mjs` | Header, pin/edit/save state, footer and measured text port | DescriptionEditor controller / Vue per-object drafts |
| `fields.ui.mjs`, `fields.json` | Label/card geometry, icons, errors, readonly state and masonry | Native SObjectFieldModel / configured form adapters |
| `editor.ui.mjs` | Header, actual segmented creation mode, batch count/tokens/name example, per-object review and footer | SObjectEditorController / RecordForm and native EditCmd; browser simple-database batch uses existing insert_multiple |
| `duplicate.ui.mjs` | Five steps, relation modes, process content, totals, remember/cancel/retry/unknown result | SObjectDuplicateController / advanced-duplicate API and profiles |
| `delete.ui.mjs` | Concrete dependency groups and entries, selection, retry/busy/unknown result | Native deletion command / existing object-deletion API |
| `links.ui.mjs` | Two lists, search, Ctrl/Shift selection, staging, transfer and save | Native link controller / existing instance-link command |
| `report.ui.mjs` | Identity, metrics, task/status/process/person/note/child sections and navigation | Native report controller / read-only result-items object_report projection |
| `snapshot_tree.ui.mjs` | Collapsed process branches, snapshots and file ports | Native report/file controllers and browser FilePreview |
| `snapshot.ui.mjs` | Toolbar, options, summary, splitter and file columns | Existing Snapshot Browser selection, query, native file and derivative adapters |
| `watch.ui.mjs` | Relative path, repository selection, validation/save | Native watch owner; browser states the missing desktop capability |
| `inspector.ui.mjs` | Context header, quick task fields, related tasks and work-hour summary | Existing communication/task/work-hour controllers; Inspector stays in the workspace dock |
| `note.ui.mjs` | Bubble geometry, avatar, author/time/actions, measured text/link/file sections and edit/delete child content | Existing note drafts, timeline, rich text, attachments and mutation owners |

Products ship independent physical copies. There is no WebEngine, runtime link
between checkouts, second store or replacement write executor. Frame `Segmented`
and `StatusChip` use existing neutral house controls. `Button.iconAction` uses
the existing flat native tool action; ordinary Button paint is unchanged.

## Preserved behavior and explicit capabilities

- Drafts retain object/project/process/task context and original revisions.
  Following the same canonical task context does not clear the UI or requery.
  Full task editing opens the normal modeless object form. Existing browser
  inline task editing stays available separately in Task actions.
- Native filesystem, DCC, watch, open-folder/download and repository identities
  remain native. Browser files use authorized URLs, derivatives and download;
  it does not claim a local watch service or filesystem adapter.
- Native batch creation retains all configured field and preview owners.
  Browser batch creation currently accepts ordinary database actions; custom
  actions, uploads and instance creation use individual forms. The disabled
  Multiple option explains this limit. Supported tokens match native
  `{n}` / `{n:01}` through `{n:09}`, with at most 100 objects.
- Read failures retain drafts. Object forms, duplicate/delete/link wizards and
  note changes block resubmission after lost replies; they do not retry writes automatically. Known duplicate conflicts can reanalyze while
  retaining compatible field values and relationship/content choices.
- Report costs never enter presentation without wage/column access. Report
  tasks and notes open their actual context, publications their source project,
  and child records their configured search. Names/statuses/schema values are data.
- Report participants, hours, progress and file sizes use the column-filtered
  projection too; aggregates must not reveal values hidden in the source fields.
- Narrow report task rows stack metadata to avoid the archived clipping.
  Browser phone Back/Help, related-task drill-in, inline task editor, replies/history and preview
  remain explicit host capabilities, rather than disappearing during migration.

The two-list link scene also owns the body, native viewport and row insets,
empty state and loading bounds. Native SmoothListView retains its public names,
selection/drag/pagination; captures explicitly alias those measured viewport
names to the corresponding web value ports. Native row insets reserve scrollbar
space. Browser-only related-task drill-in keeps a minimum 24px action target.

The report header preserves the original centered preview, intrinsic type chip,
icon plus stacked label/value metadata and proportional metric columns. Hosts
measure their house font; the common module owns the geometry. Description
links and text selection remain value ports. At phone widths, all metrics stay
visible instead of reproducing the original clipped bottom rows.
Status chips retain their house font and accent instead of the Frame node's
generic text defaults; every report-header capture checks the type fits in full.

## Notes and write outcomes

Dependency rows keep the original 44/52px heights. The shared viewport and
row scene use native ListView and browser VirtualCollection; both retain scroll
on a selection refresh and virtualize long dependency lists. Read-only and empty
Inspector cards retain their original height. Loading uses the existing house
overlay; submitted deletion/duplication cannot be presented as an undoable request.
The temporary-server harness stops its own ASGI producer before restoring test
data, avoiding a race between fixture reset and the update collector.

The same `note.ui.mjs` orders status, text, sKey previews and attachments with
measured heights. Qt retains MessageBodyText, SKeyPreviewCard and AttachmentCard;
Vue uses escaped rich text and the existing preview/file controls. Both hosts
retain native emoji-only sizing. The shared file border paints inside its 64px
row. Browser attachment activation opens FilePreview with the original authorized
file and Download; Handler retains open/download/folder and Repository Sync.

Edit opens a modeless child; Delete opens a modal confirmation. Both share the
text/buttons/errors, retain drafts on failure and wait for the owner's result.
Lost replies prevent another write. Read and write generations are independent:
retargeting cannot discard an already submitted operation's outcome. Native note
children also capture the original search key, rejecting a row reused by another
context. Browser children hide with their dock without losing the draft and clear
on a project/session change. Browser
link previews use the existing protected endpoint, per-context generations and
revocable private-file URLs. Replies and edit history remain browser capabilities.

## Reproduction and evidence

Run from the Stream application folder with its installed development environment:

```powershell
.venv/Scripts/python.exe -X utf8 tools/sync_tactic_frame.py --handler-root D:/code/th_codex --copy-from stream
.venv/Scripts/python.exe -X utf8 tools/frame_objects/capture.py
node frontend/tests/frame_objects.mjs
.venv/Scripts/python.exe -X utf8 tools/frame_objects/report.py
.venv/Scripts/python.exe -X utf8 tools/frame_foundation/check_platform.py --handler-root D:/code/th_codex
```

`--smoke` captures 53 scenes in three themes at 320/880 px, dark EN (318 per host). The full run covers
three themes, light/dark, EN/RU and 320/880 px. The source-checked review page
uses original/current QML and Vue columns. `reference.json` identifies the
pre-B08 Handler checkpoint (already containing earlier Frame work). Git archive
reconstructs it into an ignored cache; there is no dependency on a developer's
untracked backup ZIP. Archived missing icons are recorded; current icons must resolve.

References use production QML and its actual models. Editor/inspector regions
are cropped from the corresponding archived screen; note header/body and child content are
verbatim extracted render fragments (fixture text initializes the original editor). Current field captures exercise the label,
card and validation surface, with value adapters checked through the control
catalog and actual forms. Fixtures and screenshots do not replace server tests.
The gallery is component evidence, not a connected Handler/server acceptance run.

Real temporary-server journeys cover description drafts, create/edit, batch
preview/create, advanced duplication and conflicts, two-list link/unlink,
report ACL/data/pages/context navigation, snapshot files, dependency deletion,
unknown writes and 320/360px touch forms. The dock driver covers exact task and
project, revisions, stale reads, float/stack/restore, themes and phone Back/Help.
Native suites exercise their original controllers and actual Qt input.

## Release acceptance

- **60 platform stages passed** on the final source fingerprints, including
  real input, IME events, resize, dock lifecycle, three DPI scales and packaging.
- **101 native object tests** passed. Another **12 offline window/archive tests**
  verify all registered windows reopen/shut down without QML warnings and that
  Handler's update archive contains the new object components and portable files.
- **2544 original/current native captures** and **1272 paired QML/Vue states**
  passed across three themes, light/dark, EN/RU and 320/880 px. Real description,
  toolbar and status input plus 100-row dependency virtualization/scroll checks
  run after the visual matrix. Matching the two current hosts is checked
  separately from the original-layout review.
- Real temporary-server object journeys and the full native-table/mobile journeys
  passed; original mutation owners, ACL/revisions, lost replies, private file
  previews, exact task context and retained drafts are covered.
- EN/RU Help includes usage examples and host-specific screenshots. The versioned
  reproduction tools and pinned original checkpoint regenerate the local gallery
  at `tools/frame_objects/output/index.html`; generated bulk output stays ignored.

Conversation lists/general messaging remain B11, complete Task Manager remains
B09, scheduling remains B10. Those are separate scopes, not unfinished B08 work.

The broader legacy Messages suite has two pre-existing failures outside this
block: `test_message_lists_use_a_bottom_anchor` and
`test_message_text_has_compact_header_gap_and_side_padding`. Both reproduce on
checkpoint `000c6a4a009f` with `QT_QUICK_CONTROLS_STYLE=Material` and
`QT_QPA_FONTDIR=C:/Windows/Fonts`; they are recorded for B11 rather than hidden
by weakening expectations. The focused B08 note/controller/input checks pass.

Physical touch/OS IME and compositor/GPU behavior need hardware acceptance.
This block's temporary-server journeys use SQLite, not production PostgreSQL.
