"""Actual workspace/controller input for the responsive result-view switcher."""
import os
from pathlib import Path
import unittest

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
import tests.test_process_menu_latency as fixture


class ResultViewSwitcherTests(unittest.TestCase):
    setUpClass = classmethod(fixture.ProcessMenuLatencyTests.setUpClass.__func__)
    setUp = fixture.ProcessMenuLatencyTests.setUp
    scene = fixture.ProcessMenuLatencyTests.scene

    def click(self, window, item):
        cursor=item.findChild(QObject,'compactIconButtonCursorArea')
        if cursor: cursor.setProperty('lastActivationAt',-1000.0)
        point=item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint()
        QTest.mouseClick(item.window(),Qt.LeftButton,Qt.NoModifier,point)
        fixture.frame(window)

    def test_modes_keyboard_busy_and_resize_keep_the_original_controller(self):
        self.controller.workspace_model.replace_nodes([])
        with self.scene(width=1100,animated=False) as (window,view):
            self.assertTrue(view.property('inlineResultViews'))
            picker=fixture.visual_control(view,'searchResultViewPicker')
            self.assertIsNotNone(picker)
            self.assertEqual((picker.width(),picker.height()),(114,40))
            for mode in ('table','tiles','continious'):
                self.click(window,fixture.visual_control(view,'searchResultViewPicker_'+mode))
                self.assertEqual(self.controller.results_view_mode,mode)
                self.assertEqual(picker.property('currentValue'),mode)
            radio=fixture.visual_control(view,'searchResultViewPicker_continious')
            radio.forceActiveFocus()
            QTest.keyClick(window,Qt.Key_End)
            fixture.frame(window)
            self.assertEqual(self.controller.results_view_mode,'table')
            focused=fixture.visual_control(view,'searchResultViewPicker_table')
            from PySide6.QtQml import QQmlEngine, QQmlExpression
            border=QQmlExpression(QQmlEngine.contextForObject(focused),focused,'background.border.width')
            self.assertEqual(border.evaluate()[0],1)
            tab=self.controller._current_tab()
            tab.loading=True
            self.controller.search_state_changed.emit()
            fixture.frame(window)
            self.assertFalse(picker.isEnabled())
            tab.loading=False
            self.controller.search_state_changed.emit()
            fixture.frame(window)
            trigger=view.findChild(QQuickItem,'searchResultsViewMenuButton')
            for mode in ('compact','splitted_vertical','splitted_horizontal'):
                self.click(window,trigger)
                menu=view.findChild(QObject,'searchResultViewsMenu')
                self.assertTrue(menu.property('opened'))
                target=next(item for item in fixture.visual_items(menu.property('contentItem'))
                    if item.objectName()=='actionMenuPrimaryTarget' and item.parentItem().property('modelData').toVariant().get('command')==mode)
                self.click(window,target)
                self.assertEqual(self.controller.results_view_mode,mode)
            self.controller.set_results_view_mode('table')
            fixture.frame(window)
            tabs=self.controller.workspace_state.tabs_model
            original=[dict(tabs.get(i)) for i in range(tabs.rowCount())]
            tabs.replace([dict(entryKey='crowded'+str(i),title='A long search tab '+str(i),closable=True,current=i==0) for i in range(8)])
            fixture.frame(window)
            self.assertFalse(view.property('inlineResultViews'))
            tabs.replace(original)
            fixture.frame(window)
            self.assertTrue(view.property('inlineResultViews'))
            output=os.environ.get('RESULT_VIEW_OUTPUT')
            if output:
                Path(output).mkdir(parents=True,exist_ok=True)
                group=view.findChild(QQuickItem,'searchResultsViewsInline')
                point=group.mapToScene(QPointF()).toPoint()
                window.grabWindow().copy(point.x(),point.y(),int(group.width()),int(group.height())).save(str(Path(output)/'native-picker.png'))
                view.property('theme').setProperty('dark',False)
                fixture.frame(window)
                window.grabWindow().copy(point.x(),point.y(),int(group.width()),int(group.height())).save(str(Path(output)/'native-picker-light.png'))
            window.resize(800,650)
            view.setWidth(800)
            fixture.frame(window)
            self.assertTrue(view.property('inlineResultViews'))
            window.resize(700,650)
            view.setWidth(700)
            fixture.frame(window)
            self.assertFalse(view.property('inlineResultViews'))
            self.assertEqual(self.controller.results_view_mode,'table')


if __name__=='__main__':
    unittest.main()
