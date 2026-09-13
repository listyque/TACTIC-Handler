# Native DCC connectors

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
