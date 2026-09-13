# Configuration UI contract

Configuration is a native resizable top-level window hosted by the shared
window infrastructure. This document describes the current QML configuration
contract and removes obsolete comparisons with disabled QWidget pages.

## Shared window behavior

- The window provides page navigation, per-page dirty state, Apply, Save/OK,
  Cancel, Reset, and one close guard.
- Apply commits the active dirty page. Save commits every dirty page with a
  working persistence contract and closes only after success.
- Closing with unsaved changes offers Save, Discard, and Cancel. There is no
  hidden save.
- Reset restores the current session snapshot for the active page; it does not
  manufacture application defaults independently of the owning API.
- Geometry is owned by `FloatingWindowModel` and clamped to shared minimums and
  the active screen.
- Every page and long section scrolls within the window. Narrow layout reflows
  actions without overlapping labels, cards, or navigation.
- Configuration uses the same theme roles, controls, spacing, scrollbars,
  footers, and localization paths as the functional UI.

## Persistence boundaries

- Application UI state uses `env_read_config` and `env_write_config` only.
- Server settings use the existing `env_server` API.
- Maya Scene settings use `cfg_controls.get_maya_scene` and
  `cfg_controls.set_maya_scene`.
- Check-in settings use the same configuration keys and APIs consumed by
  Check-in/Out; there is no QML-only settings copy.
- Server-data cache domains are exposed on the dedicated Cache page. Window
  geometry, transient workers, drafts, and per-tab working state are not cache
  settings and are never removed by Clear Cache.
- Applying one page must not rewrite unrelated keys owned by another controller.

## Server page

The page loads the active server preset, TACTIC URL, current authenticated
login, portal site, and proxy routing from `env_server`.

- The active login is presentation state from the current ticket workflow, not
  a second editable login field.
- URL scheme/host, preset, site dependencies, and proxy dependencies are
  validated before save.
- Test Connection runs asynchronously through `env_inst.server_pool` and shows
  busy, success, and concise error states without blocking the GUI.
- Apply writes through `env_server`, invalidates the old ticket where required,
  and delegates reconnect/bootstrap to the application controller.
- Stored secrets are never exposed back to QML or Debug Log.
- Account and routing details use compact expandable sections rather than one
  permanently dense form.
- Server preset editing remains a separate native functional window using the
  same environment API.

## Projects page

The page uses the shared project catalog and the same filters as Project
Chooser.

Each project record may expose code, title, category, type, active/archived or
template state, built-in state, square preview, web image, and available
statistics. Missing data is shown as unavailable, not synthesized.

- Show retired, templates, and built-in project choices use the shared model.
- Double-click and Activate use the same project-selection path as Project
  Chooser.
- Selection remains stable when previews arrive asynchronously.
- Narrow layout keeps the project list usable and moves primary actions above
  it without squeezing the list to zero width.
- Create Project opens a separate native wizard shell. The wizard does not
  perform server writes until every project-creation stage has an implemented
  and tested API.
- Edit Project is the future owner for changing title, lifecycle state, and
  preview; it must use an explicit server mutation workflow.

Project activation is immediate navigation and is not part of page Apply/Reset.

## Repositories page

Repositories is a first-level Configuration page directly below Server. It
summarizes the default repository for the current platform and the enabled
locations, while structured editing remains owned by the existing Repository
Editor and native `env_tactic`/`cfg_controls` APIs.

- A repository is configured only when the active default repository has a
  non-empty path for the current platform.
- The page never performs a filesystem or server check while it renders.
  Explicit path validation continues to run in the local worker pool.
- Repository definitions, platform paths, enabled state, custom locations, and
  default selection are edited through Repository Editor; Configuration does
  not keep a second copy.
- After an online bootstrap resolves the active server preset, a missing
  default path opens one modal setup offer per application launch. Dismissing
  the offer is session-only, so the next launch asks again until setup is
  complete.
- Saving Repository Editor refreshes Check-in/Out, Drop Plate, and Repository
  Sync through the existing configuration bridge.

## Global page

`global_preferences` contains main-window close/tray behavior, bounded server
and local worker counts, diagnostic recording levels, and the read-only
configuration path. Applying worker counts updates the existing pools and the
saved values are used when pools are created on the next launch. Its normalizer,
values callback, and apply callback exclude appearance keys. Search-tab
persistence and server-data caching belong to Cache, not Global.

## Appearance page

`appearance` is a separate sidebar destination using
`ConfigurationAppearancePage.qml`. It contains themes, light/dark palettes,
icons, animation preferences, interface language, and rendering. Existing
`appearance/*` keys in `ui_main/ui_settings` are unchanged; there is no parallel
settings file or migration.

ConfigurationController owns independent session snapshots and drafts for
Global and Appearance. Apply and Reset affect only the current page. Save
applies Appearance before Global so the selected translator is installed before
save notifications. ConfigurationBridge delegates language to LocalizationController
and appearance to ApplicationController; neither apply callback rewrites the
other page's values. `tests/test_configuration_appearance.py` covers independent
apply/reset/discard/save, persistent round trips, and actual sidebar navigation.

Appearance exposes independent click, hover, content-fade, and menu/popup
animation switches. `appearance/popupAnimations` is stored by the existing
application settings owner and projected once into ApplicationController and
Theme; controls never consult configuration storage when opening. Apply changes
the live projection without restart. Popup and ToolTip replace inherited Qt style
transitions with preference-aware transitions, while ProjectChooser and scrims
use popup motion tokens. Process-count menus and Search's tag/quick-filter popups remain instant
regardless of this preference. Tests cover configuration normalization, live QML
form updates, independent theme tokens, and real popup opening/closing under
Qt's Material style (`tests/test_popup_animation_preferences.py`).
Until explicitly saved, popup motion takes its initial value from the existing
content-fade preference so introducing the switch does not re-enable motion for
users who already disabled it. Once saved, the two preferences are independent.

- Appearance settings use the shared theme catalog, including base and accent
  choices, without local colors.
- Click feedback, hover motion, fades/transitions, and popup motion are independent runtime
  preferences stored under `appearance/*Animations`. `ApplicationController`
  reads them with the rest of `ui_main` and exposes cached QObject properties;
  the root `Theme` converts those into duration tokens, so repeated delegates
  never access configuration storage.
- Disabling all four motion preferences makes every decorative transition
  immediate while preserving functional loading indicators and interaction
  states.
- The Rendering card persists `appearance/renderBackend`. The entry point
  applies it before creating `QApplication`; explicit `QSG_RHI_BACKEND` and
  `QT_QUICK_BACKEND` process values remain diagnostic/test overrides. Software
  uses `QT_QUICK_BACKEND=software`; the hardware choices use the RHI backend.
- Automatic rendering selects OpenGL on Windows to avoid the Direct3D 11
  DXGI/MPO/HDR full-display flicker seen on some systems. OpenGL, Direct3D 11,
  Direct3D 12, Vulkan, and Software remain explicit restart-required choices.

## Cache page

The page controls the independently owned persistent server-data domains
defined in `docs/cache_invalidation_policy.md`.

- Projects, Search Types, users, pipelines, processes, statuses, groups, and
  tags are one reference-data domain rather than separate ad-hoc files.
- Search, snapshots/files, relations, tasks, notes, messages, activity, and
  work hours can be enabled independently.
- Apply changes runtime behavior immediately. Disabling a domain advances its
  generation so an older worker cannot repopulate it.
- Clear Cache runs off the UI thread, advances the global generation before
  removing known domain documents, clears change cursors without leaving empty
  placeholder files, and preserves all UI state and drafts.
- Every explicit Refresh action bypasses the matching domain regardless of the
  configured switches.

## Check-in and Check-out settings

The page is divided into semantic sections with a short explanation under each
setting. It may cover:

- result and version presentation;
- explicit-page or continuous search loading;
- Snapshot Browser scope, metadata, content, and orientation defaults;
- item gestures;
- snapshot and naming behavior;
- transfer and checkout methods;
- repository validation and synchronization;
- Drop Plate grouping/matching behavior;
- preview creation;
- check-in confirmation and execution options.
- automatic cleanup of successful Commit Queue operations.

Every displayed setting must use the same key and API as its runtime consumer.
A setting without a working read/write contract must be omitted or clearly
disabled; a visual checkbox backed only by a QML model is not acceptable.

Repository definitions, the default destination, custom paths, and colors
belong to the dedicated Repositories page and Repository Editor rather than
this transfer-settings page.
Changes that require restart or reconnect state this explicitly.

## Task settings

- Initial Quick Tasks or Task Browser surface and the Quick Tasks card or
  compact presentation use the existing `tasks/workspaceSurface` and
  `tasks/quickViewMode` owners.
- Task Browser view, sorting, grouping, Inspector state, and table columns are
  applied together. Every sorting choice shown by the page, including priority,
  milestone, and supervisor, survives normalization.

## Maya Scene page

- Loads work-directory presentation, focus behavior, and the supported scene
  format through `cfg_controls`.
- Maya directory and playblast creation belong only to Check-in Options; the
  Maya page does not keep duplicate controls or a second scene-format setting.
- Save supports only verified formats such as `mayaAscii` and `mayaBinary`.
- Return focus to Maya is enabled by default for successful save, open, import,
  and reference actions. The setting is added to those Maya command payloads by
  `HandlerServerController`; the thin Maya connector owns the native window
  activation.
- Cancel and Reset restore the session snapshot and never call DCC APIs.
- The page does not import Maya modules or execute scene operations.
- Consumption of these settings inside Maya requires DCC acceptance testing.

## Validation and errors

- Invalid input blocks Apply and Save at the page that owns it.
- Worker errors retain full details in Debug Log and expose concise user text.
- A failed page does not silently commit other dependent state.
- Changing page, project, language, or theme cannot discard dirty values.
- Reopening starts a fresh snapshot and never inherits stale dirty state.

## Acceptance

Automated checks cover QML creation, page scrolling, narrow/wide layout,
session reset, close guard, supported persistence paths, and absence of
overlapping controls.

Manual checks cover real server reconnect/authentication, multiple project
types and previews, Repository Editor integration, Maya consumption, Windows
title-bar appearance, and restart-required settings.
