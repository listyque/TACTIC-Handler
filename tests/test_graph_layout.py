"""Deterministic automatic layouts shared by both administration graphs."""

import unittest

from thlib.ui.admin.graph_layout import layout_graph


class GraphLayoutTests(unittest.TestCase):
    def setUp(self):
        self.nodes = [
            {'identity': identity, 'label': label}
            for identity, label in (
                ('render', 'Render'), ('model', 'Model'), ('rig', 'Rig'),
                ('publish', 'Publish'), ('z_orphan', 'Z orphan'),
                ('a_orphan', 'A orphan'), ('m_orphan', 'M orphan'),
                ('b_orphan', 'B orphan'),
            )
        ]
        self.edges = [
            {'from': 'model', 'to': 'rig'},
            {'from': 'rig', 'to': 'render'},
            {'from': 'render', 'to': 'publish'},
        ]

    @staticmethod
    def positions(records):
        return {row['identity']: (row['nodeX'], row['nodeY']) for row in records}

    def test_flow_keeps_direction_and_puts_orphans_in_alphabetical_rows(self):
        positions = self.positions(layout_graph(self.nodes, self.edges, 'flow'))
        self.assertLess(positions['model'][0], positions['rig'][0])
        self.assertLess(positions['rig'][0], positions['render'][0])
        self.assertLess(positions['render'][0], positions['publish'][0])
        orphan_y = {positions[name][1] for name in (
            'a_orphan', 'b_orphan', 'm_orphan', 'z_orphan')}
        self.assertLess(len(orphan_y), 4, 'orphans must wrap instead of forming one column')
        self.assertEqual(positions['a_orphan'][1], positions['b_orphan'][1])
        self.assertLess(positions['a_orphan'][0], positions['b_orphan'][0])

    def test_network_is_a_deterministic_web_and_grid_is_bounded(self):
        network = layout_graph(self.nodes, self.edges, 'network')
        reversed_input = layout_graph(list(reversed(self.nodes)), list(reversed(self.edges)), 'network')
        self.assertEqual(network, reversed_input)
        connected = [self.positions(network)[name] for name in ('model', 'rig', 'render', 'publish')]
        self.assertEqual(len(set(connected)), 4)

        many = [{'identity': 'node_%02d' % index, 'label': 'Node %02d' % index}
                for index in range(30)]
        grid = self.positions(layout_graph(many, [], 'grid'))
        self.assertGreater(len({point[1] for point in grid.values()}), 1)
        self.assertLessEqual(max(
            sum(point[1] == row for point in grid.values())
            for row in {point[1] for point in grid.values()}), 6)

    def test_reference_nodes_are_not_returned_and_unknown_layout_is_rejected(self):
        nodes = self.nodes + [{'identity': 'missing', 'label': 'Missing', 'referenceOnly': True}]
        self.assertNotIn('missing', self.positions(layout_graph(nodes, self.edges, 'flow')))
        with self.assertRaisesRegex(ValueError, 'Unknown graph layout'):
            layout_graph(self.nodes, self.edges, 'spiral')


if __name__ == '__main__':
    unittest.main()
