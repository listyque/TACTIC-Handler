# Tactic Frame: Scripts and native tools

This contract describes source ownership, behavior and verification scope.
TH and TS ship independently; native-only actions remain native capabilities.
Use [the shared contract](contract.md) and [the feature index](index.md).

## Composition and ownership

| Surface | Portable description | Owners and capabilities retained |
| --- | --- | --- |
| Script Editor | `features/scripts/editor.ui.mjs`, `source.ui.mjs` | Existing buffers, analysis/completion, undo/history, revisions, execution and cleanup. Native: local Python/QML, server and selected DCC. Browser: server Python/JS and browser JS. Unsupported saved languages stay visible/read-only |
| Shelf bar/editor | `features/scripts/bar.ui.mjs`, `shelf.ui.mjs` | Existing personal/global/tab/preset XML, ACL, revision and assignment owners. Hierarchical script/icon pickers and native DCC shelf export remain house controls |
| Script triggers | `features/scripts/triggers.ui.mjs` | Existing Handler before/after hooks, matching, ordered rules, validation and writes. A native capability, not a browser hook installer |
| DCC options | `features/tools/dcc.ui.mjs` | Connector manifests, normalization and action invocation. Confirmation stays bound to the client selected when the form opened |
| Handler Server | `features/tools/server.ui.mjs` | Existing service lifecycle, client/capability/result models, fixed registered commands, JSON validation and transport |
| Selected-object Database tools | `features/tools/database.ui.mjs` | Existing active-object and exact-selection writes, dirty/context retention and field ordering. Large field lists are virtualized; scrolling preserves drafts. Administration Raw Database belongs to B03 |
| Batch Manager | Existing `side_tools/batch_scheduler` | Scheduler, DCC/render work, native launcher and its existing web UI are preserved. No replacement scheduler or additional browser version |

Native adapters are grouped under `thlib/ui/qml/features/scripts` and
`features/tools`; public QML names remain small compatibility facades. Vue
adapters remain under `frontend/src/features/scripts`. Both repositories ship
their own physical module copies. Neither product imports the other checkout.

Source editing, the typed tree/tabs and native saved-history hosting keep their
existing engine presenters. Shared parts include workspace, commands, surfaces,
fields, list rows and state predicates. Comparisons check corresponding Frame
controls and source-editor host geometry, not pixel identity for every engine's
text rasterization or native-only capability.

## Small reusable native example

Handler ships `side_tools/frame_tool` in its existing side-tools release path.
From a local Python script on the GUI thread:

```python
from side_tools.frame_tool.showcase import show

show([{"id": "asset-a", "title": "Robot Arm"},
      {"id": "asset-b", "title": "Robot Body"}])
```

- `selection.ui.mjs` composes existing Field, List, Label and Button controls.
- `Main.qml` is a nonmodal native window and its small event adapter.
- `showcase.py` retains/releases the component and window, using the existing
  record model and GUI engine. It creates no application, worker, server or browser.

Preview produces the explicit selection as JSON. It performs no check-in,
repository synchronization, queue submission or render. Tests cover 100 objects,
visible scrolling, keyboard/mouse input, resize, clear, hide/reopen and close
cleanup. Close the example before reloading its Python module during development.
Batch Manager remains a separate tool with its existing execution owners.

## Execution and lifecycle requirements

- Completion after a newline no longer matches the previous word; an empty
  prefix starts at the cursor in both products.
- DCC confirmation rejects a different selected client before running or saving
  options. Returning to the original client or reopening the action recovers.
- Native shelf drafts cannot save into another tab's context. Picker results
  carry button/rule identity and document scope; discard/reload invalidates an
  old picker even when the same record remains selected.
- Trigger reload asks before discarding a draft; cancellation keeps the draft.
- Confirmed browser assignments immediately display Used on this tab.
- An unknown browser write result keeps shelf fields and picker buttons disabled;
  draft events use the same shared edit predicate until reload.
- Script chooser triggers use one shared Frame Button face, including icon,
  alignment and typography. Existing tree popup owners remain in their hosts.
  Closing a valid selection returns keyboard focus; removing/recycling a row
  invalidates its pending popup before another button can occupy that index.
- Hidden wrapped Frame labels stay hidden instead of intercepting pointer input.
- Numeric patterns use literal Unicode grouping spaces accepted by JavaScript
  and Qt's PCRE2 bridge. Russian grouped decimal input is tested.
- Snapshot arrays use the array adapter even with declared fields, keeping them
  out of Qt role-model delegate lifetimes. A resize, array clear and disabled
  sender previously caused a native access violation. Both adapters pass row
  indexes, preserving selection. Native updates remain synchronous; rapid input,
  large-list identity, selection and IME remain platform checks.
- Source toolbars reserve scrollbar space in both engines. Old browser editor
  geometry overrides were removed; decorative borders no longer shift shared
  content by a pixel.

Cancel in native confirmation cancels a pending request. It does not safely
terminate already running Python. Server/browser execution retains its existing
limitation; the UI does not invent forced interruption.

## Verification

Run the focused drivers under `tools/frame_scripts/` from the Stream development
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

Shelf runtime labels come from the saved script language through the existing
script catalog/model. `local_python` and `dcc_python` show a compact TH marker;
server/browser languages remain distinct tooltip labels. The browser result
header captures the language at invocation, including failures. This is
presentation metadata only: execution permissions, dispatch and trigger
payloads are unchanged.
