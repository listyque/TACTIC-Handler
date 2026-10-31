"""Real shipped showcase controls, local state and both palettes."""
import unittest
from PySide6.QtCore import Q_ARG, QMetaObject, Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from tests import test_frame_table as frames
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.source_editor import SourceEditorService


class FrameShowcaseTests(unittest.TestCase):
    create=frames.FrameTableTests.create
    close=frames.FrameTableTests.close
    item=frames.FrameTableTests.item
    click=frames.FrameTableTests.click

    @classmethod
    def setUpClass(cls):
        cls.app=frames.gui_test_application()

    def send(self,view,event):
        self.assertTrue(QMetaObject.invokeMethod(view,'dispatch',Q_ARG('QVariant',event)))
        self.app.processEvents()

    def model(self,view):
        value=view.property('model')
        return value.toVariant() if hasattr(value,'toVariant') else value

    def test_live_families_and_actual_input(self):
        source=SourceEditorService()
        window,view=self.create('features/administration/ComponentShowcaseView.qml',dict(sourceEditor=source),
            width=1000,height=760,context=qml_icon_bindings(frames.QML.parents[2]))
        models=self.item(view,'componentShowcase').property('models').toVariant()
        self.assertEqual([row['id'] for row in models['families'][:6]],
                         ['typography','colors','headers','icons','buttons','toggles'])
        for family in ['typography','headers','colors','icons','buttons','toggles','text-fields',
                       'choices','numbers','dates','user-choice','pickers','tabs','badges','lists','charts']:
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
            self.assertFalse(window.grabWindow().isNull())


if __name__=='__main__':
    unittest.main()
