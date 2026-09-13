# User UI contract

## Sources reviewed

- Current QML shell, authentication flow, Tasks and Communication controllers.
- Original `Ui_userIconWidget`, top-bar user menu, account editing path, task/note user rendering.
- Existing `Login`, `LoginGroup`, `env_inst` and `tactic_classes` APIs. `thlib/side` was excluded.
- No Git metadata is present in the supplied working directory, so deleted intermediate
  earlier revisions cannot be reconstructed from repository history.

## Original behavior

- The top bar displayed the current `Login` icon. It used cached `icon`/`publish`
  snapshots and fell back to display-name initials on a deterministic login color.
- Its user menu exposed `Edit My Account`; this opened the common sObject editor for
  the current `sthpw/login` with the `edit_account` view.
- Task assignees and note authors used the same login objects/icons. Search user menus
  were grouped through `Login.get_login_groups()` and `LoginGroup.get_logins()`.
- The original top-bar UI did not provide direct user switching. A different user could
  authenticate only through the normal login/ticket flow.

## Current data contract

| Field | Source | Fallback/constraint |
|---|---|---|
| Login | `Login.get_login()` / `env_server.get_user()` | Empty while signed out |
| Display name | `Login.get_display_name()` | Login code |
| Login groups | `Login.get_login_groups()` | Empty list |
| Primary login group | Cached `login_group.access_level`, effective access rules, project/default metadata | Presentation grouping only; never grants permission |
| Roles | `role`/`roles` returned in login info | Never inferred from group names |
| Avatar | Cached login `icon` or `publish` snapshot; native web/preview/main file before icon fallback | Initials; no eager download; tiny icon derivatives are never stretched into the shared large avatar source |
| Email | `email` returned in login info | Hidden when absent |
| Contact | `phone_number`, `phone`, `telephone`, `mobile` | Hidden when absent |
| Address | `address` returned in login info | Hidden when absent; editable with the profile |
| Project | current `ApplicationController` project | Empty before project selection |
| Connection/server | current controller/environment | Read-only |
| Assigned-task summary | `sthpw/task`, `assigned = login`, current project | Complete server aggregate; no unused task samples are returned |
| Work-hour summary | `sthpw/work_hour`, selected login, current project and current Monday–Sunday week | Visible to the same user or a server-authorized supervisor |
| Recent activity | the same complete non-chat activity journal and selected-user scope as Activity Feed | A note visible here cannot be omitted by the feed's All filter; chat remains in Messages |

No password, ticket, raw TACTIC object or inferred personal data may enter QML models.

## Actions

- Open current profile from the top-bar user menu and the tools catalog.
- Open the users list from both menus; selecting a user opens that profile in the same
  singleton window.
- Open an assignee/author profile by clicking the user in Tasks or Communication.
- Refresh profile tasks/activity asynchronously.
- Sign out by clearing the existing ticket and returning to the existing Login dialog.
- Edit the selected user's group membership through the native login membership API.
- Edit the group-wide `access_level` beside membership. The value belongs to the
  login group, affects every member, and is persisted by one restricted server operation.
- Direct user switching is intentionally absent because it was not an original action;
  sign out followed by login supports changing identity through the established flow.

## Side effects and safety

- Opening profiles performs one read-only server query for task aggregates,
  authorized current-week work hours, and recent non-chat activity.
- Sign out clears the current ticket and workspace presentation state; it does not delete
  server data or stored server configuration.
- Profile editing uses a restricted allow-list and the native login object API; passwords
  and group membership never enter QML storage.
- Group importance is resolved centrally for list presentation from the native TACTIC
  levels (`high`, `medium`, `low`, `min`, `none`), cached allow rules and semantic role.
  Empty, `0`, and unknown legacy values do not override a meaningful group. Authorization
  remains server-side and is never inferred from this presentation rank.

## Search Object duplication

- `Duplicate…` analyzes the selected Search Object off the UI thread and opens a
  five-step native editor for fields, schema relationships, snapshots, tasks and messages,
  and review. Its first page consumes the same TACTIC Edit View field catalog, field model,
  validation, responsive layout, and control delegates as `EditSObject`; it does not infer
  a second set of text-only controls from database columns.
- Identity, project, and relationship columns remain server-managed. Parent links may be
  preserved or cleared; direct children may be copied; instance targets are never cloned,
  only new instance connector records are created for the duplicate.
- Current snapshots are copied through TACTIC's native inplace check-in path. Snapshot,
  task, process-message, task-message, and attachment choices are made independently per
  process. Root messages are queried from `sthpw/note` by their native object or task
  identity; duplication does not depend on a synthetic `Note.get_by_sobjects` API. Note
  attachments are discovered from both native note snapshots and attachment connections
  and checked into the copied note. Snapshots directly owned by a task are checked into
  the copied task. Missing repository paths or a failed server create are reported as
  duplication errors instead of being counted as successful copies.
- A remembered profile is scoped by project and Search Type and stores only relation and
  process choices. Object-specific field values are never persisted in the profile.
- The primary `Duplicate` action stays visible on every wizard step and immediately uses
  the current choices, including the remembered profile applied during analysis.
- `Quick duplicate with last settings` is available only after a profile exists. It still
  performs fresh analysis so removed relations, processes, or content cannot be replayed
  from stale object data.
