"""Request presentation preserves decoded scripts and diagnostic source data."""

import ast
import unittest

from thlib.ui.debug_request import request_code_blocks


class DebugRequestTests(unittest.TestCase):
    def test_multiline_script_is_readable_and_call_arguments_round_trip(self):
        script = ('# Keep this comment\n'
                  'def query():\n'
                  '    path = r"C:\\new\\test.png"\n'
                  '    return "\\n", "\'\'\'", "\\\"\\\"\\\""\n')
        kwargs = {"code": script, "path": r"C:\new\test.png", "filters": ["a", 1]}
        command = (
            "import thlib.environment as thenv\n"
            "thenv.tc().server_start(project='demo').execute_python_script("
            f"script_path='', kwargs={kwargs!r})"
        )
        blocks = request_code_blocks(command)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[1], {"name": "request_text_1", "text": script})
        self.assertIn("\n    script_path='',\n    kwargs=", blocks[0]["text"])
        call = ast.parse(blocks[0]["text"]).body[-1].value
        arguments = ast.Expression(call.keywords[1].value)
        # Only test-controlled literal data is evaluated, never a runtime request.
        decoded = eval(compile(arguments, '<test>', 'eval'), {}, {
            blocks[1]["name"]: blocks[1]["text"],
        })
        self.assertEqual(decoded, kwargs)

    def test_multiple_multiline_arguments_have_distinct_identifiers(self):
        blocks = request_code_blocks(
            "import thlib.environment as thenv\n"
            "thenv.tc().server_start(project='demo').execute_cmd("
            "'Example', args={'a': 'first\\nsecond', 'b': 'third\\nfourth'})"
        )
        self.assertEqual([block["name"] for block in blocks],
                         ["", "request_text_1", "request_text_2"])
        self.assertEqual(blocks[2]["text"], "third\nfourth")

    def test_unstructured_commands_are_not_reinterpreted(self):
        for command in ('# comment\nprint("keep me")', 'not python <xml>',
                        'def query():\n    return 1\n'):
            with self.subTest(command=command):
                self.assertEqual(request_code_blocks(command),
                                 [{"name": "", "text": command}])
        self.assertEqual(request_code_blocks(""), [])
