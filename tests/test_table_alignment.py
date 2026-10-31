"""Plain values and status chips share their column heading's alignment."""
import unittest
import os,json
from pathlib import Path
from PySide6.QtCore import Qt, QPointF, Slot
from PySide6.QtQml import QQmlExpression, QQmlEngine
from tests import test_frame_table as frames
from tests.test_columns_table_view import _TableController, _TableColumns, _visual_items
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode

def alignment(item):
    return QQmlExpression(QQmlEngine.contextForObject(item),item,'Number(horizontalAlignment)').evaluate()[0]


class Columns(_TableColumns):
    @Slot(str, str, result='QVariantMap')
    def cell(self, key, column):
        return dict(text='Оплачен', kind='text', statusColor='#008000')


class TableAlignment(unittest.TestCase):
    create=frames.FrameTableTests.create
    close=frames.FrameTableTests.close
    item=frames.FrameTableTests.item

    @classmethod
    def setUpClass(cls):cls.app=frames.gui_test_application()

    def test_heading_and_status_share_center_on_resize_and_explicit_alignment(self):
        columns=Columns()
        columns._columns=[dict(row=0,name='status',label='Status',kind='text',width=160,hideOrder=0)]
        model=WorkspaceItemModel()
        model.replace_nodes([WorkspaceNode(node_id='task',node_type='sobject',search_key='task',code='Task',title='Task')])
        window,table=self.create('SearchResultTable.qml',dict(controller=_TableController(),columnsController=columns,resultModel=model,presentationActive=True),width=800,height=200)
        bounds={}
        for width in (800,320):
            window.resize(width,200);table.setWidth(width);frames.frame(window)
            label=self.item(table,'tableColumnHeaderLabel_status')
            badge=self.item(table,'tableStatusBadge')
            center=label.mapToScene(QPointF(label.width()/2,0)).x()
            self.assertEqual(alignment(label),Qt.AlignHCenter.value)
            self.assertAlmostEqual(badge.mapToScene(QPointF(badge.width()/2,0)).x(),center,delta=.5)
            bounds[str(width)]={'headingCenter':center,'badgeCenter':badge.mapToScene(QPointF(badge.width()/2,0)).x()}
            if os.getenv('TABLE_ALIGNMENT_CAPTURE'):
                folder=Path(os.environ['TABLE_ALIGNMENT_CAPTURE']);folder.mkdir(parents=True,exist_ok=True)
                window.grabWindow().save(str(folder/f'native-{width}.png'))
        if os.getenv('TABLE_ALIGNMENT_CAPTURE'):
            (folder/'native-bounds.json').write_text(json.dumps(bounds,indent=2))
        for align,expected in (('left',Qt.AlignLeft),('right',Qt.AlignRight)):
            columns._columns[0]['displayOptions']={'justify':align};columns.stateChanged.emit();frames.frame(window)
            self.assertEqual(alignment(self.item(table,'tableColumnHeaderLabel_status')),expected.value)
            badge=self.item(table,'tableStatusBadge')
            self.assertAlmostEqual(badge.x() if align=='left' else badge.parentItem().width()-badge.x()-badge.width(),14,delta=.5)

    def test_plain_label_centers_wrapped_text_and_preserves_explicit_alignment(self):
        for options,expected in (({},Qt.AlignHCenter),({'align':'left'},Qt.AlignLeft),({'justify':'right'},Qt.AlignRight)):
            window,cell=self.create('TacticTableCellDisplay.qml',dict(controller=_TableController(),columnsController=None,userModel=None,nodeId='task',kind='text',cell={'text':'A long label that wraps'},textValue='',columnIndex=0,previewActive=False,previewUrl='',previewRevealed=False,title='',accent='#607d8b',comments=0,tasks=0,displayOptions=options),width=120,height=80)
            label=next(item for item in _visual_items(cell) if item.property('text')=='A long label that wraps')
            self.assertEqual(alignment(label),expected.value)
            self.assertEqual(label.property('leftPadding'),label.property('rightPadding'))
