"""Native project wizard branches and the real QML input path."""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QEventLoop, QObject, QPointF, QThread, QTimer, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

from thlib.ui.project_creation import (
    ProjectCreationController,
    creation_command,
    project_identifier,
)
from tests.qt_application import gui_test_application


QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class _Windows(QObject):
    @Slot(str)
    def close_window(self, _identity):
        pass

    @Slot(str)
    def show_window(self, _identity):
        pass

    @Slot(str, str)
    def show_child_window(self, _identity, _parent):
        pass

    @Slot(str)
    def open_help(self, _identity):
        pass


class ProjectCreationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_native_project_editor_and_shared_footer_have_no_corner_gaps(self):
        from thlib.ui.project_editor import ProjectEditorController

        for subject, flags in (
            ("Controls.DockWorkspaceFooter", "Qt.Dialog"),
            ("Controls.DockWorkspaceFooter", "Qt.Window"),
        ):
            engine = QQmlEngine()
            editor = ProjectEditorController(lambda: {}, None)
            windows = _Windows()
            engine.rootContext().setContextProperty("projectEditorController", editor)
            engine.rootContext().setContextProperty("windowModel", windows)
            warnings = []
            engine.warnings.connect(lambda errors: warnings.extend(errors))
            component = QQmlComponent(engine)
            component.setData(
                (
                    """import QtQuick
import QtQuick.Window
import "." as App
import "controls" as Controls
Window {
    width: 680; height: 520; visible: true; flags: %s
    App.Theme { id: theme; dark: true }
    %s { anchors.fill: parent; theme: theme }
}"""
                    % (flags, subject)
                ).encode(),
                QUrl.fromLocalFile(str(QML / "_FooterTest.qml")),
            )
            owner = component.create()
            self.assertIsNotNone(
                owner, "\n".join(e.toString() for e in component.errors())
            )
            try:
                for width, height in ((680, 520), (1080, 900)):
                    owner.setWidth(width)
                    owner.setHeight(height)
                    frame = QSignalSpy(owner.frameSwapped)
                    owner.update()
                    self.assertTrue(frame.wait(1000))
                    footer = owner.findChild(
                        QQuickItem, "dockWorkspaceFooterDivider"
                    ).parentItem()
                    if flags == "Qt.Window":
                        self.assertGreater(footer.property("bottomLeftRadius"), 0)
                        self.assertGreater(footer.property("bottomRightRadius"), 0)
                        continue
                    self.assertEqual(footer.property("bottomLeftRadius"), 0)
                    self.assertEqual(footer.property("bottomRightRadius"), 0)
                    image = owner.grabWindow()
                    center = image.pixelColor(image.width() // 2, image.height() - 2)
                    for x in (2, image.width() - 3):
                        self.assertEqual(
                            image.pixelColor(x, image.height() - 2), center
                        )
                self.assertEqual(
                    warnings, [], "\n".join(w.toString() for w in warnings)
                )
            finally:
                owner.close()
                owner.deleteLater()
                engine.deleteLater()

    def test_native_command_branches_preserve_options(self):
        values = {
            "title": "Example project",
            "code": "example_project",
            "source": "_empty",
            "namespace": "",
            "theme": "TACTIC/default_theme",
            "isMainProject": True,
            "isTemplate": True,
        }
        command, args = creation_command(values)
        self.assertEqual(command, "tactic.command.CreateProjectCmd")
        self.assertEqual(args["project_type"], "example_project")
        self.assertTrue(args["is_template"])
        self.assertTrue(args["is_main_project"])
        values["namespace"] = "studio"
        self.assertEqual(creation_command(values)[1]["project_type"], "studio")
        values["source"] = "vfx|/templates/vfx"
        command, args = creation_command(values)
        self.assertEqual(command, "tactic.command.ProjectTemplateInstallerCmd")
        self.assertEqual(args["path"], "/templates/vfx")
        self.assertEqual(args["template_code"], "vfx")
        self.assertTrue(args["force_database"])
        self.assertNotIn("project_type", args)
        self.assertNotIn("is_main_project", args)
        self.assertNotIn("is_template", args)
        values["source"] = "studio_template"
        self.assertNotIn("path", creation_command(values)[1])

    def test_new_session_defaults_to_no_web_theme(self):
        controller = ProjectCreationController(SimpleNamespace())
        catalog = {
            "themes": [{"value": "TACTIC/default_theme", "label": "Server theme"}]
        }
        self.assertEqual(controller.draft["theme"], "")
        controller._operation = "catalog"
        controller._result((catalog, controller._generation))
        self.assertEqual(controller.draft["theme"], "")
        controller.set_value("theme", "TACTIC/default_theme")
        controller._operation = "catalog"
        controller._result((catalog, controller._generation))
        self.assertEqual(controller.draft["theme"], "TACTIC/default_theme")
        with patch.object(controller, "reload_catalog"):
            controller.begin_session()
        self.assertEqual(controller.draft["theme"], "")
        self.assertEqual(
            creation_command(
                {**controller.draft, "title": "Fixture", "code": "fixture"}
            )[1]["project_theme"],
            "",
        )

    def test_title_conversion_and_validation_match_native_limits(self):
        self.assertEqual(project_identifier("My Project! -- Test"), "my_project_test")
        valid = {"title": "My Project", "code": "my_project", "source": "_empty"}
        for field, value in (
            ("title", ""),
            ("title", "a" * 101),
            ("code", "9project"),
            ("code", "a" * 31),
            ("code", "project/path"),
            ("namespace", "sthpw"),
            ("namespace", "prod"),
            ("source", ""),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                creation_command({**valid, field: value})

    def test_preview_upload_and_creation_use_native_commands(self):
        from thlib import tactic_classes as tc

        server = Mock()
        server.get_transaction_ticket.return_value = "fixture-ticket"
        server.execute_cmd.return_value = {
            "info": {"lib_path": "/assets/temp/image.png"}
        }
        with (
            TemporaryDirectory() as directory,
            patch.object(tc, "server_start", return_value=server),
        ):
            image = Path(directory) / "image.png"
            image.touch()
            result = ProjectCreationController._create(
                "tactic.command.CreateProjectCmd",
                {"project_code": "fixture"},
                str(image),
            )
        self.assertEqual(result, "fixture")
        server.upload_file.assert_called_once_with(str(image))
        self.assertEqual(
            server.execute_cmd.call_args_list[0].args[0],
            "tactic.command.CopyFileToAssetTempCmd",
        )
        self.assertEqual(
            server.execute_cmd.call_args_list[1].kwargs["args"]["project_image_path"],
            "/assets/temp/image.png",
        )

    def test_retry_after_creation_only_reloads_the_project(self):
        controller = ProjectCreationController(SimpleNamespace())
        controller._created_code = "created_fixture"
        controller._step = 3
        with patch.object(controller, "_start") as start:
            controller.submit()
        self.assertEqual(start.call_args.args[0], controller._load_created_project)
        self.assertEqual(start.call_args.args[2], "finish")

    def test_description_saved_before_activation_without_repeating_creation(self):
        project = Mock()
        project.get_code.return_value = "fixture"
        project.get_title.return_value = "Fixture"
        project.get_info.return_value = {"description": "Copied template description"}
        application = Mock()
        application._load_projects.return_value = [project]
        controller = ProjectCreationController(application)
        controller._created_code = "fixture"
        controller.set_value("description", "ignored after creation")
        controller._draft["description"] = "  A new project description  "
        controller._draft["category"] = "  Animation  "
        project.commit.side_effect = RuntimeError("Temporary failure")
        with self.assertRaisesRegex(RuntimeError, "Temporary failure"):
            controller._load_created_project()
        application._prepare_project_selection.assert_not_called()
        project.commit.side_effect = None
        controller._load_created_project()
        project.set_value.assert_any_call("description", "A new project description")
        project.set_value.assert_any_call("category", "Animation")
        self.assertEqual(project.commit.call_count, 2)
        application._prepare_project_selection.assert_called_once_with(
            "fixture", "Fixture"
        )
        self.assertNotIn("destination", controller.draft)

        # Clearing a copied template description is intentional too.
        controller._draft["description"] = ""
        controller._load_created_project()
        project.set_value.assert_any_call("description", "")

    def test_step_navigation_only_returns_to_previous_steps(self):
        controller = ProjectCreationController(SimpleNamespace())
        controller._step = 2
        for step in (-1, 3, 99):
            controller.select_step(step)
            self.assertEqual(controller.step, 2)
        controller._busy = True
        controller.select_step(0)
        self.assertEqual(controller.step, 2)
        controller._busy = False
        controller._created_code = "fixture"
        controller.select_step(0)
        self.assertEqual(controller.step, 2)
        controller._created_code = ""
        controller._error = "fixture error"
        controller.select_step(0)
        self.assertEqual(controller.step, 0)
        self.assertEqual(controller.error, "")

    def test_creation_and_activation_through_real_worker_pool(self):
        from thlib.environment import env_inst
        from thlib.pool import ThreadsPool

        project = Mock()
        project.get_code.return_value = "fixture"
        project.get_title.return_value = "Native server title"
        project.get_info.return_value = {"description": ""}
        application = Mock()
        application._load_projects.return_value = [project]
        application._prepare_project_selection.return_value = (
            "fixture",
            "Native server title",
        )
        controller = ProjectCreationController(application)
        controller._catalog = {"templates": []}
        controller._draft.update(title="Fixture", code="fixture", theme="")
        controller._step = 3
        pool = ThreadsPool()
        pool.start()
        loop = QEventLoop()
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        controller.completed.connect(loop.quit)
        worker_threads = []

        def create(*_arguments):
            worker_threads.append(QThread.currentThread())
            return "fixture"

        try:
            with (
                patch.object(env_inst, "server_pool", pool),
                patch.object(controller, "_create", side_effect=create),
            ):
                controller.submit()
                timeout.start(3000)
                loop.exec()
            self.assertFalse(controller.busy)
            self.assertEqual(controller.error, "")
            self.assertEqual(controller.createdCode, "fixture")
            self.assertNotEqual(worker_threads, [self.app.thread()])
            application.project_model.replace.assert_called_once_with([project])
            application._prepare_project_selection.assert_called_once_with(
                "fixture", "Native server title"
            )
            application._apply_selected_project.assert_called_once_with(
                "fixture", "Native server title"
            )
        finally:
            timeout.stop()
            controller.shutdown()
            pool.exit()
            self.app.processEvents()

    def test_template_actions_use_native_commands(self):
        from thlib import tactic_classes as tc

        server = Mock()
        with patch.object(tc, "server_start", return_value=server):
            ProjectCreationController._install_template("/fixture/template.zip")
            ProjectCreationController._template_command("export", {"value": "studio"})
            ProjectCreationController._template_command("delete", {"code": "studio"})
        self.assertEqual(
            [call.args[0] for call in server.execute_cmd.call_args_list],
            [
                "tactic.ui.app.ProjectTemplateInstallCmd",
                "tactic.command.ProjectTemplateCreatorCmd",
                "tactic.ui.app.ProjectTemplateDeleteCmd",
            ],
        )
        server.upload_file.assert_called_once_with("/fixture/template.zip")

    def test_export_accepts_an_ordinary_project_without_loading_wizard_catalog(self):
        from thlib.environment import env_inst

        project = Mock()
        project.is_builtin.return_value = False
        controller = ProjectCreationController(Mock())
        with (
            patch.object(env_inst, "projects", {"fixture": project}),
            patch.object(controller, "_start") as start,
        ):
            controller.export_project("fixture")
        start.assert_called_once_with(
            controller._template_command, ("export", {"value": "fixture"}), "export"
        )

    def test_worker_failure_is_visible_without_generic_mutation_retry(self):
        from thlib.environment import env_inst
        from thlib.pool import ThreadsPool

        application = Mock()
        controller = ProjectCreationController(application)
        pool = ThreadsPool()
        pool.start()
        loop = QEventLoop()
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)
        controller.stateChanged.connect(
            lambda: loop.quit() if controller.error else None
        )

        def fail():
            raise ValueError("Native fixture failure")

        try:
            with patch.object(env_inst, "server_pool", pool), patch("sys.stdout"):
                controller._start(fail, (), "create")
                timeout.start(3000)
                loop.exec()
            self.assertFalse(controller.busy)
            self.assertEqual(controller.error, "Native fixture failure")
            self.assertTrue(controller.uncertain)
            controller._step = 3
            with patch.object(controller, "_start") as start:
                controller.submit()
                start.assert_not_called()
            controller._draft["code"] = "possibly_created"
            controller._operation = "catalog"
            controller._result(
                (
                    {"projectCodes": ["possibly_created"], "themes": []},
                    controller._generation,
                )
            )
            self.assertFalse(controller.uncertain)
            self.assertEqual(controller.createdCode, "possibly_created")
            with patch.object(controller, "_start") as start:
                controller.submit()
                start.assert_called_once_with(
                    controller._load_created_project, (), "finish"
                )

            report = application._report_error_payload.call_args
            self.assertIsNotNone(report)
            self.assertEqual(len(report.args), 2)
            self.assertIn(
                "ValueError: Native fixture failure", report.args[0]["stacktrace"]
            )
        finally:
            timeout.stop()
            controller.shutdown()
            pool.exit()
            self.app.processEvents()

    def test_server_catalog_matches_native_templates_themes_and_retired_codes(self):
        from thlib import tactic_query as tq

        template = Mock()
        template.get_value.side_effect = {
            "code": "studio",
            "title": "Server Studio",
        }.get
        retired = Mock()
        retired.get_value.return_value = "retired_fixture"
        template_search = Mock()
        template_search.get_sobjects.return_value = [template]
        code_search = Mock()
        code_search.get_sobjects.return_value = [template, retired]
        search = Mock(side_effect=[template_search, code_search])
        project = Mock()
        project.get_default_project.return_value = ""
        project.get_all_projects.return_value = [template]
        plugins = Mock()
        plugins.get_plugins_data.return_value = {
            "TACTIC/default_theme": {"description": "Server description"}
        }
        biz = ModuleType("pyasm.biz")
        biz.Project = project
        biz.PluginUtil = Mock(return_value=plugins)
        common = ModuleType("pyasm.common")
        common.Common = SimpleNamespace(get_display_title=lambda value: value.title())
        common.Environment = Mock()
        search_module = ModuleType("pyasm.search")
        search_module.Search = search
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "studio-1.0.0.zip").touch()
            (root / "another-1.0.0.zip").touch()
            (root / "another").mkdir()
            (root / "src/plugins/TACTIC/vfx").mkdir(parents=True)
            common.Environment.get_template_dir.return_value = directory
            common.Environment.get_install_dir.return_value = directory
            common.Environment.get_builtin_plugin_dir.return_value = directory
            common.Environment.is_builtin_plugin.return_value = True
            with patch.dict(
                sys.modules,
                {
                    "pyasm": ModuleType("pyasm"),
                    "pyasm.biz": biz,
                    "pyasm.common": common,
                    "pyasm.search": search_module,
                },
            ):
                catalog = tq.get_project_creation_catalog()
        self.assertEqual(
            [row["kind"] for row in catalog["templates"]],
            ["project", "file", "builtin"],
        )
        self.assertEqual(catalog["templates"][0]["label"], "Server Studio")
        self.assertEqual(catalog["themes"][0]["description"], "Server description")
        self.assertEqual(
            catalog["themes"][0]["preview"],
            "/tactic/builtin_plugins/TACTIC/default_theme/media/screenshot.jpg",
        )
        self.assertIn("retired_fixture", catalog["projectCodes"])
        code_search.set_show_retired.assert_called_once_with(True)
        self.assertFalse(catalog["isMainProject"])

    def test_wizard_real_input_and_all_four_steps_at_both_widths(self):
        from tests.frame_configuration_fixture import Surface
        from tests.test_configuration_layout import ConfigurationLayoutTests

        surface = Surface("wizard", 1100, 740, language="ru")
        self.addCleanup(surface.close)
        helper = ConfigurationLayoutTests()
        click = lambda name: helper.click(surface, name)
        controller = surface.creator
        helper.type(surface, "setting_title", "Demo Project")
        self.assertEqual(controller.draft["title"], "Demo Project")
        self.assertEqual(controller.draft["code"], "demo_project")
        helper.type(surface, "setting_category", "Animation")
        helper.type(surface, "setting_description", "Project description")
        helper.type(surface, "setting_namespace", "studio_namespace")
        click("setting_isTemplate")
        self.assertTrue(controller.draft["isTemplate"])
        for step in range(4):
            self.assertEqual(controller.step, step)
            for width in (360, 680, 1080):
                for height in (520, 740):
                    surface.window.setWidth(width)
                    surface.window.setHeight(height)
                    surface.view.setWidth(width)
                    surface.view.setHeight(height)
                    surface.settle()
                    button = surface.item("projectNext")
                    point = button.mapToScene(QPointF())
                    self.assertGreaterEqual(point.x(), 0)
                    self.assertLessEqual(point.x() + button.width(), width)
                    self.assertLessEqual(point.y() + button.height(), height)
                    footer = surface.item("projectWizardFooter")
                    self.assertAlmostEqual(
                        footer.mapToScene(QPointF(0, footer.height())).y(),
                        height,
                        delta=0.5,
                    )
                    image = surface.window.grabWindow()
                    center = image.pixelColor(image.width() // 2, image.height() - 2)
                    for x in (2, image.width() - 3):
                        self.assertEqual(
                            image.pixelColor(x, image.height() - 2), center
                        )
                    if step == 2:
                        self.assertEqual(
                            surface.item("setting_theme").property("currentValue"), ""
                        )
            if step < 3:
                click("projectNext")
        self.assertEqual(
            surface.item("setting_description").property("text"), "Project description"
        )
        self.assertTrue(surface.item("setting_title").property("readOnly"))
        click("projectBack")
        self.assertEqual(controller.step, 2)
        controller.set_value("namespace", "sthpw")
        click("projectNext")
        self.assertEqual(controller.step, 2)
        self.assertTrue(controller.error)
        selector = helper.reveal(surface, "setting_source")
        selector.forceActiveFocus()
        QTest.keyClick(surface.window, Qt.Key_Down)
        surface.settle()
        self.assertEqual(controller.draft["source"], "library")
        click("projectNext")
        self.assertEqual(controller.step, 3)
        self.assertFalse(surface.evaluate("requestClose()"))
        click("projectKeepEditing")
        self.assertFalse(surface.view.property("discard"))
        controller._busy = True
        controller.stateChanged.emit()
        surface.settle()
        self.assertFalse(surface.evaluate("requestClose()"))
        self.assertFalse(surface.item("projectNext").isEnabled())
        controller._busy = False
        controller.stateChanged.emit()
        surface.settle()
        self.assertEqual(surface.warnings, [])

    def test_selected_preview_and_undo_fit_narrow_wizard_and_editor(self):
        from tests.frame_configuration_fixture import Surface
        from tests.test_configuration_layout import ConfigurationLayoutTests
        from PySide6.QtCore import QRectF

        with TemporaryDirectory() as directory:
            path = Path(directory) / "preview.png"
            image = QImage(32, 32, QImage.Format_RGB32)
            image.fill(Qt.red)
            self.assertTrue(image.save(str(path)))
            for screen, field in (
                ("wizard", "projectImagePicker"),
                ("editor", "projectEditorImage"),
            ):
                surface = Surface(screen, 360, 740)
                try:
                    if screen == "wizard":
                        surface.creator.set_value("previewPath", str(path))
                        surface.creator._step = 1
                        surface.creator.stateChanged.emit()
                    else:
                        surface.editor.set_preview_path(str(path))
                    surface.settle()
                    helper = ConfigurationLayoutTests()
                    for width in (360, 530, 800):
                        surface.window.setWidth(width)
                        surface.view.setWidth(width)
                        surface.settle()
                        outer = surface.item(field)
                        undo = surface.item("imagePickerCancelPreview")
                        bounds = undo.mapRectToItem(
                            outer, QRectF(0, 0, undo.width(), undo.height())
                        )
                        self.assertGreaterEqual(bounds.top(), 0)
                        self.assertLessEqual(bounds.bottom(), outer.height() + 0.5)
                    helper.click(surface, "imagePickerCancelPreview")
                    self.assertFalse(
                        surface.creator.draft["previewPath"]
                        if screen == "wizard"
                        else surface.editor.previewPath
                    )
                    self.assertEqual(surface.warnings, [])
                finally:
                    surface.close()

    def test_native_editor_dirty_guard_and_square_host_footer(self):
        from tests.frame_configuration_fixture import Surface
        from tests.test_configuration_layout import ConfigurationLayoutTests

        surface = Surface("editor", 680, 520)
        self.addCleanup(surface.close)
        helper = ConfigurationLayoutTests()
        self.assertFalse(surface.editor.dirty)
        self.assertTrue(surface.evaluate("requestClose()"))
        self.assertTrue(surface.item("setting_code").property("readOnly"))
        helper.type(surface, "setting_title", "Updated project")
        self.assertTrue(surface.editor.dirty)
        self.assertFalse(surface.evaluate("requestClose()"))
        helper.click(surface, "projectEditorKeep")
        self.assertFalse(surface.view.property("discard"))
        for width, height in ((680, 520), (1080, 900)):
            surface.window.setWidth(width)
            surface.window.setHeight(height)
            surface.view.setWidth(width)
            surface.view.setHeight(height)
            surface.settle()
            footer = surface.item("projectEditorFooter")
            self.assertAlmostEqual(
                footer.mapToScene(QPointF(0, footer.height())).y(), height, delta=0.5
            )
            image = surface.window.grabWindow()
            center = image.pixelColor(image.width() // 2, image.height() - 2)
            for x in (2, image.width() - 3):
                self.assertEqual(image.pixelColor(x, image.height() - 2), center)
        surface.editor.begin_session()
        surface.settle()
        self.assertFalse(surface.editor.dirty)
        self.assertFalse(surface.view.property("discard"))
        self.assertEqual(surface.warnings, [])

    def test_template_manager_real_selection_and_modal_confirmation(self):
        from tests.frame_configuration_fixture import Surface
        from tests.test_configuration_layout import ConfigurationLayoutTests
        from tests.frame_support_fixture import evaluate

        surface = Surface("templates", 680, 520)
        self.addCleanup(surface.close)
        helper = ConfigurationLayoutTests()
        self.assertTrue(surface.item("templateInstall").isEnabled())
        helper.click(surface, "template_cg_template")
        self.assertEqual(surface.view.property("selectedCode"), "cg_template")
        helper.click(surface, "templateDelete")
        dialog = evaluate(surface.engine, surface.view, "deleteConfirmation")
        self.assertTrue(dialog.property("modal"))
        self.assertTrue(dialog.property("visible"))
        # Popup content is a separate Qt visual subtree, so use its actual window.
        content = dialog.property("contentItem")
        children = [content]
        for item in children:
            children.extend(item.childItems())
        cancel = next(
            item for item in children if item.objectName() == "templateDeleteCancel"
        )
        QTest.mouseClick(
            cancel.window(),
            Qt.LeftButton,
            pos=cancel.mapToScene(
                QPointF(cancel.width() / 2, cancel.height() / 2)
            ).toPoint(),
        )
        surface.settle()
        self.assertFalse(dialog.property("visible"))
        self.assertEqual(surface.creator.busy, False)
        self.assertEqual(surface.warnings, [])


if __name__ == "__main__":
    unittest.main()
