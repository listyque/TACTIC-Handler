---
reference: Handler
group: Guide
icon: tune
order: 7
---
# Common controls

Checkboxes share a centered indicator mark, including Messages notifications.
Click the label or tap the mark to toggle the value; use Space with the keyboard.
Disabled checkboxes retain their value.

Combo boxes open on click and close when the same field is clicked again.
Their lists fit the longest label within the available screen width, including
when the field sits in a narrow table column.

User selectors show an avatar, name and login, with grouped searchable choices and a check
beside the current assignee. Search by name, login, email or group. Down enters the list;
arrows move between users, Enter selects and Escape closes without changing the value.

Date fields use the same calendar throughout tasks, milestones, timesheets and record forms.
Click the calendar icon, choose a month and day, and set hours/minutes when available.
Today and Clear are in the footer. Dates display in your interface language; focus the
text field to edit YYYY-MM-DD or YYYY-MM-DD HH:mm. Arrow keys move between calendar days.
Escape cancels browsing. Date-only fields do not accept a time; required fields must contain
a valid date. Unchanged record dates retain their original time zone and precision.

> The same controls and visual states are reused throughout the application. Use the cross in a search
> field to clear its query. Escape clears ordinary searches; suggestion fields keep their own keyboard
> navigation.

## Main controls

Search fields support suggestions and tags. Tabs isolate work contexts.

Filter chips show active constraints. Badges show task, note, queue, or notification counts.

Three-dot buttons contain secondary actions. A six-dot grip moves a dock; right-click it for Help,
docking/floating, maximize and close. Release it on a highlighted zone to dock; outside these zones
it floats within the browser workspace. Escape cancels the gesture. Adjacent docks share a splitter.
Stacked docks keep one shared move grip beside their tabs, including when Results is the active tab;
the search toolbar itself has no grip. Title buttons are fixed circles with centered icons.
Splitters throughout the application use the same short centered resize grip. Drag it to resize
adjacent panels; it highlights on hover and press.
The grip is 3 × 40 pixels inside a 10-pixel separator, including editors,
Snapshot Browser and the results/versions split. Focus the separator and use
arrow keys to resize it with the keyboard; editor splitters also support Home
and End. On phones the separator is hidden and panels use the mobile layout.

Scrollbars use the Handler appearance in panels, menus, dialogs and code editors.
They remain visible whenever content overflows and reserve a 12-pixel gutter in
Chromium/Electron. The centered thumb expands from 5 to 8 pixels on hover or drag;
the gutter stays fixed. Other browsers use their native thin scrollbar fallback.

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

On phone item and task screens, routine reads keep the current scroll position. Opening a screen
or returning to it restores its saved position after loading; a new wheel or touch gesture cancels
that pending restore. Search and tab controls hide while scrolling down and return while scrolling up.
Collapsed controls retain their extent inside the root scroll content, so visible rows stay in place
when toolbars hide or return. Small movements near the start leave the toolbars visible.

Drag a shared scrollbar with the mouse or touch to move its owning list directly, including inside
native popup windows. Dragging a scrollbar navigates only the records already loaded.

Incremental lists request another page only after a wheel or flick gesture reaches the end, or when
their explicit load action is used.

## Usage notes

- Hover a compact icon for its tooltip.
- Mouse clicks tolerate a small release drift at a button or tab edge, matching Handler's drag threshold. Moving away starts a drag or cancels the click. Actions still run on release, once; keyboard and touch use their native activation.
- Focus does not draw an outline around controls. Keyboard navigation, selection markers and button focus backgrounds remain available.
- Disabled controls are unavailable for the current selection or while an operation is running.
- Selection uses the theme accent rather than a separate local color.
- Every dock footer uses the same height, upper divider, and rounded lower corners.
- Transient notifications stay above the dock footer so its actions remain accessible.

## Inspector and shared windows (0.112.34)

Inspector uses the same ItemPreview, user/status selectors, text/date fields, slider, attachment
card, composer, menus and buttons as the other panels. API reads and writes stay in its container;
its context header only presents data and emits actions.

Floating dialogs share dragging by the title bar, eight resize edges, maximize/restore and
Alt+F10. Focus the title bar: Alt+arrows moves it and Alt+Shift+arrows changes its size in 10px steps.
Escape or losing window focus cancels an active pointer gesture. Nested dialogs own separate controls;
an embedded dock does not add a second set. On narrow screens the window fills the viewport.
Resize hit areas follow the window border rather than scrolling over form fields. This behavior
is available now; completing dock layout persistence remains a separate workspace block.

## Windows, dialogs and docks in TACTIC Stream

Help, Messages, Activity Feed, Notifications, Script Editor, Script Shelf, Debug Log, UI responsiveness, User Profile, Duplicate and other utility windows are nonmodal, matching Handler. Their frame supports moving, resizing, maximizing/restoring and minimizing to the title bar. Reopening raises the same window and restores its content. Closing Help returns to the invoking screen without losing its draft.

Blocking project wizards, Administration, schema/process editors, Quick Filter Editor and task forms retain modal guards. Short confirmations, pickers and local forms use compact themed dialogs without work-window controls. A utility window opened from a blocking dialog remains usable above that owner; closing the owner closes its child views.

Task Inspector, Calendar, Tasks, files and preview panels remain docks. Weekly Timesheet, Work Reports and Cost Reports are separate docks with independent state. New panels use Handler's default tab groups; your saved layout is retained. On phones, work windows use the existing full-screen Back layout; compact confirmations remain compact.

Notifications places its title and Clear history action, description, and full-width filters in three
separate rows, matching Handler. Narrow windows show filter icons with accessible labels; segment
labels stay on one line. Filtering does not delete events; Clear history removes this session's history.


When dock tabs overflow, scroll their strip horizontally. The scrollbar has its
own space below the labels and selection marker. Switching a tab keeps the
loaded panel and its current working state.

In narrow graph panels the zoom percentage gives way to the four graph actions.
If necessary, the actions wrap to another row; zoom, reset and center selection
remain reachable. The automatic layout action keeps its own space.

In editable Administration lists, sorting keeps the active text field, caret and
selection with its record. Input-method composition stays in the editor until
committed; Enter during composition does not submit the form. If the edited
record is removed, its text is never assigned to the next row. Scrolling and
resizing retain a valid viewport when the list becomes shorter or empty.

## Shared control behavior

Buttons, fields, choices and checkboxes use the same sizes, typography and
interaction states in Handler and Stream. Long button labels are elided within
the button. A mixed checkbox displays a dash; the next activation chooses a
normal value. Disabled controls preserve their values and cannot issue actions.
An open picker closes if its owner becomes disabled.

The icon library opens beside its button. Search or choose an icon set, use the
arrow keys to move through the grid and Enter to choose. Escape cancels and
returns focus. The color dialog previews a draft: OK accepts it; Cancel keeps
the previous color. An empty color starts with the current theme accent.

Use arrows in the Sidebar Editor tree to select rows and expand or collapse
sections; Home and End select the first and last visible rows. Editing guards
remain active. A responsive view decides whether its splitter is useful on a
phone; narrow width alone does not disable a visible splitter.
