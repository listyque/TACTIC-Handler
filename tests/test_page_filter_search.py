"""Native house search input, live conditions and stale suggestion ownership."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from PySide6.QtCore import QObject, Signal, Slot, Qt, QPointF
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtGui import QInputMethodEvent
from tests import test_custom_layout as fixture
from tests import test_frame_table as frames
from tests.test_columns_table_view import _TableController, _TableColumns
from thlib.ui.table.custom_layout import CustomLayoutController


class Services(fixture.Services):
    filterSuggestionsReady = Signal(str, 'QVariantList', str)

    @Slot('QVariantMap', str)
    def request_filter_suggestions(self, query, request):
        self.filterSuggestionsReady.emit(request, [{'name':'status','value':'In Progress'}], '')


class Worker(QObject):
    result=Signal(object)
    error=Signal(object)
    settled=Signal(object)
    def __init__(self, operation):
        super().__init__();self.operation=operation;self.cancelled=False
    def start(self): pass
    def cancel(self): self.cancelled=True


class PageFilterSearch(unittest.TestCase):
    create=frames.FrameTableTests.create
    close=frames.FrameTableTests.close
    item=frames.FrameTableTests.item
    click=frames.FrameTableTests.click

    @classmethod
    def setUpClass(cls): cls.app=frames.gui_test_application()

    def test_native_search_suggestions_typed_submit_and_removal(self):
        def type_text(text):
            event = QInputMethodEvent(); event.setCommitString(text); self.app.sendEvent(window, event)
        services=Services(dict(layoutView='dashboard.search',layoutNodes=[],layoutFilters=[
            dict(name='status',title='Status',dataType='text',relation='=',value='',enabled=False),
            dict(name='amount',title='Amount',dataType='numeric',relation='>=',value=0,enabled=False)]))
        window,view=self.create('features/table/CustomLayoutView.qml',dict(services=services,
            controller=_TableController(),columnsController=_TableColumns(),users=None,administration=None),width=800,height=400)
        field=self.item(view,'pageFilterSearch')
        self.click(window,field);type_text('sta');frames.frame(window)
        for _ in range(50):
            QTest.qWait(10)
            if field.property('popupOpen'):break
        self.assertTrue(field.property('popupOpen'), (field.property('activeFocus'), field.property('errorText'), field.property('suggestions')))
        QTest.keyClick(window,Qt.Key_Down);frames.frame(window)
        popup = field.findChild(QObject, 'pageFilterSuggestionsPopup')
        self.assertEqual(popup.property('currentIndex'), 0)
        accepted = QSignalSpy(field.suggestionAccepted)
        QTest.keyClick(window,Qt.Key_Return);frames.frame(window)
        self.assertEqual(accepted.count(), 1, (field.property('activeFocus'), popup.property('visible'), popup.property('currentIndex'), popup.recordAt(0).toVariant(), field.property('errorText')))
        self.assertEqual(field.property('text'),'Status: ', field.property('errorText'))
        for _ in range(50):
            QTest.qWait(10)
            if field.property('popupOpen'):break
        QTest.keyClick(window,Qt.Key_Down);QTest.keyClick(window,Qt.Key_Return);frames.frame(window)
        self.assertEqual(services.events[-1]['values']['status'],dict(enabled=True,value='In Progress'))
        for _ in range(50):
            QTest.qWait(10)
            if not field.property('popupOpen'):break
        self.click(window,self.item(view,'pageRuntimeRemove_status'))
        self.assertFalse(services.events[-1]['values']['status']['enabled'])
        self.click(window,field);type_text('Amount: 0');QTest.keyClick(window,Qt.Key_Return);frames.frame(window)
        self.assertEqual(services.events[-1]['values']['amount'],dict(enabled=True,value=0))
        window.resize(320,400);view.setWidth(320);frames.frame(window)
        chip=self.item(view,'pageRuntimeRemove_amount')
        self.assertLessEqual(chip.mapToScene(QPointF()).x()+chip.width(),308)
        self.click(window,field);type_text('Pro')
        for _ in range(100):
            QTest.qWait(10)
            if popup.property('opened'):break
        row=self.item(popup.property('contentItem'),'pageFilterSuggestionRow_0')
        self.click(window,row)
        self.assertEqual(services.events[-1]['values']['status'],dict(enabled=True,value='In Progress'))

    def test_old_results_and_closed_owner_cannot_publish_suggestions(self):
        from thlib.environment import env_inst
        services=Services({});services._document=dict(layoutView='dashboard.search',targetSearchKey='sthpw/project?code=one')
        services._document_generation=0;services._nested_scopes={};services._nested_changed=lambda:None
        owner=CustomLayoutController(services);owner.context={'project':'one'}
        workers=[]
        def add(operation):
            worker=Worker(operation);workers.append(worker);return worker
        pool=SimpleNamespace(is_stopped=False,add_task=add)
        with patch.object(env_inst,'server_pool',pool),patch('thlib.tactic_classes.server_start',return_value=SimpleNamespace(execute_cmd=lambda *_:None)):
            spy=QSignalSpy(owner.filterSuggestionsReady)
            owner.request_filter_suggestions({'field':'status','text':'old'},'one')
            owner.request_filter_suggestions({'field':'status','text':'new'},'two')
            self.assertTrue(workers[0].cancelled);self.assertEqual(len(workers),1)
            workers[0].result.emit({'info':{'filterSuggestions':[{'name':'status','value':'old'}]}})
            workers[0].settled.emit(workers[0]);QTest.qWait(20)
            self.assertEqual(spy.count(),0);self.assertEqual(len(workers),2)
            workers[1].result.emit({'info':{'filterSuggestions':[{'name':'status','value':'new'}]}});QTest.qWait(10)
            self.assertEqual(spy.at(0)[0],'two')
            owner.close();self.assertTrue(workers[1].cancelled)
            workers[1].result.emit({'info':{'filterSuggestions':[]}});workers[1].settled.emit(workers[1]);QTest.qWait(10)
            self.assertEqual(spy.count(),1)
