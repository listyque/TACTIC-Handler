"""Real System Info QML input and stale/denied read handling."""
from copy import deepcopy
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import tempfile

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.test_frame_script_tools import ScriptToolsTests, QML
from tests.test_agent_request import Application, isolate_chat_settings
from tests.profile_ui_responsiveness import frame
from thlib.environment import env_inst
from thlib.ui.system_info import SystemInfoController, CLASS
from thlib.ui.icon_font import qml_icon_bindings

FACTS = dict(sections=[dict(title='Server', fields=[['OS', 'Fixture OS'], ['Node Name', 'fixture']]),
    dict(title='Asset Folders', fields=[['default', '/fixture/' + 'long-path/' * 20],
        ['Writable (access check)', False]])], cpuCount=2, mailConfigured=True,
    mailFrom='fixture@example.invalid', links=[dict(name='shots',title='Shots',url='/projects/one/?system_link=shots')],
    internalLinks=[dict(name='shots',title='Shots',url='/projects/one/?system_link=shots')])


class SystemApplication(Application):
    project_changed = Signal(str,str)


class Server:
    def __init__(self, log=None, **_kwargs):
        self.calls = 0
        self.error = ''
        self.log = log if log is not None else []
        self.protocol = 'xmlrpc'
        self.transport = SimpleNamespace(proxy={})
        self.login_ticket = 'fixture'
        self.site = None

    def get_server_name(self): return 'http://fixture.invalid'
    def set_transport(self, value): self.transport = value
    def set_server(self, value): pass
    def set_project(self, value): pass
    def set_ticket(self, value): pass

    def execute_class_method(self, class_name, method, kwargs):
        assert class_name == CLASS
        self.log.append((method,deepcopy(kwargs)))
        self.calls += 1
        if self.error:
            raise RuntimeError(self.error)
        if method == 'get_info': return deepcopy(FACTS)
        if method == 'connection_probe': return dict(node='fixture',pid=1,port='8081')
        if method == 'performance_probe': return dict(rows=1,columns=2)
        if method == 'run_test': return dict(message='Script completed')
        raise AssertionError(method)


class SystemInfoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ScriptToolsTests.setUpClass()

    def test_native_refresh_copy_narrow_error_close_and_permission(self):
        isolate_chat_settings(self)
        surface = ScriptToolsTests(); surface.setUp(); self.addCleanup(surface.doCleanups)
        for name, value in qml_icon_bindings(QML.parents[2], surface.engine).items():
            surface.engine.rootContext().setContextProperty(name, value)
        app = SystemApplication()
        controller = SystemInfoController(app, env_inst.server_pool)
        self.addCleanup(controller.shutdown)
        server = Server()
        with patch('thlib.tactic_classes.server_start', return_value=server):
            controller.open()
            def wait():
                deadline = time.monotonic() + 10
                while controller.model['busy'] and time.monotonic() < deadline:
                    QTest.qWait(5)
                self.assertFalse(controller.model['busy'])
            wait()
            self.assertFalse(controller.model['error'], controller.model)
            self.assertEqual(server.calls, 1)
            view = surface.create(QML/'SystemInfoView.qml', dict(theme=surface.theme,
                controller=controller, width=800, height=600))
            window = QQuickWindow(); window.resize(800,600); surface.windows.append(window)
            view.setParentItem(window.contentItem()); window.show(); frame(window)
            for width in (320,800):
                window.resize(width,600); view.setWidth(width); frame(window)
                copy = surface.item(view, 'systemCopy')
                self.assertLessEqual(copy.x()+copy.width(), width)
                value = surface.item(view, 'systemValue_1')
                self.assertIn('Fixture OS', value.property('text'))
                surface.click(window, copy)
                self.assertIn('Fixture OS', QGuiApplication.clipboard().text())
                surface.item(view, 'systemRefresh').forceActiveFocus()
                QTest.keyClick(window, Qt.Key_Space); wait(); frame(window)
            self.assertEqual(server.calls, 3)
            QTest.qWait(100)
            self.assertEqual(server.calls, 3, 'No idle polling')
            server.error = 'Fixture disconnected'
            surface.click(window, surface.item(view, 'systemRefresh')); wait(); frame(window)
            self.assertEqual(controller.model['error'], server.error)
            self.assertFalse(surface.item(view, 'systemCopy').property('enabled'))
            generation = controller._generation
            app.window_model.close_window('system_info')
            controller.done(dict(generation=generation, sections=FACTS['sections']))
            self.assertEqual(controller.model['sections'], [])
            app.can_administer = False
            controller.open()
            self.assertFalse(app.window_model.is_window_visible('system_info'))
            self.assertFalse(surface.warnings, surface.warnings)

    def test_all_legacy_action_buttons_and_fields_use_native_controls(self):
        isolate_chat_settings(self)
        from PySide6.QtCore import QPointF
        surface = ScriptToolsTests(); surface.setUp(); self.addCleanup(surface.doCleanups)
        for name,value in qml_icon_bindings(QML.parents[2],surface.engine).items():
            surface.engine.rootContext().setContextProperty(name,value)
        app=SystemApplication(); app.server_url='http://fixture.invalid'
        controller=SystemInfoController(app,env_inst.server_pool); self.addCleanup(controller.shutdown)
        server=Server()
        with tempfile.TemporaryDirectory(prefix='handoff-fixture-') as directory, \
                patch('thlib.environment.env_server.get_proxy',return_value={}), \
                patch('thlib.tactic_classes.server_start',return_value=server), \
                patch('thlib.tactic_classes.TacticServerStub',side_effect=lambda **kwargs:Server(server.log,**kwargs)), \
                patch('PySide6.QtGui.QDesktopServices.openUrl',return_value=True) as opened:
            controller.open()
            def wait():
                deadline=time.monotonic()+10
                while controller.model['busy'] and time.monotonic()<deadline: QTest.qWait(5)
                self.assertFalse(controller.model['busy'])
            wait()
            controller._model['directories']={'win32':{'client_repo_dir':directory,'client_handoff_dir':directory}}
            view=surface.create(QML/'SystemInfoView.qml',dict(theme=surface.theme,controller=controller,width=800,height=600))
            window=QQuickWindow();window.resize(800,600);surface.windows.append(window)
            view.setParentItem(window.contentItem());window.show();frame(window)
            def reveal(name):
                item=surface.item(view,name); scroll=surface.item(view,'systemBody')
                point=item.mapToItem(scroll,QPointF(0,0))
                scroll.setProperty('contentY',max(0,scroll.property('contentY')+point.y()-40));frame(window)
                return item
            def click(name):
                surface.click(window,reveal(name));wait();frame(window)
            click('systemBalanceTest')
            self.assertEqual(len(controller.model['results']['balance']['samples']),50)
            for width in (320, 800):
                window.resize(width, 600); view.setWidth(width); frame(window)
                summary = surface.item(view, 'systemBalanceTestResult')
                self.assertIn('This sample does not show', summary.property('text'))
                self.assertLessEqual(summary.property('contentHeight'), summary.height())
            click('systemPerformanceTest')
            self.assertEqual(controller.model['results']['performance']['count'],2)
            self.assertEqual(sum(method=='performance_probe' for method,_ in server.log),4)
            click('systemEmailTest')
            self.assertIn(('run_test',{'action':'email','values':{'sender':'fixture@example.invalid','recipients':'fixture@example.invalid'}}),server.log)
            field=reveal('systemScriptPath');surface.click(window,field)
            for char in 'tests/probe': QTest.keyClick(window,char)
            click('systemScriptTest')
            self.assertIn(('run_test',{'action':'script','values':{'path':'tests/probe'}}),server.log)
            click('systemHandoffTest')
            self.assertTrue(all(row['available'] for row in controller.model['results']['handoff']['paths']))
            reveal('systemIncludeInternal').forceActiveFocus();frame(window)
            QTest.keyClick(window,Qt.Key_Space);frame(window)
            self.assertTrue(controller.model['includeInternal'])
            click('systemIncludeInternal')
            self.assertFalse(controller.model['includeInternal'])
            QTest.keyClick(window,Qt.Key_Space);frame(window)
            click('systemLinkTest')
            self.assertEqual(opened.call_count,1)
            click('systemOpenLink_0')
            self.assertEqual(opened.call_count,2)
            self.assertFalse(any(values.get('action') == 'clear_sidebar' for _, values in server.log))
            self.assertIsNone(view.findChild(QObject, 'systemClearSidebar'))
            self.assertTrue(app.window_model.is_window_visible('system_info'))
            app.project_changed.emit('two','Two')
            self.assertFalse(app.window_model.is_window_visible('system_info'))
            self.assertEqual(controller.model['sections'],[])
            self.assertFalse(surface.warnings,surface.warnings)


if __name__ == '__main__':
    unittest.main()
