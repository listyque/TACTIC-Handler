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
runner denials. Cache identity includes server and project; no tickets/passwords
are stored in packages or cache names. Payloads are bounded, hashed and validated
before atomic installation; cached sources are verified again before importing.
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

Configuration -> Client plugins is a native desktop integration page. Its
build/publish controls use the installed Python runtime; build selects a source
folder containing `plugin.json`, a release version and an output folder. Sources
for Batch Render live under `plugins/batch_render`. `BUILD_BATCH_PLUGIN.bat` and
`tools/client_plugins.py build --version 1.0.2 --output <folder>` provide the same
builder; the BAT/CLI requires Python 3. The GUI does not need external Python.
Publish a built ZIP from this page while signed into the intended server/project.
The browser has no desktop loader or equivalent execution page in this stage.

The Niki dispatcher body is preserved byte-for-byte from the reviewed VM export
(SHA-256 `15b45a92abb641c66fdd4fd1a4eda7c2fb9c9e0cb694cf8b4d9b20c1a1d5df48`).
Only the package entry wrapper supplies the correct Qt parent. Its existing
`stream/batch/dispatcher_runner` group rules govern plugin launch. Original
legacy scripts, names, argument shapes and business data are retained.

Verification includes deterministic package/cache tests, actual native QML input,
original legacy Docker installation/download, native dispatcher open, active
release pinning, subsequent launch update and rollback. Rendering real frames,
Maya/Redshift availability and the entire render/check-in queue remain separate
production workflow checks. No production deployment is part of this stage.
