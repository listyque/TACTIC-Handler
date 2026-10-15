"""Large diagnostics must preserve their text without blocking Qt rendering."""
from pathlib import Path
import os
import subprocess
import sys
import unittest


class ErrorDialogRendering(unittest.TestCase):
    def test_large_fault_remains_responsive_and_copyable(self):
        environment = dict(os.environ, QT_QPA_PLATFORM='offscreen',
                           QT_QUICK_CONTROLS_STYLE='Material')
        # Exercise the platform render thread, independently of other QML tests.
        for key in ('QT_QUICK_BACKEND', 'QSG_RENDER_LOOP', 'QSG_RHI_BACKEND'):
            environment.pop(key, None)
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', __file__, '--probe'],
                                env=environment, capture_output=True, text=True,
                                encoding='utf-8', timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('TypeError:', result.stderr)
        self.assertNotIn('ReferenceError:', result.stderr)
        self.assertNotIn('Binding loop', result.stderr)


def probe():
    import json
    import tempfile
    import time
    from unittest.mock import patch
    from xmlrpc.client import Fault
    from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QTimer, QUrl
    from PySide6.QtGui import QFontDatabase, QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    from PySide6.QtQuick import QQuickWindow
    from PySide6.QtTest import QTest
    from thlib.environment import env_mode
    from thlib.ui.debug_logging import DebugLogController

    app = QGuiApplication([])
    if os.name == 'nt':
        QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
    qml = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'
    with tempfile.TemporaryDirectory() as directory, \
            patch('thlib.ui.debug_logging.env_read_config', return_value={}), \
            patch('thlib.ui.debug_logging.env_write_config'), \
            patch.object(env_mode, 'current_path', directory):
        log = DebugLogController(Path(directory))
        log.set_recording_levels(['EXCEPTION'])
        engine = QQmlEngine()
        engine.addImportPath(str(qml))
        context = engine.rootContext()
        for name, value in [('debugLog', log), ('debugEntryModel', log.entries_model),
                            ('debugGroupModel', log.groups_model), ('debugSessionModel', log.sessions_model)]:
            context.setContextProperty(name, value)
        theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / 'Theme.qml')))
        theme = theme_component.createWithInitialProperties({'dark': True})
        components, views = [], []
        window = QQuickWindow()
        window.resize(1200, 850)

        def create(name):
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / name)))
            view = component.createWithInitialProperties({'theme': theme})
            assert view is not None, [e.toString() for e in component.errors()]
            view.setParentItem(window.contentItem())
            view.setWidth(window.width())
            view.setHeight(window.height())
            components.append(component)
            views.append(view)
            return view

        view = create('ErrorDialog.qml')
        window.show()
        paths = [f'D:/source/episodes/Episode 01 — Arrival/versions/shot/test_source_file_{i:04d}_'
                 + 'abcdefghij' * 8 + '.abc' for i in range(10000)]
        source = 'def checkin():\n    return create_snapshot_extended(files_info=' + repr(json.dumps({'version_files': paths})) + ')\n'
        command = 'import thlib.tactic_classes as tc\ntc.server_start().execute_python_script("", kwargs=' + repr({'code': source}) + ')'
        trace = 'Traceback (most recent call last):\n' + source + '\nSObjectException: test failure'
        fault = Fault(500, trace)
        errors, beats = [], [time.monotonic()]
        timer = QTimer()
        timer.setInterval(50)
        timer.timeout.connect(lambda: beats.append(time.monotonic()))
        timer.start()

        def checked(action):
            try:
                action()
            except Exception as error:
                import traceback
                traceback.print_exc()
                errors.append(error)
                app.quit()

        def show():
            log.raise_error(fault, stacktrace=trace, command=command)

        def narrow_and_copy():
            assert log.error_message == str(fault)
            assert log.error_stacktrace == trace
            assert log.error_command == command
            def descendants(item):
                yield item
                for child in item.childItems():
                    yield from descendants(child)
            areas = [item for item in descendants(view) if item.objectName() == 'errorRequestCode']
            assert len(areas) == 2
            area = next(item for item in areas if item.property('text') == source)
            area.forceActiveFocus()
            QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
            QTest.keyClick(window, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
            assert app.clipboard().text() == source
            button = view.findChild(QObject, 'copyErrorStacktrace')
            body = view.findChild(QObject, 'errorBodyFlickable')
            position = button.mapToScene(QPointF(button.width()/2, button.height()/2))
            body.setProperty('contentY', body.property('contentY') + position.y() - body.height()/2)
            app.processEvents()
            position = button.mapToScene(QPointF(button.width()/2, button.height()/2))
            QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                             QPoint(round(position.x()), round(position.y())))
            assert app.clipboard().text() == trace
            body.setProperty('contentY', 0)
            window.resize(360, 850)
            view.setWidth(360)
            assert not window.grabWindow().isNull()

        def show_log():
            view.setVisible(False)
            window.resize(1200, 850)
            log.set_visible(True)
            log.select_entry(log.entries_model.rowCount() - 1)
            assert log.selected_entry['command'] == command
            create('DebugLogView.qml')
            log.copy_selected_command()
            assert app.clipboard().text() == command

        def finish():
            assert not window.grabWindow().isNull()
            gaps = [b-a for a,b in zip(beats, beats[1:])]
            assert len(beats) > 20, len(beats)
            assert max(gaps) < 10, max(gaps)
            log.shutdown()
            record = log._read_session_records(log._json_log)[-1]
            assert record['message'] == str(fault)
            assert record['command'] == command
            assert record['stacktrace'] == trace
            print(json.dumps({'max_heartbeat_gap_seconds': max(gaps), 'fault_characters': len(str(fault))}))
            window.close()
            app.quit()

        for delay, action in [(100, show), (5000, narrow_and_copy), (10000, show_log), (15000, finish)]:
            QTimer.singleShot(delay, lambda fn=action: checked(fn))
        app.exec()
        log.shutdown()
        assert not errors, errors


if __name__ == '__main__':
    if '--probe' in sys.argv:
        probe()
    else:
        unittest.main()
