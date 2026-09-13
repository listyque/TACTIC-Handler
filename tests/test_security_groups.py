"""Security writes use native membership APIs and preserve unrelated edits."""

from copy import deepcopy
import json
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from thlib.ui import security_store


class SecurityStoreTests(unittest.TestCase):
    def setUp(self):
        self.tables = {
            'sthpw/login_group': [dict(code='G1', login_group='artists',
                                      description='Artists', access_rules='<rules/>')],
            'sthpw/login': [dict(login=name, password='must-not-be-returned')
                            for name in ('alice', 'bob', 'charlie')],
            'sthpw/login_in_group': [dict(login='alice', login_group='artists'),
                                     dict(login='charlie', login_group='artists')],
        }
        self.calls = []
        fixture = self

        class NativeObject:
            def __init__(self, table, data, new=False):
                self.table, self.data, self.new = table, data, new

            def get_value(self, name, **_):
                return self.data.get(name, '')

            def get_data(self):
                return dict(self.data)

            def set_value(self, name, value):
                self.data[name] = value

            def commit(self):
                if self.new:
                    self.data['code'] = 'G2'
                    fixture.tables[self.table].append(self.data)
                    self.new = False

            def add_to_group(self, group):
                fixture.calls.append(('add', self.data['login'], group))
                fixture.tables['sthpw/login_in_group'].append(
                    dict(login=self.data['login'], login_group=group))

            def remove_from_group(self, group):
                fixture.calls.append(('remove', self.data['login'], group))
                fixture.tables['sthpw/login_in_group'][:] = [
                    row for row in fixture.tables['sthpw/login_in_group']
                    if (row['login'], row['login_group']) != (self.data['login'], group)]

        class Search:
            def __init__(self, table):
                self.table, self.filters = table, []
                self.show_retired = False

            def set_show_retired(self, show):
                self.show_retired = show

            def add_filter(self, name, value):
                self.filters.append((name, [value]))

            def add_filters(self, name, values):
                self.filters.append((name, values))

            def get_sobjects(self):
                return [NativeObject(self.table, row) for row in fixture.tables[self.table]
                        if all(row.get(name) in values for name, values in self.filters)
                        and (self.show_retired or row.get('s_status') != 'retired')]

            def get_sobject(self):
                return next(iter(self.get_sobjects()), None)

        self.enterContext(patch.dict(sys.modules, {'pyasm.search': SimpleNamespace(
            Search=Search, SearchType=SimpleNamespace(
                create=lambda table: NativeObject(table, {}, True)))}))
        self.server = SimpleNamespace(get_login=lambda: 'admin')
        self.enterContext(patch.object(security_store, 'server', self.server, create=True))
        self.enterContext(patch.dict(sys.modules, {'pyasm.common': SimpleNamespace(
            Environment=SimpleNamespace(get_security=lambda: SimpleNamespace(
                is_admin=lambda: self.server.get_login() == 'admin')))}))

    def test_link_unlink_is_idempotent_and_does_not_remove_concurrent_member(self):
        for _ in range(2):
            security_store.save_security_group('G1', 'artists', 'New description', ['bob'], ['alice'])
        self.assertEqual(self.calls, [('add', 'bob', 'artists'), ('remove', 'alice', 'artists')])
        self.assertEqual({row['login'] for row in self.tables['sthpw/login_in_group']},
                         {'bob', 'charlie'})
        self.assertEqual(self.tables['sthpw/login_group'][0]['access_rules'], '<rules/>')

    def test_create_and_retry_keep_one_group(self):
        for _ in range(2):
            security_store.save_security_group('', 'lighting', 'Lighting team', ['bob'], [])
        self.assertEqual(len(self.tables['sthpw/login_group']), 2)
        self.assertEqual(self.calls, [('add', 'bob', 'lighting')])

    def test_create_does_not_modify_an_existing_group_with_the_same_name(self):
        original = deepcopy(self.tables)
        with self.assertRaises(ValueError):
            security_store.save_security_group('', 'artists', 'Artists', ['bob'], [])
        self.assertEqual(self.tables, original)

    def test_missing_user_and_unprivileged_requests_fail_before_writes(self):
        original = deepcopy(self.tables)
        with self.assertRaises(ValueError):
            security_store.save_security_group('G1', 'artists', 'Changed', ['missing'], [])
        self.server.get_login = lambda: 'bob'
        with self.assertRaises(PermissionError):
            security_store.save_security_group('G1', 'artists', 'Changed', [], ['alice'])
        self.assertEqual(self.tables, original)

    def test_catalog_never_returns_login_passwords(self):
        payload = json.loads(security_store.query_security_groups())
        self.assertEqual(len(payload['users']), len(self.tables['sthpw/login']))
        self.assertNotIn('must-not-be-returned', str(payload))

    def test_retired_members_remain_visible_and_can_be_unlinked(self):
        self.tables['sthpw/login'][0]['s_status'] = 'retired'
        payload = json.loads(security_store.query_security_groups())
        self.assertTrue(payload['users'][0]['retired'])
        security_store.save_security_group('G1', 'artists', 'Artists', [], ['alice'])
        self.assertEqual(self.calls, [('remove', 'alice', 'artists')])


if __name__ == '__main__':
    unittest.main()
