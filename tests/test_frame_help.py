"""Exercise the shipped Help Frame screen with actual Qt controls and local articles."""
import unittest
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl, Qt, QCoreApplication, QEvent
from PySide6.QtQml import QQmlEngine, QQmlComponent, QQmlExpression
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
import tests.test_sidebar_editor_qml as sidebar_fixture
from thlib.ui.help import HelpController
from thlib.ui.icon_font import qml_icon_bindings

ROOT = Path(__file__).resolve().parents[1]
class Localization(QObject):
    languageChanged = Signal()
    language = "en"
    @Property(str, notify=languageChanged)
    def current_language(self): return self.language
    def use(self, value):
        self.language = value
        self.languageChanged.emit()
class Windows(QObject):
    helpRequested = Signal(str)
    @Property(str, constant=True)
    def helpTopic(self): return "overview"
    @Slot(str)
    def close_window(self, name): pass

class FrameHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()
        cls.icons = qml_icon_bindings(ROOT, cls.app)
    def setUp(self):
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda errors: self.warnings.extend(error.toString() for error in errors))
        self.localization = Localization()
        self.windows = Windows()
        self.help = HelpController(ROOT / "thlib/ui/help_articles", self.localization)
        context = self.engine.rootContext()
        for name, value in dict(self.icons, helpController=self.help, windowModel=self.windows, localizationController=self.localization).items():
            context.setContextProperty(name, value)
        self.component = QQmlComponent(self.engine)
        source = 'import QtQuick\nimport QtQuick.Controls\nimport "' + (ROOT/'thlib/ui/qml').as_uri() + '" as TH\nApplicationWindow { visible:true; width:1100; height:740; TH.Theme {id:theme; dark:true} TH.HelpView {id:helpView; theme:theme; anchors.fill:parent} }'
        self.component.setData(source.encode(), QUrl())
        self.assertTrue(self.component.isReady(), [error.toString() for error in self.component.errors()])
        self.window = self.component.create()
        self.assertIsNotNone(self.window)
        frame(self.window)
        self.addCleanup(self.close)
    def close(self):
        self.window.close(); self.window.deleteLater(); self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    def item(self, name):
        return next(item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem()) if item.objectName() == name)
    def evaluate(self, source):
        view = self.item("applicationHelpView")
        expression = QQmlExpression(QQmlEngine.contextForObject(view), view, source.replace("helpView.", ""))
        value, undefined = expression.evaluate()
        self.assertFalse(expression.hasError(), expression.error().toString())
        return value.toVariant() if hasattr(value, 'toVariant') else value
    def wait_for(self, expression):
        from PySide6.QtCore import QElapsedTimer
        timer = QElapsedTimer(); timer.start()
        while not self.evaluate(expression) and timer.elapsed() < 1000:
            QTest.qWait(5)
        self.assertTrue(self.evaluate(expression), expression)

    def test_real_search_filters_native_topic_rows(self):
        search = self.item('helpTopicSearch')
        search.forceActiveFocus()
        for letter in 'windows': QTest.keyClick(self.window, letter)
        frame(self.window)
        self.assertEqual(self.evaluate('helpView.ui.query'), 'windows')
        self.assertGreater(self.evaluate('helpView.scene.topicRows.length'), 0)
        self.assertEqual(self.warnings, [])
    def test_document_scroll_and_hidden_language_are_retained(self):
        self.windows.helpRequested.emit('windows'); frame(self.window)
        self.wait_for('!documentPane.restoring')
        self.evaluate('documentPane.contentItem.contentY = 220'); frame(self.window)
        saved = self.evaluate('ui.positions.windows')
        self.assertGreater(saved, 0)
        self.windows.helpRequested.emit('overview'); frame(self.window)
        self.windows.helpRequested.emit('windows'); frame(self.window)
        self.wait_for('!documentPane.restoring')
        self.assertAlmostEqual(self.evaluate('documentPane.contentItem.contentY'), saved, delta=1)
        self.window.hide(); QCoreApplication.processEvents()
        from unittest.mock import patch
        with patch.object(self.help, '_load_articles', wraps=self.help._load_articles) as load:
            self.localization.use('ru'); QCoreApplication.processEvents()
            load.assert_not_called()
            self.window.show(); frame(self.window)
            load.assert_called_once_with('ru')
        self.assertEqual(self.help.selected_topic_id, 'windows')
        self.assertIn('Окна', self.help.article['title'])
        self.assertEqual(self.warnings, [])

    def test_help_window_owner_reopen_and_proxy_retention(self):
        from unittest.mock import patch
        from thlib.ui.workspace_models.windows import FloatingWindowModel, VisibleFloatingWindowModel
        model = FloatingWindowModel({})
        calls = []; model.helpRequested.connect(calls.append)
        proxy = VisibleFloatingWindowModel(model)
        with patch.object(model, '_save'):
            model.show_window('administration')
            model.open_help('windows')
            model.open_help('windows')
            self.assertEqual(calls, ['windows', 'windows'])
            self.assertEqual(model.data(model.index(model._row('help'),0), model.ParentWindowRole), 'administration')
            model.close_window('administration')
            self.assertFalse(model.data(model.index(model._row('help'),0), model.VisibleRole))
            proxy._release_hidden_rows()
            self.assertTrue(proxy.mapFromSource(model.index(model._row('help'),0)).isValid())
            model.open_help()
            self.assertEqual(calls[-1], '')
            self.assertEqual(model.data(model.index(model._row('help'),0), model.ParentWindowRole), '')

    def test_export_is_exact_and_rejects_nonlocal_targets(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            target = Path(directory) / "article.md"
            self.assertTrue(self.help.save_current_file(QUrl.fromLocalFile(str(target))))
            self.assertEqual(target.read_bytes(), Path(self.help.article["filePath"]).read_bytes())
            self.assertFalse(self.help.save_current_file(QUrl("https://example.test/article.md")))
            self.assertTrue(self.help.error)
            self.assertFalse(self.help.save_current_file(QUrl.fromLocalFile(str(Path(directory)/"missing"/"article.md"))))
            self.assertTrue(target.read_bytes())

    def test_explicit_context_and_phone_topics_use_same_state(self):
        self.windows.helpRequested.emit('search')
        frame(self.window)
        self.assertEqual(self.help.selected_topic_id, 'search')
        self.window.resize(360, 740); frame(self.window)
        self.assertTrue(self.evaluate('helpView.scene.compact'))
        self.assertFalse(self.item('helpTopicsPanel').isVisible())
        self.item('helpShowTopics').forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space); frame(self.window)
        self.assertTrue(self.item('helpTopicsPanel').isVisible())
        self.assertEqual(self.warnings, [])

if __name__ == '__main__': unittest.main()
