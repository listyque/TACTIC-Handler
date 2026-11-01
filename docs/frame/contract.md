# Shared QML / Vue contract

**Tactic Frame** describes UI with ordinary JavaScript objects in standard `.mjs`
modules. Keep UI descriptions and state separate; do not introduce a new language,
parser or file extension. This contract applies to shared screens and prototypes.
It supplements each product's AGENTS and component policies. Do not rewrite an
unrelated working screen merely to adopt the contract.

Idle task values share `features/tasks/cells.ui.mjs` geometry (`choiceLayout`) and
paint roles (`choiceStyle`). `choice` builds the same browser scene from them.
Native value-only updates may reuse geometry and fonts, but must update text,
colors and enabled states immediately. Native avatar image groups may be lazy
for missing/pending sources; loaded image geometry and input remain unchanged.

## Product boundaries

TH and TS are independent products, repositories and bundles. TH ships Python,
QML and its own `.mjs` copy; TS ships its server and built Vue resources. Normal
startup/build/update must not require the other checkout, shared runtime folders
or symlinks. No separate shared package is required at this stage.

The skeleton is logically shared; apply changes to both physical copies. Each
client retains its controls, domain controllers, transport, authentication and
file capabilities. An identical UI description does not make a TH API object
interchangeable with a Stream HTTP payload or server-side SObject.

Frame copies live in TS `src/tactic_stream/shared_ui` and TH
`thlib/ui/qml/tactic_frame`. From the Stream product directory, verify with
`tools/sync_tactic_frame.py --handler-root <handler-checkout> --check` (the default
mode). Copy only explicitly with `--copy-from stream` or `--copy-from handler`;
this tool is not part of ordinary product builds.

## Single owners

Only the hovered workflow cell opens a preview; checked peer rows stay compact.
Bulk status/assignee edits retain their existing selected-row scope.
Task workflow hover previews use normal theme-height fields, wider cards and
dates, independently of the compact row height. Hover only over inline cards
starts expansion; the count action opens Task Manager directly. The preview
retains that action outside its scrolling card content. Expanded geometry and
date-range labels are owned by `features/table/cells.ui.mjs` in both engines.

Content spacing uses the shared foundation's semantic scale in logical pixels:
12 for a body/panel interior, 8 between related controls and 16 between sections.
Tables and dock/page bodies add no outer side gutter. A dialog body has one
inset after its header; account for browser borders once. Preserve authored XML
geometry and scrollbar/hit-area reserves. See [Content spacing](spacing.md).

Workspace tab backgrounds have square corners. Keep the selection underline and
close-button feedback rounded; tab styling must not change general panel radii.

Native tabs, segmented choices and search tables keep `activeFocusOnTab` enabled
while they hold active focus, even as selection or visibility changes. Once focus
moves, an inactive entry leaves Tab order. Qt rejects disabling that flag on the
active focus item; browser `tabindex` has no such restriction. Test native Qt
messages as well as QML engine warnings when checking these transitions.

Tag editors measure labels in the rendered font and include the existing button
icon, spacing and padding. Pack whole chips onto the next row; only labels wider
than the popup's available label area may elide.

Table active rows and keyboard focus use the content-selection background across the whole row, without a separate row outline. Checked selection remains independent.

Floating dock windows are the visual reference for floating windows: reuse their chrome, title bar, borders and controls. Keep resize grips quiet and integrated into the corner, without a filled circular button.

Window/dialog outer corners use an 8-DIP radius across themes. Browser legacy
headers are normalized by the window host; Frame page headers remain content
toolbars beneath a common outer title bar. The host forwards Close to the
feature's existing close action (including its disabled state), or dispatches
its cancellable cancel event. Compact confirmations retain their existing
buttons and modality. Native functional windows and sign-in use the same
operating-system frame as detached docks; embedded dialogs use Controls.Dialog.
Menus, navigation drawers, toast notifications and OS file pickers keep their
separate roles. Window hosts never rewrite a draft or authorize a save.

Embedded table headers, data-row backgrounds, inline notices/errors and pending-change bars use square corners. Keep the
existing theme radii and sizing on controls, dialogs and item cards; a local
table styling correction must not change those shared defaults.

Dashboard tables include their title in the declared height. Embedded Auto Fit
fits all configured columns before considering overflow; explicit hidden columns
stay hidden. Page containers add no implicit horizontal gutter. Status colors
use passive house badges, leaving row selection and inline editors with their
existing owners.

`Chart` uses shared geometry/paint for bar, line and donut displays, with native
Canvas in both renderers and ordinary Frame labels/legends. Missing line values
break the path; signed values are supported except for donuts. Full values are
available through hover tooltips and accessible labels. Redraw follows data,
size, palette or hover changes; there is no idle animation. Optional Box shadows
are cached independently from card contents, including the software Qt backend.

### Controls, infrastructure and forms

Classify by responsibility, not location, filename, size or nested element count.
Search, Identity, Progress, Empty and FileField nodes adapt the existing house
search/identity/progress/empty/file controls. Search emits action (text),
acceptAction (prepared suggestion record) and commitAction; its host owns results.
Progress receives value/min/max or indeterminate, without starting an operation.
FileField emits browser Files or native file URLs; the host owns files, validation
and uploads. Native FileInput itself uses Frame, so its adapter must resolve that
type lazily by URL rather than introduce a static recursive type dependency.

The base library contains primitives and neutral composite controls. Several
buttons/fields do not automatically make a component a domain form.

| Layer | Responsibility | Examples |
| --- | --- | --- |
| Primitive | One value, action or signal with neutral properties/events | Button, CheckBox, TextField, Icon |
| Base composite control | Reusable interaction; accepts prepared data, emits events | ComboBox, clearable SearchField, DateField/calendar, UserPicker, TabRail, Menu, SettingRow |
| Infrastructure | Input, rendering, placement and lifecycle | ActivationHandler, FrameView, popup coordinator, window/dock host |
| Form / domain fragment | A particular workflow, data, validation and operations | Groups editor, TaskInspector, Task Calendar, ProjectCard, ProcessSelectionTree |

Can the component serve another workflow using neutral data/handlers, without a
project, Search Type, task code, ACL or domain controller? If not, it is a form or
domain fragment. No direct HTTP call does not imply a neutral control: domain
knowledge also belongs to the workflow. A Send label and sending state are neutral;
a message ID and message-send operation are domain knowledge.

Controls own local input, focus, expansion and error display. Forms own domain
validation, drafts, loading, saving, confirmations and results. A picker receives
users but does not change membership; a calendar chooses a date but does not
load task schedules. A shared header provides action slots; a task mode switcher
that invokes task commands remains a domain fragment. Location cannot change
these rules: ProjectCard, ProjectFilterToggles and ProcessSelectionTree remain
domain components even under controls/. SettingRow is base composition;
ConfigurationPage is a form. Do not create a base type per form or move domain
commands into a control just to reuse its appearance.

| Concern | Owner | Forbidden in adapters |
| --- | --- | --- |
| Structure, IDs, dimensions, spacing, responsiveness | Shared description and layout calculation | Independent page layouts or local coordinate corrections |
| Screen state, transitions, gesture rules | One engine-independent module | Duplicated validation, date arithmetic, drag, zoom or undo |
| Native paint/input | Named engine primitives | API calls, project knowledge or business rules |
| Colors, typography, icons, motion | Existing theme owners | Per-page palettes or custom SVGs for standard actions |
| Client feature availability | Explicit capability contract | Silent hiding, altered command meaning or placeholder success |
| TACTIC, ACL, persistence, errors | Existing domain controllers and server commands | A second save path in controls or client substitutes for server ACL |

Primitive names express their meaning: Button, CheckBox, TextField, Label. QML
uses Handler controls; Vue uses matching App* controls. Wrapping two independently
implemented screens in matching containers is not a shared skeleton.

`Area.flat` is a transparent multiline editor inside a composite surface, such
as the agent chat composer. Both native renderers retain the house text input,
selection, caret, placeholder and scrolling while omitting its separate frame.

## Required change procedure

1. Inspect the existing Handler screen, nested controls and handlers. Identify
   operations, states, host type and client capabilities.
2. Change shared structure/rules. Define a new primitive's name, dimensions,
   typography, states and event contract once if one is actually needed.
3. Implement it in both engines through existing house controls. The adapter
   normalizes input; the shared module decides the state transition.
4. Exercise identical scenarios through actual Qt/browser input, with identical
   data, theme, language, scale and window size. Check relevant default,
   disabled, focus/hover/pressed, error/empty, reopen, Escape, cancel and save states.
5. Compare real control geometry, colors and typography, not only models. Capture
   both implementations, document limits and fix differences in the same task.
6. Update the affected contract and product help. A menu or backend entry point
   does not certify the complete workflow; identify unsupported parts explicitly.

Unsupported nodes/commands fail explicitly. No silent fallback, server-UI `eval`
or page-specific CSS repairing only one engine. Check consumers after shared
style changes. WebEngine/WebView/HTML inside QML requires an explicit user
instruction; visual convenience is not authorization. Python/QML Script Editor
and standalone Batch Manager retain their native execution systems.

Shared geometry depends on the primitive contract. It does not guarantee identical
font rasterization, system menus or OS capabilities. Do not promise pixel parity
without measurements and screenshots. Headless browser captures must not hide
scrollbars. Preserve native disabled behavior and actual input/focus semantics.

## Screen and editor contracts

Groups uses shared `groups.ui.mjs` / `groups.state.mjs` for catalogue, tabs, form,
membership, warnings and permitted actions. Users uses `users.ui.mjs` /
`users.state.mjs` for search, archived accounts, Profile/Account/Groups, fields,
password and membership. Existing client controllers keep persistence ownership.
Confirm save/reset; an unknown write result blocks retry until successful readback.
Never return passwords in catalogues. A legacy server field such as license type
may be shown only where that server actually provides it; this does not restore
excluded Stream licensing.

Access rules uses `security.ui.mjs` / `security.state.mjs` for scopes, matrix,
lists/editor, group settings, XML/JSON/inherited values and local buffer state.
`admin.document.mjs` shares draft actions and confirmations; domain controllers
retain validation and permission resolution. Choice and virtualized Grid retain
fixed headers and separate scrollbars. Load FrameGrid.qml by URL after the current
scene exists to avoid recursive FrameView compilation. Read Qt list models by
named roles and JavaScript arrays through modelData.

Raw database, Sidebar and Columns use their shared ui/state modules, including
the nested Cell editor. `controls/forms/sections.ui.mjs` defines form rows.
Unapplied Sidebar/Columns fields participate in dirty/close guards; invalid text
survives navigation. Unknown writes require readback. Native Grid publishes a
stable row-vector snapshot before model reset; its URL loader owns bindings
separately from delegates.

Column header display editing uses the shared Columns definition-source selector: current-view display declaration, then inherited `definition`, with an explicit missing-source state. Form input editing continues to target `edit_definition`. Source projection accepts the selected saved view name without constructing its widget; raw identifiers and XML search remain available for unsupported classes.

Administration has ten sections: Groups, Users, Access rules, Search Types,
Project schema, Workflow, Columns Editor, Raw database, Layout Editor and Sidebar.
Naming, process dependencies, type deletion/creation and the window shell also
use Frame. `administration.ui/state.mjs` describes the common shell. View may host
a migrated child Frame screen or an empty host port, not an independently laid
out old screen presented as a shared implementation. Ports retain editor instances;
shared modules place them. Toolbars observe their port size, not the whole dialog.
Search Types/Schema → Workflow and Sidebar → Groups use the main sections,
preserve drafts and do not reload the pipeline just because navigation returns.

Code uses native SourceEditor/CodeEditor with shared `code.ui.mjs` actions for
undo/redo, clipboard, find/replace, help, font size and history. TH uses a private
QObject with its own Qt Slot declarations and highlighter, not a borrowed Script
Editor session/settings. Update QTextDocument input imperatively and synchronize
Python responses after the current event so stale intermediate text cannot reset
the cursor. List delegates retain stable keys; selection must not destroy a drag
source by replacing the entire JavaScript model.

Layout uses standard minidom/DOMParser. Shared layout.document/state/ui/preview
owns structural edits, templates, movement, layers, conditions, bindings and
preview. Preserve unknown attributes/nodes/comments; forbid DTD/external entities.
Save requires server validation of the exact current XML and confirmation.
Keep server ACL, revisions and native commands; never retry an unknown write
without reading its outcome. Project reset reads the Layout catalogue from memory;
uncached projects discover through the existing read-only worker procedure with
captured server/ticket. Late replies cannot change another project's editor.

## Explicit capability differences

- TH Layout Editor is native; Open view runs configured SObject layouts in the
  system browser with its own authorized session, never a ticket in the URL.
  TS opens the layout in its working window. Layout validation/writes use the
  installed Stream layout-authoring API, not imports from a neighboring checkout.
- Naming keeps Handler's native local simulation and browser-side server checks
  explicit. Preview does not run arbitrary scripts.
- TH opens related objects through its existing object opener. The additional
  browser read-only details window uses Frame; it does not imply desktop file
  operations are available in a browser.
- Native files/DCC and browser inspection/administration remain separate
  capabilities. Share applicable semantics without inventing a browser equivalent
  for every desktop action. Compare editor contents, not system window chrome.

## Verification and source navigation

From TS's product directory, `tools/frame_controls/elements.py --handler-root`
reproduces the control inventory; `controls/catalog.data.mjs` records families/variants.
Presence, paired screenshots and tested behavior are separate evidence. Sample
or state counts do not count base control types or certify the whole library.

Use the relevant `tools/frame_<screen>/capture_qml.py` and frontend scenario;
Users reuses Groups with `--users`. `tools/frame_admin/native_regression.py`
uses separate application processes because repeated full test-application
construction is unstable in the installed PySide. `--failed` reruns failures
without losing the combined log. A normal product remains one native application.
Use `tools/frame_admin/capture.py`, `node tools/frame_admin/browser_regression.mjs`,
`tools/frame_admin/report.py <screen>` and `tools/frame_admin/catalog.py` for paired
capture/reporting. Source hashes must match current local modules, controls and
themes; a run must fail if sources change during capture. Tests use isolated data.

Compare state, scene structure, real geometry, colors/fonts, internal indicators,
button glyphs and input. Qt/Chromium text widths differ: measure label width for
centering rather than loosening control-rectangle tolerances. `check_focus.py`
checks mouse, Tab and programmatic focus. `check_icons.py` and
`frontend/tests/frame_icons.mjs` verify all five icon packs and reject unresolved
native fallback glyphs. The real built-app Administration scenario uses temporary
SQLite and HTTP; it is not a production/PostgreSQL certification. Paired capture
harnesses never submit destructive type deletion.

Legacy icon resolution belongs to shared `core/legacy_icons.mjs` and
`core/icons.mjs`. Admit only known bare raster names and exact original
`/context/icons/...` paths; custom/remote basenames do not inherit an alias.
Keep unresolved behavior for unknown project names/prototype keys. PROCESS retains
its original tile-grid meaning; modern process keeps its separate semantic.
Catalogue registration does not promise all historical IconWdg/plugin coverage.

The shared Gantt prototype demonstrates a common primitive graph and state
transitions; it does not certify production persistence, large data, mobile
layout, every OS scale or complete input-state coverage. Use the existing demo
harness and its source map rather than replacing production widgets with it.

## TH reference map

- [Native component policy](../ui_component_policy.md) and [map](../ui_component_map.md)
- [Handler architecture](../application_architecture.md) and [client API](../handler_api.md)
- [Files](files.md), [support/connection](support.md), [tables](table.md)
- [Stream source layout](../../../TS/tactic_stream/src/tactic_stream/shared_ui/README.md)
- [TH and TS API/source boundaries](../../../TS/tactic_stream/docs/admin_agent/SOURCES.md)

Layout-reference controls use the optional neutral `trailingAction` descriptor
in `controls/forms/sections.ui.mjs`; the shared form reserves one square control
beside the field. Domain state resolves the referenced Search Type/view or known
same-project page; adapters retain editors and route commands. Page-link parsing
never opens arbitrary/external URLs as local administration targets. Passing an
empty `controlId` to `FrameView.focusListRow(id, index, '')` reveals a row without
moving keyboard focus. Canvas selection unfolds ancestors before revealing it.

Nested Item layout navigation belongs to `layout.state.mjs`: it resolves view
widgets using explicit/inherited Search Types, guards dirty/pending work and
retains up to32 parent UI contexts without draft documents. Both adapters load
through their existing readonly configuration owners and reject missing views
or original configuration sources. Return restores source, widget and UI context;
the existing outer Page layout return remains available after unwinding.
Native FrameDragScope owns an exclusive release-within-bounds tap and emits it
once through FrameView, while DragHandler can take over for a drag. Regression
input covers mouse, keyboard, touch and drag/drop without duplicate activation.

Item layout sample data belongs to `layout.samples.mjs`. The common model
uses it only without matching real DTOs for the selected widget and ancestor
scope, never on busy/read/preview errors. Samples have no record identity or
external assets; shared composition and canvas render them without record
operations or enrichment requests. Geometry changes use the ordinary XML draft
path. Both adapters retain the real result surface while samples are visible;
native also retains the sample canvas owner while its scene clears on updates.
Regressions exercise empty/typed scopes, real-data transitions, actual resize,
configuration-only saves and absence of persisted synthetic records.

Page editor document controls are grouped by `page.chrome.mjs` in a full-width
toolbar above the editor panels. Page selection and explicit New page are always
available; empty catalogs hide irrelevant canvas controls. Named pages expose
preview and XML directly, with secondary operations behind a labelled Actions
menu. Undo/Redo and viewport tools share the next row. Both adapters keep the
existing reducer, dirty guards and explicit draft/Check/Save boundary.
Logical paper/content boxes allow resize handles and measurements to extend
outside them; the viewport owns clipping and scrolling, including under zoom.

Object-card image shading uses `search/card.ui.mjs::tileShade` in both native
and browser adapters. The overlay covers the title and description from the top;
object-card text uses primary/selection foreground, while other card kinds retain
their secondary text. Regression checks cover actual white/black preview paint,
light/dark and selected/unselected states, plus 4.5:1 contrast against extreme
images across the three shipped themes. No image sampling or frame-time work is
added to production rendering.

The CheckBox primitive accepts an optional `radius` for its row surface; omission
keeps the existing 10 DIP corner. The access matrix requests zero while retaining
the ordinary native checkbox indicator, keyboard behavior and accessible name.

Expanded related tables share `nested.ui.mjs` focus geometry: the active child remains clear, shared scrim actions cover its parent viewport and close the same scope. Shadow paint reuses the Frame Box. Disabled search reserves no toolbar; its actions move to the existing footer. Enabled search uses the main suggestion presenters and preserves nested scope.

Round buttons are used for main-menu controls and all window/dock title-bar actions. Local service tools use the shared square icon-action control (`iconAction:true`, `round:false`), preserving icon centering and keyboard/touch input.

Panel surfaces and control interiors are separate geometry. A full-width panel
keeps its background at the edge; header, content and footer children keep symmetric
`spacing.content` insets and reserve scrollbar space. The viewport stays full size;
apply this interior once without rewriting authored page/card padding.
Verify both boundaries in native and browser rendering.

Service Button and icon-action controls default to 4 DIP corners in all themes. Frame titlebar Boxes explicitly mark their direct Button children round; native Button and AppButton honor that flag. Primary navigation/window chrome opts in, while local table and editor service controls remain square. Dock chrome declares round actions in shell/dock_chrome.ui.mjs; its drag grip keeps its separate geometry. Browser window hosts also round retained icon actions in the outer title bar, including feature-owned Help and Close. Media, avatars, static chips, status/radio/switch indicators and ripples are separate paint roles.

Shared dashboard conditions use the `pageFilterSearch` port and house SearchField.
The shared `page.filters.mjs` owns matching, typed values, chip layout and removal.
The native CustomLayoutController owns bounded asynchronous value hints and ignores
old page/query results; its close path cancels pending hints. Search remains in the
current window while navigating hints so IME and keyboard focus stay in the field.
Filter values are local page state. The server's CustomLayoutReadCmd resolves only
configured widget scopes, source constraints and native read permissions; see the
Stream Frame contract for the server boundary.

Table headings and plain/status values share cells.ui.mjs alignment: center by default, retaining explicit display justify/align left/center/right. Both engines keep symmetric insets, wrapped-label alignment and column-axis badge placement across resize.

Native workspace pages pass the dock interior corner radius into the shared page chrome; web dock clipping remains the owner of its exterior. Frame Box surfaces honor bottomLeftRadius and bottomRightRadius independently. Keep the page header bottom edge square and native glyphs directly rendered without a whole-dock mask/layer.

Workflow hover previews reuse 128 by 84 DIP task cards in a responsive one-to-three-column grid, with 8 DIP gaps, 12 DIP outer padding, a bounded vertical scroller and a separate Task Manager footer. At most three complete rows are shown before scrolling. Covered inline cards must not receive input through the preview.

Task cell editors open single-value choices directly; paired dates keep their combined editor. Immediate single-field forms use the field title once. Progress uses the house slider and percentage readout; planned hours use the house quarter-hour stepper with a visible hour unit. Preserve project minute/hour conversion, per-field edit permissions and the owning task draft.

Result density follows `features/search/card.ui.mjs:compactRows`: below 445 DIP of the owning pane, existing item cards use compact geometry. Explicit compact mode stays compact; table mode is unchanged. Resize only changes presentation, retaining loaded nodes, expansion and selection.

Wide search headers reveal up to three configured quick-filter groups through the shared search header budget and quickStrip description. Label widths use the rendered control font; whole groups return to the existing full popup as space contracts. Both engines reuse their existing quick-filter selection/configuration owners. Inline quick-filter triggers use the theme field radius and low surface, normal-weight labels, leading semantic icons and a separate trailing chevron. Action nodes honor radiusRole through the existing ItemSurface in both engines; all glyphs retain the same parent activation target.

Apply cached native quick-filter configuration after the groups binding settles
(`Qt.callLater`), because applying settings emits the groups notification again.
The browser already loads its catalog asynchronously. Native/browser inline-filter
regressions verify that expanding a compact header shows the configured groups.

Column `value_align` overrides content alignment only (left/center/right, empty inherits authored display justify/align). Headings call the same alignment helper with content=false. Shared contentX positions value badges and related actions; native text/status and ordinary preview/action presenters retain their existing input owners. Full-width authored widgets keep their internal layout.

Administration header icons (including reload, Help and close) retain round surfaces. Text actions and local catalogue controls keep their existing shape.
