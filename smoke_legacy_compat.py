"""Non-interactive smoke check for critical legacy public entry points."""

from __future__ import annotations

import importlib
import ast
import contextlib
import io
from pathlib import Path


LEGACY_UI_CLASSES = {
    "thlib.ui_classes.ui_main_classes": ("Ui_Main",),
    "thlib.ui_classes.ui_conf_classes": ("Ui_configuration_dialogWidget",),
    "thlib.ui_classes.ui_search_classes": (
        "Ui_searchWidget", "Ui_advancedSearchWidget",
    ),
    "thlib.ui_classes.ui_checkin_out_classes": ("Ui_checkInOutWidget",),
    "thlib.ui_classes.ui_commit_queue_classes": ("Ui_commitQueueWidget",),
    "thlib.ui_classes.ui_addsobject_classes": (
        "Ui_addTacticSobjectWidget", "Ui_linkSobjectsWidget",
    ),
    "thlib.ui_classes.ui_tasks_classes": ("Ui_tasksDockWidget",),
    "thlib.ui_classes.ui_notes_classes": (
        "Ui_notesWidget", "Ui_messageWidget",
    ),
    "thlib.ui_classes.ui_watch_folder_classes": (
        "Ui_projectWatchFoldersWidget", "Ui_repositoryEditorWidget",
    ),
    "thlib.ui_classes.ui_maya_dialogs_classes": (
        "Ui_importOptionsWidget", "Ui_openOptionsWidget",
        "Ui_referenceOptionsWidget",
    ),
    "thlib.ui_classes.ui_tactic_api_server_classes": ("Ui_TacticApiClient",),
    "thlib.ui_classes.ui_tactic_server_classes": ("Ui_TacticServer",),
}


def require(condition, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    launcher = importlib.import_module("launch")
    selected, forwarded = launcher._selected_ui(
        ["launch.py", "--ui", "legacy", "--example"]
    )
    require(selected == "legacy", "legacy launcher selection changed")
    require(forwarded == ["launch.py", "--example"], "launcher arguments changed")

    root = Path(__file__).parent
    standalone_tree = ast.parse(
        (root / "main_standalone.py").read_text(encoding="utf-8")
    )
    require(
        any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "startup"
            for node in standalone_tree.body
        ),
        "main_standalone.startup is unavailable",
    )

    try:
        environment = importlib.import_module("thlib.environment")
        tactic_classes = importlib.import_module("thlib.tactic_classes")
        search_classes = importlib.import_module(
            "thlib.ui_classes.ui_search_classes"
        )
        require(environment.env_inst.server_pool is not None, "server_pool is missing")
        require(environment.env_inst.local_pool is not None, "local_pool is missing")
        require(callable(tactic_classes.server_query), "server_query is unavailable")
        require(
            callable(search_classes.get_suggestion_filter),
            "legacy get_suggestion_filter import is unavailable",
        )
        for module_name, class_names in LEGACY_UI_CLASSES.items():
            module = importlib.import_module(module_name)
            for class_name in class_names:
                require(
                    callable(getattr(module, class_name, None)),
                    f"{module_name}.{class_name} is unavailable",
                )
    except ImportError as error:
        if "No Qt binding were found" not in str(error):
            raise
        print("Legacy Qt runtime imports: SKIPPED (no binding installed)")

    repository_tree = ast.parse(
        (root / "modern_ui" / "repository_sync.py").read_text(
            encoding="utf-8"
        )
    )
    repository_class = next(
        node for node in repository_tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "RepositorySyncController"
    )
    repository_api = {
        node.name for node in repository_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    required_queue_api = {
        "schedule_file_object", "is_all_downloads_done",
        "isHidden", "setHidden", "show", "hide",
    }
    missing = required_queue_api.difference(repository_api)
    require(not missing, f"repository queue API is missing: {sorted(missing)}")

    from thlib.pool import ThreadsPool
    from thlib.side.Qt import QtCore

    application = QtCore.QCoreApplication.instance()
    if application is None:
        application = QtCore.QCoreApplication([])
    retry_pool = ThreadsPool()
    retry_pool.start()
    calls = []
    events = []

    def retry_probe():
        calls.append(len(calls) + 1)
        if len(calls) == 1:
            raise ConnectionError("legacy retry probe")
        return "ok"

    worker = retry_pool.add_task(retry_probe)
    loop = QtCore.QEventLoop()
    worker.error.connect(lambda _error: events.append(worker.retry()))
    worker.result.connect(lambda _result: loop.quit())
    with contextlib.redirect_stdout(io.StringIO()):
        worker.start()
        QtCore.QTimer.singleShot(1500, loop.quit)
        loop.exec()
    retry_pool.exit()
    require(calls == [1, 2], "legacy worker.retry() did not rerun the task")
    require(events == [True], "legacy worker.retry() result changed")

    print("Legacy compatibility smoke check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
