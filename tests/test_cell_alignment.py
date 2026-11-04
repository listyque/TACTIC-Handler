"""Column alignment XML and real native text/decorated/action geometry."""
import os
from pathlib import Path
import unittest
from xml.etree import ElementTree

from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QFontDatabase
from PySide6.QtQml import QQmlEngine, QQmlExpression
import tests.test_frame_table as frames
from tests.test_columns_table_view import _Application, _SType, _TableController
from thlib.ui.columns_editor import ColumnsEditorController
from thlib.ui.icon_font import qml_icon_bindings


class CellAlignmentTests(unittest.TestCase):
    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item

    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()
        for font in ('segoeui.ttf', 'seguisb.ttf'):
            QFontDatabase.addApplicationFont('C:/Windows/Fonts/' + font)

    def test_wizard_preserves_legacy_alignment_custom_xml_and_validates(self):
        controller = ColumnsEditorController(_Application(_SType()))
        source = '<config><!--keep--><table><element name="description" custom="keep"><display widget="format"><justify>right</justify></display></element></table></config>'
        row = controller.catalog_wizard(source)['elements'][0]
        for align in ('left', 'center', 'right', ''):
            changed = controller.update_catalog_wizard(source, row['path'], 'valueAlign', align)
            self.assertTrue(changed)
            self.assertEqual(controller.catalog_wizard(changed)['elements'][0]['valueAlign'], align)
            element = ElementTree.fromstring(changed).find('table/element')
            self.assertEqual(element.get('value_align'), align)
            self.assertEqual(element.get('custom'), 'keep')
            self.assertEqual(element.findtext('display/justify'), 'right')
            self.assertIn('<!--keep-->', changed)
        for bad in ('justify', 'LEFT', 'left; color:red'):
            self.assertEqual(controller.update_catalog_wizard(source, row['path'], 'valueAlign', bad), '')
        self.assertIn('<justify>right</justify>', row['xml'])
        updated_xml = controller.update_catalog_wizard(
            source, row['path'], 'xml',
            '<element name="description" title="Custom Desc" width="220"><display class="tactic.ui.table.ExpressionElementWdg"><expression>@GET(.description)</expression></display></element>'
        )
        self.assertTrue(updated_xml)
        updated_row = controller.catalog_wizard(updated_xml)['elements'][0]
        self.assertEqual(updated_row['title'], 'Custom Desc')
        self.assertEqual(updated_row['width'], 220)
        self.assertEqual(updated_row['widget'], 'tactic.ui.table.ExpressionElementWdg')
        self.assertIn('<expression>@GET(.description)</expression>', updated_row['xml'])
        options = controller.widget_options_for(updated_row['widget'])
        self.assertEqual(len(options), 21)
        self.assertIn({'value': 'tactic.ui.table.ExpressionElementWdg', 'label': 'Expression'}, options)
        self.assertFalse(any(row['value'] == 'expression' for row in options))
        for bad_xml in ('', '<element/>', '<other name="x"/>', '<element name="x">broken'):
            self.assertEqual(controller.update_catalog_wizard(source, row['path'], 'xml', bad_xml), '')

    def props(self, **extra):
        return dict(controller=_TableController(), columnsController=None, userModel=None,
            nodeId='A', kind='text', cell={'text':'Mechanical robot arm — an episode asset with a long description.'},
            textValue='', columnIndex=1, previewActive=False, previewUrl='', previewRevealed=False,
            title='Robot Arm', accent='#607d8b', comments=0, tasks=0, displayOptions={}, **extra)

    def test_text_badge_preview_and_action_follow_content_alignment(self):
        window, view = self.create('TacticTableCellDisplay.qml', self.props(), width=240, height=100,
            context=qml_icon_bindings(Path(__file__).resolve().parents[1]))
        for align, expected in [('left', Qt.AlignLeft), ('center', Qt.AlignHCenter), ('right', Qt.AlignRight)]:
            view.setProperty('displayOptions', {'value_align':align})
            frames.frame(window)
            label = next(item for item in frames._visual_items(view)
                if item.isVisible() and item.property('lineCount') is not None and str(item.property('text') or '').startswith('Mechanical'))
            expression=QQmlExpression(QQmlEngine.contextForObject(label), label, 'Number(horizontalAlignment)')
            self.assertEqual(expression.evaluate()[0], int(expected))
            self.assertGreater(label.property('lineCount'), 1, str((label.width(), label.height(), label.property('text'), label.property('font').pixelSize())))
            output=os.environ.get('CELL_ALIGNMENT_OUTPUT')
            if output:
                Path(output).mkdir(parents=True, exist_ok=True)
                for dark in (True, False):
                    view.property('theme').setProperty('dark', dark)
                    window.setColor(view.property('theme').property('workspace'))
                    frames.frame(window)
                    window.grabWindow().save(str(Path(output)/('native-text-'+align+'-'+('dark' if dark else 'light')+'.png')))
        view.setProperty('displayOptions', {'justify':'right', 'value_align':''})
        frames.frame(window)
        self.assertEqual(expression.evaluate()[0], int(Qt.AlignRight))
        view.setProperty('fieldName', 'duration')
        view.setProperty('cell', {'text':'2 Minutes'})
        positions=[]
        for align in ('left', 'center', 'right'):
            view.setProperty('displayOptions', {'value_align':align})
            frames.frame(window)
            positions.append(self.item(view, 'tableValueBadge').mapToItem(view, QPointF()).x())
        self.assertLess(positions[0], positions[1])
        self.assertLess(positions[1], positions[2])
        view.setProperty('kind', 'thumbnail')
        for align in ('left', 'right'):
            view.setProperty('displayOptions', {'value_align':align})
            frames.frame(window)
            preview=self.item(view, 'tableCellPreview')
            self.assertAlmostEqual(preview.x() if align=='left' else view.width()-preview.x()-preview.width(), 8)
        view.setProperty('kind', 'checkin')
        frames.frame(window)
        action=self.item(view, 'tableCellCheckin')
        self.assertAlmostEqual(view.width()-action.x()-action.width(), 6)
        point=action.mapToScene(QPointF(action.width()/2, action.height()/2)).toPoint()
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
        frames.frame(window)
        self.assertEqual(view.property('controller').table_widget_actions[-1][0], 'checkin')

    def test_full_table_keeps_heading_alignment_independent(self):
        from tests.test_columns_table_view import _TableColumns
        from thlib.ui.workspace_models.results import WorkspaceItemModel
        from thlib.ui.workspace_models.results_types import WorkspaceNode
        text='Mechanical robot arm — an episode asset with a long description.'
        columns=_TableColumns()
        columns._columns=[dict(row=i,name='d'+str(i),label='Description',width=240,kind='text',dataType='text',displayOptions={'value_align':align})
            for i,align in enumerate(('left','center','right'))]
        columns.cell=lambda *_: {'text':text, 'kind':'text'}
        model=WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(node_id='A',node_type='sobject',search_key='A',code='A',title='Robot Arm',values={'d'+str(i):text for i in range(3)})])
        window,view=self.create('SearchResultTable.qml',dict(controller=_TableController(),columnsController=columns,resultModel=model,
            userModel=None,presentationActive=True,scrollColumns=True,selectable=False,rowHeight=100),width=820,height=170,
            context=qml_icon_bindings(Path(__file__).resolve().parents[1]))
        QTest.qWait(30)
        frames.frame(window)
        headings=[item for item in frames._visual_items(view) if item.objectName().startswith('tableColumnHeaderLabel_')]
        self.assertEqual(len(headings),3)
        for heading in headings:
            expression=QQmlExpression(QQmlEngine.contextForObject(heading),heading,'Number(horizontalAlignment)')
            self.assertEqual(expression.evaluate()[0],int(Qt.AlignHCenter))
        labels=sorted((item for item in frames._visual_items(view) if item.isVisible() and item.property('text')==text and item.property('lineCount') is not None),key=lambda item:item.mapToItem(view,QPointF()).x())
        self.assertEqual(len(labels),3)
        for label,align in zip(labels,(Qt.AlignLeft,Qt.AlignHCenter,Qt.AlignRight)):
            expression=QQmlExpression(QQmlEngine.contextForObject(label),label,'Number(horizontalAlignment)')
            self.assertEqual(expression.evaluate()[0],int(align))
        output=os.environ.get('CELL_ALIGNMENT_OUTPUT')
        if output:
            Path(output).mkdir(parents=True,exist_ok=True)
            view.forceActiveFocus()
            for dark in (True,False):
                view.property('theme').setProperty('dark',dark)
                window.setColor(view.property('theme').property('workspace'))
                frames.frame(window)
                window.grabWindow().save(str(Path(output)/('native-table-'+('dark' if dark else 'light')+'.png')))


if __name__ == '__main__':
    unittest.main()
