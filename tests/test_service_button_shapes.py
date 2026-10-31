"""Square service paint and main-window exceptions through actual native input."""
import json
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
from PySide6.QtCore import QPointF, QUrl, Qt, QCoreApplication, QEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlProperty
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from thlib.ui.icon_font import qml_icon_bindings

ROOT = Path(__file__).resolve().parents[1]


def items(root):
    yield root
    for child in root.childItems():
        yield from items(child)


def surface_radius(control):
    radius = control.property("radius")
    if radius is not None:
        return radius
    background = QQmlProperty(control, "background").read()
    if background is not None and background.property("radius") is not None:
        return background.property("radius")
    return next(item.property("radius") for item in items(control)
        if item.property("radius") is not None
        and item.width() >= control.width() - 4 and item.height() >= control.height() - 4)


class ServiceButtonShapesTests(unittest.TestCase):
    def test_service_shapes_and_main_chrome_across_themes_and_input(self):
        app = gui_test_application()
        engine = QQmlEngine()
        for name, value in qml_icon_bindings(ROOT, app).items():
            engine.rootContext().setContextProperty(name, value)
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(ROOT / "tests/fixtures/frame_controls/ServiceButtonShapes.qml")))
        self.assertTrue(component.isReady(), [error.toString() for error in component.errors()])
        records = json.loads((ROOT / "tests/fixtures/frame_service_buttons.json").read_text())
        window = component.createWithInitialProperties({"records": records})
        self.assertIsNotNone(window)
        results = []
        try:
            for style in ("md3", "material5", "fluent"):
                window.setProperty("styleName", style)
                for dark in (True, False):
                    window.setProperty("dark", dark)
                    for width in (320, 800):
                        window.resize(width, 650)
                        frame(window)
                        # Cases reuse controls: wait past their real duplicate-input guard.
                        guard = max((item.property("duplicateWindow") or 0 for item in items(window.contentItem())), default=0)
                        QTest.qWait(guard + 1)
                        ids = ["mainClose", "mainSave"] + [record["id"] for record in records] + ["serviceCount", "serviceFilter", "serviceSummary", "serviceReaction"]
                        for name in ids:
                            control = next(item for item in items(window.contentItem()) if item.objectName() == name)
                            expected = name.startswith("main")
                            radius = min(control.height() / 2, surface_radius(control))
                            self.assertEqual(radius, control.height() / 2 if expected else 4, (style, dark, name))
                            point = control.mapToScene(QPointF(control.width()/2,control.height()/2)).toPoint()
                            before = len(window.property("events").toVariant())
                            QTest.mouseMove(window, point)
                            QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, point)
                            self.assertEqual(min(control.height()/2,surface_radius(control)), radius)
                            QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, point)
                            frame(window)
                            self.assertEqual(len(window.property("events").toVariant()), before + (name != "serviceDisabled"), name)
                            target = control
                            if name == "serviceCount":
                                target = next(item for item in items(control) if item.objectName() == "itemCountCompactButton")
                            elif name == "serviceSummary":
                                target = next(item for item in items(control) if item.objectName() == "summaryChipAction")
                            elif name == "serviceReaction":
                                target = next(item for item in items(control) if item.objectName() == "reactionChipAction")
                            target.forceActiveFocus()
                            if name != "serviceDisabled":
                                before = len(window.property("events").toVariant())
                                QTest.keyClick(window, Qt.Key_Space)
                                frame(window)
                                self.assertEqual(len(window.property("events").toVariant()), before + 1, name)
                            position = control.mapToScene(QPointF())
                            results.append(dict(style=style,dark=dark,width=width,id=name,
                                x=position.x(),y=position.y(),controlWidth=control.width(),height=control.height(),radius=radius))
                        if os.environ.get("SERVICE_BUTTON_CAPTURE"):
                            out = Path(os.environ["SERVICE_BUTTON_CAPTURE"])
                            out.mkdir(parents=True,exist_ok=True)
                            window.grabWindow().save(str(out/f"native-{style}-{dark}-{width}.png"))
            self.assertEqual(warnings, [])
            if os.environ.get("SERVICE_BUTTON_CAPTURE"):
                (out/"native.json").write_text(json.dumps(results),encoding="utf-8")
        finally:
            window.close()
            window.deleteLater()
            app.processEvents()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
