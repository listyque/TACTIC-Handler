# TACTIC-Handler query plugin

This optional TACTIC Team 5.0 package runs the existing
`thlib/tactic_query.py` procedures through a native TACTIC `Command`, without
Mako or changes to TACTIC's XML-RPC implementation. The XML-RPC access log
still names the native `execute_cmd` endpoint; the command title, description,
and errors identify the procedure. The default **Local** mode continues
to send procedure source with each call and requires no server installation.
Nuitka builds bundle procedure source as `.source` package data because
compiled functions do not retain readable Python text. Both Local mode and
plugin deployment use these copies when `.py` files are absent.

Build with `python server_plugin/build_plugin.py`. The output is
`dist/tactic_handler_queries.zip`; inside it, the package directory is
`tactic_handler_queries`. Extract that directory under TACTIC's
`Environment.get_plugin_dir()` (normally
`<TACTIC_DATA>/plugins`). Register the extracted directory as a TACTIC
administrator:

```python
from tactic.command import PluginInstaller
PluginInstaller(relative_dir='tactic_handler_queries', register=True,
                verbose=False).execute()
```

Then select **Server plugin** under
Configuration → Server → Query execution. On the first matching request, an
administrator session uploads and installs this package if it is missing or
out of date. This one-time bootstrap uses `execute_python_script`; normal
procedure calls use the native `execute_cmd` endpoint. Only the three
bootstrap queries (project catalog, project metadata, and initial cache
updates) may fall back to the existing script route if installation fails,
so a stale plugin cannot block sign-in. Other query failures stay visible.
The server package contains only server procedures, not client-side script
builders or legacy examples. The command loader keeps the same module name;
each worker verifies and compiles `api.py` on its first request or when the
client's source hash changes. Matching requests use the already loaded
functions without disk I/O or a lock. The installer invalidates its Python
import cache and native calls retry briefly while other workers discover a
newly installed package. Changes to the stable command loader itself still
require a TACTIC service restart through its process manager; TACTIC's
XML-RPC client API has no general server-restart method. Other custom scripts
keep their current path. The setting is per server address for the
installation, not per login. Installation and native queries were tested on
TACTIC 4.9.0.b02 and TACTIC Team 5.0.

The client and server compare SHA-256 hashes of the bundled server procedures.
On a mismatch, an administrator session deploys the current client package;
non-administrators can still sign in, but must switch to **Local** or ask an
administrator to install the package before using other queries. Selecting
plugin mode authorizes this server-side installation.
