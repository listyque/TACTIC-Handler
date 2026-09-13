from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.workspace_models.results_presentation import PresentationMixin


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class _TextTag:
    def __init__(self, text: str):
        self.text = text


class _Tag:
    def __init__(
        self,
        name: str = "",
        text: str = "",
        *,
        values: str = "",
        labels: str = "",
    ):
        self._name = name
        self.text = text
        self.values = _TextTag(values) if values else None
        self.labels = _TextTag(labels) if labels else None

    def get(self, key: str):
        return self._name if key == "name" else None


class _TagCollection:
    def __init__(self, tags):
        self._tags = list(tags)

    def find_all(self):
        return list(self._tags)


class _Definition:
    def __init__(self, *, element=None, colors=None, edit_definition=None):
        self.element = element
        self.colors = colors
        self.edit_definition = edit_definition


class _SType:
    def __init__(self):
        self.calls = []

    def get_definition(self, name, bs=False):
        self.calls.append((name, bs))
        if name == "table":
            return [
                {"name": "script", "title": "Script Link"},
                {"name": "status"},
                {"name": "enabled"},
                {"name": "details"},
                {"name": "zero"},
                {"name": "description"},
            ]
        if name == "color":
            return _Definition(
                element=_Tag("status"),
                colors=_TagCollection([
                    _Tag("ready", "#4caf50"),
                    _Tag("hold", "#f0a000"),
                ]),
            )
        if name == "edit_definition":
            return _Definition(
                element=_Tag("status"),
                edit_definition=_TagCollection([
                    _Tag(
                        "status",
                        values="ready|hold",
                        labels="Ready for review|On hold",
                    ),
                ]),
            )
        raise AssertionError(name)


class WorkspaceInfoItemPresentationTests(unittest.TestCase):
    def test_legacy_column_specific_presentation_is_preserved(self):
        stype = _SType()
        full_details = "12345678901234567890123456789012345"
        items = PresentationMixin._build_info_items(stype, {
            "name": "Ignored title",
            "script": "https://example.test/tools/run.py",
            "status": "ready",
            "enabled": True,
            "details": full_details,
            "zero": 0,
            "description": "Excluded description",
            "outside_table": "Excluded field",
        })

        self.assertEqual(
            [item["column"] for item in items],
            ["script", "status", "enabled", "details"],
        )
        self.assertEqual(stype.calls, [
            ("table", False),
            ("color", True),
            ("edit_definition", True),
        ])
        self.assertEqual(items[0], {
            "column": "script",
            "kind": "link",
            "text": "Script Link",
            "tooltip": "https://example.test/tools/run.py",
            "url": "https://example.test/tools/run.py",
            "color": "",
        })
        self.assertEqual(items[1]["text"], "Ready for review")
        self.assertEqual(items[1]["color"], "#4caf50")
        self.assertEqual(items[2]["kind"], "boolean")
        self.assertEqual(items[2]["text"], "Enabled")
        self.assertEqual(items[2]["tooltip"], "Enabled: True")
        self.assertEqual(items[3]["text"], full_details[:30])
        self.assertEqual(items[3]["tooltip"], full_details)

    def test_missing_table_definition_has_no_generic_fallback(self):
        class EmptySType:
            @staticmethod
            def get_definition(name, bs=False):
                return []

        self.assertEqual(
            PresentationMixin._build_info_items(
                EmptySType(), {"script": "https://example.test"}
            ),
            [],
        )

    def test_completion_keeps_its_related_search_type(self):
        class Pipeline:
            @staticmethod
            def get_processes_info_by_type(kind):
                return [{"name": "Completion"}] if kind == "progress" else []

            @staticmethod
            def get_pipeline_process(_name):
                return {"workflow": {"search_type": "demo/shot"}}

        class TargetType:
            @staticmethod
            def get_stype_color(fmt="hex"):
                return "#2e9f68" if fmt == "hex" else ""

        class Project:
            @staticmethod
            def get_search_type(search_type):
                self.assertEqual(search_type, "demo/shot")
                return TargetType()

        class SearchType:
            @staticmethod
            def get_pipeline():
                return {"main": Pipeline()}

            @staticmethod
            def get_stype_color(fmt="hex"):
                return "#607d8b" if fmt == "hex" else ""

            @staticmethod
            def get_project():
                return Project()

        class SObject:
            @staticmethod
            def get_pipeline_code():
                return "main"

            @staticmethod
            def get_progress_count(_name, count_type):
                return {"approved_count": 4, "total_count": 6}[count_type]

        self.assertEqual(
            PresentationMixin._progress_items(SObject(), SearchType()),
            [{
                "name": "Completion",
                "label": "4 / 6",
                "color": "#2e9f68",
                "approved": 4,
                "total": 6,
                "searchType": "demo/shot",
            }],
        )


class WorkspaceInfoItemQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_list_and_card_reuse_the_plain_interactive_strip(self):
        row = (QML / "WorkspaceResultItem.qml").read_text(encoding="utf-8")
        card = (QML / "WorkspaceCard.qml").read_text(encoding="utf-8")
        control = (
            QML / "controls" / "InfoValueStrip.qml"
        ).read_text(encoding="utf-8")

        self.assertIn("Controls.InfoValueStrip", row)
        self.assertIn("Controls.InfoValueStrip", card)
        self.assertNotIn("Rectangle {", control)
        self.assertIn('property string separatorText: "/"', control)
        self.assertNotIn('qsTr("%1 Link")', control)
        self.assertIn("Qt.openUrlExternally", control)

    def test_plain_strip_instantiates_and_lays_out_legacy_values(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        self.assertIsNotNone(
            theme,
            "\n".join(error.toString() for error in theme_component.errors()),
        )
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(QML / "controls" / "InfoValueStrip.qml")
            ),
        )
        strip = component.createWithInitialProperties({
            "theme": theme,
            "width": 360,
            "height": 16,
            "items": [
                {
                    "kind": "link",
                    "text": "Script Link",
                    "tooltip": "https://example.test/script.py",
                    "url": "https://example.test/script.py",
                },
                {"kind": "text", "text": "Ready", "tooltip": "Ready"},
            ],
        })
        self.assertIsNotNone(
            strip,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(360, 32)
        strip.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(20)

        def visual_descendants(item):
            for child in item.childItems():
                yield child
                yield from visual_descendants(child)

        texts = {
            str(item.property("text"))
            for item in visual_descendants(strip)
            if item.objectName() == "infoValueText"
        }
        self.assertEqual(texts, {"Script Link", "Ready"})
        self.assertGreater(float(strip.property("implicitWidth")), 0)
        self.assertEqual(float(strip.property("implicitHeight")), 16)
        window.hide()
        strip.setParentItem(None)
        strip.deleteLater()
        window.deleteLater()
        theme.deleteLater()

    def test_completion_chip_opens_its_tracked_search_type(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(QML / "controls" / "CompletionStrip.qml")
            ),
        )
        strip = component.createWithInitialProperties({
            "theme": theme,
            "items": [{
                "name": "Completion",
                "label": "4 / 6",
                "color": "#2e9f68",
                "searchType": "demo/shot",
            }],
        })
        self.assertIsNotNone(
            strip,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(240, 40)
        strip.setParentItem(window.contentItem())
        window.show()
        self.app.processEvents()

        requests = []
        strip.completionRequested.connect(requests.append)
        pending = list(strip.childItems())
        chip = None
        while pending:
            child = pending.pop()
            if child.objectName() == "completionChip_0":
                chip = child
                break
            pending.extend(child.childItems())
        self.assertIsNotNone(chip)
        self.assertEqual(chip.property("text"), "Completion: 4 / 6")
        self.assertEqual(strip.property("implicitHeight"), 24)
        point = chip.mapToScene(QPointF(chip.width() / 2, chip.height() / 2))
        QTest.mouseClick(window, Qt.LeftButton, pos=point.toPoint())
        self.app.processEvents()
        self.assertEqual(requests, ["demo/shot"])

        chip.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Space)
        self.app.processEvents()
        self.assertEqual(requests, ["demo/shot", "demo/shot"])

        window.hide()
        strip.setParentItem(None)
        strip.deleteLater()
        window.deleteLater()
        theme.deleteLater()


if __name__ == "__main__":
    unittest.main()
