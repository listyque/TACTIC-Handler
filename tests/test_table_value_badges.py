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
        for field, value in [('valueIcon', 'FAS_CLOCK'), ('valueStyle', 'badge'), ('valueTextStyle', 'heading')]:
            source = controller.update_catalog_wizard(source, row['path'], field, value)
        row = controller.catalog_wizard(source)['elements'][0]
        self.assertEqual((row['valueIcon'], row['valueStyle']), ('FAS_CLOCK', 'badge'))
        self.assertEqual(row['valueTextStyle'], 'heading')
        element = ElementTree.fromstring(source).find('table/element')
        self.assertEqual(element.get('custom'), 'keep')
        self.assertEqual(element.findtext('display/icon'), 'FAS_CUBE')
        self.assertEqual(element.findtext('display/option'), 'keep')
        self.assertIn('<!--keep-->', source)
        cleared = controller.update_catalog_wizard(source, row['path'], 'valueIcon', '')
        self.assertEqual(controller.catalog_wizard(cleared)['elements'][0]['valueIcon'], '')
        for field,value in [('valueIcon','<script>'),('valueStyle','unknown'),('valueTextStyle','huge')]:
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
        view.setProperty('cell', {'text': 'Episode 02 — Repair'})
        for style, size, weight in [('heading', 16, 600), ('small', 12, 400), ('', 13, 400)]:
            view.setProperty('displayOptions', {'value_text_style': style})
            frames.frame(window)
            label=next(item for item in frames._visual_items(view)
                if item.property('text')=='Episode 02 — Repair' and item.property('lineCount') is not None)
            self.assertEqual(label.property('font').pixelSize(), size)
            self.assertEqual(label.property('font').weight(), weight)
            if output and style:
                window.grabWindow().save(str(Path(output)/('native-'+style+'.png')))
        view.setProperty('displayOptions', {'value_icon':'FAS_CUBE', 'value_style':'badge', 'value_text_style':'heading'})
        frames.frame(window)
        self.assertEqual(self.item(view,'tableValueLabel').property('font').pixelSize(),16)

    def test_table_keeps_horizontal_dividers_and_column_text_hierarchy(self):
        from tests.test_columns_table_view import _TableColumns
        from thlib.ui.workspace_models.results import WorkspaceItemModel
        from thlib.ui.workspace_models.results_types import WorkspaceNode
        columns = _TableColumns()
        columns._columns = [
            dict(row=0,name='name',label='Name',width=240,kind='text',dataType='text',displayOptions={'value_text_style':'heading'}),
            dict(row=1,name='description',label='Description',width=360,kind='text',dataType='text',displayOptions={'value_text_style':'small'}),
        ]
        records = {
            'A': {'name':'Episode 02 — Repair','description':'The workshop repair sequence.'},
            'B': {'name':'Episode 03','description':'Arrival at the station.'},
        }
        columns.cell = lambda key, field: {'text':records[key][field], 'kind':'text'}
        model = WorkspaceItemModel()
        model.replace_nodes([
            WorkspaceNode(node_id='A',node_type='sobject',search_key='A',code='A',title='Episode 02 — Repair',values={'name':'Episode 02 — Repair','description':'The workshop repair sequence.'}),
            WorkspaceNode(node_id='B',node_type='sobject',search_key='B',code='B',title='Episode 03',values={'name':'Episode 03','description':'Arrival at the station.'}),
        ])
        window,view=self.create('SearchResultTable.qml',dict(controller=_TableController(),columnsController=columns,resultModel=model,userModel=None,presentationActive=True,scrollColumns=True),width=800,height=220,
            context=qml_icon_bindings(Path(__file__).resolve().parents[1]))
        from PySide6.QtTest import QTest
        from time import monotonic
        deadline=monotonic()+2
        while monotonic()<deadline and not any(item.property('text')=='Episode 02 — Repair' and item.property('lineCount') is not None for item in frames._visual_items(view)):
            QTest.qWait(10)
        self.assertTrue(any(item.property('text')=='Episode 02 — Repair' and item.property('lineCount') is not None for item in frames._visual_items(view)),str([(item.objectName(),item.property('text')) for item in frames._visual_items(view)]))
        labels=[item for item in frames._visual_items(view) if item.property('lineCount') is not None]
        name=next(item for item in labels if item.property('text')=='Episode 02 — Repair')
        description=next(item for item in labels if item.property('text')=='The workshop repair sequence.')
        self.assertEqual(name.property('font').pixelSize(),16)
        self.assertEqual(description.property('font').pixelSize(),12)
        surfaces=[item for item in frames._visual_items(view) if item.objectName()=='searchResultTableRowSurface']
        self.assertEqual(len(surfaces),2)
        for surface in surfaces:
            self.assertEqual(surface.property('borderWidth'),0)
            self.assertTrue(any(item.height()==1 and item.width()>=view.width() and item.property('color')==view.property('theme').property('tableDivider') for item in surface.parentItem().childItems()))
        output=os.environ.get('TABLE_DISCLOSURE_OUTPUT')
        if output:
            window.setColor(view.property('theme').property('workspace'))
            for setting in ('hoverAnimationsEnabled','clickAnimationsEnabled','fadeAnimationsEnabled','popupAnimationsEnabled'):
                view.property('theme').setProperty(setting,False)
            from PySide6.QtCore import QPoint
            QTest.mouseMove(window,QPoint(-10,-10))
            view.forceActiveFocus()
            frames.frame(window)
            window.grabWindow().save(str(Path(output)/'native-table.png'))
            view.property('theme').setProperty('dark',False)
            window.setColor(view.property('theme').property('workspace'))
            frames.frame(window)
            self.assertEqual(name.property('font').pixelSize(),16)
            window.grabWindow().save(str(Path(output)/'native-table-light.png'))


if __name__ == '__main__':
    unittest.main()
