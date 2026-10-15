"""Native project wizard branches and the real QML input path."""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')

from PySide6.QtCore import QEventLoop, QObject, QPointF, QThread, QTimer, Qt, QUrl, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

from thlib.ui.project_creation import (
    ProjectCreationController, creation_command, project_identifier,
)
from tests.qt_application import gui_test_application


QML = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'


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
            ('App.ProjectEditorView', 'Qt.Dialog'),
            ('Controls.DockWorkspaceFooter', 'Qt.Dialog'),
            ('Controls.DockWorkspaceFooter', 'Qt.Window'),
        ):
            engine = QQmlEngine()
            editor = ProjectEditorController(lambda: {}, None)
            windows = _Windows()
            engine.rootContext().setContextProperty('projectEditorController', editor)
            engine.rootContext().setContextProperty('windowModel', windows)
            warnings = []
            engine.warnings.connect(lambda errors: warnings.extend(errors))
            component = QQmlComponent(engine)
            component.setData(('''import QtQuick
import QtQuick.Window
import "." as App
import "controls" as Controls
Window {
    width: 680; height: 520; visible: true; flags: %s
    App.Theme { id: theme; dark: true }
    %s { anchors.fill: parent; theme: theme }
}''' % (flags, subject)).encode(), QUrl.fromLocalFile(str(QML / '_FooterTest.qml')))
            owner = component.create()
            self.assertIsNotNone(owner, '\n'.join(e.toString() for e in component.errors()))
            try:
                for width, height in ((680, 520), (1080, 900)):
                    owner.setWidth(width)
                    owner.setHeight(height)
                    frame = QSignalSpy(owner.frameSwapped)
                    owner.update()
                    self.assertTrue(frame.wait(1000))
                    footer = owner.findChild(QQuickItem, 'dockWorkspaceFooterDivider').parentItem()
                    if flags == 'Qt.Window':
                        self.assertGreater(footer.property('bottomLeftRadius'), 0)
                        self.assertGreater(footer.property('bottomRightRadius'), 0)
                        continue
                    self.assertEqual(footer.property('bottomLeftRadius'), 0)
                    self.assertEqual(footer.property('bottomRightRadius'), 0)
                    image = owner.grabWindow()
                    center = image.pixelColor(image.width() // 2, image.height() - 2)
                    for x in (2, image.width() - 3):
                        self.assertEqual(image.pixelColor(x, image.height() - 2), center)
                self.assertEqual(warnings, [], '\n'.join(w.toString() for w in warnings))
            finally:
                owner.close()
                owner.deleteLater()
                engine.deleteLater()

    def test_native_command_branches_preserve_options(self):
        values = {
            'title': 'Example project', 'code': 'example_project',
            'source': '_empty', 'namespace': '', 'theme': 'TACTIC/default_theme',
            'isMainProject': True, 'isTemplate': True,
        }
        command, args = creation_command(values)
        self.assertEqual(command, 'tactic.command.CreateProjectCmd')
        self.assertEqual(args['project_type'], 'example_project')
        self.assertTrue(args['is_template'])
        self.assertTrue(args['is_main_project'])
        values['namespace'] = 'studio'
        self.assertEqual(creation_command(values)[1]['project_type'], 'studio')
        values['source'] = 'vfx|/templates/vfx'
        command, args = creation_command(values)
        self.assertEqual(command, 'tactic.command.ProjectTemplateInstallerCmd')
        self.assertEqual(args['path'], '/templates/vfx')
        self.assertEqual(args['template_code'], 'vfx')
        self.assertTrue(args['force_database'])
        self.assertNotIn('project_type', args)
        self.assertNotIn('is_main_project', args)
        self.assertNotIn('is_template', args)
        values['source'] = 'studio_template'
        self.assertNotIn('path', creation_command(values)[1])

    def test_new_session_defaults_to_no_web_theme(self):
        controller = ProjectCreationController(SimpleNamespace())
        catalog = {'themes': [{'value': 'TACTIC/default_theme', 'label': 'Server theme'}]}
        self.assertEqual(controller.draft['theme'], '')
        controller._operation = 'catalog'
        controller._result((catalog, controller._generation))
        self.assertEqual(controller.draft['theme'], '')
        controller.set_value('theme', 'TACTIC/default_theme')
        controller._operation = 'catalog'
        controller._result((catalog, controller._generation))
        self.assertEqual(controller.draft['theme'], 'TACTIC/default_theme')
        with patch.object(controller, 'reload_catalog'):
            controller.begin_session()
        self.assertEqual(controller.draft['theme'], '')
        self.assertEqual(creation_command({**controller.draft, 'title': 'Fixture', 'code': 'fixture'})[1]['project_theme'], '')

    def test_title_conversion_and_validation_match_native_limits(self):
        self.assertEqual(project_identifier('My Project! -- Test'), 'my_project_test')
        valid = {'title': 'My Project', 'code': 'my_project', 'source': '_empty'}
        for field, value in (
            ('title', ''), ('title', 'a' * 101), ('code', '9project'),
            ('code', 'a' * 31), ('code', 'project/path'), ('namespace', 'sthpw'),
            ('namespace', 'prod'), ('source', ''),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                creation_command({**valid, field: value})

    def test_preview_upload_and_creation_use_native_commands(self):
        from thlib import tactic_classes as tc
        server = Mock()
        server.get_transaction_ticket.return_value = 'fixture-ticket'
        server.execute_cmd.return_value = {'info': {'lib_path': '/assets/temp/image.png'}}
        with TemporaryDirectory() as directory, patch.object(tc, 'server_start', return_value=server):
            image = Path(directory) / 'image.png'
            image.touch()
            result = ProjectCreationController._create(
                'tactic.command.CreateProjectCmd', {'project_code': 'fixture'}, str(image),
            )
        self.assertEqual(result, 'fixture')
        server.upload_file.assert_called_once_with(str(image))
        self.assertEqual(server.execute_cmd.call_args_list[0].args[0], 'tactic.command.CopyFileToAssetTempCmd')
        self.assertEqual(server.execute_cmd.call_args_list[1].kwargs['args']['project_image_path'], '/assets/temp/image.png')

    def test_retry_after_creation_only_reloads_the_project(self):
        controller = ProjectCreationController(SimpleNamespace())
        controller._created_code = 'created_fixture'
        controller._step = 3
        with patch.object(controller, '_start') as start:
            controller.submit()
        self.assertEqual(start.call_args.args[0], controller._load_created_project)
        self.assertEqual(start.call_args.args[2], 'finish')

    def test_description_saved_before_activation_without_repeating_creation(self):
        project = Mock()
        project.get_code.return_value = 'fixture'
        project.get_title.return_value = 'Fixture'
        project.get_info.return_value = {'description': 'Copied template description'}
        application = Mock()
        application._load_projects.return_value = [project]
        controller = ProjectCreationController(application)
        controller._created_code = 'fixture'
        controller.set_value('description', 'ignored after creation')
        controller._draft['description'] = '  A new project description  '
        controller._draft['category'] = '  Animation  '
        project.commit.side_effect = RuntimeError('Temporary failure')
        with self.assertRaisesRegex(RuntimeError, 'Temporary failure'):
            controller._load_created_project()
        application._prepare_project_selection.assert_not_called()
        project.commit.side_effect = None
        controller._load_created_project()
        project.set_value.assert_any_call('description', 'A new project description')
        project.set_value.assert_any_call('category', 'Animation')
        self.assertEqual(project.commit.call_count, 2)
        application._prepare_project_selection.assert_called_once_with('fixture', 'Fixture')
        self.assertNotIn('destination', controller.draft)

        # Clearing a copied template description is intentional too.
        controller._draft['description'] = ''
        controller._load_created_project()
        project.set_value.assert_any_call('description', '')

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
        controller._created_code = 'fixture'
        controller.select_step(0)
        self.assertEqual(controller.step, 2)
        controller._created_code = ''
        controller._error = 'fixture error'
        controller.select_step(0)
        self.assertEqual(controller.step, 0)
        self.assertEqual(controller.error, '')

    def test_creation_and_activation_through_real_worker_pool(self):
        from thlib.environment import env_inst
        from thlib.pool import ThreadsPool

        project = Mock()
        project.get_code.return_value = 'fixture'
        project.get_title.return_value = 'Native server title'
        project.get_info.return_value = {'description': ''}
        application = Mock()
        application._load_projects.return_value = [project]
        application._prepare_project_selection.return_value = ('fixture', 'Native server title')
        controller = ProjectCreationController(application)
        controller._catalog = {'templates': []}
        controller._draft.update(title='Fixture', code='fixture', theme='')
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
            return 'fixture'

        try:
            with patch.object(env_inst, 'server_pool', pool), patch.object(controller, '_create', side_effect=create):
                controller.submit()
                timeout.start(3000)
                loop.exec()
            self.assertFalse(controller.busy)
            self.assertEqual(controller.error, '')
            self.assertEqual(controller.createdCode, 'fixture')
            self.assertNotEqual(worker_threads, [self.app.thread()])
            application.project_model.replace.assert_called_once_with([project])
            application._prepare_project_selection.assert_called_once_with('fixture', 'Native server title')
            application._apply_selected_project.assert_called_once_with('fixture', 'Native server title')
        finally:
            timeout.stop()
            controller.shutdown()
            pool.exit()
            self.app.processEvents()

    def test_template_actions_use_native_commands(self):
        from thlib import tactic_classes as tc
        server = Mock()
        with patch.object(tc, 'server_start', return_value=server):
            ProjectCreationController._install_template('/fixture/template.zip')
            ProjectCreationController._template_command('export', {'value': 'studio'})
            ProjectCreationController._template_command('delete', {'code': 'studio'})
        self.assertEqual([call.args[0] for call in server.execute_cmd.call_args_list], [
            'tactic.ui.app.ProjectTemplateInstallCmd',
            'tactic.command.ProjectTemplateCreatorCmd',
            'tactic.ui.app.ProjectTemplateDeleteCmd',
        ])
        server.upload_file.assert_called_once_with('/fixture/template.zip')

    def test_export_accepts_an_ordinary_project_without_loading_wizard_catalog(self):
        from thlib.environment import env_inst
        project = Mock()
        project.is_builtin.return_value = False
        controller = ProjectCreationController(Mock())
        with patch.object(env_inst, 'projects', {'fixture': project}), patch.object(controller, '_start') as start:
            controller.export_project('fixture')
        start.assert_called_once_with(controller._template_command, ('export', {'value': 'fixture'}), 'export')

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
        controller.stateChanged.connect(lambda: loop.quit() if controller.error else None)

        def fail():
            raise ValueError('Native fixture failure')

        try:
            with patch.object(env_inst, 'server_pool', pool), patch('sys.stdout'):
                controller._start(fail, (), 'create')
                timeout.start(3000)
                loop.exec()
            self.assertFalse(controller.busy)
            self.assertEqual(controller.error, 'Native fixture failure')
            report = application._report_error_payload.call_args
            self.assertIsNotNone(report)
            self.assertEqual(len(report.args), 2)
            self.assertIn('ValueError: Native fixture failure', report.args[0]['stacktrace'])
        finally:
            timeout.stop()
            controller.shutdown()
            pool.exit()
            self.app.processEvents()

    def test_server_catalog_matches_native_templates_themes_and_retired_codes(self):
        from thlib import tactic_query as tq

        template = Mock()
        template.get_value.side_effect = {'code': 'studio', 'title': 'Server Studio'}.get
        retired = Mock()
        retired.get_value.return_value = 'retired_fixture'
        template_search = Mock()
        template_search.get_sobjects.return_value = [template]
        code_search = Mock()
        code_search.get_sobjects.return_value = [template, retired]
        search = Mock(side_effect=[template_search, code_search])
        project = Mock()
        project.get_default_project.return_value = ''
        project.get_all_projects.return_value = [template]
        plugins = Mock()
        plugins.get_plugins_data.return_value = {'TACTIC/default_theme': {'description': 'Server description'}}
        biz = ModuleType('pyasm.biz')
        biz.Project = project
        biz.PluginUtil = Mock(return_value=plugins)
        common = ModuleType('pyasm.common')
        common.Common = SimpleNamespace(get_display_title=lambda value: value.title())
        common.Environment = Mock()
        search_module = ModuleType('pyasm.search')
        search_module.Search = search
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'studio-1.0.0.zip').touch()
            (root / 'another-1.0.0.zip').touch()
            (root / 'another').mkdir()
            (root / 'src/plugins/TACTIC/vfx').mkdir(parents=True)
            common.Environment.get_template_dir.return_value = directory
            common.Environment.get_install_dir.return_value = directory
            common.Environment.get_builtin_plugin_dir.return_value = directory
            common.Environment.is_builtin_plugin.return_value = True
            with patch.dict(sys.modules, {
                'pyasm': ModuleType('pyasm'), 'pyasm.biz': biz,
                'pyasm.common': common, 'pyasm.search': search_module,
            }):
                catalog = tq.get_project_creation_catalog()
        self.assertEqual([row['kind'] for row in catalog['templates']], ['project', 'file', 'builtin'])
        self.assertEqual(catalog['templates'][0]['label'], 'Server Studio')
        self.assertEqual(catalog['themes'][0]['description'], 'Server description')
        self.assertEqual(catalog['themes'][0]['preview'], '/tactic/builtin_plugins/TACTIC/default_theme/media/screenshot.jpg')
        self.assertIn('retired_fixture', catalog['projectCodes'])
        code_search.set_show_retired.assert_called_once_with(True)
        self.assertFalse(catalog['isMainProject'])

    def test_wizard_real_input_and_all_four_steps_at_both_widths(self):
        from thlib.ui.icon_font import qml_icon_bindings
        from thlib.ui.localization import CatalogTranslator

        translator = CatalogTranslator(QML.parent / 'translations/ru.json')
        self.app.installTranslator(translator)
        controller = ProjectCreationController(SimpleNamespace())
        controller._catalog = {
            'templates': [{'value': 'studio', 'label': 'Studio Template', 'kind': 'project'}],
            'themes': [{'value': 'TACTIC/default_theme', 'label': 'Server theme'}],
            'projectCodes': [], 'installedTemplates': [],
        }
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        bindings = qml_icon_bindings(QML.parents[2], engine)
        for name, value in bindings.items():
            engine.rootContext().setContextProperty(name, value)
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(errors))
        windows = _Windows()
        engine.rootContext().setContextProperty('projectCreationController', controller)
        engine.rootContext().setContextProperty('windowModel', windows)
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import QtQuick.Controls
import "." as App
ApplicationWindow {
    width: 680; height: 680; visible: true
    flags: Qt.Dialog
    App.Theme { id: theme; dark: true }
    App.ProjectWizardView { objectName: "projectWizard"; anchors.fill: parent; theme: theme }
}''', QUrl.fromLocalFile(str(QML / '_ProjectWizardTest.qml')))
        owner = component.create()
        self.assertIsNotNone(owner, '\n'.join(error.toString() for error in component.errors()))

        def find_item(name):
            item = None
            items = [owner.contentItem()]
            for candidate in items:
                items.extend(candidate.childItems())
                if candidate.objectName() == name:
                    item = candidate
                    break
            self.assertIsNotNone(item, name)
            return item

        def click(name):
            frame = QSignalSpy(owner.frameSwapped)
            owner.update()
            self.assertTrue(frame.wait(1000), 'Wizard layout did not render')
            item = find_item(name)
            QTest.mouseClick(owner, Qt.LeftButton, pos=item.mapToScene(QPointF(
                item.width() / 2, item.height() / 2,
            )).toPoint())
            frame = QSignalSpy(owner.frameSwapped)
            owner.update()
            self.assertTrue(frame.wait(1000), 'Wizard input did not render')

        def verify_stage_layout():
            for width in (680, 1080):
                owner.setWidth(width)
                for height in (520, 680):
                    owner.setHeight(height)
                    frame = QSignalSpy(owner.frameSwapped)
                    owner.update()
                    self.assertTrue(frame.wait(1000))
                    primary = owner.findChild(QQuickItem, (
                        'projectWizardCreate' if controller.step == 3
                        else 'projectWizardNext'
                    ))
                    position = primary.mapToScene(QPointF())
                    self.assertGreaterEqual(position.x(), 0)
                    self.assertLessEqual(position.x() + primary.width(), width)
                    self.assertLessEqual(position.y() + primary.height(), height)
                    wizard = owner.findChild(QQuickItem, 'projectWizard')
                    self.assertEqual(wizard.property('compactNavigation'), width < 900)
                    counter = owner.findChild(QObject, 'projectWizardStepCounter')
                    self.assertEqual(counter.property('text'), f'Шаг {controller.step + 1} из 4')
                    if controller.step == 2:
                        theme_selector = find_item('projectWizardTheme')
                        self.assertEqual(theme_selector.property('currentIndex'), 0)
                        self.assertEqual(theme_selector.property('currentValue'), '')
                        self.assertEqual(theme_selector.property('displayText'), 'Без темы')
                        theme_row = find_item('projectWizardThemeSetting')
                        self.assertEqual(theme_row.property('description'), 'Только для веб-интерфейса TACTIC. Не влияет на внешний вид TACTIC-Handler.')
                        selector = find_item('projectWizardTemplate')
                        actions = find_item('projectWizardTemplateActions')
                        selector_bottom = selector.mapToScene(QPointF(0, selector.height())).y()
                        actions_top = actions.mapToScene(QPointF()).y()
                        self.assertGreaterEqual(actions_top - selector_bottom, 12)
                    scroll = owner.findChild(QQuickItem, 'projectWizardScroll')
                    bar = owner.findChild(QQuickItem, 'projectWizardContentBar')
                    if scroll.property('contentHeight') > scroll.height() + 0.5:
                        self.assertTrue(bar.isVisible())
                        self.assertGreater(bar.height(), 0)
                        bar_position = bar.mapToScene(QPointF())
                        self.assertLessEqual(bar_position.x() + bar.width(), width)

        try:
            self.app.processEvents()
            click('projectWizard_title')
            for character in 'Demo Project':
                QTest.keyClick(owner, character)
            self.assertEqual(controller.draft['title'], 'Demo Project')
            self.assertEqual(controller.draft['code'], 'demo_project')
            click('projectWizard_category')
            for character in 'Animation':
                QTest.keyClick(owner, character)
            self.assertEqual(controller.draft['category'], 'Animation')
            click('projectWizard_description')
            for character in 'Project description':
                QTest.keyClick(owner, character)
            self.assertEqual(controller.draft['description'], 'Project description')
            flickable = find_item('projectWizardScroll').property('contentItem')
            namespace = find_item('projectWizard_namespace')
            flickable.setProperty('contentY', namespace.mapToScene(QPointF()).y() - 170)
            click('projectWizard_namespace')
            for character in 'studio_namespace':
                QTest.keyClick(owner, character)
            self.assertEqual(controller.draft['namespace'], 'studio_namespace')
            self.assertIn('studio/shot', namespace.parentItem().parentItem().parentItem().property('description'))
            click('projectWizardIsTemplate')
            self.assertTrue(controller.draft['isTemplate'])
            flickable.setProperty('contentY', 0)
            verify_stage_layout()
            for width in (680, 1080):
                owner.setWidth(width)
                self.app.processEvents()
                next_button = owner.findChild(QQuickItem, 'projectWizardNext')
                position = next_button.mapToScene(QPointF())
                self.assertGreaterEqual(position.x(), 0)
                self.assertLessEqual(position.x() + next_button.width(), width)
                footer = owner.findChild(
                    QQuickItem, 'dockWorkspaceFooterDivider',
                ).parentItem()
                for height in (520, 680, 900):
                    owner.setHeight(height)
                    self.app.processEvents()
                    bottom = footer.mapToScene(QPointF(0, footer.height())).y()
                    self.assertAlmostEqual(bottom, height, delta=0.5)
                    image = owner.grabWindow()
                    self.assertFalse(image.isNull())
                    bottom_color = image.pixelColor(image.width() // 2, image.height() - 2)
                    for x in (2, image.width() - 3):
                        self.assertEqual(
                            image.pixelColor(x, image.height() - 2), bottom_color,
                            f'Footer leaves a gap at {width}x{height}, x={x}',
                        )
            click('projectWizardNext')
            self.assertEqual(controller.step, 1)
            verify_stage_layout()
            owner.requestActivate()
            self.assertTrue(QTest.qWaitForWindowActive(owner))
            find_item('projectWizardStep_0').forceActiveFocus(Qt.OtherFocusReason)
            changed = QSignalSpy(controller.stateChanged)
            QTest.keyClick(owner, Qt.Key_Space)
            if not changed.count():
                self.assertTrue(changed.wait(1000), 'Keyboard step navigation did not activate')
            self.assertEqual(controller.step, 0)
            click('projectWizardNext')
            click('projectWizardNext')
            self.assertEqual(controller.step, 2)
            self.assertFalse(find_item('projectWizard_namespace').isVisible())
            self.assertFalse(find_item('projectWizardIsTemplate').isVisible())
            verify_stage_layout()
            controller.set_value('namespace', 'sthpw')
            click('projectWizardNext')
            self.assertEqual(controller.step, 2)
            self.assertTrue(controller.error)
            click('projectWizardTemplate')
            QTest.keyClick(owner, Qt.Key_Down)
            QTest.keyClick(owner, Qt.Key_Return)
            self.app.processEvents()
            self.assertEqual(controller.draft['source'], 'studio')
            click('projectWizardNext')
            self.assertEqual(controller.step, 3)
            verify_stage_layout()
            self.assertEqual(find_item('projectWizardReviewDescription').property('text'), 'Project description')
            self.assertEqual(find_item('projectWizardReviewCategory').property('value'), 'Animation')
            preview = find_item('projectWizardReviewPreview')
            self.assertEqual(preview.property('fallbackText'), 'DE')
            with TemporaryDirectory() as directory:
                image_path = Path(directory) / 'preview.png'
                image = QImage(128, 128, QImage.Format_RGB32)
                image.fill(Qt.red)
                self.assertTrue(image.save(str(image_path)))
                controller.set_value('previewPath', str(image_path))
                self.assertEqual(preview.property('source'), QUrl.fromLocalFile(str(image_path)))
                ready = QSignalSpy(preview.imageReady)
                source_image = preview.findChild(QQuickItem, 'previewSourceImage')
                if source_image.property('sourceSize').width() == 0:
                    self.assertTrue(ready.wait(1000), 'Review preview did not load')
                self.assertEqual(source_image.property('sourceSize').width(), 88 if owner.width() < 900 else 128)
                verify_stage_layout()
                controller.set_value('previewPath', '')
            self.assertIsNone(owner.findChild(QObject, 'projectWizardDestination'))
            click('projectWizardStep_1')
            self.assertEqual(controller.step, 1)
            click('projectWizardNext')
            click('projectWizardNext')
            self.assertEqual(controller.step, 3)
            create = owner.findChild(QQuickItem, 'projectWizardCreate')
            self.assertTrue(create.isVisible())
            self.assertTrue(create.isEnabled())
            with patch.object(controller, '_start') as start:
                click('projectWizardCreate')
            self.assertEqual(start.call_args.args[2], 'create')
            self.assertEqual(start.call_args.args[1][0], 'tactic.command.ProjectTemplateInstallerCmd')
            self.assertEqual(warnings, [], '\n'.join(w.toString() for w in warnings))
        finally:
            self.app.removeTranslator(translator)
            owner.close()
            owner.deleteLater()
            engine.deleteLater()

    def test_template_manager_creates_with_the_real_controller(self):
        controller = ProjectCreationController(SimpleNamespace())
        controller._catalog = {'templates': [], 'installedTemplates': []}
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        engine.rootContext().setContextProperty('projectCreationController', controller)
        windows = _Windows()
        engine.rootContext().setContextProperty('windowModel', windows)
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import QtQuick.Controls
import "." as App
ApplicationWindow {
    width: 680; height: 520; visible: true
    App.Theme { id: theme; dark: true }
    App.ProjectTemplatesView { anchors.fill: parent; theme: theme }
}''', QUrl.fromLocalFile(str(QML / '_ProjectTemplatesTest.qml')))
        owner = component.create()
        self.assertIsNotNone(owner, '\n'.join(error.toString() for error in component.errors()))
        try:
            self.app.processEvents()
            self.assertIsNotNone(owner.findChild(QObject, 'projectTemplateImport'))
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()


if __name__ == '__main__':
    unittest.main()
