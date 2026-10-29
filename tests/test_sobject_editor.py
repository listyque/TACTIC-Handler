import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl, Slot
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtTest import QTest

from thlib import tactic_widgets as tw
from thlib.ui.checkin_out import CheckinOutController
from thlib.ui.sobject_editor import SObjectEditorController, SObjectFieldModel
from thlib.ui.controllers.commands import CommandsMixin
from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.workspace_models.windows import FloatingWindowModel


class _Emitter:
    def __init__(self):
        self.callbacks = []
        self.count = 0

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in list(self.callbacks):
            callback(*args)
        self.count += 1


class _WindowModel:
    def __init__(self):
        self.opened = []
        self.raised = []
        self.visible = set()

    def show_window(self, window_id):
        self.opened.append(window_id)
        self.visible.add(window_id)

    def is_window_visible(self, window_id):
        return window_id in self.visible

    def raise_window(self, window_id):
        self.raised.append(window_id)


class _CommandsHarness(CommandsMixin):
    can_manage_tools = True

    def __init__(self):
        self.debug_log = None
        self.window_model = _WindowModel()
        self._sobject_editor_request = {}
        self.sobjectEditorRequested = _Emitter()
        self.searched = []

    def _active_stype(self):
        return "active-stype"

    def _notify(self, _message):
        pass

    def _search_by_key(self, search_key):
        self.searched.append(search_key)

    @staticmethod
    def refresh_current():
        pass


class _Source:
    def __init__(self, stype):
        self.stype = stype

    def get_stype(self):
        return self.stype


class _ItemHarness(ItemOperationsMixin):
    def __init__(self, source):
        self.debug_log = None
        self.node = SimpleNamespace(
            node_id="asset-one",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            source=source,
            parent_id="",
        )
        self.nodes = {self.node.node_id: self.node}
        self._sobject_editor_request = {}
        self.window_model = _WindowModel()
        self.opened = []
        self.notifications = []

    def _node_for_any(self, node_id):
        return self.nodes.get(node_id)

    def _file_object_for_node(self, _node_id):
        return None

    def open_window(self, window_id):
        self.opened.append(window_id)

    def _notify(self, message):
        self.notifications.append(message)


class SObjectEditorLifecycleTests(unittest.TestCase):
    def test_editor_admission_tracks_changes_reverts_and_inflight_work(self):
        from copy import deepcopy
        controller = SObjectEditorController(lambda: {})
        controller.model.replace([dict(fieldName="name", fieldType="string", fieldValue="Original",
            fieldReadOnly=False, fieldRequired=False, fieldError="")])
        controller._baseline = deepcopy(controller.model.values())
        self.assertTrue(controller.can_replace_session())
        controller.model.setValue(0, "Unsaved")
        self.assertFalse(controller.can_replace_session())
        controller.model.setValue(0, "Original")
        self.assertTrue(controller.can_replace_session())
        for flag in ("_busy", "_uncertain", "_batch_enabled"):
            setattr(controller, flag, True)
            self.assertFalse(controller.can_replace_session(), flag)
            setattr(controller, flag, False)

    def test_shared_entry_retargets_only_a_clean_editor(self):
        from thlib.ui.sobject_editor import open_sobject_editor
        app = _CommandsHarness()
        app.window_model.visible.add("add_sobject")
        app.sobject_editor_can_replace = lambda: True
        source = object()
        self.assertTrue(open_sobject_editor(app, dict(mode="edit", sobject=source)))
        self.assertIs(app._sobject_editor_request["sobject"], source)
        self.assertEqual(app.sobjectEditorRequested.count, 1)
        app.sobject_editor_can_replace = lambda: False
        self.assertFalse(open_sobject_editor(app, dict(mode="insert", operation="publish")))
        self.assertIs(app._sobject_editor_request["sobject"], source)
        self.assertEqual(app.sobjectEditorRequested.count, 1)
        self.assertEqual(app.window_model.raised, ["add_sobject", "add_sobject"])

    def test_publish_cell_opens_existing_editor_with_its_exact_view(self):
        source = _Source(object())
        app = _ItemHarness(source)
        app.invoke_table_widget_action("publish", "asset-one", dict(actionView="review_publish"))
        self.assertEqual(app.opened, ["add_sobject"])
        self.assertEqual(app._sobject_editor_request["view"], "review_publish")
        self.assertEqual(app._sobject_editor_request["operation"], "publish")
        self.assertEqual(app._sobject_editor_request["mode"], "edit")
        self.assertIs(app._sobject_editor_request["sobject"], source)

    def test_task_edit_view_receives_project_in_server_arguments(self):
        worker = SimpleNamespace(
            result=_Emitter(), error=_Emitter(), start=lambda: None,
        )
        pool = SimpleNamespace(add_task=Mock(return_value=worker))
        context = {
            "mode": "edit",
            "stype": SimpleNamespace(get_pretty_name=lambda: "Task"),
            "project_code": "demo",
            "search_type": "sthpw/task",
            "sobject": SimpleNamespace(get_search_key=lambda: (
                "sthpw/task?project=demo&code=TASK001"
            )),
        }
        controller = SObjectEditorController(lambda: context)

        with patch("thlib.environment.env_inst.server_pool", pool):
            controller.begin_session()

        self.assertEqual(pool.add_task.call_args.args[2]["project"], "demo")

    def test_lost_save_reply_blocks_resubmission(self):
        controller = SObjectEditorController(lambda: {})
        controller._request_id = 7
        controller._edit_widget = Mock()
        controller._save_failed(7, {"exception": ConnectionError("Lost reply")})
        self.assertTrue(controller.presentation["uncertain"])
        controller.submit()
        controller._edit_widget.commit.assert_not_called()
        from xmlrpc.client import Fault
        controller._save_failed(7, {"exception": Fault(409, "Revision changed")})
        self.assertFalse(controller.presentation["uncertain"])
        self.assertIn("Revision changed", controller.error)

    def test_create_context_reuses_search_key_navigation(self):
        controller = _CommandsHarness()
        project = SimpleNamespace(get_code=lambda: "demo")
        stype = SimpleNamespace(
            get_code=lambda: "demo/asset",
            get_project=lambda: project,
        )
        controller._sobject_editor_request = {"stype": stype}

        context = controller.sobject_editor_context()
        context["open_created"](
            "demo/asset?project=demo&code=ASSET001"
        )

        self.assertEqual(controller.searched, [
            "demo/asset?project=demo&code=ASSET001",
        ])

    def test_prepared_edit_starts_session_before_first_window_show(self):
        controller = _CommandsHarness()
        source = object()
        controller._sobject_editor_request = {
            "mode": "edit",
            "stype": object(),
            "sobject": source,
            "_prepared": True,
        }
        events = []
        controller.sobjectEditorRequested.connect(lambda: events.append((
            "session", controller._sobject_editor_request.get("sobject"),
        )))
        original_show = controller.window_model.show_window

        def show_window(window_id):
            events.append(("window", window_id))
            original_show(window_id)

        controller.window_model.show_window = show_window

        controller.open_window("add_sobject")

        self.assertEqual(events, [
            ("session", source),
            ("window", "add_sobject"),
        ])

    def test_visible_editor_reloads_new_context_and_is_raised(self):
        controller = _CommandsHarness()
        controller.window_model.visible.add("add_sobject")
        source = object()
        controller._sobject_editor_request = {
            "mode": "edit",
            "stype": object(),
            "sobject": source,
            "_prepared": True,
        }
        seen = []
        controller.sobjectEditorRequested.connect(
            lambda: seen.append(
                controller._sobject_editor_request.get("sobject")
            )
        )

        controller.open_window("add_sobject")

        self.assertEqual(seen, [source])
        self.assertEqual(controller.window_model.opened, [])
        self.assertEqual(controller.window_model.raised, ["add_sobject"])

    def test_item_edit_uses_the_shared_prepared_window_route(self):
        stype = object()
        source = _Source(stype)
        controller = _ItemHarness(source)

        controller.invoke_item_action("edit", "asset-one")

        self.assertEqual(controller.opened, ["add_sobject"])
        self.assertIs(controller._sobject_editor_request["sobject"], source)
        self.assertIs(controller._sobject_editor_request["stype"], stype)
        self.assertTrue(controller._sobject_editor_request["_prepared"])

    def test_snapshot_edit_uses_owner_schema_and_snapshot_target(self):
        stype = object()
        owner = _Source(stype)

        class Snapshot:
            @staticmethod
            def get_stype():
                raise AttributeError("snapshot has no project")

        snapshot = Snapshot()
        controller = _ItemHarness(snapshot)
        controller.node.node_type = "snapshot"
        controller.node.parent_id = "asset-root"
        controller.nodes["asset-root"] = SimpleNamespace(
            node_id="asset-root",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            source=owner,
            parent_id="",
        )

        controller.invoke_item_action("edit", "asset-one")

        self.assertEqual(controller.opened, ["add_sobject"])
        self.assertIs(controller._sobject_editor_request["sobject"], snapshot)
        self.assertIs(controller._sobject_editor_request["stype"], stype)
        self.assertEqual(controller.notifications, [])

    def test_editor_visibility_is_not_restored_without_context(self):
        with tempfile.TemporaryDirectory():
            settings = {
                "workspace/floatingWindows": json.dumps([{
                    "window_id": "add_sobject",
                    "title": "Old Edit SObject",
                    "kind": "add_sobject",
                    "x": 0.2,
                    "y": 0.2,
                    "width": 0.5,
                    "height": 0.6,
                    "visible": True,
                    "z": 8,
                    "blocking": False,
                    "geometry_mode": "relative",
                }]),
            }

            model = FloatingWindowModel(settings)

        self.assertFalse(model.is_window_visible("add_sobject"))

    def test_self_related_create_forwards_native_instance_path(self):
        project = SimpleNamespace(get_code=lambda: "demo")
        relation = {
            "from": "demo/asset",
            "to": "demo/asset",
            "relationship": "instance",
            "instance_type": "demo/asset_in_asset",
        }
        schema = SimpleNamespace(
            get_child=lambda *_args: relation,
            get_parent_instance=lambda *_args: {"path": "child_asset"},
        )
        stype = SimpleNamespace(
            get_code=lambda: "demo/asset",
            get_pretty_name=lambda: "Assets",
            get_project=lambda: project,
            get_schema=lambda: schema,
        )
        parent = SimpleNamespace(
            get_stype=lambda: stype,
            get_search_key=lambda: "demo/asset?code=PARENT",
        )
        controller = SObjectEditorController(lambda: {})
        controller._request_id = 1
        controller._mode = "insert"

        controller._schema_loaded(
            1,
            stype,
            {"parent_sobject": parent, "relation": relation},
            {
                "EditWdg": {
                    "kwargs": {
                        "input_prefix": "insert",
                        "search_type": "demo/asset",
                        "parent_key": "demo/asset?code=PARENT",
                    },
                },
                "InputWidgets": [],
            },
        )

        with patch.object(tw.tc, "insert_sobjects", return_value={}) as insert:
            controller._edit_widget.commit({"name": "Child"})

        insert.assert_called_once_with(
            "demo/asset",
            "demo",
            {"name": "Child"},
            parent_key="demo/asset?code=PARENT",
            instance_type="demo/asset_in_asset",
            instance_path="child_asset",
        )


class _EditorStype:
    def __init__(self, data_types=None):
        self.data_types = dict(data_types or {})

    @staticmethod
    def get_code():
        return "demo/asset"

    def get_column_data_type(self, column):
        return self.data_types.get(column, "text")


class _EditorSObject:
    def __init__(self, info=None, stype=None, pipeline_code="main"):
        self.info = dict(info or {})
        self.stype = stype
        self.pipeline_code = pipeline_code

    def get_info(self):
        return dict(self.info)

    def get_value(self, name):
        return self.info.get(name)

    def get_stype(self):
        return self.stype

    def get_pipeline_code(self):
        return self.pipeline_code


class SObjectWidgetContractTests(unittest.TestCase):
    def test_stock_preview_size_keeps_native_image_picker(self):
        source = dict(name="preview", class_name="tactic.ui.widget.upload_wdg.SimpleUploadWdg",
            action_class="pyasm.command.UploadAction", kwargs=dict(icon_size="100%"))
        field = SObjectEditorController.describe_field(_EditorStype(), {}, source)
        self.assertEqual(field["fieldType"], "preview")

    def test_publish_keeps_upload_action_as_file_and_rejects_null_preview(self):
        source = dict(name="attachment", class_name="tactic.ui.widget.upload_wdg.SimpleUploadWdg",
            action_class="pyasm.command.UploadAction", kwargs=dict(context="publish/reference"))
        field = SObjectEditorController.describe_field(_EditorStype(), dict(operation="publish"), source)
        self.assertEqual(field["fieldType"], "file")
        self.assertEqual(field["fieldValue"], "")
        self.assertEqual(field["submitName"], "attachment")
        source["action_class"] = "pyasm.command.NullAction"
        field = SObjectEditorController.describe_field(_EditorStype(), dict(operation="publish"), source)
        self.assertEqual(field["fieldType"], "unsupported")
        controller = SObjectEditorController(lambda: {})
        controller._context_data = dict(operation="publish")
        controller.model.replace([field])
        controller._edit_widget = Mock()
        self.assertFalse(controller.presentation["valid"])
        controller.submit()
        controller._edit_widget.commit.assert_not_called()
        self.assertIn("unsupported", controller.error)

    def test_configured_publish_routes_to_editcmd_and_preserves_field_names(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"payload.txt"
            path.write_bytes(b"Native configured publication")
            stype = SimpleNamespace(get_project=lambda: SimpleNamespace(get_code=lambda: "demo"))
            editor = tw.TacticEditWdg(dict(stype=stype, kwargs=dict(input_prefix="edit", view="review_publish",
                search_type="demo/asset", search_key="demo/asset?code=A"), configured_publish=[
                    dict(name="title_alias", class_name="pyasm.widget.input_wdg.TextWdg", action_options=dict(column="name")),
                    dict(name="attachment", class_name="tactic.ui.widget.upload_wdg.SimpleUploadWdg", context="publish/reference")]))
            server = Mock()
            server.get_transaction_ticket.return_value = "private-test-ticket"
            server.execute_cmd.return_value = dict(info=dict(sobject=dict(__search_key__="demo/asset?code=A")))
            with patch.object(tw.tc, "server_start", return_value=server):
                result = editor.commit(dict(title_alias="Published", attachment=str(path)))
            server.update.assert_not_called()
            server.upload_file.assert_called_once_with(str(path))
            command, args, values = server.execute_cmd.call_args.args
            self.assertEqual(command, "tactic.ui.panel.EditCmd")
            self.assertEqual(args["view"], "review_publish")
            self.assertEqual(args["element_names"], ["title_alias", "attachment"])
            self.assertEqual(values["edit|title_alias"], "Published")
            self.assertEqual(values["edit|attachment|context"], "publish/reference")
            self.assertEqual(values["edit|attachment|path"], "payload.txt")
            self.assertEqual(result["__search_key__"], "demo/asset?code=A")
            server.execute_cmd.return_value = dict(info={})
            with self.assertRaises(ConnectionError):
                editor._commit_publish(dict(title_alias="Published"), server)

    def test_configured_publish_expands_multi_upload_and_submits_named_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            icon_path = Path(directory) / "icon.png"
            main_path = Path(directory) / "asset.ma"
            icon_path.write_bytes(b"icon")
            main_path.write_bytes(b"main")
            controller = SObjectEditorController(lambda: {})
            sources = [
                dict(name="images", class_name="pyasm.widget.input_wdg.ThumbInputWdg", action_class=""),
                dict(
                    name="files",
                    class_name="tactic.ui.widget.upload_wdg.UploadWdg",
                    action_class="pyasm.command.NullAction",
                    kwargs=dict(names="icon|main"),
                    subcontext=True,
                    upload_fields=[dict(name="icon", required=False), dict(name="main", required=True)],
                    context_input=dict(type="select", value="publish", labels=["publish"], values=["publish"]),
                ),
            ]
            descriptors = controller.build_descriptors(_EditorStype(), dict(operation="publish"), sources, mode="edit")
            self.assertEqual([item["fieldName"] for item in descriptors], [
                "images", "files|icon", "files|main", "files|context", "files|subcontext", "files|description", "files|is_revision"
            ])
            self.assertEqual(descriptors[0]["fieldType"], "thumbnail")
            self.assertTrue(descriptors[2]["fieldRequired"])
            stype = SimpleNamespace(get_project=lambda: SimpleNamespace(get_code=lambda: "demo"))
            editor = tw.TacticEditWdg(dict(
                stype=stype,
                kwargs=dict(input_prefix="edit", view="publish", search_type="demo/asset", search_key="demo/asset?code=A"),
                configured_publish=[dict(name="files", class_name="tactic.ui.widget.upload_wdg.UploadWdg", kwargs=dict(names="icon|main"), upload_fields=[dict(name="icon"), dict(name="main")])],
            ))
            server = Mock()
            server.get_transaction_ticket.return_value = "ticket-1"
            server.execute_cmd.return_value = dict(info=dict(sobject=dict(__search_key__="demo/asset?code=A")))
            with patch.object(tw.tc, "server_start", return_value=server):
                editor.commit({
                    "files|icon": str(icon_path),
                    "files|main": str(main_path),
                    "files|context": "publish",
                    "files|subcontext": "hi",
                    "files|description": "Note",
                    "files|is_revision": True,
                })
            self.assertEqual(server.upload_file.call_count, 2)
            _command, _args, values = server.execute_cmd.call_args.args
            self.assertEqual(values["edit|icon|path"], "icon.png")
            self.assertEqual(values["edit|main|path"], "asset.ma")
            self.assertEqual(values["edit|files|context"], "publish")
            self.assertEqual(values["edit|files|subcontext"], "hi")
            self.assertEqual(values["edit|files|is_revision"], True)

    def test_keywords_use_tags_editor_in_insert_and_edit(self):
        for mode in ("insert", "edit"):
            field = SObjectEditorController.describe_field(
                _EditorStype({"keywords": "text"}), {},
                {"name": "tag_alias", "class_name": "pyasm.widget.input_wdg.TextAreaWdg",
                 "action_options": {"column": "keywords"}}, mode=mode,
            )
            self.assertEqual(field["fieldType"], "tags")
            self.assertEqual(field["submitName"], "keywords")

    def test_batch_preview_builds_editable_numbered_drafts(self):
        controller = SObjectEditorController(lambda: {})
        controller._mode = "insert"
        controller.model.replace([
            self._field_descriptor_for_submission(
                "name", "string", "Sh_{n:03}"
            ),
            self._field_descriptor_for_submission(
                "description", "multiline", "DESC FOR SH_{n:03}"
            ),
        ])

        controller.set_batch_enabled(True)
        controller.set_batch_count(3)
        self.assertEqual(controller.batchExample, "Sh_001 … Sh_003")
        controller.preview_batch()

        self.assertTrue(controller.batchPreview)
        self.assertEqual(controller.model.values()["name"], "Sh_001")
        self.assertEqual(
            controller.model.values()["description"], "DESC FOR SH_001"
        )
        controller.model.setValue(1, "special first shot")
        controller.show_batch_item(1)
        self.assertEqual(controller.model.values()["name"], "Sh_002")
        self.assertEqual(
            controller.model.values()["description"], "DESC FOR SH_002"
        )
        controller.show_batch_item(0)
        self.assertEqual(
            controller.model.values()["description"],
            "special first shot",
        )
        values, previews = controller._batch_submission()
        self.assertEqual(
            [item["name"] for item in values],
            ["Sh_001", "Sh_002", "Sh_003"],
        )
        self.assertEqual(values[0]["description"], "special first shot")
        self.assertEqual(values[1]["description"], "DESC FOR SH_002")
        self.assertEqual(previews, [[], [], []])

    def test_batch_name_field_marker_controls_the_generated_names(self):
        controller = SObjectEditorController(lambda: {})
        controller._mode = "insert"
        controller.model.replace([
            self._field_descriptor_for_submission(
                "name", "string", "shot_{n}"
            )
        ])

        controller.set_batch_enabled(True)

        self.assertEqual(controller.batchExample, "shot_1 … shot_10")
        changes = []
        controller.stateChanged.connect(lambda: changes.append(True))
        controller.model.setValue(0, "take_{n:02}")
        self.assertTrue(changes)
        self.assertEqual(controller.batchExample, "take_01 … take_10")

    def test_batch_without_number_markers_remains_available(self):
        controller = SObjectEditorController(lambda: {})
        controller._mode = "insert"
        controller.model.replace([
            self._field_descriptor_for_submission("name", "string", "shot")
        ])

        controller.set_batch_enabled(True)
        controller.set_batch_count(2)
        controller.preview_batch()

        values, _previews = controller._batch_submission()
        self.assertEqual(values, [{"name": "shot"}, {"name": "shot"}])

    def test_batch_submit_sends_all_reviewed_drafts_together(self):
        controller = SObjectEditorController(lambda: {})
        controller._mode = "insert"
        controller._edit_widget = object()
        controller.model.replace([
            self._field_descriptor_for_submission(
                "name", "string", "shot_{n:03}"
            )
        ])
        submitted = []
        controller._submit_values = submitted.append
        controller.set_batch_enabled(True)
        controller.set_batch_count(2)
        controller.preview_batch()

        controller.submit()

        self.assertEqual(submitted, [[
            {"name": "shot_001"}, {"name": "shot_002"},
        ]])

    def test_native_widget_classes_have_coherent_inheritance_and_semantics(self):
        expected = {
            "tactic.ui.widget.upload_wdg.SimpleUploadWdg": (
                tw.TacticSimpleUploadWdg, "preview",
            ),
            "pyasm.widget.input_wdg.TextWdg": (tw.TacticTextWdg, "string"),
            "tactic.ui.input.text_input_wdg.TextInputWdg": (tw.TacticTextInputWdg, "string"),
            "pyasm.widget.input_wdg.TextAreaWdg": (
                tw.TacticTextAreaWdg, "multiline",
            ),
            "pyasm.widget.input_wdg.SelectWdg": (
                tw.TacticSelectWdg, "enum",
            ),
            "pyasm.widget.input_wdg.CheckboxWdg": (
                tw.TacticCheckboxWdg, "bool",
            ),
            "pyasm.prod.web.prod_input_wdg.CurrentCheckboxWdg": (
                tw.TacticCurrentCheckboxWdg, "bool",
            ),
            "tactic.ui.input.task_input_wdg.TaskSObjectInputWdg": (
                tw.TacticTaskSObjectInputWdg, "parent",
            ),
            "tactic.ui.widget.calendar_wdg.CalendarInputWdg": (
                tw.TacticCalendarInputWdg, "datetime",
            ),
            "pyasm.prod.web.prod_input_wdg.ProjectSelectWdg": (
                tw.TacticProjectSelectWdg, "project",
            ),
            "tactic.ui.input.pipeline_input_wdg.PipelineInputWdg": (
                tw.TacticPipelineInputWdg, "pipeline",
            ),
            "tactic.ui.input.process_group_select_wdg.ProcessGroupSelectWdg": (
                tw.TacticProcessGroupSelectWdg, "user",
            ),
            "tactic.ui.input.process_context_wdg.ProcessInputWdg": (
                tw.TacticProcessInputWdg, "process",
            ),
            "tactic.ui.input.process_context_wdg.SubContextInputWdg": (
                tw.TacticSubContextInputWdg, "string",
            ),
            "tactic.ui.widget.misc_input_wdg.TaskStatusSelectWdg": (
                tw.TacticTaskStatusSelectWdg, "status",
            ),
            "pyasm.widget.input_wdg.ThumbInputWdg": (
                tw.TacticThumbInputWdg, "thumbnail",
            ),
            "pyasm.widget.input_wdg.UploadWdg": (
                tw.TacticUploadWdg, "multi_upload",
            ),
            "tactic.ui.widget.upload_wdg.UploadWdg": (
                tw.TacticRichUploadWdg, "multi_upload",
            ),
            "pyasm.widget.input_wdg.PasswordWdg": (
                tw.TacticPasswordWdg, "password",
            ),
        }
        options = {
            "name": "field",
            "values": ["one"],
            "labels": ["One"],
            "kwargs": {},
        }
        for tactic_name, (widget_type, kind) in expected.items():
            with self.subTest(tactic_name=tactic_name):
                self.assertIs(
                    tw.get_widget_class(tactic_name, "input"), widget_type
                )
                widget = widget_type(options)
                self.assertEqual(widget.get_class_name(), tactic_name)
                self.assertEqual(widget.get_editor_kind("text"), kind)

        self.assertEqual(set(expected), set(tw.input_classes["tactic"]))

        self.assertTrue(issubclass(tw.TacticPasswordWdg, tw.TacticTextWdg))
        self.assertTrue(issubclass(tw.TacticProjectSelectWdg, tw.TacticSelectWdg))
        self.assertTrue(issubclass(tw.TacticPipelineInputWdg, tw.TacticSelectWdg))

    def test_select_preserves_server_labels_values_column_and_flags(self):
        widget = tw.TacticSelectWdg({
            "name": "fallback",
            "values": ["ip", "done"],
            "labels": ["In progress", "Complete"],
            "kwargs": {"required": "true"},
            "action_options": {"column": "status"},
        })

        self.assertEqual(widget.get_submit_name(), "status")
        self.assertTrue(widget.get_required())
        self.assertEqual(widget.get_editor_options(), [
            {"label": "In progress", "value": "ip"},
            {"label": "Complete", "value": "done"},
        ])

    def test_vfx_text_input_keeps_native_value_required_and_read_only(self):
        source = dict(name='name', title='Name',
                      class_name='tactic.ui.input.text_input_wdg.TextInputWdg',
                      kwargs={'required': 'true', 'read_only': 'true'},
                      __display_values__=['Original'], action_options={})
        descriptor = SObjectEditorController.describe_field(
            _EditorStype({'name': 'varchar'}), {}, source, mode='insert')
        self.assertEqual(descriptor['fieldType'], 'string')
        self.assertEqual(descriptor['fieldValue'], 'Original')
        self.assertTrue(descriptor['fieldRequired'])
        self.assertTrue(descriptor['fieldReadOnly'])
        descriptor.update(fieldValue='', fieldReadOnly=False)
        self.assertEqual(SObjectFieldModel._error_for(descriptor), 'This field is required')
        source['kwargs'] = {'validation_js': 'custom()'}
        descriptor = SObjectEditorController.describe_field(
            _EditorStype({'name': 'varchar'}), {}, source, mode='insert')
        self.assertEqual(descriptor['fieldType'], 'unsupported')

    def test_select_omits_unlabeled_blank_but_keeps_named_default(self):
        widget = tw.TacticSelectWdg({
            "name": "storyboard",
            "values": ["", "(With Storyboard)", "(No Storyboard)"],
            "labels": ["", "(With Storyboard)", "(No Storyboard)"],
            "kwargs": {},
        })
        self.assertEqual(widget.get_editor_options(), [
            {"label": "(With Storyboard)", "value": "(With Storyboard)"},
            {"label": "(No Storyboard)", "value": "(No Storyboard)"},
        ])

        widget.set_values(["", "saved"])
        widget.set_labels(["-- Default --", ""])
        self.assertEqual(widget.get_editor_options(), [
            {"label": "-- Default --", "value": ""},
            {"label": "saved", "value": "saved"},
        ])

    def test_select_method_query_options_and_persistent_default(self):
        controller = SObjectEditorController(lambda: {})
        descriptor = controller.describe_field(
            _EditorStype({"owner": "varchar"}),
            {},
            {
                "name": "owner",
                "title": "Owner",
                "class_name": "pyasm.widget.input_wdg.SelectWdg",
                "values": ["USER001", "USER002"],
                "labels": ["Alice", "Bob"],
                "__display_values__": ["USER002"],
                "action_options": {},
                "kwargs": {"query": "sthpw/login|get_code()|get_name()"},
            },
            mode="insert",
        )
        self.assertEqual(descriptor["fieldOptions"], [
            {"label": "Alice", "value": "USER001"},
            {"label": "Bob", "value": "USER002"},
        ])
        self.assertEqual(descriptor["fieldValue"], "USER002")

    def test_pipeline_submits_display_code_instead_of_pipeline_label(self):
        controller = SObjectEditorController(lambda: {})
        descriptor = controller.describe_field(
            _EditorStype({"pipeline_code": "varchar"}),
            {},
            {
                "name": "pipeline_code",
                "title": "Pipeline",
                "class_name": (
                    "tactic.ui.input.pipeline_input_wdg.PipelineInputWdg"
                ),
                "values": [
                    "",
                    "niki_friends/assets",
                    "niki_friends/assets_2D",
                ],
                "labels": ["-- Default --", "3D Asset", "2D Asset"],
                "__display_values__": {
                    "value": "3D Asset",
                    "values": ["-- Default --", "3D Asset", "2D Asset"],
                    "labels": ["-- Default --", "3D Asset", "2D Asset"],
                },
                "action_options": {},
                "kwargs": {"default": "3D Asset", "use_code": "false"},
            },
            mode="insert",
        )

        self.assertEqual(descriptor["fieldOptions"], [
            {"label": "-- Default --", "value": ""},
            {"label": "3D Asset", "value": "niki_friends/assets"},
            {"label": "2D Asset", "value": "niki_friends/assets_2D"},
        ])
        self.assertEqual(descriptor["fieldValue"], "niki_friends/assets")
        controller.model.replace([descriptor])
        self.assertEqual(controller.model.submission_values("insert"), {
            "pipeline_code": "niki_friends/assets",
        })

    def test_password_never_exposes_or_resubmits_current_value(self):
        controller = SObjectEditorController(lambda: {})
        controller._mode = "edit"
        descriptor = controller._field_descriptor(
            _EditorStype({"password": "varchar"}),
            {"sobject": _EditorSObject({"password": "secret"})},
            {
                "name": "password",
                "title": "Password",
                "class_name": "pyasm.widget.input_wdg.PasswordWdg",
                "kwargs": {},
            },
        )

        self.assertEqual(descriptor["fieldType"], "password")
        self.assertEqual(descriptor["fieldValue"], "")
        controller.model.replace([descriptor])
        self.assertEqual(controller.model.submission_values("edit"), {})

    def test_unknown_server_widget_is_visible_but_never_submitted(self):
        controller = SObjectEditorController(lambda: {})
        descriptor = controller._field_descriptor(
            _EditorStype(),
            {},
            {
                "name": "custom",
                "title": "Custom field",
                "class_name": "studio.CustomInputWdg",
                "kwargs": {},
            },
        )

        self.assertEqual(descriptor["fieldType"], "unsupported")
        self.assertTrue(descriptor["fieldReadOnly"])
        controller.model.replace([descriptor])
        self.assertEqual(controller.model.submission_values("insert"), {})

    def test_boolean_submission_matches_legacy_integer_contract(self):
        model = SObjectFieldModel()
        model.replace([{
            "fieldName": "is_active",
            "submitName": "active",
            "fieldType": "bool",
            "fieldValue": True,
            "defaultValue": False,
            "fieldRequired": False,
            "fieldReadOnly": False,
            "fieldOptions": [],
            "fieldError": "",
        }])

        self.assertEqual(model.submission_values("edit"), {"active": 1})

    def test_process_options_preserve_server_names_and_colors(self):
        pipeline = SimpleNamespace(pipeline={
            "asset_build": {"color": "#123456"},
            "review": {"color": "#654321"},
        })
        asset_stype = SimpleNamespace(
            get_pipeline=lambda: {"main": pipeline},
        )
        target = _EditorSObject(stype=asset_stype)

        options = SObjectEditorController._process_options({
            "parent_sobject": target,
        })

        self.assertEqual(options[0], {
            "label": "asset_build",
            "value": "asset_build",
            "color": "#123456",
            "icon": "process",
        })

    def test_task_status_options_follow_parent_process_workflow(self):
        process_pipeline = SimpleNamespace(
            pipeline={"animation": {"color": "#123456"}},
            get_process_info=lambda process: {
                "task_pipeline": "animation_tasks",
                "type": "manual",
            },
            get_pipeline_process=lambda process: {},
        )
        task_pipeline = SimpleNamespace(pipeline={
            "In progress": {"color": "#446688"},
            "Ready": {"color": "#66aa88"},
        })
        workflow = SimpleNamespace(
            get_by_pipeline_code=lambda search_type, code: (
                task_pipeline if code == "animation_tasks" else None
            ),
            get_by_process_node_type=lambda search_type, node_type: None,
        )
        asset_stype = SimpleNamespace(
            get_pipeline=lambda: {"main": process_pipeline},
            get_workflow=lambda: workflow,
        )
        target = _EditorSObject(stype=asset_stype)

        options = SObjectEditorController._status_options(
            {
                "parent_sobject": target,
                "info_dict": {"process": "animation"},
            },
            {},
        )

        self.assertEqual(options, [
            {
                "label": "In progress",
                "value": "In progress",
                "color": "#446688",
                "icon": "status",
            },
            {
                "label": "Ready",
                "value": "Ready",
                "color": "#66aa88",
                "icon": "status",
            },
        ])

    def test_preview_uses_shared_checkin_after_object_commit(self):
        calls = []
        checkin = SimpleNamespace(
            prepare_external_checkin=lambda **kwargs: calls.append(kwargs)
        )
        controller = SObjectEditorController(lambda: {}, checkin=checkin)
        source = SimpleNamespace(
            get_title=lambda: "Hero",
            get_code=lambda: "ASSET001",
        )
        controller._title = "Asset"
        controller._context_data = {
            "sobject": source,
            "project_code": "demo",
        }
        controller.model.replace([
            self._field_descriptor_for_submission(
                "preview", "preview", "D:/images/hero.png"
            )
        ])

        error = controller._queue_preview(
            {"__search_key__": "demo/asset?code=ASSET001"},
            "demo/asset?code=ASSET001",
        )

        self.assertEqual(error, "")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["context"], "icon")
        self.assertEqual(calls[0]["paths"], ["D:/images/hero.png"])
        self.assertTrue(calls[0]["update_versionless"])
        self.assertFalse(calls[0]["queue_when_ready"])
        self.assertTrue(calls[0]["start_when_ready"])
        self.assertFalse(calls[0]["queue_before_naming"])

    def test_batch_previews_upload_silently_in_sequence(self):
        calls = []
        refreshed = []
        project = SimpleNamespace(get_code=lambda: "demo")
        stype = SimpleNamespace(get_project=lambda: project)
        checkin = SimpleNamespace(
            operationFinished=_Emitter(),
            operationBusy=False,
            namingBusy=False,
            prepare_external_checkin=lambda **kwargs: calls.append(kwargs)
        )
        controller = SObjectEditorController(lambda: {}, checkin=checkin)
        controller._request_id = 7
        controller._mode = "insert"
        controller._title = "Shot"
        controller._context_data = {
            "stype": stype,
            "project_code": "demo",
            "parent_sobject": object(),
            "refresh": lambda: refreshed.append(True),
        }
        controller._submitted_values = [
            {"name": "shot_001"}, {"name": "shot_002"},
        ]
        controller._submitted_previews = [
            ["D:/images/one.png"], ["D:/images/two.png"],
        ]

        controller._save_finished(7, [
            {
                "__search_key__": "demo/shot?code=SHOT001",
                "code": "SHOT001",
                "name": "shot_001",
            },
            {
                "__search_key__": "demo/shot?code=SHOT002",
                "code": "SHOT002",
                "name": "shot_002",
            },
        ])

        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0]["queue_before_naming"])
        self.assertFalse(calls[0]["queue_when_ready"])
        self.assertTrue(calls[0]["start_when_ready"])
        checkin.operationFinished.emit(True, "")
        self.assertEqual(len(calls), 2)
        self.assertFalse(calls[1]["queue_before_naming"])
        self.assertFalse(calls[1]["queue_when_ready"])
        self.assertTrue(calls[1]["start_when_ready"])
        self.assertEqual(refreshed, [True])

    def test_preview_field_keeps_multiple_unique_local_images(self):
        model = SObjectFieldModel()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first image.png"
            second = Path(directory) / "second.jpg"
            invalid = Path(directory) / "notes.txt"
            for path in (first, second, invalid):
                path.touch()
            model.replace([self._field_descriptor_for_submission(
                "preview", "preview", ""
            )])

            count = model.add_preview_files(0, [
                QUrl.fromLocalFile(str(first)),
                QUrl.fromLocalFile(str(second)),
                QUrl.fromLocalFile(str(first)),
                QUrl.fromLocalFile(str(invalid)),
            ])

            self.assertEqual(count, 2)
            self.assertEqual(
                model.preview_paths(),
                [first.as_posix(), second.as_posix()],
            )
            self.assertEqual(model.preview_name(str(first)), first.name)
            self.assertTrue(
                model.preview_url(str(first)).toString().startswith("file:")
            )
            model.remove_preview_file(0, 0)
            self.assertEqual(model.preview_paths(), [second.as_posix()])

    def test_retired_record_rejected_and_check_saved_recovers_uncertain_state(self):
        controller = SObjectEditorController(lambda: {})
        controller._request_id = 3
        controller._mode = "edit"
        retired = _EditorSObject({"name": "Old", "s_status": "retired"})
        controller._schema_loaded(
            3,
            _EditorStype(),
            {"sobject": retired},
            {"EditWdg": {"kwargs": {"search_type": "demo/asset"}}, "InputWidgets": []},
        )
        self.assertIn("Retired records cannot be edited", controller.error)
        self.assertEqual(controller.model.count, 0)

        active = _EditorSObject({"name": "Original"})
        controller._context_data = {"sobject": active, "search_key": "demo/asset?code=A"}
        controller._submitted_values = {"name": "Saved"}
        controller._uncertain = True
        controller._check_saved_finished(3, {"name": "Original"})
        self.assertFalse(controller.presentation["uncertain"])
        self.assertIn("Changes were not saved", controller.error)

        controller._uncertain = True
        controller._check_saved_finished(3, {"name": "Conflict"})
        self.assertTrue(controller.presentation["uncertain"])
        self.assertIn("Record changed on the server", controller.error)

        saved = []
        controller.saved.connect(saved.append)
        controller._uncertain = True
        controller._check_saved_finished(3, {"__search_key__": "demo/asset?code=A", "name": "Saved"})
        self.assertFalse(controller.presentation["uncertain"])
        self.assertEqual(saved, ["demo/asset?code=A"])

        model = SObjectFieldModel()
        model.replace([self._field_descriptor_for_submission("preview", "preview", "")])
        model.clear_preview_files(0)
        self.assertEqual(model.preview_paths(), [])

    def test_failed_auto_start_naming_finishes_the_quiet_operation(self):
        finished = []
        checkin = SimpleNamespace(
            _naming_request=4,
            _naming_busy=True,
            _queue_after_naming=False,
            _start_after_naming=True,
            _naming_error="",
            _application=SimpleNamespace(debug_log=None),
            preparationChanged=_Emitter(),
            operationFinished=_Emitter(),
        )
        checkin.operationFinished.connect(
            lambda success, error: finished.append((success, error))
        )

        CheckinOutController._naming_failed(
            checkin, 4, ValueError("No preview destination")
        )

        self.assertEqual(finished, [(False, "No preview destination")])

    def test_created_object_opens_through_existing_search_key_route(self):
        opened = []
        refreshed = []
        controller = SObjectEditorController(lambda: {})
        controller._request_id = 7
        controller._mode = "insert"
        controller._context_data = {
            "open_created": opened.append,
            "refresh": lambda: refreshed.append(True),
        }

        controller._save_finished(7, {
            "__search_key__": (
                "demo/asset?project=demo&code=ASSET001"
            ),
        })

        self.assertEqual(opened, [
            "demo/asset?project=demo&code=ASSET001",
        ])
        self.assertEqual(refreshed, [])

    def test_created_related_object_refreshes_parent_without_opening_tab(self):
        opened = []
        refreshed = []
        controller = SObjectEditorController(lambda: {})
        controller._request_id = 7
        controller._mode = "insert"
        controller._context_data = {
            "parent_sobject": object(),
            "open_created": opened.append,
            "refresh": lambda: refreshed.append(True),
        }

        controller._save_finished(7, {
            "__search_key__": "demo/shot?project=demo&code=SHOT001",
        })

        self.assertEqual(opened, [])
        self.assertEqual(refreshed, [True])

    def test_sobject_preview_starts_when_naming_is_ready(self):
        started = []
        queued = []
        files = SimpleNamespace(
            _records=[{"path": "D:/images/hero.png"}],
            replace=lambda records: setattr(files, "_records", records),
        )
        checkin = SimpleNamespace(
            _naming_request=3,
            _prepared_virtual_snapshot=None,
            _naming_busy=True,
            _naming_error="",
            _start_after_naming=True,
            _queue_after_naming=False,
            files=files,
            preparationChanged=_Emitter(),
            payloadReady=True,
            start_checkin=lambda: started.append(True),
            queue_current_operation=lambda: queued.append(True),
        )

        CheckinOutController._naming_ready(checkin, 3, {
            "versioned": {
                "paths": ["assets/ASSET001/icon/v001"],
                "names": [["hero", ".png"]],
            },
            "versionless": {
                "paths": ["assets/ASSET001/icon"],
                "names": [["hero", ".png"]],
            },
        })

        self.assertEqual(started, [True])
        self.assertEqual(queued, [])
        self.assertFalse(checkin._start_after_naming)

    @staticmethod
    def _field_descriptor_for_submission(name, field_type, value):
        return {
            "fieldName": name,
            "submitName": name,
            "fieldType": field_type,
            "fieldValue": value,
            "defaultValue": "",
            "fieldRequired": False,
            "fieldReadOnly": False,
            "fieldOptions": [],
            "fieldError": "",
        }


class _EditorWindowModel(QObject):
    @Slot(str)
    def close_window(self, _window_id):
        pass


class SObjectEditorQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    @staticmethod
    def _field(name, field_type, value=""):
        return {
            "fieldName": name,
            "submitName": name,
            "title": name.replace("_", " ").title(),
            "fieldType": field_type,
            "originalType": "text",
            "fieldValue": value,
            "defaultValue": value,
            "fieldRequired": name == "name",
            "fieldReadOnly": field_type in {"parent", "thumbnail"},
            "fieldOptions": (
                [{"label": "Ready", "value": "Ready", "color": "#557799"}]
                if field_type == "status" else []
            ),
            "fieldError": "",
            "fieldDescription": "",
            "fieldIcon": SObjectEditorController._field_icons[field_type],
            "widgetClass": "test.Widget",
        }

    @classmethod
    def _visual_child(cls, item, object_name):
        for child in item.childItems():
            if child.objectName() == object_name:
                return child
            nested = cls._visual_child(child, object_name)
            if nested is not None:
                return nested
        return None

    def test_storyboard_choice_popup_contains_only_named_server_options(self):
        descriptor = SObjectEditorController.describe_field(
            _EditorStype({"storyboard": "text"}),
            {},
            {
                "name": "storyboard",
                "title": "Storyboard",
                "class_name": "pyasm.widget.input_wdg.SelectWdg",
                "values": ["", "(With Storyboard)", "(No Storyboard)"],
                "labels": ["", "(With Storyboard)", "(No Storyboard)"],
                "__display_values__": {"value": "(No Storyboard)"},
                "kwargs": {},
            },
            mode="insert",
        )
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        theme = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        ).createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "SObjectValueEditor.qml"))
        )
        editor = component.createWithInitialProperties({
            "theme": theme,
            "fieldType": descriptor["fieldType"],
            "fieldValue": descriptor["fieldValue"],
            "fieldOptions": descriptor["fieldOptions"],
            "width": 320,
            "height": 48,
        })
        self.assertIsNotNone(
            editor, "\n".join(error.toString() for error in component.errors())
        )
        window = QQuickWindow()
        window.resize(320, 48)
        editor.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(40)
        try:
            combo = editor.findChild(QObject, "sobjectValueChoiceEditor")
            self.assertIsNotNone(combo)
            self.assertEqual(combo.property("count"), 2)
            self.assertEqual(combo.property("currentValue"), "(No Storyboard)")

            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier, QPoint(160, 24)
            )
            QTest.qWait(80)
            options = combo.findChild(QQuickItem, "comboBoxPopupList")
            self.assertIsNotNone(options)
            self.assertEqual(options.property("count"), 2)
            QTest.keyClick(options.window(), Qt.Key_Escape)
            QTest.qWait(20)

            editor.setProperty("width", 640)
            window.resize(640, 48)
            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier, QPoint(320, 24)
            )
            QTest.qWait(80)
            self.assertEqual(options.property("count"), 2)
        finally:
            window.close()
            editor.setParentItem(None)
            editor.deleteLater()
            window.deleteLater()
            from PySide6.QtCore import QCoreApplication, QEvent
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_real_form_reflows_without_moving_footer_or_clipping_fields(self):
        engine = QQmlEngine()
        qml_warnings = []
        engine.warnings.connect(
            lambda warnings: qml_warnings.extend(
                warning.toString() for warning in warnings
            )
        )
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        controller = SObjectEditorController(lambda: {})
        controller._title = "Asset"
        controller._search_type = "demo/asset"
        controller._parent_title = "Episode 01"
        pipeline = self._field(
            "pipeline_code", "pipeline", "demo/assets"
        )
        pipeline["fieldOptions"] = [
            {"label": "-- Default --", "value": ""},
            {"label": "3D Asset", "value": "demo/assets"},
            {"label": "2D Asset", "value": "demo/assets_2d"},
        ]
        controller.model.replace([
            self._field("name", "string", "Hero"),
            self._field(
                "description",
                "multiline",
                "\n".join(f"Description line {index}" for index in range(20)),
            ),
            self._field("status", "status", "Ready"),
            self._field("due", "datetime", "2026-08-23 10:30:00"),
            pipeline,
        ])
        engine.rootContext().setContextProperty(
            "sobjectEditorController", controller
        )
        engine.rootContext().setContextProperty(
            "sobjectFieldModel", controller.model
        )
        engine.rootContext().setContextProperty(
            "windowModel", _EditorWindowModel(engine)
        )
        engine.rootContext().setContextProperty("userListModel", [])
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "SObjectFieldEditor.qml")),
        )
        editor = component.createWithInitialProperties({
            "theme": theme,
            "editorWindowId": "add_sobject",
            "width": 1100,
            "height": 680,
        })
        self.assertIsNotNone(
            editor,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(1100, 680)
        editor.setParentItem(window.contentItem())
        window.show()
        self.app.processEvents()

        footer = self._visual_child(editor, "sobjectEditorFooter")
        repeater = self._visual_child(editor, "sobjectEditorFieldRepeater")
        qml_context = QQmlEngine.contextForObject(repeater)
        name_frame, name_undefined = QQmlExpression(
            qml_context, repeater, "itemAt(0).children[0]"
        ).evaluate()
        description_frame, description_undefined = QQmlExpression(
            qml_context, repeater, "itemAt(1).children[0]"
        ).evaluate()
        name_item, name_item_undefined = QQmlExpression(
            qml_context, repeater, "itemAt(0)"
        ).evaluate()
        description_item, description_item_undefined = QQmlExpression(
            qml_context, repeater, "itemAt(1)"
        ).evaluate()
        status_item, status_item_undefined = QQmlExpression(
            qml_context, repeater, "itemAt(2)"
        ).evaluate()
        due_item, due_item_undefined = QQmlExpression(
            qml_context, repeater, "itemAt(3)"
        ).evaluate()
        pipeline_item, pipeline_item_undefined = QQmlExpression(
            qml_context, repeater, "itemAt(4)"
        ).evaluate()
        self.assertFalse(name_undefined)
        self.assertFalse(description_undefined)
        self.assertFalse(name_item_undefined)
        self.assertFalse(description_item_undefined)
        self.assertFalse(status_item_undefined)
        self.assertFalse(due_item_undefined)
        self.assertFalse(pipeline_item_undefined)
        self.assertIsNotNone(footer)
        create_mode = self._visual_child(editor, "sobjectCreateMode_batch")
        refresh_button = self._visual_child(editor, "sobjectEditorRefresh")
        self.assertIsNotNone(create_mode)
        self.assertIsNotNone(refresh_button)
        self.assertGreaterEqual(create_mode.property("width"), 110)
        create_mode_center = create_mode.mapToItem(
            editor, QPointF(0, create_mode.property("height") / 2)
        ).y()
        refresh_center = refresh_button.mapToItem(
            editor, QPointF(0, refresh_button.property("height") / 2)
        ).y()
        self.assertAlmostEqual(create_mode_center, refresh_center)
        object_names = [
            child.objectName() for child in editor.findChildren(QObject)
            if child.objectName()
        ]
        count_label = self._visual_child(editor, "sobjectEditorFieldCount")
        self.assertIsNotNone(
            name_frame,
            (
                object_names,
                count_label.property("text") if count_label else None,
                qml_warnings,
            ),
        )
        self.assertIsNotNone(description_frame)
        self.assertGreater(
            description_item.property("x"), name_item.property("x")
        )
        self.assertAlmostEqual(
            description_item.property("y"), name_item.property("y")
        )
        self.assertAlmostEqual(
            status_item.property("x"), name_item.property("x")
        )
        self.assertAlmostEqual(
            status_item.property("y"),
            name_item.property("y") + name_item.property("height") + 10,
        )
        self.assertAlmostEqual(
            due_item.property("x"), description_item.property("x")
        )
        self.assertAlmostEqual(
            due_item.property("y"),
            description_item.property("y")
            + description_item.property("height") + 10,
        )
        self.assertLess(
            name_item.property("width"), editor.property("width") * 0.6
        )
        description_scroll_bar = self._visual_child(
            description_frame,
            "sobjectMultilineVerticalScrollBar_description",
        )
        self.assertIsNotNone(description_scroll_bar)
        self.assertTrue(description_scroll_bar.property("hasOverflow"))
        self.assertTrue(description_scroll_bar.property("visible"))
        pipeline_combo = self._visual_child(
            pipeline_item, "sobjectValueChoiceEditor"
        )
        self.assertIsNotNone(pipeline_combo)
        self.assertEqual(pipeline_combo.property("count"), 3)
        self.assertEqual(
            pipeline_combo.property("currentValue"), "demo/assets"
        )
        self.assertTrue(name_frame.property("compact"))
        self.assertGreater(description_frame.property("height"), 100)
        editor_host = self._visual_child(
            name_frame, "sobjectFieldEditorHost_name"
        )
        self.assertIsNotNone(editor_host)
        editor_right = editor_host.mapToItem(
            name_frame, QPointF(editor_host.width(), 0)
        ).x()
        self.assertLessEqual(editor_right, name_frame.width() - 13)
        self.assertAlmostEqual(
            footer.property("height"),
            theme.property("dockWorkspaceFooterHeight"),
        )

        editor.setProperty("width", 520)
        window.resize(520, 680)
        self.app.processEvents()
        resized_name_item, resized_name_undefined = QQmlExpression(
            qml_context, repeater, "itemAt(0)"
        ).evaluate()
        self.assertFalse(resized_name_undefined)
        self.assertIs(resized_name_item, name_item)
        self.assertTrue(name_frame.property("compact"))
        self.assertAlmostEqual(
            description_item.property("x"), name_item.property("x")
        )
        self.assertGreater(
            description_item.property("y"), name_item.property("y")
        )
        self.assertLessEqual(
            name_frame.property("width"), editor.property("width") - 40
        )
        self.assertAlmostEqual(
            footer.property("height"),
            theme.property("dockWorkspaceFooterHeight"),
        )
        form_scroll = self._visual_child(editor, "sobjectEditorFormScroll")
        form_scroll_bar = self._visual_child(editor, "sobjectEditorFormVerticalScrollBar")
        self.assertIsNotNone(form_scroll)
        self.assertIsNotNone(form_scroll_bar)
        editor.setProperty("height", 300)
        window.resize(520, 300)
        self.app.processEvents()
        self.assertTrue(
            form_scroll_bar.property("hasOverflow"),
            {
                "scrollHeight": form_scroll.property("height"),
                "scrollContentHeight": form_scroll.property("contentHeight"),
                "barViewport": form_scroll_bar.property("viewportExtent"),
                "barContent": form_scroll_bar.property("contentExtent"),
                "barParent": str(form_scroll_bar.parent()),
                "barTarget": str(form_scroll_bar.property("flickableTarget")),
            },
        )
        self.assertTrue(form_scroll_bar.property("visible"))
        self.assertGreater(
            form_scroll.property("contentHeight"),
            form_scroll.property("height"),
        )
        controller.set_batch_enabled(True)
        batch_count = self._visual_child(editor, "sobjectBatchCount")
        self.assertIsNotNone(batch_count)
        batch_count = batch_count.property("item")
        count_expression = QQmlExpression(
            QQmlEngine.contextForObject(batch_count),
            batch_count,
            "up.indicator.clicked()",
        )
        count_expression.evaluate()
        self.assertFalse(count_expression.hasError(), count_expression.error())
        self.app.processEvents()
        self.assertEqual(controller.batchCount, 11)
        controller.set_batch_count(3)
        self.app.processEvents()
        batch_setup = self._visual_child(editor, "sobjectBatchSetup")
        self.assertIsNotNone(batch_setup)
        self.assertTrue(batch_setup.property("visible"))
        current_name_item, undefined = QQmlExpression(
            qml_context, repeater, "itemAt(0)"
        ).evaluate()
        self.assertFalse(undefined)
        name_editor = self._visual_child(
            current_name_item, "sobjectValueTextEditor"
        )
        self.assertIsNotNone(name_editor)
        name_editor.forceActiveFocus()
        name_editor.setProperty("cursorPosition", 2)
        padded_button = self._visual_child(editor, "sobjectBatchToken_2")
        self.assertIsNotNone(self._visual_child(editor, "sobjectBatchToken_1"))
        four_digit_button = self._visual_child(editor, "sobjectBatchToken_3")
        self.assertIsNotNone(four_digit_button)
        four_digit_right = four_digit_button.mapToItem(
            batch_setup, QPointF(four_digit_button.width(), 0)
        ).x()
        self.assertLessEqual(
            four_digit_right,
            batch_setup.property("width") - 13,
            {
                "batchWidth": batch_setup.property("width"),
                "buttonX": four_digit_button.property("x"),
                "buttonWidth": four_digit_button.property("width"),
                "buttonParent": str(four_digit_button.parent()),
            },
        )
        padded_expression = QQmlExpression(
            QQmlEngine.contextForObject(padded_button),
            padded_button,
            "clicked()",
        )
        padded_expression.evaluate()
        self.assertFalse(
            padded_expression.hasError(), padded_expression.error()
        )
        self.app.processEvents()
        self.assertEqual(controller.model.values()["name"], "He{n:03}ro")
        current_description_item, undefined = QQmlExpression(
            qml_context, repeater, "itemAt(1)"
        ).evaluate()
        self.assertFalse(undefined)
        description_editor = self._visual_child(
            current_description_item, "sobjectValueMultilineTextEditor"
        )
        self.assertIsNotNone(description_editor)
        description_editor.forceActiveFocus()
        description_editor.setProperty("cursorPosition", 0)
        number_button = self._visual_child(editor, "sobjectBatchToken_0")
        number_expression = QQmlExpression(
            QQmlEngine.contextForObject(number_button),
            number_button,
            "clicked()",
        )
        number_expression.evaluate()
        self.assertFalse(number_expression.hasError(), number_expression.error())
        self.app.processEvents()
        self.assertTrue(
            controller.model.values()["description"].startswith("{n}")
        )
        controller.preview_batch()
        self.app.processEvents()
        batch_navigator = self._visual_child(editor, "sobjectBatchNavigator")
        self.assertIsNotNone(batch_navigator)
        self.assertTrue(batch_navigator.property("visible"))
        self.assertIsNone(self._visual_child(editor,"sobjectBatchSetup"))
        current_description_item, undefined = QQmlExpression(
            qml_context, repeater, "itemAt(1)"
        ).evaluate()
        self.assertFalse(undefined)
        multiline_editor = self._visual_child(
            current_description_item, "sobjectValueMultilineTextEditor"
        )
        self.assertIsNotNone(multiline_editor)
        multiline_editor.forceActiveFocus()
        multiline_editor.setProperty("text", "manual description")
        self.app.processEvents()
        next_button = self._visual_child(editor, "sobjectBatchNext")
        next_expression = QQmlExpression(
            QQmlEngine.contextForObject(next_button),
            next_button,
            "clicked()",
        )
        next_expression.evaluate()
        self.assertFalse(next_expression.hasError(), next_expression.error())
        self.app.processEvents()
        previous_button = self._visual_child(editor, "sobjectBatchPrevious")
        previous_expression = QQmlExpression(
            QQmlEngine.contextForObject(previous_button),
            previous_button,
            "clicked()",
        )
        previous_expression.evaluate()
        self.assertFalse(
            previous_expression.hasError(), previous_expression.error()
        )
        self.app.processEvents()
        restored_description_item, undefined = QQmlExpression(
            qml_context, repeater, "itemAt(1)"
        ).evaluate()
        self.assertFalse(undefined)
        restored_editor = self._visual_child(
            restored_description_item, "sobjectValueMultilineTextEditor"
        )
        self.assertIsNotNone(restored_editor)
        self.assertEqual(restored_editor.property("text"), "manual description")
        submitted_values, _submitted_previews = controller._batch_submission()
        self.assertEqual(
            [item["name"] for item in submitted_values],
            ["He001ro", "He002ro", "He003ro"],
        )
        self.assertEqual(
            submitted_values[0]["description"], "manual description"
        )
        self.assertTrue(
            submitted_values[1]["description"].startswith("2Description")
        )
        unexpected_warnings = [
            warning for warning in qml_warnings
            if "current style does not support customization" not in warning
        ]
        self.assertEqual(unexpected_warnings, [])
        editor.deleteLater()
        theme.deleteLater()
        window.close()
        editor.setParentItem(None)
        window.deleteLater()
        from PySide6.QtCore import QCoreApplication, QEvent
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_preview_field_shows_every_local_image_with_shared_scrollbar(self):
        engine = QQmlEngine()
        qml_warnings = []
        engine.warnings.connect(
            lambda warnings: qml_warnings.extend(
                warning.toString() for warning in warnings
            )
        )
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        field_model = SObjectFieldModel()
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index in range(6):
                path = Path(directory) / f"preview {index}.png"
                image = QImage(4, 4, QImage.Format.Format_ARGB32)
                image.fill(0xff336699)
                self.assertTrue(image.save(str(path)))
                paths.append(str(path))
            theme_component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
            )
            theme = theme_component.createWithInitialProperties({"dark": True})
            component = QQmlComponent(
                engine,
                QUrl.fromLocalFile(str(qml_dir / "SObjectValueEditor.qml")),
            )
            editor = component.createWithInitialProperties({
                "theme": theme,
                "fieldType": "preview",
                "fieldValue": paths,
                "fieldOptions": [],
                "fieldModel": field_model,
                "width": 460,
                "height": 194,
            })
            self.assertIsNotNone(
                editor,
                "\n".join(error.toString() for error in component.errors()),
            )
            window = QQuickWindow()
            window.resize(460, 194)
            editor.setParentItem(window.contentItem())
            window.show()
            self.app.processEvents()

            count = editor.findChild(QObject, "sobjectPreviewCount")
            repeater = editor.findChild(QObject, "sobjectPreviewRepeater")
            tile, tile_undefined = QQmlExpression(
                QQmlEngine.contextForObject(repeater), repeater, "itemAt(0)"
            ).evaluate()
            self.assertFalse(tile_undefined)
            thumbnail = self._visual_child(
                tile, "sobjectPreviewThumbnail_0"
            )
            drop_area = editor.findChild(QObject, "sobjectPreviewDropArea")
            scroll_bar = editor.findChild(
                QObject, "sobjectPreviewHorizontalScrollBar"
            )
            self.assertEqual(count.property("text"), "Preview images: 6")
            self.assertEqual(repeater.property("count"), 6)
            self.assertIsNotNone(thumbnail, qml_warnings)
            self.assertTrue(
                thumbnail.property("source").toString().startswith("file:")
            )
            self.assertTrue(drop_area.property("enabled"))
            self.assertTrue(scroll_bar.property("hasOverflow"))
            self.assertTrue(scroll_bar.property("visible"))
            unexpected_warnings = [
                warning for warning in qml_warnings
                if "current style does not support customization" not in warning
            ]
            self.assertEqual(unexpected_warnings, [])
            editor.deleteLater()
            theme.deleteLater()
            window.close()
            editor.setParentItem(None)
            window.deleteLater()
            from PySide6.QtCore import QCoreApplication, QEvent
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


if __name__ == "__main__":
    unittest.main()
