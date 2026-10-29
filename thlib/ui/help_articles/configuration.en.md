---
group: Guide
icon: settings
order: 5
---
# Configuration

The page title and actions share one header. Window controls remain native.
Restoring the window preserves the current page and its draft; closing still
checks for unsaved changes.

Scroll long pages with the mouse wheel or trackpad over their content. The shared scrollbar remains visible whenever the page exceeds the available height.

> Configuration edits one preference page at a time. Use the Help button beside the current page
> title for an exact explanation of every option on that page.

## Page navigation

The left column selects **Server**, **Repositories**, **Projects**, **Check-in Options**, **Global**,
**Appearance**, **Cache**, **Tasks**, or **Maya Scene**. A dot beside a page means that its draft
differs from the saved configuration.

## Common actions

The current page's Reset and Apply buttons, plus Save and Close for the window, are in the top
header beside the page title. In a narrow window they show icons with tooltips.

| Control | What it does |
| --- | --- |
| **Help** | Opens the article for the page currently shown, not a generic settings article. |
| **Reset** | Restores the current page's saved values. It is enabled only when that page has unsaved changes. |
| **Apply** | Applies the current page without closing Configuration. |
| **Save** | Saves pending configuration changes without closing the window. It becomes disabled when all changes are saved. |
| **Close** | Requests to close Configuration. If drafts exist, choose Save, Discard, or return to editing. |

Settings on one page do not overwrite another page. Long pages retain a visible scrollbar, and
server-defined names such as projects, processes, repositories, and Search Types are shown exactly
as supplied by TACTIC.

## Where values live

User preferences use the shared TACTIC Handler configuration API. The **Global** page shows the
active configuration root for diagnostics. Window geometry and short-lived working state are saved
separately from user-facing preferences.

## Shared composition

Configuration now uses the same Tactic Frame navigation and explained settings rows in Handler and Stream. Long pages reserve space for a visible scrollbar; on phones the page selector replaces the sidebar. The current page keeps its own draft. Native preset saves preserve drafts on other pages. Local/DCC/tray/GPU options belong to Handler; browser XML, web paths and browser preferences remain Stream capabilities. No embedded browser is used by Handler.

On narrow repository editors, Reset and Sync use icon buttons with full tooltips; Save remains labelled. Project Save and template installation keep their complete captions in English and Russian.

The Projects page separates the catalogue and project actions into bordered surfaces. Filters stay in the catalogue header, the project count stays in its footer, and only the list scrolls. On narrow windows the actions appear above the catalogue.

AI providers opens the connection editor directly inside Configuration. Select or create a connection, edit its settings and use its own Save or Check connection actions. Switching configuration pages preserves the connection draft; hidden editors stop connection polling. Account changes clear the draft. The agent chat can still open the same editor as a separate window.
