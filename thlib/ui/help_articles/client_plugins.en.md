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

1. Set a new three-part release version, for example **1.0.2**.
2. Click **Build ZIP…**, select the source folder containing `plugin.json`, then
   the output folder. No compiler or separately installed Python is needed.
3. Click **Publish ZIP…**, choose the built archive and confirm the target project.
   Clients fetch this release automatically on their next plugin launch.
4. To roll back, publish a previously built ZIP. Existing release files are kept.

Batch Render sources live in `plugins/batch_render` in the Handler source
checkout. **BUILD_BATCH_PLUGIN.bat** is an alternative builder requiring Python 3.
The dispatcher implementation remains the reviewed VM version. Its original
`stream/batch/dispatcher_runner` group access rules also control plugin launch;
existing legacy buttons and scripts continue using their own original paths.

Packages contain executable desktop Python. Publish trusted code and keep secrets,
settings and tickets outside source packages. Legacy web routes may expose package
source publicly; group launch restrictions are not source-code encryption or a
sandbox. A download/checksum/compatibility error prevents loading the new code.
Actual Maya/Redshift rendering needs separate validation on your workstation.
