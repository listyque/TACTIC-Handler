---
group: Workflows
icon: link
order: 95
---
# Related objects

With Stream, Handler loads the relationship list using your project permissions.
The window distinguishes an unconfigured relationship from a read-only one.
Creating a record also requires access to the native editor.

Open the relationship button on an object row or card. The menu shows related types and **Related objects**. Choose a type directly, or open the window and choose **Related type**. The selected object's identity stays attached to the query: filtering and paging do not search the whole project.

The window uses the standard title bar, shadow, resize and maximize/restore controls. Closing it preserves the main search. Changing project or connection invalidates the old context.

**Create related object** opens the existing creation form with the owning object. Row actions use the existing object operations and server permissions. **Link existing objects** remains a separate editor for instance relations; its unsaved-change and uncertain-save guards still apply.
