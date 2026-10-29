"""Real table-button clicks drive the existing dock visibility owner."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import tests.test_frame_table as frames
from tests.test_sobject_info_entrypoint import _ItemOperationsHarness, _sobject_node
from thlib.ui.workspace_models.docks import DockPanelModel


class TableCheckinToggleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    click = frames.FrameTableTests.click
    item = frames.FrameTableTests.item

    def test_checkin_button_shows_hides_and_reopens_without_preparing_on_hide(self):
        node = _sobject_node()
        owner = _ItemOperationsHarness(node)
        owner.dock_model = DockPanelModel({})
        owner._checkin_target_for_node = lambda selected: dict(searchKey=selected.search_key)
        owner._prepare_checkin_target = Mock(return_value=True)
        owner._checkin_controller = SimpleNamespace(set_process_and_context=Mock())
        cell = dict(available=True, process='model', context='model/review', checkinMode='sequence', transferMode='move')
        window, view = self.create('TacticTableActionCell.qml', dict(kind='checkin', cell=cell), width=100, height=58)
        view.clicked.connect(lambda: owner.invoke_table_widget_action('checkin', node.node_id, cell))
        button = self.item(view, 'tableCellCheckin')
        self.assertFalse(owner.dock_model.is_panel_presented('drop_plate'))
        self.click(window, button)
        self.assertTrue(owner.dock_model.is_panel_presented('drop_plate'))
        self.assertEqual(owner._prepare_checkin_target.call_count, 1)
        self.assertEqual(owner._prepare_checkin_target.call_args.args[0]['context'], 'model/review')
        owner._pending_table_checkin = dict(targetSearchKey='pending-parent')
        self.click(window, button)
        self.assertFalse(owner.dock_model.is_panel_visible('drop_plate'))
        self.assertEqual(owner._prepare_checkin_target.call_count, 1)
        self.assertEqual(owner._pending_table_checkin, {})
        self.click(window, button)
        self.assertTrue(owner.dock_model.is_panel_presented('drop_plate'))
        self.assertEqual(owner._prepare_checkin_target.call_count, 2)

        # A covered tab must be raised, rather than hidden while already invisible.
        owner.dock_model.show_panel('tasks')
        owner.dock_model.place_panel('tasks', 'drop_plate', 'center')
        self.assertFalse(owner.dock_model.is_panel_presented('drop_plate'))
        self.click(window, button)
        self.assertTrue(owner.dock_model.is_panel_presented('drop_plate'))

        owner.dock_model.float_panel('drop_plate', .2, .2, .4, .4)
        self.click(window, button)
        self.assertFalse(owner.dock_model.is_panel_visible('drop_plate'))
