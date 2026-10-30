# Sources by product and execution environment

Read only the relevant section. References do not authorize execution. Verify
live capabilities and permissions; historical evidence applies to its baseline.

| Intended work | Owner and entry |
| --- | --- |
| Create a project/template or change persistent project configuration | TS server: [operations](OPERATIONS.md), [API](#ts-server-api), [structures](#ts-server-structures). |
| Automate a running Handler or a standalone script using its session | TH client: [object API and structures](#th-client-api-and-structures). |
| Understand browser behavior or Stream Help | [TS configuration and UI](#ts-configuration-and-ui). |
| Understand native desktop behavior or Handler Help | [TH client references](#th-client-api-and-structures). |
| Work on portable UI descriptions | [Shared Tactic Frame](#shared-tactic-frame); each product retains native controls/transport. |
| Trace original TACTIC semantics | [Original server reference](#original-tactic-server-reference); storage under TH does not make it a client-object schema. |

TH/TS links require sibling checkouts or authorized host retrieval. Report missing
references. Keep credentials and private configuration out of model context.

Existing-project workflows, entity fields and attached files: [EDITING](EDITING.md).

Project page URLs: [TS config/url contract](../custom_urls.md). These are page
addresses, not anonymous API access or agent credentials. Use existing table/layout
definitions; configured REST/Python URL handlers remain unavailable.

External host: [MCP](CONNECTION.md), [Codex setup and acceptance](CODEX.md).

## TS server API

These URLs belong to the selected Stream server: `{server_url}/api/documentation`,
`{server_url}/api/compatibility`, `{server_url}/docs`. Discover one method at a time.
The Python TACTIC SDK is a server client; it is not `tactic_handler_api`.

| Reference | What to read / when |
| --- | --- |
| [API compatibility guide](../../frontend/public/help/api_compatibility.en.md) | Wire formats, native operations, ordinary-account permissions, journals and limitations. Start here for an API integration. |
| [Live reference builder](../../src/tactic_stream/server/documentation.py) | `api_documentation`: how runtime signatures, examples and help are assembled. |
| [Method help](../../src/tactic_stream/compatibility/api_help.json) | Method-specific EN/RU help. |
| [Original method manifest](../../src/tactic_stream/compatibility/api_manifest.json) | Select `methods[method_name]`; captured signatures/status are subordinate to live discovery. |
| [Server API](../../src/tactic_stream/server/api.py) | Relevant `Api` method and dispatch boundary, not the captured manifest text. |
| [HTTP routes](../../src/tactic_stream/server/app.py) | Exact route, allowed fields/actions, authorization and response/error envelope. Editor routes are not all exposed in OpenAPI. |
| [Python SDK](../../src/tactic_client_lib/tactic_server_stub.py) | The chosen client method, argument normalization and result decoding. Raw XML-RPC and SDK return shapes differ. |
| [HTML / server JavaScript](../../frontend/public/help/html_api.en.md) | Existing HTML/JS integration, separate from modern renderer support. |

## TS server structures

Server Search/SObject/Command owns persistent data, permissions and transactions.
Handler wrappers are client objects with different methods and lifetimes.

| Reference | What to read / when |
| --- | --- |
| [Current core model guide](../../frontend/public/help/core_model.en.md) | Server objects, project resolution, pending writes and transactions. |
| [Stream project schema capture](../../src/tactic_stream/compatibility/project_schema.json) | Select a physical `spt_*` table. Initial schema data, not the final upgraded/live schema. |
| [Bootstrap registry](../../src/tactic_stream/compatibility/bootstrap_registry.json) and [bootstrap DDL](../../src/tactic_stream/compatibility/bootstrap.sql) | Initial system definitions; compare upgrades and live registry before designing a new type. |
| [Predefined schema relationships](../../src/tactic_stream/compatibility/predefined_schemas.json) | Select `simple`, `admin`, `config`, etc.; then compare the project's actual resolved schema. |
| [Business upgrades](../../src/tactic_stream/compatibility/business_upgrade.json) and [schema upgrades](../../src/tactic_stream/compatibility/schema_upgrade.json) | Changes after capture; live metadata remains authoritative. |

## TS configuration and UI

| Reference | What to read / when |
| --- | --- |
| [Administration guide](../../frontend/public/help/administration.en.md) | Search Types, Project schema, Workflow, groups/rules and naming subsections. Includes source maps and feature boundaries. |
| [Table view](../../frontend/public/help/table_view.en.md) and [table contract](../frame/table.md) | Column/view operations, typed cells, nested tables and actual migration scope. |
| [Widget reference](../../frontend/public/help/widget_database.en.md), [examples](../../frontend/public/help/table_widget_examples.en.md), [checklist](../../frontend/public/help/table_widget_checklist.en.md) | Handler configuration/examples; historical statuses are not execution guarantees. |
| [Current shared widget catalogue](../../src/tactic_stream/shared_ui/features/table/widgets.json) | Filter by `class`, `value` or `aliases`; inspect `adapter`. Registration alone does not prove every option works. |
| [Actual cell support](../../src/tactic_stream/server/table_cells.py) and [interface resolver](../../src/tactic_stream/server/interface.py) | `describe_cell` / `describe_composition` support for the requested option. |
| [XML configuration operations](../../src/tactic_stream/server/widget_configuration.py) | Source/layer revisions, check/preview/save and conflict handling. |
| [Default configuration XML](../../src/tactic_stream/config/search_type/widget/DEFAULT-conf.xml) and [blank object layout](../../src/tactic_stream/config/layouts/blank.xml) | Default table/object syntax; preserve the project's actual inheritance. |
| [Object layout contract](../../src/tactic_stream/server/item_layout.py) | Bounded widgets/actions/conditions and `describe_item_layout` validation; use for declarative object layouts only. |
| [Sidebar editor](../../frontend/public/help/sidebar_editor.en.md) and [search filters](../../frontend/public/help/search_filters.en.md) | Navigation, default results, nested/saved searches. |

## TS workflows, files and scripts

External model connections and credentials: [PROVIDERS](PROVIDERS.md). TS owns
encrypted profile storage and request authorization; TH owns its native settings
view; the external host owns model inference and tool orchestration.

Stream/server guides; desktop files and DCC require TH capabilities.

| Reference | What to read / when |
| --- | --- |
| [Tasks](../../frontend/public/help/tasks.en.md), [task contract](../frame/tasks.md), [schedule contract](../frame/schedule.md) | Parent/process/status, workspace, dates and scheduling. |
| [Object reports](../../frontend/public/help/sobject_info.en.md) and [object contract](../frame/objects.md) | Parents, reports, forms, links, snapshots and object operations. |
| [Naming command](../../src/tactic/ui/panel/naming_cmd.py) | `FIELDS`, `naming_request`, `preview_naming`: exact rule/sample fields and execution boundary. |
| [Workflow command](../../src/tactic/ui/panel/workflow_cmd.py) | `workflow_request`: XML/process settings, current revision and managed bindings. |
| [Script Editor guide](../../frontend/public/help/script_editor.en.md), [script contract](../frame/scripts.md), [Shelf guide](../../frontend/public/help/script_shelf.en.md) | Languages, context, storage/history and execution differences. |
| [File contract](../frame/files.md), [Commit Queue](../../frontend/public/help/commit_queue.en.md), [repositories](../../frontend/public/help/repositories.en.md) | Upload/check-in ownership, file groups, previews, naming and repository assumptions. |

## Projects, templates and executable evidence

Project/template/plugin operations run on the server, including calls from TH.

| Reference | What to read / when |
| --- | --- |
| [Project creation guide](../../frontend/public/help/project_creation.en.md) | Wizard choices, project modes and template selection. |
| [Project creation command](../../src/tactic/command/create_project_cmd.py) | `check`, `execute`, `create_search_types`: code/type/database bootstrap and rollback boundaries. |
| [Template commands](../../src/tactic/command/project_template_cmd.py) | Installer, exporter, remapped references, actual export scope and unsupported updater. |
| [Plugin commands](../../src/tactic/command/plugin.py) | Manifest/SPT/includes, trusted code, file effects and supported import/export behavior. |
| [CG manifest](../../../cg/manifest.xml), [schema example](../../../cg/sthpw_schema.spt), [view examples](../../../cg/config_widget_config.spt) | Selected template records; SPT is executable input, not passive JSON. |
| [Original VFX manifest](../../../legacy/src/plugins/TACTIC/vfx/manifest.xml) and [Scrum manifest](../../../legacy/src/plugins/TACTIC/scrum/manifest.xml) | Template composition and include paths. Original examples may contain excluded/unsupported elements; inspect the installed configuration. |
| [Transport tests](../../tests/test_transport.py) | `test_*_editor_commands` / `test_schema_editor_command_and_creation_revision`: requests, results, denial/conflict. |
| [Creation lifecycle test](../../tests/test_project_creation.py), [template contract](../../tests/test_schema_template.py), [export contract](../../tests/scripts/template_export_contract.py) | Project rollback, template/schema and export assertions; run only on authorized isolated data. |

## TH client API and structures

Use `tactic_handler_api` for Handler automation, its existing controllers for UI,
and native File/Snapshot methods for desktop files. `get_api()` uses the running
application; submit blocking data work through its documented executor. `local()`
uses configured Handler authentication and needs explicit lifetime cleanup.
Neither a TH handle nor its Python SObject is a server `pyasm.search.SObject`.
A shared search key does not make their APIs or return shapes interchangeable.

| Reference | What to read / when |
| --- | --- |
| [Handler object API](../../../../TH/docs/handler_api.md) | `get_api` / `local`, object tree, background work, handles and files. Client API, not Stream HTTP. |
| [Handler administration contract](../../../../TH/docs/administration.md) | Native editor documents, discovery, schema capabilities, workflow dependencies and concurrency. |
| [Legacy view semantics](../../../../TH/docs/tactic_compatibility/table_views.md) | Definitions, layers, display/edit/action options and lossless XML round trips. Original/Handler contract; check Stream support separately. |
| [Communication contract](../../../../TH/docs/communication_and_feed_contract.md) and [cache policy](../../../../TH/docs/cache_invalidation_policy.md) | Notifications/activity effects and propagation of changes between clients. |
| [TH application architecture](../../../../TH/docs/application_architecture.md) | Native controllers/models, state ownership, worker boundaries and module map. |
| [TH API exports](../../../../TH/tactic_handler_api/__init__.py), [runtime](../../../../TH/tactic_handler_api/api.py), [objects](../../../../TH/tactic_handler_api/objects.py) | `get_api` borrows the running API; `local()` owns a headless session. Query results, pending edits and object lifetimes are client contracts. |
| [TH native objects](../../../../TH/thlib/tactic_classes.py), [queries](../../../../TH/thlib/tactic_query.py), [file API](../../../../TH/tactic_handler_api/files.py) | Native object/path/preview methods and queued transfers; do not reconstruct server paths or call network work on the GUI thread. |
| [TH built-in Help](../../../../TH/thlib/ui/help_articles/README.md), [administration Help](../../../../TH/thlib/ui/help_articles/administration.en.md) | Native `<topic>.<language>.md`, metadata and English fallback; separate from TS Help. |
| [TH integration service](../../../../TH/docs/handler_server_architecture.md) | Local/desktop routing, not the Stream server. DCC/Maya is out of scope. |
| [TH documentation index](../../../../TH/docs/index.md) | Remaining native UI, integration and verification contracts. |

## Shared Tactic Frame

Portable `.mjs` descriptions/state rules have independent copies in TH and TS.
QML and Vue render with their own native controls. Transport, file capabilities,
threading and persistent writes stay with their product owners. Paired UI parity
must be checked; it cannot be inferred from an identical description.

| Reference | What to read / when |
| --- | --- |
| [Shared UI contract](../frame/contract.md), [control catalogue](../frame/control_catalog.md), [source map](../../src/tactic_stream/shared_ui/README.md) | Renderer/control boundaries, not instructions to edit QML/Vue. |

## Original TACTIC server reference

These files reside in TH for reference but describe original TACTIC 5.0 server
schemas, not Handler's in-memory objects or current Stream DDL. Filter catalogues
by the exact table. Compare live registry, upgrades and permissions before use.
Removed `file_access` / `snapshot_type` tables and deprecated `pyasm.prod` paths
are historical. Stream uses `pyasm.biz.ProjectSetting` for `config/prod_setting`.

| Reference | What to read / when |
| --- | --- |
| [Database reference introduction](../../../../TH/docs/tactic_database/README.md) | Original 5.0 scope; custom studio types are not enumerated. Backup examples concern that environment. |
| [Database rules](../../../../TH/docs/tactic_database/01_DATABASE_RULES.md) | Logical types, polymorphic parents, project scope and native write paths. |
| [Core table catalogue](../../../../TH/docs/tactic_database/02_CORE_TABLE_CATALOG.md) | Fields, owning classes and relations for one original table (`task`, `snapshot`, `file`, etc.). |
| [Project config catalogue](../../../../TH/docs/tactic_database/03_CONFIG_TABLE_CATALOG.md) | `spt_widget_config`, `spt_naming`, `spt_process`, scripts, triggers and settings. Includes historical class names. |
| [Relationships and flows](../../../../TH/docs/tactic_database/04_RELATIONSHIPS_AND_FLOWS.md) | Follow the relevant object/task/check-in/workflow flow before designing another relationship. |
| [Write policy matrix](../../../../TH/docs/tactic_database/05_WRITE_POLICY_MATRIX.md) | Which subsystem owns a derived/system record; do not manually fabricate its rows. |
| [Live schema comparison](../../../../TH/docs/tactic_database/06_LIVE_DATABASE_CHECK.md) and [evidence limits](../../../../TH/docs/tactic_database/07_EVIDENCE_AND_LIMITATIONS.md) | Source DDL versus registry/behavior evidence; diagnostic SQL is not a normal write path. |
| [Machine-readable original catalogue](../../../../TH/docs/tactic_database/machine/tactic50_core_tables.json) | Filter by `table`; read `columns`, `relations`, `preferred_write_path`, `confidence`. |
| [Original system DDL](../../../../TH/docs/tactic_database/source_schemas/sthpw_schema.sql) and [config DDL](../../../../TH/docs/tactic_database/source_schemas/config_schema.sql) | Original PostgreSQL field/constraint provenance; not a migration to apply. |

## TS Help, delivery and evidence

- [Native dashboards, project item cards, sidebar editing and MCP](DASHBOARDS_MCP.md): shared bricks,
  read/preview/save receipts, revocable one-project MCP access and its actual limits.

- [TS Help index](../../frontend/public/help/index.json): topic IDs and languages;
  choose one `<id>.en.md` / `<id>.ru.md`. [Russian administration](../../frontend/public/help/administration.ru.md)
  and [Russian core model](../../frontend/public/help/core_model.ru.md) are product help.
  `/ui/help/` contains installed copies, not an additional manual. TH Help has its
  own source and loader, linked above; do not substitute one product's guide for the other.
- [Server](../delivery/SERVER_DELIVERY.en.md), [Windows](../delivery/WINDOWS_DELIVERY.en.md),
  [file-project](../delivery/FILE_PROJECT_DELIVERY.en.md), [recovery](../delivery/RECOVERY_ACCEPTANCE.md):
  installation/upgrade/recovery procedures and their stated acceptance limits.
- [Compatibility](../compatibility.md): scope and behavioral checks. [Original compatibility map](../../../../TH/docs/tactic_compatibility/README.md)
  and [widget contract](../../../../TH/docs/tactic_compatibility/widget_support.md)
  explain original/TH behavior; verify TS support separately.
- [TS architecture](../architecture.md) and [setup](../../README.md) are maintained
  entry points. Agent backlog, old 0.20 handoffs and work journals are local
  workspace material outside both repositories; they are not required context.
