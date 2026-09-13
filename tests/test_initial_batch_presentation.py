from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QMetaObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from thlib.ui.controllers.tab_switch_performance import SearchTabSwitchMonitor
from thlib.ui.ui_performance import UiPerformanceMonitor
from tests.profile_ui_responsiveness import frame


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class InitialBatchPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_first_rows_are_presented_together_after_layout(self):
        engine = QQmlEngine()
        controls_uri = (QML / "controls").as_uri()
        component = QQmlComponent(engine)
        component.setData(
            f'''import QtQuick
import "{controls_uri}" as Controls

Item {{
    id: host
    width: 320
    height: 240
    property alias presentationReady: presentation.ready
    property alias listOpacity: list.opacity
    property int delegateCount: 0

    function loadRows() {{
        list.model = 80
    }}

    ListView {{
        id: list
        anchors.fill: parent
        opacity: presentation.ready ? 1 : 0
        delegate: Rectangle {{
            required property int index
            width: ListView.view.width
            height: 32
            Component.onCompleted: host.delegateCount += 1
        }}
    }}

    Controls.InitialBatchPresentation {{
        id: presentation
        view: list
    }}
}}
'''.encode("utf-8"),
            QUrl(),
        )
        host = component.create()
        self.assertIsNotNone(
            host,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(320, 240)
        host.setParentItem(window.contentItem())
        window.show()

        self.assertTrue(QMetaObject.invokeMethod(host, "loadRows"))
        self.assertFalse(host.property("presentationReady"))
        self.assertEqual(host.property("listOpacity"), 0)

        QTest.qWait(50)

        self.assertTrue(host.property("presentationReady"))
        self.assertEqual(host.property("listOpacity"), 1)
        self.assertGreater(host.property("delegateCount"), 1)

        window.close()
        host.deleteLater()

    def test_blocked_batch_is_hidden_until_its_layout_is_ready(self):
        engine = QQmlEngine()
        controls_uri = (QML / "controls").as_uri()
        component = QQmlComponent(engine)
        component.setData(
            f'''import QtQuick
import "{controls_uri}" as Controls

Item {{
    id: host
    width: 320
    height: 240
    property bool loading: false
    property alias presentationReady: presentation.ready
    property alias listOpacity: list.opacity

    ListView {{
        id: list
        anchors.fill: parent
        model: 40
        opacity: presentation.ready ? 1 : 0
        delegate: Item {{
            required property int index
            width: ListView.view.width
            height: 32
        }}
    }}

    Controls.InitialBatchPresentation {{
        id: presentation
        view: list
        blocked: host.loading
    }}
}}
'''.encode("utf-8"),
            QUrl(),
        )
        host = component.create()
        self.assertIsNotNone(
            host,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(320, 240)
        host.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(30)
        self.assertTrue(host.property("presentationReady"))

        host.setProperty("loading", True)
        self.assertFalse(host.property("presentationReady"))
        self.assertEqual(host.property("listOpacity"), 0)
        host.setProperty("loading", False)
        self.assertFalse(host.property("presentationReady"))
        QTest.qWait(30)
        self.assertTrue(host.property("presentationReady"))
        self.assertEqual(host.property("listOpacity"), 1)

        window.close()
        host.deleteLater()

    def test_disabled_presentation_uses_inherited_item_enabled(self):
        source = (
            QML / "controls" / "InitialBatchPresentation.qml"
        ).read_text(encoding="utf-8")
        self.assertNotIn("property bool enabled", source)

        engine = QQmlEngine()
        controls_uri = (QML / "controls").as_uri()
        component = QQmlComponent(engine)
        component.setData(
            f'''import QtQuick
import "{controls_uri}" as Controls

Item {{
    width: 320
    height: 240
    property alias presentationReady: presentation.ready

    ListView {{
        id: list
        anchors.fill: parent
        model: 1
        delegate: Item {{
            required property int index
            width: ListView.view.width
            height: 32
        }}
    }}

    Controls.InitialBatchPresentation {{
        id: presentation
        view: list
        enabled: false
    }}
}}
'''.encode("utf-8"),
            QUrl(),
        )
        host = component.create()
        self.assertIsNotNone(
            host,
            "\n".join(error.toString() for error in component.errors()),
        )
        self.assertTrue(host.property("presentationReady"))
        host.deleteLater()

    def test_viewport_position_is_restored_after_model_layout(self):
        engine = QQmlEngine()
        controls_uri = (QML / "controls").as_uri()
        component = QQmlComponent(engine)
        component.setData(
            f'''import QtQuick
import "{controls_uri}" as Controls

Item {{
    width: 320
    height: 240
    property alias listContentY: list.contentY
    property real requestedContentY: -1
    onRequestedContentYChanged:
        presentation.restoreContentY(requestedContentY, true)

    ListView {{
        id: list
        anchors.fill: parent
        model: 100
        delegate: Item {{
            required property int index
            width: ListView.view.width
            height: 32
        }}
    }}

    Controls.InitialBatchPresentation {{
        id: presentation
        view: list
        enabled: false
    }}
}}
'''.encode("utf-8"),
            QUrl(),
        )
        host = component.create()
        self.assertIsNotNone(
            host,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(320, 240)
        host.setParentItem(window.contentItem())
        window.show()
        QTest.qWait(30)

        host.setProperty("requestedContentY", 416.0)
        self.assertAlmostEqual(host.property("listContentY"), 416.0)
        QTest.qWait(30)

        self.assertAlmostEqual(host.property("listContentY"), 416.0)
        window.close()
        host.deleteLater()

    def test_tab_switch_timing_completes_on_the_next_rendered_frame(self):
        engine = QQmlEngine()
        performance = UiPerformanceMonitor()
        performance.set_recording(True)
        monitor = SearchTabSwitchMonitor(performance=performance)
        component = QQmlComponent(engine)
        component.setData(b'import QtQuick; Rectangle { width: 160; height: 100; color: "gray" }', QUrl())
        presenter = component.create()
        window = QQuickWindow()
        window.resize(160, 100)
        presenter.setParentItem(window.contentItem())
        window.show()
        window.requestActivate()
        frame(window)
        try:
            serial = monitor.begin("Assets")
            monitor.commit(serial, {"rows": 20})
            self.assertTrue(monitor.switching)
            frame(window, lambda: presenter.setProperty("color", "blue"))
            self.app.processEvents()
            self.assertFalse(monitor.switching)
            self.assertGreaterEqual(monitor.metrics["firstFrameMs"], 0)
            self.assertEqual(performance._samples[0]["status"], "Frame presented")
        finally:
            monitor.cancel()
            performance.shutdown()
            window.close()
            presenter.deleteLater()
            window.deleteLater()

    def test_item_heavy_views_use_the_shared_initial_presentation(self):
        expectations = {
            "SearchResultSurface.qml": (
                'objectName: "initialResultPresentation"',
                'objectName: "initialTilePresentation"',
            ),
            "TaskProcessPanel.qml": (
                'objectName: "initialQuickTaskPresentation"',
            ),
            "TaskBrowserTable.qml": (
                'objectName: "initialTaskTablePresentation"',
            ),
        }
        for filename, markers in expectations.items():
            source = (QML / filename).read_text(encoding="utf-8")
            for marker in markers:
                self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
