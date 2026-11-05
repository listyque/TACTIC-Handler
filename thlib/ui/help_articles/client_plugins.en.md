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

Click **Refresh** to list plugins. Clicking a row only selects it. Use its
**Launch** button to open the tool; an already running tool offers **Show window**.
The main-window film button and account-menu actions remain direct launch commands.
**Enabled** makes that plugin available for this client and server/project; it
does not launch it. Disabling does not interrupt a running queue.
The list shows the available release and, while open, the running release.
Before launch Handler checks the current server version and your group access.
An open plugin keeps its version; close it and open it again to use an update.
A changed server/account/project does not reuse another context's cache or access.
Keep your session stable while a render queue is running.

Administrators can build and publish releases on the same page:

1. Click **Build plugin package…**. This administrative tool packages plugin
   source code; it is not needed to launch or download an existing plugin.
2. Enter a new three-part plugin version, for example **1.2.1**. The version field
   is in this dialog only; it starts empty. Cancel leaves everything unchanged.
3. Click **Build ZIP**, select the source folder containing `plugin.json`, then
   the output folder. No compiler or separately installed Python is needed.
4. Click **Publish ZIP…**, choose the built archive and confirm the target project.
   Clients fetch this release automatically on their next plugin launch.
5. To roll back, publish a previously built ZIP. Existing release files are kept.

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

**Start … automatically** is a separate checkbox for each plugin.
Only checked, enabled and permitted plugins open after sign-in and project
selection. It does not apply to every installed or enabled plugin. The option
belongs to the current server/project. Batch Render restores its queue paused;
use **Start queue** to render.

Installed code is in **plugins/batch_render** under this client's profile folder.
There are no protocol, server, project or version directories. Reopening checks
server permissions and updates this one folder. A running tool keeps its code;
close it before updating or opening it for another server/project. Settings are
separate: **settings/batch_render.json**, **settings/batch_render_window.json**
and **settings/batch_render_queue.json**. Each file keeps account/server/project
entries inside JSON so another context cannot restore your queue. Version numbers
remain package metadata, not local directory names. Previously installed source
folders are not configuration files and need not be copied to a new client.

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
