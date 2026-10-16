"""Profile layout, grouping, counts and command targets through the shipped Frame view."""

import unittest
from PySide6.QtCore import QPointF, Qt, QObject
from PySide6.QtTest import QTest
from tests.frame_support_fixture import Surface, controls, variant
from tests import test_sidebar_editor_qml as sidebar_fixture


class UserProfileQmlTests(unittest.TestCase):
    def surface(self, width=1100):
        surface = Surface("profile", width, 740)
        self.addCleanup(surface.close)
        return surface

    @staticmethod
    def item(surface, name):
        return next(
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                surface.window.contentItem()
            )
            if item.objectName() == name
        )

    def test_summary_chip_keeps_short_caption_and_count_centered(self):
        surface = self.surface()
        chip = self.item(surface, "profileTask_statusSummary_0")
        items = sidebar_fixture.SidebarEditorQmlTests.descendants(chip)
        caption = next(item for item in items if item.property("text") == "In progress")
        count = next(
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(chip)
            if item.property("text") == "5"
        )
        self.assertAlmostEqual(
            caption.width(), caption.property("implicitWidth"), delta=0.1
        )
        row = caption.parentItem()
        self.assertAlmostEqual(row.x() + row.width() / 2, chip.width() / 2, delta=0.6)
        self.assertAlmostEqual(
            count.x() - caption.x() - caption.width(),
            row.property("spacing"),
            delta=0.1,
        )
        self.assertFalse(surface.warnings, surface.warnings)

    def test_user_directory_reserves_scrollbar_gutter_and_searches_all_identity_fields(
        self,
    ):
        surface = self.surface()
        base = surface.users.get(0)
        surface.users.replace(
            [
                dict(
                    base,
                    login="user" + str(index),
                    displayName="User " + str(index),
                    email="email" + str(index) + "@example.test",
                )
                for index in range(20)
            ]
        )
        surface.settle()
        directory = self.item(surface, "userDirectoryList")
        scrollbar = self.item(surface, "userDirectoryScrollBar")
        row = self.item(surface, "userDirectoryRow_user0")
        gutter = directory.width() - row.width()
        self.assertEqual(gutter, 16)
        self.assertGreaterEqual(gutter, scrollbar.width() + 4)
        self.assertTrue(scrollbar.isVisible())
        for query, count in [
            ("User 1", 11),
            ("absent", 0),
            ("artists", 20),
            ("email3@", 1),
        ]:
            surface.view.setProperty("userSearch", query)
            surface.settle()
            self.assertEqual(directory.property("count"), count, query)
        self.assertFalse(surface.warnings, surface.warnings)

    def test_profile_metadata_remains_inside_card_at_narrow_widths(self):
        surface = self.surface()
        for width in (1100, 900, 640, 360):
            surface.window.resize(width, 740)
            surface.view.setWidth(width)
            surface.settle()
            if width < 760:
                surface.view.setProperty("directoryExpanded", False)
                surface.settle()
            card = self.item(surface, "profileSummaryCard")
            server = self.item(surface, "profileInfoValue5")
            point = server.mapToItem(card, QPointF(0, server.height()))
            self.assertLessEqual(point.y(), card.height() - 12)
            self.assertLessEqual(point.x() + server.width(), card.width())
        self.assertFalse(surface.warnings, surface.warnings)

    def test_work_summary_counts_permissions_and_server_status_labels(self):
        surface = self.surface()
        user = surface.controllers.findChild(QObject, "userController")
        user.setProperty(
            "taskSummary", dict(total=32, incomplete=16, overdue=7, dueThisWeek=0)
        )
        user.setProperty(
            "taskStatusSummary",
            [dict(label="Paid", value="server_paid", count=16, color="#00aa44")],
        )
        surface.settle()
        for key, value in [
            ("total", "32"),
            ("completed", "16"),
            ("incomplete", "16"),
            ("overdue", "7"),
            ("dueThisWeek", "0"),
        ]:
            self.assertEqual(
                self.item(surface, "profileTaskMetric_" + key).property("text"), value
            )
        self.assertEqual(
            self.item(surface, "profileTask_statusSummary_0").property("label"),
            "Paid",
        )
        user.setProperty("canViewWorkHours", False)
        surface.settle()
        self.assertNotIn("profileHoursHeading", controls(surface.window))
        user.setProperty("canViewWorkHours", True)
        surface.settle()
        self.assertIsNotNone(self.item(surface, "profileHoursHeading"))
        self.assertFalse(surface.warnings, surface.warnings)


if __name__ == "__main__":
    unittest.main()
