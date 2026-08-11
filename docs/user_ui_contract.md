# User UI contract

## Sources reviewed

- Current QML shell, authentication flow, Tasks and Communication controllers.
- Original `Ui_userIconWidget`, top-bar user menu, account editing path, task/note user rendering.
- Existing `Login`, `LoginGroup`, `env_inst` and `tactic_classes` APIs. `thlib/side` was excluded.
- No Git metadata is present in the supplied working directory, so deleted intermediate
  modern revisions cannot be reconstructed from repository history.

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
| Avatar | Cached login `icon` or `publish` snapshot | Initials; no eager download |
| Email | `email` returned in login info | Hidden when absent |
| Contact | `phone`, `telephone`, `mobile`, `address` | Hidden when absent |
| Project | current `ApplicationController` project | Empty before project selection |
| Connection/server | current controller/environment | Read-only |
| Assigned tasks | `sthpw/task`, `assigned = login`, current project | Async, read-only |
| Recent activity | `sthpw/status_log`, `login = login`, current project | Hidden/unavailable when API or permissions reject it |

No password, ticket, raw TACTIC object or inferred personal data may enter QML models.

## Actions

- Open current profile from the top-bar user menu and the temporary tools catalog.
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

- Opening profiles performs read-only server queries for tasks and status history.
- Sign out clears the current ticket and workspace presentation state; it does not delete
  server data or stored server configuration.
- Profile editing uses a restricted allow-list and the native login object API; passwords
  and group membership never enter QML storage.
- Group importance is resolved centrally for list presentation from the native TACTIC
  levels (`high`, `medium`, `low`, `min`, `none`), cached allow rules and semantic role.
  Empty, `0`, and unknown legacy values do not override a meaningful group. Authorization
  remains server-side and is never inferred from this presentation rank.
