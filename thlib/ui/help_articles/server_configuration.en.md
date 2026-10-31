---
group: Configuration
icon: dns
order: 30
---
# Server configuration

> Server configuration selects the TACTIC endpoint and connection preset, shows the active account,
> and controls how often shared background requests run.

## Connection

| Setting or action | What it controls |
| --- | --- |
| **Server address** | The TACTIC HTTP endpoint used by the current draft and by **Test**. Changing it does not authenticate an account. |
| **Server preset** | Selects a saved bundle of endpoint, account state, portal site, and proxy routing. |
| **Query execution** | **Local** sends procedure source with each call and needs no server install. **Server plugin** uses a native TACTIC command from a versioned `tactic_handler_queries` package. An administrator session installs missing versions automatically and retries while workers discover the package. If a worker still cannot import it, administrators can explicitly restart a managed Stream server through Administration → Backend server, or use its service manager. If the plugin is unavailable, only the project catalog, project metadata, and initial cache query use the existing script path so sign-in remains possible. Other query failures remain visible. The mode is stored per server address for this installation. Other custom scripts remain local. |
| **Edit presets and routing** | Opens Server Presets without saving the current page. |
| **Current account** | Shows the login attached to the active ticket, or **Not signed in** when no valid account is active. |
| **Test** | Tests the address and routing currently visible on the page. It does not save the draft or request credentials. |
| **Generate ticket** | Applies the server page and opens TACTIC authentication. This is the only server-settings action that asks for a login and password. |

After signing in to another server, Handler checks that the previously selected
project exists there. If it does not, Handler selects an available project from
the new server before loading the workspace.

## Background checks

| Setting | Choices and effect |
| --- | --- |
| **Server updates** | Every 5, 10, 30, or 60 seconds. One batched request checks connectivity, refreshes messages, reactions, activity and task changes, and updates the current user's presence. It updates one `sthpw/message` presence record per user, not an sObject activity log. A shorter interval is more current but sends more requests and presence writes. The connection menu retains **Ping now** for manual diagnosis. |

## Application updates

Set **Update sObject search key** to the full search key of the TACTIC object that receives application release snapshots. Leave it empty to disable checks. Handler checks at startup after sign-in and every 24 hours while running. Each release snapshot must contain a ZIP named with four version numbers (for example `0_5_1_0.zip`); the ZIP must contain the contents of the portable `app` directory, including `launch.py` and `thlib/version.json` with the same version.
Only trusted maintainers should be able to publish snapshots to this object: installing a release runs the code inside its ZIP.

When a newer version appears, choose **Install update** or **Later**. The Update window also lists older release snapshots and previous local installations for manual rollback. Installation downloads and validates the ZIP, closes Handler, swaps the portable `app` directory, keeps local settings and scripts, then restarts. If the new application does not reach its first frame, the installer restores and starts the previous version. Automatic installation is available only in a portable build; it does not modify a source checkout or the bundled Python runtime. New Python dependencies must be installed separately.

Open the full version history through **Application menu → Update**. An
administrator or supervisor can open the release archive generator with
**Ctrl + double-click** on the current version in that window, matching the
legacy maintainer workflow. Regular users can install published updates but
cannot create release archives.

The **Changelog** tab shows the complete history shipped with your installed
version, including while offline. Release notes come from `CHANGELOG.md`, which
is included in update ZIPs. Each completed change increments the final version
number and adds a dated entry. The archive generator starts with the current
version and its changelog notes; rebuilding the same release keeps that version.
Creating an archive requires an entry for the chosen version in `CHANGELOG.md`.

## Server Presets editor

| Field or action | What it does |
| --- | --- |
| **Preset name / Add preset** | Creates a new draft preset under that unique display name. |
| **Active preset** | Identifies the preset currently used by Server configuration. Select another before deleting it. |
| **Delete preset** | Removes the selected non-active draft preset after confirmation. |
| **Server address** | HTTP endpoint stored in this preset. |
| **TACTIC TEAM Mode (local repository)** | For a local TEAM installation that shares the repository with Handler. Entering `http://127.0.0.1:9123` checks it automatically; you can turn it off. While enabled, preview delivery is local, check-in is In-Place, and check-out is Local. The three controls are locked in Check-in Options. Verify both applications use the same repository path before checking in files. |
| **Stored account** | Read-only login state associated with the preset. Sign-in changes only through **Generate ticket**. |
| **Use portal site / Site name** | Routes requests through the named TACTIC portal site when enabled. |
| **Use proxy / Proxy server** | Sends this preset's requests through the configured proxy when enabled. |
| **Proxy login / Proxy password** | Optional credentials used only by that proxy route. |
| **Save** | Writes all preset drafts and returns them to Server configuration. |
| **Cancel** | Closes the editor without writing its drafts. |

The editor never asks for a TACTIC password; return here and use **Generate ticket** to authenticate.
If a monitor is disconnected or its resolution changes, an editor window saved outside the current screen is brought back into view automatically. Your presets and other window positions are not reset.

When TEAM mode is active and you save Repository configuration, Handler asks
separately whether to set TACTIC's server-wide path for the selected default
repository alias to its local path. A TACTIC administrator or supervisor can confirm the server
change. The folder must be accessible to the TACTIC server process. Declining
keeps the server configuration unchanged; if paths differ, In-Place check-ins
will not be visible correctly in TACTIC's web interface. Restart TACTIC if
its web interface still uses the old path after an update.
Use **Sync path** in the Repository editor to repeat this step later without
changing the local repository settings.

If the connection test fails, first verify the scheme (`http://` or `https://`), host and port, then
check portal and proxy values in the selected preset.


## Server push (SSE)

Handler reconnects automatically when an established SSE feed closes or an update response is interrupted; these transport failures do not open an Application error dialog. Every SSE failure is recorded under **communication/server-updates** at **ERROR** level, included in the default Debug Log settings. Details include the request endpoint, server host/port, project, channels, HTTP status, Qt network reason and attempt number; tickets and proxy credentials are excluded. Invalid response formats retain their parser traceback. Authentication expiry still requests sign-in, and permission failures remain visible. Cancelling or replacing a subscription does not report an error.

Choose **Update delivery → Server push (SSE)** in Server configuration or the Connection menu. Periodic checks remain the default, and the interval is shown only in that mode. Apply/Save uses the existing configuration owner; Cancel discards unapplied changes. SSE requires a TACTIC Stream server with `/admin/server-events`; choose polling for other TACTIC installations. Errors do not silently change modes. Tickets/cursors/subscriptions travel in a POST body, never a URL; proxy settings are reused and redirects are not followed with credentials.

Stream's monitored updates process coalesces native commit signals. Qt receives matching type/channel invalidations asynchronously, merges them for 200 ms and allows one native update read at a time. Search Type badges, Task Manager/Inspector and chats subscribe to their data. Closed Messages still receives chat notifications. Activity Feed receives project events while open or notifications are enabled. Project-owned records use their project; chat messages use delivery recipients. Incomplete legacy routing metadata may notify a broader type. Subscriptions are per Search Type, not per object.

Changing project/subscriptions/mode closes the previous stream. Check-in pauses it and resumes afterward. Cursors/drafts remain owned by existing controllers. Failed reads are not queued for replay; reconnect retries use backoff and jitter. Authentication/project access and presence still require a lightweight server check every 20 seconds. Closing Handler stops timers, pending requests and the stream.

The feed is shared on one Stream server; raw SQL bypassing native transactions and exactly-once event delivery are not provided. A lost post-commit signal is repaired by reconnect/manual refresh. Proxy buffering must be disabled. Tests exercise real Qt HTTP, 100 merged invalidations, the actual Handler service against a native Stream fixture, polling regressions and QML configuration. Production Apache/PostgreSQL load and portal/proxy deployments are not certified by those checks.


### SSE verification fixes (Stream 0.112.47 / Handler 0.6.0.20)

Both clients also subscribe to reference data, Script Shelf/widget configuration, custom scripts and trigger definitions. Active searches include connections and status logs, routed by the native row project. Chat recipients from multiple changed messages are merged; chat attachments use the captured message participants when available. No post-commit database read is added. Each new SSE channel explicitly invalidates subscribed types, including startup with a retained cache and no journal cursor. This initial synchronization can reread models when subscriptions change; idle connections remain silent. Web Script Shelf and Script Editor coalesce catalog reloads while busy and preserve unsaved buffers. Other limits above still apply.


Web shelf catalog refresh waits while its editor has unsaved changes, preserving the original save revision and conflict check. Pipeline/schema/search-type metadata invalidates the selected project reference cache; config/process is subscribed as well.


### Update delivery options and open connections

Configuration → Server lets each client choose periodic checks or SSE. In SSE mode, **Update batching delay** combines received invalidations before one data request: 100, 200 (default), 500 or 1000 ms. This is a fixed collection window, not a timer restarted by every event; continuous changes cannot postpone a read indefinitely. A change applies to subsequent windows and keeps pending work. Apply/Save persist it; Cancel discards an unapplied draft. Periodic-check intervals remain separate.

In the Stream web administrator Configuration → Server → Processes and monitoring, **Update collection interval** sets the single server collector and each web worker's feed check interval to 0.1–2 seconds (default 0.5). Save to the native XML and restart the backend. Higher values coalesce more commits; lower values reduce latency. It does not change authentication/presence heartbeats or scan the database. Handler has no server-process configuration editor; use the Stream web configuration for this server-wide setting.

The same administrator page displays **SSE connections** from all web workers: login, project, client, network address, connection time, worker PID and subscribed channels/types. Several rows for the same user are separate open connections (for example browser tabs and Handler). **Refresh connections** updates the snapshot without replacing a settings draft. There is no extra browser polling. Normal disconnects appear within the collection interval; crashed workers expire after 45 seconds. Only authenticated administrators can read this list. Tickets and payloads are never recorded. Proxies may report their address unless the trusted proxy configuration supplies the client address. Client labels are informational, not verified identities. Periodic clients, XML-RPC calls and user presence are not part of this list.

This block completes optional SSE delivery and its controls in both clients. Windows WNS and browser Web Push are separate future integrations; no option pretending to enable them is present. Shared local cache, raw external SQL and the commit-to-marker crash gap remain the documented limits above.


Early disconnects before the first SSE frame (including header-send failure) remove the subscription at the response boundary. Both ASGI disconnect paths are checked. Browser and Handler explicitly label their connections; other callers appear as Unknown client. These labels remain informational.

## Choosing the Handler API transport

In Handler, open **Configuration → Server**, select the connection preset, and choose **API transport**:

- **XML-RPC** is the default for existing and new presets. Use it with Legacy TACTIC or TACTIC Stream.
- **JSON (TACTIC Stream)** uses Stream's `/admin/rpc` endpoint. Update and restart Stream and Handler before enabling it. Legacy TACTIC does not provide this endpoint.

**Test** checks the selected transport, address and draft preset proxy without saving. **Apply** or **Generate ticket** saves the choice in the selected preset, reconnects and opens authentication. **Cancel** discards the draft. **Edit presets and routing** also exposes the transport for each preset; saving one preset does not change another preset's transport. Presets saved before this setting continue using XML-RPC.

The choice covers sign-in, queries, commands and server Python procedures. Binary data and datetimes retain SDK types. File uploads and repository downloads retain their existing HTTP paths. Query execution (**Local / Server plugin**) and update delivery (**Periodic checks / SSE**) remain separate settings.

A failed JSON request is reported without silently switching transport or replaying a write. To connect to Legacy, explicitly choose XML-RPC. Both RPC paths use the same server permissions and request log.

This connection selector belongs to Handler. The Stream browser connects to its own server through JSON and has no Legacy-server transport selector.


## Sign-in and client capabilities

Help and Debug Log remain available before sign-in. Enter submits only a complete login/password pair while no authentication is pending. Handler keeps its existing server presets, ticket generation and proxy/site routing; preset edits are applied through the existing Configuration owner. Stream signs in to the current browser origin and does not expose native server-preset routing. Password entry is cleared when its sign-in window closes.

Handler updates keep the existing release controller, changelog, portable-install eligibility, cancellation and install confirmation. Maintainers retain Ctrl-double-click on the current version to open release creation. The browser does not install native client ZIPs. Connection menus and session expiry retain the existing shell owners; a shared layout never grants permissions or retries an unknown mutation.

## Server processes and restart

Administrators can open **Administration → Backend server** in Handler or Stream.
**Web workers** edits the installation's `services/process_count`; **Running web
workers** shows the ready processes reported by its monitor. Save first, then use
**Restart TACTIC Stream** and confirm the connection interruption. Saving alone
never restarts the server. Refresh reloads saved values; Discard explicitly drops
the draft. Concurrent configuration changes require a reload before restarting.

The existing monitor recreates its workers/listeners using saved configuration;
no remote shell or new launcher is started by the interface. The interface waits
up to 90 seconds for the matching restart to become ready, without resending the
restart command. The endpoint must be managed by a current TacticMonitor and the
account must be an administrator. Explicit startup overrides still take priority.
If network settings changed, open the new address and reconnect. Closing the
interface does not cancel an accepted restart; the short interruption affects
other clients too. Schedule it when no critical operations are in progress.
