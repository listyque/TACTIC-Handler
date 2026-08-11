# Modern UI component policy

This policy is enforced for changed QML surfaces in addition to `AGENTS.md`.

- Actions use `Md3Button`, `Md3FilledActionButton`, `CompactIconButton`, or an
  existing domain action button. Icon-only actions are centered by the shared
  control and use a semantic name resolved by `MaterialIcon`.
- Refresh actions use the shared `refresh` icon and the owning controller's
  refresh slot. Loading uses `ContentLoadingOverlay` for blocking content and
  `Md3BusyIndicator` for inline progress.
- User text uses `Md3TextField`/`Md3TextArea`; context menus are supplied by the
  common text controls.
- Dialogs and popups use `Md3Dialog` and `Md3Popup`, with a theme supplied by
  the caller. Standalone windows are registered by `FloatingWindowModel` and
  loaded by the generic `WindowContent` host.
- Responsive content reuses `ResponsiveFlow`, shared sizing policy, and dock
  minimum sizes. Cursor behavior belongs to the reusable interactive control.
- Colors come from the active theme. Source strings are English and translated
  with `qsTr`; project-defined names, processes, statuses, and search types are
  server data and are never translated or hardcoded.

`DockHost` owns only placement/resize/stacking. `DockContentRegistry` owns the
existing dock content components. Its large Results component is the remaining
safe split candidate; moving it is deferred until dedicated Results lifecycle
tests cover selection, paging, tree/card views, and restored tabs.

`ApplicationController` already coordinates domain mixins and independent
controllers. Moving its shared startup state further is deferred because the
authentication, project bootstrap, and search restoration lifecycle currently
cross those owners; splitting it without a lifecycle contract would only move
lines, not responsibility.
