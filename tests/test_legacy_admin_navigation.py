"""Real portable administration navigation under Legacy and Stream modes."""
from pathlib import Path
import unittest

from PySide6.QtCore import QCoreApplication, QEvent, QUrl, Qt
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests.test_columns_table_view import _visual_items
from thlib.ui.icon_font import qml_icon_bindings

ROOT = Path(__file__).resolve().parents[1]


class LegacyAdminNavigationTests(unittest.TestCase):
    def test_native_navigation_filters_all_responsive_forms(self):
        app = gui_test_application()
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
        for name, value in qml_icon_bindings(ROOT, app).items():
            engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(engine)
        component.setData(b'''
import QtQuick
import "." as TH
import "tactic_frame" as Frame
import "tactic_frame/features/administration/administration.ui.mjs" as UI
Window {
    id: root
    width: 1400; height: 1100; visible: true
    property bool streamMode: false
    property bool collapsed: false
    property string lastSection: ""
    property var model: ({section:"groups", project:"demo", projects:[],
        locked:false, busy:false, drafts:[], streamApi:streamMode})
    property var records: UI.availableSections(model)
    TH.Theme {id: appTheme; dark:true; clickAnimationsEnabled:false; hoverAnimationsEnabled:false}
    Component {id: blankPort; Item {}}
    Frame.FrameView {
        anchors.fill: parent; theme: appTheme
        scene: UI.describe(root.model, {collapsed:root.collapsed}, width, height, "en")
        models: ({sections:root.records})
        views: ({content:blankPort, projectPicker:blankPort, toolbar:blankPort})
        describeRow: (list, record) => UI.row(list, record, root.model, {collapsed:root.collapsed}, "en")
        onEvent: action => {if (action.type === "section") root.lastSection = action.value}
    }
}
''', QUrl.fromLocalFile(str(ROOT / 'thlib/ui/qml/LegacyAdminNavigationHarness.qml')))
        self.assertTrue(component.isReady(), [error.toString() for error in component.errors()])
        window = component.create()
        self.assertIsNotNone(window, [error.toString() for error in component.errors()])
        try:
            for stream in (False, True):
                window.setProperty('streamMode', stream)
                for width, collapsed in ((1400, False), (1400, True), (700, False)):
                    window.resize(width, 1100)
                    window.setProperty('collapsed', collapsed)
                    frame(window)
                    self.assertEqual(warnings, [])
                    ids = [row['id'] for row in window.property('records').toVariant()]
                    for identity in ('dashboards', 'layouts'):
                        self.assertEqual(identity in ids, stream)
                    if width >= 1000:
                        names = {item.objectName() for item in _visual_items(window.contentItem())}
                        self.assertIn('adminSection_groups', names)
                        for identity in ('dashboards', 'layouts'):
                            self.assertEqual('adminSection_' + identity in names, stream)
                        group = next(item for item in _visual_items(window.contentItem())
                                     if item.objectName() == 'adminSection_groups')
                        window.setProperty('lastSection', '')
                        QTest.mouseClick(window, Qt.LeftButton,
                                         pos=group.mapToScene(group.boundingRect().center()).toPoint())
                        frame(window)
                        self.assertEqual(window.property('lastSection'), 'groups')
            self.assertEqual(warnings, [])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
