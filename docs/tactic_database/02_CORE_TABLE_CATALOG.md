# Core / sthpw Table Catalog
Поля перечислены по PostgreSQL-схемам ветки `5.0`. Отсутствие SQL foreign key не означает отсутствие логической связи.
## DAM/check-in
### `file`

- **Логический search type:** `sthpw/file`
- **Физическое размещение:** `sthpw` DB; таблица `file`
- **Зарегистрированный класс:** `pyasm.biz.file.File`
- **Категория / статус:** `DAM/check-in` / `active core`; уверенность: `high`
- **Назначение:** One tracked physical/logical file belonging to a snapshot.
- **Поля схемы 5.0:** `id`, `file_name`, `search_type`, `search_id`, `timestamp`, `st_size`, `file_range`, `code`, `snapshot_code`, `project_code`, `md5`, `checkin_dir`, `source_path`, `relative_dir`, `type`, `base_type`, `metadata`, `metadata_search`, `repo_type`, `base_dir_alias`
- **Как записывать:** Create/update only through FileCheckin/FileAppendCheckin/Snapshot/file APIs.
- **Политика:** `checkin_api_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** snapshot_code; search_type/search_id; repo/base_dir_alias/relative_dir.
- **Не делать:** Never insert file rows directly: naming, repository paths, snapshot XML, versionless files and triggers must stay consistent.

### `file_access`

- **Логический search type:** `sthpw/file_access`
- **Физическое размещение:** `sthpw` DB; таблица `file_access`
- **Зарегистрированный класс:** `pyasm.biz.FileAccess`
- **Категория / статус:** `DAM/check-in` / `optional/internal`; уверенность: `high`
- **Назначение:** Audit of file access/download by login.
- **Поля схемы 5.0:** `id`, `code`, `file_code`, `login`, `timestamp`
- **Как записывать:** Use FileAccess/file-serving subsystem.
- **Политика:** `subsystem_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** file_code -> file.
- **Не делать:** file_code is legacy-typed; do not repurpose as permissions.

### `remote_repo`

- **Логический search type:** `sthpw/remote_repo`
- **Физическое размещение:** `sthpw` DB; таблица `remote_repo`
- **Зарегистрированный класс:** `pyasm.biz.RemoteRepo`
- **Категория / статус:** `DAM/check-in` / `legacy optional`; уверенность: `medium`
- **Назначение:** Legacy/optional remote repository endpoint mapping.
- **Поля схемы 5.0:** `id`, `code`, `ip_address`, `ip_mask`, `repo_base_dir`, `sandbox_base_dir`, `login`
- **Как записывать:** Use RemoteRepo/repository administration.
- **Политика:** `repository_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login; network masks/paths.
- **Не делать:** Do not confuse with sthpw/repo or modern repo definitions/configuration.

### `repo`

- **Логический search type:** `sthpw/repo`
- **Физическое размещение:** `sthpw` DB; таблица `repo`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `DAM/check-in` / `legacy optional`; уверенность: `medium`
- **Назначение:** Legacy repository handler/path registry.
- **Поля схемы 5.0:** `id`, `code`, `description`, `handler`, `web_dir`, `lib_dir`
- **Как записывать:** Use repository administration/configuration APIs.
- **Политика:** `repository_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** file repo/base alias (logical).
- **Не делать:** Repository configuration may also live outside this table; inspect deployment before relying on it.

### `snapshot`

- **Логический search type:** `sthpw/snapshot`
- **Физическое размещение:** `sthpw` DB; таблица `snapshot`
- **Зарегистрированный класс:** `pyasm.biz.Snapshot`
- **Категория / статус:** `DAM/check-in` / `active core`; уверенность: `high`
- **Назначение:** Version/revision publication attached to an SObject; owns snapshot XML and file set.
- **Поля схемы 5.0:** `id`, `search_type`, `search_id`, `column_name`, `snapshot`, `description`, `process`, `login`, `lock_login`, `timestamp`, `lock_date`, `context`, `version`, `s_status`, `snapshot_type`, `code`, `repo`, `is_current`, `label`, `revision`, `level_type`, `level_id`, `metadata`, `is_latest`, `status`, `project_code`, `search_code`, `is_synced`
- **Как записывать:** Use Snapshot.create and check-in commands, normally FileCheckin/FileAppendCheckin.
- **Политика:** `checkin_api_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** file.snapshot_code; search_type/search_id/search_code; level.
- **Не делать:** Never direct-insert: version allocation, current/latest, files, naming, repository and triggers must be atomic.

### `snapshot_type`

- **Логический search type:** `sthpw/snapshot_type`
- **Физическое размещение:** `sthpw` DB; таблица `snapshot_type`
- **Зарегистрированный класс:** `pyasm.biz.SnapshotType`
- **Категория / статус:** `DAM/check-in` / `active optional`; уверенность: `medium`
- **Назначение:** Snapshot/check-in type configuration and optional pipeline/path flavor.
- **Поля схемы 5.0:** `id`, `code`, `pipeline_code`, `timestamp`, `login`, `s_status`, `relpath`, `project_code`, `subcontext`, `snapshot_flavor`, `relfile`
- **Как записывать:** Use SnapshotType/check-in configuration manager.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** snapshot.snapshot_type; pipeline_code.
- **Не делать:** Legacy/optional in many projects; do not confuse snapshot_type with process/context.

## audit/internal
### `access_log`

- **Логический search type:** нет зарегистрированного search type в консолидированном SQL
- **Физическое размещение:** `sthpw` DB; таблица `access_log`
- **Зарегистрированный класс:** не указан
- **Категория / статус:** `audit/internal` / `internal`; уверенность: `medium`
- **Назначение:** Request/access timing log used by the web/runtime layer.
- **Поля схемы 5.0:** `id`, `code`, `url`, `data`, `start_time`, `end_time`, `duration`
- **Как записывать:** Do not create from application modules; let the request/access logger own it.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** url; start_time/end_time/duration.
- **Не делать:** Not a user activity feed; retention may be short and fields are technical.

### `cache`

- **Логический search type:** `sthpw/cache`
- **Физическое размещение:** `sthpw` DB; таблица `cache`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `audit/internal` / `internal`; уверенность: `high`
- **Назначение:** Small system cache/mtime registry.
- **Поля схемы 5.0:** `id`, `key`, `mtime`
- **Как записывать:** Use the owning cache subsystem.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** key -> cached resource.
- **Не делать:** Never use as application data or durable state.

### `change_timestamp`

- **Логический search type:** нет зарегистрированного search type в консолидированном SQL
- **Физическое размещение:** `sthpw` DB; таблица `change_timestamp`
- **Зарегистрированный класс:** не указан
- **Категория / статус:** `audit/internal` / `active internal`; уверенность: `high`
- **Назначение:** Last-change/index records used to detect modified objects and transactions.
- **Поля схемы 5.0:** `id`, `code`, `search_type`, `search_code`, `changed_on`, `changed_by`, `project_code`, `transaction_code`
- **Как записывать:** Let transaction/commit machinery update it.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type+search_code; transaction_code.
- **Не делать:** Do not use as full audit history; it is an invalidation/change-detection structure.

### `command_log`

- **Логический search type:** `sthpw/command_log`
- **Физическое размещение:** `sthpw` DB; таблица `command_log`
- **Зарегистрированный класс:** `pyasm.command.CommandLog`
- **Категория / статус:** `audit/internal` / `legacy/internal`; уверенность: `high`
- **Назначение:** Historical record of executed TACTIC commands.
- **Поля схемы 5.0:** `id`, `code`, `class_name`, `paramaters`, `login`, `timestamp`
- **Как записывать:** Written by command execution framework.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login; class_name; timestamp.
- **Не делать:** Field name paramaters is legacy; do not build new business logic on it.

### `debug_log`

- **Логический search type:** `sthpw/debug_log`
- **Физическое размещение:** `sthpw` DB; таблица `debug_log`
- **Зарегистрированный класс:** `pyasm.biz.DebugLog`
- **Категория / статус:** `audit/internal` / `active internal`; уверенность: `high`
- **Назначение:** Application debug log with category and level.
- **Поля схемы 5.0:** `id`, `code`, `category`, `level`, `message`, `timestamp`, `login`, `s_status`
- **Как записывать:** Use DebugLog/logger APIs.
- **Политика:** `append_via_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** category; level; login.
- **Не делать:** Not a durable activity/audit feed; can be retired/cleaned.

### `exception_log`

- **Логический search type:** `sthpw/exception_log`
- **Физическое размещение:** `sthpw` DB; таблица `exception_log`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `audit/internal` / `active internal`; уверенность: `high`
- **Назначение:** Unhandled/server exception records.
- **Поля схемы 5.0:** `id`, `class`, `message`, `stack_trace`, `login`, `timestamp`
- **Как записывать:** Written by exception logging framework.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login; class; timestamp.
- **Не делать:** May contain stack traces and sensitive data; admin-only access and retention.

### `retire_log`

- **Логический search type:** `sthpw/retire_log`
- **Физическое размещение:** `sthpw` DB; таблица `retire_log`
- **Зарегистрированный класс:** `pyasm.search.RetireLog`
- **Категория / статус:** `audit/internal` / `active internal`; уверенность: `high`
- **Назначение:** Log of retired SObjects.
- **Поля схемы 5.0:** `id`, `code`, `search_type`, `search_id`, `login`, `timestamp`
- **Как записывать:** Written by retire/delete machinery.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type/search_id.
- **Не делать:** Do not use as the retired object itself or manually append.

### `sobject_log`

- **Логический search type:** `sthpw/sobject_log`
- **Физическое размещение:** `sthpw` DB; таблица `sobject_log`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `audit/internal` / `active internal`; уверенность: `high`
- **Назначение:** Per-SObject index of actions linked to a transaction log.
- **Поля схемы 5.0:** `id`, `code`, `search_type`, `search_id`, `data`, `login`, `timestamp`, `transaction_log_id`
- **Как записывать:** Written by transaction logging.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** transaction_log_id; search_type/search_id.
- **Не делать:** Incomplete by design for some operations/large transactions; do not use as sole source of truth.

### `transaction_log`

- **Логический search type:** `sthpw/transaction_log`
- **Физическое размещение:** `sthpw` DB; таблица `transaction_log`
- **Зарегистрированный класс:** `pyasm.search.TransactionLog`
- **Категория / статус:** `audit/internal` / `active core/internal`; уверенность: `high`
- **Назначение:** Full transaction/command log including XML change payload and undo-related metadata.
- **Поля схемы 5.0:** `id`, `code`, `transaction`, `login`, `timestamp`, `description`, `command`, `title`, `type`, `namespace`
- **Как записывать:** Written by transaction manager.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** sobject_log.transaction_log_id; transaction_code references.
- **Не делать:** Large/sensitive; do not mutate, and do not treat every row as user-facing activity.

### `transaction_state`

- **Логический search type:** `sthpw/transaction_state`
- **Физическое размещение:** `sthpw` DB; таблица `transaction_state`
- **Зарегистрированный класс:** `pyasm.search.TransactionState`
- **Категория / статус:** `audit/internal` / `internal`; уверенность: `high`
- **Назначение:** Temporary XML-RPC/transaction state keyed by ticket.
- **Поля схемы 5.0:** `id`, `ticket`, `timestamp`, `data`
- **Как записывать:** Use transaction/XML-RPC state subsystem.
- **Политика:** `internal_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** ticket.
- **Не делать:** Ephemeral internal state, not user settings.

## bootstrap/meta
### `db_resource`

- **Логический search type:** `sthpw/db_resource`
- **Физическое размещение:** `sthpw` DB; таблица `db_resource`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `bootstrap/meta` / `active admin`; уверенность: `high`
- **Назначение:** Database connection resource used by projects/search types.
- **Поля схемы 5.0:** `id`, `code`, `host`, `port`, `vendor`, `login`, `password`
- **Как записывать:** Use project/database-resource administration APIs.
- **Политика:** `admin_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** project.db_resource; search_object.database.
- **Не делать:** Contains credentials; never expose password to clients or logs.

### `project`

- **Логический search type:** `sthpw/project`
- **Физическое размещение:** `sthpw` DB; таблица `project`
- **Зарегистрированный класс:** `pyasm.biz.Project`
- **Категория / статус:** `bootstrap/meta` / `active core`; уверенность: `high`
- **Назначение:** Registered TACTIC project/template and its DB/naming/runtime metadata.
- **Поля схемы 5.0:** `id`, `code`, `title`, `sobject_mapping_cls`, `dir_naming_cls`, `code_naming_cls`, `pipeline`, `snapshot`, `type`, `last_db_update`, `description`, `initials`, `file_naming_cls`, `reg_hours`, `node_naming_cls`, `s_status`, `status`, `last_version_update`, `palette`, `category`, `is_template`, `db_resource`
- **Как записывать:** Use pyasm.biz.Project/project creation and upgrade tools.
- **Политика:** `project_manager_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** db_resource; search_object database={project}.
- **Не делать:** Creating a row alone does not create the project database, schema, config or permissions.

### `project_type`

- **Логический search type:** `sthpw/project_type`
- **Физическое размещение:** `sthpw` DB; таблица `project_type`
- **Зарегистрированный класс:** `pyasm.biz.ProjectType`
- **Категория / статус:** `bootstrap/meta` / `legacy/extension`; уверенность: `high`
- **Назначение:** Project-type strategy class registry (naming, mapping, repository handlers).
- **Поля схемы 5.0:** `id`, `code`, `dir_naming_cls`, `file_naming_cls`, `code_naming_cls`, `node_naming_cls`, `sobject_mapping_cls`, `s_status`, `type`, `repo_handler_cls`
- **Как записывать:** Use ProjectType/plugin/admin setup APIs.
- **Политика:** `admin_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** project.type.
- **Не делать:** Stores importable class names; invalid values can break project behavior.

### `schema`

- **Логический search type:** `sthpw/schema`
- **Физическое размещение:** `sthpw` DB; таблица `schema`
- **Зарегистрированный класс:** `pyasm.biz.Schema`
- **Категория / статус:** `bootstrap/meta` / `active core`; уверенность: `high`
- **Назначение:** XML project/data-model relationship schema.
- **Поля схемы 5.0:** `id`, `code`, `description`, `schema`, `timestamp`, `login`, `s_status`
- **Как записывать:** Use pyasm.biz.Schema/schema editor and project setup tools.
- **Политика:** `schema_manager_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_object types and relationships.
- **Не делать:** Do not update independently of search types/physical columns; validate XML.

### `search_object`

- **Логический search type:** `sthpw/search_object`
- **Физическое размещение:** `sthpw` DB; таблица `search_object`
- **Зарегистрированный класс:** `pyasm.search.SearchType`
- **Категория / статус:** `bootstrap/meta` / `active core`; уверенность: `high`
- **Назначение:** Search-type registry mapping logical search_type to DB/table/class/schema.
- **Поля схемы 5.0:** `id`, `code`, `search_type`, `namespace`, `description`, `database`, `table_name`, `class_name`, `title`, `schema`, `color`, `id_column`, `default_layout`
- **Как записывать:** Use SearchType/search-type creator and database schema tools.
- **Политика:** `search_type_manager_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** all SObject resolution.
- **Не делать:** A row alone does not create/migrate the physical table or views; class_name is executable configuration.

## configuration
### `custom_property`

- **Логический search type:** `config/custom_property`
- **Физическое размещение:** `sthpw` DB; таблица `custom_property`
- **Зарегистрированный класс:** `pyasm.biz.CustomProperty`
- **Категория / статус:** `configuration` / `active config`; уверенность: `medium`
- **Назначение:** Project-local custom property definitions for a search type.
- **Поля схемы 5.0:** `id`, `code`, `search_type`, `name`, `description`, `login`
- **Как записывать:** Use the custom-property/property manager; generic SObject write is acceptable only if its expected schema is preserved.
- **Политика:** `manager_or_generic`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type; name.
- **Не делать:** This does not itself add a physical DB column in every workflow; coordinate with search-type/schema tools.

### `doc`

- **Логический search type:** `sthpw/doc`
- **Физическое размещение:** `sthpw` DB; таблица `doc`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `configuration` / `optional`; уверенность: `medium`
- **Назначение:** Documentation alias/path registry.
- **Поля схемы 5.0:** `id`, `code`, `alias`, `rel_path`
- **Как записывать:** Use generic SObject APIs or the documentation manager.
- **Политика:** `generic_sobject`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** alias; rel_path.
- **Не делать:** Stores references/paths, not document file contents.

## configuration/triggers
### `trigger`

- **Логический search type:** `sthpw/trigger`
- **Физическое размещение:** `sthpw` DB; таблица `trigger`
- **Зарегистрированный класс:** `pyasm.biz.TriggerSObj`
- **Категория / статус:** `configuration/triggers` / `active compatibility/core`; уверенность: `high`
- **Назначение:** Global/system trigger definition.
- **Поля схемы 5.0:** `id`, `code`, `class_name`, `script_path`, `description`, `event`, `mode`, `project_code`, `s_status`, `process`, `data`
- **Как записывать:** Use TriggerSObj/trigger administration.
- **Политика:** `trigger_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** event/process/project_code.
- **Не делать:** Prefer config/trigger for project-scoped behavior; executable configuration must be secured.

## dispatcher/jobs
### `queue`

- **Логический search type:** `sthpw/queue`
- **Физическое размещение:** `sthpw` DB; таблица `queue`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `dispatcher/jobs` / `active internal`; уверенность: `high`
- **Назначение:** Dispatcher/job queue record.
- **Поля схемы 5.0:** `id`, `code`, `queue`, `priority`, `description`, `state`, `login`, `timestamp`, `command`, `serialized`, `s_status`, `project_code`, `search_id`, `search_type`, `dispatcher_id`, `policy_code`, `host`
- **Как записывать:** Use dispatcher/queue command APIs.
- **Политика:** `owning_subsystem`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** dispatcher_id; policy_code; target search_type/search_id.
- **Не делать:** Do not insert jobs manually unless implementing the dispatcher contract including serialized command and state.

## ingest/watch
### `watch_folder`

- **Логический search type:** `sthpw/watch_folder`
- **Физическое размещение:** `sthpw` DB; таблица `watch_folder`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `ingest/watch` / `active optional`; уверенность: `medium`
- **Назначение:** Watched folder configuration that launches a script/process for incoming files.
- **Поля схемы 5.0:** `id`, `code`, `name`, `project_code`, `base_dir`, `search_type`, `process`, `timestamp`, `script_path`
- **Как записывать:** Use watch-folder/ingest manager.
- **Политика:** `watch_folder_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** project_code+search_type+process.
- **Не делать:** Do not treat as a generic filesystem bookmark; script and service lifecycle matter.

## localization
### `translation`

- **Логический search type:** `sthpw/translation`
- **Физическое размещение:** `sthpw` DB; таблица `translation`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `localization` / `optional`; уверенность: `medium`
- **Назначение:** Global locale msgid/msgstr translation records.
- **Поля схемы 5.0:** `id`, `code`, `language`, `msgid`, `msgstr`, `line`, `login`, `timestamp`
- **Как записывать:** Use localization manager.
- **Политика:** `translation_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** language+msgid.
- **Не делать:** Do not mix with config/translation semantics without deciding global vs project scope.

## messaging
### `message`

- **Логический search type:** `sthpw/message`
- **Физическое размещение:** `sthpw` DB; таблица `message`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `messaging` / `active core`; уверенность: `high`
- **Назначение:** Message channel/container and latest/current message state; used for chat, sobject, script and progress categories.
- **Поля схемы 5.0:** `id`, `code`, `category`, `message`, `status`, `login`, `project_code`, `timestamp`
- **Как записывать:** Use the messaging/chat subsystem; create channel/container through its server command.
- **Политика:** `message_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** message_log.message_code; subscription.message_code.
- **Не делать:** A row is not necessarily one chat message. Do not use it as arbitrary notifications table.

### `message_log`

- **Логический search type:** `sthpw/message_log`
- **Физическое размещение:** `sthpw` DB; таблица `message_log`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `messaging` / `active core`; уверенность: `high`
- **Назначение:** Append-only message entries/history for a message channel.
- **Поля схемы 5.0:** `id`, `code`, `message_code`, `category`, `message`, `status`, `login`, `project_code`, `timestamp`
- **Как записывать:** Use server.log_message / ChatCmd / message logging API.
- **Политика:** `message_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** message_code -> message.
- **Не делать:** Do not direct-insert: channel state, category, subscriptions and polling semantics can diverge.

### `note`

- **Логический search type:** `sthpw/note`
- **Физическое размещение:** `sthpw` DB; таблица `note`
- **Зарегистрированный класс:** `pyasm.biz.Note`
- **Категория / статус:** `messaging` / `active core`; уверенность: `high`
- **Назначение:** Comment/note attached polymorphically to any SObject, optionally by process/context and parent thread.
- **Поля схемы 5.0:** `id`, `code`, `project_code`, `search_type`, `search_id`, `login`, `context`, `timestamp`, `note`, `title`, `parent_id`, `status`, `label`, `process`, `sort_order`, `access`
- **Как записывать:** Use Note.create/add_note APIs.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type/search_id; parent_id; process/context.
- **Не делать:** Do not create a parallel task_comments table; preserve access/private and parent_id semantics.

### `subscription`

- **Логический search type:** `sthpw/subscription`
- **Физическое размещение:** `sthpw` DB; таблица `subscription`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `messaging` / `active core`; уверенность: `high`
- **Назначение:** User subscription/membership to a message channel with last-cleared read cursor.
- **Поля схемы 5.0:** `id`, `code`, `category`, `message_code`, `login`, `project_code`, `status`, `last_cleared`, `timestamp`
- **Как записывать:** Use Subscription/message APIs.
- **Политика:** `message_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** message_code+login.
- **Не делать:** Do not use as universal arbitrary subscription without message_code semantics; last_cleared is a watermark.

## notifications
### `group_notification`

- **Логический search type:** `sthpw/group_notification`
- **Физическое размещение:** `sthpw` DB; таблица `group_notification`
- **Зарегистрированный класс:** `pyasm.biz.GroupNotification`
- **Категория / статус:** `notifications` / `active config`; уверенность: `high`
- **Назначение:** Association between a notification definition and a login group.
- **Поля схемы 5.0:** `id`, `login_group`, `notification_id`
- **Как записывать:** Use GroupNotification/notification administration APIs.
- **Политика:** `notification_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login_group -> notification_id.
- **Не делать:** This is configuration, not an inbox row.

### `notification`

- **Логический search type:** `sthpw/notification`
- **Физическое размещение:** `sthpw` DB; таблица `notification`
- **Зарегистрированный класс:** `pyasm.biz.Notification`
- **Категория / статус:** `notifications` / `active core`; уверенность: `high`
- **Назначение:** Notification definition/rule: event/listen_event, recipients, template and handler configuration.
- **Поля схемы 5.0:** `id`, `code`, `event`, `listen_event`, `data`, `description`, `process`, `type`, `search_type`, `project_code`, `rules`, `subject`, `message`, `email_handler_cls`, `mail_to`, `mail_cc`, `mail_bcc`, `s_status`, `title`, `status`
- **Как записывать:** Use pyasm.biz.Notification / notification manager.
- **Политика:** `notification_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** group_notification; notification_log.
- **Не делать:** Not a per-user inbox item. Do not insert one row per delivered notification.

### `notification_log`

- **Логический search type:** `sthpw/notification_log`
- **Физическое размещение:** `sthpw` DB; таблица `notification_log`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `notifications` / `active internal`; уверенность: `high`
- **Назначение:** Delivery/execution log for generated notifications.
- **Поля схемы 5.0:** `id`, `project_code`, `login`, `command_cls`, `subject`, `message`, `timestamp`
- **Как записывать:** Written by notification subsystem.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** notification_login.notification_log_id.
- **Не делать:** Treat as audit/history; do not use as notification definition.

### `notification_login`

- **Логический search type:** `sthpw/notification_login`
- **Физическое размещение:** `sthpw` DB; таблица `notification_login`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `notifications` / `active internal`; уверенность: `high`
- **Назначение:** Per-login delivery association/status for a notification_log entry.
- **Поля схемы 5.0:** `id`, `notification_log_id`, `login`, `type`, `project_code`, `timestamp`
- **Как записывать:** Written by notification delivery subsystem.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** notification_log_id; login.
- **Не делать:** Not equivalent to chat read receipts.

## organization
### `department`

- **Логический search type:** `sthpw/department`
- **Физическое размещение:** `sthpw` DB; таблица `department`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `organization` / `optional`; уверенность: `medium`
- **Назначение:** Simple department directory.
- **Поля схемы 5.0:** `id`, `code`, `name`, `timestamp`
- **Как записывать:** Generic insert/update through TACTIC API is acceptable.
- **Политика:** `generic_sobject`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login.department (logical).
- **Не делать:** Keep code stable if referenced from login.department or custom logic.

## preferences
### `pref_list`

- **Логический search type:** `sthpw/pref_list`
- **Физическое размещение:** `sthpw` DB; таблица `pref_list`
- **Зарегистрированный класс:** `pyasm.biz.PrefList`
- **Категория / статус:** `preferences` / `optional config`; уверенность: `high`
- **Назначение:** Definition/catalog of available preference keys and options.
- **Поля схемы 5.0:** `id`, `code`, `key`, `description`, `options`, `type`, `category`, `timestamp`, `title`
- **Как записывать:** Use PrefList/preference administration.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** pref_setting.key.
- **Не делать:** Not the user value store; values belong in pref_setting.

### `pref_setting`

- **Логический search type:** `sthpw/pref_setting`
- **Физическое размещение:** `sthpw` DB; таблица `pref_setting`
- **Зарегистрированный класс:** `pyasm.biz.PrefSetting`
- **Категория / статус:** `preferences` / `active core`; уверенность: `high`
- **Назначение:** Per-user/project preference key-value values.
- **Поля схемы 5.0:** `id`, `project_code`, `login`, `key`, `value`, `timestamp`
- **Как записывать:** Use PrefSetting APIs.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login+project_code+key.
- **Не делать:** Namespace keys; do not store security- or workflow-authoritative state.

### `wdg_settings`

- **Логический search type:** `sthpw/wdg_settings`
- **Физическое размещение:** `sthpw` DB; таблица `wdg_settings`
- **Зарегистрированный класс:** `pyasm.web.WidgetSettings`
- **Категория / статус:** `preferences` / `active core`; уверенность: `high`
- **Назначение:** Persistent per-user widget state.
- **Поля схемы 5.0:** `id`, `key`, `login`, `data`, `timestamp`, `project_code`
- **Как записывать:** Use WidgetSettings.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login+project_code+key.
- **Не делать:** UI-only state; namespace keys and avoid authoritative business data.

## relationships
### `connection`

- **Логический search type:** `sthpw/connection`
- **Физическое размещение:** `sthpw` DB; таблица `connection`
- **Зарегистрированный класс:** `pyasm.biz.SObjectConnection`
- **Категория / статус:** `relationships` / `active core`; уверенность: `high`
- **Назначение:** Generic directed relationship between two arbitrary SObjects with a context.
- **Поля схемы 5.0:** `id`, `code`, `context`, `project_code`, `src_search_type`, `src_search_id`, `dst_search_type`, `dst_search_id`, `login`, `timestamp`
- **Как записывать:** Use SObjectConnection / server.connect_sobjects and disconnect APIs.
- **Политика:** `subsystem_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** src_search_type/src_search_id -> dst_search_type/dst_search_id; context.
- **Не делать:** Never hand-insert without resolving source/destination identity; modern deployments may add search_code columns.

## scheduling
### `special_day`

- **Логический search type:** нет зарегистрированного search type в консолидированном SQL
- **Физическое размещение:** `sthpw` DB; таблица `special_day`
- **Зарегистрированный класс:** не указан
- **Категория / статус:** `scheduling` / `optional legacy`; уверенность: `medium`
- **Назначение:** Calendar/work-schedule exception or special-day configuration.
- **Поля схемы 5.0:** `id`, `code`, `week`, `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`, `year`, `login`, `description`, `type`, `project_code`
- **Как записывать:** Use scheduling/calendar APIs; generic write only if contract is understood.
- **Политика:** `generic_or_schedule_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** project_code/login/year/week.
- **Не делать:** Fields are legacy weekly/hour values; verify feature before extending.

## search/index
### `sobject_list`

- **Логический search type:** `sthpw/sobject_list`
- **Физическое размещение:** `sthpw` DB; таблица `sobject_list`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `search/index` / `internal/optional`; уверенность: `medium`
- **Назначение:** Auxiliary indexed/list representation of SObject references and keywords.
- **Поля схемы 5.0:** `id`, `code`, `search_type`, `search_id`, `keywords`, `timestamp`, `project_code`
- **Как записывать:** Let indexing/search-list subsystem maintain it.
- **Политика:** `owning_subsystem`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type/search_id.
- **Не делать:** Not a business collection or relation table.

## security/users
### `login`

- **Логический search type:** `sthpw/login`
- **Физическое размещение:** `sthpw` DB; таблица `login`
- **Зарегистрированный класс:** `pyasm.security.Login`
- **Категория / статус:** `security/users` / `active core`; уверенность: `high`
- **Назначение:** User/account record and profile.
- **Поля схемы 5.0:** `id`, `code`, `login`, `password`, `upn`, `login_groups`, `first_name`, `last_name`, `display_name`, `email`, `phone_number`, `department`, `namespace`, `snapshot`, `s_status`, `project_code`, `license_type`, `hourly_wage`, `data`
- **Как записывать:** Use pyasm.security.Login, password/authentication and user-management APIs.
- **Политика:** `security_api_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login_in_group; ticket; task.assigned; note.login.
- **Не делать:** Never write password directly; preserve external-auth/UPN/status semantics.

### `login_group`

- **Логический search type:** `sthpw/login_group`
- **Физическое размещение:** `sthpw` DB; таблица `login_group`
- **Зарегистрированный класс:** `pyasm.security.LoginGroup`
- **Категория / статус:** `security/users` / `active core`; уверенность: `high`
- **Назначение:** Security group with XML access_rules and project/default metadata.
- **Поля схемы 5.0:** `id`, `code`, `login_group`, `name`, `sub_groups`, `access_rules`, `redirect_url`, `namespace`, `description`, `project_code`, `s_status`, `start_link`, `access_level`, `is_default`, `data`
- **Как записывать:** Use LoginGroup/Security Manager APIs.
- **Политика:** `security_api_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login_in_group; group_notification.
- **Не делать:** Do not treat group name as authorization; effective access is computed by AccessManager.

### `login_in_group`

- **Логический search type:** `sthpw/login_in_group`
- **Физическое размещение:** `sthpw` DB; таблица `login_in_group`
- **Зарегистрированный класс:** `pyasm.security.LoginInGroup`
- **Категория / статус:** `security/users` / `active core`; уверенность: `high`
- **Назначение:** Membership link between login and login_group.
- **Поля схемы 5.0:** `id`, `code`, `login`, `login_group`
- **Как записывать:** Use Login.add_to_group/remove_from_group or group membership APIs.
- **Политика:** `security_api_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login -> login_group.
- **Не делать:** Avoid duplicates; changes affect effective security and caches.

### `ticket`

- **Логический search type:** `sthpw/ticket`
- **Физическое размещение:** `sthpw` DB; таблица `ticket`
- **Зарегистрированный класс:** `pyasm.security.Ticket`
- **Категория / статус:** `security/users` / `active core`; уверенность: `high`
- **Назначение:** Authentication/session ticket with expiry/category.
- **Поля схемы 5.0:** `id`, `code`, `ticket`, `login`, `timestamp`, `expiry`, `category`
- **Как записывать:** Use Ticket/authentication/session APIs.
- **Политика:** `security_api_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login.
- **Не делать:** Never mint or update tickets directly from clients.

## sync
### `sync_job`

- **Логический search type:** `sthpw/sync_job`
- **Физическое размещение:** `sthpw` DB; таблица `sync_job`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `sync` / `active optional`; уверенность: `high`
- **Назначение:** Outgoing/incoming remote synchronization job.
- **Поля схемы 5.0:** `id`, `code`, `login`, `timestamp`, `command`, `data`, `state`, `host`, `project_code`, `error_log`, `server_code`, `transaction_code`
- **Как записывать:** Use synchronization engine.
- **Политика:** `sync_engine_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** sync_server/server_code; transaction_code.
- **Не делать:** Command/data/state and transaction linkage are engine contracts.

### `sync_log`

- **Логический search type:** `sthpw/sync_log`
- **Физическое размещение:** `sthpw` DB; таблица `sync_log`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `sync` / `active optional`; уверенность: `high`
- **Назначение:** Processed synchronization transaction/result log.
- **Поля схемы 5.0:** `id`, `code`, `transaction_code`, `status`, `error`, `login`, `timestamp`, `project_code`
- **Как записывать:** Written by sync engine.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** transaction_code; project_code.
- **Не делать:** Do not retry by editing rows; use sync job/recovery APIs.

### `sync_server`

- **Логический search type:** `sthpw/sync_server`
- **Физическое размещение:** `sthpw` DB; таблица `sync_server`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `sync` / `active optional`; уверенность: `high`
- **Назначение:** Remote TACTIC synchronization peer and credentials/rules.
- **Поля схемы 5.0:** `id`, `code`, `host`, `login`, `timestamp`, `state`, `ticket`, `access_rules`, `description`, `sync_mode`, `base_dir`, `file_mode`
- **Как записывать:** Use sync-server administration.
- **Политика:** `sync_admin`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** sync_job.server_code.
- **Не делать:** Contains ticket/access rules and connectivity data; protect as secret config.

## time tracking
### `work_hour`

- **Логический search type:** `sthpw/work_hour`
- **Физическое размещение:** `sthpw` DB; таблица `work_hour`
- **Зарегистрированный класс:** `pyasm.biz.WorkHour`
- **Категория / статус:** `time tracking` / `active optional`; уверенность: `high`
- **Назначение:** Time/work-hour entry linked to an SObject/task/process.
- **Поля схемы 5.0:** `id`, `code`, `project_code`, `description`, `category`, `process`, `login`, `day`, `start_time`, `end_time`, `straight_time`, `over_time`, `search_type`, `search_id`, `status`, `task_code`
- **Как записывать:** Use WorkHour/timecard APIs.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type/search_id; task_code; login.
- **Не делать:** Durations, dates and task linkage may drive reports/payroll; validate rather than ad-hoc insert.

## user productivity
### `clipboard`

- **Логический search type:** `sthpw/clipboard`
- **Физическое размещение:** `sthpw` DB; таблица `clipboard`
- **Зарегистрированный класс:** `pyasm.biz.Clipboard`
- **Категория / статус:** `user productivity` / `active optional`; уверенность: `high`
- **Назначение:** Server-side user clipboard entries referencing arbitrary SObjects.
- **Поля схемы 5.0:** `id`, `project_code`, `login`, `search_type`, `search_id`, `timestamp`, `category`
- **Как записывать:** Use pyasm.biz.Clipboard or existing clipboard server APIs.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login + search_type/search_id.
- **Не делать:** Do not duplicate object data; store only the reference and category.

### `interaction`

- **Логический search type:** `sthpw/interaction`
- **Физическое размещение:** `sthpw` DB; таблица `interaction`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `user productivity` / `optional/internal`; уверенность: `medium`
- **Назначение:** Generic per-user interaction/state store keyed by a string.
- **Поля схемы 5.0:** `id`, `code`, `project_code`, `login`, `key`, `data`, `timestamp`
- **Как записывать:** Use only through the feature that defines the key/data contract.
- **Политика:** `owning_subsystem`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** login+project_code+key.
- **Не делать:** Do not turn it into an unversioned dumping ground; namespace keys.

## workflow
### `pipeline`

- **Логический search type:** `sthpw/pipeline`
- **Физическое размещение:** `sthpw` DB; таблица `pipeline`
- **Зарегистрированный класс:** `pyasm.biz.Pipeline`
- **Категория / статус:** `workflow` / `active compatibility/core`; уверенность: `high`
- **Назначение:** Global/system pipeline XML and metadata; historically the primary Pipeline table.
- **Поля схемы 5.0:** `id`, `code`, `pipeline`, `timestamp`, `search_type`, `project_code`, `description`, `color`, `s_status`, `autocreate_tasks`, `use_workflow`
- **Как записывать:** Use pyasm.biz.Pipeline and pipeline editor/synchronization routines.
- **Политика:** `pipeline_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** task.pipeline_code; config/process.pipeline_code.
- **Не делать:** Do not edit XML and related process rows independently; config/pipeline also exists in project DBs.

## workflow/tasks
### `milestone`

- **Логический search type:** `sthpw/milestone`
- **Физическое размещение:** `sthpw` DB; таблица `milestone`
- **Зарегистрированный класс:** `pyasm.biz.Milestone`
- **Категория / статус:** `workflow/tasks` / `active optional`; уверенность: `high`
- **Назначение:** Project milestone/due-date object.
- **Поля схемы 5.0:** `id`, `code`, `project_code`, `description`, `due_date`
- **Как записывать:** Use pyasm.biz.Milestone or generic SObject APIs when no extra behavior is needed.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** task.milestone_code.
- **Не делать:** Tasks reference milestone_code logically.

### `status_log`

- **Логический search type:** `sthpw/status_log`
- **Физическое размещение:** `sthpw` DB; таблица `status_log`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `workflow/tasks` / `active core`; уверенность: `high`
- **Назначение:** Append-only status transition history for an SObject, commonly task.
- **Поля схемы 5.0:** `id`, `search_type`, `search_id`, `status`, `login`, `timestamp`, `to_status`, `from_status`, `project_code`
- **Как записывать:** Let Task/status-change/trigger machinery append it.
- **Политика:** `read_only_system`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type/search_id; from_status/to_status.
- **Не делать:** Do not update old rows or use as current status; current value lives on the target object/task.

### `task`

- **Логический search type:** `sthpw/task`
- **Физическое размещение:** `sthpw` DB; таблица `task`
- **Зарегистрированный класс:** `pyasm.biz.Task`
- **Категория / статус:** `workflow/tasks` / `active core`; уверенность: `high`
- **Назначение:** Concrete work item for one target SObject and process.
- **Поля схемы 5.0:** `id`, `assigned`, `description`, `status`, `discussion`, `bid_start_date`, `bid_end_date`, `bid_duration`, `actual_start_date`, `actual_end_date`, `search_type`, `search_id`, `timestamp`, `s_status`, `priority`, `process`, `context`, `milestone_code`, `pipeline_code`, `parent_id`, `sort_order`, `depend_id`, `project_code`, `supervisor`, `code`, `login`, `completion`
- **Как записывать:** Use Task.create/task APIs and status methods.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type/search_id; pipeline_code/process; milestone/dependency.
- **Не делать:** Do not create a parallel task table; preserve search target, process, pipeline, assignee and status triggers.

