---
group: Configuration
icon: deployed-code
order: 62
---
# Client plugins

Launch **Batch Render** with the film button beside the project selector in the main window. The account menu also lists enabled client tools available to your groups. Launching does not open Configuration; errors appear as notifications. Disabled, denied or unavailable plugins have no launch action.

Open **Configuration -> Client plugins** after signing in and selecting a project.
These tools run in Handler. The project's original TACTIC server stores and
publishes their releases; TACTIC Stream is not required.

Click **Refresh**, then a plugin to open it. **Enabled** controls future launches
for this client and server/project. Disabling does not interrupt a running queue.
The list shows the available release and, while open, the running release.
Before launch Handler checks the current server version and your group access.
An open plugin keeps its version; close it and open it again to use an update.
A changed server/account/project does not reuse another context's cache or access.
Keep your session stable while a render queue is running.

Administrators can build and publish releases on the same page:

1. Set a new three-part release version, for example **1.2.0**.
2. Click **Build ZIP…**, select the source folder containing `plugin.json`, then
   the output folder. No compiler or separately installed Python is needed.
3. Click **Publish ZIP…**, choose the built archive and confirm the target project.
   Clients fetch this release automatically on their next plugin launch.
4. To roll back, publish a previously built ZIP. Existing release files are kept.

Batch Render sources live in `plugins/batch_render` in the Handler source
checkout. **BUILD_BATCH_PLUGIN.bat** is an alternative builder requiring Python 3.
The modular plugin includes a native render queue and its own web control panel. Its original
`stream/batch/dispatcher_runner` group access rules also control plugin launch;
existing legacy buttons and scripts continue using their own original paths.

Packages contain executable desktop Python. Publish trusted code and keep secrets,
settings and tickets outside source packages. Legacy web routes may expose package
source publicly; group launch restrictions are not source-code encryption or a
sandbox. A download/checksum/compatibility error prevents loading the new code.
Actual Maya/Redshift rendering needs separate validation on your workstation.

**Open when Handler starts** opens the enabled plugin automatically after login
and project selection. This option belongs to the current server/project. It
opens Batch Render with the saved queue paused; use **Start queue** to render.

Installed versions are in `plugins/installed/<protocol>/<server>/<project>/<plugin>/<version>`
under this client's settings folder. New server packages use names such as
`th_batch_render-1.2.0`, without checksum folder names. These packages require
Handler 0.6.0.389 or later; older packages still work in this client.

Batch Render's search and status filters update immediately without another
server request. Empty and unfamiliar render statuses are available as filters.
**Web panel** opens its web panel; copy the protected LAN link for another computer.
The render settings select its port and access protection. An occupied port is
reported in the window; close the plugin to stop its web panel. The native
summary uses Tactic Frame; the browser panel remains a separate remote interface.

Adding an episode discovers its shots without changing the server task status or
starting Maya. Click **Start queue** to release staged episodes, even if an older
queue was running when you added them. **Run only this** and **Test render** are
explicit start commands. Restored queues always open paused.

A new profile shows all configured render statuses except **Проверен** and **No
render status**. Saved filter choices are preserved. Shift-click selects a shot
range; Ctrl-click toggles a shot. Ctrl+A selects the current episode's shots,
arrow keys move focus and Shift+arrows extend the range. Space or a selected
shot's checkbox includes/excludes the selection. The episode checkbox changes
all editable shots and shows a mixed state for partial inclusion. Completed,
active and unconfirmed-save shots are protected. Drag the grip to reorder,
including excluded shots. Ordinary selection preserves both lists' scroll.

The native and web panels use the Handler interface language and the same item
heights, previews, indentation and house theme roles. Project titles and statuses
remain unchanged. Selection updates only the changed rows; render output is
coalesced without dropping log events. Close/reopen an already running plugin
for a published update to take effect.
