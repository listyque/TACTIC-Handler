---
group: Guide
icon: settings
order: 3
---
# Windows setup wizard

Run **TACTIC-Handler-Setup-<version>.exe** on a new or existing workstation. Choose
an empty application folder or an existing TH installation. The installer includes
portable Python and Qt; a separate Python installation is unnecessary. Updating an
existing installation preserves its settings, logs and local scripts and keeps the
previous folder beside it for rollback. Close TH, including its tray icon, first.
The setup bundle is Windows-only; Stream's browser has no local installer counterpart.

You can repeat configuration later with **TH Setup.exe** in the application folder
or the **TACTIC Handler Setup** desktop shortcut. TH must remain closed during setup.
The progress track below the form shows all five steps. Forms remain scrollable,
errors appear beside the current step,
and the review page lists each setting separately before Apply.

1. Enter the server root URL and sign in with your own account. The wizard never
   prefills a login. The standard installer starts with an empty server field; a
   team installer may provide its server default. Back preserves entered
   fields and your project, repository, plugin, Maya and shelf choices for the
   same account/project. Your password stays only in memory until Apply or exit;
   it is not saved. The regular TH profile stores the server-issued ticket.
   Failed credentials, connection/HTTP/certificate failures and project-list
   permissions have separate messages. A credential rejection identifies the
   login/password pair; the server does not identify which one was incorrect.
2. Choose a project, repository alias and a local or network folder. For a new
   configuration, the default is **repo** inside the selected TH installation
   folder. Apply creates it if needed; an existing configured path stays selected.
   Other folders must already exist. Updates preserve the installation's **repo** folder.
   This is a client-side repository mapping. No server repository settings change.
3. Enable the DCC plugins you need. Maya supports automatic discovery and installation
   for Python 3 profiles (2022 or newer). Select its closed versions and a project
   shelf; select **Launcher only** to omit custom script buttons. Other listed DCC
   adapters can be enabled here; their native installation remains manual.
4. Review the settings and choose whether to create desktop shortcuts for TH and
   Setup. Press **Apply**, then **Finish**. Restart Maya before using its integration.

Only the signed-in user's personal shelves and shared shelves are offered. The
button preview excludes missing scripts, unsupported languages and scripts denied
by the user's groups. Permissions are fetched again immediately before applying.
Buttons invoke existing TH entry points; no script bodies are copied or rewritten.
Run Setup again to refresh an installed Maya shelf after a group or shelf change.
TH checks script access again when a saved shelf button is invoked; a local shelf
is not an authorization boundary or a sandbox for arbitrary Python.

Applying uses the same configuration as Configuration → Server, Repository and
DCC plugins. On failure the wizard restores the settings, shortcuts and managed
integration files it touched. Existing foreign or modified Maya integration files
are preserved and reported. Cancel before Apply leaves selected settings unapplied.
No accounts, groups, permissions, schemas or server scripts are changed.

To build a preconfigured team installer without a compiler or external Python,
run **TH Setup Builder.exe** from the application folder. Choose the base
installer (or a previously generated EXE), set the public defaults (server,
project code, installation folder, repository folder name, DCC plugins, default
shelf and desktop shortcuts), and click **Create EXE**. Logins, passwords and
session tickets are never stored in generated installers.
