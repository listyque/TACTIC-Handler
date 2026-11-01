"""Administration header icons are round; local catalogue actions stay square."""
import os
from pathlib import Path
import unittest
from unittest.mock import PropertyMock, patch

from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from tests import test_editor_windows_qml as windows_fixture
from tests import test_sidebar_editor_qml as sidebar_fixture
from tests.test_admin_plugins import DOCUMENT, ROW
from tests.test_service_button_shapes import surface_radius
from tests.profile_ui_responsiveness import frame


class AdministrationButtonShapesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        windows_fixture.EditorWindowQmlTests.setUpClass()

    def test_header_buttons_are_round_aligned_and_keep_collapse_actions(self):
        fixture = windows_fixture.EditorWindowQmlTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.enterContext(patch.object(type(fixture.application), 'is_stream_server',
                                      new_callable=PropertyMock, return_value=True))
        admin = fixture.admin
        admin._project = 'demo'
        editor = admin.pluginsEditor
        editor._project = 'demo'
        editor._loaded = editor._can_write = True
        editor._identity = ROW['identity']
        editor._catalog = [dict(ROW)]
        editor._document = dict(DOCUMENT['document'])
        editor._original = dict(DOCUMENT['document'])
        editor._metadata = dict(DOCUMENT['metadata'])
        admin.open()
        admin.select_section('plugins')
        window = fixture.window('administration')
        window.resize(1400, 940)
        frame(window)

        def item(name):
            return next(control for control in sidebar_fixture.SidebarEditorQmlTests.descendants(window.contentItem())
                        if control.objectName() == name and control.isVisible())

        for name in ('adminToggleNavigation', 'administrationHelpButton', 'pluginReload', 'pluginCollapse'):
            control = item(name)
            self.assertEqual((control.width(), control.height()), (34, 34), name)
            if name == 'pluginCollapse':
                self.assertEqual(surface_radius(control), 4, name)
            else:
                self.assertGreaterEqual(surface_radius(control), (control.width() - 2) / 2, name)
        reload = item('pluginReload')
        help_button = item('administrationHelpButton')
        reload_origin = reload.mapToScene(QPointF())
        help_origin = help_button.mapToScene(QPointF())
        self.assertEqual(reload_origin.y(), help_origin.y())
        for name in ('adminToggleNavigation', 'adminToggleNavigation', 'pluginCollapse', 'pluginCollapse'):
            control = item(name)
            QTest.mouseClick(window, Qt.LeftButton, pos=control.mapToScene(QPointF(17, 17)).toPoint())
            frame(window)
        if os.environ.get('ADMIN_BUTTON_CAPTURE'):
            window.grabWindow().save(str(Path(os.environ['ADMIN_BUTTON_CAPTURE'])))
        self.assertEqual(fixture.warnings, [])
