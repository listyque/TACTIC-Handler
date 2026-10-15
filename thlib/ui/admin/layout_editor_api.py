"""Use the installed layout-authoring API through native TACTIC RPC."""


def layout_editor_request(action: str, project_code: str, search_type: str, view: str,
                          source_id=None, xml: str = '', revision: str = '') -> str:
    import json
    from pyasm.biz import Project
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select the target project before editing layouts')
    if action not in ('read', 'preview', 'save'):
        raise ValueError('Unknown layout operation')
    from tactic_stream.server.widget_configuration import (
        read_widget_configuration, preview_widget_configuration, save_widget_configuration)
    if action == 'preview':
        result = preview_widget_configuration(search_type, view, source_id, xml, revision)
    elif action == 'save':
        result = save_widget_configuration(search_type, view, source_id, xml, revision)
    else:
        result = {'configuration': read_widget_configuration(search_type, view),
                  'sampleItems': [], 'sampleError': ''}
        try:
            from pyasm.search import Search, SearchKey
            from tactic_stream.server.result_items import read_result_items
            search = Search(search_type)
            search.add_limit(3)
            keys = [SearchKey.get_by_sobject(row, use_id=False) for row in search.get_sobjects()]
            if keys:
                result['sampleItems'] = read_result_items(search_type, keys)['items']
        except Exception as error:
            result['sampleError'] = str(error)
    return json.dumps(result, ensure_ascii=False, default=str)
