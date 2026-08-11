"""Run after maya_client.start() from Maya's Script Editor."""

import tactic_handler_dcc.environment as thenv


def inspect_asset(search_type, code):
    sobjects, query_info = thenv.tc().get_sobjects_new(
        search_type=search_type,
        filters=[("code", code)],
        include_snapshots=False,
    )
    if not sobjects:
        return None

    sobject = next(iter(sobjects.values()))
    result = {
        "title": sobject.get_title(),
        "search_key": sobject.get_search_key(),
        "description": sobject.get_value("description"),
        "query_info": query_info,
        "snapshots": [],
    }
    processes = sobject.get_snapshots()
    publish = processes.get("publish")
    if not publish:
        return result
    context = publish.get_contexts().get("publish")
    if not context:
        return result
    for snapshot in context.get_versions().values():
        result["snapshots"].append({
            "version": snapshot.get_version(),
            "files": [
                {
                    "type": file_object.get_type(),
                    "path": file_object.get_full_abs_path(),
                    "web_path": file_object.get_full_web_path(),
                }
                for file_object in snapshot.get_files_objects()
            ],
        })
    return result
