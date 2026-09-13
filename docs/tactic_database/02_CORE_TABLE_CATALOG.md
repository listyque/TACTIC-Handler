# Core / sthpw Table Catalog
Fields are listed from the PostgreSQL schemas of the `5.0`. The absence of a SQL foreign key does not imply the absence of a logical relationship.
## DAM/check-in
### `file`

- **Logical search type:** `sthpw/file`
- **Physical location:** `sthpw` DB; table `file`
- **Registered class:** `pyasm.biz.file.File`
- **Category / status:** `DAM/check-in` / `active core`; confidence: `high`
- **Purpose:** One tracked physical/logical file belonging to a snapshot.
- **5.0 schema fields:** `id`, `file_name`, `search_type`, `search_id`, `timestamp`, `st_size`, `file_range`, `code`, `snapshot_code`, `project_code`, `md5`, `checkin_dir`, `source_path`, `relative_dir`, `type`, `base_type`, `metadata`, `metadata_search`, `repo_type`, `base_dir_alias`
- **Write path:** Create/update only through FileCheckin/FileAppendCheckin/Snapshot/file APIs.
- **Policy:** `checkin_api_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** snapshot_code; search_type/search_id; repo/base_dir_alias/relative_dir.
- **Do not:** Never insert file rows directly: naming, repository paths, snapshot XML, versionless files and triggers must stay consistent.

### `file_access`

- **Logical search type:** `sthpw/file_access`
- **Physical location:** `sthpw` DB; table `file_access`
- **Registered class:** `pyasm.biz.FileAccess`
- **Category / status:** `DAM/check-in` / `optional/internal`; confidence: `high`
- **Purpose:** Audit of file access/download by login.
- **5.0 schema fields:** `id`, `code`, `file_code`, `login`, `timestamp`
- **Write path:** Use FileAccess/file-serving subsystem.
- **Policy:** `subsystem_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** file_code -> file.
- **Do not:** file_code is legacy-typed; do not repurpose as permissions.

### `remote_repo`

- **Logical search type:** `sthpw/remote_repo`
- **Physical location:** `sthpw` DB; table `remote_repo`
- **Registered class:** `pyasm.biz.RemoteRepo`
- **Category / status:** `DAM/check-in` / `legacy optional`; confidence: `medium`
- **Purpose:** Legacy/optional remote repository endpoint mapping.
- **5.0 schema fields:** `id`, `code`, `ip_address`, `ip_mask`, `repo_base_dir`, `sandbox_base_dir`, `login`
- **Write path:** Use RemoteRepo/repository administration.
- **Policy:** `repository_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login; network masks/paths.
- **Do not:** Do not confuse with sthpw/repo or modern repo definitions/configuration.

### `repo`

- **Logical search type:** `sthpw/repo`
- **Physical location:** `sthpw` DB; table `repo`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `DAM/check-in` / `legacy optional`; confidence: `medium`
- **Purpose:** Legacy repository handler/path registry.
- **5.0 schema fields:** `id`, `code`, `description`, `handler`, `web_dir`, `lib_dir`
- **Write path:** Use repository administration/configuration APIs.
- **Policy:** `repository_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** file repo/base alias (logical).
- **Do not:** Repository configuration may also live outside this table; inspect deployment before relying on it.

### `snapshot`

- **Logical search type:** `sthpw/snapshot`
- **Physical location:** `sthpw` DB; table `snapshot`
- **Registered class:** `pyasm.biz.Snapshot`
- **Category / status:** `DAM/check-in` / `active core`; confidence: `high`
- **Purpose:** Version/revision publication attached to an SObject; owns snapshot XML and file set.
- **5.0 schema fields:** `id`, `search_type`, `search_id`, `column_name`, `snapshot`, `description`, `process`, `login`, `lock_login`, `timestamp`, `lock_date`, `context`, `version`, `s_status`, `snapshot_type`, `code`, `repo`, `is_current`, `label`, `revision`, `level_type`, `level_id`, `metadata`, `is_latest`, `status`, `project_code`, `search_code`, `is_synced`
- **Write path:** Use Snapshot.create and check-in commands, normally FileCheckin/FileAppendCheckin.
- **Policy:** `checkin_api_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** file.snapshot_code; search_type/search_id/search_code; level.
- **Do not:** Never direct-insert: version allocation, current/latest, files, naming, repository and triggers must be atomic.

### `snapshot_type`

- **Logical search type:** `sthpw/snapshot_type`
- **Physical location:** `sthpw` DB; table `snapshot_type`
- **Registered class:** `pyasm.biz.SnapshotType`
- **Category / status:** `DAM/check-in` / `active optional`; confidence: `medium`
- **Purpose:** Snapshot/check-in type configuration and optional pipeline/path flavor.
- **5.0 schema fields:** `id`, `code`, `pipeline_code`, `timestamp`, `login`, `s_status`, `relpath`, `project_code`, `subcontext`, `snapshot_flavor`, `relfile`
- **Write path:** Use SnapshotType/check-in configuration manager.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** snapshot.snapshot_type; pipeline_code.
- **Do not:** Legacy/optional in many projects; do not confuse snapshot_type with process/context.

## audit/internal
### `access_log`

- **Logical search type:** no search type is registered in the consolidated SQL
- **Physical location:** `sthpw` DB; table `access_log`
- **Registered class:** not specified
- **Category / status:** `audit/internal` / `internal`; confidence: `medium`
- **Purpose:** Request/access timing log used by the web/runtime layer.
- **5.0 schema fields:** `id`, `code`, `url`, `data`, `start_time`, `end_time`, `duration`
- **Write path:** Do not create from application modules; let the request/access logger own it.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** url; start_time/end_time/duration.
- **Do not:** Not a user activity feed; retention may be short and fields are technical.

### `cache`

- **Logical search type:** `sthpw/cache`
- **Physical location:** `sthpw` DB; table `cache`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `audit/internal` / `internal`; confidence: `high`
- **Purpose:** Small system cache/mtime registry.
- **5.0 schema fields:** `id`, `key`, `mtime`
- **Write path:** Use the owning cache subsystem.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** key -> cached resource.
- **Do not:** Never use as application data or durable state.

### `change_timestamp`

- **Logical search type:** no search type is registered in the consolidated SQL
- **Physical location:** `sthpw` DB; table `change_timestamp`
- **Registered class:** not specified
- **Category / status:** `audit/internal` / `active internal`; confidence: `high`
- **Purpose:** Last-change/index records used to detect modified objects and transactions.
- **5.0 schema fields:** `id`, `code`, `search_type`, `search_code`, `changed_on`, `changed_by`, `project_code`, `transaction_code`; current 5.0 upgrades also add indexed `timestamp`
- **Write path:** Let transaction/commit machinery update it.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type+search_code; transaction_code. `changed_on` and `changed_by` are JSON maps keyed by column; `timestamp` is the row time.
- **Do not:** Do not use as full audit history or treat `changed_on`/`changed_by` as scalar columns; it is an invalidation/change-detection structure containing only the latest change state per object.

### `command_log`

- **Logical search type:** `sthpw/command_log`
- **Physical location:** `sthpw` DB; table `command_log`
- **Registered class:** `pyasm.command.CommandLog`
- **Category / status:** `audit/internal` / `legacy/internal`; confidence: `high`
- **Purpose:** Historical record of executed TACTIC commands.
- **5.0 schema fields:** `id`, `code`, `class_name`, `paramaters`, `login`, `timestamp`
- **Write path:** Written by command execution framework.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login; class_name; timestamp.
- **Do not:** Field name paramaters is legacy; do not build new business logic on it.

### `debug_log`

- **Logical search type:** `sthpw/debug_log`
- **Physical location:** `sthpw` DB; table `debug_log`
- **Registered class:** `pyasm.biz.DebugLog`
- **Category / status:** `audit/internal` / `active internal`; confidence: `high`
- **Purpose:** Application debug log with category and level.
- **5.0 schema fields:** `id`, `code`, `category`, `level`, `message`, `timestamp`, `login`, `s_status`
- **Write path:** Use DebugLog/logger APIs.
- **Policy:** `append_via_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** category; level; login.
- **Do not:** Not a durable activity/audit feed; can be retired/cleaned.

### `exception_log`

- **Logical search type:** `sthpw/exception_log`
- **Physical location:** `sthpw` DB; table `exception_log`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `audit/internal` / `active internal`; confidence: `high`
- **Purpose:** Unhandled/server exception records.
- **5.0 schema fields:** `id`, `class`, `message`, `stack_trace`, `login`, `timestamp`
- **Write path:** Written by exception logging framework.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login; class; timestamp.
- **Do not:** May contain stack traces and sensitive data; admin-only access and retention.

### `retire_log`

- **Logical search type:** `sthpw/retire_log`
- **Physical location:** `sthpw` DB; table `retire_log`
- **Registered class:** `pyasm.search.RetireLog`
- **Category / status:** `audit/internal` / `active internal`; confidence: `high`
- **Purpose:** Log of retired SObjects.
- **5.0 schema fields:** `id`, `code`, `search_type`, `search_id`, `login`, `timestamp`
- **Write path:** Written by retire/delete machinery.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type/search_id.
- **Do not:** Do not use as the retired object itself or manually append.

### `sobject_log`

- **Logical search type:** `sthpw/sobject_log`
- **Physical location:** `sthpw` DB; table `sobject_log`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `audit/internal` / `active internal`; confidence: `high`
- **Purpose:** Per-SObject index of actions linked to a transaction log.
- **5.0 schema fields:** `id`, `code`, `search_type`, `search_id`, `data`, `login`, `timestamp`, `transaction_log_id`; current 5.0 upgrades also add `parent_type`, `parent_code`, and `action`
- **Write path:** Written by transaction logging.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** transaction_log_id; search_type/search_id.
- **Do not:** Incomplete by design: delete mutations are omitted and per-object rows are not generated for transactions whose uncompressed XML exceeds 10 KiB. Do not use it as the sole source of truth.

### `transaction_log`

- **Logical search type:** `sthpw/transaction_log`
- **Physical location:** `sthpw` DB; table `transaction_log`
- **Registered class:** `pyasm.search.TransactionLog`
- **Category / status:** `audit/internal` / `active core/internal`; confidence: `high`
- **Purpose:** Full transaction/command log including XML change payload and undo-related metadata.
- **5.0 schema fields:** `id`, `code`, `transaction`, `login`, `timestamp`, `description`, `command`, `title`, `type`, `namespace`
- **Write path:** Written by transaction manager.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** sobject_log.transaction_log_id; transaction_code references.
- **Do not:** Large/sensitive; do not mutate, and do not treat every row as user-facing activity. Read `transaction` with `get_xml_value("transaction")`, not as raw text, because payloads larger than 10 KiB are stored with `zlib:` compression.

### `transaction_state`

- **Logical search type:** `sthpw/transaction_state`
- **Physical location:** `sthpw` DB; table `transaction_state`
- **Registered class:** `pyasm.search.TransactionState`
- **Category / status:** `audit/internal` / `internal`; confidence: `high`
- **Purpose:** Temporary XML-RPC/transaction state keyed by ticket.
- **5.0 schema fields:** `id`, `ticket`, `timestamp`, `data`
- **Write path:** Use transaction/XML-RPC state subsystem.
- **Policy:** `internal_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** ticket.
- **Do not:** Ephemeral internal state, not user settings.

## bootstrap/meta
### `db_resource`

- **Logical search type:** `sthpw/db_resource`
- **Physical location:** `sthpw` DB; table `db_resource`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `bootstrap/meta` / `active admin`; confidence: `high`
- **Purpose:** Database connection resource used by projects/search types.
- **5.0 schema fields:** `id`, `code`, `host`, `port`, `vendor`, `login`, `password`
- **Write path:** Use project/database-resource administration APIs.
- **Policy:** `admin_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** project.db_resource; search_object.database.
- **Do not:** Contains credentials; never expose password to clients or logs.

### `project`

- **Logical search type:** `sthpw/project`
- **Physical location:** `sthpw` DB; table `project`
- **Registered class:** `pyasm.biz.Project`
- **Category / status:** `bootstrap/meta` / `active core`; confidence: `high`
- **Purpose:** Registered TACTIC project/template and its DB/naming/runtime metadata.
- **5.0 schema fields:** `id`, `code`, `title`, `sobject_mapping_cls`, `dir_naming_cls`, `code_naming_cls`, `pipeline`, `snapshot`, `type`, `last_db_update`, `description`, `initials`, `file_naming_cls`, `reg_hours`, `node_naming_cls`, `s_status`, `status`, `last_version_update`, `palette`, `category`, `is_template`, `db_resource`
- **Write path:** Use pyasm.biz.Project/project creation and upgrade tools.
- **Policy:** `project_manager_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** db_resource; search_object database={project}.
- **Do not:** Creating a row alone does not create the project database, schema, config or permissions.

### `project_type`

- **Logical search type:** `sthpw/project_type`
- **Physical location:** `sthpw` DB; table `project_type`
- **Registered class:** `pyasm.biz.ProjectType`
- **Category / status:** `bootstrap/meta` / `legacy/extension`; confidence: `high`
- **Purpose:** Project-type strategy class registry (naming, mapping, repository handlers).
- **5.0 schema fields:** `id`, `code`, `dir_naming_cls`, `file_naming_cls`, `code_naming_cls`, `node_naming_cls`, `sobject_mapping_cls`, `s_status`, `type`, `repo_handler_cls`
- **Write path:** Use ProjectType/plugin/admin setup APIs.
- **Policy:** `admin_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** project.type.
- **Do not:** Stores importable class names; invalid values can break project behavior.

### `schema`

- **Logical search type:** `sthpw/schema`
- **Physical location:** `sthpw` DB; table `schema`
- **Registered class:** `pyasm.biz.Schema`
- **Category / status:** `bootstrap/meta` / `active core`; confidence: `high`
- **Purpose:** XML project/data-model relationship schema.
- **5.0 schema fields:** `id`, `code`, `description`, `schema`, `timestamp`, `login`, `s_status`
- **Write path:** Use pyasm.biz.Schema/schema editor and project setup tools.
- **Policy:** `schema_manager_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_object types and relationships.
- **Do not:** Do not update independently of search types/physical columns; validate XML.

### `search_object`

- **Logical search type:** `sthpw/search_object`
- **Physical location:** `sthpw` DB; table `search_object`
- **Registered class:** `pyasm.search.SearchType`
- **Category / status:** `bootstrap/meta` / `active core`; confidence: `high`
- **Purpose:** Search-type registry mapping logical search_type to DB/table/class/schema.
- **5.0 schema fields:** `id`, `code`, `search_type`, `namespace`, `description`, `database`, `table_name`, `class_name`, `title`, `schema`, `color`, `id_column`, `default_layout`
- **Write path:** Use SearchType/search-type creator and database schema tools.
- **Policy:** `search_type_manager_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** all SObject resolution.
- **Do not:** A row alone does not create/migrate the physical table or views; class_name is executable configuration.

## configuration
### `custom_property`

- **Logical search type:** `config/custom_property`
- **Physical location:** `sthpw` DB; table `custom_property`
- **Registered class:** `pyasm.biz.CustomProperty`
- **Category / status:** `configuration` / `active config`; confidence: `medium`
- **Purpose:** Project-local custom property definitions for a search type.
- **5.0 schema fields:** `id`, `code`, `search_type`, `name`, `description`, `login`
- **Write path:** Use the custom-property/property manager; generic SObject write is acceptable only if its expected schema is preserved.
- **Policy:** `manager_or_generic`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type; name.
- **Do not:** This does not itself add a physical DB column in every workflow; coordinate with search-type/schema tools.

### `doc`

- **Logical search type:** `sthpw/doc`
- **Physical location:** `sthpw` DB; table `doc`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `configuration` / `optional`; confidence: `medium`
- **Purpose:** Documentation alias/path registry.
- **5.0 schema fields:** `id`, `code`, `alias`, `rel_path`
- **Write path:** Use generic SObject APIs or the documentation manager.
- **Policy:** `generic_sobject`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** alias; rel_path.
- **Do not:** Stores references/paths, not document file contents.

## configuration/triggers
### `trigger`

- **Logical search type:** `sthpw/trigger`
- **Physical location:** `sthpw` DB; table `trigger`
- **Registered class:** `pyasm.biz.TriggerSObj`
- **Category / status:** `configuration/triggers` / `active compatibility/core`; confidence: `high`
- **Purpose:** Global/system trigger definition.
- **5.0 schema fields:** `id`, `code`, `class_name`, `script_path`, `description`, `event`, `mode`, `project_code`, `s_status`, `process`, `data`
- **Write path:** Use TriggerSObj/trigger administration.
- **Policy:** `trigger_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** event/process/project_code.
- **Do not:** Prefer config/trigger for project-scoped behavior; executable configuration must be secured.

## dispatcher/jobs
### `queue`

- **Logical search type:** `sthpw/queue`
- **Physical location:** `sthpw` DB; table `queue`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `dispatcher/jobs` / `active internal`; confidence: `high`
- **Purpose:** Dispatcher/job queue record.
- **5.0 schema fields:** `id`, `code`, `queue`, `priority`, `description`, `state`, `login`, `timestamp`, `command`, `serialized`, `s_status`, `project_code`, `search_id`, `search_type`, `dispatcher_id`, `policy_code`, `host`
- **Write path:** Use dispatcher/queue command APIs.
- **Policy:** `owning_subsystem`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** dispatcher_id; policy_code; target search_type/search_id.
- **Do not:** Do not insert jobs manually unless implementing the dispatcher contract including serialized command and state.

## ingest/watch
### `watch_folder`

- **Logical search type:** `sthpw/watch_folder`
- **Physical location:** `sthpw` DB; table `watch_folder`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `ingest/watch` / `active optional`; confidence: `medium`
- **Purpose:** Watched folder configuration that launches a script/process for incoming files.
- **5.0 schema fields:** `id`, `code`, `name`, `project_code`, `base_dir`, `search_type`, `process`, `timestamp`, `script_path`
- **Write path:** Use watch-folder/ingest manager.
- **Policy:** `watch_folder_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** project_code+search_type+process.
- **Do not:** Do not treat as a generic filesystem bookmark; script and service lifecycle matter.

## localization
### `translation`

- **Logical search type:** `sthpw/translation`
- **Physical location:** `sthpw` DB; table `translation`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `localization` / `optional`; confidence: `medium`
- **Purpose:** Global locale msgid/msgstr translation records.
- **5.0 schema fields:** `id`, `code`, `language`, `msgid`, `msgstr`, `line`, `login`, `timestamp`
- **Write path:** Use localization manager.
- **Policy:** `translation_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** language+msgid.
- **Do not:** Do not mix with config/translation semantics without deciding global vs project scope.

## messaging
### `message`

- **Logical search type:** `sthpw/message`
- **Physical location:** `sthpw` DB; table `message`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `messaging` / `active core`; confidence: `high`
- **Purpose:** Message channel/container and latest/current message state; used for chat, sobject, script and progress categories.
- **5.0 schema fields:** `id`, `code`, `category`, `message`, `status`, `login`, `project_code`, `timestamp`
- **Write path:** Use the messaging/chat subsystem; create channel/container through its server command.
- **Policy:** `message_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** message_log.message_code; subscription.message_code.
- **Do not:** A row is not necessarily one chat message. Do not use it as arbitrary notifications table.

### `message_log`

- **Logical search type:** `sthpw/message_log`
- **Physical location:** `sthpw` DB; table `message_log`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `messaging` / `active core`; confidence: `high`
- **Purpose:** Append-only message entries/history for a message channel.
- **5.0 schema fields:** `id`, `code`, `message_code`, `category`, `message`, `status`, `login`, `project_code`, `timestamp`
- **Write path:** Use server.log_message / ChatCmd / message logging API.
- **Policy:** `message_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** message_code -> message.
- **Do not:** Do not direct-insert: channel state, category, subscriptions and polling semantics can diverge.

### `note`

- **Logical search type:** `sthpw/note`
- **Physical location:** `sthpw` DB; table `note`
- **Registered class:** `pyasm.biz.Note`
- **Category / status:** `messaging` / `active core`; confidence: `high`
- **Purpose:** Comment/note attached polymorphically to any SObject, optionally by process/context and parent thread.
- **5.0 schema fields:** `id`, `code`, `project_code`, `search_type`, `search_id`, `login`, `context`, `timestamp`, `note`, `title`, `parent_id`, `status`, `label`, `process`, `sort_order`, `access`
- **Write path:** Use Note.create/add_note APIs.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type/search_id; parent_id; process/context.
- **Do not:** Do not create a parallel task_comments table; preserve access/private and parent_id semantics.

### `subscription`

- **Logical search type:** `sthpw/subscription`
- **Physical location:** `sthpw` DB; table `subscription`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `messaging` / `active core`; confidence: `high`
- **Purpose:** User subscription/membership to a message channel with last-cleared read cursor.
- **5.0 schema fields:** `id`, `code`, `category`, `message_code`, `login`, `project_code`, `status`, `last_cleared`, `timestamp`
- **Write path:** Use Subscription/message APIs.
- **Policy:** `message_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** message_code+login.
- **Do not:** Do not use as universal arbitrary subscription without message_code semantics; last_cleared is a watermark.

## notifications
### `group_notification`

- **Logical search type:** `sthpw/group_notification`
- **Physical location:** `sthpw` DB; table `group_notification`
- **Registered class:** `pyasm.biz.GroupNotification`
- **Category / status:** `notifications` / `active config`; confidence: `high`
- **Purpose:** Association between a notification definition and a login group.
- **5.0 schema fields:** `id`, `login_group`, `notification_id`
- **Write path:** Use GroupNotification/notification administration APIs.
- **Policy:** `notification_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login_group -> notification_id.
- **Do not:** This is configuration, not an inbox row.

### `notification`

- **Logical search type:** `sthpw/notification`
- **Physical location:** `sthpw` DB; table `notification`
- **Registered class:** `pyasm.biz.Notification`
- **Category / status:** `notifications` / `active core`; confidence: `high`
- **Purpose:** Notification definition/rule: event/listen_event, recipients, template and handler configuration.
- **5.0 schema fields:** `id`, `code`, `event`, `listen_event`, `data`, `description`, `process`, `type`, `search_type`, `project_code`, `rules`, `subject`, `message`, `email_handler_cls`, `mail_to`, `mail_cc`, `mail_bcc`, `s_status`, `title`, `status`
- **Write path:** Use pyasm.biz.Notification / notification manager.
- **Policy:** `notification_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** group_notification; notification_log.
- **Do not:** Not a per-user inbox item. Do not insert one row per delivered notification.

### `notification_log`

- **Logical search type:** `sthpw/notification_log`
- **Physical location:** `sthpw` DB; table `notification_log`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `notifications` / `active internal`; confidence: `high`
- **Purpose:** Delivery/execution log for generated notifications.
- **5.0 schema fields:** `id`, `project_code`, `login`, `command_cls`, `subject`, `message`, `timestamp`
- **Write path:** Written by notification subsystem.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** notification_login.notification_log_id.
- **Do not:** Treat as audit/history; do not use as notification definition.

### `notification_login`

- **Logical search type:** `sthpw/notification_login`
- **Physical location:** `sthpw` DB; table `notification_login`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `notifications` / `active internal`; confidence: `high`
- **Purpose:** Per-login delivery association/status for a notification_log entry.
- **5.0 schema fields:** `id`, `notification_log_id`, `login`, `type`, `project_code`, `timestamp`
- **Write path:** Written by notification delivery subsystem.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** notification_log_id; login.
- **Do not:** Not equivalent to chat read receipts.

## organization
### `department`

- **Logical search type:** `sthpw/department`
- **Physical location:** `sthpw` DB; table `department`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `organization` / `optional`; confidence: `medium`
- **Purpose:** Simple department directory.
- **5.0 schema fields:** `id`, `code`, `name`, `timestamp`
- **Write path:** Generic insert/update through TACTIC API is acceptable.
- **Policy:** `generic_sobject`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login.department (logical).
- **Do not:** Keep code stable if referenced from login.department or custom logic.

## preferences
### `pref_list`

- **Logical search type:** `sthpw/pref_list`
- **Physical location:** `sthpw` DB; table `pref_list`
- **Registered class:** `pyasm.biz.PrefList`
- **Category / status:** `preferences` / `optional config`; confidence: `high`
- **Purpose:** Definition/catalog of available preference keys and options.
- **5.0 schema fields:** `id`, `code`, `key`, `description`, `options`, `type`, `category`, `timestamp`, `title`
- **Write path:** Use PrefList/preference administration.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** pref_setting.key.
- **Do not:** Not the user value store; values belong in pref_setting.

### `pref_setting`

- **Logical search type:** `sthpw/pref_setting`
- **Physical location:** `sthpw` DB; table `pref_setting`
- **Registered class:** `pyasm.biz.PrefSetting`
- **Category / status:** `preferences` / `active core`; confidence: `high`
- **Purpose:** Per-user/project preference key-value values.
- **5.0 schema fields:** `id`, `project_code`, `login`, `key`, `value`, `timestamp`
- **Write path:** Use PrefSetting APIs.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login+project_code+key.
- **Do not:** Namespace keys; do not store security- or workflow-authoritative state.

### `wdg_settings`

- **Logical search type:** `sthpw/wdg_settings`
- **Physical location:** `sthpw` DB; table `wdg_settings`
- **Registered class:** `pyasm.web.WidgetSettings`
- **Category / status:** `preferences` / `active core`; confidence: `high`
- **Purpose:** Persistent per-user widget state.
- **5.0 schema fields:** `id`, `key`, `login`, `data`, `timestamp`, `project_code`
- **Write path:** Use WidgetSettings.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login+project_code+key.
- **Do not:** UI-only state; namespace keys and avoid authoritative business data.

## relationships
### `connection`

- **Logical search type:** `sthpw/connection`
- **Physical location:** `sthpw` DB; table `connection`
- **Registered class:** `pyasm.biz.SObjectConnection`
- **Category / status:** `relationships` / `active core`; confidence: `high`
- **Purpose:** Generic directed relationship between two arbitrary SObjects with a context.
- **5.0 schema fields:** `id`, `code`, `context`, `project_code`, `src_search_type`, `src_search_id`, `dst_search_type`, `dst_search_id`, `login`, `timestamp`
- **Write path:** Use SObjectConnection / server.connect_sobjects and disconnect APIs.
- **Policy:** `subsystem_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** src_search_type/src_search_id -> dst_search_type/dst_search_id; context.
- **Do not:** Never hand-insert without resolving source/destination identity; modern deployments may add search_code columns.

## scheduling
### `special_day`

- **Logical search type:** no search type is registered in the consolidated SQL
- **Physical location:** `sthpw` DB; table `special_day`
- **Registered class:** not specified
- **Category / status:** `scheduling` / `optional legacy`; confidence: `medium`
- **Purpose:** Calendar/work-schedule exception or special-day configuration.
- **5.0 schema fields:** `id`, `code`, `week`, `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`, `year`, `login`, `description`, `type`, `project_code`
- **Write path:** Use scheduling/calendar APIs; generic write only if contract is understood.
- **Policy:** `generic_or_schedule_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** project_code/login/year/week.
- **Do not:** Fields are legacy weekly/hour values; verify feature before extending.

## search/index
### `sobject_list`

- **Logical search type:** `sthpw/sobject_list`
- **Physical location:** `sthpw` DB; table `sobject_list`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `search/index` / `internal/optional`; confidence: `medium`
- **Purpose:** Auxiliary indexed/list representation of SObject references and keywords.
- **5.0 schema fields:** `id`, `code`, `search_type`, `search_id`, `keywords`, `timestamp`, `project_code`
- **Write path:** Let indexing/search-list subsystem maintain it.
- **Policy:** `owning_subsystem`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type/search_id.
- **Do not:** Not a business collection or relation table.

## security/users
### `login`

- **Logical search type:** `sthpw/login`
- **Physical location:** `sthpw` DB; table `login`
- **Registered class:** `pyasm.security.Login`
- **Category / status:** `security/users` / `active core`; confidence: `high`
- **Purpose:** User/account record and profile.
- **5.0 schema fields:** `id`, `code`, `login`, `password`, `upn`, `login_groups`, `first_name`, `last_name`, `display_name`, `email`, `phone_number`, `department`, `namespace`, `snapshot`, `s_status`, `project_code`, `license_type`, `hourly_wage`, `data`
- **Write path:** Use pyasm.security.Login, password/authentication and user-management APIs.
- **Policy:** `security_api_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login_in_group; ticket; task.assigned; note.login.
- **Do not:** Never write password directly; preserve external-auth/UPN/status semantics.

### `login_group`

- **Logical search type:** `sthpw/login_group`
- **Physical location:** `sthpw` DB; table `login_group`
- **Registered class:** `pyasm.security.LoginGroup`
- **Category / status:** `security/users` / `active core`; confidence: `high`
- **Purpose:** Security group with XML access_rules and project/default metadata.
- **5.0 schema fields:** `id`, `code`, `login_group`, `name`, `sub_groups`, `access_rules`, `redirect_url`, `namespace`, `description`, `project_code`, `s_status`, `start_link`, `access_level`, `is_default`, `data`
- **Write path:** Use LoginGroup/Security Manager APIs.
- **Policy:** `security_api_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login_in_group; group_notification.
- **Do not:** Do not treat group name as authorization; effective access is computed by AccessManager.

### `login_in_group`

- **Logical search type:** `sthpw/login_in_group`
- **Physical location:** `sthpw` DB; table `login_in_group`
- **Registered class:** `pyasm.security.LoginInGroup`
- **Category / status:** `security/users` / `active core`; confidence: `high`
- **Purpose:** Membership link between login and login_group.
- **5.0 schema fields:** `id`, `code`, `login`, `login_group`
- **Write path:** Use Login.add_to_group/remove_from_group or group membership APIs.
- **Policy:** `security_api_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login -> login_group.
- **Do not:** Avoid duplicates; changes affect effective security and caches.

### `ticket`

- **Logical search type:** `sthpw/ticket`
- **Physical location:** `sthpw` DB; table `ticket`
- **Registered class:** `pyasm.security.Ticket`
- **Category / status:** `security/users` / `active core`; confidence: `high`
- **Purpose:** Authentication/session ticket with expiry/category.
- **5.0 schema fields:** `id`, `code`, `ticket`, `login`, `timestamp`, `expiry`, `category`
- **Write path:** Use Ticket/authentication/session APIs.
- **Policy:** `security_api_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login.
- **Do not:** Never mint or update tickets directly from clients.

## sync
### `sync_job`

- **Logical search type:** `sthpw/sync_job`
- **Physical location:** `sthpw` DB; table `sync_job`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `sync` / `active optional`; confidence: `high`
- **Purpose:** Outgoing/incoming remote synchronization job.
- **5.0 schema fields:** `id`, `code`, `login`, `timestamp`, `command`, `data`, `state`, `host`, `project_code`, `error_log`, `server_code`, `transaction_code`
- **Write path:** Use synchronization engine.
- **Policy:** `sync_engine_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** sync_server/server_code; transaction_code.
- **Do not:** Command/data/state and transaction linkage are engine contracts.

### `sync_log`

- **Logical search type:** `sthpw/sync_log`
- **Physical location:** `sthpw` DB; table `sync_log`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `sync` / `active optional`; confidence: `high`
- **Purpose:** Processed synchronization transaction/result log.
- **5.0 schema fields:** `id`, `code`, `transaction_code`, `status`, `error`, `login`, `timestamp`, `project_code`
- **Write path:** Written by sync engine.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** transaction_code; project_code.
- **Do not:** Do not retry by editing rows; use sync job/recovery APIs.

### `sync_server`

- **Logical search type:** `sthpw/sync_server`
- **Physical location:** `sthpw` DB; table `sync_server`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `sync` / `active optional`; confidence: `high`
- **Purpose:** Remote TACTIC synchronization peer and credentials/rules.
- **5.0 schema fields:** `id`, `code`, `host`, `login`, `timestamp`, `state`, `ticket`, `access_rules`, `description`, `sync_mode`, `base_dir`, `file_mode`
- **Write path:** Use sync-server administration.
- **Policy:** `sync_admin`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** sync_job.server_code.
- **Do not:** Contains ticket/access rules and connectivity data; protect as secret config.

## time tracking
### `work_hour`

- **Logical search type:** `sthpw/work_hour`
- **Physical location:** `sthpw` DB; table `work_hour`
- **Registered class:** `pyasm.biz.WorkHour`
- **Category / status:** `time tracking` / `active optional`; confidence: `high`
- **Purpose:** Time/work-hour entry linked to an SObject/task/process.
- **5.0 schema fields:** `id`, `code`, `project_code`, `description`, `category`, `process`, `login`, `day`, `start_time`, `end_time`, `straight_time`, `over_time`, `search_type`, `search_id`, `status`, `task_code`
- **Write path:** Use WorkHour/timecard APIs.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type/search_id; task_code; login.
- **Do not:** Durations, dates and task linkage may drive reports/payroll; validate rather than ad-hoc insert.

## user productivity
### `clipboard`

- **Logical search type:** `sthpw/clipboard`
- **Physical location:** `sthpw` DB; table `clipboard`
- **Registered class:** `pyasm.biz.Clipboard`
- **Category / status:** `user productivity` / `active optional`; confidence: `high`
- **Purpose:** Server-side user clipboard entries referencing arbitrary SObjects.
- **5.0 schema fields:** `id`, `project_code`, `login`, `search_type`, `search_id`, `timestamp`, `category`
- **Write path:** Use pyasm.biz.Clipboard or existing clipboard server APIs.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login + search_type/search_id.
- **Do not:** Do not duplicate object data; store only the reference and category.

### `interaction`

- **Logical search type:** `sthpw/interaction`
- **Physical location:** `sthpw` DB; table `interaction`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `user productivity` / `optional/internal`; confidence: `medium`
- **Purpose:** Generic per-user interaction/state store keyed by a string.
- **5.0 schema fields:** `id`, `code`, `project_code`, `login`, `key`, `data`, `timestamp`
- **Write path:** Use only through the feature that defines the key/data contract.
- **Policy:** `owning_subsystem`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** login+project_code+key.
- **Do not:** Do not turn it into an unversioned dumping ground; namespace keys.

## workflow
### `pipeline`

- **Logical search type:** `sthpw/pipeline`
- **Physical location:** `sthpw` DB; table `pipeline`
- **Registered class:** `pyasm.biz.Pipeline`
- **Category / status:** `workflow` / `active compatibility/core`; confidence: `high`
- **Purpose:** Global/system pipeline XML and metadata; historically the primary Pipeline table.
- **5.0 schema fields:** `id`, `code`, `pipeline`, `timestamp`, `search_type`, `project_code`, `description`, `color`, `s_status`, `autocreate_tasks`, `use_workflow`
- **Write path:** Use pyasm.biz.Pipeline and pipeline editor/synchronization routines.
- **Policy:** `pipeline_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** task.pipeline_code; config/process.pipeline_code.
- **Do not:** Do not edit XML and related process rows independently; config/pipeline also exists in project DBs.

## workflow/tasks
### `milestone`

- **Logical search type:** `sthpw/milestone`
- **Physical location:** `sthpw` DB; table `milestone`
- **Registered class:** `pyasm.biz.Milestone`
- **Category / status:** `workflow/tasks` / `active optional`; confidence: `high`
- **Purpose:** Project milestone/due-date object.
- **5.0 schema fields:** `id`, `code`, `project_code`, `description`, `due_date`
- **Write path:** Use pyasm.biz.Milestone or generic SObject APIs when no extra behavior is needed.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** task.milestone_code.
- **Do not:** Tasks reference milestone_code logically.

### `status_log`

- **Logical search type:** `sthpw/status_log`
- **Physical location:** `sthpw` DB; table `status_log`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `workflow/tasks` / `active core`; confidence: `high`
- **Purpose:** Append-only status transition history for an SObject, commonly task.
- **5.0 schema fields:** `id`, `search_type`, `search_id`, `status`, `login`, `timestamp`, `to_status`, `from_status`, `project_code`
- **Write path:** Let Task/status-change/trigger machinery append it.
- **Policy:** `read_only_system`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type/search_id; from_status/to_status.
- **Do not:** Do not update old rows or use as current status; current value lives on the target object/task.

### `task`

- **Logical search type:** `sthpw/task`
- **Physical location:** `sthpw` DB; table `task`
- **Registered class:** `pyasm.biz.Task`
- **Category / status:** `workflow/tasks` / `active core`; confidence: `high`
- **Purpose:** Concrete work item for one target SObject and process.
- **5.0 schema fields:** `id`, `assigned`, `description`, `status`, `discussion`, `bid_start_date`, `bid_end_date`, `bid_duration`, `actual_start_date`, `actual_end_date`, `search_type`, `search_id`, `timestamp`, `s_status`, `priority`, `process`, `context`, `milestone_code`, `pipeline_code`, `parent_id`, `sort_order`, `depend_id`, `project_code`, `supervisor`, `code`, `login`, `completion`
- **Write path:** Use Task.create/task APIs and status methods.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type/search_id; pipeline_code/process; milestone/dependency.
- **Do not:** Do not create a parallel task table; preserve search target, process, pipeline, assignee and status triggers.
