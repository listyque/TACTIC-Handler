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
from thlib.ui.client_plugins import ClientPluginsController, _PluginSources
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


    def test_plugin_lazy_imports_do_not_write_or_read_bytecode(self):
        import importlib
        import sys
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'late.py').write_text('value=17\n')
            name='_th_fixture_sources'
            import types
            package=types.ModuleType(name)
            package.__path__=[folder]
            finder=_PluginSources(name,root)
            sys.modules[name]=package
            sys.meta_path.insert(0,finder)
            previous=sys.dont_write_bytecode
            try:
                sys.dont_write_bytecode=False
                result=importlib.import_module(name+'.late')
                self.assertEqual(result.value,17)
                self.assertFalse(list(root.rglob('*.pyc')))
            finally:
                sys.dont_write_bytecode=previous
                sys.meta_path.remove(finder)
                sys.modules.pop(name+'.late',None)
                sys.modules.pop(name,None)


    def test_launch_actions_follow_existing_rights_and_enablement(self):
        with tempfile.TemporaryDirectory() as folder:
            original=env_mode.get_current_path()
            env_mode.set_current_path(folder)
            application=Application()
            controller=ClientPluginsController(application,parent=application)
            try:
                controller._rows=[{'code':'th_batch_render','title':'Batch Render','allowed':True,'error':''},
                                  {'code':'denied','title':'Denied','allowed':False,'error':''}]
                self.assertEqual([a['command'] for a in controller.launchActions],['client_plugin:th_batch_render'])
                controller.set_enabled('th_batch_render',False)
                self.assertEqual(controller.launchActions,[])
                controller.set_enabled('th_batch_render',True)
                controller._busy=True
                self.assertFalse(controller.launchActions[0]['enabled'])
                controller._rows[0]['allowed']=False
                self.assertEqual(controller.launchActions,[])
            finally:
                controller.shutdown()
                env_mode.set_current_path(original)

    def test_autostart_is_opt_in_scoped_and_attempted_once(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as folder:
            original = env_mode.get_current_path()
            env_mode.set_current_path(folder)
            application = Application()
            controller = ClientPluginsController(application, parent=application)
            try:
                controller._rows = [{'code':'th_batch_render','title':'Batch Render','allowed':True,'error':''},
                                    {'code':'second_plugin','title':'Second plugin','allowed':True,'error':''}]
                with patch.object(env_inst, 'ui_main', object()), patch.object(controller, 'open_plugin') as launch:
                    controller._autostart_next()
                    launch.assert_not_called()
                    controller.set_autostart('th_batch_render', True)
                    self.assertTrue(controller.rows[0]['autostart'])
                    self.assertFalse(controller.rows[1]['autostart'])
                    controller.set_enabled('th_batch_render', False)
                    controller._autostart_next()
                    launch.assert_not_called()
                    controller.set_enabled('th_batch_render', True)
                    controller._rows[0]['allowed'] = False
                    controller._autostart_next()
                    launch.assert_not_called()
                    controller._rows[0]['allowed'] = True
                    controller._autostart_next()
                    controller._autostart_next()
                    launch.assert_called_once_with('th_batch_render')
                    application.current_project_code = 'another'
                    self.assertFalse(controller.rows[0]['autostart'])
                    controller.set_autostart('th_batch_render', True)
                    controller._autostart_next()
                    self.assertEqual(launch.call_count,2)
                    controller.shutdown()
                    controller._autostart_next()
                    self.assertEqual(launch.call_count,2)
            finally:
                controller.shutdown()
                env_mode.set_current_path(original)

    def test_main_menu_launch_is_not_restricted_to_administrators(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from thlib.ui.controllers.commands import CommandsMixin
        from thlib.ui.menu_schema import MenuRegistry
        class Host(CommandsMixin,QObject):
            command_requested=Signal(str)
            can_manage_tools=False
            is_stream_server=False
            debug_log=None
        host=Host()
        host._menus=MenuRegistry()
        plugins=SimpleNamespace(launchActions=[{'title':'Batch Render','icon':'movie',
                                                'command':'client_plugin:th_batch_render'}],open_plugin=Mock())
        host.attach_client_plugins(plugins)
        self.assertEqual(host.menu_actions('user')[0]['command'],'client_plugin:th_batch_render')
        host.invoke('client_plugin:th_batch_render')
        plugins.open_plugin.assert_called_once_with('th_batch_render')

    def test_top_bar_launch_button_mouse_keyboard_and_touch(self):
        from PySide6.QtCore import Property,Slot
        class Launcher(QObject):
            stateChanged=Signal()
            def __init__(self):
                super().__init__()
                self.actions=[{'title':'Batch Render','command':'client_plugin:th_batch_render','enabled':True}]
                self.calls=[]
            @Property('QVariantList',notify=stateChanged)
            def launchActions(self): return self.actions
            @Slot(str)
            def open_plugin(self,code): self.calls.append(code)
        controller=Launcher()
        source=Path(__file__).parents[1]
        engine=QQmlApplicationEngine()
        warnings=[]
        engine.warnings.connect(lambda values:warnings.extend(value.toString() for value in values))
        engine.rootContext().setContextProperty('testLauncher',controller)
        qml=b'''import QtQuick
import "." as App
import "features/plugins" as Plugins
Window { width: 300; height: 100; visible: true
 App.Theme { id: palette; dark: true }
 Plugins.BatchRenderButton { x: 12; y: 12; width: 36; height: 36; theme: palette; controller: testLauncher }
}'''
        engine.loadData(qml,QUrl.fromLocalFile(str(source/'thlib/ui/qml/button-test.qml')))
        self.assertTrue(engine.rootObjects(),warnings)
        window=engine.rootObjects()[0]
        try:
            self.app.processEvents()
            button=window.findChild(QObject,'batchRenderLaunchButton')
            self.assertTrue(button.isVisible())
            point=button.mapToScene(QPointF(18,18)).toPoint()
            QTest.mouseClick(window,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point)
            button.forceActiveFocus()
            QTest.keyClick(window,Qt.Key.Key_Return)
            self.assertEqual(controller.calls,['th_batch_render']*2)
            # Separate authentic input from the house 180 ms duplicate-activation guard.
            QTest.qWait(200)
            device=QTest.createTouchDevice()
            QTest.touchEvent(window,device).press(0,point,window).commit()
            QTest.touchEvent(window,device).release(0,point,window).commit()
            self.app.processEvents()
            self.assertEqual(controller.calls,['th_batch_render']*3)
            controller.actions=[]
            controller.stateChanged.emit()
            self.app.processEvents()
            self.assertFalse(button.isVisible())
            self.assertFalse(warnings,warnings)
        finally:
            window.close()
            engine.deleteLater()
            self.app.processEvents()

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
                with patch.object(ClientPluginsController,'_catalog',return_value=([record,dict(record,code='second_plugin',title='Second plugin with a deliberately long descriptive name')],True)):
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
                    # Catalogue selection is inert; only explicit launch actions call the loader.
                    with patch.object(controller,'_run') as launch:
                        item=find('clientPluginSelect_fixture_plugin')
                        point=item.mapToScene(QPointF(item.width()/2,item.height()/2)).toPoint()
                        QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=point)
                        self.assertTrue(item.property('selected'))
                        item.forceActiveFocus()
                        QTest.keyClick(window,Qt.Key.Key_Return)
                        launch.assert_not_called()
                        button=find('clientPluginLaunch_fixture_plugin')
                        self.assertEqual(button.property('text'),'Запустить')
                        QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint())
                        self.assertEqual(launch.call_count,1)
                        self.assertEqual(launch.call_args.args[:2],('open','fixture_plugin'))
                        button.forceActiveFocus()
                        QTest.keyClick(window,Qt.Key.Key_Space)
                        self.assertEqual(launch.call_count,2)
                        device=QTest.createTouchDevice()
                        point=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint()
                        QTest.touchEvent(window,device).press(0,point,window).commit()
                        QTest.touchEvent(window,device).release(0,point,window).commit()
                        self.app.processEvents()
                        self.assertEqual(launch.call_count,3)
                        controller.set_enabled('fixture_plugin',False)
                        self.app.processEvents()
                        button=find('clientPluginLaunch_fixture_plugin')
                        self.assertFalse(button.isEnabled())
                        launch.reset_mock()
                        QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint())
                        launch.assert_not_called()
                        controller.set_enabled('fixture_plugin',True)
                        self.app.processEvents()
                        key=(controller._scope(controller._context()),'fixture_plugin')
                        controller._runs[key]={'version':'1.0.0'}
                        controller.stateChanged.emit();self.app.processEvents()
                        self.assertEqual(find('clientPluginLaunch_fixture_plugin').property('text'),'Показать окно')
                        controller._runs.clear();controller.stateChanged.emit();self.app.processEvents()
                    autostart=find('clientPluginAutostart_fixture_plugin')
                    self.assertEqual(autostart.property('text'),'Автоматически запускать Fixture plugin')
                    autostart.forceActiveFocus()
                    QTest.keyClick(window,Qt.Key.Key_Space)
                    pump(lambda:controller.rows[0]['autostart'])
                    self.assertFalse(controller.rows[1]['autostart'])
                    self.assertFalse(find('clientPluginAutostart_second_plugin').property('checked'))
                    controller.set_autostart('fixture_plugin',False)
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
                    # Building is a separate, explained action; merely opening/cancelling is inert.
                    dialog=window.findChild(QObject,'clientPluginBuildDialog')
                    field=window.findChild(QObject,'clientPluginBuildVersion')
                    self.assertFalse(dialog.property('visible'))
                    self.assertEqual(field.property('text'),'')
                    with patch.object(controller,'build') as build:
                        QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint())
                        pump(lambda:dialog.property('opened'))
                        self.assertEqual(dialog.property('title'),'Сборка пакета плагина')
                        confirm=window.findChild(QObject,'clientPluginBuildConfirm')
                        cancel=window.findChild(QObject,'clientPluginBuildCancel')
                        self.assertFalse(confirm.isEnabled())
                        field.setProperty('text','bad version')
                        self.assertFalse(confirm.isEnabled())
                        field.setProperty('text','1.2.1')
                        self.app.processEvents()
                        self.assertTrue(confirm.isEnabled())
                        self.assertGreaterEqual(dialog.property('x'),0)
                        self.assertLessEqual(dialog.property('x')+dialog.property('width'),500)
                        QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=cancel.mapToScene(QPointF(cancel.width()/2,cancel.height()/2)).toPoint())
                        pump(lambda:not dialog.property('visible'))
                        build.assert_not_called()
                        QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=button.mapToScene(QPointF(button.width()/2,button.height()/2)).toPoint())
                        pump(lambda:dialog.property('opened'))
                        QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=confirm.mapToScene(QPointF(confirm.width()/2,confirm.height()/2)).toPoint())
                        pump(lambda:not dialog.property('visible'))
                        build.assert_called_once_with('1.2.1')
                    controller._admin=False;controller.stateChanged.emit()
                    self.app.processEvents()
                    self.assertFalse(find('clientPluginBuild').isVisible())
                    for code in ('fixture_plugin','second_plugin'):
                        for action in ('Launch','Autostart'):
                            control=find(f'clientPlugin{action}_{code}')
                            self.assertGreaterEqual(control.mapToScene(QPointF()).x(),0)
                            self.assertLessEqual(control.mapToScene(QPointF(control.width(),0)).x(),500)
                    self.assertFalse(warnings,warnings)
                    window.close()
            finally:
                controller.shutdown()
                engine.deleteLater()
                self.app.processEvents()
                QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
                self.app.removeTranslator(translator)
                env_mode.set_current_path(original)
