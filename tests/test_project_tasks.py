"""Native task creation without a selected object uses its real project owner."""
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import QPointF, QUrl, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow, QQuickItem
from PySide6.QtTest import QTest
from pathlib import Path
from thlib.environment import env_inst, env_mode
import thlib.tactic_classes as tc
from thlib.ui.tasks import TasksController
from thlib.ui.workspace_models.records import RecordListModel
import tests.test_tasks_controller as fixture


class ProjectTaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.enterContext(patch.object(env_mode, 'current_path', temp.name))
        self.application = fixture.FakeApplication()
        self.application.workspace_state._selected_sobject = None
        self.application.workspace_state._task_sobjects = []
        self.project = tc.Project({'code': 'test', 'title': 'Files', 'type': 'file_project',
                                   '__search_key__': 'sthpw/project?code=test'})
        self.project.workflow = fixture.FakeWorkflow()
        self.project.stypes = {}
        self.enterContext(patch.object(env_inst, 'get_project_by_code', return_value=self.project))
        self.controller = TasksController(self.application)

    def test_create_save_reload_and_inspector(self):
        self.assertTrue(self.controller.canCreateAdvancedTask)
        self.assertTrue(self.controller.create_advanced_task_draft())
        row = self.controller.table_model._records[0]
        code = row['taskCode']
        self.assertEqual(row['parentKey'], 'sthpw/project?code=test')
        self.assertEqual(row['process'], 'task')
        self.assertEqual(row['taskPipeline'], 'task')
        self.assertTrue(row['statusChoices'])
        self.controller.stage_advanced_value(code, 'description', 'Fix depot import')
        info = fixture.FakeTask(code='TASK_NEW', description='Fix depot import').get_info()
        info.update(search_type='sthpw/project', search_code='test', project_code='test', process='task')
        with patch.object(env_inst.server_pool, 'add_task', side_effect=lambda operation: fixture.ImmediateWorker(operation)), \
                patch.object(tc, 'insert_sobjects', return_value=info) as insert:
            self.assertTrue(self.controller.save_advanced_changes())
            QGuiApplication.processEvents()
        self.assertEqual(insert.call_args.kwargs['parent_key'], 'sthpw/project?code=test')
        self.assertEqual(insert.call_args.args[1], 'test')
        self.assertEqual(insert.call_args.args[2]['pipeline_code'], 'task')
        self.assertEqual(self.controller.advancedDirtyCount, 0, self.controller.advancedError)
        self.assertIn('TASK_NEW', self.controller._advanced_tasks)
        self.controller.open_notes('sthpw/project?code=test', 'task', 'TASK_NEW')
        self.assertEqual(self.application.opened_search_keys[-1], ('sthpw/project?code=test', 'task'))

    def test_project_draft_uses_worker_catalog_without_loading_search_schema(self):
        self.project.workflow = None
        self.project.get_stypes = lambda: self.fail("Project task must not query schema on the UI thread")
        self.controller._task_field_catalogs['test'] = {'statusChoices': [
            {'value': 'Ready', 'label': 'Ready', 'color': '#123456'}]}
        self.assertTrue(self.controller.create_advanced_task_draft())
        self.assertEqual(self.controller.table_model._records[0]['statusChoices'][0]['value'], 'Ready')
        self.controller._task_field_catalogs['test']['statusChoices'][0]['value'] = 'Working'
        self.controller._refresh_advanced_raw_preserving_inserts()
        self.controller._rebuild_advanced_models()
        self.assertEqual(self.controller.table_model._records[0]['statusChoices'][0]['value'], 'Working')

    def test_worker_field_catalog_returns_project_status_choices(self):
        from thlib.ui.task_workspace.field_catalog import load_task_field_catalog
        widgets = {"InputWidgets": [{"name": "status", "__display_values__": {
            "values": ["Ready", "Working"], "labels": ["Ready", "Working"]}}]}
        with patch.object(tc, "execute_procedure_serverside", return_value=widgets):
            catalog = load_task_field_catalog("test", include_milestones=False)
        self.assertEqual([item["value"] for item in catalog["statusChoices"]], ["Ready", "Working"])

    def test_real_qml_plus_creates_project_draft_without_selection(self):
        qml = Path(__file__).parents[1] / 'thlib/ui/qml'
        engine = QQmlEngine()
        engine.addImportPath(str(qml))
        for name, value in {'tasksController': self.controller,
                            'advancedTaskModel': self.controller.advanced_model,
                            'advancedTaskTableModel': self.controller.table_model,
                            'taskGanttModel': self.controller.gantt_model,
                            'userListModel': RecordListModel(('login', 'displayName', 'initials', 'avatarUrl'))}.items():
            engine.rootContext().setContextProperty(name, value)
        theme = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / 'Theme.qml'))).createWithInitialProperties({'dark': True})
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / 'TasksWorkspaceView.qml')))
        view = component.createWithInitialProperties({'theme': theme, 'embedded': True})
        self.assertIsNotNone(view, str(component.errors()))
        window = QQuickWindow()
        view.setParentItem(window.contentItem())
        window.resize(900, 560)
        view.setSize(window.size())
        window.show()
        QTest.qWait(40)
        button = view.findChild(QQuickItem, 'taskWorkspaceCreateButton')
        self.assertTrue(button.isEnabled())
        point = button.mapToScene(QPointF(button.width()/2, button.height()/2)).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, pos=point)
        QTest.qWait(30)
        self.assertEqual(self.controller.advancedDirtyCount, 1)
        self.assertEqual(self.controller.table_model._records[0]['parentKey'], 'sthpw/project?code=test')
        window.close()
        view.deleteLater()
        window.deleteLater()
