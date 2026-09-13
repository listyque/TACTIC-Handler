from __future__ import annotations

from copy import deepcopy
import traceback
from xml.etree import ElementTree

from PySide6.QtCore import QObject, Property, Signal, Slot

from . import tactic_definition
from .workspace_models.records import RecordListModel


class ColumnsEditorController(QObject):
    """Own the native TACTIC table projection and its DB view overrides."""

    stateChanged = Signal()
    cellRevisionChanged = Signal()
    applied = Signal()
    focusRequested = Signal()
    _protected = {"id", "code", "project_code", "timestamp", "login"}
    _internal = {
        "__search_key__", "__search_type__", "__tasks_count__",
        "__notes_count__", "__snapshots__",
    }
    def __init__(self, application, tasks_controller=None, parent=None):
        super().__init__(parent)
        self._application = application
        self._tasks_controller = tasks_controller
        self.model = RecordListModel((
            "name", "label", "dataType", "displayVisible", "displayWidth",
            "order", "readOnly", "widgetClass", "widgetKey", "cellKind",
            "resolvedClass", "sortable", "editable",
            "displayOptions", "displayXml", "editClass", "editWidget",
            "editOptions", "editXml", "editVisible", "actionClass",
            "actionOptions",
        ))
        self._source_records = []
        self._source_elements = {}
        self._unmanaged_elements = []
        self._definition_root = None
        self._definition_xml = ""
        self._database_views = {}
        self._definition_catalog = []
        self._definition_catalog_loaded = False
        self._definition_catalog_project = ""
        self._definition_catalog_project_object = None
        self._cells = {}
        self._cell_revision = 0
        self._table_widgets = {}
        self._data_types = {}
        self._row_worker = None
        self._row_request_id = 0
        self._row_sync_pending = False
        self._edit_sources = {}
        self._stype_code = ""
        self._title = "Columns"
        self._dirty = False
        self._busy = False
        self._error = ""
        self._workers = set()
        self._reload_pending = False
        self._requested_row = 0
        self._requested_name = ""
        self._requested_definition_target = "definition"
        application.selected_node_changed.connect(self._reload_if_in_use)
        application.project_changed.connect(self._reload_if_in_use)
        application.results_view_changed.connect(self._reload_table_if_active)
        search_state_changed = getattr(application, "search_state_changed", None)
        if search_state_changed is not None:
            search_state_changed.connect(self._sync_table_rows)

    @Property(str, notify=stateChanged)
    def title(self):
        return self._title

    @Property(bool, notify=stateChanged)
    def dirty(self):
        return self._dirty

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(str, notify=stateChanged)
    def definitionXml(self):
        return self._definition_xml

    @Property(str, notify=stateChanged)
    def searchType(self):
        return self._stype_code

    @Property("QVariantList", notify=stateChanged)
    def definitionCatalog(self):
        return [dict(record) for record in self._definition_catalog]

    @Property("QVariantList", notify=stateChanged)
    def definitionCatalogSearchTypes(self):
        values = {}
        try:
            stypes = (
                self._definition_catalog_project_object.get_stypes() or {}
            ).values()
            for stype in stypes:
                code = str(stype.get_code() or "")
                if not code:
                    continue
                title = str(stype.get_pretty_name() or code)
                values[code] = (
                    code if title == code else f"{code} ({title})"
                )
        except (AttributeError, TypeError):
            pass
        for record in self._definition_catalog:
            code = str(record.get("searchType") or "")
            if code:
                values.setdefault(code, code)
        return [
            {"value": code, "label": label}
            for code, label in sorted(
                values.items(), key=lambda item: item[1].lower()
            )
        ]

    @Property(bool, notify=stateChanged)
    def definitionCatalogLoaded(self):
        return self._definition_catalog_loaded

    @Property(bool, notify=stateChanged)
    def hasColumns(self):
        return bool(self.visibleColumns)

    @Property("QVariantList", constant=True)
    def inputWidgetOptions(self):
        from thlib.tactic_widgets import input_classes

        return [
            {
                "value": class_name,
                "label": self.tr(tactic_definition.INPUT_LABELS.get(
                    class_name.rsplit(".", 1)[-1],
                    class_name.rsplit(".", 1)[-1],
                )),
            }
            for class_name in input_classes["tactic"]
        ]

    @Property("QVariantList", constant=True)
    def displayWidgetOptions(self):
        return [
            {"value": value, "label": self.tr(label)}
            for value, label in tactic_definition.DISPLAY_WIDGETS
        ]

    @Property("QVariantList", notify=stateChanged)
    def visibleColumns(self):
        return [
            {
                "row": row,
                "name": record["name"],
                "label": record["label"],
                "width": record["displayWidth"],
                "kind": record["cellKind"],
                "dataType": record["dataType"],
                "sortable": record["sortable"],
                "editable": record["editable"],
                "displayOptions": dict(record["displayOptions"]),
            }
            for row, record in enumerate(self.model._records)
            if record["displayVisible"]
        ]

    @Property(int, notify=cellRevisionChanged)
    def cellRevision(self):
        return self._cell_revision

    def _current_tab(self):
        return self._application._current_tab()

    @Property(int, notify=focusRequested)
    def requestedRow(self):
        return self._requested_row

    @Property(str, notify=focusRequested)
    def requestedName(self):
        return self._requested_name

    @Property(str, notify=focusRequested)
    def requestedDefinitionTarget(self):
        return self._requested_definition_target

    def _current_stype(self):
        tab = self._current_tab()
        if tab and getattr(tab, "stype", None):
            return tab.stype
        node = self._application.workspace_model.node_for(
            self._application.selected_node_id
        )
        if node and node.source:
            try:
                return node.source.get_stype()
            except (AttributeError, TypeError):
                return None
        return None

    def _current_search_keys(self):
        tab = self._current_tab()
        return [
            str(sobject.get_search_key() or "")
            for sobject in (getattr(tab, "sobjects", None) or [])
            if sobject.get_search_key()
        ]

    def _reload_if_in_use(self, *_args):
        windows = getattr(self._application, "window_model", None)
        docks = getattr(self._application, "dock_model", None)
        if (
            windows and windows.is_window_visible("columns_editor")
            or docks and docks.is_panel_presented("db_table")
        ):
            self.reload()

    def _reload_table_if_active(self, *_args):
        tab = self._current_tab()
        if tab and getattr(tab, "view_mode", "") == "table":
            self.reload()

    @Slot()
    def begin_session(self):
        self.reload()

    @staticmethod
    def _definition_catalog_records(records, current_search_type):
        catalog = []
        current_base = str(current_search_type or "").split("?", 1)[0]
        for source_row, source in enumerate(records or []):
            if not isinstance(source, dict):
                continue
            search_type = str(source.get("search_type") or "")
            view = str(source.get("view") or "")
            if not search_type or not view:
                continue
            search_key = str(source.get("__search_key__") or "")
            code = str(source.get("code") or "")
            identity = search_key or code or "|".join((
                search_type, view, str(source.get("login") or ""),
                str(source.get("category") or ""), str(source_row),
            ))
            catalog.append({
                "identity": identity,
                "searchKey": search_key,
                "code": code,
                "searchType": search_type,
                "view": view,
                "login": str(source.get("login") or ""),
                "category": str(source.get("category") or ""),
                "widgetType": str(source.get("widget_type") or ""),
                "config": str(source.get("config") or ""),
                "current": search_type.split("?", 1)[0] == current_base,
            })
        catalog.sort(key=lambda record: (
            not record["current"], record["searchType"].lower(),
            record["view"].lower(), record["login"].lower(),
            record["code"].lower(),
        ))
        for row, record in enumerate(catalog):
            record["row"] = row
        return catalog

    def _set_definition_catalog(self, project_code, project, records):
        self._definition_catalog = self._definition_catalog_records(
            records, self._stype_code
        )
        self._definition_catalog_project = str(project_code or "")
        self._definition_catalog_project_object = project
        self._definition_catalog_loaded = True
        self._error = ""
        self.stateChanged.emit()

    @Slot()
    def load_definition_catalog(self):
        self._load_definition_catalog(False)

    @Slot()
    def reload_definition_catalog(self):
        self._load_definition_catalog(True)

    def _load_definition_catalog(self, force):
        stype = self._current_stype()
        if stype is None or self._busy:
            return
        project_code = str(self._application._current_project_code or "")
        if (
            not force and self._definition_catalog_loaded
            and self._definition_catalog_project == project_code
        ):
            return
        try:
            project = stype.get_project()
        except AttributeError:
            project = getattr(stype, "project", None)

        def operation():
            import thlib.tactic_classes as tc
            records = tc.server_start(project=project_code).query(
                "config/widget_config", []
            ) or []
            return project_code, project, records

        self._run(operation, self._definition_catalog_loaded_from_server)

    @Slot(object)
    def _definition_catalog_loaded_from_server(self, payload):
        project_code, project, records = payload
        if project_code != str(self._application._current_project_code or ""):
            return
        try:
            project.get_config_views().config_dict = [
                dict(record) for record in records
                if isinstance(record, dict)
            ]
        except AttributeError:
            pass
        self._set_definition_catalog(project_code, project, records)

    def _catalog_xml_node(self, root, path):
        node = root
        for part in str(path or "").split("/"):
            if not part:
                continue
            children = list(node)
            index = int(part)
            if not 0 <= index < len(children):
                raise ValueError(self.tr(
                    "Definition XML path no longer exists."
                ))
            node = children[index]
        return node

    @Slot(str, result="QVariantList")
    def catalog_simple_rows(self, xml):
        """Flatten any widget_config XML into editable visual rows."""
        try:
            source = str(xml or "").strip()
            root = (
                ElementTree.fromstring(source)
                if source else ElementTree.Element("config")
            )
        except ElementTree.ParseError as error:
            self._error = str(error)
            self.stateChanged.emit()
            return []

        rows = []

        def append_node(node, path, depth):
            rows.append({
                "kind": "element",
                "name": node.tag,
                "value": "",
                "path": path,
                "depth": depth,
                "detail": str(node.get("name") or node.get("class") or ""),
            })
            for name, value in node.attrib.items():
                rows.append({
                    "kind": "attribute",
                    "name": name,
                    "value": str(value),
                    "path": path,
                    "depth": depth + 1,
                    "detail": "",
                })
            children = list(node)
            if not children or str(node.text or "").strip():
                rows.append({
                    "kind": "text",
                    "name": "# text",
                    "value": str(node.text or "").strip(),
                    "path": path,
                    "depth": depth + 1,
                    "detail": "",
                })
            for index, child in enumerate(children):
                child_path = f"{path}/{index}" if path else str(index)
                append_node(child, child_path, depth + 1)

        append_node(root, "", 0)
        had_error = bool(self._error)
        self._error = ""
        if had_error:
            self.stateChanged.emit()
        return rows

    @Slot(str, str, str, str, str, result=str)
    def update_catalog_simple_value(self, xml, path, kind, name, value):
        try:
            source = str(xml or "").strip()
            root = (
                ElementTree.fromstring(source)
                if source else ElementTree.Element("config")
            )
            node = self._catalog_xml_node(root, path)
            if kind == "attribute":
                if name not in node.attrib:
                    raise ValueError(self.tr(
                        "Definition XML attribute no longer exists."
                    ))
                node.set(name, str(value or ""))
            elif kind == "text":
                node.text = str(value or "")
            else:
                raise ValueError(self.tr(
                    "Only XML values can be edited in Simple mode."
                ))
        except (ElementTree.ParseError, TypeError, ValueError) as error:
            self._error = str(error)
            self.stateChanged.emit()
            return ""
        had_error = bool(self._error)
        self._error = ""
        if had_error:
            self.stateChanged.emit()
        return ElementTree.tostring(root, encoding="unicode")

    @Slot(int, str, result=bool)
    def save_catalog_xml(self, row, xml):
        if self._busy or not 0 <= row < len(self._definition_catalog):
            return False
        xml = str(xml or "").strip()
        try:
            ElementTree.fromstring(xml)
        except ElementTree.ParseError as error:
            self._error = str(error)
            self.stateChanged.emit()
            return False
        record = dict(self._definition_catalog[row])
        if not record["searchKey"] and not record["code"]:
            self._error = self.tr(
                "The selected definition has no stable identity."
            )
            self.stateChanged.emit()
            return False
        project_code = self._definition_catalog_project

        def operation():
            import thlib.tactic_classes as tc
            server = tc.server_start(project=project_code)
            search_key = record["searchKey"] or server.build_search_key(
                "config/widget_config", record["code"],
                project_code=project_code,
            )
            server.insert_update(
                search_key, {"config": xml}, triggers=False
            )
            return {
                "identity": record["identity"],
                "code": record["code"],
                "searchKey": search_key,
                "config": xml,
            }

        self._run(operation, self._catalog_xml_saved)
        return True

    @Slot(object)
    def _catalog_xml_saved(self, payload):
        payload = dict(payload or {})
        identity = str(payload.get("identity") or "")
        xml = str(payload.get("config") or "")
        code = str(payload.get("code") or "")
        search_key = str(payload.get("searchKey") or "")
        for record in self._definition_catalog:
            if record["identity"] == identity:
                record["config"] = xml
                record["searchKey"] = search_key
                break
        project = self._definition_catalog_project_object
        try:
            records = project.get_config_views().config_dict
        except AttributeError:
            records = []
        for record in records or []:
            if (
                code and str(record.get("code") or "") == code
                or search_key and str(record.get("__search_key__") or "")
                == search_key
            ):
                record["config"] = xml
                record["__search_key__"] = search_key
                break
        self._reload_pending = True
        self._error = ""
        self.stateChanged.emit()
        self._application.results_view_changed.emit()
        self._application._notify(self.tr("TACTIC definition saved"))

    @staticmethod
    def _view_tree(value, view="table"):
        root = (
            ElementTree.fromstring(value)
            if str(value or "").strip()
            else ElementTree.Element("config")
        )
        view_node = root if root.tag == view else root.find(f".//{view}")
        if view_node is None:
            view_node = ElementTree.SubElement(root, view)
        return root, view_node

    @staticmethod
    def _width(value):
        return tactic_definition.width(value)

    def _build_records(self, stype, payload):
        from thlib import tactic_table_widgets as table_widgets

        database_views = dict(payload.get("databaseViews") or {})
        table_xml = str(
            dict(database_views.get("table") or {}).get("config") or ""
        )
        root, table = self._view_tree(table_xml)
        sources = {}
        unmanaged = []
        for element in table.findall("element"):
            name = str(element.get("name") or "")
            if not name or name in self._internal or name.startswith("__"):
                unmanaged.append(deepcopy(element))
            else:
                sources.setdefault(name, []).append(deepcopy(element))

        columns_info = dict(stype.get_columns_info() or {})
        available = list(
            payload.get("availableColumns") or payload.get("columns") or []
        )
        selected_names = [
            str(item.get("name") or "")
            for item in payload.get("columns") or []
        ]
        by_name = {
            str(item.get("name") or ""): dict(item)
            for item in available if item.get("name")
        }
        input_sources = {
            str(source.get("name") or ""): dict(source)
            for source in payload.get("inputWidgets") or []
            if source.get("name")
        }
        edit_names = {
            str(item.get("name") or "")
            for item in available
            if item.get("name") and item.get("editSelected")
        }
        if not edit_names:
            edit_names = set(input_sources)
        if not edit_names:
            edit_xml = str(
                dict(database_views.get("edit") or {}).get("config") or ""
            )
            if edit_xml:
                _edit_root, edit_view = self._view_tree(edit_xml, "edit")
                edit_names = {
                    str(element.get("name") or "")
                    for element in edit_view.findall("element")
                    if element.get("name")
                }
        names = selected_names + [
            name for name in by_name if name not in selected_names
        ]
        records = []
        edit_sources = {}
        for order, name in enumerate(names):
            item = by_name[name]
            info = dict(columns_info.get(name) or {})
            attrs = dict(item.get("attributes") or {})
            editable = str(attrs.get("edit", "true")).lower() != "false"
            table_widget = table_widgets.create_widget(item)
            edit_source = (
                input_sources.get(name) or tactic_definition.edit_source(item)
            )
            if edit_source:
                edit_source.update({
                    "name": name,
                    "title": str(item.get("title") or name),
                    "action_options": dict(
                        edit_source.get("action_options")
                        or item.get("actionOptions") or {}
                    ),
                })
                edit_sources[name] = edit_source
            records.append({
                "name": name,
                "label": str(
                    item.get("title") or info.get("label")
                    or name.replace("_", " ").title()
                ),
                "dataType": str(
                    item.get("dataType") or info.get("data_type") or "text"
                ),
                "displayVisible": name in selected_names,
                "displayWidth": self._width(item.get("width")),
                "order": order,
                "readOnly": name in self._protected or not editable,
                "widgetClass": str(item.get("displayClass") or ""),
                "widgetKey": str(item.get("displayWidget") or ""),
                "cellKind": table_widget.get_cell_kind(
                    item.get("dataType") or info.get("data_type") or "text"
                ),
                "resolvedClass": table_widget.get_class_name() or "",
                "sortable": bool(item.get("sortable")) and name in columns_info,
                "editable": bool(edit_source)
                and table_widget.get_cell_kind(
                    item.get("dataType") or info.get("data_type") or "text"
                ) in {"text", "boolean", "link"}
                and not (name in self._protected or not editable),
                "displayOptions": dict(item.get("displayOptions") or {}),
                "displayXml": str(item.get("displayXml") or ""),
                "editClass": str(item.get("editClass") or ""),
                "editWidget": str(item.get("editWidget") or ""),
                "editOptions": dict(item.get("editOptions") or {}),
                "editXml": str(item.get("editXml") or ""),
                "editVisible": name in edit_names,
                "actionClass": str(item.get("actionClass") or ""),
                "actionOptions": dict(item.get("actionOptions") or {}),
            })
        return (
            root, sources, unmanaged, table_xml, database_views, records,
            {
                record["name"]: table_widgets.create_widget(by_name[record["name"]])
                for record in records
            },
            edit_sources,
        )

    @Slot()
    def reload(self):
        stype = self._current_stype()
        if not stype:
            self._clear()
            return
        stype_code = str(stype.get_code() or "")
        if self._dirty and stype_code == self._stype_code:
            return
        if self._busy:
            self._reload_pending = True
            return
        project_code = str(self._application._current_project_code or "")
        if project_code != self._definition_catalog_project:
            self._definition_catalog = []
            self._definition_catalog_loaded = False
            self._definition_catalog_project_object = None
        search_keys = self._current_search_keys()
        self._row_request_id += 1
        self._row_sync_pending = False
        if self._row_worker is not None:
            try:
                self._row_worker.cancel()
            except (AttributeError, RuntimeError):
                pass
            self._row_worker = None

        def operation():
            import thlib.tactic_classes as tc
            from thlib import tactic_query as tq

            layout = tc.get_table_layout(
                stype_code,
                search_keys=[],
                view="table",
                project_code=project_code,
            )
            if "inputWidgets" not in layout and search_keys:
                try:
                    schema = tc.execute_procedure_serverside(
                        tq.query_EditWdg,
                        {
                            "args": {
                                "mode": "edit",
                                "input_prefix": "edit",
                                "search_key": search_keys[0],
                                "search_type": stype_code,
                                "view": "edit",
                            },
                            "search_type": stype_code,
                            "project": project_code,
                        },
                        project=project_code,
                    )
                    layout["inputWidgets"] = list(
                        (schema or {}).get("InputWidgets") or []
                    )
                except Exception as error:
                    layout["inputWidgets"] = []
                    layout["editSchemaError"] = str(error)
            else:
                layout.setdefault("inputWidgets", [])
            return stype, layout

        self._run(operation, self._loaded)

    @Slot(object)
    def _loaded(self, result):
        stype, payload = result
        current = self._current_stype()
        current_code = str(current.get_code() or "") if current else ""
        if current_code != str(stype.get_code() or ""):
            self._reload_pending = True
            return
        try:
            (
                root, sources, unmanaged, table_xml, database_views, records,
                table_widgets, edit_sources,
            ) = self._build_records(stype, dict(payload or {}))
        except (AttributeError, TypeError, ValueError, ElementTree.ParseError) as error:
            self._error = str(error)
            self.stateChanged.emit()
            return
        self._stype_code = str(stype.get_code() or "")
        self._title = str(stype.get_pretty_name() or self._stype_code)
        if self._definition_catalog_loaded:
            current_base = self._stype_code.split("?", 1)[0]
            for record in self._definition_catalog:
                record["current"] = (
                    record["searchType"].split("?", 1)[0] == current_base
                )
            self._definition_catalog.sort(key=lambda record: (
                not record["current"], record["searchType"].lower(),
                record["view"].lower(), record["login"].lower(),
                record["code"].lower(),
            ))
            for row, record in enumerate(self._definition_catalog):
                record["row"] = row
        self._definition_root = root
        self._source_elements = sources
        self._unmanaged_elements = unmanaged
        self._definition_xml = table_xml
        self._database_views = database_views
        self._edit_sources = edit_sources
        schema_error = str(payload.get("editSchemaError") or "")
        if schema_error and getattr(self._application, "debug_log", None):
            self._application.debug_log.log(
                "WARNING",
                schema_error,
                group="tactic/columns_editor",
                source="ColumnsEditorController",
                caller=2,
            )
        self._table_widgets = table_widgets
        self._data_types = {
            record["name"]: record["dataType"] for record in records
        }
        self._cells = self._map_rows(payload)
        self._cell_revision += 1
        self.cellRevisionChanged.emit()
        self._source_records = [dict(record) for record in records]
        self.model.replace(records)
        self._dirty = False
        self._error = ""
        self.stateChanged.emit()
        self._sync_table_rows()

    def _map_rows(self, payload):
        rows = {
            str(search_key): {
                name: self._table_widgets[name].map_cell(
                    cell, self._data_types.get(name, "text")
                )
                for name, cell in dict(row or {}).items()
                if name in self._table_widgets
            }
            for search_key, row in dict(payload.get("rows") or {}).items()
        }
        for search_key, cells in rows.items():
            self._add_task_workflow_rows(search_key, cells)
        return rows

    def _sobject_for_search_key(self, search_key):
        tab = self._current_tab()
        return next((
            sobject for sobject in (getattr(tab, "sobjects", None) or [])
            if str(sobject.get_search_key() or "") == str(search_key or "")
        ), None)

    def _add_task_workflow_rows(self, search_key, cells):
        """Fill native TaskElementWdg rows with the object's empty processes."""
        tasks = self._tasks_controller
        target = self._sobject_for_search_key(search_key)
        if tasks is None or target is None:
            return
        try:
            processes = tasks._process_choices_for(target)
        except (AttributeError, KeyError, TypeError, ValueError):
            processes = []
        for cell in cells.values():
            records = cell.get("tasks")
            if not isinstance(records, list):
                continue
            remaining = [dict(record or {}) for record in records]
            ordered = []
            for process_info in processes:
                process = str(process_info.get("value") or "")
                matches = [
                    record for record in remaining
                    if str(record.get("process") or "") == process
                ]
                remaining = [
                    record for record in remaining
                    if str(record.get("process") or "") != process
                ]
                if not matches:
                    defaults = tasks._process_task_defaults(target, process)
                    matches = [{
                        "taskSearchKey": "",
                        "taskCode": "",
                        "process": process,
                        "context": process,
                        "status": str(defaults.get("status") or ""),
                        "statusColor": "",
                        "assigned": str(defaults.get("assigned") or ""),
                        "bidStart": str(defaults.get("start") or ""),
                        "bidEnd": str(defaults.get("end") or ""),
                    }]
                for record in matches:
                    record["processLabel"] = str(
                        process_info.get("label") or process
                    )
                    record["processColor"] = str(
                        process_info.get("color") or ""
                    )
                    record["hasTask"] = bool(
                        record.get("taskSearchKey") or record.get("taskCode")
                    )
                    record["assignedLabel"] = (
                        tasks._login_label(record.get("assigned"))
                        or self.tr("Not assigned")
                    )
                    ordered.append(record)
            for record in remaining:
                record["processLabel"] = str(
                    record.get("process") or record.get("context") or "Task"
                )
                record["processColor"] = str(
                    record.get("statusColor") or ""
                )
                record["hasTask"] = True
                record["assignedLabel"] = (
                    tasks._login_label(record.get("assigned"))
                    or self.tr("Not assigned")
                )
                ordered.append(record)
            cell["tasks"] = ordered

    def _task_target(self, node_id):
        node = self._application.workspace_model.node_for(str(node_id or ""))
        return getattr(node, "source", None) if node is not None else None

    @Slot(str, str, str, str, result="QVariantMap")
    def task_editor(self, node_id, process, status, assigned):
        """Resolve the same workflow choices used by Quick Tasks, on demand."""
        tasks = self._tasks_controller
        target = self._task_target(node_id)
        if tasks is None or target is None:
            return {}
        process = str(process or "")
        status = str(status or "")
        assigned = str(assigned or "")
        process_color = next((
            str(item.get("color") or "")
            for item in tasks._process_choices_for(target)
            if str(item.get("value") or "") == process
        ), "")
        statuses = tasks._with_current_status(
            tasks._status_choices_for(target, process), status, process_color
        )
        users = tasks._user_choices_for(
            target, process, include_login=assigned
        )
        return {
            "statusChoices": statuses,
            "userChoices": users,
        }

    @Slot(str, str, str, str, str, result=bool)
    def set_task_value(
        self, node_id, task_search_key, process, field, value,
    ):
        if self._busy or field not in {"status", "assigned"}:
            return False
        if self._tasks_controller is None:
            return False
        task_search_key = str(task_search_key or "")
        process = str(process or "")
        if not process:
            return False
        value = str(value or "")
        node_id = str(node_id or "")
        target = self._task_target(node_id)
        if target is None:
            return False
        parent_search_key = str(target.get_search_key() or "")
        source_records = [
            record
            for cell in (self._cells.get(parent_search_key) or {}).values()
            for record in (cell.get("tasks") or [])
        ]
        if task_search_key:
            source_record = next((
                record for record in source_records
                if str(record.get("taskSearchKey") or "") == task_search_key
                and str(record.get("process") or "") == process
            ), None)
        else:
            source_record = next((
                record for record in source_records
                if not record.get("hasTask")
                and str(record.get("process") or "") == process
            ), None)
        if source_record is None:
            return False
        context = str(source_record.get("context") or process)
        tab = self._current_tab()
        selected_node_ids = list(dict.fromkeys(
            str(selected_id or "")
            for selected_id in (
                getattr(tab, "selected_node_ids", None) or []
            )
            if selected_id
        ))
        target_node_ids = (
            selected_node_ids
            if len(selected_node_ids) > 1
            else [node_id]
        )
        plans = []
        seen_parent_keys = set()
        for target_node_id in target_node_ids:
            edit_target = self._task_target(target_node_id)
            if edit_target is None:
                self._error = self.tr(
                    "The task process is unavailable for a selected row."
                )
                self.stateChanged.emit()
                return False
            edit_parent_key = str(edit_target.get_search_key() or "")
            if not edit_parent_key or edit_parent_key in seen_parent_keys:
                continue
            records = [
                record
                for cell in (self._cells.get(edit_parent_key) or {}).values()
                for record in (cell.get("tasks") or [])
                if str(record.get("process") or "") == process
                and str(record.get("context") or process) == context
            ]
            if target_node_id == node_id:
                record = source_record
            else:
                record = next((
                    item for item in records
                    if item.get("hasTask") and item.get("taskSearchKey")
                ), None) or next((
                    item for item in records if not item.get("hasTask")
                ), None)
            if record is None:
                self._error = self.tr(
                    "The task process is unavailable for a selected row."
                )
                self.stateChanged.emit()
                return False
            editor = self.task_editor(
                target_node_id, process,
                str(record.get("status") or ""),
                str(record.get("assigned") or ""),
            )
            choices = editor.get(
                "statusChoices" if field == "status" else "userChoices"
            ) or []
            if value not in {
                str(choice.get("value") or "") for choice in choices
            }:
                self._error = self.tr(
                    "The selected task value is unavailable for a selected row."
                )
                self.stateChanged.emit()
                return False
            try:
                project_code = str(
                    edit_target.get_project().get_code() or ""
                )
            except AttributeError:
                project_code = str(
                    self._application._current_project_code or ""
                )
            plans.append({
                "nodeId": target_node_id,
                "target": edit_target,
                "parentSearchKey": edit_parent_key,
                "taskSearchKey": str(record.get("taskSearchKey") or ""),
                "projectCode": project_code,
            })
            seen_parent_keys.add(edit_parent_key)
        if not plans:
            return False

        def operation():
            from thlib import server_cache
            import thlib.tactic_classes as tc
            payloads = []
            existing = {}
            for plan in plans:
                key = plan["taskSearchKey"]
                if key:
                    existing.setdefault(plan["projectCode"], []).append(plan)
                    continue
                data = self._tasks_controller._native_process_task_defaults(
                    plan["target"], process
                )
                data.update({
                    "process": process, "context": context, field: value,
                })
                result = tc.insert_sobjects(
                    "sthpw/task", plan["projectCode"], data,
                    parent_key=plan["parentSearchKey"], triggers=True,
                )
                if not isinstance(result, dict) or not result.get(
                    "__search_key__"
                ):
                    raise RuntimeError(self.tr(
                        "TACTIC did not return the created task identity"
                    ))
                payloads.append({**plan, "result": result})
            for project_code, project_plans in existing.items():
                server = tc.server_start(project=project_code)
                if len(plans) == 1:
                    plan = project_plans[0]
                    server.update(
                        plan["taskSearchKey"], {field: value}, triggers=True
                    )
                else:
                    server.update_multiple(
                        data={
                            plan["taskSearchKey"]: {field: value}
                            for plan in project_plans
                        },
                        triggers=True,
                    )
                payloads.extend(
                    {**plan, "result": {}} for plan in project_plans
                )
            for project_code in {
                plan["projectCode"] for plan in plans
            }:
                server_cache.invalidate_domains(
                    ("tasks", "notes", "search", "activity", "work_hours"),
                    project_code,
                )
            for payload in payloads:
                payload.update({
                    "process": process, "context": context,
                    "field": field, "value": value,
                })
                payload.pop("target", None)
                payload.pop("projectCode", None)
            return payloads

        self._run(operation, self._task_value_saved)
        return True

    @Slot(object)
    def _task_value_saved(self, payloads):
        changed = False
        for payload in (
            payloads if isinstance(payloads, list) else [payloads]
        ):
            changed = self._apply_task_value_result(payload) or changed
        if changed:
            self._cell_revision += 1
            self.cellRevisionChanged.emit()
        self._application._notify(self.tr("Task saved"))

    def _apply_task_value_result(self, payload):
        payload = dict(payload or {})
        raw_result = payload.get("result")
        result = dict(raw_result) if isinstance(raw_result, dict) else {}
        previous_search_key = str(payload.get("taskSearchKey") or "")
        task_search_key = str(
            previous_search_key
            or result.get("__search_key__") or ""
        )
        task_code = str(result.get("code") or "")
        process = str(payload.get("process") or "")
        context = str(payload.get("context") or process)
        field = str(payload.get("field") or "")
        value = str(payload.get("value") or "")
        row = self._cells.get(str(payload.get("parentSearchKey") or "")) or {}
        changed = False
        matched_code = task_code
        for cell in row.values():
            records = cell.get("tasks")
            if not isinstance(records, list):
                continue
            for record in records:
                same_task = task_search_key and str(
                    record.get("taskSearchKey") or ""
                ) == task_search_key
                new_process = not previous_search_key and (
                    not record.get("hasTask")
                    and str(record.get("process") or "") == process
                    and str(record.get("context") or process) == context
                )
                if not same_task and not new_process:
                    continue
                record[field] = value
                record["hasTask"] = True
                record["taskSearchKey"] = task_search_key
                if task_code:
                    record["taskCode"] = task_code
                else:
                    matched_code = str(record.get("taskCode") or "")
                if field == "assigned":
                    record["assignedLabel"] = (
                        self._tasks_controller._login_label(value)
                        or self.tr("Not assigned")
                    )
                elif field == "status":
                    editor = self.task_editor(
                        str(payload.get("nodeId") or ""), process,
                        value, str(record.get("assigned") or ""),
                    )
                    record["statusColor"] = next((
                        str(item.get("color") or "")
                        for item in editor.get("statusChoices") or []
                        if str(item.get("value") or "") == value
                    ), str(record.get("processColor") or ""))
                changed = True
                break
        target = self._task_target(str(payload.get("nodeId") or ""))
        if target is not None:
            try:
                summaries = list(target.get_task_summaries(process) or [])
                summary = next((
                    item for item in summaries
                    if str(item.get("code") or "") == matched_code
                    or str(item.get("__search_key__") or "")
                    == task_search_key
                ), None)
                if summary is None:
                    summary = {
                        "code": matched_code,
                        "__search_key__": task_search_key,
                        "process": process,
                        "context": context,
                    }
                    summaries.append(summary)
                summary[field] = value
                target.set_task_summaries(process, summaries)
            except (AttributeError, TypeError, ValueError):
                pass
            if not previous_search_key:
                try:
                    counts = dict(target.get_tasks_count() or {})
                    count = int(counts.get(process) or 0) + 1
                    node = self._application.workspace_model.node_for(
                        str(payload.get("nodeId") or "")
                    )
                    update_count = getattr(
                        self._application.workspace_model,
                        "_set_process_count", None,
                    )
                    if node is not None and callable(update_count):
                        update_count(node, "tasks", process, count)
                    else:
                        target.set_tasks_count(process, count)
                except (AttributeError, TypeError, ValueError):
                    pass
        return changed

    @Slot()
    def _sync_table_rows(self):
        tab = self._current_tab()
        if (
            not tab or getattr(tab, "view_mode", "") != "table"
            or not self._stype_code
        ):
            return
        if self._row_worker is not None:
            self._row_sync_pending = True
            return
        missing = [
            key for key in self._current_search_keys()
            if key not in self._cells
        ]
        if not missing:
            return
        project_code = str(self._application._current_project_code or "")
        stype_code = self._stype_code
        request_id = self._row_request_id

        def operation():
            import thlib.tactic_classes as tc
            return tc.get_table_layout(
                stype_code,
                search_keys=missing,
                view="table",
                project_code=project_code,
            )

        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(operation)
            if worker is None:
                raise RuntimeError(self.tr("Server worker is unavailable"))
            self._row_worker = worker
            worker.result.connect(
                lambda payload: self._table_rows_loaded(request_id, payload)
            )
            worker.error.connect(
                lambda error: self._table_rows_failed(request_id, error)
            )
            worker.finished.connect(lambda: self._table_rows_finished(worker))
            worker.start()
        except Exception as error:
            self._row_worker = None
            self._log_row_error(str(error), traceback.format_exc())

    def _table_rows_loaded(self, request_id, payload):
        if request_id != self._row_request_id:
            return
        mapped = self._map_rows(dict(payload or {}))
        if not mapped:
            return
        self._cells.update(mapped)
        self._cell_revision += 1
        self.cellRevisionChanged.emit()

    def _table_rows_failed(self, request_id, error):
        if request_id != self._row_request_id:
            return
        payload = error[0] if isinstance(error, (tuple, list)) else {}
        self._log_row_error(
            str(payload.get("exception") or error),
            str(payload.get("traceback") or ""),
        )

    def _log_row_error(self, message, stacktrace=""):
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.log(
                "ERROR", message,
                group="tactic/columns_editor",
                source="ColumnsEditorController",
                stacktrace=stacktrace,
                caller=2,
            )

    def _table_rows_finished(self, worker):
        if self._row_worker is not worker:
            return
        self._row_worker = None
        pending = self._row_sync_pending
        self._row_sync_pending = False
        if pending:
            self._sync_table_rows()

    def _clear(self, error=""):
        self._row_request_id += 1
        self._row_sync_pending = False
        if self._row_worker is not None:
            try:
                self._row_worker.cancel()
            except (AttributeError, RuntimeError):
                pass
            self._row_worker = None
        self._stype_code = ""
        self._title = "Columns"
        self._source_records = []
        self._source_elements = {}
        self._unmanaged_elements = []
        self._definition_root = None
        self._definition_xml = ""
        self._database_views = {}
        self._definition_catalog = []
        self._definition_catalog_loaded = False
        self._definition_catalog_project = ""
        self._definition_catalog_project_object = None
        self._cells = {}
        self._table_widgets = {}
        self._data_types = {}
        self._cell_revision += 1
        self.cellRevisionChanged.emit()
        self._edit_sources = {}
        self.model.clear()
        self._dirty = False
        self._error = str(error or "")
        self.stateChanged.emit()

    @Slot(str, str, result="QVariantMap")
    def cell(self, search_key, column):
        return dict(
            dict(self._cells.get(str(search_key or "")) or {}).get(
                str(column or "")
            ) or {}
        )

    @Slot(str, int, result="QVariantMap")
    def row_cells(self, search_key, _revision=0):
        """Cross the QML boundary once per visible row, not once per cell."""
        return dict(self._cells.get(str(search_key or "")) or {})

    @Slot(str, str, result="QVariantMap")
    def cell_editor(self, node_id, column):
        """Resolve a table cell through the EditSObject field catalog."""
        column = str(column or "")
        record = next((
            item for item in self.model._records
            if item["name"] == column
        ), None)
        source = self._edit_sources.get(column)
        if not record or not record["editable"] or not source:
            return {}
        node = self._application.workspace_model.node_for(str(node_id or ""))
        sobject = getattr(node, "source", None) if node is not None else None
        stype = self._current_stype()
        if sobject is None or stype is None:
            return {}
        from thlib.ui.sobject_editor import SObjectEditorController

        descriptor = SObjectEditorController.describe_field(
            stype,
            {"stype": stype, "sobject": sobject},
            source,
            mode="edit",
        )
        if not descriptor or descriptor["fieldReadOnly"] or (
            descriptor["fieldType"] in {
                "parent", "preview", "thumbnail", "unsupported",
            }
        ):
            return {}
        return descriptor

    def _set_record(self, row, **values):
        if self._busy or not 0 <= row < len(self.model._records):
            return
        record = dict(self.model._records[row])
        record.update(values)
        self.model._records[row] = record
        index = self.model.index(row, 0)
        self.model.dataChanged.emit(
            index, index, list(self.model._role_ids.values())
        )
        self._dirty = self.model._records != self._source_records
        self._error = ""
        self.stateChanged.emit()

    @Slot(int, bool)
    def set_visible(self, row, visible):
        self._set_record(row, displayVisible=bool(visible))

    @Slot(int, bool)
    def sort_column(self, row, descending):
        if not 0 <= row < len(self.model._records):
            return
        record = self.model._records[row]
        if not record["sortable"]:
            return
        direction = "desc" if descending else "asc"
        self._application.set_result_sort_mode(
            f"column:{record['name']}:{direction}"
        )

    @Slot(int, result=bool)
    def remove_column(self, row):
        visible = [
            record for record in self.model._records
            if record["displayVisible"]
        ]
        if len(visible) <= 1 or not 0 <= row < len(self.model._records):
            return False
        self.set_visible(row, False)
        return self.apply()

    @Slot(int, str)
    def request_column_focus(self, row, target):
        if not 0 <= row < len(self.model._records):
            return
        self._requested_row = row
        self._requested_name = str(self.model._records[row]["name"])
        self._requested_definition_target = (
            target if target in {"definition", "edit_definition"}
            else "definition"
        )
        self.focusRequested.emit()

    @Slot(int, int)
    def set_width(self, row, width):
        self._set_record(row, displayWidth=self._width(width))

    @Slot(int, str)
    def set_label(self, row, label):
        label = str(label or "").strip()
        if not label:
            self._error = self.tr("Column label cannot be empty.")
            self.stateChanged.emit()
            return
        self._set_record(row, label=label)

    @Slot(int, int)
    def move(self, row, offset):
        target = row + int(offset)
        if self._busy or not (
            0 <= row < len(self.model._records)
            and 0 <= target < len(self.model._records)
        ):
            return
        records = [dict(record) for record in self.model._records]
        records.insert(target, records.pop(row))
        for order, record in enumerate(records):
            record["order"] = order
        self.model.replace(records)
        self._dirty = records != self._source_records
        self.stateChanged.emit()

    def _serialize(self, records):
        root = (
            deepcopy(self._definition_root)
            if self._definition_root is not None
            else ElementTree.Element("config")
        )
        table = root if root.tag == "table" else root.find(".//table")
        if table is None:
            table = ElementTree.SubElement(root, "table")
        for element in list(table.findall("element")):
            table.remove(element)
        for record in records:
            if not record["displayVisible"]:
                continue
            elements = self._source_elements.get(record["name"]) or [
                ElementTree.Element("element", {"name": record["name"]})
            ]
            for source in elements:
                element = deepcopy(source)
                element.set("name", record["name"])
                element.set("title", record["label"])
                element.set("width", str(record["displayWidth"]))
                table.append(element)
        for element in self._unmanaged_elements:
            table.append(deepcopy(element))
        return ElementTree.tostring(root, encoding="unicode")

    @Slot(result=bool)
    def apply(self):
        if self._busy:
            return False
        if not any(item["displayVisible"] for item in self.model._records):
            self._error = self.tr("At least one column must remain visible.")
            self.stateChanged.emit()
            return False
        stype = self._current_stype()
        project_code = str(self._application._current_project_code or "")
        if not stype or stype.get_code() != self._stype_code:
            self._error = self.tr(
                "The Search Type changed. Reopen the Columns Editor."
            )
            self.stateChanged.emit()
            return False
        records = [dict(record) for record in self.model._records]
        config_xml = self._serialize(records)

        def operation():
            import thlib.tactic_classes as tc
            return tc.save_widget_config(
                self._stype_code,
                "table",
                config_xml=config_xml,
                project_code=project_code,
            )

        self._run(operation, self._saved)
        return True

    def _definition_element(self, row, target):
        if not 0 <= row < len(self.model._records):
            raise ValueError(self.tr("Select a column."))
        return tactic_definition.definition_element(
            self._database_views, self.model._records[row], target
        )

    @Slot(int, str, result="QVariantMap")
    def element_form(self, row, target):
        target = str(target or "definition")
        try:
            element = self._definition_element(row, target)
            record = self.model._records[row]
        except (ElementTree.ParseError, TypeError, ValueError, IndexError) as error:
            self._error = str(error)
            self.stateChanged.emit()
            return {}
        edit_source = self._edit_sources.get(record["name"], {})
        return tactic_definition.element_form(
            element, record, edit_source, target
        )

    @Slot(int, str, result=str)
    def element_xml(self, row, target):
        try:
            element = self._definition_element(row, str(target or "definition"))
            return ElementTree.tostring(element, encoding="unicode")
        except (ElementTree.ParseError, TypeError, ValueError) as error:
            self._error = str(error)
            self.stateChanged.emit()
            return ""

    @Slot(int, str, str, int, str, result=bool)
    def save_element_form(self, row, target, title, width, widget):
        target = str(target or "definition")
        try:
            element = self._definition_element(row, target)
            if target != "edit_definition":
                element.set("title", str(title or "").strip())
                element.set("width", str(self._width(width)))
            display = element.find("display")
            if display is None:
                display = ElementTree.SubElement(element, "display")
            tactic_definition.set_widget(
                display,
                tactic_definition.input_widget(widget)
                if target == "edit_definition" else widget,
                is_input=target == "edit_definition",
            )
            xml = ElementTree.tostring(element, encoding="unicode")
        except (ElementTree.ParseError, TypeError, ValueError) as error:
            self._error = str(error)
            self.stateChanged.emit()
            return False
        return self._save_element(row, target, xml)

    @Slot(int, str, "QVariantMap", result=bool)
    def save_element_visual(self, row, target, form):
        target = str(target or "definition")
        form = dict(form or {})
        try:
            element = self._definition_element(row, target)
            tactic_definition.update_element(element, target, form)
            xml = ElementTree.tostring(element, encoding="unicode")
        except (ElementTree.ParseError, TypeError, ValueError) as error:
            self._error = self.tr(str(error))
            self.stateChanged.emit()
            return False
        included = (
            tactic_definition.flag(form.get("included"))
            if target == "edit_definition" else None
        )
        return self._save_element(row, target, xml, included=included)

    @Slot(int, str, str, result=bool)
    def save_element_xml(self, row, target, xml):
        return self._save_element(row, str(target or "definition"), xml)

    def _edit_view_xml(self, element_name, included):
        source = str(
            dict(self._database_views.get("edit") or {}).get("config") or ""
        )
        return tactic_definition.edit_view_xml(
            source, self.model._records, element_name, included
        )

    def _save_element(self, row, target, xml, included=None):
        if self._busy or target not in {"definition", "edit_definition", "table"}:
            return False
        if not 0 <= row < len(self.model._records):
            return False
        try:
            element = ElementTree.fromstring(str(xml or ""))
            expected_name = self.model._records[row]["name"]
            if element.tag != "element" or element.get("name") != expected_name:
                raise ValueError(
                    self.tr("XML must contain the selected <element name=...>.")
                )
        except (ElementTree.ParseError, ValueError) as error:
            self._error = str(error)
            self.stateChanged.emit()
            return False
        stype = self._current_stype()
        if not stype or str(stype.get_code() or "") != self._stype_code:
            self._error = self.tr(
                "The Search Type changed. Reopen the Columns Editor."
            )
            self.stateChanged.emit()
            return False
        stype_code = self._stype_code
        project_code = str(self._application._current_project_code or "")
        edit_config_xml = None
        if target == "edit_definition":
            if included is None:
                included = bool(self.model._records[row]["editVisible"])
            try:
                edit_config_xml = self._edit_view_xml(expected_name, included)
            except ElementTree.ParseError as error:
                self._error = str(error)
                self.stateChanged.emit()
                return False

        def operation():
            import thlib.tactic_classes as tc
            result = tc.save_widget_config(
                stype_code,
                target,
                element_xml=ElementTree.tostring(element, encoding="unicode"),
                project_code=project_code,
            )
            if target == "edit_definition":
                tc.save_widget_config(
                    stype_code,
                    "edit",
                    config_xml=edit_config_xml,
                    project_code=project_code,
                )
            return result

        self._run(operation, self._element_saved)
        return True

    def _run(self, operation, result_slot):
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(operation)
            if worker is None:
                raise RuntimeError(self.tr("Server worker is unavailable"))
            self._workers.add(worker)
            worker.result.connect(result_slot)
            worker.error.connect(self._failed)
            worker.finished.connect(lambda: self._release(worker))
            self._busy = True
            self._error = ""
            self.stateChanged.emit()
            worker.start()
        except Exception as error:
            self._busy = False
            self._error = str(error)
            self.stateChanged.emit()

    @Slot(object)
    def _saved(self, _payload):
        self._dirty = False
        self._reload_pending = True
        self.applied.emit()
        self._application.results_view_changed.emit()
        self._application._notify(self.tr("TACTIC table view saved"))

    @Slot(object)
    def _element_saved(self, _payload):
        self._reload_pending = True
        self.applied.emit()
        self._application.results_view_changed.emit()
        self._application._notify(self.tr("TACTIC element definition saved"))

    def _release(self, worker):
        self._workers.discard(worker)
        self._busy = bool(self._workers)
        self.stateChanged.emit()
        current = self._current_stype()
        current_code = str(current.get_code() or "") if current else ""
        if not self._busy and (
            self._reload_pending or current_code != self._stype_code
        ):
            self._reload_pending = False
            self.reload()

    @Slot(object)
    def _failed(self, error):
        payload, worker = error
        self._workers.discard(worker)
        self._busy = bool(self._workers)
        self._error = str(payload.get("exception") or error)
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.log(
                "ERROR", self._error,
                group="tactic/columns_editor",
                source="ColumnsEditorController",
                stacktrace=str(
                    payload.get("traceback") or traceback.format_exc()
                ),
                caller=2,
            )
        self.stateChanged.emit()

    @Slot()
    def cancel(self):
        if self._busy:
            return
        self.model.replace(self._source_records)
        self._dirty = False
        self._error = ""
        self.stateChanged.emit()

    def shutdown(self):
        self._row_request_id += 1
        if self._row_worker is not None:
            try:
                self._row_worker.cancel()
            except (AttributeError, RuntimeError):
                pass
            self._row_worker = None
        for worker in tuple(self._workers):
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        self._workers.clear()
