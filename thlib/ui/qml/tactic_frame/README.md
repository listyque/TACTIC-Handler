# Tactic Frame source map

This directory contains portable UI descriptions and presentation state.
Handler ships an independent copy in `thlib/ui/qml/tactic_frame`.
Neither product imports the other checkout at runtime.

## Read from the bottom up

| Folder | Responsibility | May depend on |
| --- | --- | --- |
| `core` | Node contract, theme roles, metrics, typography, motion | Plain JavaScript only |
| `controls` | Reusable controls, graph geometry and input, code toolbar | Core; no feature modules |
| `shell` | Window/dock/workspace composition | Core and controls |
| `features/configuration` | Configuration shell, explained settings, native/web repository and server fields | Core and controls |
| `features/projects` | Project catalogue, four-step creation, modal editor and templates | Core, controls and configuration settings/shell |
| `features/search` | Query cards, presets, tag/quick headers and editors, process visibility, menus, paging and card geometry | Core and controls; query and mutation owners stay outside descriptions |
| `features/table` | Table geometry/paint, column and view menus, typed cells, inline editor and widget catalogue | Core and controls; queries, XML revisions and writes stay with existing owners |
| `features/administration` | Administration shell, forms and document guards | Core and controls |
| `features/support/help` | Help composition, filtering, navigation and document positions | Core and controls |
| `features/support/diagnostics` | Debug sessions, event details, measurements and selection | Core and controls |
| `features/support/identity` | Profile composition, account editor and local draft decisions | Core and controls |
| `features/support/connection` | Sign-in, native presets and release composition | Core and controls |
| `features/support/feedback` | Error inspection and contextual actions | Core and controls |
| `features/administration/<section>` | A section's UI and state | Shared admin helpers and its own domain |

Administration uses `controls/forms/sections.ui.mjs` for settings rows, headings,
captions, switches and width steppers. Do not reintroduce a second form geometry
helper inside a feature. Plain CheckBox text and custom membership/cell contents
are both supported by the native renderers. Column moves keep the selected name
while recalculating its XML path; document controllers retain the XML and write
revision owners.

`shell` currently owns window geometry, main-toolbar positions and dock-header
composition, shared docking zones and previews. The neutral navigation row is
under `controls/lists`; document metrics are under `core/foundation`. Hosts retain
native input, application commands, lifecycle and persistence. Dock projection,
keyboard decisions and footer corners live in `shell/dock.*`. Main menus use the
shipped `shell/main.menus.json` catalog, `shell/main.menus.mjs` predicates and
`controls/menus/action.ui.mjs` rows. The JSON catalog is data, not a second UI
language or a runtime link between repositories. Native `MenuRegistry` loads
its own catalog and keeps procedural replacement/extension; popup ownership,
command dispatch and server state remain with existing hosts. The complete drawer container uses `shell/navigation.ui.mjs`: header/list geometry,
keyboard decisions (including off-screen rows) and armed hover dismissal. Hosts
keep scroll and real input. `shell/projects.ui.mjs` now supplies project popup,
header, category grid and expanded-card composition; the project catalog remains
its existing owner. `controls/tabs/workspace.ui.mjs` supplies search-tab paint,
rail metrics and keyboard decisions. Tab nodes opt into property-specific motion
using existing theme timing tokens; hosts retain animation preferences, focus,
real input and persisted state. `controls/tabs/section.ui.mjs` now supplies the
section rail panel, surfaces, badges, labels, close bounds, action records and
vertical drag target decisions. Hosts keep real pointer grabs, focus, scrolling,
popup lifetime and command dispatch; no second section/session model is created.
`shell/workspace.ui.mjs` supplies the whole root composition: toolbar, section
rail and dock host, including the browser phone grid. Main.qml and App.vue use
these bounds directly; native desktop keeps its expanded rail input area.
ItemPreview owns fallback contrast against its actual darkened accent in all
browser call sites, including the account avatar. Colors remain a projection of
the existing appearance owner. Session, saved layouts and phone panel selection
retain their original owners; late authentication/logout results cannot publish
into a newer browser session. Queued background reads check cancellation before
starting. B01 acceptance lives in `tools/frame_workspace` (whole-root comparison),
`tools/frame_navigation/check_workflows.py` (session races) and
`tests/test_workbench.py` (real desktop/phone persistence and mutations), all tied
to the required platform gate. Screen contents and full control-family parity
remain the following batches.

Lists default to a four-pixel row gap; `rowGap` preserves a different existing
spacing, such as Help's three pixels. `listRowHeight` is shared by both adapters,
and validation rejects a negative gap or one that consumes the entire row.
`revealListOffset` keeps keyboard selection visible before a virtualized row gains
focus. `SummaryChip` maps directly to each product's existing house control.
Short confirmations live in `controls/feedback`; authentication, ACL, mutations,
retry workers and installers never move into a portable description. B04's owner
map, capability differences and verification commands are in `docs/frame_support.md`.

## One screen

- `<screen>.ui.mjs`: visible tree and geometry. Read `describe` for the page,
  `toolbar` for its actions, `row` for repeated content, `models` for lists.
- `<screen>.state.mjs`: initial presentation state and event transitions.
  Returns the next state and explicit commands; never performs requests.
- `<screen>.fields.mjs`: existing field definitions for large forms, when needed.
- Native QML/Vue adapters: call the existing controllers/API and report results.

These are JavaScript modules, not a new markup language. A `node` declares a
named control, bounds, properties and an event. The renderer supplies the
product's native house control. Do not implement another form inside a generic
Frame slot or put server operations in the renderer.

For example, a screen declares a named action and its bounds; it does not
reach into either engine's button internals:

```js
export function describe(model, width, language) {
    const saveBounds = rect(width - 160, 0, 160, 38);
    const saveAction = { type: 'save' };
    const saveButton = button(
        'saveDocument',
        saveBounds,
        translate('Save', language),
        'save',
        saveAction,
        model.canSave
    );
    return { nodes: [saveButton] };
}
```

The screen's state module handles `save`; its engine adapter calls the existing
controller. Trace an action through those three places rather than searching
for a separate QML or Vue layout of the same screen.

## Source readability

Keep imports, constants, named section builders and exported functions separate.
Write one action or declaration per statement. Expand nested objects, state
branches and UI children; avoid comma-separated statements and long chains of
conditional expressions. Prefer `panelWidth`, `contentHeight`, `editable` and
`selectedProcess` to single-letter locals in substantial functions.

Use the pinned Prettier formatter for portable modules, Vue renderers and styles,
and Administration adapters:

```
python tools/format_tactic_frame.py
python tools/format_tactic_frame.py --check
```

The optional `--handler-root D:/code/th_codex` formats native QML with Qt's own
formatter as well. Prettier 3.6.2 is a development tool and is not added to the
application runtime. Do not minify source files. Build-output settings remain
owned by each product's existing bundler configuration.

## Sync and verification

The preparation contract is executable in `core/frame.mjs`. `node` checks
control kinds, stable nonempty IDs, finite logical-pixel bounds and named font
roles. Resolved `kind`, ID, geometry and `fontSize` cannot be overridden through
the properties object. `validateScene` checks sibling identity, action types,
required list/grid sources, cell geometry, child containers and named Views at
the renderer boundary. An intentionally absent View requires `optional: true`.
Qt sequence wrappers are accepted without copying them into JavaScript arrays.

Frame typography uses the named logical-pixel `foundation.textStyles` roles.
Descriptions set `fontRole`; renderers consume the resolved `fontSize`. Existing
Frame sizes are preserved: menuHeading 10, caption 11, secondary 12, body 13, bodyLarge 14,
section 15, title 16, heading 17, display 18 and hero 24. Qt supplies one complete
QFont so a base control's point-size binding cannot compete with a pixel size.
The older `foundation.typography` point API remains for unported house-control
consumers; do not mix its units into a Frame description. Original-wide visual
normalization is a separate migration acceptance step, not an implicit redesign.

### Collection and input ownership

- Inline-edit list records have unique string or finite numeric keys. Keys are normalized
  to strings for cross-host identity; `1` and `'1'` collide. Display labels,
  array indexes and empty server IDs do not substitute for presentation keys.
  For example, the unsaved Workflow row has `key: 'draft:<type>'` while its
  server identity remains empty.
- Action-only positional XML/tree lists retain their feature-owned reorder and
  focus rules. An XML path or navigation index identifies a document position;
  it is not an immutable entity identity that the renderer can infer.
- Array sources are immutable snapshots. `recordIndex` validates identity once
  per source replacement; `virtualRange` limits materialized rows to the viewport
  plus overscan. Empty/shrinking sources clamp the range and scroll offset.
- Native role-model lists use `fields` to consume the existing controller model
  directly. The model owns its signals, selection and resets. Use this path for
  large production data; do not copy all model records into scene nodes.
- The array adapter preserves a visible editor by key and reanchors the viewport
  when that editor moves. Caret, selection and preedit remain in the same control.
  Scrolling a row out or removing it can destroy its delegate, so persistent
  drafts and selections belong to the feature state/controller, never the row.
- Scrolling refreshes the visible rows without reindexing the array. Browser resize deliveries
  merge per target until the next frame; unobserve/disconnect discard pending
  targets. Hidden/disposed features must release their observers and callbacks.
- Both engines keep IME preedit local until commit. Enter while composing does
  not trigger a Frame command. Browser text fields use Vue's native text directive
  while retaining their existing string-valued events. Control lookup escapes
  names instead of assuming that IDs are valid CSS identifiers.

### Product boundaries

Pure descriptions/state never perform requests or retain Qt objects, DOM nodes,
timers or observers. Adapters own these resources and publish plain presentation
data. Server authorization and uncertain-write handling remain with their current
owners. Client capabilities and viewport/input mode are separate from ACL.

Only genuinely shared modules belong in this mirrored directory. Product-only
Frame descriptions stay under that product's feature directory and import its
local core. Native QML/Python user scripts keep their existing execution path;
Frame does not translate arbitrary script-created QML into Vue.

Contract checks are `frontend/tests/frame_contract.mjs`,
`frame_renderer_contract.mjs <handler-checkout>` and `frame_resize.mjs`.
`tests.test_frame_platform` in Handler and `frame_platform.mjs` in Stream exercise
real controls, 10,000 records, stable editors, composition and multiple scales.
`tools/frame_foundation/inventory.py --handler-root <path>` generates a source
inventory with hashes and entry owners. Static inventory and matching kind
registrations do not prove runtime readiness; source-driven/script/plugin UI
requires its actual runtime inputs. Existing Administration tests and paired
captures remain part of the regression gate.

Run the focused gate with:

```
python tools/frame_foundation/check_platform.py --handler-root <handler-checkout>
```

It checks formatting, copy/guide consistency, contract/renderer registrations,
resize disposal, inventory discovery, actual native input at three scales,
browser composition/scroll races, the ordinary window smoke and independent
wheel packaging. Logs and source fingerprints are written to
`tools/frame_foundation/output/platform/gate.json`; changed sources invalidate
the result. The gate isolates settings and terminates its own child process tree
on timeout. Full Administration and original-reference release checks are separate.

`tools/sync_tactic_frame.py --handler-root <path> --check` recursively checks
module paths, contents and the manifest. `--copy-from stream` is an explicit
maintenance operation, never a product build step.

QML renderers are registered by `tactic_frame/qmldir` and organized into `core`
and `controls/<kind>`. A QML type index preserves names without keeping duplicate
implementation files. Vue renderers live in `frontend/src/frame` with matching
control subfolders.

Native Administration adapters live under `features/administration/<section>`;
the root `qmldir` preserves their public type names. Source placement must follow
UI ownership rather than extensions or the date a component was added.
Native window hosts live in `shell/windows`, dock hosts in `shell/docks`.
`Main.qml` remains the application entry point. Window content paths remain
relative to the QML root; absolute URLs keep their original meaning.

The Workflow catalog is composed once in `workflow/catalog.ui.mjs`. The
Administration sidebar supplies a host on desktop; the editor retains catalog
state and commands. On narrow screens the same catalog is hosted inside the
editor. Hosts never make a second request or maintain a second catalog copy.

Compare original Handler → Frame Handler, then Frame Handler → Frame Stream.
Matching two new implementations alone does not prove original UI fidelity.


## Control contract (phase 1)

B02 extends the original sixteen-card, 372-state subset with 144 standalone
examples from `controls/catalog/variants.mjs`. The expanded kit covers each
reviewed family at its neutral contract boundary; domain screens remain separate.
Stream's `docs/frame_control_catalog.md` describes the working offline/native
catalogs, exact owners, reproduction commands and rendering/platform limits.
The original gallery retains detailed opened/hover/press/focus evidence.
The development atlas is generated by Stream's
`tools/frame_controls/elements.py`; its reviewed family registry, complete source
index and explicit gaps are separate from runtime acceptance.

The base kit includes primitives (Button, Icon, TextField) and neutral composite
controls (ComboBox, DateField/calendar, UserPicker, Menu, TabRail, SettingRow).
Both accept neutral data and emit events without business operations. Form size,
nesting and folder location do not determine its level. Infrastructure owns
input/rendering/host lifecycle. A business form or fragment owns its scenario,
domain data, validation and commands: TaskInspector, Task Calendar, ProjectCard
and ProcessSelectionTree are not base controls. A picker does not change group
membership; its owner does. A reusable header supplies action slots; a task
view-mode switcher calling tasksController remains a business fragment.

`core/interaction.mjs` resolves semantic button, field, checkbox and switch
paint. Controls apply those roles for idle, hover, press, keyboard focus and
disabled states; hosts retain native input and transient focus. Explicit error
and read-only states belong to the field. Never set an inline text color over a
button's semantic paint, or mix inherited point sizes with pixel subproperties:
replace the complete native font value.

`controls/forms/calendar.mjs` is the shared local-date parser and Monday-first
42-slot calendar. It rejects rollover dates and trailing text; years below 100
retain their actual year. A picker commits only on acceptance, never on calendar
browsing. `DateChoice` emits edit and commit actions separately. `UserChoice`
receives existing user records and emits the selected login without requests.

`controls/lists/tree.ui.mjs` owns a flat preorder tree's visible rows, selection,
expansion and arrow/Home/End navigation. Sidebar Editor uses the same row and
navigation as the executable catalog. Feature owners still guard unsaved edits
and load data. Lists and Grid retain viewport-based delegates; this is a base
control contract, not the later Search/Table feature migration.

`controls/catalog.ui.mjs` is executable documentation. Its independent Qt and
Vue harnesses render real production controls, not matching mock painters.
Run `tools/frame_controls/capture_qml.py`, then
`frontend/tests/frame_controls.mjs`, then `tools/frame_controls/report.py` to
build the local paired gallery. Native tests and browser input run in the
platform gate at scales 1/1.5/2. Paired captures cover three styles, two palettes,
EN/RU, wide/phone, long text and explicit states. Source fingerprints invalidate
old evidence. Native popup windows may extend outside their owner; a browser
popover stays within its viewport. Physical OS IME and GPU/compositor behavior
require hardware acceptance in addition to the automated offscreen/DOM tests.

`core/icons.mjs` is the common semantic alias and fallback policy. Each host
supplies its bundled font maps; semantic names never select a different glyph
because one renderer has a reduced lookup map. Explicit `set:name` selections
retain their exact catalog glyph. `frontend/tests/icons.mjs <Handler checkout>`
checks the four font files and all five catalogs; the native/browser icon driver
compares actual selected families and Unicode values. The controls gallery also
checks text origins/baselines/advances and visible icon geometry, with a 0.6 px
position tolerance. This does not claim identical rasterizer antialiasing.

`shell/dock.layout.mjs` projects the structural dock tree, computes recursive
minimum sizes, clamps shared dividers, resizes floating edges and orders visible
tabs without moving hidden slots. Projection is immutable: shrinking the host
must not overwrite preferred split ratios. Minimums come from the existing
`shell/window.sizing.mjs`, including the largest visible member of each stack.

The native Python dock model retains its dataclasses, settings and signals.
Its narrow `workspace_models/docks_projection.py` boundary converts geometry
calls to the portable module using one application-owned Qt JavaScript evaluator.
It requires the owning Qt application thread, owns no layout or UI objects, and
loads no browser or external checkout. Vue calls the same portable functions
directly. The whole-layout reference and real input drivers live in
`tools/frame_docks` and `frontend/tests/frame_dock*.mjs`.
