"""Real native chart paint, hover, resizing and palette changes."""
import unittest

from PySide6.QtCore import QPoint
from PySide6.QtQml import QJSEngine
from PySide6.QtTest import QTest

from tests import test_frame_table as frames


class FrameChartsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item

    def test_native_chart_types_hover_resize_and_palette(self):
        engine = QJSEngine()
        module = engine.importModule(str(frames.QML / 'tactic_frame/controls/charts/chart.ui.mjs'))
        self.assertFalse(module.isError(), module.toString())
        for kind in ('bar', 'line', 'donut'):
            data = dict(type=kind, labels=['First', 'Second', 'Missing', 'Fourth'],
                        values=[12, 4, None, 8])
            result = module.property('describe').call([
                engine.toScriptValue(data), engine.toScriptValue('chart'),
                engine.toScriptValue(520), engine.toScriptValue(240),
                engine.toScriptValue('en')])
            self.assertFalse(result.isError(), result.toString())
            window, view = self.create('tactic_frame/core/FrameView.qml',
                dict(scene=result.toVariant()), width=520, height=240)
            chart = self.item(view, 'chart_plot')
            g = chart.property('node')['chart']
            point = (QPoint(round(g['cx']), round(g['cy'] - (g['radius'] + g['inner']) / 2))
                     if kind == 'donut' else QPoint(round(g['marks'][1]['x']), 40))
            window.requestActivate()
            QTest.qWait(40)
            QTest.mouseMove(window, QPoint(1, 1))
            QTest.mouseMove(window, point)
            frames.frame(window)
            self.assertGreaterEqual(chart.property('hovered'), 0)
            self.assertTrue(chart.property('tip'))
            window.resize(600, 280)
            frames.frame(window)
            self.assertFalse(window.grabWindow().isNull())
            chart.property('theme').setProperty('dark', False)
            frames.frame(window)
            window.hide()


if __name__ == '__main__':
    unittest.main()
