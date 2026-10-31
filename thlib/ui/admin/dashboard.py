"""Page layout drafts reuse the asynchronous administration document owner."""

import copy
import re
from uuid import uuid4
from PySide6.QtCore import QObject, Property, Slot, QTimer, Qt
from ..source_editor import SourceEditorService
from .editor import AdminDocumentEditor
from .dashboard_api import dashboard_editor_request


class DashboardEditor(AdminDocumentEditor):
    @property
    def available(self):
        return bool(getattr(self._application, 'is_stream_server', False))

    def _request(self, action, identity='', **parameters):
        if self.available:
            super()._request(action, identity, **parameters)

    def __init__(self, application, parent=None):
        super().__init__(application, dashboard_editor_request, parent)
        self._source_editor = SourceEditorService(self)
        self._pending_save = None
        self._preview_owner = None
        self._preview_worker = None
        self._checked_document = None
        self._preview_serial = 0
        self._detail_key = ""
        self._source_serial = 0
        self._source_epoch = 0
        self._source_worker = None
        self._source_pending = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._preview)

    @Property(QObject, constant=True)
    def sourceEditor(self):
        return self._source_editor

    def _catalog_loaded(self):
        from urllib.parse import urlsplit
        from ..server_address import normalize_tactic_server_url

        address = urlsplit(normalize_tactic_server_url(getattr(self._application, 'server_url', '')))
        self._revision = self._metadata.get("revision", self._revision)
        self._source_epoch += 1
        self._metadata.update(sourceEpoch=self._source_epoch, project=self._project,
                              origin=address.scheme + '://' + address.netloc if address.netloc else '')

    @Slot(str, "QVariant", str, str)
    def load_source(self, search_type, query=None, record_key="", edit_view="edit"):
        if self._closed or not self.available:
            return
        self._source_serial += 1
        self._metadata["dataError"] = ""
        self._metadata["dataBusy"] = bool(search_type)
        self._source_pending = (
            dict(search_type=search_type, query=query, record_key=record_key,edit_view=edit_view)
            if search_type else None
        )
        if not search_type:
            self._metadata["dataSource"] = {}
        self.stateChanged.emit()
        if self._source_worker is None:
            self._load_source()

    def _load_source(self):
        if self._closed or not self.available or not self._source_pending:
            return
        from thlib.environment import env_inst

        arguments = self._source_pending
        self._source_pending = None
        generation, serial, project = self._generation, self._source_serial, self._project
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(
            lambda: self._execute_request(
                dict(action="source", project_code=project, **arguments), project, {},
            )
        )
        if worker is None:
            self._metadata.update(
                dataBusy=False, dataError=self.tr("Server worker pool is unavailable")
            )
            self.stateChanged.emit()
            return
        self._source_worker = worker

        def finish(result=None, error=None):
            self._source_worker = None
            if self._closed:
                return
            if generation == self._generation and serial == self._source_serial:
                self._metadata["dataBusy"] = False
                if error is not None:
                    self._metadata["dataError"] = str(error[0].get("exception") or error)
                else:
                    self._metadata["dataSource"] = result
                self.stateChanged.emit()
            self._load_source()

        worker.result.connect(lambda result: finish(result=result), Qt.QueuedConnection)
        worker.error.connect(lambda error: finish(error=error), Qt.QueuedConnection)
        worker.start()

    def _document_loaded(self):
        self._preview_serial += 1
        if self._metadata.get("checkedDocument") == self._document:
            self._checked_document = copy.deepcopy(self._document)
            self._update_preview()
        else:
            self._checked_document = None
            if self._document:
                self._timer.start()

    def _update_preview(self):
        if not isinstance(self._application, QObject):
            return
        if self._preview_owner is None:
            from .page_preview import PagePreview

            self._preview_owner = PagePreview(self._application, self)
            self._preview_owner.items.stateChanged.connect(self._samples_changed)
        self._preview_owner.update(self._metadata["compiled"], self._project)
        self._metadata["previewOwner"] = self._preview_owner
        self._metadata["application"] = self._application
        self._samples_changed()

    def _samples_changed(self):
        if self._closed:
            return
        model = self._metadata.get("compiled") or {}
        if not self._preview_owner or not model.get("layoutHasDetails"):
            self._detail_key = ""
            return
        rows = self._preview_owner.items.model.get("sampleItems") or []
        key = (rows[0].get("record") or {}).get("__search_key__", "") if rows else ""
        if key and (key != self._detail_key or not model.get("layoutDetail")):
            self._detail_key = key
            self._preview_serial += 1
            self._timer.start()

    @property
    def checked(self):
        return self._checked_document == self._document

    def _execute_request(self, arguments, project, original):
        if not self.available:
            raise PermissionError('Page layouts require a TACTIC Stream session')
        from thlib import tactic_classes as tc

        if arguments["action"] == "save":
            pending = self._pending_save
            assert pending and pending["document"] == arguments["document"]
            arguments["operation_id"] = pending["operation_id"]
        return tc.execute_procedure_serverside(
            self._endpoint, arguments, project=project
        )

    @Slot("QVariantMap")
    def replace_document(self, document):
        if self.busy or self.writeUncertain or not self.canWrite:
            return
        self._document = copy.deepcopy(document)
        self._error = ""
        self._preview_serial += 1
        self._timer.start()
        self.stateChanged.emit()

    def _preview(self):
        if (
            self._closed
            or not self.available
            or self.busy
            or self.writeUncertain
            or self._preview_worker is not None
            or not self._document
        ):
            return
        from thlib.environment import env_inst

        generation, serial = self._generation, self._preview_serial
        document, revision, project = (
            copy.deepcopy(self._document),
            self._revision,
            self._project,
        )
        detail_key = self._detail_key
        worker = env_inst.server_pool.add_task(
            lambda: self._execute_request(
                dict(
                    action="preview",
                    project_code=project,
                    document=document,
                    expected_revision=revision,
                    detail_key=detail_key,
                ),
                project, {},
            )
        )
        if worker is None:
            self.fail(self.tr("Server worker pool is unavailable"))
            return
        self._preview_worker = worker

        def loaded(result):
            self._preview_worker = None
            if self._closed:
                return
            if generation != self._generation or serial != self._preview_serial:
                if self._document:
                    self._timer.start()
                return
            self._metadata["compiled"] = result["model"]
            self._metadata["sourceXml"] = result["xml"]
            self._metadata["checkedDocument"] = document
            self._checked_document = document
            self._update_preview()
            self.stateChanged.emit()

        def failed(error):
            self._preview_worker = None
            if self._closed:
                return
            if generation != self._generation or serial != self._preview_serial:
                if self._document:
                    self._timer.start()
            else:
                self.fail(str(error[0].get("exception") or error))

        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.start()

    @Slot(str, str)
    def create(self, name, title):
        if self.busy or self.dirty or self.writeUncertain or not self.canWrite:
            return
        if (
            not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", name)
            or not title.strip()
            or len(title) > 256
        ):
            self.fail(self.tr("Enter a page name and title"))
            return
        if any(row["identity"] == name for row in self._catalog):
            self.fail(self.tr("A view with this name already exists"))
            return
        # A fresh revision is loaded by the regular read operation before editing.
        self._preview_serial += 1
        self._revision = self._metadata.get("revision", self._revision)
        self._identity = name
        self._document = dict(name=name, title=title, blocks=[])
        self._original = {}
        self._checked_document = None
        self._timer.start()
        self.stateChanged.emit()

    @Slot()
    def save(self):
        if (
            self.canWrite
            and self.checked
            and self.dirty
            and not self.busy
            and not self.writeUncertain
        ):
            payload = dict(
                document=copy.deepcopy(self._document), expected_revision=self._revision
            )
            if not self._pending_save or any(
                self._pending_save.get(k) != v for k, v in payload.items()
            ):
                self._pending_save = dict(payload, operation_id=str(uuid4()))
            self._request("save", self._identity)

    @Slot(bool)
    def reload_document(self, force=False):
        if self.busy or self.dirty and not force:
            return
        self._presentation_dirty = False
        self._document = copy.deepcopy(self._original)
        self._request("load", self._identity) if self._identity else self._request(
            "list"
        )

    @Slot()
    def open_saved(self):
        if not self.available or self.dirty or self.busy or not self._identity:
            return
        from urllib.parse import quote
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from thlib.environment import env_server
        from ..server_address import normalize_tactic_server_url

        QDesktopServices.openUrl(
            QUrl(
                normalize_tactic_server_url(env_server.get_server())
                + "/projects/"
                + quote(self._project, safe="")
                + "/dashboard/"
                + quote(self._identity, safe="")
            )
        )

    def shutdown(self):
        self._closed = True
        self._timer.stop()
        self._preview_serial += 1
        self._source_serial += 1
        self._source_pending = None
        if self._source_worker:
            self._source_worker.cancel()
        if self._preview_worker:
            self._preview_worker.cancel()
        if self._preview_owner:
            self._preview_owner.shutdown()
        super().shutdown()
