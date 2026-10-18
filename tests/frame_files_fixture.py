"""Isolated real file-UI owners; no production settings, repositories or requests."""

from contextlib import ExitStack
import json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from PySide6.QtCore import QObject, Property, Slot, Signal
from thlib.ui.matching_templates import MatchingTemplatesController
from thlib.ui.ingest import IngestFilesController
from thlib.ui.drop_plate import DropPlateController
from tests.test_drop_plate import _Queue, _FileObject


class Locale(QObject):
    def __init__(self, language):
        super().__init__()
        self.language = language

    @Property(str, constant=True)
    def current_language(self):
        return self.language


class Checkin(QObject):
    stateChanged = Signal()
    _process = "publish"
    _context = "review"
    _keep_file_name = False

    @Property(str, notify=stateChanged)
    def process(self):
        return self._process

    @Property(str, notify=stateChanged)
    def context(self):
        return self._context

    @Property(bool, notify=stateChanged)
    def keepFileName(self):
        return self._keep_file_name

    @Property(bool, constant=True)
    def hasObject(self):
        return True

    @Property(bool, notify=stateChanged)
    def actionAvailable(self):
        return bool(self._context)

    @Property("QVariantMap", constant=True)
    def currentObject(self):
        return {"title": "Hero Robot", "code": "ROBOT001"}

    @Slot(str)
    def set_process(self, value):
        self._process = self._context = value
        self.stateChanged.emit()

    @Slot(str)
    def set_context(self, value):
        self._context = value
        self.stateChanged.emit()

    @Slot(bool)
    def set_keep_file_name(self, value):
        self._keep_file_name = value
        self.stateChanged.emit()

    def operation_payload(self):
        return {
            "searchKey": "cg/asset?code=ROBOT001",
            "process": self.process,
            "context": self.context,
            "checkinType": "file",
            "updateVersionless": True,
            "onlyVersionless": False,
        }

    def __init__(self, data):
        super().__init__()
        self.data = data

    @Property("QVariantList", constant=True)
    def processes(self):
        return self.data["processes"]

    @Property("QVariantList", constant=True)
    def contexts(self):
        return self.data["contexts"]


class Windows(QObject):
    def __init__(self):
        super().__init__()
        self.closed = []

    @Slot(str)
    def show_window(self, kind):
        pass

    @Slot(str)
    def hide_window(self, kind):
        self.closed.append(kind)

    @Slot(str)
    def close_window(self, kind):
        self.closed.append(kind)


class FixtureFile(_FileObject):
    def __init__(self, path):
        self.path = path

    def get_all_files_list(self):
        return [self.path]

    def get_file_path(self):
        return self.path

    def get_file_name(self, _with_ext):
        return self.path.rsplit("/", 1)[-1]


class Fixture(ExitStack):
    def __init__(self, language="en"):
        super().__init__()
        self.data = json.loads(
            (Path(__file__).parent / "fixtures/frame_files.json").read_text(
                encoding="utf-8"
            )
        )
        self.enter_context(
            patch(
                "thlib.ui.matching_templates.env_read_config",
                return_value={
                    "matchingTemplates/items": json.dumps(self.data["templates"])
                },
            )
        )
        self.enter_context(patch("thlib.ui.matching_templates.env_write_config"))
        self.matching = MatchingTemplatesController()
        self.locale = Locale(language)
        self.checkin = Checkin(self.data)
        self.windows = Windows()
        self.application = SimpleNamespace(
            window_model=self.windows,
            workspace_model=SimpleNamespace(node_for=lambda _key: None),
        )
        self.ingest = IngestFilesController(self.application)
        data = self.data["ingest"]
        self.ingest._parent_title = data["parentTitle"]
        self.ingest._target_title = data["targetTitle"]
        self.ingest._target_search_type = data["searchType"]
        self.ingest._replace_rules(data["rules"])
        self.ingest.files.replace(data["files"])
        self.enter_context(
            patch("thlib.ui.drop_plate.env_read_config", return_value={})
        )
        self.enter_context(patch("thlib.ui.drop_plate.env_write_config"))
        self.queue = _Queue()
        self.drop = DropPlateController(
            self.application, self.checkin, self.queue, self.matching
        )
        self.drop._recursive = False
        self.drop._group_checkin = False
        self.drop.model.replace(self.data["groups"])
        self.drop._objects = {
            row["groupId"]: FixtureFile(row["path"]) for row in self.data["groups"]
        }

    def context(self):
        return dict(
            matchingTemplatesController=self.matching,
            matchingTemplatesModel=self.matching.model,
            checkinOutController=self.checkin,
            windowModel=self.windows,
            localizationController=self.locale,
            dropPlateController=self.drop,
            dropPlateModel=self.drop.model,
            ingestFilesController=self.ingest,
            ingestFileModel=self.ingest.files,
            ingestRuleModel=self.ingest.rules,
        )
