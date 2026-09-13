from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PySide6.QtCore import QUrl

from thlib.ui.models import ProjectModel
from thlib.ui.project_editor import ProjectEditorController


class _LocalPreview:
    def __init__(self, path: Path) -> None:
        self.path = path

    def get_full_abs_path(self):
        return str(self.path)

    def is_local_current(self):
        return True


class _SourceFile:
    def __init__(self, web, icon) -> None:
        self.web = web
        self.icon = icon
        self.web_calls = 0
        self.icon_calls = 0

    def get_web_preview(self):
        self.web_calls += 1
        return self.web

    def get_icon_preview(self):
        self.icon_calls += 1
        return self.icon


class _Snapshot:
    def __init__(self, source) -> None:
        self.source = source

    def get_files_objects(self, group_by=None):
        return {"icon": [self.source]}

    def get_previewable_files_objects(self):
        return [self.source]


class _Context:
    def __init__(self, source) -> None:
        self.snapshot = _Snapshot(source)
        self.versionless = {"latest": self.snapshot}
        self.versions = {}

    def get_versionless(self):
        return self.versionless

    def get_versions(self):
        return self.versions


class _Process:
    def __init__(self, source) -> None:
        self.context = _Context(source)

    def get_contexts(self):
        return {"icon": self.context}


class _Project:
    def __init__(
        self, code, *, retired=False, template=False, builtin=False,
        source=None, category="Production", project_type="prod",
    ) -> None:
        self.code = code
        self.info = {
            "code": code,
            "name": code.title(),
            "category": category,
            "type": project_type,
            "status": "server status",
            "s_status": "retired" if retired else "",
            "is_template": template,
            "__builtin__": builtin,
            "description": f"Description for {code}",
            "__search_key__": f"sthpw/project?code={code}",
        }
        self.process = _Process(source) if source is not None else None
        self.updated = {}
        self.commits = 0

    def get_code(self):
        return self.code

    def get_title(self):
        return self.info["name"]

    def get_info(self):
        return self.info

    def get_type(self):
        return self.info["type"]

    def is_template(self):
        return self.info["is_template"]

    def is_builtin(self):
        return self.info["__builtin__"]

    def get_process(self, name):
        return self.process if self.process is not None and name == "icon" else None

    def get_all_processes(self):
        return {"icon": self.process} if self.process is not None else {}

    def get_search_key(self):
        return self.info["__search_key__"]

    def set_value(self, key, value):
        self.updated[key] = value

    def commit(self):
        self.info.update(self.updated)
        self.updated.clear()
        self.commits += 1


class _Server:
    def __init__(self) -> None:
        self.retired = []
        self.reactivated = []

    def retire_sobject(self, key):
        self.retired.append(key)
        return {"s_status": "retired"}

    def reactivate_sobject(self, key):
        self.reactivated.append(key)
        return {"s_status": ""}


class ProjectCatalogTests(unittest.TestCase):
    def setUp(self):
        from thlib.environment import env_mode

        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, "current_path", directory))

    def test_unfiltered_project_choices_ignore_chooser_filters_and_preview_loading(self):
        from PySide6.QtTest import QSignalSpy

        projects = [_Project('active'), _Project('archived', retired=True),
                    _Project('template', template=True), _Project('admin', builtin=True),
                    _Project('sthpw', builtin=True)]
        model = ProjectModel()
        changed = QSignalSpy(model.projects_changed)
        with patch.object(model, 'preview_for', side_effect=AssertionError('No preview work')):
            model.replace(projects)
            self.assertEqual(model.allProjects, [
                {'projectCode': project.code, 'title': project.info['name']} for project in projects])
            self.assertEqual(model.visibleCount, 1)
            model.setShowBuiltins(True)
            model.setShowTemplates(True)
            model.setShowRetired(True)
            self.assertEqual(len(model.allProjects), 5)
            self.assertEqual(changed.count(), 1)
            projects[0].info['name'] = 'Renamed project'
            model.replace(projects)
            self.assertEqual(model.allProjects[0]['title'], 'Renamed project')
            model.replace([])
            self.assertEqual(model.allProjects, [])
            self.assertEqual(changed.count(), 3)

    def test_lifecycle_filters_hide_optional_project_categories_by_default(self):
        active = _Project("active")
        retired = _Project("retired", retired=True)
        template = _Project("template", template=True)
        builtin = _Project("admin", builtin=True, category="System")
        model = ProjectModel()
        model.replace([active, retired, template, builtin])

        self.assertEqual(model.totalCount, 4)
        self.assertFalse(model.showRetired)
        self.assertFalse(model.showTemplates)
        self.assertFalse(model.showBuiltins)
        self.assertEqual(model.visibleCount, 1)
        self.assertEqual(model.retiredCount, 1)
        self.assertEqual(model.templateCount, 1)
        self.assertEqual(model.builtinCount, 1)
        self.assertEqual(
            [project.get_code() for project in model._entries],
            ["active"],
        )

        model.setShowRetired(True)
        model.setShowTemplates(True)
        model.setShowBuiltins(True)
        self.assertEqual(model.visibleCount, 4)
        model.setShowBuiltins(False)
        self.assertEqual(
            [project.get_code() for project in model._entries],
            ["active", "retired", "template"],
        )

        details = model.details(retired)
        self.assertTrue(details["isRetired"])
        self.assertFalse(details["isActive"])
        self.assertEqual(details["systemStatus"], "retired")
        self.assertEqual(details["status"], "server status")

    def test_large_web_preview_is_preferred_over_icon(self):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            web = directory / "project_web.jpg"
            icon = directory / "project_icon.png"
            web.write_bytes(b"web")
            icon.write_bytes(b"icon")
            source = _SourceFile(_LocalPreview(web), _LocalPreview(icon))
            project = _Project("preview", source=source)
            model = ProjectModel()

            result = model.preview_for(project)

            self.assertEqual(result, QUrl.fromLocalFile(str(web.resolve())).toString())
            self.assertEqual(source.web_calls, 1)
            self.assertEqual(source.icon_calls, 0)

    def test_project_editor_uses_native_commit_and_retire_api(self):
        project = _Project("editable")
        server = _Server()
        values = {
            "name": "Edited",
            "category": "Animation",
            "type": "production",
            "description": "Edited description",
            "is_template": True,
        }

        with patch("thlib.tactic_classes.server_start", return_value=server):
            result = ProjectEditorController._save_project(
                project, values, False, True
            )

        self.assertIs(result, project)
        self.assertEqual(project.commits, 1)
        self.assertEqual(project.info["name"], "Edited")
        self.assertTrue(project.info["is_template"])
        self.assertEqual(server.retired, [project.get_search_key()])
        self.assertEqual(project.info["s_status"], "retired")

    def test_core_project_api_keeps_builtin_projects(self):
        from thlib import tactic_classes as tc

        payload = {
            "projects": [
                {"code": "admin", "name": "Admin",
                 "__builtin__": True, "__snapshots__": []},
                {"code": "sthpw", "name": "TACTIC",
                 "__builtin__": True, "__snapshots__": []},
                {"code": "production", "name": "Production",
                 "__builtin__": False, "__snapshots__": []},
            ],
            "logins": [],
            "login_groups": [],
            "login_in_groups": [],
        }
        with (
            patch.object(
                tc, "execute_procedure_serverside", return_value=payload
            ),
            patch.object(tc, "env_write_config"),
            patch.object(tc.env_inst, "projects", {}),
            patch.object(tc.env_inst, "logins", {}),
            patch.object(
                tc.env_inst, "get_current_login", return_value="artist"
            ),
        ):
            projects = tc.get_all_projects_and_logins(force=True)

        self.assertEqual(
            list(projects), ["admin", "sthpw", "production"]
        )
        self.assertTrue(projects["admin"].is_builtin())
        self.assertTrue(projects["sthpw"].is_builtin())

    def test_project_preview_uses_normal_versionless_commit_queue_path(self):
        class Checkin:
            def __init__(self):
                self.calls = []

            def prepare_external_checkin(self, **kwargs):
                self.calls.append(kwargs)

        project = _Project("editable")
        checkin = Checkin()
        refreshed = []
        notifications = []
        controller = ProjectEditorController(
            lambda: {
                "project": project,
                "refresh": refreshed.append,
            },
            checkin,
            notifications.append,
        )
        controller._preview_path = "D:/previews/project.png"
        saved = []
        controller.saved.connect(saved.append)

        controller._save_finished(project)

        self.assertEqual(refreshed, [project])
        self.assertEqual(saved, ["editable"])
        self.assertEqual(len(checkin.calls), 1)
        call = checkin.calls[0]
        self.assertEqual(call["context"], "icon")
        self.assertTrue(call["update_versionless"])
        self.assertTrue(call["queue_when_ready"])
        self.assertNotIn("keep_file_name", call)
        self.assertEqual(controller.previewPath, "")


if __name__ == "__main__":
    unittest.main()
