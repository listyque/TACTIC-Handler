"""Configured cards use real native fields, counted controls and pointer actions."""
import unittest

from PySide6.QtCore import QObject, Slot
from tests import test_frame_table as frames


class Actions(QObject):
    def __init__(self):
        super().__init__()
        self.calls = []

    @Slot(str, str)
    def invoke_item_action(self, action, node_id):
        self.calls.append((action, node_id))


class ItemCardFields(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item
    click = frames.FrameTableTests.click

    def test_formatted_fields_and_counted_actions_resize_and_click(self):
        def element(name, kind, row, **options):
            return dict(name=name, kind=kind, row=row, column=1, span=12,
                        rows=1, height=22, parent='', variant='all', options=options)

        controller = Actions()
        layout = dict(flow='grid', collection='tree', columns=12, gap=4, elements=[
            element('state', 'field', 1, bind='record.status', format='badge',
                    colors='{"Review":"yellow"}'),
            element('due', 'field', 2, bind='record.due', format='date', text='Due date'),
            element('progress', 'field', 3, bind='record.progress', format='progress', color='green'),
            element('tasks', 'button', 4, action='tasks', icon='task', badge='node.task_count'),
            element('notes', 'button', 5, action='notes', badge='node.note_count')
        ])
        window, view = self.create('features/search/ConfiguredItem.qml', dict(
            controller=controller, nodeId='demo/record?code=P1', layout=layout,
            record=dict(kind='object', record=dict(status='Review', due='2026-11-12 00:00:00', progress=45),
                        task_count=5, note_count=3)), width=600, height=300)
        tasks = self.item(view, 'itemComposition_tasksButton')
        for width in (600, 320, 240, 480, 360) * 4:
            window.resize(width, 300)
            view.setWidth(width)
            frames.frame(window)
            self.assertEqual(self.item(view, 'itemComposition_tasksButton'), tasks)
            self.assertEqual(tasks.width(), tasks.height())
            self.assertGreaterEqual(tasks.width(), 30)
            self.assertEqual(tasks.property('badgeCount'), 5)
            self.assertEqual(self.item(view, 'itemComposition_dueValue').property('text'), '2026-11-12')
            self.assertEqual(self.item(view, 'itemComposition_progressValue').property('text'), '45%')
            self.assertEqual(self.item(view, 'itemComposition_stateValue').property('text'), 'Review')
            self.assertEqual(self.item(view, 'itemComposition_notesButton').property('text'), 'Notes · 3')
        self.click(window, tasks)
        self.click(window, self.item(view, 'itemComposition_notesButton'))
        self.assertEqual(controller.calls, [('tasks', 'demo/record?code=P1'), ('notes', 'demo/record?code=P1')])
        layout['elements'][-1]['span'] = 6
        view.setProperty('layout', layout)
        view.setWidth(240)
        frames.frame(window)
        notes = self.item(view, 'itemComposition_notesButton')
        self.assertEqual(notes.property('text'), '3')
        self.assertEqual(notes.property('toolTip'), 'Notes · 3')
        self.click(window, notes)
        self.assertEqual(controller.calls[-1], ('notes', 'demo/record?code=P1'))


if __name__ == '__main__':
    unittest.main()
