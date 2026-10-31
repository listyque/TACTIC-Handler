"""Shared resource form input, guarded Configuration lifecycle and transport shape."""

import copy
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QSignalSpy, QTest
from tests.frame_configuration_fixture import Surface
from thlib.ui.configuration_database_resources import DatabaseResourcesEditor


def fixture():
    return dict(
        identity="external",
        revision="one",
        canWrite=True,
        document=dict(
            code="external",
            vendor="PostgreSQL",
            host="database.example",
            port="5432",
            login="studio",
            password="",
            clearPassword=False,
        ),
        catalog=[
            dict(identity="external", title="external"),
            dict(identity="new", title="New resource"),
        ],
        metadata=dict(
            hasPassword=True,
            notice="",
            projects=[
                dict(
                    code="demo",
                    title="Demo project",
                    database="demo_db",
                    resource="external",
                    retired=False,
                )
            ],
        ),
    )


class DatabaseResourceConfigurationTests(unittest.TestCase):
    def test_native_transport_uses_the_shared_resource_http_contract(self):
        backend = DatabaseResourcesEditor(
            SimpleNamespace(
                can_manage_tools=True, server_url="fixture", server_user="admin"
            )
        )
        sent = []

        def open_request(request, timeout):
            sent.append((request.full_url, json.loads(request.data), timeout))
            return io.BytesIO(json.dumps(dict(result=fixture())).encode())

        server = SimpleNamespace(
            login_ticket="fixture-ticket",
            get_server_name=lambda: "http://127.0.0.1:8081",
            transport=SimpleNamespace(open=open_request),
        )
        with patch("thlib.tactic_classes.server_start", return_value=server):
            backend._execute_request(
                dict(
                    action="save",
                    operation="bind",
                    identity="external",
                    expected_revision="one",
                    project_code="demo",
                    database="demo_db",
                    confirmation="bind",
                    document=fixture()["document"],
                ),
                "admin",
                {},
            )
        self.assertTrue(
            sent[0][0].endswith("/admin/configuration/database-resources/bind")
        )
        self.assertEqual(sent[0][1]["project_code"], "demo")
        self.assertEqual(sent[0][1]["confirmation"], "bind")
        self.assertNotIn("document", sent[0][1])
        self.assertEqual(sent[0][1]["ticket"], "fixture-ticket")

    def surface(self, width=1000, height=900, language="en", dark=True):
        backend = DatabaseResourcesEditor(
            SimpleNamespace(
                can_manage_tools=True,
                debug_log=None,
                server_url="fixture",
                server_user="admin",
            )
        )
        value = fixture()
        for name in ("identity", "revision", "document", "catalog", "metadata"):
            setattr(backend, "_" + name, copy.deepcopy(value[name]))
        backend._original = copy.deepcopy(value["document"])
        backend._can_write = backend._loaded = True
        backend._project = "admin"
        backend._document_loaded()
        surface = Surface(
            "configuration",
            width=width,
            height=height,
            language=language,
            dark=dark,
            database_resources=backend,
        )
        for font in ("segoeui.ttf", "seguisb.ttf"):
            QFontDatabase.addApplicationFont("C:/Windows/Fonts/" + font)
        surface.case.config.select_page("database_resources")
        surface.settle()
        self.addCleanup(surface.close)
        self.addCleanup(backend.shutdown)
        return surface, backend

    def click(self, surface, name):
        item = surface.item(name)
        self.assertTrue(item.isVisible(), name)
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        QTest.mouseClick(surface.window, Qt.LeftButton, pos=point)
        surface.settle()

    def test_actual_form_edit_guarded_close_and_confirmed_save(self):
        surface, backend = self.surface()
        host = surface.item("resourceField_host")
        host.forceActiveFocus()
        point = host.mapToScene(QPointF(host.width() / 2, host.height() / 2)).toPoint()
        QTest.mouseClick(surface.window, Qt.LeftButton, pos=point)
        QTest.keyClick(surface.window, Qt.Key_A, Qt.ControlModifier)
        for char in "new.database":
            QTest.keyClick(surface.window, ord(char.upper()))
        surface.settle()
        self.assertEqual(backend.document["host"], "NEW.DATABASE")
        self.assertIn("database_resources", surface.case.config.dirty_pages)
        close = QSignalSpy(surface.case.config.closeAllowed)
        confirmation = QSignalSpy(surface.case.config.confirmationRequested)
        surface.case.config.request_close()
        self.assertEqual(confirmation.count(), 1)
        self.assertEqual(close.count(), 0)
        self.click(surface, "configurationConfirm_keep")
        requests = []
        with patch.object(
            backend,
            "_request",
            side_effect=lambda *args, **kwargs: requests.append((args, kwargs)),
        ):
            self.click(surface, "resource_save")
            self.assertEqual(backend.confirmation, "save")
            self.click(surface, "databaseResourceConfirm")
        self.assertEqual(requests[0][0][0], "save")
        self.assertEqual(requests[0][1]["confirmation"], "save")
        surface.case.config.reset_current()
        self.assertFalse(backend.dirty)
        self.assertFalse(surface.warnings)

    def test_secret_field_and_both_theme_language_layouts(self):
        output = os.environ.get("DATABASE_RESOURCE_CAPTURE")
        for language, dark in (("en", True), ("ru", False)):
            with self.subTest(language=language):
                surface, backend = self.surface(language=language, dark=dark)
                password = surface.item("resourceField_password")
                self.assertEqual(password.property("text"), "")
                self.assertGreater(password.width(), 100)
                self.assertTrue(surface.item("resourceScrollbar").isVisible())
                self.assertEqual(backend.document["password"], "")
                if output:
                    path = (
                        Path(output)
                        / f"native-{language}-{'dark' if dark else 'light'}.png"
                    )
                    path.parent.mkdir(parents=True, exist_ok=True)
                    self.assertTrue(surface.window.grabWindow().save(str(path)))
                surface.close()

    def test_confirmed_operations_and_role_revocation(self):
        surface, backend = self.surface()
        requests = []
        backend.set_project("demo")
        with patch.object(
            backend,
            "_request",
            side_effect=lambda *args, **kwargs: requests.append((args, kwargs)),
        ):
            backend.action("upgrade")
            self.assertEqual(backend.confirmation, "upgrade")
            backend.action("reject")
            self.assertEqual(requests, [])
            backend.action("bind")
            backend.action("accept")
        self.assertEqual(requests[0][1]["project_code"], "demo")
        self.assertEqual(requests[0][1]["operation"], "bind")
        self.assertEqual(requests[0][1]["confirmation"], "bind")
        backend.set_field("password", "draft secret")
        backend._application.can_manage_tools = False
        backend._session_changed()
        self.assertNotIn("draft secret", json.dumps(backend.document))
        self.assertFalse(surface.case.config.dirty)

    def test_cancelled_save_cannot_close_a_later_session(self):
        surface, backend = self.surface()
        config = surface.case.config
        closed = QSignalSpy(config.closeAllowed)
        backend.set_field("host", "changed.example")
        config.save_and_close()
        self.assertEqual(backend.confirmation, "save")
        backend.action("reject")
        backend._original = copy.deepcopy(backend.document)
        backend.committed.emit()
        self.assertEqual(closed.count(), 0)
