"""Actual gallery input and the existing scoped checkout owner."""

import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
import tests.test_frame_table as frames
import tests.test_table_nested as nested
from tests.test_columns_table_view import _visual_items


FIXTURE = Path(__file__).parent / 'fixtures/table_snapshot_gallery.json'


class SnapshotGalleryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = nested.NestedTableTests.create
    close = nested.NestedTableTests.close
    click = nested.NestedTableTests.click
    item = nested.NestedTableTests.item

    def fixture(self, width=800):
        scope = nested.Scope()
        scope.state = json.loads(FIXTURE.read_text(encoding='utf-8'))
        scope.state.update(scope.state.pop('scope'))
        window, view = self.create(
            'features/table/NestedTableView.qml',
            dict(
                controller=frames._TableController(),
                columnsController=frames._TableColumns(),
                userModel=None,
                services=None,
                administration=None,
                scope=scope,
            ),
            width=width,
            height=320,
        )
        return scope, window, view

    def test_gallery_pointer_keyboard_and_narrow_resize_keep_rows_virtualized(self):
        scope, window, view = self.fixture()
        cards = [
            item
            for item in _visual_items(view)
            if item.objectName().startswith('nestedSnapshot_')
        ]
        self.assertGreater(len(cards), 0)
        self.assertLess(len(cards), len(scope.state['rows']))
        first_name = 'nestedSnapshot_' + scope.state['rows'][0]['key']
        self.click(window, self.item(view, first_name))
        self.assertEqual(
            scope.events[-1][0],
            dict(type='gallery-open', key=scope.state['rows'][0]['key']),
        )
        first = self.item(view, first_name)
        first.forceActiveFocus()
        window.requestActivate()
        QTest.qWait(30)
        QTest.keyClick(window, Qt.Key_Space)
        frames.frame(window)
        self.assertEqual(len(scope.events), 2)
        self.assertTrue(
            all(event[0]['type'] == 'gallery-open' for event in scope.events)
        )
        window.resize(360, 320)
        view.setWidth(360)
        frames.frame(window)
        preview = self.item(
            view, 'nestedSnapshotPreview_' + scope.state['rows'][0]['key']
        )
        self.assertEqual(preview.width(), 150)
        self.assertFalse(preview.property('round'))
        self.assertEqual(preview.property('fillMode'), 1)  # PreserveAspectFit
        self.assertFalse(
            any(
                item.objectName() == 'nestedHeaderSurface'
                for item in _visual_items(view)
            )
        )
        bar = self.item(view, 'nestedGalleryScrollBar')
        self.assertTrue(bar.property('visible'))
        self.assertTrue(bar.property('hasOverflow'))
        scope.state.update(rows=[], hasNext=False)
        scope.changed.emit()
        frames.frame(window)
        self.assertEqual(
            self.item(view, 'nestedGalleryEmpty').property('text'), 'No snapshots found'
        )

    def test_gallery_uses_checkout_only_for_a_current_visible_record(self):
        from thlib.ui.table.nested import NestedTableController
        from thlib.ui.table.services import TableServicesController
        import tests.test_table_service_workflows as workflows

        app = workflows.Application()
        services = TableServicesController(app)
        self.addCleanup(services.shutdown)
        scope = NestedTableController(
            services,
            'A',
            dict(
                searchType='sthpw/snapshot',
                parentKey=app.node.search_key,
                projectCode='demo',
                gallery=dict(scale=150),
            ),
        )
        scope._nodes['nested:S'] = SimpleNamespace(
            node_id='nested:S', search_key='sthpw/snapshot?code=S'
        )
        with (
            patch.object(services, 'scope_visible', return_value=True),
            patch.object(services, 'open_checkout') as opened,
        ):
            scope.activate(dict(type='gallery-open', key='sthpw/snapshot?code=S'))
            opened.assert_called_once_with(
                'nested:S',
                dict(targetSearchKey='sthpw/snapshot?code=S', projectCode='demo'),
            )
            scope.activate(dict(type='gallery-open', key='sthpw/snapshot?code=other'))
            self.assertEqual(opened.call_count, 1)
        with (
            patch.object(services, 'scope_visible', return_value=False),
            patch.object(services, 'open_checkout') as opened,
        ):
            scope.activate(dict(type='gallery-open', key='sthpw/snapshot?code=S'))
            opened.assert_not_called()
        scope.shutdown()


if __name__ == '__main__':
    unittest.main()
