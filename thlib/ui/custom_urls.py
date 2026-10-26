"""Open this server's configured page URLs in native workspace/layout windows."""
from copy import copy

from thlib.environment import env_server, env_inst
from .search_links import parse_custom_page_link


def open_custom_url(app, value):
    spec = parse_custom_page_link(value, str(env_server.get_server() or ''))
    services = getattr(app, '_table_services', None)
    if not spec or services is None:
        return False
    if spec['project'] not in env_inst.projects:
        app._notify(app.tr('Project is not available'))
        return True
    origin = app._current_project_code, app._bootstrap_cache_identity()
    generation = getattr(app, '_custom_url_generation', 0) + 1
    app._custom_url_generation = generation

    def resolve():
        from thlib import tactic_classes as tc
        server = copy(tc.server_start(project=spec['project']))
        server.set_project(spec['project'])
        result = server.execute_cmd('tactic.ui.panel.custom_url_cmd.CustomUrlCmd', dict(action='resolve',
            path=spec['path'], parameters=spec['parameters']))['info']
        if result.get('layoutView'):
            result['layout'] = server.execute_cmd('tactic.ui.table.CustomLayoutReadCmd', dict(
                view=result['layoutView'], search_key=result['options'].get('search_key', '')))['info']
        prepared = None
        if spec['project'] != origin[0]:
            project = env_inst.projects[spec['project']]
            prepared = app._prepare_project_selection(spec['project'], project.get_title() or spec['project'])
        return result, prepared

    def loaded(result):
        if (generation != app._custom_url_generation
                or origin != (app._current_project_code, app._bootstrap_cache_identity())):
            return
        target, prepared = result
        if prepared:
            app._apply_selected_project(*prepared)
        if target.get('layout'):
            services.customLayout.open_result(target['layout'], target['title'], 'custom-url:' + value)
            return
        records = [dict(column=target['filterField'], relation='=', value=target['filterValue'],
                        rowEnabled=True, operator='begin')] if target['filterField'] else []
        app._activate_saved_search_preset(dict(search_type=target['search_type'], view='custom-url:' + value,
            table_view=target['view'], view_mode=target['options'].get('view_mode') or 'table'),
            dict(title=target['title'], records=records))

    services._run(resolve, loaded)
    return True
