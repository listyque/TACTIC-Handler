import tactic_handler_dcc.environment as thenv


def checkin_current_scene(search_key, context="publish"):
    skey = thenv.tc().split_search_key(search_key)
    thenv.env_inst.ui_main.create_project_dock(
        skey["project_code"], False
    )
    checkin = thenv.env_inst.get_check_tree(
        project_code=skey["project_code"],
        tab_code="checkin_out",
        wdg_code=skey["pipeline_code"],
    )
    checkin.do_creating_ui()
    return checkin.checkin_from_maya(
        search_key, context, "Check-in from Maya"
    )
