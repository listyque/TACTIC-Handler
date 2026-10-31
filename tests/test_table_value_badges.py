"""Column XML presentation roundtrip and actual native passive value scenes."""
import os
from pathlib import Path
import unittest
from xml.etree import ElementTree

import tests.test_frame_table as frames
from tests.test_columns_table_view import _Application, _SType, _TableController
from thlib.ui.columns_editor import ColumnsEditorController
from thlib.ui.icon_font import qml_icon_bindings
from PySide6.QtGui import QFontDatabase


class TableValueBadges(unittest.TestCase):
    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item

    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()
        for font in ('segoeui.ttf', 'seguisb.ttf'):
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/' + font)

    def test_column_icon_style_roundtrip_preserves_custom_xml(self):
        controller = ColumnsEditorController(_Application(_SType()))
        source = '<config><!--keep--><table><element name="duration" custom="keep"><display widget="hidden_row"><icon>FAS_CUBE</icon><option>keep</option></display></element></table></config>'
        row = controller.catalog_wizard(source)['elements'][0]
        self.assertEqual(row['valueIcon'], 'FAS_CUBE')
        for field, value in [('valueIcon', 'FAS_CLOCK'), ('valueStyle', 'badge')]:
            source = controller.update_catalog_wizard(source, row['path'], field, value)
        row = controller.catalog_wizard(source)['elements'][0]
        self.assertEqual((row['valueIcon'], row['valueStyle']), ('FAS_CLOCK', 'badge'))
        element = ElementTree.fromstring(source).find('table/element')
        self.assertEqual(element.get('custom'), 'keep')
        self.assertEqual(element.findtext('display/icon'), 'FAS_CUBE')
        self.assertEqual(element.findtext('display/option'), 'keep')
        self.assertIn('<!--keep-->', source)
        cleared = controller.update_catalog_wizard(source, row['path'], 'valueIcon', '')
        self.assertEqual(controller.catalog_wizard(cleared)['elements'][0]['valueIcon'], '')
        for field,value in [('valueIcon','<script>'),('valueStyle','unknown')]:
            self.assertEqual(controller.update_catalog_wizard(source,row['path'],field,value), '')

    def test_duration_and_configured_text_use_passive_shared_badges(self):
        props = dict(controller=_TableController(), columnsController=None,
            userModel=None,nodeId='A',kind='text',cell={'text':'2 Minutes'},
            textValue='2 Minutes',columnIndex=1,previewActive=False,previewUrl='',
            previewRevealed=False,title='Duration',accent='#607d8b',comments=0,
            tasks=0,displayOptions={},fieldName='duration')
        window,view=self.create('TacticTableCellDisplay.qml',props,width=180,height=58,
            context=qml_icon_bindings(Path(__file__).resolve().parents[1]))
        label=self.item(view,'tableValueLabel')
        self.assertEqual(label.property('text'),'2 Minutes')
        self.assertEqual(self.item(view,'tableValueIcon').property('name'),'clock')
        badge=self.item(view,'tableValueBadge')
        self.assertLessEqual(badge.x()+badge.width(),view.width())
        view.setWidth(80)
        window.resize(80,58)
        frames.frame(window)
        self.assertGreaterEqual(badge.x(),0)
        self.assertLessEqual(badge.x()+badge.width(),80)
        view.setWidth(180)
        window.resize(180,58)
        frames.frame(window)
        output=os.environ.get('TABLE_DISCLOSURE_OUTPUT')
        if output:
            Path(output).mkdir(parents=True,exist_ok=True)
            window.setColor(view.property('theme').property('workspace'))
            frames.frame(window)
            window.grabWindow().save(str(Path(output)/'native-duration.png'))
        view.setProperty('fieldName','name')
        view.setProperty('displayOptions',{'value_icon':'FAS_CUBE','value_style':'badge'})
        frames.frame(window)
        self.assertEqual(self.item(view,'tableValueIcon').property('name'),'FAS_CUBE')
        view.setProperty('displayOptions',{'value_style':'text','value_icon':''})
        frames.frame(window)
        self.assertFalse(any(item.objectName()=='tableValueBadge' for item in frames._visual_items(view)))


if __name__ == '__main__':
    unittest.main()
