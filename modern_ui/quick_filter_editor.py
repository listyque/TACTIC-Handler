from __future__ import annotations

from copy import deepcopy
import json
import traceback
from xml.etree import ElementTree

from PySide6.QtCore import QObject, Property, Signal, Slot


class QuickFilterEditorController(QObject):
    """Project-wide quick-filter configuration backed by widget_config."""

    stateChanged = Signal()

    _category = "quick_filters"
    _view = "modern_quick_filters"

    def __init__(self, application, users, parent=None) -> None:
        super().__init__(parent)
        self._application = application
        self._users = users
        self._groups: list[dict] = []
        self._original_groups: list[dict] = []
        self._context_key: tuple[str, str] = ("", "")
        self._context_title = ""
        self._busy = False
        self._error = ""
        self._workers = set()
        self._loaded: dict[tuple[str, str], dict] = {}
        self._record_codes: dict[tuple[str, str], str] = {}
        try:
            users.stateChanged.connect(self.stateChanged.emit)
        except (AttributeError, TypeError):
            pass

    def _context(self) -> dict:
        return dict(self._application.quick_filter_editor_context() or {})

    @staticmethod
    def _key(context) -> tuple[str, str]:
        return (
            str(context.get("project_code") or ""),
            str(context.get("search_type") or ""),
        )

    @Property(bool, notify=stateChanged)
    def canEdit(self) -> bool:
        try:
            return bool(self._users.canManageUsers)
        except (AttributeError, RuntimeError):
            return False

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return self._groups != self._original_groups

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(str, notify=stateChanged)
    def contextTitle(self) -> str:
        return self._context_title

    @Property("QVariantList", notify=stateChanged)
    def groups(self) -> list[dict]:
        return deepcopy(self._groups)

    def _set_busy(self, value: bool, error: str = "") -> None:
        self._busy = bool(value)
        self._error = str(error or "")
        self.stateChanged.emit()

    @staticmethod
    def _configuration_from_xml(value: str) -> dict:
        if not str(value or "").strip():
            return {}
        root = ElementTree.fromstring(value)
        element = root.find("./quick_filters/values")
        if element is None or not str(element.text or "").strip():
            return {}
        result = json.loads(element.text)
        if not isinstance(result, dict) or not isinstance(
                result.get("groups", []), list):
            return {}
        return result

    @staticmethod
    def _configuration_xml(configuration: dict) -> str:
        root = ElementTree.Element("config")
        quick_filters = ElementTree.SubElement(root, "quick_filters")
        values = ElementTree.SubElement(
            quick_filters, "values", {"type": "json"}
        )
        values.text = json.dumps(
            configuration, ensure_ascii=False, separators=(",", ":")
        )
        return ElementTree.tostring(root, encoding="unicode")

    def _configuration_from_groups(self) -> dict:
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
            groups.append(record)
        return {"version": 1, "groups": groups}

    def _rebuild(self, context: dict) -> None:
        self._context_key = self._key(context)
        self._context_title = str(context.get("title") or "")
        self._groups = deepcopy(context.get("groups") or [])
        self._original_groups = deepcopy(self._groups)
        self.stateChanged.emit()

    @Slot()
    def ensure_current(self) -> None:
        context = self._context()
        key = self._key(context)
        if not all(key):
            return
        self._context_key = key
        if key in self._loaded:
            self._application.apply_quick_filter_configuration(
                key[1], self._loaded[key]
            )
            return

        def query():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=key[0])
            record = server.query(
                "config/widget_config",
                [
                    ("view", self._view),
                    ("search_type", key[1]),
                    ("category", self._category),
                ],
                ["code", "config"],
                single=True,
            ) or {}
            try:
                configuration = self._configuration_from_xml(
                    str(record.get("config") or "")
                )
            except (ElementTree.ParseError, json.JSONDecodeError, TypeError):
                configuration = {}
            return key, str(record.get("code") or ""), configuration

        self._run(query, self._loaded_result)

    @Slot()
    def begin_session(self) -> None:
        self.ensure_current()
        self._rebuild(self._context())

    @Slot(int, bool)
    def set_group_enabled(self, row: int, enabled: bool) -> None:
        if not self.canEdit or not 0 <= row < len(self._groups):
            return
        self._groups[row]["enabled"] = bool(enabled)
        self.stateChanged.emit()

    @Slot(int, int, bool)
    def set_option_enabled(
            self, group_row: int, option_row: int, enabled: bool
    ) -> None:
        if not self.canEdit or not 0 <= group_row < len(self._groups):
            return
        options = self._groups[group_row].get("options") or []
        if not 0 <= option_row < len(options):
            return
        options[option_row]["enabled"] = bool(enabled)
        self.stateChanged.emit()

    @Slot(int, int)
    def move_group(self, row: int, offset: int) -> None:
        target = row + (-1 if offset < 0 else 1)
        if (
                not self.canEdit or not 0 <= row < len(self._groups)
                or not 0 <= target < len(self._groups)):
            return
        self._groups[row], self._groups[target] = (
            self._groups[target], self._groups[row]
        )
        self.stateChanged.emit()

    @Slot()
    def discard(self) -> None:
        self._groups = deepcopy(self._original_groups)
        self.stateChanged.emit()

    @Slot()
    def save(self) -> None:
        if not self.canEdit or self._busy or not all(self._context_key):
            return
        key = self._context_key
        configuration = self._configuration_from_groups()
        config_xml = self._configuration_xml(configuration)

        def operation():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=key[0])
            record = server.query(
                "config/widget_config",
                [
                    ("view", self._view),
                    ("search_type", key[1]),
                    ("category", self._category),
                ],
                ["code"],
                single=True,
            ) or {}
            data = {
                "view": self._view,
                "login": "",
                "category": self._category,
                "search_type": key[1],
                "title": "Modern quick filters",
                "config": config_xml,
            }
            if record.get("code"):
                search_key = server.build_search_key(
                    "config/widget_config", record["code"],
                    project_code=key[0],
                )
                server.insert_update(search_key, data, triggers=False)
                code = str(record["code"])
            else:
                created = server.insert(
                    "config/widget_config", data, triggers=False
                ) or {}
                code = str(created.get("code") or "")
            return key, code, configuration

        self._run(operation, self._saved)

    @Slot()
    def reset_defaults(self) -> None:
        if not self.canEdit or self._busy or not all(self._context_key):
            return
        key = self._context_key

        def operation():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=key[0])
            record = server.query(
                "config/widget_config",
                [
                    ("view", self._view),
                    ("search_type", key[1]),
                    ("category", self._category),
                ],
                ["code"],
                single=True,
            ) or {}
            search_key = ""
            if record.get("code"):
                search_key = server.build_search_key(
                    "config/widget_config", record["code"],
                    project_code=key[0],
                )
            if search_key:
                server.delete_sobject(search_key)
            return key, "", {}

        self._run(operation, self._saved)

    def _run(self, callback, handler) -> None:
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(callback)
            self._workers.add(worker)
            worker.result.connect(handler)
            worker.error.connect(self._failed)
            worker.finished.connect(lambda: self._workers.discard(worker))
            worker.start()
            self._set_busy(True)
        except Exception as error:
            self._set_busy(False, str(error))

    @Slot(object)
    def _loaded_result(self, payload) -> None:
        key, code, configuration = payload
        self._loaded[key] = configuration
        self._record_codes[key] = code
        self._application.apply_quick_filter_configuration(
            key[1], configuration
        )
        self._set_busy(False)
        if key == self._context_key:
            self._rebuild(self._context())

    @Slot(object)
    def _saved(self, payload) -> None:
        key, code, configuration = payload
        self._loaded[key] = configuration
        self._record_codes[key] = code
        self._application.apply_quick_filter_configuration(
            key[1], configuration
        )
        self._set_busy(False)
        if key == self._context_key:
            self._rebuild(self._context())

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
        self._set_busy(False, message)
