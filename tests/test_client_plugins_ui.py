import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('QT_QUICK_BACKEND','software')
os.environ.setdefault('QT_QPA_FONTDIR','C:/Windows/Fonts')
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from PySide6.QtCore import QObject, Signal, QUrl, Qt, QPointF, QEvent, QCoreApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from thlib.environment import env_mode,env_inst,env_server
from thlib.ui.client_plugins import ClientPluginsController
from thlib.ui.localization import CatalogTranslator

class Application(QObject):
    project_changed=Signal(str,str)
    authentication_changed=Signal()
    current_project_code='fixture'

class ClientPluginUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        QQuickStyle.setStyle('Material')
        cls.app=QApplication.instance() or QApplication([])
        env_inst.start_pools()

    @classmethod
    def tearDownClass(cls):
        env_inst.exit_pools()

    def test_native_page_mouse_keyboard_narrow_and_russian(self):
        source=Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as folder:
            original=env_mode.get_current_path()
            env_mode.set_current_path(folder)
            env_server.set_server('localhost:18080')
            env_server.set_user('fixture')
            env_server.set_ticket('fixture-ticket')
            application=Application()
            controller=ClientPluginsController(application,parent=application)
            record={'code':'fixture_plugin','title':'Fixture plugin','description':'Desktop tool',
                    'version':'1.0.0','error':'','allowed':True}
            translator=CatalogTranslator(source/'thlib/ui/translations/ru.json')
            engine=QQmlApplicationEngine()
            warnings=[]
            engine.warnings.connect(lambda values:warnings.extend(value.toString() for value in values))
            engine.rootContext().setContextProperty('testController',controller)
            qml=f'''import QtQuick
import "." as App
import "features/configuration" as Configuration
Window {{ width: 800; height: 640; visible: true
 App.Theme {{ id: palette; dark: true }}
 Configuration.ClientPlugins {{ anchors.fill: parent; anchors.margins: 16; theme: palette; controller: testController }}
}}'''
            def pump(predicate):
                end=time.monotonic()+10
                while not predicate():
                    self.app.processEvents()
                    if time.monotonic()>end: self.fail(controller.error or 'Native UI timeout')
            try:
                with patch.object(ClientPluginsController,'_catalog',return_value=([record],True)):
                    engine.loadData(qml.encode(),QUrl.fromLocalFile(str(source/'thlib/ui/qml/plugin-ui-test.qml')))
                    self.assertTrue(engine.rootObjects(),warnings)
                    self.app.installTranslator(translator)
                    engine.retranslate()
                    window=engine.rootObjects()[0]
                    pump(lambda:not controller.busy and bool(controller.rows))
                    for _ in range(5): self.app.processEvents()
                    def find(name):
                        pending=[window.contentItem()]
                        while pending:
                            item=pending.pop()
                            if item.objectName()==name: return item
                            pending.extend(item.childItems())
                    self.assertFalse(warnings,warnings)
                    pump(lambda:find('clientPluginEnabled_fixture_plugin') is not None)
                    toggle=find('clientPluginEnabled_fixture_plugin')
                    point=toggle.mapToScene(QPointF(toggle.width()/2,toggle.height()/2)).toPoint()
                    QTest.mouseClick(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
                    pump(lambda:not controller.rows[0]['enabled'])
                    toggle=find('clientPluginEnabled_fixture_plugin')
                    toggle.forceActiveFocus()
                    QTest.keyClick(window,Qt.Key.Key_Space)
                    pump(lambda:controller.rows[0]['enabled'])
                    window.setWidth(500)
                    for _ in range(5): self.app.processEvents()
                    button=find('clientPluginBuild')
                    self.assertGreaterEqual(button.mapToScene(QPointF(0,0)).x(),0)
                    self.assertLessEqual(button.mapToScene(QPointF(button.width(),0)).x(),500)
                    self.assertFalse(warnings,warnings)
                    window.close()
            finally:
                controller.shutdown()
                engine.deleteLater()
                self.app.processEvents()
                QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
                self.app.removeTranslator(translator)
                env_mode.set_current_path(original)
