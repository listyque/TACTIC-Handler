"""Isolated preview scopes reuse the normal native layout/table/item renderers."""

import copy
from PySide6.QtCore import QObject, Property
from ..table.services import TableServicesController
from ..layout_editor import LayoutEditorHost


class PagePreview(QObject):
    def __init__(self, application, parent=None):
        super().__init__(parent)
        self._application = application
        self._services = TableServicesController(application, self, document_window="")
        self._owner = self._services.customLayout
        self._items = LayoutEditorHost(application, self)
        self._item_scope = None

    @Property(QObject, constant=True)
    def services(self):
        return self._services

    @Property(QObject, constant=True)
    def owner(self):
        return self._owner

    @Property(QObject, constant=True)
    def items(self):
        return self._items

    def update(self, model, project):
        model = copy.deepcopy(model)

        def scope(nodes):
            for node in nodes:
                if node.get("table"):
                    node["table"]["projectCode"] = project
                scope(node.get("children") or [])

        scope(model.get("layoutNodes") or [])
        scope((model.get("layoutDetail") or {}).get("layoutNodes") or [])
        self._owner.close()
        self._owner.document_data = dict(model, nodeId="")
        self._owner.open(
            self._application._current_tab(),
            dict(
                project=project,
                searchKey=model["targetSearchKey"],
                record=model.get("layoutRecord") or {},
            ),
        )
        self._services.documentChanged.emit()
        self._owner._open_tables(
            (model.get("layoutDetail") or {}).get("layoutNodes") or [],
            "customLayoutDetails",
        )
        item_scope = model.get("layoutItems")
        if (project, item_scope) != self._item_scope:
            self._item_scope = (project, item_scope)
            if item_scope:
                self._items.preview_scope(
                    project,
                    item_scope["searchType"],
                    item_scope["view"],
                    item_scope.get("filters"),
                )
            else:
                self._items.reset()

    def shutdown(self):
        self._items.shutdown()
        self._services.shutdown()
