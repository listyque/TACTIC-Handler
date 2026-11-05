# Desktop client plugins on original TACTIC

The desktop loader uses original XML-RPC, `config/plugin`, `PluginInstaller` and
public plugin file routes. It does not import Stream server commands or patch the
server. Server and browser plugins remain separate execution environments.

A release is a native ZIP whose root matches its filename. It contains only
`manifest.xml` and `payload.zip`. The manifest has one `data` node, existing
`type=config` metadata, and a `th_client` JSON value: API version, `targets=["th"]`,
SHA-256, payload size and an optional existing custom-script access path. No
installation Python, SObjects, schema or triggers are allowed in this format.
`payload.zip` contains `entry.py` and client files. Its fixed entry point is
`open_plugin(context)`, returning a native Qt window; context supplies the main
window and explicit project. The package executes trusted administrator code
with the desktop user's OS permissions. It is not a sandbox.

The server's active registry row owns the selected release. Publishing starts
one native transaction before uploading, then invokes the original installer
with registration enabled. Existing non-client plugin codes are protected.
Changed contents require a new version. Old release directories remain available;
republishing an older ZIP selects that release without uninstalling project data.
A failed database transaction can leave an unreferenced release directory; it does
not select that directory for clients. Publication requires server administrator
status. Packaging never imports the client code; Python syntax is checked only.

Each launch rechecks the authenticated project's catalogue and existing group
runner denials. Installation identity includes server and project; no tickets/passwords
are stored in packages or directory names. Payloads are bounded, hashed and validated
before atomic installation; installed sources are verified again before importing.
Different plugin identities/releases have distinct Python module namespaces.
A live native window pins its module and release. A new release takes effect on
its next launch after destruction; disablement blocks future launches and does
not stop an existing queue. Keep the account/project session stable during work.
There is no offline launch that bypasses a fresh permission check.

Legacy plugin files use the existing static web route. They can be publicly
readable according to the host's web configuration: do not package secrets or
assume group launch restrictions make Python source confidential. Publication
and catalogue requests use the current authenticated session; no ticket is sent
to a redirected download host. HTTP transport has the host's normal network
trust limitations; HTTPS is recommended where the server already supports it.

Batch Render has a native main-bar film button beside the project selector. The
account menu also exposes the same permitted/enabled plugin actions. Both routes
use the existing loader, fresh access checks and release lifecycle. Launch errors
are notified without opening Configuration. This desktop-only control has no
browser execution counterpart.

Configuration -> Client plugins is a native desktop integration page. Its
build/publish controls use the installed Python runtime; build selects a source
folder containing `plugin.json`, a release version and an output folder. Sources
for Batch Render live under `plugins/batch_render`. `BUILD_BATCH_PLUGIN.bat` and
`tools/client_plugins.py build --version 1.1.0 --output <folder>` provide the same
builder; the BAT/CLI requires Python 3. The GUI does not need external Python.
Publish a built ZIP from this page while signed into the intended server/project.
The browser has no desktop loader or equivalent execution page in this stage.

Batch Render 1.1.0 is a desktop-only, modular client plugin. Its queue,
Maya process, dependency preparation, catalogue, settings, window and HTTP panel
have separate owners. The window keeps native house controls; its summary uses
Tactic Frame. This is a separate plugin window, with no custom dashboard or TS
browser execution counterpart. The original VM scripts and legacy entry points
remain unchanged; `stream/batch/dispatcher_runner` still controls launch access.

Installed sources live under the client's settings root, for example:
`plugins/installed/http/studio.example_port-80/project-niki_friends/th_batch_render/1.1.0`.
`plugins/batch_render` is the source folder, distinct from installed releases.
New server releases use readable `th_batch_render-1.1.0` directories and ZIP names.
Checksums remain in the manifest and local `.release.json`, not directory names.
API 2 supports these names and QML/MJS/browser assets; Handler still reads API 1
packages for rollback. API 2 packages require Handler 0.6.0.389 or later. Inactive
version directories cannot be overwritten with changed contents. Old hash-named
caches are no longer used; an active old window must be closed before moving or
removing its files.

**Open when Handler starts** is opt-in per plugin/server/project in Configuration
-> Client plugins. After authentication/project restoration, the normal loader
rechecks access and opens each eligible plugin once per application session.
Disabling the plugin blocks automatic launch too. Opening Batch Render restores
the saved queue paused; it never starts restored renders automatically.

Episode discovery loads tasks and prefetched native snapshots in batches, follows
all pages, selects the latest task before filtering and includes taskless/empty
and project-specific statuses. Filter changes and text search apply locally,
including clicks during a refresh. Locally queued episodes remain out of the
catalogue; removing them respects the current filters. Saved explicit empty
filter selections remain empty after reopening.

The globe opens Batch Render's own HTTP panel. Copy LAN link includes the token
when protection is enabled (the default for a new profile). Render settings
control panel enablement, port and secret-link protection; a bind failure is
shown rather than pretending the panel is running. `/api/health` is authenticated
and reports the HTTP service; `/api/state` also checks the Qt controller bridge.
The browser controls this running desktop queue; it is not a server render farm.
Closing the window stops its HTTP listener and releases pending requests.

Verification includes deterministic package/installation tests, actual native QML input,
original legacy Docker installation/download, native dispatcher open, active
release pinning, subsequent launch update and rollback. Rendering real frames,
Maya/Redshift availability and the entire render/check-in queue remain separate
production workflow checks. No production deployment is part of this stage.
