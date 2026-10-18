"""Native sync input reaches the existing transfer owner and temporary filesystem."""
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
from PySide6.QtCore import QObject, Slot, QPointF, Qt, QUrl, QEvent
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from tests.frame_files_fixture import Fixture
import tests.test_repository_sync_editor as EditorFixtures
from tests.profile_ui_responsiveness import frame
from thlib.ui.repository_sync import RepositorySyncController, PreparedSyncEntry

QML = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'

def visual(item, name):
    if item.objectName() == name:
        return item
    for child in item.childItems():
        result = visual(child, name)
        if result is not None:
            return result

class Application(QObject):
    @Slot(str, result='QVariantList')
    def menu_actions(self, name):
        return [{'title': 'Retry', 'command': 'sync'}, {'title': 'Remove', 'command': 'remove'}]

class LocalFile:
    def __init__(self, path):
        self.path = path

    def is_exists(self):
        return self.path.exists()

    def prepare_repo(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return str(self.path)

class FrameSyncTests(unittest.TestCase):
    maxDiff = None
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_download_retry_cancel_input_and_virtualization(self):
        data = b'Native repository download\n' * 500
        failure = threading.Event()
        failure.set()
        stop = threading.Event()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path == '/retry' and failure.is_set():
                    self.send_error(404)
                    return
                slow = self.path == '/cancel'
                size = 1024 * 1024 if slow else len(data)
                self.send_response(200)
                self.send_header('Content-Length', str(size))
                self.end_headers()
                try:
                    if not slow:
                        self.wfile.write(data)
                    else:
                        for offset in range(0, size, 16384):
                            if stop.wait(0.005): break
                            self.wfile.write(b'x' * min(16384, size - offset))
                            self.wfile.flush()
                except (ConnectionError, OSError):
                    pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with Fixture() as fixture, tempfile.TemporaryDirectory() as tmp:
                fixture.enter_context(patch('thlib.environment.env_read_config', return_value={}))
                fixture.enter_context(patch('thlib.environment.env_write_config'))
                fixture.enter_context(patch('thlib.environment.cfg_controls.get_checkin', return_value={}))
                controller = RepositorySyncController()
                application = Application()
                records = []
                for name in ('ok', 'retry', 'cancel'):
                    path = Path(tmp) / (name + '.dat')
                    handle = controller._schedule_prepared_entry(PreparedSyncEntry(
                        file_object=LocalFile(path), process='publish', local_path=str(path),
                        web_path=f'http://127.0.0.1:{server.server_port}/{name}', title=path.name,
                        expected_size=1024 * 1024 if name == 'cancel' else len(data), expected_md5=''
                    ))
                    records.append(handle.task_id)
                controller.model.toggle_checked(2)
                engine = QQmlEngine()
                warnings = []
                engine.warnings.connect(lambda errors: warnings.extend(str(error) for error in errors))
                for key, value in dict(fixture.context(), repositorySync=controller, repoSyncModel=controller.model, appController=application).items():
                    engine.rootContext().setContextProperty(key, value)
                theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'Theme.qml')))
                theme = theme_component.createWithInitialProperties({'dark': True})
                component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'RepositorySyncView.qml')))
                view = component.createWithInitialProperties({'theme': theme})
                self.assertIsNotNone(view, '\n'.join(str(error) for error in component.errors()))
                window = QQuickWindow()
                view.setParentItem(window.contentItem())
                window.resize(1000, 800)
                view.setWidth(1000)
                view.setHeight(800)
                window.show()
                def click(name, button=Qt.LeftButton):
                    item = visual(window.contentItem(), name)
                    self.assertIsNotNone(item, name)
                    QTest.mouseClick(window, button, pos=item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint())
                    frame(window)
                def wait_for(predicate):
                    deadline = time.monotonic() + 8
                    while not predicate() and time.monotonic() < deadline:
                        self.app.processEvents()
                        QTest.qWait(5)
                    self.assertTrue(predicate())
                    frame(window)
                try:
                    frame(window)
                    self.assertEqual(warnings, [])
                    click('repositorySyncCheck_' + records[0])
                    self.assertFalse(controller.model.get(0)['checked'])
                    click('repositorySyncCheck_' + records[0])
                    click('repositorySyncStart')
                    wait_for(lambda: controller.status(records[0]) == 'finished' and controller.status(records[1]) == 'failed')
                    self.assertEqual((Path(tmp) / 'ok.dat').read_bytes(), data)
                    self.assertFalse((Path(tmp) / 'retry.dat').exists())
                    failure.clear()
                    click('repositorySyncRetry_' + records[1])
                    wait_for(lambda: controller.status(records[1]) == 'finished')
                    self.assertEqual((Path(tmp) / 'retry.dat').read_bytes(), data)
                    click('repositorySyncCheck_' + records[2])
                    click('repositorySyncStart')
                    wait_for(lambda: controller.model.get(2)['active'])
                    click('repositorySyncCancel_' + records[2])
                    wait_for(lambda: controller.status(records[2]) == 'cancelled')
                    self.assertFalse((Path(tmp) / 'cancel.dat').exists())
                    self.assertFalse(list(Path(tmp).glob('*.part*')))
                    click('repositorySyncRow_' + records[2], Qt.RightButton)
                    menu = view.findChild(QObject, 'repositorySyncContextMenu')
                    wait_for(lambda: menu.property('opened'))
                    QTest.keyClick(self.app.focusWindow() or window, Qt.Key_Escape)
                    frame(window)
                    template = controller.model.get(0)
                    controller.model.extend([dict(template, taskId=f'virtual_{index}', title=f'File {index}') for index in range(1000)])
                    frame(window)
                    lst = visual(view, 'repositorySyncQueueList')
                    self.assertLess(len(lst.property('contentItem').childItems()), 50)
                    for width in (680, 390, 1000):
                        window.resize(width, 800)
                        view.setWidth(width)
                        frame(window)
                        item = visual(view, 'repositorySyncQueue')
                        self.assertLessEqual(item.mapToScene(QPointF()).x() + item.width(), width)
                    self.assertEqual(warnings, [])
                finally:
                    controller.shutdown()
                    window.close()
                    view.deleteLater()
                    window.deleteLater()
                    theme.deleteLater()
                    self.app.sendPostedEvents(None, QEvent.DeferredDelete)
                    self.app.processEvents()
        finally:
            stop.set()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_editor_presets_scope_chunk_and_prompt_cancel(self):
        with Fixture() as fixture:
            fixture.enter_context(patch('thlib.environment.cfg_controls.get_checkin', return_value={}))
            controller, requests = EditorFixtures.RepositorySyncEditorTests().make_controller()
            controller.presets.replace([{'name': 'default', 'title': 'Default', 'data': {}}])
            controller.select_preset(0)
            sync = RepositorySyncController()
            application = Application()
            engine = QQmlEngine()
            warnings = []
            engine.warnings.connect(lambda errors: warnings.extend(str(error) for error in errors))
            for key, value in dict(fixture.context(), repositorySyncEditorController=controller,
                                   repositorySyncPresetModel=controller.presets, repositorySyncTreeModel=controller.model,
                                   repositorySync=sync, repoSyncModel=sync.model, appController=application).items():
                engine.rootContext().setContextProperty(key, value)
            theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'Theme.qml')))
            theme = theme_component.createWithInitialProperties({'dark': True, 'popupAnimationsEnabled': False})
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'RepositorySyncEditorView.qml')))
            view = component.createWithInitialProperties({'theme': theme, 'windowId': 'repository_sync_editor'})
            self.assertIsNotNone(view, '\n'.join(str(error) for error in component.errors()))
            window = QQuickWindow()
            window.resize(1000, 800)
            view.setParentItem(window.contentItem())
            view.setWidth(1000)
            view.setHeight(800)
            window.show()
            def click(name):
                item = visual(window.contentItem(), name)
                self.assertIsNotNone(item, name)
                QTest.mouseClick(window, Qt.LeftButton, pos=item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint())
                frame(window)
            try:
                frame(window)
                self.assertEqual(warnings, [])
                panel = visual(view, 'repositorySyncProcessPanel')
                self.assertIsNotNone(panel)
                panel.setProperty('togglersExpanded', True)
                frame(window)
                click('repositorySyncPresetAddButton')
                dialog = view.findChild(QObject, 'repositorySyncCreatePresetDialog')
                self.assertTrue(dialog.property('opened'))
                QTest.keyClick(window, Qt.Key_Escape)
                frame(window)
                self.assertEqual(controller.presets.count(), 1)
                click('repositorySyncScope_partial')
                self.assertEqual(controller.scopeMode, 'partial')
                spin = visual(view, 'repositorySyncChunkSize')
                self.assertIsNotNone(spin)
                input_item = visual(spin, 'spinBoxTextInput')
                QTest.mouseClick(window, Qt.LeftButton, pos=input_item.mapToScene(QPointF(input_item.width()/2, input_item.height()/2)).toPoint())
                QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
                QTest.keyClick(window, Qt.Key_1)
                click('repositorySyncEditorStart')
                self.assertEqual(requests.calls[-1][1]['partial_chunk_size'], 1)
                self.assertEqual(requests.calls[-1][1]['scope_mode'], 'partial')
                self.assertEqual(visual(view, 'repositorySyncOnlyUpdatesText').property('text'), 'Only updates')
                click('repositorySyncOnlyUpdatesText')
                self.assertTrue(controller.onlyUpdates)
                for width in (680, 390, 1000):
                    window.resize(width, 800)
                    view.setWidth(width)
                    frame(window)
                    self.assertFalse(visual(visual(view, 'repositorySyncEditorStart'), 'buttonLabel').property('truncated'))
                    for name in ('repositorySyncProcessSlot', 'repositorySyncQueuePanel'):
                        item = visual(view, name)
                        box = item.mapToScene(QPointF())
                        self.assertGreaterEqual(box.x(), 0)
                        self.assertLessEqual(box.x() + item.width(), width)
                        self.assertLessEqual(box.y() + item.height(), 800)
                self.assertEqual(warnings, [])
            finally:
                sync.shutdown()
                window.close()
                view.deleteLater()
                window.deleteLater()
                theme.deleteLater()
                self.app.sendPostedEvents(None, QEvent.DeferredDelete)
                self.app.processEvents()

if __name__ == '__main__':
    unittest.main()
