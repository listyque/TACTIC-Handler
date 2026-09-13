# Project Config Table Catalog
Fields are listed from the PostgreSQL schemas of the `5.0`. The absence of a SQL foreign key does not imply the absence of a logical relationship.
## DAM/naming
### `spt_naming`

- **Logical search type:** `config/naming`
- **Physical location:** each project DB (`spt_*`); table `spt_naming`
- **Registered class:** `pyasm.biz.Naming`
- **Category / status:** `DAM/naming` / `active core`; confidence: `high`
- **Purpose:** Project naming rule for repository directories, files, sandbox and versionless behavior.
- **5.0 schema fields:** `id`, `search_type`, `dir_naming`, `file_naming`, `sandbox_dir_naming`, `snapshot_type`, `context`, `code`, `latest_versionless`, `current_versionless`, `manual_version`, `ingest_rule_code`, `condition`, `class_name`, `script_path`, `checkin_type`, `base_dir_alias`, `sandbox_dir_alias`
- **Write path:** Use Naming/naming editor APIs, then invalidate/reload naming caches if required.
- **Policy:** `naming_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type/context/snapshot_type/checkin_type; ingest_rule.
- **Do not:** Avoid duplicate overlapping defaults; checkin_type/context/snapshot_type/condition determine selection.

## configuration
### `spt_prod_setting`

- **Logical search type:** `config/prod_setting`
- **Physical location:** each project DB (`spt_*`); table `spt_prod_setting`
- **Registered class:** `pyasm.prod.biz.ProdSetting`
- **Category / status:** `configuration` / `active config`; confidence: `high`
- **Purpose:** Project production/application setting catalog.
- **5.0 schema fields:** `id`, `code`, `key`, `value`, `description`, `type`, `search_type`, `category`
- **Write path:** Use ProdSetting/ProjectSetting APIs.
- **Policy:** `class_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** key; search_type/category.
- **Do not:** Keys may be cached and interpreted globally; avoid duplicates and arbitrary semantics.

## configuration/UI
### `spt_url`

- **Logical search type:** `config/url`
- **Physical location:** each project DB (`spt_*`); table `spt_url`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `configuration/UI` / `active config`; confidence: `medium`
- **Purpose:** Custom URL route to widget/configuration.
- **5.0 schema fields:** `id`, `code`, `url`, `widget`, `description`, `timestamp`, `s_status`
- **Write path:** Use URL/widget configuration manager.
- **Policy:** `view_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** url -> widget.
- **Do not:** Widget content is executable UI configuration; restrict write permissions.

### `spt_widget_config`

- **Logical search type:** `config/widget_config`
- **Physical location:** each project DB (`spt_*`); table `spt_widget_config`
- **Registered class:** `pyasm.search.WidgetDbConfig`
- **Category / status:** `configuration/UI` / `active core`; confidence: `high`
- **Purpose:** Project view/form/table/widget XML configuration.
- **5.0 schema fields:** `id`, `code`, `view`, `category`, `search_type`, `login`, `config`, `timestamp`, `widget_type`, `s_status`
- **Write path:** Use WidgetDbConfig/View Manager APIs.
- **Policy:** `widget_config_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type+view+category+login.
- **Do not:** Do not overwrite configs blindly: category/view/search_type/login precedence matters and XML must remain valid.

## configuration/scripts
### `spt_custom_script`

- **Logical search type:** `config/custom_script`
- **Physical location:** each project DB (`spt_*`); table `spt_custom_script`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `configuration/scripts` / `active config`; confidence: `high`
- **Purpose:** Project custom script source and metadata.
- **5.0 schema fields:** `id`, `code`, `title`, `description`, `folder`, `script`, `login`, `timestamp`, `language`, `s_status`
- **Write path:** Use custom script editor/manager.
- **Policy:** `script_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** trigger/script_path references.
- **Do not:** Executable code: security-review, version and permission controls required.

## configuration/triggers
### `spt_client_trigger`

- **Logical search type:** `config/client_trigger`
- **Physical location:** each project DB (`spt_*`); table `spt_client_trigger`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `configuration/triggers` / `active config`; confidence: `medium`
- **Purpose:** Client-side event-to-callback trigger configuration.
- **5.0 schema fields:** `id`, `code`, `event`, `callback`, `description`, `timestamp`, `s_status`
- **Write path:** Use client-trigger/view configuration tools.
- **Policy:** `trigger_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** event -> callback.
- **Do not:** Callback is executable client configuration; validate and restrict permissions.

### `spt_trigger`

- **Logical search type:** `config/trigger`
- **Physical location:** each project DB (`spt_*`); table `spt_trigger`
- **Registered class:** `pyasm.biz.TriggerSObj`
- **Category / status:** `configuration/triggers` / `active core`; confidence: `high`
- **Purpose:** Project-local server trigger definition.
- **5.0 schema fields:** `id`, `code`, `class_name`, `script_path`, `title`, `description`, `event`, `mode`, `process`, `listen_process`, `trigger_type`, `data`, `timestamp`, `search_type`, `s_status`
- **Write path:** Use TriggerSObj/trigger manager and trigger installation APIs.
- **Policy:** `trigger_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** event/process/search_type.
- **Do not:** Executable class/script configuration; event/process/listen_process semantics must be validated.

## ingest
### `spt_ingest_rule`

- **Logical search type:** `config/ingest_rule`
- **Physical location:** each project DB (`spt_*`); table `spt_ingest_rule`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `ingest` / `active optional`; confidence: `medium`
- **Purpose:** Ingest rule definition tied to a session and base directory.
- **5.0 schema fields:** `id`, `code`, `spt_ingest_session_code`, `title`, `base_dir`, `rule`, `data`
- **Write path:** Use ingest manager/session APIs.
- **Policy:** `ingest_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** spt_ingest_session_code; naming.ingest_rule_code.
- **Do not:** Rule/data formats are subsystem contracts; do not ad-hoc mutate.

### `spt_ingest_session`

- **Logical search type:** `config/ingest_session`
- **Physical location:** each project DB (`spt_*`); table `spt_ingest_session`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `ingest` / `active optional`; confidence: `medium`
- **Purpose:** Ingest session/configuration root.
- **5.0 schema fields:** `id`, `code`, `title`, `base_dir`, `location`, `data`
- **Write path:** Use ingest manager.
- **Policy:** `ingest_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** ingest_rule session code.
- **Do not:** Not a generic upload session unless ingest subsystem owns it.

## localization
### `spt_translation`

- **Logical search type:** `config/translation`
- **Physical location:** each project DB (`spt_*`); table `spt_translation`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `localization` / `optional`; confidence: `medium`
- **Purpose:** Project-local translation table with language columns.
- **5.0 schema fields:** `id`, `code`, `name`, `en`, `fr`, `ja`, `es`, `login`, `timestamp`
- **Write path:** Use translation/localization manager.
- **Policy:** `translation_manager`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** name.
- **Do not:** Schema is language-column based and may not scale to arbitrary locales without migration.

## plugins
### `spt_plugin`

- **Logical search type:** `config/plugin`
- **Physical location:** each project DB (`spt_*`); table `spt_plugin`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `plugins` / `active config`; confidence: `high`
- **Purpose:** Installed plugin manifest/version/location record.
- **5.0 schema fields:** `id`, `code`, `description`, `manifest`, `timestamp`, `version`, `rel_dir`, `s_status`
- **Write path:** Use plugin installer/manager.
- **Policy:** `plugin_installer_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** spt_plugin_content.plugin_code.
- **Do not:** A row alone does not install files, content or migrations.

### `spt_plugin_content`

- **Logical search type:** `config/plugin_content`
- **Physical location:** each project DB (`spt_*`); table `spt_plugin_content`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `plugins` / `active internal`; confidence: `high`
- **Purpose:** Mapping of a plugin to content SObjects it installed/owns.
- **5.0 schema fields:** `id`, `code`, `plugin_code`, `search_type`, `search_code`
- **Write path:** Use plugin installer.
- **Policy:** `plugin_installer_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** plugin_code -> arbitrary search_type/search_code.
- **Do not:** Do not manually delete before plugin uninstall/rollback logic.

## workflow
### `spt_pipeline`

- **Logical search type:** `config/pipeline`
- **Physical location:** each project DB (`spt_*`); table `spt_pipeline`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `workflow` / `active core`; confidence: `high`
- **Purpose:** Project-local pipeline XML/configuration.
- **5.0 schema fields:** `id`, `code`, `pipeline`, `timestamp`, `search_type`, `description`, `s_status`, `color`, `autocreate_tasks`, `data`
- **Write path:** Use pipeline editor and Pipeline synchronization routines.
- **Policy:** `pipeline_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** spt_process.pipeline_code; task.pipeline_code.
- **Do not:** Do not update XML without synchronizing config/process and workflow behavior.

### `spt_process`

- **Logical search type:** `config/process`
- **Physical location:** each project DB (`spt_*`); table `spt_process`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `workflow` / `active core`; confidence: `high`
- **Purpose:** Per-process configuration supplement for a pipeline node: check-in, contexts, repository and transfer behavior.
- **5.0 schema fields:** `id`, `code`, `pipeline_code`, `process`, `color`, `sort_order`, `timestamp`, `s_status`, `checkin_mode`, `subcontext_options`, `checkin_validate_script_path`, `checkin_options_view`, `sandbox_create_script_path`, `context_options`, `description`, `repo_type`, `transfer_mode`
- **Write path:** Use pipeline/process editor and synchronization APIs.
- **Policy:** `pipeline_api`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** pipeline_code+process; task/process; naming/checkin.
- **Do not:** This is node configuration, not a task instance. Keep process+pipeline_code aligned with pipeline XML.

### `spt_process_state`

- **Logical search type:** `config/process_state`
- **Physical location:** each project DB (`spt_*`); table `spt_process_state`
- **Registered class:** `pyasm.search.SObject`
- **Category / status:** `workflow` / `active internal/core`; confidence: `high`
- **Purpose:** Runtime workflow state for one SObject/process.
- **5.0 schema fields:** `id`, `code`, `pipeline_code`, `process`, `search_type`, `search_code`, `timestamp`, `status`, `state`, `data`, `s_status`
- **Write path:** Let workflow engine create/update it.
- **Policy:** `workflow_engine_only`. Direct SQL from application code is forbidden; SQL is allowed only for migration or repair with full awareness of triggers and caches.
- **Relationships:** search_type/search_code+pipeline_code+process.
- **Do not:** Do not use as task status or UI cache; status/data are engine-owned JSON.

