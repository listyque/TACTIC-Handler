"""Synthetic editor preview renders and edits layout geometry without records."""
import os
import unittest

os.environ.setdefault('QSG_RENDER_LOOP', 'basic')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from shiboken6 import getCppPointer
from tests import test_nested_layout_links as nested
from tests.test_columns_table_view import _visual_items
from tests.profile_ui_responsiveness import frame

XML = '<config><sample_view layout="sobject-layout"><element name="title"><display class="title"><bind>record.name</bind></display></element><element name="artifact" search_type="demo/artifact" row="2"><display class="view"><view>artifact_card</view></display></element></sample_view></config>'

def layout():
    def element(name, kind, **values):
        return dict(name=name,kind=kind,options=dict(bind='record.name'),parent='',variant='all',when=[],hidden=False,
            row=1,column=1,span=12,rows=1,columns=12,height=40,role='',tag='div',flow='grid',align='stretch',tone='normal',**values)
    return dict(collection='grid',flow='grid',columns=12,elements=[element('title','title'),
        element('artifact','view',search_type='demo/artifact',widget_layout=dict(collection='grid',flow='grid',columns=12,
            elements=[element('inner','title')]))])


class SampleDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nested.NestedLayoutLinks.setUpClass()

    def setUp(self):
        self.fixture=nested.NestedLayoutLinks()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.native=self.fixture.native
        self.host=self.fixture.host
        self.host._draft_timer.stop()
        self.host._view='sample_view'
        self.host._configuration=self.fixture.config('sample_view',XML,7)
        self.host._loaded_scope=('demo','demo/asset','sample_view')
        self.host._xml=self.host._baseline=XML
        self.host._parse()
        self.host._sample_items=[]
        self.host._live_interface=dict(table=dict(item_layout=layout()))
        self.host.stateChanged.emit()
        for _ in range(8):
            frame(self.native.window)
            if any(item.objectName()=='layoutSampleScroll' and item.isVisible() for item in _visual_items(self.native.window.contentItem())):
                break
        self.assertEqual(self.native.fixture.warnings,[])

    def model(self):
        return self.native.item('administrationLayoutEditor').property('frameModel').toVariant()

    def test_empty_preview_is_selectable_and_only_geometry_changes_the_draft(self):
        self.assertIn('Sample data',self.native.item('layoutPreviewHeading').property('text'))
        self.assertIsNotNone(self.native.item('layoutSampleScroll'))
        sample=self.model()['samplePreview']
        self.assertEqual(sample['title'],'Example item')
        self.assertNotIn('__search_key__',sample['record'])
        self.assertEqual(self.host._sample_items,[])
        self.assertFalse(self.host.dirty)
        self.native.click('canvasTarget_title')
        handle=self.native.item('canvasHandle_se')
        start=handle.mapToScene(QPointF(handle.width()/2,handle.height()/2)).toPoint()
        QTest.mousePress(self.native.window,Qt.LeftButton,Qt.NoModifier,start)
        QTest.mouseMove(self.native.window,start+QPointF(0,20).toPoint(),20)
        QTest.mouseRelease(self.native.window,Qt.LeftButton,Qt.NoModifier,start+QPointF(0,20).toPoint())
        frame(self.native.window)
        self.assertTrue(self.host.dirty)
        self.assertNotIn('Example item',self.host._xml)
        self.fixture.write.assert_not_called()
        self.assertEqual(self.native.fixture.warnings,[])

    def test_selected_missing_type_uses_sample_without_recreating_real_preview(self):
        real=next(item for item in _visual_items(self.native.window.contentItem()) if item.objectName()=='searchResultsListView')
        pointer=getCppPointer(real)[0]
        self.host._sample_items=[dict(kind='object',title='Real asset',record={'__search_key__':'demo/asset?code=A','name':'Real asset'})]
        self.host.stateChanged.emit()
        frame(self.native.window)
        self.assertIsNone(self.model()['samplePreview'])
        self.native.click('layoutElement_artifact')
        self.assertEqual(self.model()['samplePreview']['search_type'],'demo/artifact')
        self.assertIsNotNone(self.native.item('canvasTarget_artifact'))
        self.native.click('layoutElement_title')
        self.assertIsNone(self.model()['samplePreview'])
        retained=next(item for item in _visual_items(self.native.window.contentItem()) if item.objectName()=='searchResultsListView')
        self.assertEqual(getCppPointer(retained)[0],pointer)
        self.assertFalse(self.host.dirty)
        self.fixture.write.assert_not_called()
        self.assertEqual(self.native.fixture.warnings,[])

    def test_sample_survives_preview_unload_and_xml_page_switch(self):
        configuration=self.host._configuration
        interface=self.host._live_interface
        self.host._configuration=None
        self.host._live_interface=None
        self.host.stateChanged.emit()
        frame(self.native.window)
        self.host._configuration=configuration
        self.host._live_interface=interface
        self.host.stateChanged.emit()
        for _ in range(8):
            frame(self.native.window)
            if any(item.objectName()=='layoutSampleScroll' and item.isVisible() for item in _visual_items(self.native.window.contentItem())):
                break
        self.native.choose_page('layoutPages','xml')
        self.native.choose_page('layoutPages','design')
        for _ in range(8):
            frame(self.native.window)
            if any(item.objectName()=='layoutSampleScroll' and item.isVisible() for item in _visual_items(self.native.window.contentItem())):
                break
        self.assertIsNotNone(self.native.item('layoutSampleScroll'))
        self.assertFalse(self.host.dirty)
        self.assertEqual(self.native.fixture.warnings,[])


if __name__=='__main__':
    unittest.main()
