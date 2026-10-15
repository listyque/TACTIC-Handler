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
| `features/administration` | Administration shell, forms and document guards | Core and controls |
| `features/administration/<section>` | A section's UI and state | Shared admin helpers and its own domain |

`shell` currently owns window geometry, main-toolbar positions and dock-header
composition. Hosts retain native input, application commands, lifecycle and
persistence. Dock trees and complete main-window menus are not migrated yet.

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
