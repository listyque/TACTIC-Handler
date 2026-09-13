from __future__ import annotations

from copy import deepcopy
import json
import uuid

from PySide6.QtCore import QObject, Property, Signal, Slot

from thlib.environment import env_read_config, env_write_config
from .workspace_models.records import RecordListModel


DEFAULT_TEMPLATES = (
    (True, "$FILENAME"),
    (True, "$FILENAME.$EXT"),
    (True, "$FILENAME.$FRAME.$EXT"),
    (True, "$FILENAME_$UDIM.$EXT"),
    (True, "$FILENAME_$UV.$EXT"),
    (True, "$FILENAME.$FRAME_$UDIM.$EXT"),
    (True, "$FILENAME.$FRAME_$UV.$EXT"),
    (True, "$FILENAME_$UV.$FRAME.$EXT"),
    (False, "$FILENAME_$LAYER.$EXT"),
    (False, "$FILENAME.$LAYER.$EXT"),
    (False, "$FILENAME_$LAYER.$FRAME.$EXT"),
    (False, "$FILENAME.$LAYER.$FRAME.$EXT"),
    (False, "$FILENAME.$LAYER_$UV.$EXT"),
    (False, "$FILENAME.$LAYER.$FRAME_$UV.$EXT"),
    (False, "$FILENAME.$LAYER_$UV.$FRAME.$EXT"),
    (False, "$FILENAME.$LAYER_$UDIM.$EXT"),
    (False, "$FILENAME.$LAYER.$FRAME_$UDIM.$EXT"),
    (False, "$FILENAME.$LAYER_$UDIM.$FRAME.$EXT"),
    (False, "$FILENAME_$LAYER.$FRAME_$UDIM.$EXT"),
)


class MatchingTemplatesController(QObject):
    stateChanged = Signal()
    templatesChanged = Signal()

    _tokens = {
        "$FILENAME", "$EXT", "$FRAME", "$UDIM", "$UV", "$LAYER",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._settings = dict(env_read_config(
            filename="ui_matching_templates",
            unique_id="ui_main",
            long_abs_path=True,
        ) or {})
        self.model = RecordListModel((
            "templateId", "templateEnabled", "pattern", "preview", "matchingType",
            "process", "context", "locked", "selected", "priority",
            "validationError",
        ))
        self._selected_id = ""
        self._test_example = ""
        self._test_result = ""
        self._saved = self._load()
        self._working = deepcopy(self._saved)
        self._replace_model()

    @Property(int, notify=stateChanged)
    def selectedRow(self) -> int:
        return next((
            index for index, item in enumerate(self._working)
            if item["templateId"] == self._selected_id
        ), -1)

    @Property("QVariantMap", notify=stateChanged)
    def selectedTemplate(self) -> dict:
        row = self.selectedRow
        return dict(self.model._records[row]) if row >= 0 else {}

    @Property(str, notify=stateChanged)
    def testExample(self) -> str:
        return self._test_example

    @Property(str, notify=stateChanged)
    def testResult(self) -> str:
        return self._test_result

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return self._working != self._saved

    @staticmethod
    def _defaults() -> list[dict]:
        result = []
        for priority, (enabled, pattern) in enumerate(DEFAULT_TEMPLATES):
            result.append({
                "templateId": uuid.uuid4().hex,
                "enabled": enabled,
                "pattern": pattern,
                "process": "",
                "context": "",
                "locked": pattern in {"$FILENAME", "$FILENAME.$EXT"},
                "priority": priority,
            })
        return result

    def _load(self) -> list[dict]:
        raw = self._settings.get("matchingTemplates/items", "")
        if not raw:
            return self._defaults()
        try:
            values = json.loads(raw)
        except (TypeError, ValueError):
            return self._defaults()
        records = []
        for priority, source in enumerate(
            values if isinstance(values, list) else []
        ):
            if not isinstance(source, dict):
                continue
            pattern = str(source.get("pattern") or "")
            if not pattern:
                continue
            records.append({
                "templateId": str(
                    source.get("templateId") or uuid.uuid4().hex
                ),
                "enabled": bool(source.get("enabled", True)),
                "pattern": pattern,
                "process": str(source.get("process") or ""),
                "context": str(source.get("context") or ""),
                "locked": pattern in {"$FILENAME", "$FILENAME.$EXT"},
                "priority": priority,
            })
        mandatory = {"$FILENAME", "$FILENAME.$EXT"}
        present = {item["pattern"] for item in records}
        for pattern in mandatory - present:
            records.insert(0, {
                "templateId": uuid.uuid4().hex,
                "enabled": True,
                "pattern": pattern,
                "process": "",
                "context": "",
                "locked": True,
                "priority": 0,
            })
        return records or self._defaults()

    @classmethod
    def _pattern_info(cls, pattern: str) -> tuple[str, str, str]:
        pattern = str(pattern or "").strip()
        if not pattern:
            return "", "", "Pattern is required"
        if "$FILENAME" not in pattern:
            return "", "", "Pattern must contain $FILENAME"
        import re
        tokens = set(re.findall(r"\$[A-Z]+\b", pattern))
        unsupported = sorted(tokens - cls._tokens)
        if unsupported:
            return "", "", f"Unsupported token: {unsupported[0]}"
        try:
            import thlib.global_functions as gf
            matcher = gf.MatchTemplate(
                [pattern], padding=cls._minimum_padding()
            )
            return (
                matcher.get_preview_string(),
                matcher.get_type_string(),
                "",
            )
        except (AttributeError, IndexError, TypeError, ValueError) as error:
            return "", "", str(error or "Invalid pattern")

    @staticmethod
    def _minimum_padding() -> int:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            value = gf.get_value_from_config(
                cfg_controls.get_checkin() or {},
                "minFramesPaddingSpinBox", 3,
            )
            return max(1, min(9, int(value)))
        except (AttributeError, TypeError, ValueError):
            return 3

    def _replace_model(self) -> None:
        records = []
        for priority, source in enumerate(self._working):
            source["priority"] = priority
            preview, matching_type, error = self._pattern_info(
                source["pattern"]
            )
            record = dict(source)
            record["templateEnabled"] = record.pop("enabled")
            record.update({
                "preview": preview,
                "matchingType": matching_type,
                "validationError": error,
                "selected": source["templateId"] == self._selected_id,
            })
            records.append(record)
        self.model.replace(records)
        self.stateChanged.emit()

    @Slot()
    def begin_edit(self) -> None:
        self._working = deepcopy(self._saved)
        if not any(
            item["templateId"] == self._selected_id
            for item in self._working
        ):
            self._selected_id = (
                self._working[0]["templateId"] if self._working else ""
            )
        self._test_result = ""
        self._replace_model()

    @Slot(int)
    def select_row(self, row: int) -> None:
        if not 0 <= row < len(self._working):
            return
        self._selected_id = self._working[row]["templateId"]
        self._replace_model()

    @Slot()
    def create_template(self) -> None:
        template_id = uuid.uuid4().hex
        self._working.append({
            "templateId": template_id,
            "enabled": True,
            "pattern": "$FILENAME.$EXT",
            "process": "",
            "context": "",
            "locked": False,
            "priority": len(self._working),
        })
        self._selected_id = template_id
        self._replace_model()

    @Slot()
    def duplicate_selected(self) -> None:
        row = self.selectedRow
        if row < 0:
            return
        record = dict(self._working[row])
        record["templateId"] = uuid.uuid4().hex
        record["locked"] = False
        self._working.insert(row + 1, record)
        self._selected_id = record["templateId"]
        self._replace_model()

    @Slot()
    def delete_selected(self) -> None:
        row = self.selectedRow
        if row < 0 or self._working[row].get("locked"):
            return
        self._working.pop(row)
        next_row = min(row, len(self._working) - 1)
        self._selected_id = (
            self._working[next_row]["templateId"] if next_row >= 0 else ""
        )
        self._replace_model()

    @Slot(int)
    def move_selected(self, offset: int) -> None:
        row = self.selectedRow
        target = row + int(offset)
        if row < 0 or not 0 <= target < len(self._working):
            return
        self._working.insert(target, self._working.pop(row))
        self._replace_model()

    @Slot(str, "QVariant")
    def update_selected(self, field: str, value) -> None:
        if field not in {"enabled", "pattern", "process", "context"}:
            return
        row = self.selectedRow
        if row < 0:
            return
        record = self._working[row]
        if field == "enabled":
            value = bool(value)
            if record.get("locked") and not value:
                return
        else:
            value = str(value or "").strip()
        if record.get(field) == value:
            return
        record[field] = value
        self._replace_model()

    @Slot(str)
    def test_pattern(self, example: str) -> None:
        self._test_example = str(example or "").strip()
        row = self.selectedRow
        if row < 0 or not self._test_example:
            self._test_result = "Enter a filename to test"
            self.stateChanged.emit()
            return
        pattern = self._working[row]["pattern"]
        _preview, _type, error = self._pattern_info(pattern)
        if error:
            self._test_result = error
            self.stateChanged.emit()
            return
        import thlib.global_functions as gf
        matches = list(
            gf.MatchTemplate(
                [pattern], padding=self._minimum_padding()
            ).get_files(
                [self._test_example]
            )
        )
        self._test_result = (
            f"Matched as {matches[0][1]['type']}"
            if matches else "No match"
        )
        self.stateChanged.emit()

    @Slot(result=bool)
    def save(self) -> bool:
        errors = [
            self._pattern_info(item["pattern"])[2]
            for item in self._working if item.get("enabled")
        ]
        if any(errors):
            self._test_result = next(error for error in errors if error)
            self.stateChanged.emit()
            return False
        self._saved = deepcopy(self._working)
        self._settings["matchingTemplates/items"] = json.dumps(
            self._saved, ensure_ascii=False
        )
        env_write_config(
            self._settings,
            filename="ui_matching_templates",
            unique_id="ui_main",
            long_abs_path=True,
        )
        self.templatesChanged.emit()
        self._replace_model()
        return True

    @Slot()
    def cancel(self) -> None:
        self._working = deepcopy(self._saved)
        self._replace_model()

    def active_patterns(self, process: str, context: str) -> list[str]:
        patterns = []
        for item in self._saved:
            if not item.get("enabled"):
                continue
            process_filter = str(item.get("process") or "")
            context_filter = str(item.get("context") or "")
            if process_filter and process_filter != process:
                continue
            if context_filter and context_filter != context:
                continue
            patterns.append(item["pattern"])
        return patterns
