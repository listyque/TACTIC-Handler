import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal

from thlib.environment import env_inst
from thlib.ui.workspace_layout_presets import (
    WORKSPACE_LAYOUT_CATEGORY,
    WorkspaceLayoutPresetController,
    layout_configuration_from_xml,
    layout_configuration_xml,
)
from thlib.ui.models import NavigationModel
from thlib.ui.sidebar_editor import SidebarEditorController
from thlib.ui.workspace_models.docks import DockPanelModel


class _Application(QObject):
    project_changed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.current_project_code = "demo"
        self.notifications = []
        self.debug_log = None

    def _notify(self, message):
        self.notifications.append(str(message))


class _Users(QObject):
    stateChanged = Signal()
    canManageUsers = True


class _Views:
    def __init__(self, records):
        self.config_dict = records


class _Project:
    def __init__(self, records):
        self.views = _Views(records)

    def get_config_views(self):
        return self.views


class _Server:
    def __init__(self, records):
        self.records = records
        self.next_code = 10

    def query(self, search_type, filters, columns=None):
        assert search_type == "config/widget_config"
        del columns
        return [
            dict(record) for record in self.records
            if all(str(record.get(key) or "") == str(value or "")
                   for key, value in filters)
        ]

    def insert(self, search_type, data, triggers=True):
        assert search_type == "config/widget_config"
        assert triggers
        self.next_code += 1
        created = {**data, "code": f"CONFIG{self.next_code:04d}"}
        self.records.append(created)
        return dict(created)

    def build_search_key(self, search_type, code, project_code=None):
        assert search_type == "config/widget_config"
        assert project_code == "demo"
        return code

    def insert_update(self, search_key, data, triggers=True):
        assert triggers
        record = next(
            row for row in self.records if row.get("code") == search_key
        )
        record.update(data)

    def delete_sobject(self, search_key):
        self.records[:] = [
            row for row in self.records
            if row.get("code") != search_key
        ]


def _preset_record(view, title, layout, code="CONFIG0001"):
    return {
        "code": code,
        "search_type": "SideBarWdg",
        "category": WORKSPACE_LAYOUT_CATEGORY,
        "view": view,
        "title": title,
        "login": "",
        "config": layout_configuration_xml(layout, view),
    }


def _controller(records, dock_model):
    application = _Application()
    project = _Project(records)
    projects = {"demo": project}
    with patch.object(env_inst, "projects", projects):
        controller = WorkspaceLayoutPresetController(
            application, _Users(), dock_model,
        )
    controller._current_project = lambda: ("demo", project)
    return application, project, controller


class WorkspaceLayoutPresetTests(unittest.TestCase):
    @staticmethod
    def _sidebar_controller(records):
        registry = SimpleNamespace(register=lambda *_args: None)
        application = SimpleNamespace(
            _registry=registry,
            navigation_model=NavigationModel(),
        )
        users = SimpleNamespace(canManageUsers=True)
        controller = SidebarEditorController(application, users)
        controller._loaded(("demo", "Demo", object(), records))
        return controller

    def test_xml_uses_exact_native_layout_document(self):
        layout = DockPanelModel({}).capture_layout()
        view = "workspace_layout@review"

        restored = layout_configuration_from_xml(
            layout_configuration_xml(layout, view), view,
        )

        self.assertEqual(restored, layout)

    def test_project_cache_projects_presets_and_assignments(self):
        source = DockPanelModel({})
        source.resize_panel(
            "results", "right", 0.0, 0.0, 0.33, 1.0, 1600, 900,
        )
        view = "workspace_layout@review"
        records = [
            _preset_record(view, "Review", source.capture_layout()),
            {
                "code": "CONFIG0002",
                "search_type": "SideBarWdg",
                "view": "definition",
                "config": (
                    "<config><element name='review' title='Review Assets'>"
                    "<display class='LinkWdg'><layout_preset>"
                    f"{view}</layout_preset></display></element></config>"
                ),
            },
        ]
        target = DockPanelModel({})
        _application, _project, controller = _controller(records, target)

        preset = controller.presets.get(0)
        self.assertEqual(preset["title"], "Review")
        self.assertEqual(preset["assignedCount"], 1)
        self.assertEqual(
            controller.options[1], {"value": view, "label": "Review"},
        )
        self.assertTrue(controller.apply_preset(view))
        self.assertEqual(
            round(target.capture_layout()["panels"][0]["width"], 2),
            0.33,
        )

    def test_save_replace_and_delete_use_one_server_record(self):
        dock_model = DockPanelModel({})
        records = []
        application, project, controller = _controller(
            records, dock_model,
        )
        server = _Server(records)
        controller._run = lambda operation, handler: handler(operation())

        with patch(
            "thlib.tactic_classes.server_start", return_value=server,
        ):
            controller.save_as("Review")
            self.assertEqual(controller.presets.count(), 1)
            saved = controller.presets.get(0)
            view = saved["view"]
            self.assertTrue(saved["code"])

            dock_model.resize_panel(
                "results", "right", 0.0, 0.0, 0.29, 1.0,
                1600, 900,
            )
            controller.update(view)
            self.assertEqual(len(records), 1)
            stored = layout_configuration_from_xml(
                records[0]["config"], view,
            )
            self.assertEqual(
                round(stored["panels"][0]["width"], 2), 0.29,
            )

            controller.delete_preset(view)

        self.assertEqual(records, [])
        self.assertEqual(project.views.config_dict, [])
        self.assertEqual(
            application.notifications[-1],
            "Workspace layout preset deleted",
        )

    def test_assigned_layout_preset_cannot_be_deleted(self):
        layout = DockPanelModel({}).capture_layout()
        view = "workspace_layout@assigned"
        records = [
            _preset_record(view, "Assigned", layout),
            {
                "code": "CONFIG0002",
                "search_type": "SideBarWdg",
                "view": "definition",
                "config": (
                    "<config><element name='assigned'><display>"
                    f"<layout_preset>{view}</layout_preset>"
                    "</display></element></config>"
                ),
            },
        ]
        _application, _project, controller = _controller(
            records, DockPanelModel({}),
        )

        controller.delete_preset(view)

        self.assertEqual(controller.presets.count(), 1)
        self.assertIn("sidebar items", controller.error)

    def test_sidebar_editor_excludes_layout_config_records(self):
        controller = self._sidebar_controller([{
            "search_type": "SideBarWdg",
            "view": "definition",
            "config": (
                "<config><element name='assets' title='Assets'>"
                "<display class='LinkWdg'/></element></config>"
            ),
        }, {
            "search_type": "SideBarWdg",
            "category": WORKSPACE_LAYOUT_CATEGORY,
            "view": "workspace_layout@review",
            "config": (
                "<config><view name='workspace_layout@review'/></config>"
            ),
        }])

        self.assertEqual(set(controller._documents), {"definition"})

    def test_sidebar_assignment_writes_native_display_data(self):
        controller = self._sidebar_controller([{
            "search_type": "SideBarWdg",
            "view": "definition",
            "config": (
                "<config><element name='assets' title='Assets'>"
                "<display class='LinkWdg'/>"
                "<search_type>demo/assets</search_type>"
                "</element></config>"
            ),
        }])
        controller.select_entry(0)

        controller.update_selected(
            "layoutPreset", "workspace_layout@review",
        )

        self.assertEqual(
            controller.selectedEntry["layoutPreset"],
            "workspace_layout@review",
        )
        self.assertIn(
            "<layout_preset>workspace_layout@review</layout_preset>",
            controller.xmlText,
        )


if __name__ == "__main__":
    unittest.main()
