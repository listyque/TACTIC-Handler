# Windows downloads

[Русский](windows_downloads.ru.md)

[Download Handler](https://github.com/listyque/TACTIC-Handler/releases) for Windows x64.
The Setup EXE includes Python and PySide6. It installs the native application,
`TH Setup.exe` and `TH Setup Builder.exe`; no system Python is needed.
These are unsigned preview builds. Item View is the main workspace; the
Perforce-like File Workspace remains a prototype.

**Clean** is a desktop client for your existing server. Run the installer, open
TH Setup, enter the server URL, sign in and select your project and local repository.
The wizard also configures supported Maya/DCC connectors and the shelf. Apply the
settings, then open `TACTIC Handler.exe`. Install into a writable folder: standalone
Handler stores its local profile in the `TACTIC-Handler` subdirectory.

**Demo** also includes a local TACTIC Stream server with SQLite. The installer opens
Stream first; choose an administrator password and sign in as `admin`. Keep Stream
running, open TH Setup and connect to `http://127.0.0.1:18881` with the same account.
Select Orbit Studio or Atlas Reference Library. The two clients see the same images,
published versions, tasks, users and plugins. Start with ordinary Item View, open
Survey Drone and inspect its tasks and lookdev publications.

Demo data lives in `%APPDATA%\TACTIC Stream Demo\server`; generated artist/reader
passwords are in its `demo-accounts.json`. The bundled Handler profile is in the
adjacent `handler` directory. Clean and demo profiles are separate.
Closing Stream stops the local demo server; Handler can still connect to a different
remote server using another preset.

The [Stream releases](https://github.com/listyque/TACTIC-Stream/releases) also provide
a portable **TH + TS** ZIP, clean or demo, and server-only Windows/Docker/DSM packages.
See the [Windows guide](https://github.com/listyque/TACTIC-Stream/wiki/Windows)
for data directories, isolated instances, build commands and recovery.

Before an update, close both applications and back up profiles and server data.
Handler's installer preserves local settings and repository files, keeps the old
installation in a sibling folder, and refuses to replace modified application files.
A previous program folder is not a database backup. Release notes state what was
checked for that particular build.
