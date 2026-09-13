"""The complete remote surface: domain methods, never arbitrary thlib access."""

METHODS = {
    "HandlerAPI": "projects project sobject snapshot logins login".split(),
    "Project": "get_code get_info stypes stype workflow download_scripts".split(),
    "SType": "get_code get_info get_project get_columns_info get query new pipelines schema".split(),
    "SObject": "get_code get_info get_search_key get_value get_project get_stype commit refresh dependencies delete link related tasks notes snapshots".split(),
    "Snapshot": "get_code get_info get_search_key get_version get_files_objects get_previewable_files_objects is_latest is_versionless".split(),
    "SearchResult": ["next"],
    "FilesAPI": "match ensure_local open reveal".split(),
    "RepositoriesAPI": "list get sync".split(),
    "CommitQueue": "get items add remove_completed".split(),
    "QueueItem": "set_description commit remove".split(),
    "DefinitionCatalog": "list get new resolve".split(),
    "Definition": "set_xml validate element commit".split(),
    "DefinitionElement": "set_attribute set_widget set_option".split(),
    "ResolvedDefinition": [],
    "UICommands": "show open_project open_search_key show_dock show_window checkin_from_dcc checkin_from_maya checkin_files".split(),
    "NativeFile": "get_info get_code get_search_key get_value get_dict get_unique_id get_file_size get_md5 get_timestamp get_metadata get_meta_file_object get_type get_base_type get_ext get_filename_with_ext get_filename get_filename_no_type_prefix get_repo_path get_abs_path get_full_abs_path get_web_path get_full_web_path is_exists is_local_current is_previewable get_web_preview get_icon_preview".split(),
    "NativeFileObject": "get_all_files_list get_name_part get_file_ext is_previewable get_metadata get_pretty_file_name get_type get_sizes_list".split(),
    "NativePipeline": "get_info get_all_pipeline_process get_pipeline_process get_all_pipeline_names get_all_tasks_pipelines_names get_process_info get_processes_info_by_type get_process_label".split(),
    "NativeSchema": "get_info get_parents get_children get_child get_parent get_child_instance get_parent_instance".split(),
    "NativeWorkflow": "get_all_pipelines get_by_stype_code get_by_pipeline_code get_by_process_node_type get_child_pipeline_by_process_code get_pipeline_by_parent".split(),
    "NativeLogin": "get_info get_login get_code get_project_code get_display_name get_login_groups get_login_group get_all_login_groups check_security".split(),
    "NativeLoginGroup": "get_info get_code get_pretty_name get_description get_login_group".split(),
    "NativeSObject": "get_info get_code get_search_key get_value".split(),
}

PROPERTIES = {
    "Project": ["definitions"],
    "SType": ["definitions"],
    "SearchResult": "items offset limit total has_more".split(),
    "QueueItem": ["id", "state"],
    "Definition": "code search_type view login xml".split(),
    "DefinitionElement": ["name"],
    "ResolvedDefinition": "search_type view xml".split(),
}
