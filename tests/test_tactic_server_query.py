from collections import OrderedDict
import unittest
from unittest.mock import patch

from thlib import tactic_classes as tc


class _Server:
    def __init__(self):
        self.direct_queries = []

    @staticmethod
    def build_search_type(stype, project):
        return "{}?project={}".format(stype, project)

    def query(self, *args, **kwargs):
        self.direct_queries.append((args, kwargs))
        return [{"code": "DIRECT"}]


class _SObject:
    def __init__(self, **info):
        self._info = dict(info)

    def get_value(self, column):
        return self._info.get(column)

    def get_info(self):
        return dict(self._info)


class TacticServerQueryTests(unittest.TestCase):
    def test_plain_filters_keep_the_lightweight_xmlrpc_query(self):
        server = _Server()
        with patch.object(tc, "server_start", return_value=server), patch.object(
            tc, "get_sobjects"
        ) as get_sobjects:
            result = tc.server_query(
                [("name", "EQI", "tree")],
                "demo/assets",
                columns=["code"],
                project="demo",
                limit=20,
            )

        self.assertEqual(result, [{"code": "DIRECT"}])
        self.assertEqual(len(server.direct_queries), 1)
        get_sobjects.assert_not_called()

    def test_tel_filters_use_the_handler_query_and_project_columns(self):
        server = _Server()
        expression = "@SOBJECT(sthpw/task['assigned', '$LOGIN'])"
        sobjects = OrderedDict([
            ("one", _SObject(code="ASSET0001", keywords="tree, green")),
            ("two", _SObject(code="ASSET0002", keywords="rock")),
        ])
        with patch.object(tc, "server_start", return_value=server), patch.object(
            tc, "get_sobjects", return_value=sobjects
        ) as get_sobjects:
            result = tc.server_query(
                [("_expression", "in", expression)],
                "demo/assets",
                columns=["keywords"],
                project="demo",
                limit=2000,
                offset=0,
            )

        self.assertEqual(
            result,
            [{"keywords": "tree, green"}, {"keywords": "rock"}],
        )
        self.assertEqual(server.direct_queries, [])
        self.assertEqual(
            get_sobjects.call_args.args[0], "demo/assets?project=demo"
        )
        self.assertEqual(
            get_sobjects.call_args.kwargs["filters"],
            [("_expression", "in", expression)],
        )
        self.assertEqual(
            get_sobjects.call_args.kwargs["order_bys"],
            ["timestamp desc"],
        )
        self.assertFalse(get_sobjects.call_args.kwargs["include_info"])
        self.assertFalse(get_sobjects.call_args.kwargs["include_snapshots"])


if __name__ == "__main__":
    unittest.main()
