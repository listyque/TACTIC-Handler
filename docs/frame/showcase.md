# Component showcase and reference audit

The shipped entry point is **Administration -> Component showcase**, in both
products. It is a local component workbench: no project reads, writes, plugin
installation or persistent drafts. Changing projects does not change its data.
Narrow layouts reserve two complete heading line boxes before the subtitle;
longer family names retain the full accessible name when elided.

The workbench contains **29 live families in six groups**. Source presence,
individual examples and complete product behavior acceptance remain separate
evidence: the workbench is not a mock project administration application.

## Source owners

- `shared_ui/controls/catalog.data.mjs`: the canonical inventory, categories,
  EN/RU family labels, existing native/Vue names, variants, boundaries and gaps.
  The source audit imports this module with Node; there is no parallel JSON list.
- `shared_ui/controls/showcase.examples.mjs`: executable neutral Frame examples.
- `shared_ui/features/administration/showcase.examples.mjs`: the remaining
  thirteen compositions, their local grid cells/models and copied source.
- `shared_ui/features/administration/showcase.ui.mjs`: local state, filtering,
  navigation, preview bounds and read-only code presentation.
- Stream's `ComponentShowcase.vue` and Handler's `ComponentShowcaseView.qml`:
  render the same scene using their house controls. Handler supplies a private
  `SourceEditorService` to the existing code control. No project editor is reused
  as its state owner.

These paths are relative to each product's independent Frame copy. The wrappers,
services and deployment bundles remain product-owned. Source snippets demonstrate
the shared `node`/`rect` API; a host still owns event handling and any named services.

The new neutral kinds are Search, Identity, Progress, Empty and FileField, mapped
to the existing house components. Native FileField loads FileInput by URL only
when instantiated: FileInput contains a FrameView, so a static type dependency
would prevent every FrameView and the application shell from loading.

Menu and short-confirmation examples use named View ports and existing AppMenu /
ActionMenu and AppDialog / Dialog owners. They are not alternate window systems.
The table uses the existing virtual Grid with 100 local editable rows; Handler
adapts these records through Qt TableModel. It does not issue object commands or
claim to replace the main record table. Graph nodes support native selection and
movement with local state. Code uses a separate editable source buffer. File
selection/drop retains display names only; nothing is uploaded or executed.
The domain fragment uses the actual task surface description with a local draft.

## Reference inspection

Reference: [Sing App Vue live demo](https://demo.flatlogic.com/sing-app-vue/).
The inspection visited 29 navigation destinations covering **28 unique routes**:
Pagination links to the same dynamic table page. Its taxonomy and examples inform
this catalogue; its source code, CSS, text passages and artwork are not copied.

| Reference destination | Frame counterpart and decision |
| --- | --- |
| Core / Typography | Existing text roles and line boxes, semantic Label headings; live role/size samples. Rich documents remain separate from plain labels. |
| Core / Colors | Existing semantic palette and surface roles; live swatches follow the current theme. No fixed Bootstrap colors added. |
| Core / Grid | Existing shared row/column/grid layout and responsive sizing. A layout grid is distinct from the data Grid control. |
| UI / Alerts | Live error/empty feedback and Retry; no project operation. |
| UI / Badge | StatusChip and SummaryChip: live semantic colors, dense/icon variants and 0/1/125 counters. Overlay badges, flow chips and presence indicators remain distinct roles. |
| UI / Buttons | Existing Button/AppButton variants, icon actions, primary and destructive actions; live enabled/disabled input. |
| UI / Card | Existing Box children and appearance/shadow contract. Do not introduce a Card wrapper solely for a new name. |
| UI / Carousel | The inspected route rendered empty. File-preview navigation is domain-owned; no generic carousel is claimed. |
| UI / Jumbotron | Compose existing typography and surfaces; no separate hero primitive is needed. |
| UI / Icons | Existing semantic icon mapping and installed font sets; live glyph/name examples. |
| UI / List Groups | Existing listAction/navigationRow, virtual lists and selected surfaces. Live count rows and two-line groups; tree/sorting variants remain in existing tools. |
| UI / Modal | Live short confirmation with Apply/Cancel, Escape and owner cleanup. |
| UI / Nav | Existing segmented controls and tabs; live local selection. Menus retain their existing popup owner. |
| UI / Navbar | Application shell and neutral header composition; do not duplicate shell routing in a base widget. |
| UI / Notifications | Existing notification owner and feedback controls. No extra background timers or demo notifications are installed. |
| UI / Popovers and Tooltips | Live contextual/check/submenu actions and the input example's native tooltip. Existing owners handle placement and dismissal. |
| UI / Progress | Live controlled determinate progress, indeterminate loading and Retry. No background work or idle timer. |
| UI / Tabs and Accordion | Segmented selection is live. Collapsible trees and panels already exist; a generic accordion example is still pending. |
| Forms / Elements | Live text/area, check/switch, choices, numeric text, date, user, color and icon inputs. Not every existing slider/picker variant is represented. |
| Forms / Validation | Existing disabled/read-only/error states; live local switching. Business validation stays with the feature and server. |
| Forms / Wizard | Existing project/setup workflows are domain components. No generic wizard contract is claimed. |
| Charts / Overview | Shared bar, line and donut Chart examples are live. |
| Charts / Apex | Another engine's examples are not additional Frame control types. |
| Charts / Echarts | Polar/scatter/gauge and multiple series are gaps, not renamed bar charts. |
| Charts / Highcharts | Same boundary: current Frame supports one series and its existing accessible values/hover. |
| Grid / draggable widgets | Existing docking and layout-editor owners. Not a generic draggable-grid promise. |
| Tables / Basic | Existing main/nested table owner, header, context menus, status and selection. No second cosmetic table implementation added. |
| Tables / Dynamic, also Pagination | Existing virtual Grid has 100 editable local rows, check cells and both scroll axes. Main record sorting/paging remains in its existing feature. |

## Extending the workbench

Add a family/variant to the existing inventory first. Reuse a house component or
shared composition; add a primitive only when the behavior requires one. An example
must say which variants it actually demonstrates. It must not write user settings,
query a project, execute Python or fake a server-backed operation.

Keep primitive controls, neutral compositions, input/window infrastructure and
domain fragments separate. For example, a count chip is neutral; a task card that
opens an inspector is a domain component. Inventory membership is not a claim of
one-to-one equivalence between native and browser class names.

## Verification

From the Stream product: `node frontend/tests/frame_showcase.mjs` checks all live
families, eight selectable states, EN/RU and 320/620/1000px scenes against the real Frame contract.
`node frontend/tests/showcase.mjs` exercises the actual Administration host, local
input, code, both palettes, narrow widths, zero server commands and Close.
`tools/frame_controls/elements.py --handler-root <handler>` still classifies actual
source against this same catalogue. Handler's `tests.test_frame_showcase` creates
the real QML, exercises input, the read-only code service and small/light layouts.
Not every state changes a passive control: read-only identity is already passive,
for example. Hover, press, focus, input method and popup lifetime are real input
states, not screenshot-only flags. These checks do not certify every catalogued
variant, style, DPI or touch device.
