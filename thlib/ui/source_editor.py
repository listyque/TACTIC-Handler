"""A private document service for the existing house source editor control."""
from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import qmlRegisterType
from .script_editor import ScriptEditorController


class SourceEditorService(QObject):
    # Qt slots must belong to this QObject's meta-object, not be aliased from another class.
    @Slot(QObject, "QVariantMap")
    def attach_editor_document(self, document, colors=None):
        ScriptEditorController.attach_editor_document(self, document, colors)

    @Slot(str, str, "QVariantMap")
    def update_editor_highlights(self, selected, search, options=None):
        ScriptEditorController.update_editor_highlights(self, selected, search, options)

    @Slot(str, int, bool, result="QVariantList")
    def code_completions(self, source, cursor, manual=False):
        return ScriptEditorController.code_completions(self, source, cursor, manual)

    @Slot(str, result="QVariantList")
    def code_symbols(self, source):
        return ScriptEditorController.code_symbols(self, source)

    @Slot(str, str, "QVariantMap", result="QVariantList")
    def search_matches(self, source, query, options=None):
        return ScriptEditorController.search_matches(self, source, query, options)

    @Slot(str, str, int, int, result="QVariantMap")
    def apply_editor_command(self, action, source, start, end):
        return ScriptEditorController.apply_editor_command(self, action, source, start, end)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._syntax_highlighter = None


qmlRegisterType(SourceEditorService, "TacticHandler.Code", 1, 0, "SourceEditorService")
