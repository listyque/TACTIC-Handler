# Write Policy Matrix
| Search type | Table | Category | Status | Policy | Preferred write path | Registered class |
|---|---|---|---|---|---|---|
| - | access_log | audit/internal | internal | read_only_system | Do not create from application modules; let the request/access logger own it. | - |
| sthpw/cache | cache | audit/internal | internal | read_only_system | Use the owning cache subsystem. | pyasm.search.SObject |
| - | change_timestamp | audit/internal | active internal | read_only_system | Let transaction/commit machinery update it. | - |
| sthpw/clipboard | clipboard | user productivity | active optional | class_api | Use pyasm.biz.Clipboard or existing clipboard server APIs. | pyasm.biz.Clipboard |
| sthpw/command_log | command_log | audit/internal | legacy/internal | read_only_system | Written by command execution framework. | pyasm.command.CommandLog |
| sthpw/connection | connection | relationships | active core | subsystem_api | Use SObjectConnection / server.connect_sobjects and disconnect APIs. | pyasm.biz.SObjectConnection |
| config/custom_property | custom_property | configuration | active config | manager_or_generic | Use the custom-property/property manager; generic SObject write is acceptable only if its expected schema is preserved. | pyasm.biz.CustomProperty |
| sthpw/db_resource | db_resource | bootstrap/meta | active admin | admin_manager | Use project/database-resource administration APIs. | pyasm.search.SObject |
| sthpw/debug_log | debug_log | audit/internal | active internal | append_via_api | Use DebugLog/logger APIs. | pyasm.biz.DebugLog |
| sthpw/department | department | organization | optional | generic_sobject | Generic insert/update through TACTIC API is acceptable. | pyasm.search.SObject |
| sthpw/doc | doc | configuration | optional | generic_sobject | Use generic SObject APIs or the documentation manager. | pyasm.search.SObject |
| sthpw/exception_log | exception_log | audit/internal | active internal | read_only_system | Written by exception logging framework. | pyasm.search.SObject |
| sthpw/file | file | DAM/check-in | active core | checkin_api_only | Create/update only through FileCheckin/FileAppendCheckin/Snapshot/file APIs. | pyasm.biz.file.File |
| sthpw/file_access | file_access | DAM/check-in | optional/internal | subsystem_api | Use FileAccess/file-serving subsystem. | pyasm.biz.FileAccess |
| sthpw/group_notification | group_notification | notifications | active config | notification_api | Use GroupNotification/notification administration APIs. | pyasm.biz.GroupNotification |
| sthpw/interaction | interaction | user productivity | optional/internal | owning_subsystem | Use only through the feature that defines the key/data contract. | pyasm.search.SObject |
| sthpw/login | login | security/users | active core | security_api_only | Use pyasm.security.Login, password/authentication and user-management APIs. | pyasm.security.Login |
| sthpw/login_group | login_group | security/users | active core | security_api_only | Use LoginGroup/Security Manager APIs. | pyasm.security.LoginGroup |
| sthpw/login_in_group | login_in_group | security/users | active core | security_api_only | Use Login.add_to_group/remove_from_group or group membership APIs. | pyasm.security.LoginInGroup |
| sthpw/message | message | messaging | active core | message_api | Use the messaging/chat subsystem; create channel/container through its server command. | pyasm.search.SObject |
| sthpw/message_log | message_log | messaging | active core | message_api | Use server.log_message / ChatCmd / message logging API. | pyasm.search.SObject |
| sthpw/milestone | milestone | workflow/tasks | active optional | class_api | Use pyasm.biz.Milestone or generic SObject APIs when no extra behavior is needed. | pyasm.biz.Milestone |
| sthpw/note | note | messaging | active core | class_api | Use Note.create/add_note APIs. | pyasm.biz.Note |
| sthpw/notification | notification | notifications | active core | notification_api | Use pyasm.biz.Notification / notification manager. | pyasm.biz.Notification |
| sthpw/notification_log | notification_log | notifications | active internal | read_only_system | Written by notification subsystem. | pyasm.search.SObject |
| sthpw/notification_login | notification_login | notifications | active internal | read_only_system | Written by notification delivery subsystem. | pyasm.search.SObject |
| sthpw/pipeline | pipeline | workflow | active compatibility/core | pipeline_api | Use pyasm.biz.Pipeline and pipeline editor/synchronization routines. | pyasm.biz.Pipeline |
| sthpw/pref_list | pref_list | preferences | optional config | class_api | Use PrefList/preference administration. | pyasm.biz.PrefList |
| sthpw/pref_setting | pref_setting | preferences | active core | class_api | Use PrefSetting APIs. | pyasm.biz.PrefSetting |
| sthpw/project | project | bootstrap/meta | active core | project_manager_only | Use pyasm.biz.Project/project creation and upgrade tools. | pyasm.biz.Project |
| sthpw/project_type | project_type | bootstrap/meta | legacy/extension | admin_manager | Use ProjectType/plugin/admin setup APIs. | pyasm.biz.ProjectType |
| sthpw/queue | queue | dispatcher/jobs | active internal | owning_subsystem | Use dispatcher/queue command APIs. | pyasm.search.SObject |
| sthpw/remote_repo | remote_repo | DAM/check-in | legacy optional | repository_manager | Use RemoteRepo/repository administration. | pyasm.biz.RemoteRepo |
| sthpw/repo | repo | DAM/check-in | legacy optional | repository_manager | Use repository administration/configuration APIs. | pyasm.search.SObject |
| sthpw/retire_log | retire_log | audit/internal | active internal | read_only_system | Written by retire/delete machinery. | pyasm.search.RetireLog |
| sthpw/schema | schema | bootstrap/meta | active core | schema_manager_only | Use pyasm.biz.Schema/schema editor and project setup tools. | pyasm.biz.Schema |
| sthpw/search_object | search_object | bootstrap/meta | active core | search_type_manager_only | Use SearchType/search-type creator and database schema tools. | pyasm.search.SearchType |
| sthpw/snapshot | snapshot | DAM/check-in | active core | checkin_api_only | Use Snapshot.create and check-in commands, normally FileCheckin/FileAppendCheckin. | pyasm.biz.Snapshot |
| sthpw/snapshot_type | snapshot_type | DAM/check-in | active optional | class_api | Use SnapshotType/check-in configuration manager. | pyasm.biz.SnapshotType |
| sthpw/sobject_list | sobject_list | search/index | internal/optional | owning_subsystem | Let indexing/search-list subsystem maintain it. | pyasm.search.SObject |
| sthpw/sobject_log | sobject_log | audit/internal | active internal | read_only_system | Written by transaction logging. | pyasm.search.SObject |
| - | special_day | scheduling | optional legacy | generic_or_schedule_api | Use scheduling/calendar APIs; generic write only if contract is understood. | - |
| config/client_trigger | spt_client_trigger | configuration/triggers | active config | trigger_manager | Use client-trigger/view configuration tools. | pyasm.search.SObject |
| config/custom_script | spt_custom_script | configuration/scripts | active config | script_manager | Use custom script editor/manager. | pyasm.search.SObject |
| config/ingest_rule | spt_ingest_rule | ingest | active optional | ingest_api | Use ingest manager/session APIs. | pyasm.search.SObject |
| config/ingest_session | spt_ingest_session | ingest | active optional | ingest_api | Use ingest manager. | pyasm.search.SObject |
| config/naming | spt_naming | DAM/naming | active core | naming_manager | Use Naming/naming editor APIs, then invalidate/reload naming caches if required. | pyasm.biz.Naming |
| config/pipeline | spt_pipeline | workflow | active core | pipeline_api | Use pipeline editor and Pipeline synchronization routines. | pyasm.search.SObject |
| config/plugin | spt_plugin | plugins | active config | plugin_installer_only | Use plugin installer/manager. | pyasm.search.SObject |
| config/plugin_content | spt_plugin_content | plugins | active internal | plugin_installer_only | Use plugin installer. | pyasm.search.SObject |
| config/process | spt_process | workflow | active core | pipeline_api | Use pipeline/process editor and synchronization APIs. | pyasm.search.SObject |
| config/process_state | spt_process_state | workflow | active internal/core | workflow_engine_only | Let workflow engine create/update it. | pyasm.search.SObject |
| config/prod_setting | spt_prod_setting | configuration | active config | class_api | Use ProdSetting/ProjectSetting APIs. | pyasm.prod.biz.ProdSetting |
| config/translation | spt_translation | localization | optional | translation_manager | Use translation/localization manager. | pyasm.search.SObject |
| config/trigger | spt_trigger | configuration/triggers | active core | trigger_manager | Use TriggerSObj/trigger manager and trigger installation APIs. | pyasm.biz.TriggerSObj |
| config/url | spt_url | configuration/UI | active config | view_manager | Use URL/widget configuration manager. | pyasm.search.SObject |
| config/widget_config | spt_widget_config | configuration/UI | active core | widget_config_api | Use WidgetDbConfig/View Manager APIs. | pyasm.search.WidgetDbConfig |
| sthpw/status_log | status_log | workflow/tasks | active core | read_only_system | Let Task/status-change/trigger machinery append it. | pyasm.search.SObject |
| sthpw/subscription | subscription | messaging | active core | message_api | Use Subscription/message APIs. | pyasm.search.SObject |
| sthpw/sync_job | sync_job | sync | active optional | sync_engine_only | Use synchronization engine. | pyasm.search.SObject |
| sthpw/sync_log | sync_log | sync | active optional | read_only_system | Written by sync engine. | pyasm.search.SObject |
| sthpw/sync_server | sync_server | sync | active optional | sync_admin | Use sync-server administration. | pyasm.search.SObject |
| sthpw/task | task | workflow/tasks | active core | class_api | Use Task.create/task APIs and status methods. | pyasm.biz.Task |
| sthpw/ticket | ticket | security/users | active core | security_api_only | Use Ticket/authentication/session APIs. | pyasm.security.Ticket |
| sthpw/transaction_log | transaction_log | audit/internal | active core/internal | read_only_system | Written by transaction manager. | pyasm.search.TransactionLog |
| sthpw/transaction_state | transaction_state | audit/internal | internal | internal_only | Use transaction/XML-RPC state subsystem. | pyasm.search.TransactionState |
| sthpw/translation | translation | localization | optional | translation_manager | Use localization manager. | pyasm.search.SObject |
| sthpw/trigger | trigger | configuration/triggers | active compatibility/core | trigger_manager | Use TriggerSObj/trigger administration. | pyasm.biz.TriggerSObj |
| sthpw/watch_folder | watch_folder | ingest/watch | active optional | watch_folder_api | Use watch-folder/ingest manager. | pyasm.search.SObject |
| sthpw/wdg_settings | wdg_settings | preferences | active core | class_api | Use WidgetSettings. | pyasm.web.WidgetSettings |
| sthpw/work_hour | work_hour | time tracking | active optional | class_api | Use WorkHour/timecard APIs. | pyasm.biz.WorkHour |
