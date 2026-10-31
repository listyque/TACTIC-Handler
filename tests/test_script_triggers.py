import os
from copy import deepcopy
from pathlib import Path
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")

from PySide6.QtCore import QObject, QPointF, Property, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.script_triggers import (
    ScriptTriggerController,
    _project_rule,
)
import thlib.tactic_classes as tc
from thlib.ui.workspace_models.records import RecordListModel


QML = Path(__file__).resolve().parents[1] / "thlib" / "ui" / "qml"


class _Windows(QObject):
    windowVisibilityChanged = Signal(str, bool)

    def __init__(self):
        super().__init__()
        self.help_topics = []

    def show_child_window(self, _window_id, _parent_id):
        pass

    @Slot(str)
    def open_help(self, topic):
        self.help_topics.append(topic)


class _Application(QObject):
    project_changed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.current_project_code = ""
        self.window_model = _Windows()
        self.notifications = []

    def _notify(self, message):
        self.notifications.append(str(message))


class _Users:
    canManageUsers = True


class _Scripts(QObject):
    stateChanged = Signal()

    def __init__(self):
        super().__init__()
        self.trigger_outputs = []
        self.shelfScriptOptions = [
            {"value": "tools/one", "label": "tools/one", "language": "local_python"},
            {"value": "tools/two", "label": "tools/two", "language": "local_python"},
            {"value": "maya/open", "label": "maya/open", "language": "dcc_python"},
        ]
        self.model = RecordListModel((
            "nodeType", "path", "folder", "title", "language", "depth",
            "expanded", "hasChildren",
        ))

    def saved_script_definition(self, path):
        option = next((
            item for item in self.shelfScriptOptions
            if item["value"] == path
        ), None)
        return {
            "path": path,
            "language": option["language"],
            "source": "RESULT = TACTIC_SCRIPT_KWARGS['event']",
        } if option else {}

    @Slot(str)
    def set_tree_filter(self, _value):
        pass

    @Slot(str)
    def toggle_folder(self, _path):
        pass

    @Slot(str, str)
    def append_trigger_output(self, path, output):
        self.trigger_outputs.append((path, output))


class _Server:
    def __init__(self):
        self.records = []
        self.stream = True
        self.ticket = 'fixture-ticket'

    def class_exists(self, owner):
        return self.stream

    def start(self, title):
        self.before = deepcopy(self.records)

    def finish(self):
        pass

    def abort(self):
        self.records = self.before
        self.ticket = None

    def get_login_ticket(self):
        return 'fixture-ticket'

    def set_login_ticket(self, ticket):
        assert ticket == 'fixture-ticket'
        self.ticket = ticket

    def execute_cmd(self, owner, values):
        assert owner == 'tactic.ui.panel.handler_automation_cmd.HandlerAutomationCmd'
        assert values['expected_revision'] == 'original-server-revision'
        assert values['operation_id']
        self.records = []
        import json
        for rule in values['rules']:
            self.insert('config/trigger', dict(trigger_type='handler_script_hook', script_path=rule['script'],
                title=rule['title'], data=json.dumps(dict(version=1, action=rule['action'], phase=rule['phase']))))
        return dict(status='OK', info=dict(records=self.records, revision='saved-server-revision'))

    def query(self, search_type, _filters, show_retired=False):
        assert search_type == "config/trigger"
        assert show_retired
        return [row for row in self.records if row['trigger_type'] == 'handler_script_hook']

    def insert(self, search_type, data, triggers=True):
        assert search_type == "config/trigger"
        assert triggers
        record = {
            **data,
            "code": "TRIGGER{:04d}".format(len(self.records) + 1),
        }
        self.records.append(record)
        return record

    def build_search_key(self, search_type, code, project_code=""):
        return f"{search_type}?project={project_code}&code={code}"

    def update(self, search_key, data, triggers=True):
        assert triggers
        code = search_key.rsplit("=", 1)[-1]
        for record in self.records:
            if record["code"] == code:
                record.update(data)

    def delete_sobject(self, search_key):
        code = search_key.rsplit("=", 1)[-1]
        self.records = [
            record for record in self.records if record["code"] != code
        ]


def _rule(identity, script, *, phase="before", order=0, action="object.update"):
    return {
        "ruleId": identity,
        "code": identity,
        "title": identity,
        "description": "",
        "action": action,
        "phase": phase,
        "searchType": "demo/asset",
        "searchKeysText": "",
        "process": "",
        "context": "",
        "script": script,
        "enabled": True,
        "order": order,
        "valid": True,
        "error": "",
        "summary": "",
    }


class ScriptTriggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.application = _Application()
        self.scripts = _Scripts()
        self.controller = ScriptTriggerController(
            self.application, _Users(), self.scripts, None, None
        )

    def test_legacy_project_reads_saves_and_runs_hooks_without_stream_commands(self):
        server = _Server()
        server.stream = False
        server.records = [dict(code='OTHER', trigger_type='other')]
        self.controller._project_code = 'demo'
        self.controller._run_server = lambda operation, handler: handler(operation())
        with patch.object(tc, 'server_start', return_value=server):
            self.controller.refresh()
            self.assertTrue(self.controller.canManage)
            self.assertFalse(self.controller.error)
            self.assertFalse(self.application.notifications)
            rule = _rule('new', 'tools/one')
            rule['code'] = ''
            rule['title'] = 'Legacy hook'
            self.controller.rules.replace(self.controller._present([rule]))
            self.controller.save()
            self.controller.refresh()
            self.assertEqual(self.controller.rules.records()[0]['title'], 'Legacy hook')
            calls = []
            self.controller._execute_rule = lambda rule, payload, finished: (calls.append(rule['title']), finished(True, ''))
            self.controller.run_before('object.update', dict(search_type='demo/asset'), lambda *args: None)
            self.assertEqual(calls, ['Legacy hook'])
            self.controller.select(0)
            self.controller.update('title', 'Updated')
            self.controller.save()
            self.assertEqual(server.records[1]['title'], 'Updated')
            self.controller.remove()
            self.controller.save()
            self.assertEqual(server.records, [dict(code='OTHER', trigger_type='other')])

    def test_legacy_save_rejects_stale_identity_and_rolls_back_partial_failure(self):
        from thlib.ui.script_triggers_legacy import read_hooks, save_hooks

        server = _Server()
        revision = read_hooks(server)['revision']
        rules = [_rule('', 'tools/one'), _rule('', 'tools/two')]
        with self.assertRaisesRegex(RuntimeError, 'Reload before saving'):
            save_hooks(server, 'demo', rules, 'stale')
        self.assertEqual(server.ticket, 'fixture-ticket')
        invalid = _rule('foreign-code', 'tools/one')
        with self.assertRaisesRegex(ValueError, 'identity'):
            save_hooks(server, 'demo', [invalid], revision)
        insert = server.insert

        def fail_second(*args, **kwargs):
            if server.records:
                raise PermissionError('write denied')
            return insert(*args, **kwargs)

        with patch.object(server, 'insert', side_effect=fail_second):
            with self.assertRaisesRegex(PermissionError, 'write denied'):
                save_hooks(server, 'demo', rules, revision)
        self.assertEqual(server.records, [])
        self.assertEqual(server.ticket, 'fixture-ticket')

    def test_stream_command_failure_does_not_fall_back_to_legacy_writes(self):
        from unittest.mock import Mock
        from xmlrpc.client import Fault

        server = Mock()
        server.class_exists.return_value = True
        server.execute_cmd.side_effect = Fault(403, 'Denied')
        self.controller._project_code = 'demo'
        self.controller._run_server = lambda operation, handler: handler(operation())
        with patch.object(tc, 'server_start', return_value=server):
            with self.assertRaises(Fault):
                self.controller.refresh()
        server.query.assert_not_called()
        server.start.assert_not_called()

    def test_discard_and_reload_invalidate_pending_picker_document(self):
        self.controller._original = [_rule("same", "tools/one")]
        self.controller.discard()
        epoch = self.controller.documentEpoch
        self.controller.discard()
        self.assertNotEqual(self.controller.documentEpoch, epoch)
        epoch = self.controller.documentEpoch
        self.controller._refreshed(("", self.controller._generation, [], "same-revision"))
        self.assertNotEqual(self.controller.documentEpoch, epoch)

    def test_matching_scripts_run_top_to_bottom_for_one_action(self):
        self.controller.rules.replace(self.controller._present([
            _rule("first", "tools/one", order=0),
            _rule("second", "tools/two", order=1),
            _rule("third", "tools/two", order=2),
        ]))
        calls = []
        self.controller._execute_rule = (
            lambda rule, _payload, finished:
            (calls.append(rule["ruleId"]), finished(True, ""))
        )
        completed = []

        self.controller.run_before(
            "object.update",
            {"search_type": "demo/asset"},
            lambda success, error: completed.append((success, error)),
        )

        self.assertEqual(calls, ["first", "second", "third"])
        self.assertEqual(completed, [(True, "")])

    def test_concurrent_before_does_not_bypass_validation_and_after_is_deferred(self):
        self.controller.rules.replace(self.controller._present([
            _rule('check', 'tools/one', action='snapshot.save'),
            _rule('done', 'tools/two', action='snapshot.save', phase='after'),
        ]))
        waiting, called, completed = [], [], []
        def execute(rule, payload, callback):
            called.append(rule['ruleId'])
            waiting.append(callback)
        self.controller._execute_rule = execute
        self.controller.run_before('snapshot.save', dict(search_type='demo/asset'), lambda *args: completed.append(args))
        self.controller.run_before('snapshot.save', dict(search_type='demo/asset'), lambda *args: completed.append(args))
        self.assertFalse(completed[0][0])
        self.controller.run_after('snapshot.save', dict(search_type='demo/asset'))
        self.assertEqual(called, ['check'])
        waiting.pop(0)(True, '')
        self.app.processEvents()
        self.assertEqual(called, ['check', 'done'])
        waiting.pop(0)(True, '')

    def test_session_change_during_validator_rejects_completed_before_result(self):
        self.controller.rules.replace(self.controller._present([_rule('check', 'tools/one')]))
        callbacks, results = [], []
        self.controller._execute_rule = lambda rule, payload, callback: callbacks.append(callback)
        self.controller.run_before('object.update', dict(search_type='demo/asset'), lambda *values: results.append(values))
        self.controller._generation += 1
        callbacks[0](True, '')
        self.assertFalse(results[-1][0])

    def test_before_failure_blocks_remaining_scripts_but_after_continues(self):
        self.controller.rules.replace(self.controller._present([
            _rule("one", "tools/one", phase="before", order=0),
            _rule("two", "tools/two", phase="before", order=1),
        ]))
        calls = []
        self.controller._execute_rule = (
            lambda rule, _payload, finished:
            (calls.append(rule["ruleId"]), finished(False, "boom"))
        )
        completed = []
        self.controller.run_before(
            "object.update", {"search_type": "demo/asset"},
            lambda success, error: completed.append((success, error)),
        )
        self.assertEqual(calls, ["one"])
        self.assertEqual(completed, [(False, "boom")])

        rows = [
            _rule("one", "tools/one", phase="after", order=0),
            _rule("two", "tools/two", phase="after", order=1),
        ]
        self.controller.rules.replace(self.controller._present(rows))
        calls.clear()
        self.controller.run_after(
            "object.update", {"search_type": "demo/asset"}
        )
        self.assertEqual(calls, ["one", "two"])

    def test_dcc_action_accepts_only_dcc_python(self):
        with self.assertRaisesRegex(ValueError, "DCC"):
            self.controller._validate([
                _rule("open", "tools/one", action="dcc.maya.scene.open")
            ])
        self.controller._validate([
            _rule("open", "maya/open", action="dcc.maya.scene.open")
        ])
        with self.assertRaisesRegex(ValueError, "Handler"):
            self.controller._validate([
                _rule("update", "maya/open", action="object.update")
            ])
        self.controller._validate([
            _rule("open", "tools/one", action="snapshot.open"),
            _rule("save", "tools/two", action="snapshot.save"),
        ])
        with self.assertRaisesRegex(ValueError, "Handler"):
            self.controller._validate([
                _rule("open", "maya/open", action="snapshot.open")
            ])

    def test_dcc_rules_can_be_configured_without_a_connected_client(self):
        actions = {
            item["value"]: item for item in self.controller.actionOptions
        }

        self.assertTrue(actions["dcc.maya.scene.open"]["dcc"])
        self.assertTrue(
            actions["dcc.maya.scene.open"]["label"].startswith("Maya DCC")
        )
        self.assertFalse(actions["snapshot.open"]["dcc"])
        self.assertNotIn("checkin", actions)
        self.controller.rules.replace(self.controller._present([
            _rule("open", "maya/open", action="dcc.maya.scene.open")
        ]))
        self.controller.select(0)
        self.assertEqual(
            [item["value"] for item in self.controller.compatibleScriptOptions],
            ["maya/open"],
        )

    def test_server_script_uses_native_saved_script_execution(self):
        calls = []

        class Server:
            def execute_python_script(self, path, kwargs=None):
                calls.append((path, dict(kwargs or {})))
                return "done"

        payload = {"project_code": "demo", "event": "object.update"}
        with patch.object(tc, "server_start", return_value=Server()):
            result = self.controller._execute_server(
                {"path": "tools/one", "language": "python"}, payload
            )

        self.assertEqual(result, "done")
        self.assertEqual(calls[0][0], "tools/one")
        self.assertEqual(calls[0][1]["event"], "object.update")
        self.assertEqual(calls[0][1]["TACTIC_SCRIPT_KWARGS"], payload)

    def test_server_trigger_result_is_written_to_script_console(self):
        rule = _rule("server", "tools/one")
        completed = []

        self.controller._execution_finished(
            rule, time.monotonic(), True,
            {"info": {"spt_ret_val": "server result"}}, "",
            lambda success, error: completed.append((success, error)),
        )

        self.assertIn("server result", self.scripts.trigger_outputs[0][1])
        self.assertEqual(completed, [(True, "")])

    def test_local_trigger_print_is_written_to_script_console(self):
        rule = _rule(
            "save", "tools/one", phase="after", action="snapshot.save"
        )
        result = self.controller._execute_local(
            {
                "path": "tools/one",
                "source": (
                    "import sys\n"
                    "print('YOU ARE SAVED THE DAY BUDDY')\n"
                    "print('STDERR IS HERE', file=sys.stderr)"
                ),
            },
            {"project_code": "demo", "event": "snapshot.save"},
        )
        completed = []

        self.controller._execution_finished(
            rule, time.monotonic(), True, result, "",
            lambda success, error: completed.append((success, error)),
        )

        self.assertEqual(self.application.notifications, [])
        self.assertEqual(self.scripts.trigger_outputs[0][0], "tools/one")
        self.assertIn(
            "YOU ARE SAVED THE DAY BUDDY",
            self.scripts.trigger_outputs[0][1],
        )
        self.assertIn("STDERR IS HERE", self.scripts.trigger_outputs[0][1])
        self.assertEqual(completed, [(True, "")])

    def test_trigger_failure_writes_full_traceback_to_script_console(self):
        rule = _rule("broken", "tools/one")
        completed = []

        self.controller._execution_finished(
            rule, time.monotonic(), False, {},
            "Traceback (most recent call last):\nRuntimeError: broken",
            lambda success, error: completed.append((success, error)),
        )

        self.assertIn("RuntimeError: broken", self.scripts.trigger_outputs[0][1])
        self.assertEqual(completed[0][0], False)

    def test_native_json_data_is_loaded_without_string_round_trip(self):
        rule = _project_rule({
            "code": "TRIGGER1",
            "title": "After edit",
            "script_path": "tools/one",
            "data": {
                "version": 1,
                "action": "object.update",
                "phase": "after",
                "search_type": "demo/asset",
            },
        }, 0)

        self.assertTrue(rule["valid"])
        self.assertEqual(rule["action"], "object.update")

        malformed = _project_rule({
            "code": "TRIGGER2",
            "script_path": "tools/one",
            "data": "[]",
        }, 1)
        self.assertFalse(malformed["valid"])

    def test_rules_are_saved_as_project_trigger_records(self):
        server = _Server()
        self.controller._project_code = "demo"
        self.controller._revision = 'original-server-revision'
        rules = [
            _rule("first", "tools/one", order=0),
            _rule("second", "tools/two", order=1),
        ]
        for rule in rules:
            rule["code"] = ""
        self.controller.rules.replace(self.controller._present(rules))
        self.controller._run_server = (
            lambda operation, handler: handler(operation())
        )

        with patch.object(tc, "server_start", return_value=server):
            self.controller.save()

        self.assertEqual(len(server.records), 2)
        self.assertEqual(
            server.records[0]["trigger_type"], "handler_script_hook"
        )
        self.assertEqual(
            [record["script_path"] for record in server.records],
            ["tools/one", "tools/two"],
        )

    def test_editor_qml_creates_without_warnings(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda values: warnings.extend(value.toString() for value in values)
        )
        context = engine.rootContext()
        context.setContextProperty("scriptTriggerController", self.controller)
        context.setContextProperty("scriptTriggerModel", self.controller.model)
        context.setContextProperty("scriptEditorController", self.scripts)
        context.setContextProperty("scriptEditorModel", self.scripts.model)
        context.setContextProperty("windowModel", self.application.window_model)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True, "popupAnimationsEnabled":False, "clickAnimationsEnabled":False})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "ScriptTriggerEditorView.qml"))
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "width": 900,
            "height": 650,
        })
        window = QQuickWindow()
        try:
            self.assertIsNotNone(
                view, [error.toString() for error in component.errors()]
            )
            view.setParentItem(window.contentItem())
            window.resize(900, 650)
            window.show()
            QTest.qWait(20)
            items = [view]
            for item in items:
                items.extend(item.childItems())
            help_button = next((item for item in items if item.objectName() == "scriptTriggerHelpButton"), None)
            self.assertIsNotNone(help_button, "\n".join(warnings))
            center = help_button.mapToScene(QPointF(
                help_button.width() / 2, help_button.height() / 2
            ))
            QTest.mouseClick(
                window, Qt.LeftButton, pos=center.toPoint()
            )
            self.assertEqual(
                self.application.window_model.help_topics,
                ["script_triggers"],
            )
            def visual(root):
                values = [root]
                for item in values:
                    values.extend(item.childItems())
                return values

            from tests.profile_ui_responsiveness import frame

            def click(item):
                point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
                QTest.mouseClick(item.window(), Qt.LeftButton, pos=point.toPoint())
                frame(window)

            def control(name):
                item = next(item for item in visual(view) if item.objectName() == name)
                loaded = item.property("item")
                return loaded if hasattr(loaded, "childItems") else item

            click(control("scriptTriggerAdd"))
            field = control("scriptTriggerTitle")
            click(field)
            QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
            for char in "Changed trigger": QTest.keyClick(window, char)
            QTest.qWait(10)
            self.assertEqual(self.controller.selectedRule["title"], "Changed trigger")
            self.assertTrue(self.controller.dirty)
            self.controller._project_code = "fixture"
            reloads = []
            self.controller._run_server = lambda *args: reloads.append(True)
            click(control("scriptTriggersReload"))
            confirmation = view.findChild(QObject, "reloadTriggerConfirmation")
            self.assertTrue(confirmation.property("visible"))
            QTest.keyClick(window, Qt.Key_Escape)
            QTest.qWait(10)
            self.assertFalse(confirmation.property("visible"))
            self.assertEqual(reloads, [])
            click(control("scriptTriggersReload"))
            discard = next(item for item in visual(confirmation.property("footer")) if item.property("text") == "Discard" and item.property("pressed") is not None)
            click(discard)
            self.assertEqual(reloads, [True])
            self.assertEqual(warnings, [])
        finally:
            window.close()
            window.deleteLater()
            if view is not None:
                view.deleteLater()
            if theme is not None:
                theme.deleteLater()
            engine.deleteLater()


if __name__ == "__main__":
    unittest.main()
