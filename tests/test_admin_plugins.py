"""Native plugin forms, actual input and the existing async command boundary."""
from copy import deepcopy
import os
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QPointF, Qt, QUrl
from PySide6.QtQuick import QQuickWindow
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest

from tests.test_agent_request import isolate_chat_settings
from tests.test_frame_script_tools import ScriptToolsTests, QML
from tests.profile_ui_responsiveness import frame
from thlib.ui.admin.plugins import PluginsEditor, COMMAND
from thlib.ui.icon_font import qml_icon_bindings

ROW = dict(identity='plugins:example', title='Example plugin', code='example', version='',
           builtin=False, active=False, path='example')
DOCUMENT = dict(identity=ROW['identity'], revision='revision-1', canWrite=True,
    document=dict(title=ROW['title'], code='example', description='A plugin package', version='',
                  manifest='<manifest><data><code>example</code></data></manifest>', file=None),
    metadata=dict(folder='', files=[dict(name='README.md', path='README.md', directory=False, size=12)],
                  builtin=False, active=False, project='one', docs='README.md', docsExist=True))


class Server:
    def __init__(self):
        self.calls = []
        self.error = ''
        self.active = False
        self.uploads = []
        self.empty = False

    def upload_file(self, path):
        self.uploads.append(path)

    def execute_cmd(self, command, args):
        assert command == COMMAND
        self.calls.append(deepcopy(args))
        if self.error:
            raise RuntimeError(self.error)
        action = args['action']
        result = deepcopy(DOCUMENT)
        if action == 'list':
            result = dict(catalog=[] if self.empty else [ROW], canWrite=True, metadata={})
        elif action == 'new':
            result = dict(identity='', revision='', canWrite=True,
                          document=dict(code='', title='', description='', type=''),
                          metadata=dict(new=True, project='one'))
        else:
            if action in ('install', 'download_url', 'create'):
                self.empty = False
                result['catalog'] = [ROW]
            if action == 'activate': self.active = True
            if action == 'deactivate':
                assert args['confirmation'] is True
                self.active = False
            if action == 'open_file':
                result['document']['file'] = dict(path='README.md', content='# Example', revision='file-1')
            if action == 'save': result['document'] = args['document']
            result['metadata']['active'] = self.active
        return dict(info=result)


class AdminPluginsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ScriptToolsTests.setUpClass()

    def test_resource_theme_draft_crosses_qml_boundary_and_saves_plain_values(self):
        isolate_chat_settings(self)
        surface=ScriptToolsTests();surface.setUp();self.addCleanup(surface.doCleanups)
        resource=dict(key='config/widget_config?project=one&code=THEME',kind='theme',title='sample_theme',field='config',revision='r1',
            source='<config><sample_theme><theme style="md3"><light base="#ffffff" accent="#123456"/><dark base="#202020" accent="#abcdef"/></theme></sample_theme></config>',
            palette=dict(style='md3',light=dict(base='#ffffff',accent='#123456'),dark=dict(base='#202020',accent='#abcdef')))
        class ResourceServer(Server):
            def execute_cmd(self,command,args):
                result=super().execute_cmd(command,args)
                if args['action']!='list':
                    result['info']['metadata'].update(active=True,resources=[resource])
                    if args['action']!='save':result['info']['document']['resource']=deepcopy(resource)
                return result
        server=ResourceServer()
        controller=PluginsEditor(SimpleNamespace(can_manage_tools=True,debug_log=None));self.addCleanup(controller.shutdown)
        with patch('thlib.tactic_classes.server_start',return_value=server):
            view=surface.create(QML/'features/administration/plugins/AdminPluginsView.qml',dict(theme=surface.theme,controller=controller,width=1000,height=780,saveActionsInHeader=False))
            window=QQuickWindow();window.resize(1000,780);surface.windows.append(window)
            view.setParentItem(window.contentItem());window.show()
            def wait():
                deadline=time.monotonic()+10
                while controller.busy and time.monotonic()<deadline:QTest.qWait(5)
                self.assertFalse(controller.busy);self.assertFalse(controller.error,controller.error);frame(window)
            controller.activate('one');wait()
            view.dispatch(dict(type='tab',value='resources'));wait()
            view.dispatch(dict(type='resource-theme',field='dark_accent',value='#998877'));frame(window)
            self.assertTrue(controller.dirty)
            surface.click(window,surface.item(view,'pluginSave'));wait()
            saved=server.calls[-1]['document']['resource']
            self.assertEqual('#998877',saved['palette']['dark']['accent'])
            self.assertIn('accent="#998877"',saved['source'])
            import json
            json.dumps(saved)
            self.assertFalse(surface.warnings,'\n'.join(surface.warnings))

    def test_first_package_guides_creation_installation_and_explicit_activation(self):
        isolate_chat_settings(self)
        surface = ScriptToolsTests(); surface.setUp(); self.addCleanup(surface.doCleanups)
        for name, value in qml_icon_bindings(QML.parents[2], surface.engine).items():
            surface.engine.rootContext().setContextProperty(name, value)
        controller = PluginsEditor(SimpleNamespace(can_manage_tools=True, debug_log=None))
        self.addCleanup(controller.shutdown)
        server = Server(); server.empty = True
        with patch('thlib.tactic_classes.server_start', return_value=server):
            def wait():
                deadline = time.monotonic() + 10
                while controller.busy and time.monotonic() < deadline: QTest.qWait(5)
                self.assertFalse(controller.busy)
                frame(window)
            view = surface.create(QML/'features/administration/plugins/AdminPluginsView.qml',
                dict(theme=surface.theme,controller=controller,width=1000,height=780,saveActionsInHeader=False))
            window = QQuickWindow(); window.setColor(QColor(surface.theme.property('workspace')))
            window.resize(1000,780); surface.windows.append(window)
            view.setParentItem(window.contentItem()); window.show()
            controller.activate('one'); wait()

            def capture(state, names):
                if not os.environ.get('PLUGINS_OUTPUT'): return
                import json
                from pathlib import Path
                folder = Path(os.environ['PLUGINS_OUTPUT']); folder.mkdir(parents=True,exist_ok=True)
                for language in ('en','ru'):
                    view.setProperty('language',language)
                    for width in (620,1000):
                        window.resize(width,780); view.setWidth(width); frame(window)
                        boxes = {}
                        for name in names:
                            item = surface.item(view,name); point = item.mapToScene(QPointF())
                            boxes[name] = dict(x=point.x(),y=point.y(),width=item.width(),height=item.height())
                            self.assertLessEqual(point.x() + item.width(), width + .5)
                            if item.property('contentHeight') is not None and item.property('text') is not None:
                                self.assertLessEqual(item.property('contentHeight'),item.height() + .5,name)
                        stem = 'guided-%s-%s-%s' % (state,width,language)
                        (folder/(stem+'.json')).write_text(json.dumps(boxes),encoding='utf-8')
                        window.grabWindow().save(str(folder/(stem+'.png')))
                window.resize(1000,780); view.setWidth(1000); view.setProperty('language','en'); frame(window)

            capture('start',['pluginWelcomeTitle','pluginWelcomeIntro','pluginEmptyInstall','pluginEmptyNew'])
            surface.click(window,surface.item(view,'pluginEmptyNew')); wait()
            self.assertFalse(surface.item(view,'pluginCreate').property('enabled'))
            capture('create',['pluginTitle','pluginCreateIntro','pluginField_title','pluginField_code','pluginCreate','pluginCancelCreate'])
            surface.click(window,surface.item(view,'pluginCancelCreate')); wait()
            self.assertEqual(controller.document,{})
            surface.click(window,surface.item(view,'pluginEmptyInstall')); frame(window)
            capture('zip',['pluginOperationTitle','pluginInstallSource','pluginZipInstructions','pluginBrowseZip','pluginCancel'])
            surface.click(window,surface.item(view,'pluginInstallSource_url')); frame(window)
            self.assertFalse(surface.item(view,'pluginConfirm').property('enabled'))
            surface.fill(window,surface.item(view,'pluginInstall_url'),'https://example.org/plugin.zip')
            capture('url',['pluginOperationTitle','pluginInstallSource','pluginInstall_url','pluginConfirm','pluginCancel'])
            surface.click(window,surface.item(view,'pluginConfirm')); wait()
            self.assertEqual(server.calls[-1]['action'],'download_url')
            self.assertFalse(server.active,'Staging must not activate a package')
            self.assertIn('Package added',surface.item(view,'pluginResult').property('text'))
            surface.click(window,surface.item(view,'pluginAction_activate')); frame(window)
            self.assertFalse(server.active,'Review must not activate a package')
            capture('activation',['pluginOperationTitle','pluginOperationContext','pluginConfirm','pluginCancel'])
            surface.click(window,surface.item(view,'pluginConfirm')); wait()
            self.assertTrue(server.active)
            self.assertEqual(surface.item(view,'pluginResult').property('text'),'Plugin is now active in this project.')
            surface.click(window,surface.item(view,'pluginToolsButton')); frame(window)
            QTest.keyClick(window,Qt.Key_Escape); frame(window)
            surface.click(window,surface.item(view,'pluginInstall')); frame(window)
            server.empty = True
            controller.activate('two'); wait()
            self.assertEqual(surface.value(view,'ui'),dict(query='',activeOnly=False,tab='info',operation='',value='',url='',checksum='',collapsed=False,source='zip',notice='',resourceAdd=False,resourceKind='widget',resourceName='',resourceType='',resourceCode='',resourceSchema=False,resourceMode='source'))
            self.assertTrue(surface.item(view,'pluginEmptyInstall').isVisible())
            self.assertFalse(surface.warnings,'\n'.join(surface.warnings))

    def test_real_native_editor_actions_geometry_error_recovery_and_no_polling(self):
        isolate_chat_settings(self)
        surface = ScriptToolsTests(); surface.setUp(); self.addCleanup(surface.doCleanups)
        for name, value in qml_icon_bindings(QML.parents[2], surface.engine).items():
            surface.engine.rootContext().setContextProperty(name, value)
        owner = SimpleNamespace(can_manage_tools=True, debug_log=None)
        controller = PluginsEditor(owner)
        self.addCleanup(controller.shutdown)
        server = Server()
        with patch('thlib.tactic_classes.server_start', return_value=server):
            def wait():
                deadline = time.monotonic() + 10
                while controller.busy and time.monotonic() < deadline:
                    QTest.qWait(5)
                self.assertFalse(controller.busy)
                QTest.qWait(15)
            controller.activate('one'); wait()
            self.assertFalse(controller.error, controller.error)
            view = surface.create(QML/'features/administration/plugins/AdminPluginsView.qml',
                dict(theme=surface.theme, controller=controller, width=1000, height=780, saveActionsInHeader=False))
            window = QQuickWindow(); window.setColor(QColor(surface.theme.property('workspace'))); window.resize(1000, 780); surface.windows.append(window)
            view.setParentItem(window.contentItem()); window.show(); frame(window)
            self.assertEqual(surface.item(view, 'pluginTitle').property('text'), 'Example plugin')
            surface.click(window, surface.item(view, 'pluginAction_activate')); frame(window)
            surface.click(window, surface.item(view, 'pluginConfirm')); wait(); frame(window)
            surface.click(window, surface.item(view, 'pluginAction_deactivate')); frame(window)
            surface.item(view, 'pluginConfirm').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Space); wait(); frame(window)
            self.assertFalse(server.active)
            view.dispatch(dict(type='tab',value='details')); frame(window)
            surface.fill(window, surface.item(view, 'pluginField_title'), 'Edited plugin')
            surface.click(window, surface.item(view, 'pluginSave')); wait(); frame(window)
            self.assertEqual(server.calls[-1]['document']['title'], 'Edited plugin')
            self.assertIn('title', server.calls[-1]['changed_fields'])
            view.dispatch(dict(type='tab',value='info')); frame(window)
            for language in ('en', 'ru'):
                view.setProperty('language', language)
                for width in (620, 1000):
                    window.resize(width, 780); view.setWidth(width); frame(window)
                    title = surface.item(view, 'pluginTitle')
                    self.assertLessEqual(title.x() + title.width(), width)
                    if os.environ.get('PLUGINS_OUTPUT'):
                        from pathlib import Path
                        folder = Path(os.environ['PLUGINS_OUTPUT']); folder.mkdir(parents=True, exist_ok=True)
                        window.grabWindow().save(str(folder / ('plugins-%s-%s.png' % (width, language))))
            window.resize(1000, 780); view.setWidth(1000); view.setProperty('language', 'en'); frame(window)
            view.dispatch(dict(type='tab', value='files')); frame(window)
            surface.click(window, surface.item(view, 'pluginFile_README.md')); wait(); frame(window)
            surface.fill(window, surface.item(view, 'scriptEditorSourceText'), '# Documentation changed')
            surface.click(window, surface.item(view, 'pluginSave')); wait(); frame(window)
            self.assertEqual(server.calls[-1]['document']['file']['content'], '# Documentation changed')
            surface.click(window, surface.item(view, 'pluginNew')); wait(); frame(window)
            self.assertFalse(surface.item(view, 'pluginCreate').property('enabled'))
            surface.fill(window, surface.item(view, 'pluginField_title'), 'Brand new')
            surface.fill(window, surface.item(view, 'pluginField_code'), 'brand_new')
            surface.item(view, 'pluginEditorScroll').setProperty('contentY', 100)
            surface.click(window, surface.item(view, 'pluginCreate')); wait(); frame(window)
            self.assertEqual(server.calls[-1]['action'], 'create')
            self.assertEqual(surface.item(view, 'pluginEditorScroll').property('contentY'), 0)
            server.error = 'Fixture access denied'
            surface.click(window, surface.item(view, 'pluginAction_activate')); frame(window)
            surface.click(window, surface.item(view, 'pluginConfirm')); wait(); frame(window)
            self.assertTrue(controller.uncertain)
            self.assertFalse(surface.item(view, 'pluginAction_activate').property('enabled'))
            server.error = ''
            surface.click(window, surface.item(view, 'pluginReload')); wait(); frame(window)
            self.assertFalse(controller.error, controller.error)
            self.assertFalse(controller.uncertain)
            count = len(server.calls); QTest.qWait(100)
            self.assertEqual(count, len(server.calls), 'No idle polling')
            self.assertFalse(surface.warnings, '\n'.join(surface.warnings))

    def test_permissions_stale_results_and_upload_keep_native_scope(self):
        isolate_chat_settings(self)
        owner = SimpleNamespace(can_manage_tools=False, debug_log=None)
        controller = PluginsEditor(owner); self.addCleanup(controller.shutdown)
        server = Server()
        with patch('thlib.tactic_classes.server_start', return_value=server):
            controller.activate('one')
            self.assertFalse(server.calls)
            self.assertIn('administrator', controller.error)
            owner.can_manage_tools = True
            controller._project = 'one'
            controller._identity = ROW['identity']
            controller._revision = 'revision-1'
            controller._metadata = deepcopy(DOCUMENT['metadata'])
            result = controller._execute_request(dict(action='upload', project_code='one',
                upload_path='D:/private/example.txt', path='example.txt'), 'one', {})
            self.assertEqual(server.uploads, ['D:/private/example.txt'])
            self.assertEqual(server.calls[-1]['upload_file_name'], 'example.txt')
            self.assertEqual(result['identity'], ROW['identity'])
            controller._document = deepcopy(DOCUMENT['document'])
            controller._document['file'] = dict(path='README.md', content='# Example', revision='file-1')
            controller._original = deepcopy(controller._document)
            controller.upload(QUrl.fromLocalFile('D:/private/replacement.txt'), False, True)
            deadline = time.monotonic() + 10
            while controller.busy and time.monotonic() < deadline:
                QTest.qWait(5)
            self.assertFalse(controller.busy)
            self.assertEqual(server.calls[-1]['path'], 'README.md')
            self.assertTrue(server.calls[-1]['confirmation'])

    def test_administration_navigation_hosts_plugins_and_protects_the_project(self):
        from tests import test_administration_qml as administration_fixture
        administration_fixture.AdministrationQmlTests.setUpClass()
        fixture = administration_fixture.AdministrationQmlTests()
        self.addCleanup(fixture.doCleanups); fixture.setUp()
        server = Server()
        with patch('thlib.tactic_classes.server_start', return_value=server):
            fixture.admin.pluginsEditor._loaded = False
            fixture.click('adminSection_plugins')
            deadline = time.monotonic() + 10
            while fixture.admin.pluginsEditor.busy and time.monotonic() < deadline:
                QTest.qWait(5)
            frame(fixture.window)
            self.assertEqual(fixture.admin.section, 'plugins')
            self.assertFalse(fixture.fixture.warnings, '\n'.join(fixture.fixture.warnings))
            self.assertFalse(fixture.admin.pluginsEditor.error, fixture.admin.pluginsEditor.error)
            self.assertTrue(fixture.admin.pluginsEditor.identity, repr(server.calls))
            self.assertEqual(fixture.item('pluginTitle').property('text'), 'Example plugin')
            editor = fixture.admin.pluginsEditor
            editor.set_field('title', 'Unsaved plugin title')
            self.assertTrue(fixture.admin.projectLocked)
            previous = fixture.admin.project
            fixture.admin.select_project('other')
            self.assertEqual(fixture.admin.project, previous)
            editor.discard()
            self.assertFalse(fixture.admin.projectLocked)
            self.assertFalse(fixture.fixture.warnings, '\n'.join(fixture.fixture.warnings))


if __name__ == '__main__': unittest.main()
