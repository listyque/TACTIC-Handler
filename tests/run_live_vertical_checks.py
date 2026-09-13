"""Opt-in read-only live checks for the documented user workflows.

The command never creates or deletes data. Mutation scenarios belong only to the
guarded isolated-project seeder described in docs/tactic_test_project.md.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.support.tactic_test_project import (
    load_manifest, validate_test_project,
)
from tests.support.vertical_workflows import vertical_names


ENABLE_ENV = "TACTIC_RUN_LIVE_VERTICALS"
PROJECT_ENV = "TACTIC_TEST_PROJECT_CODE"
SEARCH_TYPE_ENV = "TACTIC_TEST_SEARCH_TYPE"


def _require_live_target() -> tuple[str, str]:
    if os.environ.get(ENABLE_ENV) != "1":
        raise RuntimeError(f"Set {ENABLE_ENV}=1 to run live checks")
    project_code = validate_test_project(
        os.environ.get(PROJECT_ENV, ""), load_manifest(),
        require_mutation_permission=False,
    )
    search_type = str(os.environ.get(SEARCH_TYPE_ENV) or "").strip()
    return project_code, search_type


def _bootstrap(project_code: str):
    import thlib.tactic_classes as tc
    from thlib.environment import env_server

    if not env_server.get_server() or not env_server.get_ticket():
        raise RuntimeError("The selected server preset has no active ticket")
    server = tc.server_start(project="sthpw")
    if server.fast_ping() != "OK":
        raise RuntimeError("TACTIC fast_ping did not return OK")
    projects = tc.get_all_projects_and_logins(force=True)
    if project_code not in projects:
        raise RuntimeError(f"Test project is unavailable: {project_code}")
    return tc, projects[project_code]


def run(vertical: str) -> dict:
    project_code, search_type = _require_live_target()
    tc, project = _bootstrap(project_code)
    result = {"vertical": vertical, "project": project_code}

    if vertical == "login_configuration":
        from thlib.environment import env_server, env_tactic
        repositories = env_tactic.get_base_dirs(force=True) or {}
        result.update({
            "login": str(env_server.get_user() or ""),
            "preset": str(env_server.get_cur_srv_preset() or ""),
            "repositories": len(repositories),
        })
    elif vertical == "navigation_search":
        if not search_type:
            raise RuntimeError(f"Set {SEARCH_TYPE_ENV} for search checks")
        records, page_info = tc.get_sobjects(
            search_type, project_code=project_code, limit=2,
            include_snapshots=True, include_total_count=True,
        )
        result.update({
            "records": len(records or {}),
            "total": int((page_info or {}).get("total_sobjects_count") or 0),
        })
    elif vertical == "tasks_notes_work_hours":
        page = tc.get_task_workspace_page([], [], project_code, limit=5)
        result.update({
            "tasks": len(page["tasks"]),
            "parents": len(page["parents"]),
            "total": int(page.get("total") or 0),
        })
    elif vertical == "checkin_files":
        snapshots = tc.server_query(
            [], "sthpw/snapshot", project=project_code, limit=2,
        )
        result["snapshots"] = len(snapshots or [])
    elif vertical == "messages_users_activity":
        from thlib.environment import env_server
        from thlib.ui.activity import JOURNAL_ACTIVITY_KINDS
        conversations = tc.get_chat_conversations() or {}
        profile = tc.get_user_profile_data(
            env_server.get_user(), project_code,
        ) or {}
        activity = tc.get_user_recent_activity(
            "", project_code=project_code, limit=5,
            kinds=JOURNAL_ACTIVITY_KINDS,
            logins=[env_server.get_user()],
        ) or {}
        updates = tc.get_server_updates(
            project_code=project_code, limit=5,
            include_activity=True, include_presence=True,
        ) or {}
        result.update({
            "conversations": len(conversations.get("conversations") or []),
            "activity": len(activity.get("records") or []),
            "updateKeys": sorted(updates),
        })
    elif vertical == "handler_server_dcc":
        # The local protocol is exercised by the regular vertical suite. A live
        # TACTIC connection is intentionally irrelevant to thin-client routing.
        result["localProtocol"] = True
    else:
        raise KeyError(vertical)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("vertical", choices=vertical_names())
    arguments = parser.parse_args(argv)
    try:
        result = run(arguments.vertical)
    except Exception as error:
        print(f"[live:{arguments.vertical}] {error}", file=sys.stderr)
        return 1
    print(f"[live:{arguments.vertical}] {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
