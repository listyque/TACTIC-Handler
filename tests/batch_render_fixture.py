"""Isolated Qt/worker fixtures for the packaged Batch Render plugin."""
import ctypes
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from PySide6.QtCore import Property, QObject
from PySide6.QtGui import QGuiApplication, QFontDatabase
from PySide6.QtTest import QTest
from plugins.batch_render import controller as batch
from tactic_handler_api.operations import Executor
from thlib.environment import env_mode

def episode(identity="ep", shots=2):
    return {
        "id": identity,
        "episodeKey": identity,
        "title": identity,
        "test": True,
        "state": "waiting",
        "stage": "Waiting",
        "error": "",
        "elapsed": 0.0,
        "expanded": True,
        "prepared": False,
        "preparationErrors": [],
        "origin": "manual",
        "jobs": [
            {
                "id": f"{identity}-{i}",
                "shotKey": f"{identity}/shot{i}",
                "title": f"Shot {i}",
                "start": 1,
                "end": 5,
                "state": "waiting",
                "stage": "Waiting",
                "error": "",
                "progress": 0.0,
                "elapsed": 0.0,
                "renderElapsed": 0.0,
                "frame": "",
                "framesDone": 0,
                "attempt": 1,
                "scene": "",
                "logPath": "",
                "renderOutput": "",
                "renderFiles": [],
                "preparationErrors": [],
                "pid": "",
            }
            for i in range(shots)
        ],
    }


class Root(QObject):
    dark = Property(bool, lambda self: True, constant=True)
    applicationThemeStyleName = Property(str, lambda self: "default", constant=True)
    applicationThemeAccentColor = Property(str, lambda self: "#58b9e6", constant=True)
    applicationThemeBaseColor = Property(str, lambda self: "#202b32", constant=True)


class BatchCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == "nt":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetErrorMode(kernel32.GetErrorMode() | 0x0001 | 0x0002 | 0x8000)
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        # Offscreen Windows does not discover system fonts automatically.
        if os.name == "nt":
            for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
                QFontDatabase.addApplicationFont(
                    str(Path(os.environ["WINDIR"]) / "Fonts" / name)
                )

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        old = env_mode.current_path
        env_mode.current_path = self.directory.name
        self.addCleanup(setattr, env_mode, "current_path", old)
        self.executor = Executor(4, 32)
        self.api = SimpleNamespace(submit=self.executor.submit)
        self.controller = batch.BatchDispatcherController(
            self.api, "test", offline=True, settings={}
        )
        self.addCleanup(self.finish)

    def finish(self):
        self.controller.shutdown()
        thread = threading.Thread(target=lambda: self.executor.close(wait=True))
        thread.start()
        thread.join(20)
        self.assertFalse(thread.is_alive(), "Worker did not stop")
        self.controller.deleteLater()
        self.app.processEvents()

    def until(self, predicate, seconds=4):
        deadline = time.monotonic() + seconds
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            QTest.qWait(5)
        self.assertTrue(predicate(), self.controller.errorText)

    def visual(self, item, name):
        if item.objectName() == name:
            return item
        for child in item.childItems():
            found = self.visual(child, name)
            if found is not None:
                return found
        return None

