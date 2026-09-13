---
group: Guide
icon: tune
order: 7
---
# Common controls

> The same controls and visual states are reused throughout the application. Use the cross in a search
> field to clear its query. Escape clears ordinary searches; suggestion fields keep their own keyboard
> navigation.

## Main controls

Search fields support suggestions and tags. Tabs isolate work contexts.

Filter chips show active constraints. Badges show task, note, queue, or notification counts.

Three-dot buttons contain secondary actions. A six-dot grip moves a dock; right-click it for Help,
docking, detaching, and closing actions.

Right-clicking selected text keeps the selection available for Cut or Copy. Right-clicking outside
the selection moves the text cursor to the clicked position.

Touch controls emit one activation per release. Small movement remains a tap, while a deliberate
drag is handed to the surrounding scroll view without activating the control.

Menus opened by a tap or long press remain available after the opening gesture, including when
Windows sends delayed synthetic mouse input; tap an enabled menu item to run it. User pickers keep
the current login visible in its server group and mark it as unavailable when self-selection is not
allowed.

Scrollable lists and item grids show a theme-aware scrollbar whenever their content exceeds the
visible area. Vertical scrollbars stay at the right edge; horizontal scrollbars stay at the bottom
edge.

Drag a shared scrollbar with the mouse or touch to move its owning list directly, including inside
native popup windows. Dragging a scrollbar navigates only the records already loaded.

Incremental lists request another page only after a wheel or flick gesture reaches the end, or when
their explicit load action is used.

## Usage notes

- Hover a compact icon for its tooltip.
- Disabled controls are unavailable for the current selection or while an operation is running.
- Selection uses the theme accent rather than a separate local color.
- Every dock footer uses the same height, upper divider, and rounded lower corners.
- Transient notifications stay above the dock footer so its actions remain accessible.
