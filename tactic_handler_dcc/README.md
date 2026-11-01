# Native DCC connectors

Each connector is a desktop DCC plugin. Handler's **Configuration → DCC plugins**
controls installation-scoped enablement, applied on the next Handler start. The
core builds the graph from enabled manifests only and passes disabled application
ids to its local server, which refuses those registrations. Disabled adapters are
not imported during manifest discovery. Import failures are reported per plugin.
Connector defaults remain enabled for compatibility; disabling never removes
external registrations, custom scripts or server automation records.

An optional `connectors/<module>.plugin.json` contains string fields `application`,
`title`, `description`, and `version`. The module filename is the stable plugin id;
`application` defaults to that id. Metadata is readable while the adapter is
disabled. Add a Python module or package plus the manifest described below to ship
another plugin; no Maya-specific host changes or third-party plugin marketplace
are required. Only trusted local plugin code should be installed.

Optional `ui.configuration.integration` declares `title`, a desktop controller's
`module`/`controller`, relative Configuration QML `view`, and panel `height`. The
Configuration host lazily constructs that controller, parents it and calls its
`shutdown()` during application teardown. Controllers own workers and files;
QML views receive `theme` and `controller`. The Maya plugin uses this contract for
its reversible per-user installation and does not require Maya Python in TH.

Use [`maya.startup(...)`](../docs/dcc_api.md) to connect Maya, then
`tactic_handler_api.get_api()` for the
[unified Handler API](../docs/handler_api.md).

TACTIC data, repository sync and check-in belong to standalone Handler. DCC
connectors execute fixed native actions only.

`runtime.DccRuntime` owns Handler startup, reconnect, hot reload, notifications,
and saved-script execution for every DCC. Copy `_template.py` and
`connectors/_template.py` under the same DCC filename, leave the copied root
module unchanged, then edit only the connector manifest and native methods.
Handler discovers the resulting
manifest automatically and builds item actions, Tools entries, configuration,
action options, focus preferences, and triggers from it. See
[Adding another DCC](../docs/dcc_api.md#adding-another-dcc).
