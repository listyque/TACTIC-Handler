"""Qt-facing counterparts for TACTIC table display widgets."""

from thlib.tactic_widgets import TacticBaseWidget


class TacticBaseTableWidget(TacticBaseWidget):
    cell_kind = "text"

    def get_cell_kind(self, data_type="text"):
        if str(data_type or "").lower() in {"bool", "boolean"}:
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
    pass


class TacticExpressionTableWidget(TacticBaseTableWidget):
    pass


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
                for value in str(cell["text"] or "").split(",") if value
                for parts in [value.split(":", 2)] if len(parts) == 3
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


class TacticDeleteTableWidget(TacticBaseTableWidget):
    cell_kind = "delete"


table_classes = {
    "tactic": [
        "tactic.ui.common.SimpleTableElementWdg",
        "tactic.ui.common.base_table_element_wdg.SimpleTableElementWdg",
        "tactic.ui.common.RawTableElementWdg",
        "tactic.ui.common.base_table_element_wdg.RawTableElementWdg",
        "tactic.ui.table.FormatElementWdg",
        "tactic.ui.table.format_element_wdg.FormatElementWdg",
        "tactic.ui.table.ExpressionElementWdg",
        "tactic.ui.table.expression_element_wdg.ExpressionElementWdg",
        "tactic.ui.table.ExpressionValueElementWdg",
        "tactic.ui.table.expression_element_wdg.ExpressionValueElementWdg",
        "tactic.ui.table.LinkElementWdg",
        "tactic.ui.table.link_element_wdg.LinkElementWdg",
        "ThumbWdg",
        "pyasm.widget.ThumbWdg",
        "pyasm.widget.file_wdg.ThumbWdg",
        "tactic.ui.widget.DiscussionElementWdg",
        "tactic.ui.widget.discussion_wdg.DiscussionElementWdg",
        "tactic.ui.table.SObjectDetailElementWdg",
        "tactic.ui.table.sobject_detail_wdg.SObjectDetailElementWdg",
        "tactic.ui.table.CheckinButtonElementWdg",
        "tactic.ui.table.table_element_wdg.CheckinButtonElementWdg",
        "tactic.ui.table.TaskElementWdg",
        "tactic.ui.table.task_element_wdg.TaskElementWdg",
        "tactic.ui.table.TaskCompletionWdg",
        "tactic.ui.table.statistic_wdg.TaskCompletionWdg",
        "tactic.ui.table.ExploreElementWdg",
        "tactic.ui.table.ExplorerElementWdg",
        "tactic.ui.table.ExplorerTableElementWdg",
        "tactic.ui.table.explorer_wdg.ExplorerElementWdg",
        "tactic.ui.table.SObjectFilesElementWdg",
        "tactic.ui.table.sobject_summary_wdg.SObjectFilesElementWdg",
        "tactic.ui.table.MetadataElementWdg",
        "tactic.ui.table.metadata_element_wdg.MetadataElementWdg",
        "tactic.ui.table.DeleteElementWdg",
        "tactic.ui.table.delete_element_wdg.DeleteElementWdg",
    ],
    "handler": [
        TacticSimpleTableWidget,
        TacticSimpleTableWidget,
        TacticRawTableWidget,
        TacticRawTableWidget,
        TacticFormatTableWidget,
        TacticFormatTableWidget,
        TacticExpressionTableWidget,
        TacticExpressionTableWidget,
        TacticExpressionTableWidget,
        TacticExpressionTableWidget,
        TacticLinkTableWidget,
        TacticLinkTableWidget,
        TacticThumbTableWidget,
        TacticThumbTableWidget,
        TacticThumbTableWidget,
        TacticNotesTableWidget,
        TacticNotesTableWidget,
        TacticSObjectDetailTableWidget,
        TacticSObjectDetailTableWidget,
        TacticCheckinTableWidget,
        TacticCheckinTableWidget,
        TacticTaskTableWidget,
        TacticTaskTableWidget,
        TacticCompletionTableWidget,
        TacticCompletionTableWidget,
        TacticExplorerTableWidget,
        TacticExplorerTableWidget,
        TacticExplorerTableWidget,
        TacticExplorerTableWidget,
        TacticFileListTableWidget,
        TacticFileListTableWidget,
        TacticMetadataTableWidget,
        TacticMetadataTableWidget,
        TacticDeleteTableWidget,
        TacticDeleteTableWidget,
    ],
}

_table_widget_classes = dict(zip(
    table_classes["tactic"], table_classes["handler"]
))


def get_widget_class(tactic_class=""):
    return _table_widget_classes.get(tactic_class)


def create_widget(options_dict=None):
    options = dict(options_dict or {})
    class_name = str(
        options.get("resolvedClass") or options.get("displayClass") or ""
    )
    widget_class = get_widget_class(class_name) or TacticBaseTableWidget
    widget = widget_class(options)
    widget.set_class_name(class_name)
    return widget
