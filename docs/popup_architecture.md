# Transient popup architecture

## Scope

This contract covers menus, combo-box lists, calendars, suggestion lists,
pickers, and other short-lived transient surfaces. Blocking workflow windows
remain `Controls.Dialog` instances and are outside the global transient-popup
coordinator.

`controls/Popup.qml` wraps `QtControls.Popup`; `controls/Menu.qml` wraps
`QtControls.Menu` for native submenu input and ownership.
Content-driven filter/tag panels use `ScrollablePopup`; command menus use
`ActionMenu`. Selectors use `Controls.ComboBox` or `UserComboBox`.

## Ownership

- `controls/Popup.qml` and `controls/Menu.qml` expose the shared popup contract.
  `controls/PopupLogic.js` owns screen-aware placement, opening-input protection,
  same-source toggle suppression, and coordination. `PopupBackground.qml` owns
  the surface, pointer, and shadow. Mutable state belongs to each popup instance.
- Menus register children with Qt's `addMenu` and open them through
  `Menu.openAsSubmenu(row)`.
  Qt then owns adjacent placement, edge flipping, and native mouse-grab
  forwarding for the menu hierarchy; menu windows stay non-modal so ancestors
  remain enabled. `Menu.overlap` removes the two shadow gutters from the
  horizontal separation, so visible parent and child surfaces meet on either
  side of the screen. The invoking row remains the coordinator anchor.
- `controls/ScrollablePopup.qml` owns the bounded content viewport used by
  content-driven panels. It caps the surface against both its feature limit and
  the active screen, reserves the shared scrollbar gutter only on overflow,
  and keeps feature content in one width-stable column. A fixed-height panel
  bounds `implicitHeight` itself because `Popup.Window` can reapply that value
  when a dynamically populated model changes after the window has opened.
- `PopupCoordinator.qml` owns the single active transient branch. A selector
  opened inside a popup joins its parent branch; a sibling replaces the active
  child, while a new root popup closes the previous branch. Replaced owners
  have pending recovery cancelled before they are closed.
- `controls/ComboBox.qml` owns the input transaction that opens its popup.
  Pointer activation is deferred until the previous native Windows popup grab
  has completed; the built-in synchronous open is disabled for that event.
  The coordinator also remembers a just-closed owner so clicking the same field
  closes it while clicking a neighbour opens the neighbour exactly once.
  `UserComboBox.qml` replaces only the popup content and delegates lifecycle
  recovery back to the shared combo control.
- `ActionMenu.qml` owns menu levels, compact density, advanced-action visibility,
  and command dispatch. `ActionMenuRow.qml` presents a row and its focus/input.
  Rows use the active `PopupAction` control so their click cannot fall through
  to the item under the native popup window.
- `controls/PopupAction.qml` owns pointer, Enter/Space, focus, accessibility,
  and cursor behavior for custom rows and cells. Features own only their
  content and state visuals.
- Specialized popup content remains in its feature view, but it uses the base
  placement and lifecycle methods instead of moving a window locally.

## Invariants

1. Transient surfaces use `Popup.Window` unless they are intentionally embedded.
2. Position is resolved before `open()`. Code must not assign `QWindow.x` or
   `QWindow.y`, and must not reposition a shown native popup from width, height,
   or screen-change handlers.
3. `preparePositionAtItem`, `openBelowItem`, `toggleBelowItem`,
   `openCenteredIn`, and `reopenAtItem` are the only placement entry points.
   They map through global coordinates, select the anchor monitor, and clamp to
   its available geometry including taskbar boundaries. Registered submenus use
   `Menu.openAsSubmenu(row)` instead of generic popup placement.
4. Only one coordinated transient branch is active. A parent and its nested
   selector may remain open together. Opening a sibling closes only the active
   child; opening a new root popup closes the whole previous branch.
5. A combo may recover only from a close caused by the same opening pointer
   transaction. Recovery is cancelled when another popup takes ownership. A
   generic `onClosed` timer or unconditional reopen is forbidden.
   Switching between neighbouring combos must produce one `opened` signal and
   no intermediate `closed` signal for the new popup.
6. Touch protection applies to the authentic touch opening sequence and its
   possible synthetic mouse tail. It must not turn a later outside click into a
   reopen.
7. Custom popup rows and cells use `PopupAction`; standard commands use shared
   buttons or item delegates. A passive pointer observer over popup content is
   forbidden.
8. Popup size is bounded by the anchor screen. Long lists scroll inside their
   surface and reserve space for the shared scrollbar. Dragging that scrollbar
   with mouse or touch must move the owning viewport, including in
   `Popup.Window` mode.
9. Opening another popup, pressing Escape, selecting an item, and pressing
   outside each have one deterministic final state. No `onClosed` handler may
   compete with `PopupCoordinator`.

## Adding a popup

Keep command menus to seven or eight entries per level. Use action `children`
for related commands; hover, click, or Right opens the submenu, and Left returns
to its parent. A selected command closes the whole branch. Unbounded data lists
retain the shared scrollbar and its gutter. The sObject menu uses `advanced`
to hide maintenance actions until the user expands it.

Use `Controls.ComboBox` for ordinary choices and `UserComboBox` for users. Use
`ActionMenu` for command lists. For specialized fixed content, derive from
`Controls.Popup` and set a bounded size. Custom submenu content uses
`Controls.Menu` with its content registered through `addItem`. For panels that can
overflow, derive from `Controls.ScrollablePopup` and supply only its column
content. Open either through a base placement method. `toggleBelowItem()`
centrally suppresses a same-source pointer release that has already closed the
popup; calling `rememberSourceOpen()` from `onPressed` remains supported for
controls that need the open state before their command runs.

Do not create a raw `Popup`, duplicate screen clamping, mutate a native popup
window after show, or add a local reopen timer.

## Verification

`tests/test_popup_windows.py`, `tests/test_touch_controls.py`, and
`tests/test_user_combo_box.py` exercise native-window ownership, monitor edges,
long menus, context-menu activation, neighbour switching, the Task Manager
assignee-to-status handoff, nested selector branches, mouse, touch, synthetic
mouse input, same-source toggling without a local press guard, bounded filter
panels, a fixed-height tag panel populated after opening, scrollbar gutter
reservation, active filter-chip clicks, and user-list selection. An architecture
regression scans every popup block: overflow views
must use the shared scrollbar and popup actions may not use passive pointer
handlers. The QML smoke harness creates and reopens every registered window.
Neighbour switching, same-field closing, the Task Manager assignee-to-status
handoff, and touch-tail suppression are additionally run through the real
Windows QPA because offscreen input dispatch does not model the native popup
grab. `tests/test_compact_menus_qml.py` also checks hover between native submenu
windows, keyboard return to a parent, nested command dispatch, screen-edge
placement, and scrolling through presets.
