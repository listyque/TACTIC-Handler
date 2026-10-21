"""Qt counterparts for the independently shipped Frame table widget catalogue."""

import json
from pathlib import Path
from thlib.tactic_widgets import TacticBaseWidget


class TacticBaseTableWidget(TacticBaseWidget):
    cell_kind = "text"

    def get_cell_kind(self, data_type="text"):
        if self.cell_kind == "text" and str(data_type or "").lower() in {
            "bool",
            "boolean",
        }:
            return "boolean"
        return self.cell_kind

    def map_cell(self, source, data_type="text"):
        cell = dict(source or {})
        cell["kind"] = self.get_cell_kind(data_type)
        cell.setdefault("text", "")
        cell.setdefault("error", "")
        return cell


class TacticSimpleTableWidget(TacticBaseTableWidget):
    pass


class TacticRawTableWidget(TacticBaseTableWidget):
    pass


class TacticFormatTableWidget(TacticBaseTableWidget):
    def get_cell_kind(self, data_type="text"):
        if self.options_dict.get("displayOptions", {}).get("format") == "Checkbox":
            return "boolean"
        return super().get_cell_kind(data_type)


class TacticExpressionTableWidget(TacticBaseTableWidget):
    def get_cell_kind(self, data_type="text"):
        mode = self.options_dict.get("displayOptions", {}).get("mode")
        return (
            mode if mode in ("boolean", "check") else super().get_cell_kind(data_type)
        )


class TacticLinkTableWidget(TacticBaseTableWidget):
    cell_kind = "link"

    def map_cell(self, source, data_type="text"):
        cell = super().map_cell(source, data_type)
        cell["href"] = str(cell.get("href") or cell["text"])
        return cell


class TacticThumbTableWidget(TacticBaseTableWidget):
    cell_kind = "thumbnail"


class TacticNotesTableWidget(TacticBaseTableWidget):
    cell_kind = "notes"


class TacticSObjectDetailTableWidget(TacticBaseTableWidget):
    cell_kind = "sobject_detail"


class TacticCheckinTableWidget(TacticBaseTableWidget):
    cell_kind = "checkin"


class TacticTaskTableWidget(TacticBaseTableWidget):
    cell_kind = "tasks"

    def map_cell(self, source, data_type="text"):
        cell = super().map_cell(source, data_type)
        if "tasks" not in cell:
            cell["tasks"] = [
                {
                    "context": parts[0],
                    "process": parts[0].split("/", 1)[0],
                    "status": parts[1],
                    "assigned": parts[2],
                }
                for value in str(cell["text"] or "").split(",")
                if value
                for parts in [value.split(":", 2)]
                if len(parts) == 3
            ]
        return cell


class TacticCompletionTableWidget(TacticBaseTableWidget):
    cell_kind = "completion"

    def map_cell(self, source, data_type="text"):
        cell = super().map_cell(source, data_type)
        try:
            percent = float(str(cell["text"]).strip().rstrip("%"))
        except (TypeError, ValueError):
            percent = 0.0
        cell["percent"] = max(0.0, min(100.0, percent))
        return cell


class TacticExplorerTableWidget(TacticBaseTableWidget):
    cell_kind = "explorer"


class TacticFileListTableWidget(TacticBaseTableWidget):
    cell_kind = "file_list"


class TacticMetadataTableWidget(TacticBaseTableWidget):
    cell_kind = "metadata"


class TacticStructuredTableWidget(TacticBaseTableWidget):
    cell_kind = "structured"

    def get_cell_kind(self, data_type="text"):
        return self.cell_kind


class TacticDeleteTableWidget(TacticBaseTableWidget):
    cell_kind = "delete"


class TacticLockedTableWidget(TacticBaseTableWidget):
    cell_kind = "locked"


class TacticGroupedCompletionTableWidget(TacticBaseTableWidget):
    cell_kind = "group_completion"


class TacticSelectionTableWidget(TacticBaseTableWidget):
    cell_kind = "selection"


class TacticTaskSummaryTableWidget(TacticTaskTableWidget):
    cell_kind = "task_summary"


class TacticFieldsTableWidget(TacticBaseTableWidget):
    cell_kind = "fields"


class TacticStatusFlagTableWidget(TacticBaseTableWidget):
    cell_kind = "status_flag"


class TacticMessageTableWidget(TacticBaseTableWidget):
    cell_kind = "message"


class TacticCommandsTableWidget(TacticBaseTableWidget):
    cell_kind = "commands"


class TacticUnsupportedTableWidget(TacticBaseTableWidget):
    cell_kind = "unsupported"

    def get_cell_kind(self, data_type="text"):
        return self.cell_kind


_adapters = {
    "commands": TacticCommandsTableWidget,
    "value": TacticSimpleTableWidget,
    "raw": TacticRawTableWidget,
    "formatted": TacticFormatTableWidget,
    "expression": TacticExpressionTableWidget,
    "link": TacticLinkTableWidget,
    "preview": TacticThumbTableWidget,
    "notes": TacticNotesTableWidget,
    "message": TacticMessageTableWidget,
    "details": TacticSObjectDetailTableWidget,
    "checkin": TacticCheckinTableWidget,
    "tasks": TacticTaskTableWidget,
    "completion": TacticCompletionTableWidget,
    "explorer": TacticExplorerTableWidget,
    "files": TacticFileListTableWidget,
    "metadata": TacticMetadataTableWidget,
    "structured": TacticStructuredTableWidget,
    "delete": TacticDeleteTableWidget,
    "lock": TacticLockedTableWidget,
    "groupCompletion": TacticGroupedCompletionTableWidget,
    "selection": TacticSelectionTableWidget,
    "taskSummary": TacticTaskSummaryTableWidget,
    "fields": TacticFieldsTableWidget,
    "flag": TacticStatusFlagTableWidget,
}
_catalog = json.loads(
    (
        Path(__file__).parent / "ui/qml/tactic_frame/features/table/widgets.json"
    ).read_text(encoding="utf-8")
)
_table_widget_classes = {
    alias: _adapters[entry["adapter"]]
    for entry in _catalog
    for alias in entry["aliases"]
    if alias
}
table_classes = {
    "tactic": list(_table_widget_classes),
    "handler": [widget.__name__ for widget in _table_widget_classes.values()],
}


def get_widget_class(tactic_class=""):
    return _table_widget_classes.get(tactic_class)


def create_widget(options_dict=None):
    options = dict(options_dict or {})
    class_name = str(options.get("resolvedClass") or options.get("displayClass") or "")
    widget_class = get_widget_class(class_name) or (
        TacticUnsupportedTableWidget if class_name else TacticBaseTableWidget
    )
    if widget_class is not TacticUnsupportedTableWidget and options.get("actionClass") in (
        "ParentGroupAction", "tactic.ui.table.ParentGroupAction",
        "tactic.ui.table.group_element_wdg.ParentGroupAction",
    ) and not options.get("actionOptions"):
        widget_class = TacticCommandsTableWidget
    widget = widget_class(options)
    widget.set_class_name(class_name)
    return widget
