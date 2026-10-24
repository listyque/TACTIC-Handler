# Tactic Frame: Objects and inspector docks

This contract describes source ownership, behavior and verification scope.
TH and TS ship independently; native-only actions remain native capabilities.
Use [the shared contract](contract.md) and [the feature index](index.md).

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

## Verification

Run the focused drivers under `tools/frame_objects/` from the Stream development
checkout, with the actual Handler checkout supplied using `--handler-root`
where supported. The complete shared gate is:

```powershell
python tools/frame_foundation/check_platform.py --handler-root "../../TH"
```

Adjust that path relative to the working directory; in the two-repository
workspace, Stream commands run from `TS/tactic_stream` and Handler is `../../TH`.
Use isolated data, actual input, fresh source fingerprints and independent-package
checks. Generated reports belong in the ignored tool `output/` directories.
Historical release counts and captures are local archive material, not current
acceptance. Offscreen checks do not establish physical touch/IME, compositor,
DCC or deployment readiness; exercise those when the feature requires them.
