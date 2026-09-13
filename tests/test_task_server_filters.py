"""Execute the task procedure's predicates/counts/pages against an in-memory SQL DB.

The small Search double models native begin/and/or groups; it does not stub the
procedure or return predetermined pages. Live TACTIC remains a separate smoke.
"""

import ast
import json
from pathlib import Path
import re
import sqlite3
import sys
import unittest
from datetime import date, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from thlib import tactic_query as tq


NATIVE_SQL = Path(__file__).resolve().parents[1] / '.cache/tactic-source/src/pyasm/search/sql.py'


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


class Record:
    def __init__(self, values):
        self.values = dict(values)

    def get_data(self):
        return dict(self.values)

    def get_value(self, key):
        return self.values.get(key)


class TaskServerFilterTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.row_factory = sqlite3.Row
        self.db.create_function("regexp", 2, lambda pattern, value: bool(
            re.search(pattern, str(value or ""), re.I)))
        self.db.create_function("split_part", 3, lambda value, separator, part:
                                str(value or "").split(separator)[part - 1])
        columns = ("code", "project_code", "search_type", "search_code", "process",
                   "context", "status", "assigned", "supervisor", "priority",
                   "milestone_code", "bid_end_date", "timestamp", "pipeline_code", "description")
        self.db.execute("CREATE TABLE task (%s)" % ",".join(name + " TEXT" for name in columns))
        self.db.execute("CREATE TABLE note (code TEXT, project_code TEXT, search_type TEXT, search_code TEXT, process TEXT)")
        self.db.execute("CREATE TABLE asset (code TEXT, name TEXT)")
        self.db.executemany("INSERT INTO asset VALUES (?, ?)", [("A", "Zebra"), ("B", "Alpha's [hero]")])
        today = date.today()
        for number in range(24):
            row = dict.fromkeys(columns, "")
            row.update(code=f"T{number:02}", project_code="test", search_type="prod/asset?project=test",
                       search_code="A" if number % 2 else "B", process="model", context="model",
                       status="Ready" if number % 3 else "Review", assigned="a" if number % 2 else "z",
                       priority="0", bid_end_date=(today + timedelta(days=number % 6 - 1)).isoformat(),
                       timestamp=(today - timedelta(days=number)).isoformat())
            self.db.execute("INSERT INTO task VALUES (%s)" % ",".join("?" for _ in columns), list(row.values()))
        self.queries = []
        self.orderings = []
        orderings = self.orderings
        db, queries = self.db, self.queries

        class Search:
            def __init__(self, search_type):
                self.table = search_type.split("/")[-1]
                self.search_type_obj = SimpleNamespace(get_table=lambda: self.table)
                self.groups, self.columns, self.group_by, self.order = [[]], [], [], []
                self.limit, self.offset = 0, 0
                self.quoted_mode = None

            def add_where(self, expression):
                self.groups[-1].append(expression)

            def add_op(self, operation):
                if operation == "begin":
                    self.groups.append([])
                else:
                    group = self.groups.pop()
                    self.add_where("(" + (" " + operation.upper() + " ").join(group) + ")")

            def add_op_filters(self, filters):
                for item in filters:
                    if isinstance(item, str):
                        self.add_op(item)
                    elif len(item) == 2:
                        self.add_filter(*item)
                    elif item[1] == "in":
                        self.add_filters(item[0], item[2].split("|"))
                    else:
                        self.add_filter(item[0], item[2], item[1])

            def add_filter(self, column, value, op="="):
                self.add_where('"%s" %s %s' % (column, op, quote(value)))

            def add_filters(self, column, values):
                self.add_where('"%s" IN (%s)' % (column, ",".join(quote(v) for v in values)))

            def add_empty_filter(self, column):
                self.add_where('COALESCE("%s", \'\') = \'\'' % column)

            def add_null_filter(self, column):
                self.add_where('"%s" IS NULL' % column)

            def add_regex_filter(self, column, pattern):
                self.add_where('"%s" REGEXP %s' % (column, quote(pattern)))

            def add_search_filter(self, column, search):
                self.add_where('"%s" IN (%s)' % (column, search.sql()))

            def add_column(self, column, distinct=False, table=None, as_column=None):
                # TACTIC 4.9 Search AND Select have this signature (no quoted).
                self.columns.append((column, distinct, as_column))

            def set_quoted_mode(self, mode):
                self.quoted_mode = mode

            def add_group_by(self, column):
                self.group_by.append(column)

            def add_order_by(self, expression, direction=""):
                self.order.append((expression, direction))

            def get_select(self):
                return SimpleNamespace(
                    add_column=self.add_column,
                    set_quoted_mode=self.set_quoted_mode,
                    add_order_by=self.add_order_by,
                )

            def set_limit(self, value):
                self.limit = value

            def set_offset(self, value):
                self.offset = value

            def sql(self, count=False):
                assert len(self.groups) == 1, self.groups
                columns = []
                for column, distinct, alias in self.columns:
                    value = column if self.quoted_mode == "none" else '"%s"' % column
                    columns.append(("DISTINCT " if distinct else "") + value
                                   + (' AS "%s"' % alias if alias else ""))
                sql = 'SELECT %s FROM "%s"' % ("COUNT(*)" if count else ",".join(columns) or "*", self.table)
                if self.groups[0]:
                    sql += " WHERE " + " AND ".join(self.groups[0])
                if self.group_by:
                    sql += " GROUP BY " + ",".join(self.group_by)
                if not count:
                    if self.order:
                        orderings.append((self.table, list(self.order)))
                        # Match Select.get_statement, including identifier
                        # quoting: accepting arbitrary SQL here hid bad orders.
                        orders = []
                        for expression, direction in self.order:
                            value = expression + (" " + direction if direction else "")
                            if value.startswith("( CASE"):
                                orders.append(value)
                            elif re.search(r" (asc|desc)$", value, re.I):
                                head, tail = value.split(" ", 1)
                                orders.append('"%s" %s' % (head.strip('"'), tail))
                            else:
                                orders.append('"%s"."%s"' % (self.table, value))
                        sql += " ORDER BY " + ",".join(orders)
                    if self.limit:
                        sql += " LIMIT %d OFFSET %d" % (self.limit, self.offset)
                return sql

            def get_count(self):
                sql = self.sql(count=True)
                queries.append(sql)
                return db.execute(sql).fetchone()[0]

            def get_sobjects(self):
                sql = self.sql()
                queries.append(sql)
                return [Record(row) for row in db.execute(sql)]

        module = ModuleType("pyasm.search")
        module.Search = Search
        module.Sql = SimpleNamespace(quote=quote)
        module.SearchType = SimpleNamespace(column_exists=lambda kind, name: name in {"code", "name"})
        modules = patch.dict(sys.modules, {"pyasm": ModuleType("pyasm"), "pyasm.search": module})
        modules.start()
        self.addCleanup(modules.stop)
        server = patch.object(tq, "server", SimpleNamespace(
            set_project=lambda project: None,
            server=SimpleNamespace(_get_sobjects_dict=lambda rows: [row.get_data() for row in rows]),
        ), create=True)
        server.start()
        self.addCleanup(server.stop)

    def page(self, *, filters=None, quick=None, sort="due", group="none", offset=0, limit=5, today=None,
             descending=False):
        return json.loads(tq.query_task_workspace_page(
            [("project_code", "test")], [], "test", offset=offset, limit=limit,
            query={"filters": filters or {}, "quickFilters": quick or {}, "sort": sort,
                   "group": group, "descending": descending, "currentLogin": "a", "today": today, "labels": {
                       "assigned": [{"value": "a", "label": "Zed's team"}, {"value": "z", "label": "Ada"}]
                   }},
        ))

    def test_unscheduled_tasks_stay_last_in_both_directions_across_pages(self):
        self.db.execute("UPDATE task SET bid_end_date = NULL WHERE code IN ('T00', 'T01')")
        for descending in (False, True):
            with self.subTest(descending=descending):
                tasks = [task for offset in range(0, 24, 5)
                         for task in self.page(offset=offset, descending=descending)['tasks']]
                self.assertEqual(len({task['code'] for task in tasks}), 24)
                self.assertEqual([task['code'] for task in tasks[-2:]], ['T00', 'T01'])
                dates = [task['bid_end_date'] for task in tasks[:-2]]
                self.assertEqual(dates, sorted(dates, reverse=descending))

    @unittest.skipUnless(NATIVE_SQL.is_file(), 'Requires the audited TACTIC source checkout')
    def test_all_ordering_modes_execute_with_native_select(self):
        tree = ast.parse(NATIVE_SQL.read_text(encoding='utf-8'))
        select_class = next(node for node in tree.body
                            if isinstance(node, ast.ClassDef) and node.name == 'Select')
        # Run the real ORDER BY builder without importing a server or opening
        # its database connections. SQLite executes the resulting statement.
        select_class.body = [node for node in select_class.body
                             if isinstance(node, ast.FunctionDef)
                             and node.name in ('__init__', 'add_order_by', 'get_statement')]
        impl = SimpleNamespace(get_database_type=lambda: 'PostgreSQL', get_page=lambda *_: '')
        namespace = {'re': re, 'DatabaseImpl': SimpleNamespace(get=lambda: impl)}
        exec(compile(ast.Module(body=[select_class], type_ignores=[]), str(NATIVE_SQL), 'exec'), namespace)
        for sort in ('due', 'recent', 'process', 'user', 'status', 'object',
                     'priority', 'milestone', 'supervisor', 'search_type', 'project'):
            for group in ('none', 'process', 'status', 'user', 'object'):
                for descending in (False, True):
                    with self.subTest(sort=sort, group=group, descending=descending):
                        result = self.page(sort=sort, group=group, descending=descending, limit=500)
                        table, orders = self.orderings[-1]
                        select = namespace['Select']()
                        select.tables = [table]
                        for expression, direction in orders:
                            select.add_order_by(expression, direction=direction)
                        sql = select.get_statement()
                        rows = self.db.execute(sql).fetchall()
                        self.assertEqual([row['code'] for row in rows],
                                         [task['code'] for task in result['tasks']], sql)

    def test_filters_precede_count_and_limit_and_facets_do_not_shrink(self):
        self.db.execute(
            "INSERT INTO task (code, project_code, status) VALUES (?, ?, ?)",
            ("OUTSIDE", "other", "Ready"),
        )
        first = self.page(filters={"status": "Ready"}, quick={"assigned": ["a"]})
        second = self.page(filters={"status": "Ready"}, quick={"assigned": ["a"]}, offset=5)
        self.assertEqual(first["total"], 8)
        self.assertEqual([len(first["tasks"]), len(second["tasks"])], [5, 3])
        self.assertEqual(len({row["code"] for row in first["tasks"] + second["tasks"]}), 8)
        self.assertEqual({row["key"]: row["count"] for row in first["facets"]["status"]}, {"Ready": 16, "Review": 8})
        self.assertEqual(first["facets"]["preset"]["mine"], 12)
        for name in ("process", "status", "assigned", "supervisor", "priority", "milestone"):
            with self.subTest(facet=name):
                self.assertEqual(sum(item["count"] for item in first["facets"][name]), 24)
        self.assertEqual(first["facets"]["supervisor"], [
            {"key": "", "title": "", "count": 24, "accent": ""},
        ])

    def test_parent_text_is_literal_and_order_is_global(self):
        self.db.execute("INSERT INTO asset VALUES ('unused', 'Unrelated object')")
        result = self.page(filters={"text": "Alpha's [hero]"}, sort="user")
        self.assertEqual(result["total"], 12)
        self.assertTrue(all(row["search_code"] == "B" for row in result["tasks"]))
        result = self.page(sort="object", limit=13)
        self.assertEqual([row["search_code"] for row in result["tasks"]], ["B"] * 12 + ["A"])
        self.assertFalse(any("Unrelated object" in sql for sql in self.queries))
        self.assertTrue(any('FROM "asset" WHERE "code" IN (SELECT DISTINCT "search_code"' in sql
                            for sql in self.queries))
        self.assertTrue(all(row["assigned"] == "z" for row in self.page(sort="user")["tasks"]))

    def test_presets_are_or_but_filter_groups_are_and(self):
        result = self.page(quick={"preset": ["mine", "review"], "status": ["Ready"]}, limit=50)
        self.assertEqual(result["total"], 8)
        result = self.page(filters={"day": date.today().isoformat()}, limit=50)
        self.assertEqual(result["total"], 4)

    def test_relative_deadlines_use_the_request_day_not_the_server_timezone(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        result = self.page(quick={"preset": ["today"]}, today=tomorrow)
        self.assertEqual(result["total"], 4)
        self.assertTrue(all(row["bid_end_date"] == tomorrow for row in result["tasks"]))
        with self.assertRaises(ValueError):
            self.page(today="not a date")

    def test_contextual_notes_match_the_returned_note_branch(self):
        self.db.execute("UPDATE task SET context = code")
        self.db.execute("UPDATE task SET context = 'model', timestamp = NULL WHERE code IN ('T00', 'T01')")
        self.db.execute("INSERT INTO note VALUES ('N1', 'test', 'prod/asset', 'B', 'model')")
        self.db.execute("INSERT INTO note VALUES ('N2', 'test', 'sthpw/task', 'T03', 'model')")
        result = self.page(filters={"hasNotes": True}, limit=50)
        self.assertEqual({row["code"] for row in result["tasks"]}, {"T00", "T03"})
        self.assertTrue(all(row["__notes_count__"] == 1 for row in result["tasks"]))

    def test_unbounded_and_negative_pages_are_rejected(self):
        for values in ({"limit": 0}, {"limit": 10000}, {"offset": -1}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.page(**values)

    def test_malformed_filter_shapes_fail_explicitly(self):
        for values in ({"quick": {"status": "Ready"}}, {"quick": {"typo": []}},
                       {"filters": {"typo": "Ready"}}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.page(**values)


if __name__ == "__main__":
    unittest.main()
