from __future__ import annotations

from copy import deepcopy
import json
import traceback
from xml.etree import ElementTree

from PySide6.QtCore import QObject, Property, Signal, Slot

from .quick_filters import QuickFilterCatalog
from .tel_filters import CURRENT_LOGIN_FILTER


class QuickFilterEditorController(QObject):
    """One editor draft: a tab layout or a supervisor-owned server default."""

    stateChanged = Signal()

    _category = "quick_filters"

    def __init__(self, application, users, parent=None) -> None:
        super().__init__(parent)
        self._application = application
        self._users = users
        self._groups: list[dict] = []
        self._original_groups: list[dict] = []
        self._original_configuration: dict = {}
        self._standard_selections: dict[str, list[str]] = {}
        self._original_standard_selections: dict[str, list[str]] = {}
        self._context_key: tuple[str, str, str] = ("", "", "")
        self._context_title = ""
        self._busy = False
        self._error = ""
        self._workers = set()
        self._loading_keys: set[tuple[str, str, str]] = set()
        self._reload_pending: set[tuple[str, str, str]] = set()
        self._loaded: dict[tuple[str, str, str], dict] = {}
        self._record_codes: dict[tuple[str, str, str], str] = {}
        self._success_message = ""
        self._session_open = False
        self._tab_id = ""
        self._catalog_loading = False
        self._catalog_error = ""
        application.window_model.windowVisibilityChanged.connect(
            self._window_visibility_changed
        )
        try:
            users.stateChanged.connect(self.stateChanged.emit)
        except (AttributeError, TypeError):
            pass
        try:
            application.section_state_changed.connect(self.ensure_current)
            application.project_changed.connect(self._project_changed)
            application.quick_filters_changed.connect(self._catalog_changed)
        except (AttributeError, TypeError):
            pass

    def _context(self, include_groups: bool = True) -> dict:
        return dict(self._application.quick_filter_editor_context(
            include_groups=include_groups,
            shared=self.canSaveDefaults,
        ) or {})

    @staticmethod
    def _key(context) -> tuple[str, str, str]:
        return (
            str(context.get("project_code") or ""),
            str(context.get("search_type") or ""),
            str(context.get("scope_key") or ""),
        )

    @Property(bool, notify=stateChanged)
    def canEdit(self) -> bool:
        return all(self._context_key) and self._context_key in self._loaded

    @Property(bool, notify=stateChanged)
    def canSaveDefaults(self) -> bool:
        try:
            return bool(self._users.canManageUsers)
        except (AttributeError, RuntimeError):
            return False

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy or self._catalog_loading

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return (
            self._groups != self._original_groups
            or self._standard_selections
            != self._original_standard_selections
        )

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error or self._catalog_error

    @Property(str, notify=stateChanged)
    def contextTitle(self) -> str:
        return self._context_title

    @Property("QVariantList", notify=stateChanged)
    def groups(self) -> list[dict]:
        groups = deepcopy(self._groups)
        for group in groups:
            if group["key"] in QuickFilterCatalog._TASK_KEYS:
                group["title"] = self.tr(group["title"])
            selected = set(self._standard_selections.get(group["key"], ()))
            for option in group.get("options", ()):
                option["selected"] = option["key"] in selected
        return groups

    @Property("QVariantList", notify=stateChanged)
    def standardSelections(self) -> list[dict]:
        groups = {
            str(group.get("key") or ""): group for group in self._groups
        }
        result = []
        for key, values in self._standard_selections.items():
            group = groups.get(key, {})
            option_titles = {
                str(option.get("key") or ""): str(
                    option.get("title") or option.get("key") or ""
                )
                for option in group.get("options", ())
            }
            titles = [
                self.tr("MY TASKS")
                if value == CURRENT_LOGIN_FILTER
                else option_titles.get(value, value)
                for value in values
            ]
            if titles:
                result.append({
                    "key": key,
                    "title": self.tr(str(group.get("title") or key))
                    if key in QuickFilterCatalog._TASK_KEYS
                    else str(group.get("title") or key),
                    "values": titles,
                    "options": [
                        {"key": value, "title": title}
                        for value, title in zip(values, titles)
                    ],
                })
        return result

    @Property(int, notify=stateChanged)
    def standardSelectionCount(self) -> int:
        return sum(len(values) for values in self._standard_selections.values())

    def _set_busy(self, value: bool, error: str = "") -> None:
        self._busy = bool(value)
        self._error = str(error or "")
        self.stateChanged.emit()

    @staticmethod
    def _configuration_from_xml(value: str, view: str) -> dict:
        if not str(value or "").strip():
            return {}
        root = ElementTree.fromstring(value)
        view_node = next((node for node in root.findall("view")
                          if node.get("name") == view), None)
        element = view_node.find("values") if view_node is not None else None
        if root.tag != "config":
            raise ValueError("Quick-filter configuration must have a config root")
        if element is None or not str(element.text or "").strip():
            raise ValueError(
                "Quick-filter configuration values are missing"
            )
        result = json.loads(element.text)
        result = QuickFilterCatalog.validate_configuration(result)
        defaults = result["defaultSelections"]
        result["defaultSelections"] = {
            str(key): list(dict.fromkeys(
                str(item) for item in values if str(item or "")
            ))
            for key, values in defaults.items()
            if str(key or "")
        }
        return result

    @staticmethod
    def _configuration_xml(configuration: dict, view: str) -> str:
        root = ElementTree.Element("config")
        quick_filters = ElementTree.SubElement(root, "view", {"name": view})
        values = ElementTree.SubElement(
            quick_filters, "values", {"type": "json"}
        )
        values.text = json.dumps(
            configuration, ensure_ascii=False, separators=(",", ":")
        )
        return ElementTree.tostring(root, encoding="unicode")

    @staticmethod
    def _configuration_view(scope_key: str) -> str:
        # WidgetDbConfig uses <view name="..."> when the view contains @.
        # This supports native sidebar codes without using them as XML tags.
        return "quick_filters@" + scope_key

    def _configuration_from_groups(self) -> dict:
        original_settings = {
            record["key"]: record
            for record in self._original_configuration.get("groups", [])
        }
        original_groups = {
            group["key"]: group for group in self._original_groups
        }
        groups = []
        for group in self._groups:
            options = list(group.get("options") or ())
            record = {
                "key": str(group.get("key") or ""),
                "enabled": bool(group.get("enabled", True)),
            }
            enabled = [
                str(option.get("key") or "")
                for option in options if option.get("enabled", True)
            ]
            # Omitting the list means all current and future values.
            if len(enabled) != len(options):
                record["options"] = enabled
            original = original_settings.get(record["key"], {})
            original_options = original_groups.get(
                record["key"], {}
            ).get("options", [])
            if "options" in original:
                if options == original_options:
                    record["options"] = deepcopy(original["options"])
                else:
                    # A partial catalog must not erase allowed values which
                    # are absent from the current query/catalog response.
                    known = {str(option["key"]) for option in options}
                    absent = [
                        value for value in original["options"]
                        if value not in known
                    ]
                    if absent or len(enabled) != len(options):
                        record["options"] = list(dict.fromkeys(
                            enabled + absent
                        ))
            groups.append(record)
        present = {record["key"] for record in groups}
        groups.extend(
            deepcopy(record) for key, record in original_settings.items()
            if key not in present
        )
        settings = {record["key"]: record for record in groups}
        defaults = {}
        for key, source_values in self._standard_selections.items():
            setting = settings.get(key)
            if setting and setting.get("enabled", True) is False:
                continue
            values = {
                str(value) for value in source_values if str(value or "")
            }
            allowed = setting.get("options") if setting else None
            if isinstance(allowed, list):
                values.intersection_update(str(value) for value in allowed)
            if values:
                defaults[key] = sorted(values)
        return {
            "groups": groups,
            "defaultSelections": defaults,
        }

    def _rebuild(self, context: dict, *, preserve_draft: bool = False) -> None:
        draft = self._configuration_from_groups() if preserve_draft else None
        self._context_key = self._key(context)
        self._tab_id = str(context.get("tab_id") or "")
        self._context_title = str(context.get("title") or "")
        self._groups = deepcopy(context.get("groups") or [])
        self._catalog_loading = bool(context.get("loading"))
        self._catalog_error = str(context.get("error") or "")
        configuration = {
            "groups": context.get("layout") or self._loaded.get(
                self._context_key, {}
            ).get("groups", []),
            "defaultSelections": context.get("selections") or {},
        }
        self._original_configuration = deepcopy(configuration)
        self._standard_selections = deepcopy(
            configuration.get("defaultSelections") or {}
        )
        self._original_groups = deepcopy(self._groups)
        self._original_standard_selections = deepcopy(
            self._standard_selections
        )
        if draft is not None:
            self._groups = QuickFilterCatalog.configured_groups(
                self._groups, draft, include_hidden=True,
            )
            self._standard_selections = draft["defaultSelections"]
            # Strip selections removed by the refreshed server policy as well
            # as locally disabled entries, before exposing the draft to QML.
            allowed_groups = {group["key"]: group for group in self._groups}
            self._standard_selections = {
                key: values for key, values in self._standard_selections.items()
                if key in allowed_groups
            }
            if not self.canSaveDefaults:
                for key, values in self._standard_selections.items():
                    options = allowed_groups[key].get("options", [])
                    if key != "assigned":
                        allowed = {option["key"] for option in options}
                        self._standard_selections[key] = [
                            value for value in values if value in allowed
                        ]
            self._standard_selections = self._configuration_from_groups()[
                "defaultSelections"
            ]
        self.stateChanged.emit()

    @Slot()
    def _catalog_changed(self) -> None:
        if not self._session_open:
            return
        context = self._context()
        same_tab = str(context.get("tab_id") or "") == self._tab_id
        self._rebuild(context, preserve_draft=same_tab and self.dirty)

    @classmethod
    def _query_global_record(cls, server, key, columns) -> dict:
        records = server.query(
            "config/widget_config",
            [
                ("view", cls._configuration_view(key[2])),
                ("search_type", key[1]),
                ("category", cls._category),
            ],
            list(dict.fromkeys([*columns, "login"])),
        ) or []
        if isinstance(records, dict):
            records = [records]
        # Both NULL and an empty login mean project-wide in widget_config.
        # Fetch the exact view/category/type coordinate, then exclude personal
        # rows; an equality filter for "" misses NULL-backed shared records.
        records = [record for record in records if not record.get("login")]
        if len(records) > 1:
            raise RuntimeError(
                "Multiple shared quick-filter standards exist for "
                f"{key[2]}. Remove the duplicate widget_config records."
            )
        return dict(records[0]) if records else {}

    @Slot()
    def ensure_current(self) -> None:
        # The sidebar entry is stable across users, unlike a runtime tab id.
        # Building editor groups scans every loaded sObject and is only needed
        # when the modal editor actually opens.
        context = self._context(include_groups=False)
        key = self._key(context)
        if not all(key):
            return
        if key == self._context_key and key in self._loaded:
            return
        self._context_key = key
        if key in self._loaded:
            self._application.apply_quick_filter_configuration(
                key[2], self._loaded[key]
            )
            return
        if key in self._loading_keys:
            return

        def query():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=key[0])
            record = self._query_global_record(
                server, key, ["code", "config"]
            )
            configuration = self._configuration_from_xml(
                str(record.get("config") or ""), self._configuration_view(key[2]),
            )
            return key, str(record.get("code") or ""), configuration

        self._loading_keys.add(key)
        self._run(query, self._loaded_result, loading_key=key)

    @Slot()
    def begin_session(self) -> None:
        self._session_open = True
        self.ensure_current()
        self._application.request_quick_filter_data(False)
        self._rebuild(self._context())

    @Slot(str, bool)
    def _window_visibility_changed(self, window_id: str, visible: bool) -> None:
        if window_id != "quick_filter_editor":
            return
        if visible:
            self.begin_session()
        else:
            self.discard()

    @Slot(int, bool)
    def set_group_enabled(self, row: int, enabled: bool) -> None:
        if not self.canEdit or self.busy or not 0 <= row < len(self._groups):
            return
        self._groups[row]["enabled"] = bool(enabled)
        self._standard_selections = self._configuration_from_groups()[
            "defaultSelections"
        ]
        self.stateChanged.emit()

    @Slot(str, str, bool)
    def set_option_selected(
            self, group_key: str, value: str, selected: bool
    ) -> None:
        if not self.canEdit or self.busy:
            return
        group = next(
            (group for group in self._groups if group["key"] == group_key), None,
        )
        if group is None or not group.get("enabled", True):
            return
        option = next(
            (option for option in group.get("options", ())
             if option["key"] == value), None,
        )
        if option is None:
            return
        values = set(self._standard_selections.get(group_key, ()))
        if selected:
            # The model already excludes values outside this user's authority.
            # Selecting an available value restores it, never hides its chip.
            option["enabled"] = True
            values.add(value)
        else:
            values.discard(value)
        if values:
            self._standard_selections[group_key] = sorted(values)
        else:
            self._standard_selections.pop(group_key, None)
        self.stateChanged.emit()

    @Slot(int, int)
    def move_group(self, row: int, offset: int) -> None:
        target = row + (-1 if offset < 0 else 1)
        if (
                not self.canEdit or self.busy or not 0 <= row < len(self._groups)
                or not 0 <= target < len(self._groups)):
            return
        self._groups[row], self._groups[target] = (
            self._groups[target], self._groups[row]
        )
        self.stateChanged.emit()

    @Slot()
    def discard(self) -> None:
        self._session_open = False
        self._groups = deepcopy(self._original_groups)
        self._standard_selections = deepcopy(
            self._original_standard_selections
        )
        self.stateChanged.emit()

    @Slot()
    def use_current_as_standard(self) -> None:
        if not self.canEdit or self.busy:
            return
        current = self._context().get("selections") or {}
        self._standard_selections = {
            str(key): sorted({
                str(value) for value in values if str(value or "")
            })
            for key, values in current.items()
            if str(key or "") and isinstance(values, (list, tuple, set))
        }
        # Reuse the serialization path as the single policy sanitizer.
        self._standard_selections = self._configuration_from_groups()[
            "defaultSelections"
        ]
        self.stateChanged.emit()

    @Slot()
    def clear_standard(self) -> None:
        if not self.canEdit or self.busy:
            return
        self._standard_selections = {}
        self.stateChanged.emit()

    @Slot(str, str)
    def remove_standard_selection(self, group_key: str, value: str) -> None:
        if not self.canEdit or self.busy:
            return
        values = self._standard_selections.get(group_key, [])
        if value not in values:
            return
        remaining = [item for item in values if item != value]
        if remaining:
            self._standard_selections[group_key] = remaining
        else:
            del self._standard_selections[group_key]
        self.stateChanged.emit()

    @Slot()
    def save(self) -> None:
        if not self.canEdit or self.busy:
            return
        try:
            self._application.save_quick_filter_layout(
                self._tab_id, self._configuration_from_groups(),
            )
        except ValueError as error:
            self._set_busy(False, str(error))
            return
        self._rebuild(self._context())
        self._application._notify(self.tr("Quick filters saved for this tab"))

    @Slot()
    def save_defaults(self) -> None:
        if not self.canSaveDefaults or not self.canEdit or self.busy:
            return
        context = self._context(include_groups=False)
        if (self._key(context) != self._context_key
                or context.get("tab_id") != self._tab_id):
            self._set_busy(False, self.tr(
                "The search tab changed. Reopen the filter editor."
            ))
            return
        key = self._context_key
        self._success_message = self.tr("Shared default saved on the server for all users")
        configuration = self._configuration_from_groups()
        view = self._configuration_view(key[2])
        config_xml = self._configuration_xml(configuration, view)

        def operation():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=key[0])
            record = self._query_global_record(server, key, ["code"])
            data = {
                "view": view,
                "login": "",
                "category": self._category,
                "search_type": key[1],
                "title": "Quick filters",
                "config": config_xml,
            }
            if record.get("code"):
                search_key = server.build_search_key(
                    "config/widget_config", record["code"],
                    project_code=key[0],
                )
                server.insert_update(search_key, data, triggers=True)
                code = str(record["code"])
            else:
                created = server.insert(
                    "config/widget_config", data, triggers=True
                ) or {}
                code = str(created.get("code") or "")
            saved = self._query_global_record(server, key, ["code", "config"])
            restored = self._configuration_from_xml(
                str(saved.get("config") or ""), view,
            )
            if not saved or restored != configuration:
                raise RuntimeError(self.tr(
                    "The server did not retain the quick-filter standard. Reload and try again."
                ))
            return key, str(saved.get("code") or code), restored

        self._loading_keys.add(key)
        self._run(operation, self._saved, loading_key=key)

    def _run(self, callback, handler, *, loading_key=None) -> None:
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(callback)
            if worker is None:
                raise RuntimeError(self.tr("Server worker is unavailable"))
            self._workers.add(worker)
            worker.result.connect(handler)
            worker.error.connect(self._failed)

            def release():
                self._workers.discard(worker)
                if loading_key is not None:
                    self._loading_keys.discard(loading_key)
                self._set_busy(bool(self._workers), self._error)
                if loading_key in self._reload_pending:
                    self._reload_pending.discard(loading_key)
                    self._loaded.pop(loading_key, None)
                    self.ensure_current()

            worker.finished.connect(release)
            self._set_busy(True)
            worker.start()
        except Exception as error:
            if loading_key is not None:
                self._loading_keys.discard(loading_key)
            self._set_busy(False, str(error))

    @Slot(object)
    def _loaded_result(self, payload) -> None:
        key, code, configuration = payload
        if key in self._reload_pending:
            return
        self._loaded[key] = configuration
        self._record_codes[key] = code
        if self._key(self._context(include_groups=False)) == key:
            self._application.apply_quick_filter_configuration(
                key[2], configuration
            )
        if key == self._context_key and self._session_open:
            self._rebuild(self._context(), preserve_draft=self.dirty)
        elif self._session_open:
            self.stateChanged.emit()

    @Slot(object)
    def _saved(self, payload) -> None:
        key, code, configuration = payload
        self._loaded[key] = configuration
        self._record_codes[key] = code
        if self._key(self._context(include_groups=False)) == key:
            self._application.apply_quick_filter_configuration(
                key[2], configuration
            )
        if key == self._context_key:
            # Publishing must not replace the draft with a pre-existing local
            # override: the supervisor may still save this same draft locally.
            self._rebuild(self._context(), preserve_draft=True)
        else:
            self.stateChanged.emit()
        self._application._notify(
            self._success_message
            or self.tr("Shared default saved on the server for all users")
        )
        self._success_message = ""

    @Slot(str, str)
    def _project_changed(self, _project_code: str, _title: str) -> None:
        self._application.clear_quick_filter_configurations()
        self._context_key = ("", "", "")
        self._context_title = ""
        self._groups = []
        self._original_groups = []
        self._original_configuration = {}
        self._standard_selections = {}
        self._original_standard_selections = {}
        self.stateChanged.emit()

    @Slot(object)
    def apply_server_batch(self, batch) -> None:
        records = [
            *list((batch or {}).get("cacheChanges") or []),
            *list((batch or {}).get("cacheRetired") or []),
        ]
        affected_projects = {
            str(record.get("projectCode") or "")
            for record in records
            if str(record.get("searchType") or "").split("?", 1)[0]
            == "config/widget_config"
        }
        if not affected_projects:
            return
        self._reload_pending.update(
            key for key in self._loading_keys
            if "" in affected_projects or key[0] in affected_projects
        )
        for key in tuple(self._loaded):
            if "" in affected_projects or key[0] in affected_projects:
                self._loaded.pop(key, None)
                self._record_codes.pop(key, None)
        self.ensure_current()

    @Slot(object)
    def _failed(self, error) -> None:
        payload, worker = error
        self._workers.discard(worker)
        message = str(payload.get("exception") or error)
        trace = str(payload.get("traceback") or traceback.format_exc())
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            try:
                debug_log.log(
                    "ERROR", message,
                    group="search/quick_filters",
                    source="QuickFilterEditorController",
                    stacktrace=trace,
                    caller=2,
                )
            except (AttributeError, TypeError):
                pass
        self._success_message = ""
        self._set_busy(bool(self._workers), message)
