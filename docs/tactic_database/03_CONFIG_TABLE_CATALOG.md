# Project Config Table Catalog
Поля перечислены по PostgreSQL-схемам ветки `5.0`. Отсутствие SQL foreign key не означает отсутствие логической связи.
## DAM/naming
### `spt_naming`

- **Логический search type:** `config/naming`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_naming`
- **Зарегистрированный класс:** `pyasm.biz.Naming`
- **Категория / статус:** `DAM/naming` / `active core`; уверенность: `high`
- **Назначение:** Project naming rule for repository directories, files, sandbox and versionless behavior.
- **Поля схемы 5.0:** `id`, `search_type`, `dir_naming`, `file_naming`, `sandbox_dir_naming`, `snapshot_type`, `context`, `code`, `latest_versionless`, `current_versionless`, `manual_version`, `ingest_rule_code`, `condition`, `class_name`, `script_path`, `checkin_type`, `base_dir_alias`, `sandbox_dir_alias`
- **Как записывать:** Use Naming/naming editor APIs, then invalidate/reload naming caches if required.
- **Политика:** `naming_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type/context/snapshot_type/checkin_type; ingest_rule.
- **Не делать:** Avoid duplicate overlapping defaults; checkin_type/context/snapshot_type/condition determine selection.

## configuration
### `spt_prod_setting`

- **Логический search type:** `config/prod_setting`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_prod_setting`
- **Зарегистрированный класс:** `pyasm.prod.biz.ProdSetting`
- **Категория / статус:** `configuration` / `active config`; уверенность: `high`
- **Назначение:** Project production/application setting catalog.
- **Поля схемы 5.0:** `id`, `code`, `key`, `value`, `description`, `type`, `search_type`, `category`
- **Как записывать:** Use ProdSetting/ProjectSetting APIs.
- **Политика:** `class_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** key; search_type/category.
- **Не делать:** Keys may be cached and interpreted globally; avoid duplicates and arbitrary semantics.

## configuration/UI
### `spt_url`

- **Логический search type:** `config/url`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_url`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `configuration/UI` / `active config`; уверенность: `medium`
- **Назначение:** Custom URL route to widget/configuration.
- **Поля схемы 5.0:** `id`, `code`, `url`, `widget`, `description`, `timestamp`, `s_status`
- **Как записывать:** Use URL/widget configuration manager.
- **Политика:** `view_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** url -> widget.
- **Не делать:** Widget content is executable UI configuration; restrict write permissions.

### `spt_widget_config`

- **Логический search type:** `config/widget_config`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_widget_config`
- **Зарегистрированный класс:** `pyasm.search.WidgetDbConfig`
- **Категория / статус:** `configuration/UI` / `active core`; уверенность: `high`
- **Назначение:** Project view/form/table/widget XML configuration.
- **Поля схемы 5.0:** `id`, `code`, `view`, `category`, `search_type`, `login`, `config`, `timestamp`, `widget_type`, `s_status`
- **Как записывать:** Use WidgetDbConfig/View Manager APIs.
- **Политика:** `widget_config_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type+view+category+login.
- **Не делать:** Do not overwrite configs blindly: category/view/search_type/login precedence matters and XML must remain valid.

## configuration/scripts
### `spt_custom_script`

- **Логический search type:** `config/custom_script`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_custom_script`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `configuration/scripts` / `active config`; уверенность: `high`
- **Назначение:** Project custom script source and metadata.
- **Поля схемы 5.0:** `id`, `code`, `title`, `description`, `folder`, `script`, `login`, `timestamp`, `language`, `s_status`
- **Как записывать:** Use custom script editor/manager.
- **Политика:** `script_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** trigger/script_path references.
- **Не делать:** Executable code: security-review, version and permission controls required.

## configuration/triggers
### `spt_client_trigger`

- **Логический search type:** `config/client_trigger`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_client_trigger`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `configuration/triggers` / `active config`; уверенность: `medium`
- **Назначение:** Client-side event-to-callback trigger configuration.
- **Поля схемы 5.0:** `id`, `code`, `event`, `callback`, `description`, `timestamp`, `s_status`
- **Как записывать:** Use client-trigger/view configuration tools.
- **Политика:** `trigger_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** event -> callback.
- **Не делать:** Callback is executable client configuration; validate and restrict permissions.

### `spt_trigger`

- **Логический search type:** `config/trigger`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_trigger`
- **Зарегистрированный класс:** `pyasm.biz.TriggerSObj`
- **Категория / статус:** `configuration/triggers` / `active core`; уверенность: `high`
- **Назначение:** Project-local server trigger definition.
- **Поля схемы 5.0:** `id`, `code`, `class_name`, `script_path`, `title`, `description`, `event`, `mode`, `process`, `listen_process`, `trigger_type`, `data`, `timestamp`, `search_type`, `s_status`
- **Как записывать:** Use TriggerSObj/trigger manager and trigger installation APIs.
- **Политика:** `trigger_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** event/process/search_type.
- **Не делать:** Executable class/script configuration; event/process/listen_process semantics must be validated.

## ingest
### `spt_ingest_rule`

- **Логический search type:** `config/ingest_rule`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_ingest_rule`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `ingest` / `active optional`; уверенность: `medium`
- **Назначение:** Ingest rule definition tied to a session and base directory.
- **Поля схемы 5.0:** `id`, `code`, `spt_ingest_session_code`, `title`, `base_dir`, `rule`, `data`
- **Как записывать:** Use ingest manager/session APIs.
- **Политика:** `ingest_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** spt_ingest_session_code; naming.ingest_rule_code.
- **Не делать:** Rule/data formats are subsystem contracts; do not ad-hoc mutate.

### `spt_ingest_session`

- **Логический search type:** `config/ingest_session`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_ingest_session`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `ingest` / `active optional`; уверенность: `medium`
- **Назначение:** Ingest session/configuration root.
- **Поля схемы 5.0:** `id`, `code`, `title`, `base_dir`, `location`, `data`
- **Как записывать:** Use ingest manager.
- **Политика:** `ingest_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** ingest_rule session code.
- **Не делать:** Not a generic upload session unless ingest subsystem owns it.

## localization
### `spt_translation`

- **Логический search type:** `config/translation`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_translation`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `localization` / `optional`; уверенность: `medium`
- **Назначение:** Project-local translation table with language columns.
- **Поля схемы 5.0:** `id`, `code`, `name`, `en`, `fr`, `ja`, `es`, `login`, `timestamp`
- **Как записывать:** Use translation/localization manager.
- **Политика:** `translation_manager`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** name.
- **Не делать:** Schema is language-column based and may not scale to arbitrary locales without migration.

## plugins
### `spt_plugin`

- **Логический search type:** `config/plugin`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_plugin`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `plugins` / `active config`; уверенность: `high`
- **Назначение:** Installed plugin manifest/version/location record.
- **Поля схемы 5.0:** `id`, `code`, `description`, `manifest`, `timestamp`, `version`, `rel_dir`, `s_status`
- **Как записывать:** Use plugin installer/manager.
- **Политика:** `plugin_installer_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** spt_plugin_content.plugin_code.
- **Не делать:** A row alone does not install files, content or migrations.

### `spt_plugin_content`

- **Логический search type:** `config/plugin_content`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_plugin_content`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `plugins` / `active internal`; уверенность: `high`
- **Назначение:** Mapping of a plugin to content SObjects it installed/owns.
- **Поля схемы 5.0:** `id`, `code`, `plugin_code`, `search_type`, `search_code`
- **Как записывать:** Use plugin installer.
- **Политика:** `plugin_installer_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** plugin_code -> arbitrary search_type/search_code.
- **Не делать:** Do not manually delete before plugin uninstall/rollback logic.

## workflow
### `spt_pipeline`

- **Логический search type:** `config/pipeline`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_pipeline`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `workflow` / `active core`; уверенность: `high`
- **Назначение:** Project-local pipeline XML/configuration.
- **Поля схемы 5.0:** `id`, `code`, `pipeline`, `timestamp`, `search_type`, `description`, `s_status`, `color`, `autocreate_tasks`, `data`
- **Как записывать:** Use pipeline editor and Pipeline synchronization routines.
- **Политика:** `pipeline_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** spt_process.pipeline_code; task.pipeline_code.
- **Не делать:** Do not update XML without synchronizing config/process and workflow behavior.

### `spt_process`

- **Логический search type:** `config/process`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_process`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `workflow` / `active core`; уверенность: `high`
- **Назначение:** Per-process configuration supplement for a pipeline node: check-in, contexts, repository and transfer behavior.
- **Поля схемы 5.0:** `id`, `code`, `pipeline_code`, `process`, `color`, `sort_order`, `timestamp`, `s_status`, `checkin_mode`, `subcontext_options`, `checkin_validate_script_path`, `checkin_options_view`, `sandbox_create_script_path`, `context_options`, `description`, `repo_type`, `transfer_mode`
- **Как записывать:** Use pipeline/process editor and synchronization APIs.
- **Политика:** `pipeline_api`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** pipeline_code+process; task/process; naming/checkin.
- **Не делать:** This is node configuration, not a task instance. Keep process+pipeline_code aligned with pipeline XML.

### `spt_process_state`

- **Логический search type:** `config/process_state`
- **Физическое размещение:** каждая project DB (`spt_*`); таблица `spt_process_state`
- **Зарегистрированный класс:** `pyasm.search.SObject`
- **Категория / статус:** `workflow` / `active internal/core`; уверенность: `high`
- **Назначение:** Runtime workflow state for one SObject/process.
- **Поля схемы 5.0:** `id`, `code`, `pipeline_code`, `process`, `search_type`, `search_code`, `timestamp`, `status`, `state`, `data`, `s_status`
- **Как записывать:** Let workflow engine create/update it.
- **Политика:** `workflow_engine_only`. Прямой SQL из приложения запрещён; SQL допустим только в миграции/ремонте с пониманием триггеров и кэшей.
- **Связи:** search_type/search_code+pipeline_code+process.
- **Не делать:** Do not use as task status or UI cache; status/data are engine-owned JSON.

