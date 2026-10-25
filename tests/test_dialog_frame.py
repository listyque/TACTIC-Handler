"""Shared dialog caption and visible frame in the actual native control."""
import json
import os
from pathlib import Path
import unittest

from PySide6.QtCore import QObject, QMetaObject, Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlExpression
from PySide6.QtTest import QTest

from tests import test_frame_script_tools as fixture
from tests.profile_ui_responsiveness import frame


class DialogFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ScriptToolsTests.setUpClass()

    def test_caption_frame_and_escape_in_all_themes(self):
        surface = fixture.ScriptToolsTests()
        surface.setUp()
        self.addCleanup(surface.doCleanups)
        if os.name == 'nt':
            QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR'])/'Fonts/segoeui.ttf'))
            QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR'])/'Fonts/seguisb.ttf'))
            surface.app.setFont(QFont('Segoe UI'))
        window = QQuickWindow()
        window.resize(640, 440)
        surface.windows.append(window)
        window.show()
        dialog = surface.create(fixture.QML/'controls/Dialog.qml', dict(
            theme=surface.theme, parent=window.contentItem(), title='External agent',
            x=50, y=50, width=540, height=340, modal=True))
        for style in ('md3', 'material5', 'fluent'):
            for dark in (True, False):
                surface.theme.setProperty('style', style)
                surface.theme.setProperty('dark', dark)
                QMetaObject.invokeMethod(dialog, 'open')
                frame(window)
                header = dialog.findChild(QObject, 'dialogTitleBar')
                title = dialog.findChild(QObject, 'dialogTitle')
                self.assertEqual(header.property('implicitHeight'), 40)
                self.assertEqual(title.property('font').pixelSize(), 13)
                self.assertEqual(title.property('x'), 12)
                panel = dialog.findChild(QObject, 'dialogSurface')
                border_width = QQmlExpression(surface.engine.rootContext(), panel, 'border.width').evaluate()[0]
                border_color = QQmlExpression(surface.engine.rootContext(), panel, 'border.color').evaluate()[0]
                self.assertEqual(border_width, 1)
                self.assertEqual(border_color, surface.theme.property('outline'))
                header_color = header.childItems()[0].property('color')
                self.assertEqual(header_color, surface.theme.property('topBar'))
                if style == 'md3' and dark and os.environ.get('FRAME_WINDOW_CAPTURE'):
                    output = Path(os.environ['FRAME_WINDOW_CAPTURE'])
                    output.mkdir(parents=True, exist_ok=True)
                    window.grabWindow().copy(50, 50, 540, 340).save(str(output/'native-dialog.png'))
                    (output/'native-dialog.json').write_text(json.dumps(dict(
                        headerHeight=header.property('implicitHeight'), titleSize=title.property('font').pixelSize(),
                        borderWidth=border_width, border=border_color.name(), header=header_color.name()),indent=2),encoding='utf-8')
                window.requestActivate()
                QTest.keyClick(window, Qt.Key_Escape)
                frame(window)
                self.assertFalse(dialog.property('visible'))
        self.assertFalse(surface.warnings, surface.warnings)


if __name__ == '__main__':
    unittest.main()
