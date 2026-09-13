---
group: Guide
icon: settings
order: 5
---
# Configuration

> Configuration edits one preference page at a time. Use the Help button beside the current page
> title for an exact explanation of every option on that page.

## Page navigation

The left column selects **Server**, **Repositories**, **Projects**, **Check-in Options**, **Global**,
**Appearance**, **Cache**, **Tasks**, or **Maya Scene**. A dot beside a page means that its draft
differs from the saved configuration.

## Common actions

| Control | What it does |
| --- | --- |
| **Help** | Opens the article for the page currently shown, not a generic settings article. |
| **Reset** | Restores the current page's saved values. It is enabled only when that page has unsaved changes. |
| **Apply** | Applies the current page without closing Configuration. |
| **Save** | Saves pending configuration changes and closes the window. |
| **Cancel** | Requests to close Configuration. If drafts exist, choose Save, Discard, or return to editing. |

Settings on one page do not overwrite another page. Long pages retain a visible scrollbar, and
server-defined names such as projects, processes, repositories, and Search Types are shown exactly
as supplied by TACTIC.

## Where values live

User preferences use the shared TACTIC Handler configuration API. The **Global** page shows the
active configuration root for diagnostics. Window geometry and short-lived working state are saved
separately from user-facing preferences.
