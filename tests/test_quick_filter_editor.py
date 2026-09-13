import json
from copy import deepcopy
import unittest
import traceback
from unittest.mock import patch
from xmlrpc.client import Fault
from xml.etree import ElementTree

from thlib.ui.quick_filter_editor import QuickFilterEditorController


class _Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in self.callbacks:
            callback(*args)


class _Application:
    def __init__(self):
        self.section_state_changed = _Signal()
        self.project_changed = _Signal()
        self.quick_filters_changed = _Signal()
        self.window_model = type("Windows", (), {"windowVisibilityChanged": _Signal()})()
        self.context = {
            "tab_id": "assets:search",
            "project_code": "demo",
            "search_type": "demo/asset",
            "scope_key": "demo/asset@assets",
            "title": "Assets",
            "groups": [{
                "key": "column:category",
                "title": "Category",
                "enabled": True,
                "options": [
                    {"key": "props", "title": "Props", "enabled": True},
                    {
                        "key": "characters",
                        "title": "Characters",
                        "enabled": True,
                    },
                ],
            }],
            "selections": {"column:category": ["props"]},
        }
        self.applied = []
        self.notifications = []
        self.context_requests = []
        self.catalog_groups = deepcopy(self.context["groups"])
        self.local_saves = []

    def quick_filter_editor_context(self, include_groups=True, shared=True):
        self.context_requests.append(bool(include_groups))
        if include_groups:
            context = deepcopy(self.context)
            if not shared:
                context["groups"] = [group for group in context["groups"] if group["enabled"]]
                for group in context["groups"]:
                    group["options"] = [option for option in group["options"] if option["enabled"]]
            from thlib.ui.quick_filters import QuickFilterCatalog
            if self.context.get("layout"):
                context["groups"] = QuickFilterCatalog.configured_groups(
                    context["groups"], {"groups": self.context.get("layout", [])},
                    include_hidden=True,
                )
            return context
        return {
            key: value for key, value in self.context.items()
            if key != "groups"
        }

    def request_quick_filter_data(self, force=False):
        pass

    def save_quick_filter_layout(self, tab_id, configuration):
        self.local_saves.append((tab_id, configuration))
        self.context["layout"] = configuration["groups"]
        self.context["selections"] = configuration["defaultSelections"]

    def apply_quick_filter_configuration(self, search_type, configuration):
        self.applied.append((search_type, configuration))
        settings = {group["key"]: group for group in configuration.get("groups", [])}
        self.context["groups"] = deepcopy(self.catalog_groups)
        for group in self.context["groups"]:
            setting = settings.get(group["key"], {})
            group["enabled"] = setting.get("enabled", True)
            for option in group["options"]:
                option["enabled"] = ("options" not in setting
                                     or option["key"] in setting["options"])

    def _notify(self, message):
        self.notifications.append(message)

    def clear_quick_filter_configurations(self):
        pass


class _Users:
    canManageUsers = True

    def __init__(self):
        self.stateChanged = _Signal()


class _Server:
    def __init__(self, records):
        self.records = records
        self.calls = []

    def query(self, search_type, filters, columns):
        self.calls.append((search_type, filters, columns))
        return self.records


class _RuntimeServer(_Server):
    def __init__(self):
        super().__init__([])
        self.insert_calls = []

    def insert(self, search_type, data, *, triggers):
        self._validate_widget_config(data)
        self.insert_calls.append((search_type, data, triggers))
        record = {**data, "code": f"WIDGET_CONFIG{len(self.records) + 1:05}", "login": None}
        self.records.append(record)
        return record

    def query(self, search_type, filters, columns):
        records = super().query(search_type, filters, columns)
        return [deepcopy(record) for record in records if all(
            record.get(key) == value for key, value in filters
        )]

    def build_search_key(self, search_type, code, *, project_code):
        return f"{search_type}?project={project_code}&code={code}"

    def insert_update(self, search_key, data, *, triggers):
        self._validate_widget_config(data)
        record = next(record for record in self.records if search_key.endswith("code=" + record["code"]))
        record.update(data)
        record["login"] = None
        return deepcopy(record)

    def delete_sobject(self, search_key):
        self.records = []

    @staticmethod
    def _validate_widget_config(data):
        # WidgetDbConfig.validate() uses a named <view> for identifiers with
        # @; other ordinary views must be XML element names matching view.
        root = ElementTree.fromstring(data["config"])
        view = data["view"]
        if root.tag != "config":
            raise Fault(1, "It has to begin and end with the <config> </config> tag")
        if "@" in view:
            node = next((item for item in root.findall("view")
                         if item.get("name") == view), None)
        else:
            node = next((item for item in root if item.tag == view), None)
        if node is None:
            raise Fault(1, "The config xml has to begin and end with the "
                        f"<config><{view}> </{view}></config> tag")


class _RuntimeSignal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback, *_args):
        self.callbacks.append(callback)

    def emit(self, value=None):
        for callback in tuple(self.callbacks):
            if value is None:
                callback()
            else:
                callback(value)


class _Worker:
    def __init__(self, callback):
        self.callback = callback
        self.result = _RuntimeSignal()
        self.error = _RuntimeSignal()
        self.finished = _RuntimeSignal()

    def start(self):
        try:
            result = self.callback()
        except Exception as error:
            self.error.emit(({
                "exception": error, "traceback": traceback.format_exc(),
            }, self))
        else:
            self.result.emit(result)
        finally:
            self.finished.emit()


class _Pool:
    is_stopped = False

    @staticmethod
    def add_task(callback):
        return _Worker(callback)


class _DeferredWorker(_Worker):
    def start(self):
        pass

    def complete(self):
        super().start()


class _DeferredPool(_Pool):
    def __init__(self):
        self.workers = []

    def add_task(self, callback):
        worker = _DeferredWorker(callback)
        self.workers.append(worker)
        return worker


class QuickFilterEditorTests(unittest.TestCase):
    def test_supervisor_has_independent_current_tab_and_shared_save(self):
        application = _Application()
        controller = QuickFilterEditorController(application, _Users())
        key = controller._key(application.context)
        controller._loaded[key] = {}
        controller.begin_session()
        controller.set_option_selected("column:category", "characters", True)
        with patch("thlib.tactic_classes.server_start") as server:
            controller.save()
            server.assert_not_called()
        self.assertEqual(len(application.local_saves), 1)
        self.assertEqual(controller._loaded[key], {})
        server = _RuntimeServer()
        runtime = type("Runtime", (), {"server_pool": _Pool()})()
        with patch("thlib.tactic_classes.server_start", return_value=server), \
                patch("thlib.environment.env_inst", runtime):
            controller.save_defaults()
        self.assertEqual(len(server.insert_calls), 1)
        self.assertEqual(controller._loaded[key]["defaultSelections"], {
            "column:category": ["characters", "props"],
        })
        self.assertNotIn("options", controller._loaded[key]["groups"][0])

    def test_custom_sidebar_tabs_have_distinct_server_records_and_round_trip(self):
        application = _Application()
        controller = QuickFilterEditorController(application, _Users())
        server = _RuntimeServer()
        runtime = type("Runtime", (), {"server_pool": _Pool()})()
        with patch("thlib.tactic_classes.server_start", return_value=server), \
                patch("thlib.environment.env_inst", runtime):
            controller.begin_session()
            controller.set_option_selected("column:category", "characters", True)
            controller.save_defaults()
            first_key = controller._context_key
            first_config = deepcopy(controller._loaded[first_key])
            application.context.update(scope_key="demo/asset@my_tasks", tab_id="my_tasks:search")
            controller.begin_session()
            controller.clear_standard()
            controller.set_group_enabled(0, False)
            controller.save_defaults()
            second_key = controller._context_key
            self.assertEqual(len(server.records), 2)
            self.assertEqual({record["view"] for record in server.records}, {
                "quick_filters@demo/asset@assets", "quick_filters@demo/asset@my_tasks",
            })
            self.assertEqual(controller._loaded[first_key], first_config)
            controller._loaded.clear()
            application.context.update(scope_key=first_key[2], tab_id="assets:search")
            controller.ensure_current()
            self.assertEqual(controller._loaded[first_key], first_config)
            application.context.update(scope_key=second_key[2], tab_id="my_tasks:search")
            controller.ensure_current()
            self.assertFalse(controller._loaded[second_key]["groups"][0]["enabled"])
        self.assertFalse(controller.error)

    def test_regular_user_cannot_call_server_save_directly(self):
        application = _Application()
        users = _Users()
        users.canManageUsers = False
        controller = QuickFilterEditorController(application, users)
        controller._loaded[controller._key(application.context)] = {}
        controller.begin_session()
        with patch("thlib.tactic_classes.server_start") as server:
            controller.save_defaults()
            server.assert_not_called()

    def test_regular_editor_excludes_server_hidden_entries_and_saves_only_locally(self):
        application = _Application()
        application.catalog_groups.append({
            "key": "column:secret", "title": "Secret", "enabled": True,
            "options": [{"key": "internal", "title": "Internal", "enabled": True}],
        })
        configuration = {"groups": [
            {"key": "column:category", "enabled": True, "options": ["props"]},
            {"key": "column:secret", "enabled": False},
        ], "defaultSelections": {}}
        application.apply_quick_filter_configuration("demo/asset", configuration)
        user = type("Artist", (), {"canManageUsers": False, "stateChanged": _Signal()})()
        controller = QuickFilterEditorController(application, user)
        controller._loaded[("demo", "demo/asset", "demo/asset@assets")] = configuration
        controller.begin_session()
        self.assertTrue(controller.canEdit)
        self.assertFalse(controller.canSaveDefaults)
        self.assertEqual([group["key"] for group in controller.groups], ["column:category"])
        self.assertEqual([option["key"] for option in controller.groups[0]["options"]], ["props"])
        controller.set_group_enabled(0, False)
        with patch("thlib.tactic_classes.server_start") as server:
            controller.save()
            server.assert_not_called()
        self.assertEqual(application.local_saves[0][0], "assets:search")
        self.assertFalse(controller.groups[0]["enabled"])
        self.assertFalse(controller.dirty)
        controller.discard()
        controller.begin_session()
        self.assertFalse(controller.groups[0]["enabled"])
        controller.set_group_enabled(0, True)
        self.assertEqual(len(controller.groups), 1)
        self.assertEqual(len(controller.groups[0]["options"]), 1)

    def test_delayed_catalog_arrival_populates_open_editor_and_keeps_draft(self):
        application = _Application()
        catalog = deepcopy(application.context["groups"])
        application.context.update(groups=[], loading=True)
        application.catalog_groups = []
        controller = QuickFilterEditorController(application, _Users())
        controller._loaded[("demo", "demo/asset", "demo/asset@assets")] = {}
        controller.begin_session()
        self.assertEqual(controller.groups, [])
        self.assertTrue(controller.busy)
        application.context.update(groups=catalog, loading=False)
        application.quick_filters_changed.emit()
        self.assertEqual(len(controller.groups), 1)
        self.assertFalse(controller.busy)
        controller.set_group_enabled(0, False)
        application.context["groups"].append({
            "key": "column:duration", "title": "Duration", "enabled": True, "options": [],
        })
        application.quick_filters_changed.emit()
        self.assertEqual(len(controller.groups), 2)
        self.assertFalse(controller.groups[0]["enabled"])
        self.assertTrue(controller.dirty)
        controller.discard()
        application.context_requests.clear()
        application.quick_filters_changed.emit()
        self.assertEqual(application.context_requests, [])

    def test_background_standard_load_does_not_build_hidden_editor(self):
        application = _Application()
        controller = QuickFilterEditorController(application, _Users())
        key = ("demo", "demo/asset", "demo/asset@assets")
        controller._context_key = key

        controller._loaded_result((key, "WIDGET_CONFIG00001", {
            "groups": [],
            "defaultSelections": {},
        }))

        self.assertEqual(application.context_requests, [False])
        self.assertEqual(application.applied, [(
            "demo/asset@assets",
            {"groups": [], "defaultSelections": {}},
        )])
        self.assertEqual(controller._groups, [])

    def test_same_search_type_tab_switch_skips_editor_group_discovery(self):
        application = _Application()
        controller = QuickFilterEditorController(application, _Users())
        key = ("demo", "demo/asset", "demo/asset@assets")
        controller._context_key = key
        controller._loaded[key] = {
            "groups": [],
            "defaultSelections": {},
        }

        controller.ensure_current()

        self.assertEqual(application.context_requests, [False])
        self.assertEqual(application.applied, [])

    def test_versioned_payload_is_rejected(self):
        xml = QuickFilterEditorController._configuration_xml({
            "version": 2,
            "groups": [{"key": "status", "enabled": True}],
            "defaultSelections": {},
        }, "quick_filters@demo/asset@assets")

        with self.assertRaisesRegex(ValueError, "fields: version"):
            QuickFilterEditorController._configuration_from_xml(xml, "quick_filters@demo/asset@assets")

    def test_payload_round_trips_unicode_and_starting_state(self):
        source = {
            "groups": [{"key": "status", "enabled": True}],
            "defaultSelections": {"status": ["Готов"]},
        }

        view = "quick_filters@demo/asset@assets"
        xml = QuickFilterEditorController._configuration_xml(source, view)
        restored = QuickFilterEditorController._configuration_from_xml(xml, view)

        self.assertEqual(restored, source)
        root = ElementTree.fromstring(xml)
        self.assertEqual(
            json.loads(root.find("./view/values").text), source
        )

    def test_native_named_view_contract_for_plain_and_custom_tab_codes(self):
        configuration = {"groups": [], "defaultSelections": {"status": ["A&B <done>"]}}
        for scope in ("demo/asset", "complex/scenes@th_episode", "complex/scenes@my_tasks",
                      "demo/asset@Мои_задачи", 'demo/asset@items&"review"'):
            with self.subTest(scope=scope):
                view = QuickFilterEditorController._configuration_view(scope)
                xml = QuickFilterEditorController._configuration_xml(configuration, view)
                _RuntimeServer._validate_widget_config({"config": xml, "view": view})
                root = ElementTree.fromstring(xml)
                self.assertEqual(root.find("view").get("name"), view)
                self.assertEqual(QuickFilterEditorController._configuration_from_xml(xml, view),
                                 configuration)

    def test_mismatched_and_superseded_xml_wrappers_are_rejected(self):
        view = "quick_filters@complex/scenes@th_episode"
        old_xml = '<config><quick_filters><values type="json">{}</values></quick_filters></config>'
        wrong_xml = '<config><view name="another_tab"><values type="json">{}</values></view></config>'
        for xml in (old_xml, wrong_xml):
            with self.subTest(xml=xml):
                with self.assertRaisesRegex(Fault, "config xml has to begin and end"):
                    _RuntimeServer._validate_widget_config({"config": xml, "view": view})
                with self.assertRaisesRegex(ValueError, "values are missing"):
                    QuickFilterEditorController._configuration_from_xml(xml, view)

    def test_global_lookup_accepts_null_and_excludes_personal_records(self):
        server = _Server([
            {"code": "GLOBAL", "login": None},
            {"code": "PERSONAL", "login": "artist"},
        ])

        result = QuickFilterEditorController._query_global_record(
            server, ("demo", "demo/asset", "demo/asset@assets"), ["code", "config"]
        )

        self.assertEqual(result["code"], "GLOBAL")
        self.assertIn("login", server.calls[0][2])
        self.assertNotIn("single", server.calls[0][2])

    def test_duplicate_global_records_fail_explicitly(self):
        server = _Server([{"code": "A"}, {"code": "B"}])

        with self.assertRaisesRegex(RuntimeError, "Multiple shared"):
            QuickFilterEditorController._query_global_record(
                server, ("demo", "demo/asset", "demo/asset@assets"), ["code"]
            )

    def test_editor_starts_with_current_selection_not_server_default(self):
        controller = QuickFilterEditorController(_Application(), _Users())
        controller._loaded[("demo", "demo/asset", "demo/asset@assets")] = {
            "groups": [],
            "defaultSelections": {},
        }
        controller._rebuild(controller._context())

        controller.use_current_as_standard()

        self.assertFalse(controller.dirty)
        self.assertEqual(controller.standardSelectionCount, 1)
        self.assertEqual(
            controller._configuration_from_groups()["defaultSelections"],
            {"column:category": ["props"]},
        )

    def test_save_uses_global_login_and_server_triggers(self):
        application = _Application()
        controller = QuickFilterEditorController(application, _Users())
        controller._loaded[("demo", "demo/asset", "demo/asset@assets")] = {}
        controller._rebuild(controller._context())
        controller.use_current_as_standard()
        server = _RuntimeServer()
        runtime = type("Runtime", (), {"server_pool": _Pool()})()

        with patch("thlib.tactic_classes.server_start", return_value=server), \
                patch("thlib.environment.env_inst", runtime):
            controller.save_defaults()

        self.assertEqual(len(server.insert_calls), 1)
        search_type, data, triggers = server.insert_calls[0]
        self.assertEqual(search_type, "config/widget_config")
        self.assertEqual(data["login"], "")
        self.assertTrue(triggers)
        self.assertFalse(controller.busy)
        saved = controller._configuration_from_xml(data["config"], data["view"])
        self.assertEqual(
            saved["defaultSelections"],
            {"column:category": ["props"]},
        )

    def test_widget_config_change_invalidates_only_affected_project(self):
        application = _Application()
        controller = QuickFilterEditorController(application, _Users())
        controller._loaded = {
            ("demo", "demo/asset", "demo/asset@assets"): {
                "groups": [], "defaultSelections": {},
            },
            ("other", "demo/asset", "demo/asset@assets"): {
                "groups": [], "defaultSelections": {},
            },
        }
        application.context = {}

        controller.apply_server_batch({
            "cacheChanges": [{
                "searchType": "config/widget_config",
                "projectCode": "demo",
                "searchCode": "WIDGET_CONFIG00001",
            }],
        })

        self.assertNotIn(("demo", "demo/asset", "demo/asset@assets"), controller._loaded)
        self.assertIn(("other", "demo/asset", "demo/asset@assets"), controller._loaded)

    def test_background_reload_does_not_discard_editor_changes(self):
        controller = QuickFilterEditorController(_Application(), _Users())
        key = ("demo", "demo/asset", "demo/asset@assets")
        controller._loaded[key] = {}
        controller.begin_session()
        controller.set_group_enabled(0, False)
        controller._loaded_result((key, "GLOBAL", {}))
        self.assertFalse(controller.groups[0]["enabled"])
        self.assertTrue(controller.dirty)

    def test_missing_catalog_values_and_groups_survive_save(self):
        controller = QuickFilterEditorController(_Application(), _Users())
        key = ("demo", "demo/asset", "demo/asset@assets")
        category = {
            "key": "column:category", "enabled": True,
            "options": ["props", "not_currently_loaded"],
        }
        missing = {"key": "column:duration", "enabled": False}
        controller._loaded[key] = {
            "groups": [category, missing], "defaultSelections": {},
        }
        controller._rebuild(controller._context())
        settings = controller._configuration_from_groups()
        self.assertEqual(settings["groups"], [category, missing])

    def test_poll_during_save_waits_and_reads_the_saved_standard(self):
        controller = QuickFilterEditorController(_Application(), _Users())
        key = ("demo", "demo/asset", "demo/asset@assets")
        controller._loaded[key] = {}
        controller.begin_session()
        controller.use_current_as_standard()
        server = _RuntimeServer()
        pool = _DeferredPool()
        runtime = type("Runtime", (), {"server_pool": pool})()
        with patch("thlib.tactic_classes.server_start", return_value=server), \
                patch("thlib.environment.env_inst", runtime):
            controller.save_defaults()
            controller.apply_server_batch({"cacheChanges": [{
                "searchType": "config/widget_config", "projectCode": "demo",
            }]})
            self.assertEqual(len(pool.workers), 1)
            pool.workers[0].complete()
            self.assertEqual(len(pool.workers), 2)
            pool.workers[1].complete()
        self.assertFalse(controller.busy)
        self.assertEqual(controller._loaded[key]["defaultSelections"], {
            "column:category": ["props"],
        })

    def test_invalidated_inflight_read_is_not_applied(self):
        application = _Application()
        controller = QuickFilterEditorController(application, _Users())
        pool = _DeferredPool()
        runtime = type("Runtime", (), {"server_pool": pool})()
        with patch("thlib.tactic_classes.server_start", return_value=_Server([])), \
                patch("thlib.environment.env_inst", runtime):
            controller.ensure_current()
            controller.apply_server_batch({"cacheChanges": [{
                "searchType": "config/widget_config", "projectCode": "demo",
            }]})
            pool.workers[0].complete()
            self.assertEqual(application.applied, [])
            self.assertEqual(len(pool.workers), 2)
            pool.workers[1].complete()
        self.assertEqual(application.applied, [("demo/asset@assets", {})])

    def test_remove_one_starting_value_keeps_other_values_and_group_policy(self):
        controller = QuickFilterEditorController(_Application(), _Users())
        controller._application.context["selections"] = {"column:category": ["props", "characters"]}
        controller._loaded[("demo", "demo/asset", "demo/asset@assets")] = {
            "groups": [],
            "defaultSelections": {"column:category": ["props", "characters"]},
        }
        controller.begin_session()
        controller.remove_standard_selection("column:category", "props")
        self.assertEqual(controller.standardSelections[0]["options"], [
            {"key": "characters", "title": "Characters"},
        ])
        self.assertTrue(controller.groups[0]["enabled"])
        self.assertTrue(controller.dirty)
        controller.remove_standard_selection("column:category", "characters")
        self.assertEqual(controller._configuration_from_groups()["defaultSelections"], {})

    def test_failed_server_readback_keeps_draft_and_reports_error(self):
        controller = QuickFilterEditorController(_Application(), _Users())
        controller._loaded[("demo", "demo/asset", "demo/asset@assets")] = {}
        controller.begin_session()
        controller.set_option_selected("column:category", "characters", True)
        server = _RuntimeServer()
        runtime = type("Runtime", (), {"server_pool": _Pool()})()
        with patch("thlib.tactic_classes.server_start", return_value=server), \
                patch("thlib.environment.env_inst", runtime), \
                patch.object(server, "insert", return_value={"code": "NOT_SAVED"}):
            controller.save_defaults()
        self.assertIn("did not retain", controller.error)
        self.assertFalse(controller.busy)
        self.assertEqual(controller._workers, set())
        self.assertTrue(controller.dirty)
        self.assertEqual(controller._application.notifications, [])

    def test_personal_record_is_never_used_as_shared_standard(self):
        server = _Server([{"code": "PERSONAL", "login": "artist"}])
        self.assertEqual(QuickFilterEditorController._query_global_record(
            server, ("demo", "demo/asset", "demo/asset@assets"), ["code"],
        ), {})

    def test_selection_changes_do_not_hide_values_or_touch_group_visibility(self):
        application = _Application()
        controller = QuickFilterEditorController(application, _Users())
        controller._loaded[controller._key(application.context)] = {}
        controller.begin_session()
        original_groups = deepcopy(controller._groups)
        controller.set_option_selected("column:category", "characters", True)
        controller.set_option_selected("column:category", "characters", True)
        self.assertEqual(controller.standardSelectionCount, 2)
        self.assertTrue(controller.groups[0]["options"][1]["selected"])
        self.assertEqual(controller._groups, original_groups)
        controller.set_option_selected("column:category", "characters", False)
        self.assertFalse(controller.groups[0]["options"][1]["selected"])
        self.assertTrue(controller.groups[0]["options"][1]["enabled"])
        self.assertEqual(controller._groups, original_groups)
        controller.clear_standard()
        self.assertFalse(any(option["selected"] for option in controller.groups[0]["options"]))
        controller.use_current_as_standard()
        self.assertTrue(controller.groups[0]["options"][0]["selected"])

    def test_editor_selection_cannot_resurrect_server_hidden_values_for_regular_users(self):
        application = _Application()
        configuration = {"groups": [{
            "key": "column:category", "options": ["props"],
        }], "defaultSelections": {}}
        application.apply_quick_filter_configuration(application.context["scope_key"], configuration)
        users = _Users()
        users.canManageUsers = False
        controller = QuickFilterEditorController(application, users)
        controller._loaded[controller._key(application.context)] = configuration
        controller.begin_session()
        controller.set_option_selected("column:category", "characters", True)
        self.assertEqual(controller._standard_selections, {"column:category": ["props"]})
        self.assertEqual(len(controller.groups[0]["options"]), 1)
        controller.set_group_enabled(0, False)
        controller.set_option_selected("column:category", "props", True)
        self.assertEqual(controller.standardSelectionCount, 0)


if __name__ == "__main__":
    unittest.main()
