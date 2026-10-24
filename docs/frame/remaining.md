# Tactic Frame: Additional application surfaces

This contract describes source ownership, behavior and verification scope.
TH and TS ship independently; native-only actions remain native capabilities.
Use [the shared contract](contract.md) and [the feature index](index.md).

## Shared composition and retained owners

| Surface | Portable description | Existing owner retained |
| --- | --- | --- |
| Knowledge workspace | `features/knowledge/workspace.ui.mjs` | Project, selection, lazy article host, navigation persistence and requests |
| Navigation and outline | `features/knowledge/navigation.ui.mjs` | Native role models/drag-and-drop and browser catalog; article lookup and heading scrolling |
| Reader/editor commands | `features/knowledge/commands.ui.mjs` | Markdown, drafts, revisions, publication, permissions, history, attachment and image operations |
| Formatting toolbar | `features/knowledge/format.ui.mjs` | Qt rich document and browser selection/range editing, native anchored menus and DOM menus |
| Collaboration first use | `features/support/collaboration/initialization.ui.mjs` | Explicit authorized schema initialization and host-owned confirmation; no creation during reads |
| Timesheet and hour editor | `features/workhours/sheet.ui.mjs` | Existing time-entry controllers/commands, selection, daily limits, approval, user scope and writes |
| Work and Cost Reports | `features/workhours/reports.ui.mjs` | Native permission-filtered report models and server-authorized browser report catalog |
| API console | `features/support/documentation/api.ui.mjs` | Stream method catalog, credentials, request validation and explicit execution |
| Transaction details | `features/support/documentation/journal.ui.mjs` | Stream server-filtered journal XML and request identity |

Corresponding renderers use their own house controls. Native Knowledge and Work
Hours adapters live in `thlib/ui/qml/features/knowledge`, `features/workhours`
and `features/collaboration`; public names remain thin facades. Vue adapters stay
under their feature directories. Both products ship independent copies of the
portable modules. No WebEngine or runtime link to another checkout is introduced.

Typed rich text, image selection/resizing and attachment presenters remain engine
adapters, not a second implementation of persistence or permissions. Browser API
and transaction details are intentional capabilities; no extra native window is
invented. Batch Manager keeps its native launcher, scheduler and existing web UI.
User/plugin/DCC-generated UI remains with its script/connector execution owner.

## Input and lifecycle corrections

- Pointer and keyboard Action controls send `pressAction` before activation.
  Anchored menus preserve their previous open state and text selection before
  focus moves; press is not a second mutation command.
- Shared editor/viewer bars wrap at narrow widths. Fields keep semantic names,
  complete primary actions, visible scrolling and stable control identities.
- Hour duration accepts 0.01–24 with two decimal places and dot/comma input.
  Existing server validation additionally enforces daily totals. Description
  remains multiline; full approval text remains visible on narrow forms.
- Report lists retain virtualization at 1,500 rows. Narrow report choices omit
  types unavailable to the existing permission owner.
- Messages and Knowledge first use now share explicit schema confirmation in
  both engines. It names both message metadata tables and project article
  columns, preserves existing data, and closes on project changes. Browser
  Messages initialization now calls the existing Knowledge schema procedure, as
  Handler already does; ordinary reads still create nothing. Isolated HTTP
  tests cover both schemas, repeated initialization, read-only calls and ACL.
- Browser Knowledge initialization, organization, deletion, attachments and
  clipboard callbacks use the existing request generation. A previous project
  cannot publish into a new one or reset its busy state/permissions. Already
  submitted writes can finish for their original project; the UI does not claim
  cancellation or retry them automatically.
- Closing the API console aborts catalogue loading and clears temporary
  credentials. Late execution/sign-in/copy completions cannot update a removed
  view. A late journal-copy completion cannot update another transaction.

## Verification

Run the focused drivers under `tools/frame_remaining/` from the Stream development
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
