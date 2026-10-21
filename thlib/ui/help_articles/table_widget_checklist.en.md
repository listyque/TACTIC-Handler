---
group: Guide
icon: table
order: 96
---

# Table View: active widget checklist

[Table View / Columns Editor](table_view.en.md) · [B07](table_widgets_b07.en.md) · [Widget Database](widget_database.en.md)

Current as of 2026-10-21: 239 shipped XML/CG entries; 68 referenced adapted classes, **3 pending**, 30 excluded production dependencies, 3 explicitly unfinished. The complete catalogue contains 71 classes / 171 named aliases. DependencyLink now has a shared snapshot tree; ParentGroup and the two publish classes remain pending. Checkout currently accepts ordinary single files; sequence/UDIM and remaining options stay open. Registration does not certify every original option; stage 2/B07 remain open.

L01–L07 order: relationships/nested rows (8) → discussion/message/task (4) →
configured actions/layout (3) → files (7) → status/process (6) →
Gantt/timecard/hours (5) → service cells (7) and full B07 acceptance.
Each group requires an original scenario, XML/data, real operations,
permissions/errors/rollback, paired captures and EN/RU Help. Inspect dynamic
references while reading configs; clearly unfinished originals are excluded.

**The detailed lists below are the historical October 13–14 audit:** it covered
449 configurations including read-only local databases. Its old statuses and
invalid references are not the current execution order. Every confirmed mention,
including definitions, nested and scripted references, remains in scope.
See B07 above for current behavior. Bottom/group_bottom/total_summary and other
historical options need separate acceptance, beyond a generic editor.

L02 adapters reuse existing panels; see B07 above for XML and explicit limits.

## Invalid class reference: repair configuration (3)

### `Htactic.ui.table.HiddenRowElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/planner_right/element[instances]/display` — dynamic, title_icon

### `tacic.ui.widget.DiscussionWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/definition/element[discussion]/display` — sticky

### `tactic.ui.widget.DiscussionWdg`

References: 8.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[notes_popup]/display/cbjs_action`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/definition/element[discussion]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/artist/element[discussion]/display`

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

## Excluded: pyasm.prod (27)

### `pyasm.prod.web.RenderLinkTableElement`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\layer-conf.xml → config/definition/element[render_link]/display`

### `pyasm.prod.web.asset_info_wdg.AssetInfoWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/definition/element[info]/display`

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/asset_prod_notes/element[asset]/display`

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/shots_in_asset/element[info]/display` — width

### `pyasm.prod.web.asset_info_wdg.CondensedAssetInfoWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/summary_small/element[asset_info]/display` — css

### `pyasm.prod.web.asset_info_wdg.CondensedShotInfoWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/summary_small/element[shot]/display`

### `pyasm.prod.web.asset_info_wdg.ShotInfoWdg`

References: 8.

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/definition/element[shot]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/artist/element[shot]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/supe/element[shot]/display`

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `pyasm.prod.web.composite_wdg.CompLayerTableElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\composite-conf.xml → config/definition/element[comp_explore]/display`

### `pyasm.prod.web.composite_wdg.ExploreTableElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\layer-conf.xml → config/definition/element[explore]/display`

### `pyasm.prod.web.composite_wdg.LayerTableElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/composite/element[input_layers]/display`

### `pyasm.prod.web.frame_info_wdg.FrameRangeWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[frames]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/definition/element[frames]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/summary/element[frames]/display`

### `pyasm.prod.web.layout_summary_wdg.AssetsInShotWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/layout_summary/element[assigned assets]/display`

### `pyasm.prod.web.layout_summary_wdg.AssignedShotWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/shots_in_asset/element[assigned shots]/display`

### `pyasm.prod.web.layout_summary_wdg.TasksInSObjectWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/shots_in_asset/element[tasks]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/layout_summary/element[task breakdown]/display`

### `pyasm.prod.web.prod_input_wdg.AssetCheckboxWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/layout/element[prod_asset]/display` — persist_on_submit

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/set_items/element[update]/display`

### `pyasm.prod.web.prod_input_wdg.SObjectCheckboxWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/layout/element[select_instance]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/layout_left/element[select_shot]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/layout_right/element[select_parent]/display`

### `pyasm.prod.web.prod_input_wdg.ShotCheckboxWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\sequence-conf.xml → config/layout/element[prod_sequence]/display` — persist_on_submit

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/layout/element[prod_shot]/display` — persist_on_submit

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/task_planner/element[prod_shot]/display` — persist_on_submit

### `pyasm.prod.web.prod_table_element_wdg.BinTableElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\submission-conf.xml → config/definition/element[bin]/display`

### `pyasm.prod.web.prod_table_element_wdg.ThumbPublishWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\sequence-conf.xml → config/table_episode/element[images]/display`

### `pyasm.prod.web.prod_wdg.SnapshotInfoWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/log/element[code]/display`

### `pyasm.prod.web.render_wdg.RenderTableElementWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/render/element[render]/display`

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[render]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\DEFAULT-conf.xml → config/definition/element[render]/display`

### `pyasm.prod.web.shot_instance_adder_wdg.NumSequenceInstanceWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\sequence-conf.xml → config/layout/element[number_of_instances]/display`

### `pyasm.prod.web.shot_instance_adder_wdg.NumTasksWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/task_planner/element[number_of_tasks]/display`

### `pyasm.prod.web.sobject_planner_wdg.NumSObjectInstancesWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/planner_left/element[number_of_instances]/display`

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/planner_right/element[number_of_instances]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\login_group-conf.xml → config/planner_right/element[number_of_instances]/display`

### `pyasm.prod.web.statistics_wdg.EpisodeCompletionWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\sequence-conf.xml → config/completion/element[completion]/display` — width

### `pyasm.prod.web.statistics_wdg.FrameCompletionWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\sequence-conf.xml → config/completion/element[frame_completion]/display`

### `pyasm.prod.web.submission_wdg.SubmissionDataTableElement`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\submission-conf.xml → config/definition/element[info]/display`

- `src\tactic_stream\config\search_type\widget\prod\submission-conf.xml → config/table/element[info]/display`

- `src\tactic_stream\config\search_type\widget\prod\submission-conf.xml → config/client/element[info]/display`

### `pyasm.prod.web.version_wdg.LatestVersionWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/set_items/element[latest ver]/display`

### `pyasm.prod.web.version_wdg.SessionVersionWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/set_items/element[session ver]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/session_items/element[session ver]/display`

## Needs source/example/implementation (58)

### `pyasm.widget.dependency_wdg.DependencyLink`

References: 2.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[dependency]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\DEFAULT-conf.xml → config/definition/element[dependency]/display`

### `pyasm.widget.discussion_wdg.DiscussionWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/asset_prod_notes/element[notes]/display` — append_setting, include_submission, scroll

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/preprod_notes/element[notes]/display` — include_submission, scroll, setting

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/prod_notes/element[notes]/display` — append_setting, include_submission, scroll

### `pyasm.widget.gantt_wdg.GanttWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\login-conf.xml → config/schedule/element[gantt]/display` — handlers

### `pyasm.widget.my_tactic_summary_wdg.MyTacticSummaryWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\project-conf.xml → config/mytactic/element[summary]/display`

### `pyasm.widget.parallel_status.ParallelStatusEditWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/edit/element[task_status]/display`

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_edit_definition/element[task_status]/display`

### `pyasm.widget.parallel_status.ParallelStatusWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/summary_small/element[task_status]/display` — bar_height, label_format, report

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[task_status]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/summary_small/element[task_status]/display` — bar_height, label_format, report

### `pyasm.widget.sobject_browser_wdg.SObjectConnectionElement`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\art_reference-conf.xml → config/definition/element[related]/display`

### `pyasm.widget.statistic_wdg.TaskCompletionWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/summary/element[completion]/display` — width

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/completion/element[task_completion]/display`

### `pyasm.widget.table_element_wdg.AuxDataWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/set_items/element[instance]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/session_items/element[instance]/display`

### `pyasm.widget.table_element_wdg.CheckboxColWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\prod\art_reference-conf.xml → config/list/element[select_key]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/list/element[select_key]/display`

### `pyasm.widget.table_element_wdg.FileAppendLinkTableElement`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[append]/display`

### `pyasm.widget.table_element_wdg.HiddenRowToggleWdg`

References: 25.

- `src\tactic_stream\config\search_type\widget\config\pipeline-conf.xml → config/definition/element[pipeline_hidden]/display` — dynamic_class, search_type, show_gear, show_insert, show_row_select, show_search_limit, view

- `src\tactic_stream\config\search_type\widget\config\plugin-conf.xml → config/definition/element[manifest_hidden]/display` — dynamic_class, search_type, show_gear, show_insert, show_row_select, show_search_limit, view

- `src\tactic_stream\config\search_type\widget\config\trigger-conf.xml → config/definition/element[data_hidden]/display` — dynamic_class, search_type, show_gear, show_insert, show_row_select, show_search_limit, view

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `pyasm.widget.table_element_wdg.PublishTableElement`

References: 2.

- `src\tactic_stream\config\search_type\widget\prod\camera-conf.xml → config/table/element[publish]/display`

- `src\tactic_stream\config\search_type\widget\prod\cut_sequence-conf.xml → config/table/element[publish]/display`

### `pyasm.widget.table_element_wdg.RenderLinkTableElement`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[render]/display`

### `pyasm.widget.table_element_wdg.SearchTypeElementWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\sthpw\DEFAULT-conf.xml → config/definition/element[search_type]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\note-conf.xml → config/definition/element[search_type]/display` — filename

### `pyasm.widget.table_element_wdg.SimpleTableElementWdg`

References: 5.

- `src\tactic_stream\config\search_type\widget\sthpw\note-conf.xml → config/definition/element[status]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\note-conf.xml → config/definition/element[access]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\search_object-conf.xml → config/definition/element[search_type]/display`

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `pyasm.widget.table_element_wdg.SubmissionLinkTableElement`

References: 5.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/definition/element[submit]/display`

- `src\tactic_stream\config\search_type\widget\prod\sequence-conf.xml → config/definition/element[submit]/display`

- `src\tactic_stream\config\search_type\widget\prod\sequence-conf.xml → config/table_episode/element[submit]/display`

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `pyasm.widget.table_element_wdg.UpdateWdg`

References: 6.

- `src\tactic_stream\config\search_type\widget\config\naming-conf.xml → config/definition/element[update]/display` — delete

- `src\tactic_stream\config\search_type\widget\prod\layer-conf.xml → config/definition/element[update]/display` — delete

- `src\tactic_stream\config\search_type\widget\prod\render-conf.xml → config/definition/element[update]/display` — insert

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `pyasm.widget.table_element_wdg.WikiElementWdg`

References: 9.

- `src\tactic_stream\config\search_type\widget\config\custom_script-conf.xml → config/definition/element[script]/display`

- `src\tactic_stream\config\search_type\widget\prod\cut_sequence-conf.xml → config/table/element[description]/display`

- `src\tactic_stream\config\search_type\widget\prod\plate-conf.xml → config/table/element[description]/display`

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `pyasm.widget.task_wdg.SObjectTaskTableElement`

References: 8.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/definition/element[task]/display` — bid_edit, simple_date, width

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/supe/element[task]/display` — bid_edit, supe, width

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[task]/display` — bid_edit, simple_date, width

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `pyasm.widget.task_wdg.TaskParentSpacingTableElement`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\task-conf.xml → config/definition/element[context]/display`

### `pyasm.widget.timecard_wdg.TimecardInfoTableElement`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\timecard-conf.xml → config/definition/element[timecard info]/display`

### `pyasm.widget.timecard_wdg.WeekTableElement`

References: 2.

- `src\tactic_stream\config\search_type\widget\sthpw\DEFAULT-conf.xml → config/definition/element[weekly]/display` — width

- `src\tactic_stream\config\search_type\widget\sthpw\timecard-conf.xml → config/definition/element[weekly]/display` — width

### `tactic.ui.app.message_wdg.MessageTableElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\message_log-conf.xml → config/definition/element[message]/display`

### `tactic.ui.app.search_type_element_wdg.SearchTypeHasTableElementWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\sthpw\search_object-conf.xml → config/definition/element[has_table]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\search_type-conf.xml → config/definition/element[has_table]/display`

### `tactic.ui.cgapp.loader_element_wdg.LoaderElementWdg`

References: 6.

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/definition/element[input]/display` — mode, search_type

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/definition/element[output]/display` — mode, search_type

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/definition/element[input]/display` — mode, search_type

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.cgapp.publish_element_wdg.PublishElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\shot_instance-conf.xml → config/definition/element[publish]/display` — search_type

### `tactic.ui.input.process_group_select_wdg.LoginTableElementWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\sthpw\task-conf.xml → config/definition/element[assigned]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\task-conf.xml → config/definition/element[supervisor]/display`

### `tactic.ui.panel.security_manager_wdg.SecurityManagerButtonWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\login_group-conf.xml → config/definition/element[global_rules]/display`

### `tactic.ui.table.button_wdg.ButtonElementWdg`

References: 26.

- `src\tactic_stream\config\search_type\widget\config\client_trigger-conf.xml → config/definition/element[edit]/display` — cbjs_action, icon

- `src\tactic_stream\config\search_type\widget\config\plugin-conf.xml → config/definition/element[create]/display` — cbjs_action

- `src\tactic_stream\config\search_type\widget\config\plugin-conf.xml → config/definition/element[uninstall]/display` — cbjs_action, icon

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.custom_layout_element_wdg.CustomLayoutElementWdg`

References: 11.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[asset_panel_wdg]/display` — include_mako, view

- `cg-template:None/columns.thumb_view → config/columns.thumb_view/html/element[preview]/display` — icon_size, include_mako, show_resize_scroll, view

- `cg-template:sthpw/task/definition → config/definition/element[expand]/display/dynamic_class`

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.drop_element_wdg.DropElementWdg`

References: 10.

- `src\tactic_stream\config\search_type\widget\config\plugin-conf.xml → config/definition/element[drop_zone]/display`

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[drop]/display`

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[drop_item]/display`

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.gantt_element_wdg.GanttElementWdg`

References: 11.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[task_schedule]/display` — options

- `src\tactic_stream\config\search_type\widget\prod\sequence-conf.xml → config/definition/element[shot_task_schedule]/display` — options

- `src\tactic_stream\config\search_type\widget\sthpw\project-conf.xml → config/definition/element[task_schedule]/display` — options

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.group_element_wdg.ParentGroupTableElementWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\sthpw\DEFAULT-conf.xml → config/definition/element[parent]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\note-conf.xml → config/definition/element[parent]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\work_hour-conf.xml → config/definition/element[parent]/display`

### `tactic.ui.table.hidden_row_element_wdg.HiddenRowElementWdg`

References: 52.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[history]/display` — dynamic_class, icon

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[checkin]/display` — dynamic_class

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[general_checkin_simple]/display` — dynamic_class

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.hidden_row_element_wdg.RowAddElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[show_related]/display`

### `tactic.ui.table.preference_wdg.PreferenceDescriptionWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\pref_list-conf.xml → config/user/element[description]/display`

### `tactic.ui.table.preference_wdg.PreferenceEditWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\pref_list-conf.xml → config/user/element[value]/display`

### `tactic.ui.table.project_wdg.ProjectTemplateUpdateWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\project-conf.xml → config/definition/element[template_update]/display` — icon

### `tactic.ui.table.project_wdg.ProjectWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\project-conf.xml → config/definition/element[project_info]/display`

### `tactic.ui.table.related_element_wdg.RelatedElementWdg`

References: 2.

- `cg-template:cg/assets/definition → config/definition/element[delete]/display`

- `cg_test.db:cg/assets/definition/WIDGET_CONFIG00101 → config/definition/element[delete]/display`

### `tactic.ui.table.snapshot_element_wdg.SnapshotFileElementWdg`

References: 2.

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[file]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[history]/display`

### `tactic.ui.table.snapshot_element_wdg.SnapshotLockedElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[is_locked]/display`

### `tactic.ui.table.sobject_detail_wdg.SObjectTaskStatusElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[task_detail]/display`

### `tactic.ui.table.sobject_summary_wdg.SObjectSummaryElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[summary]/display`

### `tactic.ui.table.statistic_wdg.MilestoneCompletionWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\milestone-conf.xml → config/definition/element[completion]/display` — width

### `tactic.ui.table.statistic_wdg.TaskDaysDueElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\task-conf.xml → config/definition/element[days_due]/display`

### `tactic.ui.table.statistic_wdg.TaskGroupCompletionWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[group_completion]/display` — width

### `tactic.ui.table.subcontext_wdg.ProcessElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\task-conf.xml → config/definition/element[process]/display`

### `tactic.ui.table.subcontext_wdg.SubContextElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\task-conf.xml → config/definition/element[subcontext]/display`

### `tactic.ui.table.table_element_wdg.CheckoutButtonElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[checkout]/display`

### `tactic.ui.table.table_element_wdg.GeneralPublishElementWdg`

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\art_reference-conf.xml → config/definition/element[general_publish]/display` — preview

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[general_publish]/display` — preview

- `src\tactic_stream\config\search_type\widget\prod\script-conf.xml → config/definition/element[general_publish]/display` — preview

### `tactic.ui.table.table_element_wdg.NotificationTriggerElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\notification-conf.xml → config/definition/element[email_test]/display`

### `tactic.ui.table.table_element_wdg.RecipientElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\notification_log-conf.xml → config/definition/element[recipients]/display`

### `tactic.ui.table.task_element_wdg.TaskSummaryElementWdg`

References: 6.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[task_status_summary]/display`

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[task_summary_minimal]/display` — mode

- `cg-template:sthpw/task/definition → config/definition/element[task_status_summary]/display` — mode

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.task_element_wdg.WorkElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\task-conf.xml → config/definition/element[work]/display` — icon, transfer_mode

### `tactic.ui.table.work_hours_element_wdg.WorkHoursElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\task-conf.xml → config/definition/element[work_hours]/display`

### `tactic.ui.widget.misc_input_wdg.TaskStatusElementWdg`

References: 4.

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[status]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\task-conf.xml → config/definition/element[status]/display`

- `cg-template:sthpw/task/definition → config/definition/element[status]/display` — edit_scope

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

## Current Handler scenario implemented; legacy options remain (18)

### `pyasm.widget.file_wdg.ThumbWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 52.

- `src\tactic_stream\config\search_type\widget\prod\art_reference-conf.xml → config/definition/element[images]/display` — filename, icon_size, original

- `src\tactic_stream\config\search_type\widget\prod\art_reference-conf.xml → config/list/element[snapshot]/display` — icon_size

- `src\tactic_stream\config\search_type\widget\prod\asset-conf.xml → config/summary_small/element[snapshot]/display` — icon_size

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `pyasm.widget.table_element_wdg.ArrayTableElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\DEFAULT-conf.xml → config/definition/element[project_code]/display`

### `pyasm.widget.table_element_wdg.XmlWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 13.

- `src\tactic_stream\config\search_type\widget\config\pipeline-conf.xml → config/definition/element[pipeline]/display`

- `src\tactic_stream\config\search_type\widget\config\plugin-conf.xml → config/definition/element[manifest]/display`

- `src\tactic_stream\config\search_type\widget\config\url-conf.xml → config/definition/element[widget]/display`

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.common.base_table_element_wdg.SimpleTableElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 26.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[color]/display` — css_background

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/definition/element[status]/display`

- `src\tactic_stream\config\search_type\widget\prod\shot-conf.xml → config/definition/element[scan_status]/display`

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.delete_element_wdg.DeleteElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[delete]/display`

### `tactic.ui.table.explorer_wdg.ExplorerElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[explorer]/display`

### `tactic.ui.table.expression_element_wdg.ExpressionElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 52.

- `src\tactic_stream\config\search_type\widget\config\pipeline-conf.xml → config/tool/element[num_processes]/display` — expression

- `src\tactic_stream\config\search_type\widget\config\process-conf.xml → config/definition/element[search_type]/display` — calc_mode, expression

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[pipeline]/display` — expression

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.format_element_wdg.FormatElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 24.

- `src\tactic_stream\config\search_type\widget\config\naming-conf.xml → config/definition/element[latest_versionless]/display` — format

- `src\tactic_stream\config\search_type\widget\config\naming-conf.xml → config/definition/element[current_versionless]/display` — format

- `src\tactic_stream\config\search_type\widget\config\naming-conf.xml → config/definition/element[manual_version]/display` — format

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.json_element_wdg.JsonElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 2.

- `src\tactic_stream\config\search_type\widget\config\process-conf.xml → config/definition/element[workflow]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\sync_job-conf.xml → config/definition/element[data]/display`

### `tactic.ui.table.link_element_wdg.LinkElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 2.

- `cg-template:cg/scenes/definition → config/definition/element[detail]/display`

- `cg_test.db:cg/scenes/definition/WIDGET_CONFIG00036 → config/definition/element[detail]/display`

### `tactic.ui.table.metadata_element_wdg.MetadataElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[metadata]/display`

### `tactic.ui.table.snapshot_element_wdg.SnapshotVersionElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[version]/display`

### `tactic.ui.table.sobject_detail_wdg.SObjectDetailElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 3.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[detail]/display`

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[expand]/display`

- `src\tactic_stream\config\search_type\widget\sthpw\DEFAULT-conf.xml → config/definition/element[detail]/display` — use_parent

### `tactic.ui.table.sobject_summary_wdg.SObjectFilesElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[file_list]/display`

### `tactic.ui.table.statistic_wdg.TaskCompletionWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 1.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[completion]/display` — width

### `tactic.ui.table.table_element_wdg.CheckinButtonElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 4.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[general_checkin]/display` — width

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[general_checkin]/display` — mode, width

- `cg-template:cg/scenes/definition → config/definition/element[general_checkin]/display` — lock_process, mode, process, show_context, show_links, sobject_mode, subcontext, transfer_mode, width

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.table.task_element_wdg.TaskElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 14.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[task_pipeline_panels]/display` — bg_color, edit, edit_assigned, edit_status, layout, show_assigned, show_dates, show_filler_tasks, status_color

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[task_pipeline_vertical]/display` — edit, edit_assigned, edit_status, layout, show_assigned, show_dates, show_filler_tasks, status_color

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[task_pipeline_report]/display` — bg_color, edit, edit_assigned, edit_status, layout, show_assigned, show_dates

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

### `tactic.ui.widget.discussion_wdg.DiscussionElementWdg`

- [x] Source and inheritance

- [x] Values and errors comparison

- [x] TH/Stream typed transport

- [x] Paired TH/Stream captures

- [x] XML example and EN/RU Help

References: 12.

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[forum]/display`

- `src\tactic_stream\config\search_type\widget\prod\DEFAULT-conf.xml → config/default_definition/element[notes]/display`

- `src\tactic_stream\config\search_type\widget\prod\submission-conf.xml → config/definition/element[notes]/display` — process

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

## Input widget / compatible table alias; separate form contract (1)

### `pyasm.widget.input_wdg.TextWdg`

References: 66.

- `src\tactic_stream\config\search_type\widget\config\naming-conf.xml → config/edit_definition/element[snapshot_type]/display` — hint

- `src\tactic_stream\config\search_type\widget\config\process-conf.xml → config/edit_definition/element[subcontext_options]/display` — hint

- `src\tactic_stream\config\search_type\widget\config\prod_setting-conf.xml → config/edit/element[key]/display` — hint, size

All locations/options are listed in the HTML/CSV/JSON checklist under reports/table-view-2026-10-13.

## Excluded: unfinished source (1)

### `tactic.ui.table.snapshot_element_wdg.SnapshotServerElementWdg`

References: 1.

- `src\tactic_stream\config\search_type\widget\sthpw\snapshot-conf.xml → config/definition/element[server]/display`
