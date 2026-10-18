"""Shared repository confirmations keep the existing settings/server owner."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
from PySide6.QtCore import QObject, Qt, QPointF, QMetaObject
from PySide6.QtTest import QTest
from thlib.environment import env_server
from tests.frame_configuration_fixture import Surface

QML = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'

class RepositoryPromptTests(unittest.TestCase):
    def test_team_confirmation_input_long_path_and_changed_target(self):
        with patch.object(env_server, 'is_team_local_repository', return_value=True):
            surface = Surface('repository_editor', 1000, 740, qml=QML)
            try:
                owner = surface.repositories
                path = '//fixture/repository/' + 'very_long_directory/' * 30
                owner._current_code = 'default'
                owner._current_path = path
                owner.configurationChanged.emit()
                surface.settle()
                def click(name):
                    item = surface.item(name)
                    point = item.mapToScene(QPointF(item.width()/2, item.height()/2)).toPoint()
                    QTest.mouseClick(surface.window, Qt.LeftButton, pos=point)
                    surface.settle()
                click('repositorySync')
                dialog = surface.view.findChild(QObject, 'teamRepositorySyncDialog')
                self.assertTrue(dialog.property('opened'))
                self.assertEqual(surface.item('repositoryTeamPath').property('text'), 'default → ' + path)
                self.assertTrue(surface.item('repositoryTeamScrollBar').property('hasOverflow'))
                click('repositoryTeamCancel')
                self.assertEqual(owner.sync_calls, 0)
                click('repositorySync')
                click('repositoryTeamAccept')
                self.assertEqual(owner.sync_calls, 1)
                click('repositorySync')
                owner._current_path = '//fixture/changed'
                owner.configurationChanged.emit()
                surface.settle()
                self.assertFalse(surface.item('repositoryTeamAccept').isEnabled())
                self.assertIsNotNone(surface.item('repositoryTeamChanged'))
                QMetaObject.invokeMethod(dialog, 'accept')
                surface.settle()
                self.assertEqual(owner.sync_calls, 1)
                self.assertEqual(surface.warnings, [])
            finally:
                surface.close()

if __name__ == '__main__':
    unittest.main()
