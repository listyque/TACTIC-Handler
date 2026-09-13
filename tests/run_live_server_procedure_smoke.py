"""Run guarded read-only server procedures against an isolated TACTIC project."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.support.tactic_test_project import load_manifest, validate_test_project


ENABLE_ENV = "TACTIC_RUN_LIVE_SERVER_SMOKE"
PROJECT_ENV = "TACTIC_TEST_PROJECT_CODE"


def main() -> int:
    if os.environ.get(ENABLE_ENV) != "1":
        print(f"Set {ENABLE_ENV}=1 to run the live server smoke", file=sys.stderr)
        return 2

    try:
        project_code = validate_test_project(
            os.environ.get(PROJECT_ENV, ""),
            load_manifest(),
            require_mutation_permission=False,
        )
        import thlib.tactic_classes as tc
        from thlib.environment import env_server

        if not env_server.get_server() or not env_server.get_ticket():
            raise RuntimeError("The selected server preset has no active ticket")
        server = tc.server_start(project="sthpw")
        if server.fast_ping() != "OK":
            raise RuntimeError("TACTIC fast_ping did not return OK")

        scope = [('project_code', project_code)]
        page = tc.get_task_workspace_page(scope, [], project_code, limit=2)
        filtered = tc.get_task_workspace_page(
            scope, [], project_code, limit=2,
            query={
                'filters': {'hasNotes': True}, 'quickFilters': {},
                'sort': 'object', 'group': 'process',
                'currentLogin': env_server.get_user(),
            },
        )
        if len(filtered['tasks']) > 2 or 'status' not in filtered['facets']:
            raise AssertionError('Filtered task page violates the bounded query contract')
        conversations = tc.get_chat_conversations() or {}
        profile = tc.get_user_profile_data(
            env_server.get_user(), project_code,
        ) or {}
        from thlib.ui.activity import JOURNAL_ACTIVITY_KINDS
        activity = tc.get_user_recent_activity(
            "", project_code=project_code, limit=2,
            kinds=JOURNAL_ACTIVITY_KINDS,
            logins=[env_server.get_user()],
        ) or {}
        updates = tc.get_server_updates(
            project_code=project_code,
            limit=2,
            include_activity=True,
            include_presence=True,
        ) or {}
        result = {
            "project": project_code,
            "procedures": {
                "task_workspace": {
                    "tasks": len(page.get("tasks") or []),
                    "parents": len(page.get("parents") or []),
                },
                "filtered_task_workspace": {
                    "tasks": len(filtered['tasks']),
                    "facets": sorted(filtered['facets']),
                },
                "chat_conversations": len(
                    conversations.get("conversations") or []
                ),
                "user_activity": len(activity.get("records") or []),
                "server_updates": sorted(updates),
            },
        }
    except Exception as error:
        print(
            f"[live-server-procedures] {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
