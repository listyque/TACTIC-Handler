"""Offline execution of the Server Python demo seed in its real wrapper shape."""

import ast
from pathlib import Path
import sys
import textwrap
import types
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parent / "tactic_demo_seed.py"


class DemoSeedTests(unittest.TestCase):
    def test_short_runs_return_progress_and_create_all_links(self):
        rows = {}
        links = {"complex/asset_in_scene": [], "dolly3d/texture_in_assets": []}
        existing_logins = {"alice", "bob"}

        class Item:
            def __init__(self, values, kind):
                self.values = values
                self.kind = kind

            def get_value(self, field):
                return self.values.get(field)

            def get_id(self):
                return self.values["id"]

            def set_value(self, field, value):
                self.values[field] = value

            def set_sobject_value(self, parent):
                self.values.update(search_type=parent.kind,
                                   search_code=parent.get_value("code"),
                                   search_id=parent.get_id())

            def commit(self, triggers=False):
                pass

            def add_to_group(self, group):
                code = "%s:%s" % (self.get_value("login"), group)
                rows[("sthpw/login_in_group", code)] = Item({
                    "id": len(rows) + 1, "code": code,
                    "login": self.get_value("login"), "login_group": group,
                }, "sthpw/login_in_group")

        class Server:
            next_id = 0

            def set_project(self, code):
                self.project = code

            def insert_multiple(self, search_type, data, parent_key=None, triggers=True):
                result = []
                for row in data:
                    self.next_id += 1
                    values = dict(row)
                    code = values.get("code", "%s_%s" % (search_type, self.next_id))
                    values.update(code=code, id=self.next_id,
                                  project_code=self.project,
                                  search_type=search_type)
                    if parent_key:
                        parent_type, parent_code = parent_key.split("?code=", 1)
                        parent = rows[(parent_type, parent_code)]
                        values.update(search_type=parent_type,
                                      search_code=parent_code,
                                      search_id=parent.get_id())
                    rows[(search_type, code)] = Item(values, search_type)
                    result.append(dict(values, __search_key__="%s?code=%s" % (search_type, code)))
                return result

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []

            def add_filter(self, name, value, op="="):
                self.filters.append((name, value, op))

            def set_show_retired(self, value):
                pass

            def get_sobject(self):
                return object()

            def get_count(self):
                if self.search_type in links:
                    return len(links[self.search_type])
                return len(self.get_sobjects())

            def get_sobjects(self):
                if self.search_type == "sthpw/login":
                    items = [Item({"login": name}, "sthpw/login")
                             for name in sorted(existing_logins)]
                    items.extend(item for (kind, _), item in rows.items()
                                 if kind == "sthpw/login")
                elif self.search_type == "sthpw/pipeline":
                    return [types.SimpleNamespace(get_process_names=lambda: ["model", "review"])]
                else:
                    items = [item for (kind, _code), item in rows.items()
                             if kind == self.search_type]
                for name, value, op in self.filters:
                    if op == "like":
                        items = [item for item in items if str(item.get_value(name) or "")
                                 .startswith(str(value).rstrip("%"))]
                    else:
                        items = [item for item in items if item.get_value(name) == value]
                return items

        class Schema:
            @classmethod
            def get(cls, project_code):
                return cls()

            def get_related_search_types(self, search_type, direction=None):
                return ["complex/shot"] if search_type == "complex/scenes" else []

            def get_relationship_attrs(self, first, second):
                if second == "complex/assets_category":
                    return {"relationship": "code", "from": first, "to": second,
                            "from_col": "assets_category_code"}
                instance_type = ("complex/asset_in_scene" if first == "complex/scenes"
                                 else "dolly3d/texture_in_assets")
                return {"relationship": "instance", "from": first, "to": second,
                        "instance_type": instance_type}

        class SearchType:
            @staticmethod
            def get_columns(search_type):
                columns = ["code", "name", "description"]
                if search_type in {"complex/scenes", "dolly3d/assets"}:
                    columns.append("keywords")
                if search_type == "dolly3d/assets":
                    columns.append("assets_category_code")
                return columns

            @staticmethod
            def create(search_type):
                if search_type == "sthpw/login_group":
                    code = "DEMO_GROUP_%03d" % (len(rows) + 1)
                    group = Item({"id": len(rows) + 1, "code": code}, search_type)
                    rows[(search_type, code)] = group
                    return group
                class Instance:
                    def add_related_connection(self, first, second, src_path=None):
                        self.endpoints = (first, second)

                    def commit(self):
                        links[search_type].append(self.endpoints)

                return Instance()

        class Login:
            @staticmethod
            def create(name, password, groups, project_code):
                assert password and project_code == "demo"
                code = "DEMO_LOGIN_%03d" % (len(rows) + 1)
                user = Item({"id": len(rows) + 1, "code": code,
                             "login": name}, "sthpw/login")
                rows[("sthpw/login", code)] = user
                for group in groups:
                    user.add_to_group(group)
                return user

        class SearchKey:
            @staticmethod
            def build_search_key(search_type, code, project_code=None):
                return "%s?code=%s" % (search_type, code)

            @staticmethod
            def get_by_search_key(key):
                search_type, code = key.split("?code=", 1)
                return rows.get((search_type, code))

        search_module = types.ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchType = SearchType
        search_module.SearchKey = SearchKey
        biz_module = types.ModuleType("pyasm.biz")
        biz_module.Schema = Schema
        security_module = types.ModuleType("pyasm.security")
        security_module.Login = Login
        package = types.ModuleType("pyasm")
        package.__path__ = []

        source = "def run_seed():\n" + textwrap.indent(SCRIPT.read_text(encoding="utf-8"), "    ")
        tree = ast.parse(source, filename=str(SCRIPT))
        for assignment in tree.body[0].body:
            if not isinstance(assignment, ast.Assign):
                continue
            name = getattr(assignment.targets[0], "id", None)
            if name in {"EPISODES", "ASSETS", "TEXTURES", "MAX_SECONDS_PER_RUN"}:
                assignment.value = ast.Constant(value={
                    "EPISODES": 2, "ASSETS": 4, "TEXTURES": 4,
                    "MAX_SECONDS_PER_RUN": 0,
                }[name])
            elif name == "PROJECT_CODE":
                assignment.value = ast.Constant(value="demo")
        ast.fix_missing_locations(tree)
        namespace = {"server": Server()}
        with patch.dict(sys.modules, {"pyasm": package, "pyasm.search": search_module,
                                      "pyasm.biz": biz_module,
                                      "pyasm.security": security_module}):
            exec(compile(tree, str(SCRIPT), "exec"), namespace)
            phases = []
            for _ in range(40):
                result = namespace["run_seed"]()
                phases.append(result["phase"])
                if result["phase"] == "episodes_created":
                    rows[("complex/scenes", "DEMO_EP001")].set_value(
                        "keywords", "manual"
                    )
                if result["phase"] == "complete":
                    break
            row_count = len(rows)
            asset = rows[("dolly3d/assets", "DEMO_AST0001")]
            marker_key = next(key for key, item in rows.items()
                              if key[0] == "sthpw/note"
                              and item.get_value("search_id") == asset.get_id()
                              and item.get_value("note") ==
                              "[DEMO] Asset tasks and review notes are ready for handoff.")
            note_key = next(key for key, item in rows.items()
                            if key[0] == "sthpw/note"
                            and item.get_value("search_id") == asset.get_id()
                            and item.get_value("note") !=
                            "[DEMO] Asset tasks and review notes are ready for handoff.")
            rows.pop(marker_key)
            rows.pop(note_key)
            resume = namespace["run_seed"]()
            self.assertEqual(resume["phase"], "asset_tasks_and_notes")
            self.assertEqual(len(rows), row_count)
            episode = rows[("complex/scenes", "DEMO_EP001")]
            episode_marker = next(key for key, item in rows.items()
                                  if key[0] == "sthpw/note"
                                  and item.get_value("search_id") == episode.get_id()
                                  and item.get_value("note") ==
                                  "[DEMO] Episode review notes are ready for handoff.")
            episode_message = next(key for key, item in rows.items()
                                   if key[0] == "sthpw/note"
                                   and item.get_value("search_id") == episode.get_id()
                                   and str(item.get_value("note") or "")
                                   .startswith("[DEMO] Episode review:"))
            rows.pop(episode_marker)
            rows.pop(episode_message)
            episode_resume = namespace["run_seed"]()
            self.assertEqual(episode_resume["phase"], "episode_discussions")
            self.assertEqual(len(rows), row_count)
            episode_task = next(item for (kind, _), item in rows.items()
                                if kind == "sthpw/task"
                                and item.get_value("search_type") == "complex/scenes")
            episode_note = next(item for (kind, _), item in rows.items()
                                if kind == "sthpw/note"
                                and item.get_value("search_type") == "complex/scenes"
                                and item.get_value("note") !=
                                "[DEMO] Episode review notes are ready for handoff.")
            episode_note.set_sobject_value(episode_task)
            no_migration = namespace["run_seed"]()
            links["complex/asset_in_scene"].clear()
            repair = namespace["run_seed"]()
            after_repair = namespace["run_seed"]()
            for assignment in tree.body[0].body:
                if (isinstance(assignment, ast.Assign)
                        and getattr(assignment.targets[0], "id", None) == "INSPECT_ONLY"):
                    assignment.value = ast.Constant(value=True)
            inspection_namespace = {"server": Server()}
            ast.fix_missing_locations(tree)
            exec(compile(tree, str(SCRIPT), "exec"), inspection_namespace)
            inspection = inspection_namespace["run_seed"]()

        self.assertEqual(result["phase"], "complete")
        self.assertEqual(result["project"], "demo")
        self.assertEqual(result["counts"]["episodes"], 2)
        self.assertGreaterEqual(result["counts"]["shots"], 4)
        self.assertEqual(result["counts"]["categories"], 10)
        self.assertEqual(result["counts"]["assets"], 4)
        self.assertEqual(result["counts"]["episode_asset_links"], 4)
        self.assertEqual(result["counts"]["textures"], 4)
        self.assertEqual(result["counts"]["asset_texture_links"], 4)
        self.assertEqual(phases[:4], [
            "episodes_created", "shots_created", "shots_created", "episode_tasks_and_notes",
        ])
        self.assertEqual(repair["phase"], "episode_asset_links")
        self.assertEqual(no_migration["phase"], "complete")
        self.assertEqual(episode_note.get_value("search_type"), "sthpw/task")
        self.assertEqual(after_repair["phase"], "complete")
        self.assertEqual(len(rows), row_count)
        self.assertEqual(inspection["phase"], "inspection")
        for name, value in after_repair["counts"].items():
            self.assertEqual(inspection["counts"][name], value)
        self.assertEqual(inspection["counts"]["episode_discussions"], 2)
        self.assertEqual(inspection["counts"]["asset_discussions"], 4)
        self.assertTrue(all(row.get_value("assets_category_code")
                            for (kind, _code), row in rows.items() if kind == "dolly3d/assets"))
        self.assertTrue(all(row.get_value("keywords")
                            for (kind, _code), row in rows.items()
                            if kind in {"complex/scenes", "dolly3d/assets"}))
        self.assertTrue(rows[("complex/scenes", "DEMO_EP001")]
                        .get_value("keywords").startswith("manual, "))
        self.assertTrue(any(kind == "sthpw/task" and row.get_value("search_type") == "dolly3d/assets"
                            for (kind, _code), row in rows.items()))
        self.assertTrue(any(kind == "sthpw/note" and row.get_value("search_type") == "dolly3d/assets"
                            for (kind, _code), row in rows.items()))
        self.assertFalse(any(kind == "sthpw/login" for kind, _ in rows))
        self.assertFalse(any(kind == "sthpw/login_group" for kind, _ in rows))

        existing_logins.clear()
        existing_logins.add("admin")
        for assignment in tree.body[0].body:
            if not isinstance(assignment, ast.Assign):
                continue
            name = getattr(assignment.targets[0], "id", None)
            if name and name.startswith(("CREATE_", "LINK_", "TAG_")):
                assignment.value = ast.Constant(value=name in {"CREATE_USERS", "CREATE_GROUPS"})
            elif name == "INSPECT_ONLY":
                assignment.value = ast.Constant(value=False)
            elif name == "MAX_SECONDS_PER_RUN":
                assignment.value = ast.Constant(value=100)
        ast.fix_missing_locations(tree)
        user_namespace = {"server": Server()}
        with patch.dict(sys.modules, {"pyasm": package, "pyasm.search": search_module,
                                      "pyasm.biz": biz_module,
                                      "pyasm.security": security_module}):
            exec(compile(tree, str(SCRIPT), "exec"), user_namespace)
            user_phases = [user_namespace["run_seed"]()["phase"] for _ in range(4)]
        self.assertEqual(user_phases, [
            "groups_created", "users_created", "complete", "complete",
        ])
        self.assertEqual(sum(kind == "sthpw/login" for kind, _ in rows), 200)
        self.assertEqual(sum(kind == "sthpw/login_group" for kind, _ in rows), 12)
        self.assertEqual(sum(kind == "sthpw/login_in_group" for kind, _ in rows), 200)
        self.assertEqual({row.get_value("login_group") for (kind, _), row in rows.items()
                          if kind == "sthpw/login_in_group"},
                         {row.get_value("login_group") for (kind, _), row in rows.items()
                          if kind == "sthpw/login_group"})

        rows.clear()
        for connection_rows in links.values():
            connection_rows.clear()
        for assignment in tree.body[0].body:
            if (isinstance(assignment, ast.Assign)
                    and getattr(assignment.targets[0], "id", "").startswith(
                        ("CREATE_", "LINK_", "TAG_"))):
                assignment.value = ast.Constant(value=True)
        ast.fix_missing_locations(tree)
        fresh_namespace = {"server": Server()}
        with patch.dict(sys.modules, {"pyasm": package, "pyasm.search": search_module,
                                      "pyasm.biz": biz_module,
                                      "pyasm.security": security_module}):
            exec(compile(tree, str(SCRIPT), "exec"), fresh_namespace)
            for _ in range(12):
                fresh_result = fresh_namespace["run_seed"]()
                if fresh_result["phase"] == "complete":
                    break
        self.assertEqual(fresh_result["phase"], "complete")
        self.assertEqual(fresh_result["counts"]["users"], 200)
        self.assertEqual(fresh_result["counts"]["groups"], 12)
        self.assertEqual(fresh_result["counts"]["episode_asset_links"], 4)
        self.assertEqual(fresh_result["counts"]["asset_texture_links"], 4)

        links["complex/asset_in_scene"].clear()
        for assignment in tree.body[0].body:
            if (isinstance(assignment, ast.Assign)
                    and getattr(assignment.targets[0], "id", "").startswith(
                        ("CREATE_", "LINK_", "TAG_"))):
                assignment.value = ast.Constant(value=False)
        ast.fix_missing_locations(tree)
        with patch.dict(sys.modules, {"pyasm": package, "pyasm.search": search_module,
                                      "pyasm.biz": biz_module,
                                      "pyasm.security": security_module}):
            disabled_namespace = {"server": Server()}
            exec(compile(tree, str(SCRIPT), "exec"), disabled_namespace)
            self.assertEqual(disabled_namespace["run_seed"]()["phase"], "complete")
            self.assertFalse(links["complex/asset_in_scene"])
            for assignment in tree.body[0].body:
                if (isinstance(assignment, ast.Assign)
                        and getattr(assignment.targets[0], "id", None)
                        == "LINK_EPISODE_ASSETS"):
                    assignment.value = ast.Constant(value=True)
            ast.fix_missing_locations(tree)
            repair_namespace = {"server": Server()}
            exec(compile(tree, str(SCRIPT), "exec"), repair_namespace)
            repair_namespace["run_seed"]()
        self.assertEqual(len(links["complex/asset_in_scene"]), 4)


if __name__ == "__main__":
    unittest.main()
