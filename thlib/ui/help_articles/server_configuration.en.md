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
| **Edit presets and routing** | Opens Server Presets without saving the current page. |
| **Current account** | Shows the login attached to the active ticket, or **Not signed in** when no valid account is active. |
| **Test** | Tests the address and routing currently visible on the page. It does not save the draft or request credentials. |
| **Generate ticket** | Applies the server page and opens TACTIC authentication. This is the only server-settings action that asks for a login and password. |

## Background checks

| Setting | Choices and effect |
| --- | --- |
| **Connection ping** | **Off**, every 10 seconds, or every 60 seconds. It only checks whether the endpoint remains reachable. |
| **Server updates** | Every 5, 10, 30, or 60 seconds. One batched request refreshes messages, reactions, activity, and task changes. A shorter interval is more current but sends more requests. |
| **Presence heartbeat** | Every 30, 60, 120, or 300 seconds. It keeps the current user's online status reliable and cannot be disabled. |

## Server Presets editor

| Field or action | What it does |
| --- | --- |
| **Preset name / Add preset** | Creates a new draft preset under that unique display name. |
| **Active preset** | Identifies the preset currently used by Server configuration. Select another before deleting it. |
| **Delete preset** | Removes the selected non-active draft preset after confirmation. |
| **Server address** | HTTP endpoint stored in this preset. |
| **Stored account** | Read-only login state associated with the preset. Sign-in changes only through **Generate ticket**. |
| **Use portal site / Site name** | Routes requests through the named TACTIC portal site when enabled. |
| **Use proxy / Proxy server** | Sends this preset's requests through the configured proxy when enabled. |
| **Proxy login / Proxy password** | Optional credentials used only by that proxy route. |
| **Save** | Writes all preset drafts and returns them to Server configuration. |
| **Cancel** | Closes the editor without writing its drafts. |

The editor never asks for a TACTIC password; return here and use **Generate ticket** to authenticate.

If the connection test fails, first verify the scheme (`http://` or `https://`), host and port, then
check portal and proxy values in the selected preset.
