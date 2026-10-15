from urllib.parse import parse_qs, urlsplit

from tactic_handler_api import get_api
from tactic_handler_dcc import maya as handler_maya


def save_current_scene_as_new_version():
    search_key = handler_maya.get_skey_from_scene() or ""
    context = parse_qs(urlsplit(search_key).query).get("context", [""])[0]
    runtime = handler_maya.runtime()
    if not search_key or not context:
        raise RuntimeError("The scene is not linked to a TACTIC object")
    if runtime is None or not runtime.connected:
        raise RuntimeError("TACTIC Handler is not connected to Maya")

    get_api().ui.checkin_from_maya(
        search_key,
        context,
        "Fast Save",
        runtime.client_id,
    ).wait()
    return True
