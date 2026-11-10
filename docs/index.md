# TACTIC Handler documentation

GitHub Wiki: [English](https://github.com/listyque/TACTIC-Handler/wiki/Home) · [Русский](https://github.com/listyque/TACTIC-Handler/wiki/Home-ru).

Handler is the native desktop client. Its Python objects, GUI thread, local files,
check-in queue and DCC router are distinct from Stream's server runtime.

The product handbook covers setup, workflows, and operational notes.
[English](handbook.en.md) · [Русский](handbook.ru.md)

Windows Clean/Demo downloads and combined bundles:
[English](windows_downloads.en.md) · [Русский](windows_downloads.ru.md).

## Product presentations

- Visual presentation: [English](../README.md) · [Русский](../README.ru.md).
- Full product and workspace tour: [English](presentations/product-tour.en.md) · [Русский](presentations/product-tour.ru.md).
- Plugin examples — Batch Render and the restored VFX template: [English](presentations/plugins.en.md) · [Русский](presentations/plugins.ru.md).
- Maya plugin and studio shelves: [English](presentations/maya.en.md) · [Русский](presentations/maya.ru.md).
- Built-in project assistant: [English](presentations/assistant.en.md) · [Русский](presentations/assistant.ru.md).
- Custom dashboards: [English](presentations/dashboards.en.md) · [Русский](presentations/dashboards.ru.md).
- Built-in Help: [English](presentations/help.en.md) · [Русский](presentations/help.ru.md).
- Project Knowledge Base: [English](presentations/knowledge-base.en.md) · [Русский](presentations/knowledge-base.ru.md).

## Client APIs and execution

- [Unified Handler API](handler_api.md): client objects, background operations and UI commands.
- [Handler Server](handler_server_architecture.md) and [thin-client protocol](thin_client_protocol.md).
- [DCC API](dcc_api.md): selected native clients and their execution ownership.
- [Cache and invalidation](cache_invalidation_policy.md).
- Product guides: [Script Editor](../thlib/ui/help_articles/script_editor.en.md),
  [triggers](../thlib/ui/help_articles/script_triggers.en.md), [shelf](../thlib/ui/help_articles/script_shelf.en.md).

## Architecture and current contracts

- [Application architecture](application_architecture.md) and [UI behavior](application_ui_explained.md).
- [Component policy](ui_component_policy.md), [component map](ui_component_map.md),
  [user UI contract](user_ui_contract.md), [popups](popup_architecture.md), [localization](qml_localization.md).
- [Search](search_architecture.md), [tasks](tasks_workspace.md), [work hours and costs](work_hours.md).
- [Communication](communication_and_feed_contract.md), [Knowledge Base](knowledge_base.md),
  [Administration](administration.md).
- [QML performance](qml_performance.md) and [performance ownership rules](ui_performance_rules.md).
- [Feature contracts](qml_ui_contracts/) and [shared Frame contracts](frame/index.md).

## Server references: a different owner

- [Original TACTIC database](tactic_database/README.md) documents server tables;
  it does not describe Handler's in-memory Python objects.
- [TACTIC compatibility](tactic_compatibility/README.md) records native client interpretation.
- Stream server APIs, structures, web Help and administrator instructions are owned
  by the separate TS repository. In a paired checkout use its
  [documentation index](../../TS/tactic_stream/docs/index.md).

## Verification and delivery

- [Testing strategy](testing_strategy.md), [vertical workflows](vertical_stabilization.md),
  [isolated test project](tactic_test_project.md).
- [Release readiness](release_readiness.md), [acceptance checklist](release_acceptance_checklist.md).
- File project delivery: [English](file_project_delivery.en.md) / [Russian](file_project_delivery.ru.md).

## File ownership

`thlib` owns the native client; `tactic_handler_api` its public facade;
`handler_server` the local router; `tactic_handler_dcc` native connectors;
`side_tools` reusable installed tools; `tests` and `scripts` verification and tooling.
Product Help remains in `thlib/ui/help_articles` with its EN/RU pairs and viewer.
Do not duplicate that manual in this directory.

Keep maintained engineering documents in English and link new material from this
index or the relevant domain index. Use AGENTS for engineering rules. Backlogs,
handoffs, dated measurements and obsolete plans belong in the workspace's local
`agent-work/` archive, outside Git and release bundles. Settings, scripts written by
users, logs, update payloads and caches are local state, not discarded application source.
