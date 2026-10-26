"""Actual native request controls and captured context; no provider is required."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json
import os
import time
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, Qt, Signal, QMimeData, QUrl, QPoint, QPointF, QCoreApplication
from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication, QImage, QColor, QDragEnterEvent, QDropEvent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.test_frame_script_tools import ScriptToolsTests, QML
from tests.profile_ui_responsiveness import frame
from thlib.ui.agent_request import AgentRequestController
from thlib.ui.controllers.types import ActionRegistry
from thlib.ui.workspace_models.windows import FloatingWindowModel
from thlib.ui.icon_font import qml_icon_bindings
from thlib.environment import env_inst


class Application(QObject):
    authentication_changed = Signal()
    signing_out = Signal()
    notification_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._registry = ActionRegistry()
        self.window_model = FloatingWindowModel({})
        self.current_project_code = 'one'
        self.can_administer = True
        self.section = SimpleNamespace(entry_key='cg/shot@shots', title='Shots', search_type='cg/shot')
        self.tab = SimpleNamespace(table_view='table')
        self.keys = ['cg/shot?project=one&code=SH001']

    def _current_section(self):
        return self.section

    def _current_tab(self):
        return self.tab

    def script_shelf_context(self):
        return dict(search_keys=list(self.keys))


class Server:
    def __init__(self):
        self.requests = {}
        self.last = None
        self.files = {}

    def execute_cmd(self, command, values):
        action = values['action']
        if 'AgentAttachmentCmd' in command:
            code = values['attachment_id']
            if action == 'start':
                self.files[code] = dict(attachment_id=code, name=values['name'], size=values['size'], media_type=values['media_type'])
            result = self.files[code]
        elif action == 'state':
            result = dict(hosts=[dict(host_id='host', label='Codex', capabilities=dict(changes=True, trials=False, steering=True, models=[dict(id='fixture',label='Fixture model', is_default=True, efforts=['low', 'high'])]))],
                requests=[dict(request_id=key, prompt=row['document']['prompt'], status=row['status']) for key, row in self.requests.items()])
        elif action == 'submit':
            result = dict(request_id=values['request_id'], document=deepcopy(values['document']),
                          model=values['document'].get('model', ''), effort=values['document'].get('effort', ''),
                          status='running', events=['External agent started'], answer='', error='',
                          messages=[dict(id=values['request_id'], role='user', text=values['document']['prompt'],
                              attachments=[self.files[code] for code in values['document'].get('attachments', [])])])
            self.requests[result['request_id']] = result
            self.last = result
        elif action == 'message':
            result = self.requests[values['request_id']]
            result.update(model=values.get('model', ''), effort=values.get('effort', ''))
            result['messages'].append(dict(id=values['message_id'], role='user', text=values['text'], attachments=[]))
            result['status'] = 'running'
        elif action == 'cancel':
            result = self.requests[values['request_id']]
            result['status'] = 'cancelled'
        else:
            result = self.requests[values['request_id']]
        return dict(status='OK', info=deepcopy(result))


class AgentRequestUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ScriptToolsTests.setUpClass()

    def test_context_real_input_submission_cancel_reopen_and_stale_reply(self):
        surface = ScriptToolsTests()
        surface.setUp()
        self.addCleanup(surface.doCleanups)
        for name, value in qml_icon_bindings(QML.parents[2], surface.engine).items():
            surface.engine.rootContext().setContextProperty(name, value)
        if os.name == 'nt':
            for name in ('segoeui.ttf', 'segoeuib.ttf'):
                QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR'])/'Fonts'/name))
            surface.app.setFont(QFont('Segoe UI'))
        app = Application()
        notices = []
        app.notification_changed.connect(notices.append)
        controller = AgentRequestController(app, env_inst.server_pool)
        self.addCleanup(controller.reset)
        server = Server()
        with patch('thlib.tactic_classes.server_start', return_value=server):
            controller.open()
            view = surface.create(QML/'features/scripts/AgentRequestView.qml',
                dict(theme=surface.theme, controller=controller, width=1000, height=650))
            window = QQuickWindow()
            window.resize(1000, 650)
            window.setColor(surface.theme.property('workspace'))
            surface.windows.append(window)
            view.setParentItem(window.contentItem())
            window.show()
            window.requestActivate()

            def wait():
                deadline = time.monotonic() + 10
                while controller._in_flight and time.monotonic() < deadline:
                    QTest.qWait(10)
                self.assertFalse(controller._in_flight)
                self.assertFalse(controller.model['error'], controller.model)
                frame(window)

            wait()
            choice = surface.item(view, 'agentRequestModel')
            choice.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            self.assertEqual(controller.model['model'], 'fixture')
            effort = surface.item(view, 'agentRequestEffort')
            effort.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            surface.item(view, 'agentRequestEffort').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            self.assertEqual(controller.model['effort'], 'high')
            clipboard = QGuiApplication.clipboard()
            saved_clipboard = QMimeData()
            original = clipboard.mimeData()
            for format in original.formats() if original else []:
                saved_clipboard.setData(format, original.data(format))
            if original and original.formats():
                self.addCleanup(clipboard.setMimeData, saved_clipboard)
            else:
                self.addCleanup(clipboard.clear)
            image = QImage(32, 32, QImage.Format_RGB32)
            image.fill(QColor('red'))
            clipboard.setImage(image)
            surface.item(view, 'agentRequestPrompt').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_V, Qt.ControlModifier)
            wait()
            self.assertEqual(len(controller.model['attachments']), 1)
            self.assertTrue(controller.model['previews'])
            with tempfile.TemporaryDirectory(prefix='native-agent-drop-') as directory:
                path = Path(directory)/'dropped.bin'
                path.write_bytes(b'Native drop fixture')
                mime = QMimeData()
                mime.setUrls([QUrl.fromLocalFile(str(path))])
                enter = QDragEnterEvent(QPoint(400, 250), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
                QCoreApplication.sendEvent(window, enter)
                surface.app.processEvents()
                drop = QDropEvent(QPointF(400, 250), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
                QCoreApplication.sendEvent(window, drop)
                wait()
                self.assertTrue(drop.isAccepted())
                self.assertEqual(len(controller.model['attachments']), 2)
            surface.fill(window, surface.item(view, 'agentRequestPrompt'), 'Explain the selected shots')
            surface.click(window, surface.item(view, 'agentRequestChanges'))
            self.assertTrue(controller.model['allowChanges'])
            self.assertEqual(controller.model['prompt'], 'Explain the selected shots')
            controller._request('poll')
            wait()
            self.assertEqual(controller.model['prompt'], 'Explain the selected shots')
            surface.click(window, surface.item(view, 'agentRequestSend'))
            wait()
            self.assertEqual(server.last['document']['context']['search_keys'], app.keys)
            self.assertEqual(server.last['document']['effort'], 'high')
            self.assertFalse(surface.item(view, 'agentRequestEffort').isEnabled())
            self.assertEqual(server.last['document']['context']['page'], 'cg/shot@shots')
            self.assertEqual(len(server.last['document']['attachments']), 2)
            surface.fill(window, surface.item(view, 'agentRequestPrompt'), 'Use the reference process')
            surface.click(window, surface.item(view, 'agentRequestSend'))
            wait()
            self.assertEqual(server.last['messages'][-1]['text'], 'Use the reference process')
            server.last.update(status='completed', outcome='completed', answer='**Done**')
            server.last['messages'].append(dict(id='answer', role='assistant', text='**Done**', attachments=[]))
            controller._request('poll')
            wait()
            self.assertIn('Task completed', notices)
            surface.item(view, 'agentRequestModel').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Up)
            frame(window)
            self.assertEqual(controller.model['model'], '')
            self.assertEqual(controller.model['effort'], '')
            self.assertEqual(surface.item(view, 'agentRequestEffort').property('currentIndex'), 0)
            surface.item(view, 'agentRequestEffort').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            surface.fill(window, surface.item(view, 'agentRequestPrompt'), 'Summarize the result')
            surface.click(window, surface.item(view, 'agentRequestSend'))
            wait()
            self.assertEqual(len(server.last['messages']), 4)
            self.assertEqual(server.last['model'], '')
            self.assertEqual(server.last['effort'], 'low')
            app.current_project_code = 'two'
            app.keys = ['cg/shot?project=two&code=OTHER']
            self.assertEqual(controller.model['request']['document']['context']['project'], 'one')
            surface.click(window, surface.item(view, 'agentRequestCancel'))
            wait()
            self.assertEqual(controller.model['request']['status'], 'cancelled')
            controller.application.window_model.close_window('agent_request')
            controller.open()
            wait()
            self.assertEqual(controller.model['request']['document']['context']['project'], 'one')
            for width in (520, 1000):
                view.setWidth(width)
                window.resize(width, 650)
                frame(window)
                self.assertGreater(surface.item(view, 'agentRequestOutput').height(), 0)
            output = os.environ.get('TACTIC_AGENT_CAPTURE')
            if output:
                capture = dict(controller.model)
                Path(output).mkdir(parents=True, exist_ok=True)
                Path(output, 'native-model.json').write_text(json.dumps(capture, ensure_ascii=False), encoding='utf-8')
                paired = Path(output, 'browser-model.json')
                if paired.is_file():
                    controller._model = json.loads(paired.read_text(encoding='utf-8'))
                    controller.changed.emit()
                    frame(window)
                    self.assertEqual(surface.item(view, 'agentRequestHistory').property('currentIndex'), 1)
                window.grabWindow().save(str(Path(output, 'native.png')))
            generation = controller._generation
            controller.reset()
            controller._done(dict(generation=generation, selected='stale', request={}, hosts=[], requests=[]))
            self.assertEqual(controller.model['selected'], '')
            with patch('thlib.tactic_classes.server_start', side_effect=PermissionError('Session expired')):
                controller.open()
                self.assertEqual(controller.model['error'], 'Session expired')
            controller.deleteLater()
            app.deleteLater()
            self.assertFalse(surface.warnings, surface.warnings)


if __name__ == '__main__':
    unittest.main()
