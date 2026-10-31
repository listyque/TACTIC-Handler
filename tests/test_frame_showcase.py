"""Real shipped showcase controls, local state and both palettes."""
import unittest
from PySide6.QtCore import Q_ARG, QMetaObject, Qt, QObject, QPointF, QCoreApplication, QEvent
from PySide6.QtTest import QTest
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from tests import test_frame_table as frames
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.source_editor import SourceEditorService
from tests.qt_application import run_native_windows_test


class FrameShowcaseTests(unittest.TestCase):
    item=frames.FrameTableTests.item
    click=frames.FrameTableTests.click

    def create(self, *args, **kwargs):
        window, view = frames.FrameTableTests.create(self, *args, **kwargs)
        window.requestActivate()
        QTest.qWait(20)
        self.app.processEvents()
        return window, view

    def close(self, window, view, engine, warnings, owners):
        frames.FrameTableTests.close(self, window, view, engine, warnings, owners)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()
        self.assertEqual(warnings, [])

    @classmethod
    def setUpClass(cls):
        cls.app=frames.gui_test_application()

    def send(self,view,event):
        self.assertTrue(QMetaObject.invokeMethod(view,'dispatch',Q_ARG('QVariant',event)))
        self.app.processEvents()

    def model(self,view):
        value=view.property('model')
        return value.toVariant() if hasattr(value,'toVariant') else value

    def edit(self, window, item, text):
        self.click(window, item)
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        event = QInputMethodEvent()
        event.setCommitString(text)
        QGuiApplication.sendEvent(item, event)
        frames.frame(window)

    def test_new_family_interactions_and_popup_lifecycle(self):
        if run_native_windows_test(self): return
        source = SourceEditorService()
        window, view = self.create('features/administration/ComponentShowcaseView.qml', dict(sourceEditor=source),
            width=1000, height=760, context=qml_icon_bindings(frames.QML.parents[2]))
        self.send(view, dict(type='family', value='search'))
        self.edit(window, self.item(view, 'sampleSearch'), 'Robot')
        self.assertEqual(self.model(view)['search'], 'Robot')
        QTest.qWait(40)
        frames.frame(window)
        suggestion = next((item for owner in QGuiApplication.topLevelWindows()
                           if hasattr(owner, 'contentItem') for item in frames._visual_items(owner.contentItem())
                           if item.objectName() == 'searchSuggestionRow_0' and item.isVisible()), None)
        self.assertIsNotNone(suggestion)
        point = suggestion.mapToScene(QPointF(suggestion.width()/2, suggestion.height()/2)).toPoint()
        QTest.mouseClick(suggestion.window(), Qt.LeftButton, Qt.NoModifier, point)
        frames.frame(window)
        self.assertEqual(self.model(view)['search'], 'Robot Arm')
        self.send(view, dict(type='family', value='tables'))
        frames.frame(window)
        self.edit(window, self.item(view, 'sampleCell_0:1'), 'Edited cell')
        self.assertEqual(self.model(view)['cells']['0:1'], 'Edited cell')
        self.send(view, dict(type='family', value='editors'))
        frames.frame(window)
        self.edit(window, self.item(view, 'scriptEditorSourceText'), 'print("local")')
        self.assertEqual(self.model(view)['editorText'], 'print("local")')
        self.send(view, dict(type='family', value='input-runtime'))
        self.click(window, self.item(view, 'sampleActivation'))
        self.assertEqual(self.model(view)['activations'], 1)
        device = QTest.createTouchDevice()
        activation = self.item(view, 'sampleActivation')
        point = activation.mapToScene(QPointF(activation.width()/2, activation.height()/2)).toPoint()
        QTest.touchEvent(window, device).press(0, point, window).commit()
        frames.frame(window)
        QTest.touchEvent(window, device).release(0, point, window).commit()
        frames.frame(window)
        self.assertEqual(self.model(view)['activations'], 2)
        self.edit(window, self.item(view, 'sampleIME'), 'Кириллица 日本語')
        self.assertEqual(self.model(view)['ime'], 'Кириллица 日本語')
        self.send(view, dict(type='family', value='popups'))
        self.click(window, self.item(view, 'sampleOpenDialog'))
        frames.frame(window)
        self.assertTrue(self.model(view)['dialogOpen'])
        self.click(window, self.item(window.contentItem(), 'sampleConfirmApply'))
        QTest.qWait(250)
        self.assertFalse(self.model(view)['dialogOpen'])
        self.assertEqual(self.model(view)['last'], 'accept')
        self.click(window, self.item(view, 'sampleOpenDialog'))
        self.send(view, dict(type='family', value='identity'))
        frames.frame(window)
        self.assertFalse(self.model(view)['dialogOpen'])

    def test_all_new_states_create_without_warnings(self):
        source = SourceEditorService()
        window, view = self.create('features/administration/ComponentShowcaseView.qml', dict(sourceEditor=source),
            width=620, height=760, context=qml_icon_bindings(frames.QML.parents[2]))
        for family in ['search','identity','menus','popups','feedback','tables','scroll-layout','previews',
                       'drag-files','editors','graphs','input-runtime','domain-fragments']:
            self.send(view, dict(type='family', value=family))
            for state in ['default','disabled','readonly','error','long','loading','empty','selected']:
                self.send(view, dict(type='state', value=state))
                frames.frame(window)
                self.assertFalse(window.grabWindow().isNull(), (family, state))

    def test_menu_graph_and_splitter_real_input(self):
        if run_native_windows_test(self): return
        source = SourceEditorService()
        window, view = self.create('features/administration/ComponentShowcaseView.qml', dict(sourceEditor=source),
            width=1000, height=760, context=qml_icon_bindings(frames.QML.parents[2]))
        self.send(view, dict(type='family', value='menus'))
        self.click(window, self.item(view, 'sampleMenu'))
        QTest.qWait(450)
        target = None
        observed = []
        for owner in QGuiApplication.topLevelWindows():
            if not hasattr(owner, 'contentItem'): continue
            for item in frames._visual_items(owner.contentItem()):
                if item.objectName() != 'actionMenuPrimaryTarget' or not item.isVisible(): continue
                record = item.parentItem().property('modelData')
                if hasattr(record, 'toVariant'): record = record.toVariant()
                observed.append((item.objectName(), record))
                if record and record.get('command') == 'toggle': target = item
        self.assertIsNotNone(target, str(observed))
        point = target.mapToScene(QPointF(target.width()/2, target.height()/2)).toPoint()
        QTest.mouseClick(target.window(), Qt.LeftButton, Qt.NoModifier, point)
        QTest.qWait(250)
        self.assertFalse(self.model(view)['menuChecked'])
        self.send(view, dict(type='family', value='graphs'))
        frames.frame(window)
        self.click(window, self.item(view, 'graphNode_a'))
        self.assertEqual(self.model(view)['graphSelected'], ['a'])
        QTest.keyClick(window, Qt.Key_Right)
        frames.frame(window)
        self.assertEqual(self.model(view)['graphPositions'][0]['nodeX'], 34)
        self.send(view, dict(type='family', value='scroll-layout'))
        frames.frame(window)
        splitter = self.item(view, 'sampleSplitter')
        self.click(window, splitter)
        before = self.model(view)['split']
        QTest.keyClick(window, Qt.Key_Right)
        frames.frame(window)
        self.assertGreater(self.model(view)['split'], before)

    def test_live_families_and_actual_input(self):
        source=SourceEditorService()
        window,view=self.create('features/administration/ComponentShowcaseView.qml',dict(sourceEditor=source),
            width=1000,height=760,context=qml_icon_bindings(frames.QML.parents[2]))
        models=self.item(view,'componentShowcase').property('models').toVariant()
        self.assertEqual([row['id'] for row in models['families'][:6]],
                         ['typography','colors','headers','icons','buttons','toggles'])
        for family in ['typography','headers','colors','icons','buttons','toggles','text-fields',
                       'choices','numbers','dates','user-choice','pickers','tabs','badges','lists','charts',
                       'search','identity','menus','popups','feedback','tables','scroll-layout','previews',
                       'drag-files','editors','graphs','input-runtime','domain-fragments']:
            self.send(view,dict(type='family',value=family))
            frames.frame(window)
            self.assertEqual(self.model(view)['family'],family)
        self.send(view,dict(type='family',value='toggles'))
        self.click(window,self.item(view,'sampleCheckbox'))
        self.assertFalse(self.model(view)['checked'])
        self.send(view,dict(type='family',value='lists'))
        self.click(window,self.item(view,'sampleList_tasks'))
        self.assertEqual(self.model(view)['row'],'tasks')
        self.send(view,dict(type='family',value='text-fields'))
        self.click(window,self.item(view,'sampleField'))
        QTest.keyClick(window,Qt.Key_A,Qt.ControlModifier)
        event=QInputMethodEvent()
        event.setCommitString('Edited locally')
        QGuiApplication.sendEvent(self.item(view,'sampleField'),event)
        frames.frame(window)
        self.assertEqual(self.model(view)['text'],'Edited locally')
        self.send(view,dict(type='state',value='disabled'))
        self.assertFalse(self.item(view,'sampleField').isEnabled())
        self.send(view,dict(type='reset'))
        self.assertEqual(self.model(view)['text'],'Robot Arm')
        self.send(view,dict(type='code'))
        frames.frame(window)
        self.assertGreater(self.item(view,'showcaseCodeSource').height(),0)
        for width in (620,320):
            view.setWidth(width);window.resize(width,760)
            view.property('theme').setProperty('dark',False)
            frames.frame(window)
            self.assertGreaterEqual(self.item(view,'showcaseTitle').height(),64)
            self.assertFalse(window.grabWindow().isNull())


if __name__=='__main__':
    unittest.main()
