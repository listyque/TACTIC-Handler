"""Native Login contracts: retired reads, profile writes, authority and secrets."""

import copy
import json
import sys
import textwrap
from types import SimpleNamespace
from unittest.mock import patch

import tests.test_security_groups as groups_fixture
from thlib import tactic_query as tq
from thlib.ui.admin.users_api import query_admin_users


class AdminUserApiTests(groups_fixture.SecurityStoreTests):
    def setUp(self):
        super().setUp()
        self.tables['sthpw/snapshot'] = []
        self.tables['sthpw/login'].append(dict(login='retired_artist', code='retired_artist',
                                               s_status='retired', password='secret-hash'))
        for row in self.tables['sthpw/login']:
            row.setdefault('code', row['login'])
        self.native_search = sys.modules['pyasm.search']
        self.native_search.SearchKey = SimpleNamespace(
            get_by_sobject=lambda item, **_: item.table + '?code=' + item.get_value('code'))
        # Address is not a standard login column; absent fields must not be
        # offered by the admin form or sent back as empty values on creation.
        self.native_search.SearchType.get_columns = lambda _: [
            'code', 'login', 'upn', 'first_name', 'last_name', 'display_name',
            'email', 'phone_number', 'department', 'namespace', 's_status',
            'project_code', 'license_type', 'hourly_wage', 'password', 'data']
        self.native_search.Search.add_relationship_filters = lambda *_args, **_kwargs: None
        self.snapshot_api = SimpleNamespace(
            get_files_dict_by_snapshots=lambda _: {})
        self.enterContext(patch.dict(sys.modules, {'pyasm.biz': SimpleNamespace(
            Snapshot=self.snapshot_api)}))
        self.enterContext(patch.object(tq, 'server', self.server, create=True))
        self.native_object = type(self.native_search.Search('sthpw/login').get_sobject())
        self.native_object.get_code = lambda item: item.get_value('code')
        self.native_object.get_version = lambda item: item.get_value('version')
        self.native_object.is_latest = lambda item: bool(
            item.get_value('is_latest'))

        def set_password(login, password):
            self.calls.append(('password', login.get_value('login')))
            login.set_value('password', 'hashed-test-value')

        def retire(login):
            self.calls.append(('retire', login.get_value('login')))
            login.set_value('s_status', 'retired')

        def reactivate(login):
            self.calls.append(('reactivate', login.get_value('login')))
            login.set_value('s_status', None)

        def create(login, password, groups, project_code):
            self.calls.append(('create', login))
            row = dict(login=login, code=login, upn=login, password='hashed-test-value')
            self.tables['sthpw/login'].append(row)
            return self.native_object('sthpw/login', row)

        self.native_object.set_password = set_password
        self.native_object.retire = retire
        self.native_object.reactivate = reactivate
        self.enterContext(patch.dict(sys.modules, {'pyasm.security': SimpleNamespace(
            Login=SimpleNamespace(create=create))}))

    def test_directory_includes_retired_but_never_credentials_or_absent_columns(self):
        self.tables['sthpw/login'][0]['hourly_wage'] = 0
        result = json.loads(query_admin_users())
        rows = {row['identity']: row for row in result['catalog']}
        self.assertEqual(rows['retired_artist']['document']['s_status'], 'retired')
        self.assertEqual(rows['alice']['document']['hourly_wage'], 0)
        self.assertNotIn('password', str(result))
        self.assertNotIn('secret-hash', str(result))
        self.assertNotIn('address', result['metadata']['fields'])

    def test_directory_and_writes_require_native_admin_not_a_privileged_name(self):
        original = copy.deepcopy(self.tables)
        self.server.get_login = lambda: 'admin'
        with patch.object(sys.modules['pyasm.common'].Environment, 'get_security',
                          return_value=SimpleNamespace(is_admin=lambda: False)):
            with self.assertRaises(PermissionError):
                query_admin_users()
            with self.assertRaises(PermissionError):
                tq.mutate_user_profile('alice', {'first_name': 'Changed'}, require_admin=True)
            with self.assertRaises(PermissionError):
                tq.create_user_profile('new', require_admin=True)
        self.assertEqual(self.tables, original)

    def test_directory_carries_available_groups_not_only_selected_memberships(self):
        self.tables['sthpw/login_group'].append(dict(
            code='G2', login_group='lighting', description='Lighting team'))
        result = json.loads(query_admin_users())
        self.assertEqual(result['metadata']['groups']['alice'], ['artists'])
        self.assertEqual([row['login_group'] for row in result['metadata']['groupCatalog']],
                         ['artists', 'lighting'])

    def test_directory_serializes_profile_snapshots_without_client_globals(self):
        self.tables['sthpw/snapshot'].append({
            'code': 'SNAPSHOT001',
            'search_code': 'alice',
            'process': 'icon',
            'version': -1,
        })
        file_object = self.native_object('sthpw/file', {
            'code': 'FILE001',
            'snapshot_code': 'SNAPSHOT001',
            'file_name': 'alice.png',
        })
        self.snapshot_api.get_files_dict_by_snapshots = (
            lambda _: {'SNAPSHOT001': [file_object]}
        )

        result = json.loads(query_admin_users())

        alice = next(
            row for row in result['catalog'] if row['identity'] == 'alice'
        )
        snapshot = alice['snapshots'][0]
        self.assertEqual(
            snapshot['__search_key__'],
            'sthpw/snapshot?code=SNAPSHOT001',
        )
        self.assertEqual(
            snapshot['__files__'][0]['__search_key__'],
            'sthpw/file?code=FILE001',
        )

    def test_retired_user_can_be_edited_reactivated_and_retired_through_native_methods(self):
        result = json.loads(tq.mutate_user_profile('retired_artist',
            {'first_name': 'Alex', 's_status': ''}, require_admin=True))
        self.assertEqual(result['first_name'], 'Alex')
        self.assertIsNone(result['s_status'])
        self.assertEqual(self.calls, [('reactivate', 'retired_artist')])
        tq.mutate_user_profile('retired_artist', {'s_status': 'retired'}, require_admin=True)
        tq.mutate_user_profile('retired_artist', {'s_status': 'retired'}, require_admin=True)
        self.assertEqual(self.calls.count(('retire', 'retired_artist')), 1)

    def test_membership_uses_native_login_operations_and_preserves_other_users(self):
        self.tables['sthpw/login_group'].append(dict(code='G2', login_group='lighting'))
        for _ in range(2):
            tq.mutate_user_profile('alice', groups=['lighting'], require_admin=True)
        self.assertEqual(self.calls, [('add', 'alice', 'lighting'), ('remove', 'alice', 'artists')])
        self.assertIn({'login': 'charlie', 'login_group': 'artists'}, self.tables['sthpw/login_in_group'])
        tq.mutate_user_profile('retired_artist', groups=['artists'], require_admin=True)
        self.assertEqual(self.calls[-1], ('add', 'retired_artist', 'artists'))

    def test_cannot_retire_authenticated_account_and_creation_checks_retired_duplicates(self):
        self.tables['sthpw/login'].append(dict(login='admin', code='admin'))
        original = copy.deepcopy(self.tables)
        with self.assertRaises(ValueError):
            tq.mutate_user_profile('admin', {'s_status': 'retired'}, require_admin=True)
        with self.assertRaises(ValueError):
            tq.create_user_profile('retired_artist', require_admin=True)
        self.assertEqual(self.tables, original)

    def test_native_creation_initializes_upn_and_password_is_not_echoed(self):
        result = json.loads(tq.create_user_profile('new_artist',
            {'first_name': 'Alice', 'upn': '', 'hourly_wage': ''},
            password='test-secret', require_admin=True))
        self.assertEqual(result['upn'], 'new_artist')
        self.assertEqual(result['first_name'], 'Alice')
        self.assertNotIn('password', result)
        self.assertNotIn('hourly_wage', result)
        result = json.loads(tq.mutate_user_profile('new_artist', password='changed-secret', require_admin=True))
        self.assertNotIn('password', result)
        self.assertEqual(self.calls[-1], ('password', 'new_artist'))

    def test_rpc_serializer_preserves_admin_flag_and_query_contract(self):
        for endpoint, arguments in (
            (query_admin_users, {}),
            (tq.mutate_user_profile, {'login': 'alice', 'values': {'first_name': 'Alice'}, 'require_admin': True}),
            (tq.create_user_profile, {'login': 'new_artist', 'require_admin': True}),
        ):
            script = tq.prepare_serverside_script(endpoint, arguments,
                shrink=False, catch_traceback=False)['code']
            compile('def execute():\n' + textwrap.indent(script, '    '), '<admin-users>', 'exec')
