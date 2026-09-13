from pathlib import Path
import os
import unittest

from PySide6.QtCore import QCoreApplication, QElapsedTimer, QEvent, QObject, QPoint, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtTest import QTest

from tests.qt_application import gui_test_application
from tests.test_workspace_layout_presets_qml import _PresetController
from thlib.ui.workspace_models.docks import DockPanelModel
from thlib.ui.pointer import PointerController
from thlib.ui.icon_font import qml_icon_bindings


QML = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'


class CompactMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == 'nt':
            os.environ.setdefault('QT_QPA_FONTDIR', str(Path(os.environ['WINDIR']) / 'Fonts'))
        cls.app = gui_test_application()
        cls.font_context = qml_icon_bindings(QML.parents[2], cls.app)

    def setUp(self):
        self.engine = QQmlEngine()
        for name, value in self.font_context.items():
            self.engine.rootContext().setContextProperty(name, value)
        self.warnings = []
        self.qt_objects = []
        self.engine.warnings.connect(lambda errors: self.warnings.extend(
            error.toString() for error in errors))
        self.panels = DockPanelModel({})
        self.presets = _PresetController()
        self.pointer = PointerController()
        self.engine.rootContext().setContextProperty('pointerController', self.pointer)
        self.engine.rootContext().setContextProperty('panels', self.panels)
        self.engine.rootContext().setContextProperty('presets', self.presets)
        self.component = QQmlComponent(self.engine)
        self.component.setData(b'''
import QtQuick
import QtQuick.Controls
Window {
    id: window
    width: 900; height: 700; visible: true
    property string command: ""
    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    ActionMenu {
        id: menu; objectName: "testMenu"; theme: theme; compact: true
        actions: [
            {title: "Paste", command: "paste"},
            {title: "View", children: [
                {title: "Table", command: "table", checked: true},
                {title: "More", children: [{title: "Calendar", command: "calendar"}]}
            ]},
            {separator: true},
            {title: "Preview", command: "preview", advanced: true}
        ]
        onTriggered: value => window.command = value
    }
    DockMenu { id: dock; objectName: "testDock"; theme: theme
        panelModel: panels; layoutPresetController: presets }
    function openMenu() { menu.openAt(window.contentItem, 20, 20, false) }
    function openDock() { dock.openAt(window.contentItem, 20, 20, false) }
}
''', QUrl.fromLocalFile(str(QML / '_CompactMenuTest.qml')))
        self.window = self.component.create()
        self.assertIsNotNone(self.window, '\n'.join(
            error.toString() for error in self.component.errors()))
        self.window.requestActivate()
        self.settle()

    def tearDown(self):
        self.evaluate('menu.close(); dock.close()')
        self.settle()
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.settle()

    def settle(self):
        for _ in range(12):
            self.app.processEvents()

    def wait_for(self, predicate, message=''):
        elapsed = QElapsedTimer()
        elapsed.start()
        while not predicate() and elapsed.elapsed() < 1000:
            QTest.qWait(10)
        self.assertTrue(predicate(), message)

    def evaluate(self, expression):
        expr = QQmlExpression(QQmlEngine.contextForObject(self.window), self.window, expression)
        value = expr.evaluate()
        self.assertFalse(expr.hasError(), expr.error().toString())
        result = value[0] if isinstance(value, tuple) else value
        if isinstance(result, QObject):
            self.qt_objects.append(result)
        return result

    def action_target(self, menu_name, title):
        menu = self.evaluate(menu_name)
        def visual_children(item):
            for child in item.childItems():
                yield child
                yield from visual_children(child)
        return next(target for target in visual_children(menu.property('contentItem'))
            if target.objectName() == 'actionMenuPrimaryTarget' and target.property('visible')
            and target.parentItem().property('modelData').toVariant().get('title') == title)

    def action_surface(self, menu_name, title):
        row = self.action_target(menu_name, title).parentItem()
        return next(child for child in row.childItems()
                    if child.objectName() == 'actionMenuRowSurface')

    def click(self, menu_name, title):
        target = self.action_target(menu_name, title)
        point = target.mapToScene(QPoint(int(target.width() / 2), int(target.height() / 2)))
        QTest.mouseClick(target.window(), Qt.LeftButton, Qt.NoModifier, point.toPoint())
        self.settle()

    def test_hover_between_submenus_keeps_the_native_menu_branch_active(self):
        if self.app.platformName() == 'offscreen':
            self.skipTest('Native popup mouse grabs require a window-system backend')
        for animations in ('false', 'true'):
            self.evaluate('theme.popupAnimationsEnabled = ' + animations)
            self.window.openDock()
            self.wait_for(lambda: self.evaluate('dock.opened'))
            self.settle()
            for title in ('Tasks and reports', 'Browsing', 'Layout presets',
                          'Tools', 'Tasks and reports'):
                target = self.action_target('dock', title)
                point = target.mapToScene(QPoint(int(target.width() / 2), int(target.height() / 2)))
                QTest.mouseMove(target.window(), point.toPoint())
                self.wait_for(lambda: self.evaluate(
                    'dock.activeSubmenu && dock.activeSubmenu.opened && '
                    'dock.activeSubmenu.openingAnchorItem && '
                    'dock.activeSubmenu.openingAnchorItem.modelData.title === ' + repr(title)),
                    f'animations={animations}, submenu={title}')
                self.assertGreater(
                    self.evaluate(
                        'dock.activeSubmenu.objectName === "workspacePresetsMenu" '
                        '? dock.activeSubmenu.contentItem.contentHeight '
                        ': dock.activeSubmenu.displayedActions.length'
                    ),
                    0,
                )
                focused = sum(
                    self.action_target('dock', candidate).hasActiveFocus()
                    for candidate in (
                        'Tasks and reports', 'Browsing', 'Layout presets',
                        'Tools',
                    )
                )
                self.assertEqual(focused, 1)
                child = self.evaluate('dock.activeSubmenu.contentItem').window()
                parent = self.evaluate('dock.contentItem').window()
                self.assertIs(child.transientParent(), parent)
                popup_windows = [
                    window for window in self.app.topLevelWindows()
                    if window.isVisible()
                    and window.flags() & Qt.WindowType_Mask == Qt.Popup
                ]
                self.assertEqual(
                    len(popup_windows),
                    2,
                    [(window.objectName(), window.title(), window.geometry(),
                      window.transientParent()) for window in popup_windows],
                )
                highlighted = [
                    candidate for candidate in (
                        'Tasks and reports', 'Browsing', 'Layout presets', 'Tools')
                    if self.action_surface('dock', candidate).opacity() > 0.01
                ]
                self.assertEqual(highlighted, [title])
                QTest.mouseMove(child, QPoint(50, 35))
                self.settle()
                self.assertTrue(self.evaluate('dock.opened'))
                self.assertTrue(self.evaluate('dock.activeSubmenu.opened'))
                self.assertEqual(child.modality(), Qt.NonModal)
                self.assertTrue(self.app.focusWindow() is not None)
            self.evaluate('dock.close()')
            self.wait_for(lambda: not self.evaluate('dock.visible'))
            self.assertFalse(child.isVisible())
        self.assertEqual(self.warnings, [])

    def test_advanced_toggle_keeps_clipboard_primary_and_normalizes_separators(self):
        self.window.openMenu()
        self.settle()
        self.assertEqual(self.evaluate('menu.displayedActions.map(a => a.title || "-").join("|")'),
                         'Paste|View|-|Advanced menu')
        basic_height = self.evaluate('menu.height')
        self.click('menu', 'Advanced menu')
        self.assertTrue(self.evaluate('menu.advancedExpanded'))
        self.assertGreater(self.evaluate('menu.height'), basic_height)
        self.click('menu', 'Basic menu')
        self.assertEqual(self.evaluate('menu.height'), basic_height)
        self.click('menu', 'Paste')
        self.assertEqual(self.window.property('command'), 'paste')
        self.assertFalse(self.evaluate('menu.visible'))
        self.assertEqual(self.warnings, [])

    def test_hovered_action_owns_the_highlight_when_focus_lags(self):
        self.window.openMenu()
        self.settle()
        focused = self.action_target('menu', 'Paste')
        hovered = self.action_target('menu', 'View').parentItem()
        focused.forceActiveFocus(Qt.MouseFocusReason)
        self.engine.rootContext().setContextProperty(
            'hoveredActionForTest', hovered)
        self.evaluate('menu.hoveredAction = hoveredActionForTest')
        self.assertTrue(self.evaluate(
            'menu.hoveredAction === hoveredActionForTest'))
        self.wait_for(
            lambda: self.action_surface('menu', 'View').opacity() > 0.01)

        self.assertEqual(self.action_surface('menu', 'Paste').opacity(), 0)
        self.assertGreater(self.action_surface('menu', 'View').opacity(), 0)
        self.assertEqual(self.warnings, [])

    def test_nested_submenu_mouse_and_keyboard_close_the_whole_branch(self):
        self.window.openMenu()
        self.settle()
        self.click('menu', 'View')
        self.assertTrue(self.evaluate('menu.activeSubmenu.opened'))
        self.assertTrue(self.evaluate('menu.opened'))
        self.click('menu.activeSubmenu', 'More')
        self.assertTrue(self.evaluate('menu.activeSubmenu.activeSubmenu.opened'))
        self.click('menu.activeSubmenu.activeSubmenu', 'Calendar')
        self.assertEqual(self.window.property('command'), 'calendar')
        self.assertFalse(self.evaluate('menu.visible'))
        self.assertFalse(self.evaluate('menu.activeSubmenu.visible'))
        self.assertEqual(self.warnings, [])

    def test_dock_groups_retain_all_panels_and_live_checks(self):
        self.window.openDock()
        self.settle()
        self.assertLessEqual(self.evaluate('dock.actions.filter(a => !a.separator && a.visible !== false).length'), 8)
        self.assertEqual(self.evaluate('dock.actions.reduce((n,a) => n + (a.children ? a.children.length : 0), 0)'),
                         self.panels.rowCount())
        self.click('dock', 'Tasks and reports')
        self.click('dock.activeSubmenu', 'Task Manager')
        self.assertFalse(self.panels.is_panel_visible('tasks'))
        self.window.openDock()
        self.settle()
        self.assertFalse(self.evaluate('dock.actions[1].children[0].checked'))
        self.assertEqual(self.warnings, [])

    def test_layout_presets_open_separately(self):
        self.window.openDock()
        self.settle()
        self.click('dock', 'Layout presets')
        popup = self.window.findChild(QObject, 'workspacePresetsMenu')
        self.assertTrue(popup.property('opened'))
        self.assertTrue(self.evaluate('dock.opened'))
        parent_window = self.evaluate('dock.contentItem').window()
        child_window = self.evaluate('dock.activeSubmenu.contentItem').window()
        shadow = self.evaluate('dock.effectiveShadowMargin')
        area = child_window.screen().availableGeometry()
        parent_right = parent_window.x() + parent_window.width() - shadow
        parent_left = parent_window.x() + shadow
        if parent_right + child_window.width() - shadow <= area.right() + 1:
            self.assertAlmostEqual(child_window.x() + shadow, parent_right, delta=1)
        elif parent_left - child_window.width() + shadow >= area.left():
            self.assertAlmostEqual(child_window.x() + child_window.width() - shadow, parent_left, delta=1)
        self.assertGreaterEqual(child_window.x(), area.left())
        self.assertLessEqual(child_window.x() + child_window.width(), area.right() + 1)
        content = self.evaluate('dock.activeSubmenu.contentItem')
        self.assertEqual(self.evaluate('dock.activeSubmenu.count'), 0)
        QTest.keyClick(content.window(), Qt.Key_Left)
        self.settle()
        self.assertFalse(popup.property('visible'))
        self.assertTrue(self.evaluate('dock.opened'))
        self.assertTrue(self.action_target('dock', 'Layout presets').hasActiveFocus())
        self.assertEqual(self.warnings, [])

    def test_many_presets_scroll_without_expanding_the_main_menu(self):
        record = self.presets.records.get(0)
        preset_count = self.window.screen().availableGeometry().height() // 40 + 12
        self.presets.records.replace([
            {**record, 'view': 'workspace_layout@' + str(i), 'title': 'Layout ' + str(i)}
            for i in range(preset_count)
        ])
        self.window.openDock()
        self.settle()
        main_height = self.evaluate('dock.height')
        self.click('dock', 'Layout presets')
        popup = self.window.findChild(QObject, 'workspacePresetsMenu')
        content = popup.property('contentItem')
        self.assertGreater(content.property('contentHeight'), content.property('height'))
        self.assertLessEqual(popup.property('height'), popup.property('maximumAvailableHeight'))
        section = self.window.findChild(QObject, 'workspaceLayoutPresetMenuSection')
        targets = section.keyboardTargets().toVariant()
        self.assertTrue(targets)
        for _ in range(preset_count * 2 - 3):
            QTest.keyClick(content.window(), Qt.Key_Down)
            self.settle()
        self.assertGreater(content.property('contentY'), 0)
        self.assertEqual(self.evaluate('dock.height'), main_height)
        self.assertEqual(self.warnings, [])

    def test_keyboard_submenu_navigation_and_escape_restore_parent_focus(self):
        self.window.openMenu()
        self.settle()
        popup = self.evaluate('menu.contentItem').window()
        QTest.keyClick(popup, Qt.Key_Down)
        self.settle()
        QTest.keyClick(popup, Qt.Key_Right)
        self.settle()
        child = self.evaluate('menu.activeSubmenu.contentItem').window()
        self.assertTrue(self.evaluate('menu.activeSubmenu.opened'))
        QTest.keyClick(child, Qt.Key_Left)
        self.settle()
        self.assertFalse(self.evaluate('menu.activeSubmenu.visible'))
        self.assertTrue(self.evaluate('menu.opened'))
        self.assertEqual(self.evaluate('menu.focusedActionIndex'), 1)
        QTest.keyClick(popup, Qt.Key_Right)
        self.settle()
        QTest.keyClick(child, Qt.Key_Return)
        self.settle()
        self.assertEqual(self.window.property('command'), 'table')
        self.assertFalse(self.evaluate('menu.visible'))
        self.assertEqual(self.warnings, [])

    def test_overflow_reserves_scrollbar_gutter_and_reveals_keyboard_selection(self):
        self.evaluate('menu.usePopupWindow = false; menu.availableScreenHeight = 220; '
                      'menu.actions = Array.from({length: 20}, (_, i) => '
                      '({title: "Saved preset " + i, command: "preset:" + i})); menu.open()')
        self.settle()
        self.assertLessEqual(self.evaluate('menu.height'), 212)
        scrollbar = self.evaluate('menu').findChild(QObject, 'actionMenuScrollBar')
        self.assertTrue(scrollbar.property('hasOverflow'))
        self.evaluate('for (let i = 0; i < 19; ++i) menu.focusRelativeAction(1)')
        self.settle()
        flickable = self.evaluate('menu.contentItem')
        self.assertGreater(flickable.property('contentY'), 0)
        self.assertEqual(self.warnings, [])

    def test_native_submenu_flips_left_at_screen_edge_in_narrow_and_wide_windows(self):
        self.window.setPosition(0, 0)
        self.window.openMenu()
        self.settle()
        self.click('menu', 'View')
        parent = self.evaluate('menu.contentItem').window()
        child = self.evaluate('menu.activeSubmenu.contentItem').window()
        shadow = self.evaluate('menu.effectiveShadowMargin')
        self.assertAlmostEqual(
            child.x() + shadow, parent.x() + parent.width() - shadow, delta=1,
        )
        self.evaluate('menu.close()')
        self.settle()

        for width in (380, 900):
            self.window.setWidth(width)
            edge = self.window.mapFromGlobal(self.window.screen().availableGeometry().bottomRight())
            self.evaluate(f'menu.openAt(window.contentItem, {edge.x() - 24}, {edge.y() - 24}, false)')
            self.settle()
            self.click('menu', 'View')
            parent = self.evaluate('menu.contentItem').window()
            child = self.evaluate('menu.activeSubmenu.contentItem').window()
            area = child.screen().availableGeometry()
            self.assertGreaterEqual(child.x(), area.left())
            self.assertGreaterEqual(child.y(), area.top())
            self.assertLessEqual(child.x() + child.width(), area.right() + 1)
            self.assertLessEqual(child.y() + child.height(), area.bottom() + 1)
            self.assertLess(child.x(), parent.x())
            shadow = self.evaluate('menu.effectiveShadowMargin')
            self.assertAlmostEqual(
                child.x() + child.width() - shadow,
                parent.x() + shadow,
                delta=1,
            )
            self.evaluate('menu.close()')
            self.settle()
        self.assertEqual(self.warnings, [])

    def test_touch_opens_submenu_once(self):
        self.window.openMenu()
        self.settle()
        content = self.evaluate('menu.contentItem')
        device = QTest.createTouchDevice()
        # Paste is row zero; View is row one in the actual menu column.
        point = QPoint(int(content.x() + content.width() / 2),
                       int(content.y() + self.evaluate('menu.actionHeight(menu.actions[0])') + 16))
        sequence = QTest.touchEvent(content.window(), device)
        sequence.press(0, point, content.window()).commit()
        sequence.release(0, point, content.window()).commit()
        self.settle()
        self.assertTrue(self.evaluate('menu.activeSubmenu && menu.activeSubmenu.opened'))
        self.assertEqual(self.window.property('command'), '')
        self.assertEqual(self.warnings, [])


if __name__ == '__main__':
    unittest.main()
