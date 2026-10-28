"""Real native field, choice, checkbox and saved-state recovery input."""

import copy
import os
from pathlib import Path
import unittest
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFontDatabase, QInputMethodEvent, QGuiApplication
from PySide6.QtTest import QTest
from tests import test_frame_table as frames
from tests.test_columns_table_view import _TableController, _TableColumns
from tests.test_custom_layout import Services


class FormServices(Services):
    formSettled = Signal(str, "QVariantMap")

    @Slot(str, "QVariantMap")
    def save_form(self, identity, values):
        self.events.append(dict(identity=identity, values=copy.deepcopy(values)))


class NativeRecordParts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()
        for name in ("segoeui.ttf", "seguisb.ttf"):
            path = Path(os.environ.get("WINDIR", "")) / "Fonts" / name
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item
    click = frames.FrameTableTests.click

    def test_edit_save_recovery_and_preview_are_native(self):
        form = dict(
            searchKey="demo/asset?code=A",
            expectedRevision="R1",
            configRevision="C1",
            scope=dict(view="dashboard.test", path=[0]),
            fields=[
                dict(name="name", title="Name", type="text", value="Before"),
                dict(
                    name="status",
                    title="Status",
                    type="select",
                    value="first",
                    options=[
                        dict(value="first", label="First"),
                        dict(value="last", label="Last"),
                    ],
                ),
                dict(name="ready", title="Ready", type="bool", value=False),
            ],
        )
        owner = FormServices(
            dict(
                layoutView="dashboard.test",
                targetSearchKey="demo/asset?code=A",
                layoutNodes=[
                    dict(
                        kind="form", text="Fields", columns=2, editorPath=[0], form=form
                    )
                ],
            )
        )
        window, view = self.create(
            "features/table/CustomLayoutView.qml",
            dict(
                services=owner,
                controller=_TableController(),
                columnsController=_TableColumns(),
                users=None,
                administration=None,
            ),
            width=800,
            height=500,
        )
        self.addCleanup(QTest.keyClick, window, Qt.Key_Escape)
        field = self.item(view, "customLayout_0_field_name")
        field.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        event = QInputMethodEvent()
        event.setCommitString("After")
        QGuiApplication.sendEvent(field, event)
        frames.frame(window)
        choice = self.item(view, "customLayout_0_field_status")
        choice.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Down)
        frames.frame(window)
        self.click(window, self.item(view, "customLayout_0_field_ready"))
        self.click(window, self.item(view, "customLayout_0_save"))
        self.assertEqual(
            owner.events[-1]["values"]["values"],
            dict(name="After", status="last", ready=True),
        )
        request = owner.events[-1]
        owner.formSettled.emit(
            request["identity"],
            dict(failure=dict(message="Connection lost", uncertain=True)),
        )
        frames.frame(window)
        self.assertFalse(self.item(view, "customLayout_0_field_name").isEnabled())
        self.click(window, self.item(view, "customLayout_0_save"))
        self.assertEqual(owner.events[-1]["values"]["action"], "check")
        owner.formSettled.emit(request["identity"], dict(state="conflict"))
        frames.frame(window)
        self.assertFalse(self.item(view, "customLayout_0_save").isEnabled())
        self.click(window, self.item(view, "customLayout_0_cancel"))
        self.assertEqual(
            self.item(view, "customLayout_0_field_name").property("text"), "Before"
        )
        view.setProperty("editing", True)
        frames.frame(window)
        self.assertFalse(self.item(view, "customLayout_0_field_name").isEnabled())
        self.assertFalse(self.item(view, "customLayout_0_field_status").isEnabled())
