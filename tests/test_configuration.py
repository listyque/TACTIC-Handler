from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from types import ModuleType
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import Mock, patch

from thlib.ui.configuration import (
    ConfigurationController,
    _CHECKIN_CONTROLS,
    read_dcc_preferences,
    write_dcc_preferences,
)
from thlib.ui.application_composition import ConfigurationBridge
from thlib.ui.controllers.commands import CommandsMixin
from thlib.ui.repository_editor import RepositoryEditorController
from thlib.ui.workspace_models.state import WorkspaceState
from thlib.ui.workspace_models.windows import FloatingWindowModel
from thlib.environment import env_mode, env_tactic


QML = Path(__file__).resolve().parents[1] / "thlib" / "ui" / "qml"


class ConfigurationTests(unittest.TestCase):
    def test_repository_check_creates_missing_folders_and_rejects_empty_paths(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / 'repo' / 'assets'
            result = RepositoryEditorController._check_paths({'base': str(target), 'empty': ''})
            self.assertTrue(target.is_dir())
            self.assertTrue(result['base']['ok'])
            self.assertFalse(result['empty']['ok'])
            self.assertEqual(RepositoryEditorController._check_paths({'base': str(target)})['base']['text'], 'Available')

    def test_repository_check_reports_creation_error_without_aborting_other_paths(self):
        with TemporaryDirectory() as directory:
            blocker = Path(directory) / 'file'
            blocker.touch()
            result = RepositoryEditorController._check_paths({'bad': str(blocker / 'repo'), 'good': str(Path(directory) / 'repo')})
            self.assertFalse(result['bad']['ok'])
            self.assertTrue(result['good']['ok'])

    def test_new_repository_defaults_disable_local(self):
        from thlib.ui.repository_editor import _empty_base_dirs
        for key in ('win32_local_repo_dir', 'linux_local_repo_dir'):
            self.assertFalse(_empty_base_dirs()[key][4])
        defaults = {key: '' for key in _empty_base_dirs()}
        with patch.object(env_tactic, 'base_dirs', {}), patch.object(env_tactic, 'get_default_base_dirs', return_value=defaults), patch.object(env_tactic, 'save_base_dirs'), patch('thlib.environment.env_read_config', return_value=None):
            actual = env_tactic.get_base_dirs()
            for key in ('win32_local_repo_dir', 'linux_local_repo_dir'):
                self.assertFalse(actual[key][4])

        saved = _empty_base_dirs()
        saved['win32_local_repo_dir'][4] = True
        with patch.object(env_tactic, 'base_dirs', {}), patch('thlib.environment.env_read_config', return_value=saved):
            self.assertTrue(env_tactic.get_base_dirs()['win32_local_repo_dir'][4])

    def test_handler_server_autostart_defaults_on_and_can_be_disabled(self):
        from thlib.environment import env_inst

        probe = SimpleNamespace(_settings={})
        self.assertTrue(CommandsMixin.handler_server_autostart_enabled(probe))
        probe.debug_log = None
        probe._write_settings = Mock()
        probe._notify = Mock()
        with patch.object(env_inst, "set_thread_counts"):
            CommandsMixin.apply_global_configuration(
                probe, {"autoStartHandlerServer": False},
            )
        self.assertFalse(CommandsMixin.handler_server_autostart_enabled(probe))
        probe._write_settings.assert_called_once()

        source = (QML.parent / "application.py").read_text(encoding="utf-8")
        self.assertIn("if controller.handler_server_autostart_enabled():", source)

    def test_save_all_keeps_configuration_open(self):
        applied = []
        controller = ConfigurationController(
            lambda *_args: None, self.fail,
            global_values=lambda: {"autoStartHandlerServer": True},
            apply_global_configuration=lambda values: applied.append(values),
        )
        controller._original_values["global_preferences"] = {
            "autoStartHandlerServer": True,
        }
        controller.update_page("global_preferences", {
            "autoStartHandlerServer": False,
        })
        closed = []
        controller.closeAllowed.connect(lambda: closed.append(True))

        self.assertTrue(controller.save_all())
        self.assertEqual(applied[0]["autoStartHandlerServer"], False)
        self.assertFalse(controller.dirty)
        self.assertEqual(closed, [])

    def test_server_repository_alias_map_keeps_default_handler_path(self):
        source = {"asset_base_dir": {
            "default": "D:/tactic/assets", "local": "D:/shared/assets",
        }}
        server = SimpleNamespace(get_base_dirs=lambda: source)
        with (
            patch("thlib.tactic_classes.server_start", return_value=server),
            patch("thlib.environment.env_write_config"),
            patch.object(env_tactic, "default_base_dirs", None),
        ):
            self.assertEqual(
                env_tactic.query_base_dirs()["asset_base_dir"],
                "D:/tactic/assets",
            )

    def test_online_web_base_dir_comes_from_server(self):
        local_dirs = {"web_base_dir": ["", "Web", [], "web", False]}
        with (
            patch.object(env_mode, "status", False),
            patch.object(env_tactic, "base_dirs", local_dirs),
            patch.object(env_tactic, "query_base_dirs", return_value={
                "web_base_dir": "/assets",
            }) as query,
            patch.object(env_tactic, "get_base_dirs", return_value=local_dirs),
            patch.object(env_tactic, "save_base_dirs") as save,
            patch.object(env_tactic, "get_custom_dirs"),
        ):
            env_mode.set_online()
            query.assert_called_once_with()
            self.assertEqual(local_dirs["web_base_dir"][0], "/assets")
            save.assert_called_once_with()

    def test_team_repository_sync_updates_selected_alias_and_platform_path(self):
        from thlib.tactic_query import set_team_repository_path

        config = ModuleType("pyasm.common")
        security = SimpleNamespace(
            is_admin=lambda: True,
            get_group_names=lambda: [],
        )
        config.Environment = SimpleNamespace(get_security=lambda: security)
        values = {"default": "D:/old", "review": "D:/review"}
        writes = []
        config.Config = SimpleNamespace(
            get_dict_value=lambda *_args: dict(values),
            get_value=lambda *_args: "D:/old",
            set_value=lambda *_args: writes.append(_args),
            save_config=lambda: writes.append("saved"),
            reload_config=lambda: writes.append("reloaded"),
        )
        with (
            TemporaryDirectory() as directory,
            patch.dict(sys.modules, {"pyasm.common": config}),
        ):
            self.assertEqual(set_team_repository_path(directory, "base"), "updated")
            self.assertEqual(writes[0][2]["default"], directory)
            self.assertEqual(writes[0][2]["review"], "D:/review")
            self.assertEqual(writes[1:], ["saved", "reloaded"])
            security.is_admin = lambda: False
            with self.assertRaises(PermissionError):
                set_team_repository_path(directory, "base")
            security.get_group_names = lambda: ["project_supervisor"]
            self.assertEqual(set_team_repository_path(directory, "base"), "updated")
            with self.assertRaises(ValueError):
                set_team_repository_path(directory, "../invalid")
            writes.clear()
            self.assertEqual(set_team_repository_path(directory, "local"), "updated")
            self.assertEqual(writes[0][2]["local"], directory)
            self.assertEqual(writes[0][2]["review"], "D:/review")
            self.assertEqual(
                writes[1][1],
                "win32_local_repo_dir" if sys.platform == "win32"
                else "linux_local_repo_dir",
            )
            values["default"] = directory
            writes.clear()
            self.assertEqual(
                set_team_repository_path(directory, "base"), "unchanged"
            )
            self.assertEqual(writes, [])

    def test_team_local_mode_forces_transfer_choices_in_shared_config(self):
        from thlib.environment import cfg_controls, env_server
        from thlib.ui.checkin_out import CheckinOutController
        from thlib.ui.message_attachments import AttachmentUploadController
        from thlib.ui.repository_sync import RepositorySyncController

        saved = ConfigurationController._store_controls({}, {
            "previewsThroughHttp": True,
            "checkinMethod": 4,
            "checkoutMethod": 1,
        }, {key: _CHECKIN_CONTROLS[key] for key in (
            "previewsThroughHttp", "checkinMethod", "checkoutMethod"
        )})
        controller = ConfigurationController(lambda *_args: None, self.fail)
        with (
            patch.object(env_server, "is_team_local_repository", return_value=True),
            patch.object(cfg_controls, "checkin", saved),
            patch.object(cfg_controls, "set_checkin") as set_checkin,
        ):
            values = controller._checkin_values()
            self.assertEqual(
                (values["previewsThroughHttp"], values["checkinMethod"],
                 values["checkoutMethod"]),
                (False, 1, 0),
            )
            self.assertFalse(RepositorySyncController.previews_through_http_enabled())
            self.assertEqual(CheckinOutController._checkin_mode(None), "inplace")
            self.assertEqual(AttachmentUploadController._checkin_mode(), "inplace")
            controller._original_values["checkin_preferences"] = values
            controller.update_page("checkin_preferences", {
                **values, "verifyRepositoryMd5": True,
            })
            self.assertTrue(controller._apply_page("checkin_preferences"))

        stored = ConfigurationController._controls_values(
            set_checkin.call_args.args[0], _CHECKIN_CONTROLS
        )
        self.assertEqual(
            (stored["previewsThroughHttp"], stored["checkinMethod"],
             stored["checkoutMethod"]),
            (0, 1, 0),
        )

    def test_all_task_sort_choices_survive_configuration_normalization(self):
        for sort_mode in ("priority", "milestone", "supervisor"):
            with self.subTest(sort_mode=sort_mode):
                values = ConfigurationController._normalize_tasks({
                    "sortMode": sort_mode,
                    "quickViewMode": "compact",
                    "workspaceSurface": "browser",
                })
                self.assertEqual(values["sortMode"], sort_mode)
                self.assertEqual(values["quickViewMode"], "compact")
                self.assertEqual(values["workspaceSurface"], "browser")

    def test_task_column_draft_is_normalized_for_configuration_save(self):
        values = ConfigurationController._normalize_tasks({
            "columns": [{
                "key": "status", "label": "Status", "width": 900,
                "visible": False, "required": False,
            }],
        })
        self.assertEqual(values["columns"], [{
            "key": "status", "label": "Status", "width": 480,
            "visible": False, "required": False, "order": 0,
        }])

    def test_checkin_runtime_preferences_use_their_existing_owners(self):
        calls = []
        controller = SimpleNamespace(
            loading_mode="pages",
            snapshot_browser_show_all=False,
            snapshot_browser_show_more=True,
            snapshot_browser_content_mode="both",
            snapshot_browser_image_mode="fit",
            snapshot_browser_orientation="horizontal",
            set_loading_mode=lambda value: calls.append(("loading", value)),
            toggle_snapshot_browser_option=lambda value: calls.append(
                ("snapshot-toggle", value)
            ),
            set_snapshot_browser_content_mode=lambda value: calls.append(
                ("snapshot-content", value)
            ),
            set_snapshot_browser_image_mode=lambda value: calls.append(
                ("snapshot-image", value)
            ),
            set_snapshot_browser_orientation=lambda value: calls.append(
                ("snapshot-orientation", value)
            ),
            refresh_checkin_defaults=lambda: calls.append(("reload", "core")),
            repository_sync=SimpleNamespace(
                reload_configuration=lambda: calls.append(
                    ("reload", "repository-sync")
                )
            ),
        )
        commit_queue = SimpleNamespace(
            autoClean=False,
            set_auto_clean=lambda value: calls.append(("auto-clean", value)),
            reload_repository_configuration=lambda: calls.append(
                ("reload", "commit-queue")
            ),
        )
        delivery = SimpleNamespace(
            commit_queue=commit_queue,
            checkin_out=SimpleNamespace(
                reload_repository_configuration=lambda: calls.append(
                    ("reload", "checkin-out")
                )
            ),
            drop_plate=SimpleNamespace(
                reload_configuration=lambda: calls.append(
                    ("reload", "drop-plate")
                )
            ),
        )
        bridge = ConfigurationBridge(
            SimpleNamespace(controller=controller), None, None, delivery
        )

        self.assertEqual(bridge.checkin_values(), {
            "loadingMode": "pages",
            "snapshotShowAll": False,
            "snapshotShowMore": True,
            "snapshotContentMode": "both",
            "snapshotImageMode": "fit",
            "snapshotOrientation": "horizontal",
            "commitQueueAutoClean": False,
        })
        bridge.apply_checkin({
            "loadingMode": "infinite",
            "snapshotShowAll": True,
            "snapshotShowMore": True,
            "snapshotContentMode": "files",
            "snapshotImageMode": "fill",
            "snapshotOrientation": "vertical",
            "commitQueueAutoClean": True,
        })

        self.assertIn(("loading", "infinite"), calls)
        self.assertIn(("snapshot-toggle", "all"), calls)
        self.assertNotIn(("snapshot-toggle", "more"), calls)
        self.assertIn(("snapshot-content", "files"), calls)
        self.assertIn(("snapshot-image", "fill"), calls)
        self.assertIn(("snapshot-orientation", "vertical"), calls)
        self.assertIn(("auto-clean", True), calls)

    def test_checkin_apply_forwards_runtime_preferences(self):
        applied = []
        controller = ConfigurationController(
            lambda *_args: None,
            lambda _message: None,
            apply_checkin_configuration=applied.append,
            checkin_values=lambda: {
                "loadingMode": "pages",
                "snapshotContentMode": "both",
            },
        )
        with patch(
            "thlib.environment.cfg_controls.get_checkin", return_value={}
        ), patch("thlib.environment.cfg_controls.set_checkin"):
            controller.begin_session()
            values = controller.page_values("checkin_preferences")
            values["loadingMode"] = "infinite"
            values["snapshotContentMode"] = "preview"
            controller.update_page("checkin_preferences", values)
            self.assertTrue(controller._apply_page("checkin_preferences"))

        self.assertEqual(applied[0]["loadingMode"], "infinite")
        self.assertEqual(applied[0]["snapshotContentMode"], "preview")

    def test_maya_preferences_come_from_the_connector_schema(self):
        with patch("thlib.ui.configuration.env_read_config", return_value={}):
            defaults = read_dcc_preferences("maya")

        self.assertEqual(defaults["scene_type"], "mayaBinary")
        self.assertTrue(defaults["focus_after_open"])
        self.assertTrue(defaults["focus_after_save"])
        self.assertFalse(defaults["create_maya_dirs"])
        self.assertTrue(defaults["create_playblast"])

        saved = {
            "maya": {
                "scene_type": "mayaAscii",
                "focus_after_open": False,
                "focus_after_save": True,
                "create_maya_dirs": True,
                "create_playblast": False,
            }
        }
        with patch(
            "thlib.ui.configuration.env_read_config", return_value=saved
        ):
            values = read_dcc_preferences("maya")
        self.assertEqual(values, saved["maya"])

    def test_dcc_preferences_have_one_generic_owner(self):
        with patch(
            "thlib.ui.configuration.env_read_config", return_value={}
        ), patch(
            "thlib.ui.configuration.env_write_config"
        ) as write_config:
            write_dcc_preferences("maya", {
                "current_workdir": "D:/project",
                "focus_after_open": False,
                "focus_after_save": True,
                "create_maya_dirs": True,
                "create_playblast": False,
                "scene_type": "mayaAscii",
            })

        stored = write_config.call_args.args[0]["maya"]
        self.assertNotIn("current_workdir", stored)
        self.assertEqual(stored["scene_type"], "mayaAscii")
        self.assertFalse(stored["focus_after_open"])
        self.assertTrue(stored["create_maya_dirs"])
        dcc_page = (
            QML / "ConfigurationDccPage.qml"
        ).read_text(encoding="utf-8")
        checkin_page = (QML / "CheckinOptionsPage.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("root.schema.sections", dcc_page)
        self.assertNotIn("create_maya_dirs", checkin_page)
        self.assertNotIn("create_playblast", checkin_page)

    def test_maya_workspace_is_live_read_only_configuration(self):
        scene = {"project": "D:/maya/project"}
        with patch("thlib.ui.configuration.env_read_config", return_value={}):
            controller = ConfigurationController(
                lambda *_args: None, lambda _message: None,
                dcc_runtime_values=lambda application: (
                    scene if application == "maya" else {}
                ),
            )
            controller.begin_session()
            self.assertEqual(
                controller.page_values("dcc.maya")["current_workdir"],
                "D:/maya/project",
            )
            scene["project"] = "D:/maya/next"
            self.assertEqual(
                controller.page_values("dcc.maya")["current_workdir"],
                "D:/maya/next",
            )
            self.assertFalse(controller.dirty)

    def test_current_repository_defaults_to_only_active_repository(self):
        repositories = [("base", {
            "name": "asset_base_dir",
            "value": ["D:/repo", "General", "", "base", True],
        })]
        with patch.object(
            env_tactic, "get_all_base_dirs", return_value=repositories
        ), patch(
            "thlib.environment.cfg_controls.get_checkin", return_value={}
        ), patch(
            "thlib.global_functions.get_value_from_config",
            return_value=None,
        ):
            repository = env_tactic.get_current_repo()

        self.assertEqual(repository, repositories[0][1])

    def test_current_repository_recovers_from_stale_index(self):
        repositories = [("base", {
            "name": "asset_base_dir",
            "value": ["D:/repo", "General", "", "base", True],
        })]
        with patch.object(
            env_tactic, "get_all_base_dirs", return_value=repositories
        ), patch(
            "thlib.environment.cfg_controls.get_checkin", return_value={}
        ), patch(
            "thlib.global_functions.get_value_from_config",
            return_value=7,
        ):
            repository = env_tactic.get_current_repo()

        self.assertEqual(repository, repositories[0][1])

    def test_selected_language_is_installed_before_appearance_save_notice(self):
        calls = []
        controller = SimpleNamespace(
            apply_appearance_configuration=lambda _values: calls.append(
                "notification"
            )
        )
        localization = SimpleNamespace(
            set_language=lambda _language: calls.append("language")
        )
        bridge = ConfigurationBridge(
            SimpleNamespace(
                controller=controller,
                localization=localization,
            ),
            None,
            None,
            None,
        )

        bridge.apply_appearance({"language": "ru"})

        self.assertEqual(calls, ["language", "notification"])

    def test_render_backend_preference_is_persisted_for_next_start(self):
        class PreferencesOwner:
            def __init__(self):
                self._settings = {
                    "appearance/renderBackend": "automatic",
                }
                self._click_animations_enabled = True
                self._hover_animations_enabled = True
                self._fade_animations_enabled = True
                self._popup_animations_enabled = True
                self.animation_preferences_changed = SimpleNamespace(
                    emit=lambda: self.notifications.append("motion")
                )
                self.debug_log = None
                self.notifications = []
                self.write_count = 0

            def close_to_tray_enabled(self):
                return True

            def set_dark_theme(self, _enabled):
                pass

            def set_theme_style(self, _style):
                pass

            def set_theme_accents(self, _values):
                pass

            def set_icon_set(self, _value):
                pass

            def _write_settings(self):
                self.write_count += 1

            def _notify(self, message):
                self.notifications.append(message)

        owner = PreferencesOwner()

        translated_notice = (
            "Графический API сохранён. Перезапустите TACTIC Handler, "
            "чтобы применить его."
        )
        with patch(
            "thlib.ui.controllers.commands.QCoreApplication.translate",
            return_value=translated_notice,
        ) as translate:
            CommandsMixin.apply_appearance_configuration(owner, {
                "closeToTray": True,
                "renderBackend": "opengl",
                "clickAnimations": False,
                "hoverAnimations": False,
                "fadeAnimations": False,
                "popupAnimations": False,
            })

        self.assertEqual(
            owner._settings["appearance/renderBackend"], "opengl"
        )
        self.assertGreaterEqual(owner.write_count, 1)
        self.assertEqual(owner.notifications[-1], translated_notice)
        self.assertIn("motion", owner.notifications)
        self.assertFalse(owner._click_animations_enabled)
        self.assertFalse(owner._hover_animations_enabled)
        self.assertFalse(owner._fade_animations_enabled)
        self.assertFalse(owner._popup_animations_enabled)
        self.assertFalse(owner._settings["appearance/clickAnimations"])
        self.assertFalse(owner._settings["appearance/hoverAnimations"])
        self.assertFalse(owner._settings["appearance/fadeAnimations"])
        self.assertFalse(owner._settings["appearance/popupAnimations"])
        translate.assert_called_once_with(
            "TacticHandler",
            "Graphics backend saved. Restart TACTIC Handler to apply it.",
        )

    def test_process_tab_cache_setting_keeps_its_existing_storage_key(self):
        class CacheOwner:
            def __init__(self):
                self._settings = {"workspace/cacheProcessTabs": True}
                self.flush_count = 0
                self.write_count = 0

            def _search_cache_enabled(self):
                return bool(self._settings["workspace/cacheProcessTabs"])

            def flush_search_cache(self):
                self.flush_count += 1

            def _write_settings(self):
                self.write_count += 1

        owner = CacheOwner()

        self.assertEqual(
            CommandsMixin.configuration_workspace_cache_values(owner),
            {"cacheProcessTabs": True},
        )
        CommandsMixin.apply_workspace_cache_configuration(
            owner, {"cacheProcessTabs": False}
        )

        self.assertFalse(owner._settings["workspace/cacheProcessTabs"])
        self.assertEqual(owner.flush_count, 1)
        self.assertEqual(owner.write_count, 1)

    def test_repositories_page_is_immediately_below_server(self):
        pages = WorkspaceState().configuration_page_model.records()

        self.assertEqual(
            [page["target"] for page in pages[:3]],
            ["server", "repository", "project"],
        )
        self.assertIn("repository", ConfigurationController._builtin_pages)

    def test_repository_setup_requires_default_platform_path(self):
        records = [
            {
                "title": "General",
                "code": "base",
                "windowsPath": "",
                "linuxPath": "/mnt/tactic",
                "active": True,
                "isDefault": True,
            },
            {
                "title": "Local",
                "code": "local",
                "windowsPath": "D:/TACTIC/local",
                "linuxPath": "",
                "active": True,
                "isDefault": False,
            },
        ]

        missing = RepositoryEditorController._configuration_summary(
            records, "windowsPath"
        )
        configured = RepositoryEditorController._configuration_summary(
            records, "linuxPath"
        )

        self.assertFalse(missing["configured"])
        self.assertEqual(missing["title"], "General")
        self.assertEqual(missing["activeCount"], 2)
        self.assertTrue(configured["configured"])
        self.assertEqual(configured["path"], "/mnt/tactic")

        handoff_only = RepositoryEditorController._configuration_summary(
            [{
                "title": "Handoff",
                "code": "client_handoff",
                "windowsPath": "D:/handoff",
                "active": True,
                "isDefault": False,
                "defaultEligible": False,
            }],
            "windowsPath",
        )
        self.assertFalse(handoff_only["configured"])

    def test_checkin_page_does_not_overwrite_repository_editor_default(self):
        normalized = ConfigurationController._normalize_checkin({
            "loadingMode": "infinite",
            "snapshotShowAll": True,
            "snapshotShowMore": True,
            "snapshotContentMode": "files",
            "snapshotImageMode": "fill",
            "snapshotOrientation": "vertical",
            "commitQueueAutoClean": True,
        })
        self.assertEqual(normalized["loadingMode"], "infinite")
        self.assertTrue(normalized["snapshotShowAll"])
        self.assertTrue(normalized["snapshotShowMore"])
        self.assertEqual(normalized["snapshotContentMode"], "files")
        self.assertEqual(normalized["snapshotImageMode"], "fill")
        self.assertEqual(normalized["snapshotOrientation"], "vertical")
        self.assertTrue(normalized["commitQueueAutoClean"])
        stored = ConfigurationController._store_controls(
            {
                "QComboBox": {
                    "obj_name": ["repositoryComboBox"],
                    "value": [2],
                }
            },
            normalized,
            _CHECKIN_CONTROLS,
        )

        names = stored["QComboBox"]["obj_name"]
        values = stored["QComboBox"]["value"]
        self.assertEqual(values[names.index("repositoryComboBox")], 2)

    def test_appearance_normalizes_accents_and_icon_set(self):
        values = ConfigurationController._normalize_appearance({
            "cacheProcessTabs": True,
            "darkTheme": False,
            "themeStyle": "fluent",
            "themeAccents": {
                "fluent": {"light": "emerald", "dark": "indigo"},
            },
            "iconSet": "material-design",
            "renderBackend": "d3d11",
            "language": "en",
            "debugLogLevels": ["ERROR"],
        })

        self.assertEqual(values["themeStyle"], "fluent")
        self.assertEqual(values["themeAccents"]["fluent"], {
            "light": "emerald", "dark": "indigo",
        })
        self.assertEqual(values["iconSet"], "material-design")
        self.assertEqual(values["renderBackend"], "d3d11")
        self.assertTrue(values["clickAnimations"])
        self.assertTrue(values["hoverAnimations"])
        self.assertTrue(values["fadeAnimations"])
        self.assertTrue(values["popupAnimations"])
        self.assertNotIn("closeToTray", values)
        self.assertNotIn("debugLogLevels", values)
        self.assertNotIn("cacheProcessTabs", values)

        disabled = ConfigurationController._normalize_global({
            "closeToTray": False,
            "serverThreads": 99,
            "localThreads": 0,
        })
        self.assertFalse(disabled["closeToTray"])
        self.assertEqual(disabled["serverThreads"], 32)
        self.assertEqual(disabled["localThreads"], 1)
        self.assertNotIn("renderBackend", disabled)

        motion_disabled = ConfigurationController._normalize_appearance({
            "clickAnimations": False,
            "hoverAnimations": False,
            "fadeAnimations": False,
            "popupAnimations": False,
        })
        self.assertFalse(motion_disabled["clickAnimations"])
        self.assertFalse(motion_disabled["hoverAnimations"])
        self.assertFalse(motion_disabled["fadeAnimations"])
        self.assertFalse(motion_disabled["popupAnimations"])
        initial_popup_preference = ConfigurationController._normalize_appearance({
            "fadeAnimations": False,
        })
        self.assertFalse(initial_popup_preference["popupAnimations"])
        independent_popup_preference = ConfigurationController._normalize_appearance({
            "fadeAnimations": False, "popupAnimations": True,
        })
        self.assertTrue(independent_popup_preference["popupAnimations"])

    def test_appearance_exposes_independent_animation_controls(self):
        source = (
            QML / "ConfigurationAppearancePage.qml"
        ).read_text(encoding="utf-8")

        for key, title in (
            ("clickAnimations", "Click animations"),
            ("hoverAnimations", "Hover animations"),
            ("fadeAnimations", "Fades and transitions"),
            ("popupAnimations", "Menu and popup animations"),
        ):
            self.assertIn(f'"{key}": {key}.checked', source)
            self.assertIn(f'id: {key}', source)
            self.assertIn(f'title: qsTr("{title}")', source)

    def test_appearance_exposes_render_backend_picker(self):
        source = (
            QML / "ConfigurationAppearancePage.qml"
        ).read_text(encoding="utf-8")

        self.assertIn('"renderBackend": renderBackend.currentValue', source)
        self.assertIn('title: qsTr("Graphics backend")', source)
        for backend in (
            "automatic", "opengl", "d3d11", "d3d12", "vulkan",
            "software",
        ):
            self.assertIn(f'"value": "{backend}"', source)

    def test_cache_page_normalizes_every_server_data_domain(self):
        values = ConfigurationController._normalize_cache({
            "reference": False,
            "messages": False,
        })

        self.assertFalse(values["reference"])
        self.assertFalse(values["messages"])
        self.assertTrue(values["search"])
        self.assertTrue(values["tasks"])
        self.assertTrue(values["cacheProcessTabs"])
        self.assertEqual(len(values), 10)

    def test_obsolete_checkinout_configuration_page_is_not_registered(self):
        self.assertNotIn(
            "checkinout_preferences", ConfigurationController._builtin_pages
        )
        self.assertNotIn(
            "checkinout_preferences",
            [window.window_id for window in FloatingWindowModel._defaults()],
        )

    def test_project_creation_wizard_is_native_modal(self):
        wizard = next(
            window for window in FloatingWindowModel._defaults()
            if window.window_id == "project_wizard"
        )

        self.assertEqual(wizard.kind, "project_wizard")
        self.assertTrue(wizard.blocking)
        self.assertIn(
            "project_wizard", FloatingWindowModel._context_required_windows
        )
        self.assertEqual(
            FloatingWindowModel._content_source(wizard),
            "ProjectWizardView.qml",
        )

    def test_project_editor_is_native_modal_and_uses_shared_project_card(self):
        editor = next(
            window for window in FloatingWindowModel._defaults()
            if window.window_id == "project_editor"
        )

        self.assertEqual(editor.kind, "project_editor")
        self.assertTrue(editor.blocking)
        self.assertIn(
            "project_editor", FloatingWindowModel._context_required_windows
        )
        self.assertEqual(
            FloatingWindowModel._content_source(editor),
            "ProjectEditorView.qml",
        )
        configuration = (QML / "ConfigurationProjectPage.qml").read_text(
            encoding="utf-8"
        )
        chooser = (QML / "ProjectChooser.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn("Controls.ProjectCard {", configuration)
        self.assertIn("Controls.ProjectCard {", chooser)
        self.assertIn('appController.edit_project(', configuration)

    def test_configuration_uses_shared_explained_setting_rows(self):
        section = (QML / "ConfigurationSection.qml").read_text(
            encoding="utf-8"
        )
        row = (QML / "controls" / "SettingsRow.qml").read_text(
            encoding="utf-8"
        )
        checkin = (QML / "CheckinOptionsPage.qml").read_text(
            encoding="utf-8"
        )
        configuration_files = [
            QML / "ConfigurationPage.qml",
            QML / "ConfigurationServerPage.qml",
            QML / "ConfigurationRepositoryPage.qml",
            QML / "ConfigurationProjectPage.qml",
            QML / "ConfigurationGlobalPreferencesPage.qml",
            QML / "ConfigurationTaskPreferencesPage.qml",
            QML / "ConfigurationCachePage.qml",
            QML / "ConfigurationDccPage.qml",
            QML / "DccSettingField.qml",
            QML / "ConfigurationAppearancePage.qml",
        ]
        configuration = "\n".join(
            path.read_text(encoding="utf-8")
            for path in configuration_files
        )

        configuration_view = (QML / "ConfigurationView.qml").read_text(
            encoding="utf-8"
        )
        global_preferences = (
            QML / "ConfigurationGlobalPreferencesPage.qml"
        ).read_text(encoding="utf-8")
        cache_preferences = (
            QML / "ConfigurationCachePage.qml"
        ).read_text(encoding="utf-8")
        for source in (configuration_view, configuration, checkin):
            self.assertEqual(
                source.count("ScrollBar.vertical: Controls.ScrollBar"),
                source.count("flickableTarget:"),
            )

        self.assertIn('color: "transparent"', section)
        self.assertIn("property bool fillContentHeight", section)
        self.assertIn("property string description", row)
        self.assertIn("default property alias controlData", row)
        self.assertGreaterEqual(checkin.count("Controls.SettingsRow {"), 25)
        self.assertIn('title: qsTr("Repository synchronization")', checkin)
        self.assertGreaterEqual(configuration.count("Controls.SettingsRow {"), 15)
        self.assertIn('"closeToTray": closeToTray.checked', global_preferences)
        self.assertIn('"serverThreads": serverThreads.value', global_preferences)
        self.assertIn('"localThreads": localThreads.value', global_preferences)
        self.assertIn('title: qsTr("Close to system tray")', global_preferences)
        self.assertIn(
            'objectName: "activityFeedNotificationsSwitch"',
            global_preferences,
        )
        self.assertIn(
            "activityFeedController.set_notifications_enabled(",
            global_preferences,
        )
        self.assertNotIn("cacheProcessTabs", global_preferences)
        self.assertIn(
            'title: qsTr("Cache process tabs")', cache_preferences
        )
        self.assertIn(
            'title: qsTr("Clear tabs cache")', cache_preferences
        )

if __name__ == "__main__":
    unittest.main()
