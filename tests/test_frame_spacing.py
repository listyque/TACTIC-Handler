"""Actual house-control bounds for the shared spacing contract."""
import json
import os
from pathlib import Path
import unittest

from PySide6.QtCore import QMetaObject, QPointF, QObject
from PySide6.QtGui import QFontDatabase
from tests import test_frame_table as fixture

FIELDS = [
    dict(kind='Heading', id='general', title='General'),
    dict(kind='Field', id='name', title='Name', description='Object name',
         props=dict(text='Robot Arm')),
    dict(kind='Switch', id='enabled', title='Enabled', props=dict(checked=True)),
    dict(kind='Area', id='description', title='Description', height=96, fullWidth=True),
    dict(kind='Button', id='apply', title='Apply', props=dict(action=dict(type='apply'))),
]


class FrameSpacingTests(unittest.TestCase):
    create = fixture.FrameTableTests.create
    close = fixture.FrameTableTests.close
    item = fixture.FrameTableTests.item
    click = fixture.FrameTableTests.click

    @classmethod
    def setUpClass(cls):
        cls.app = fixture.gui_test_application()
        for name in ('segoeui.ttf', 'segoeuib.ttf'):
            font = Path('C:/Windows/Fonts')/name
            if font.exists():
                assert QFontDatabase.addApplicationFont(str(font)) >= 0

    def test_form_edges_and_real_panel_dialog_insets(self):
        path = Path(__file__).parent/'fixtures/frame_spacing.qml'
        window, view = self.create(str(path.resolve()), dict(fields=FIELDS), width=800, height=600)
        for flag in ('clickAnimationsEnabled', 'hoverAnimationsEnabled', 'fadeAnimationsEnabled', 'popupAnimationsEnabled'):
            view.property('theme').setProperty(flag, False)
        measurements = []
        for style in ('md3', 'material5', 'fluent'):
            view.property('theme').setProperty('styleName', style)
            for dark in (True, False):
                view.property('theme').setProperty('dark', dark)
                for width in (320, 800):
                    window.resize(width, 600)
                    view.setWidth(width)
                    view.setProperty('mode', 'form')
                    fixture.frame(window)
                    card = self.item(view, 'section_general')
                    for name in ('nameLabel', 'enabledLabel', 'description', 'apply'):
                        item = self.item(view, name)
                        self.assertEqual(item.mapToItem(card, QPointF()).x(), 12)
                    button = self.item(view, 'apply')
                    self.assertEqual(card.height() - button.mapToItem(card, QPointF()).y() - button.height(), 12)
                    self.click(window, button)
                    self.assertEqual(view.property('lastEvent').toVariant()['type'], 'apply')
                    output = os.environ.get('FRAME_SPACING_CAPTURE')
                    if output and style == 'md3':
                        Path(output).mkdir(parents=True, exist_ok=True)
                        self.assertTrue(window.grabWindow().save(str(Path(output)/f'form-th-{width}-{dark}.png')))
                    view.setProperty('mode', 'panel')
                    fixture.frame(window)
                    panel = self.item(view, 'spacingPanel')
                    self.assertEqual(panel.property('padding'), 12)
                    row = self.item(view, 'spacingListRow')
                    content = row.property('contentItem')
                    self.assertGreaterEqual(row.height(), content.property('implicitHeight') + 24)
                    QMetaObject.invokeMethod(view, 'openDialog')
                    fixture.frame(window)
                    dialog = view.findChild(QObject, 'spacingDialog')
                    body = dialog.property('contentItem')
                    self.assertEqual(body.property('x'), 12)
                    self.assertEqual(body.property('y'), 52)
                    measurements.append(dict(style=style, dark=dark, width=width,
                        panelPadding=panel.property('padding'), dialogX=body.property('x'), dialogY=body.property('y')))
                    QMetaObject.invokeMethod(dialog, 'close')
        if os.environ.get('FRAME_SPACING_CAPTURE'):
            (Path(os.environ['FRAME_SPACING_CAPTURE'])/'native-bounds.json').write_text(json.dumps(measurements, indent=2), encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
