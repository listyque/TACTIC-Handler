import datetime
import unittest

from thlib.color_hash import color_hash
from thlib.global_functions import html_to_hex, hex_to_html, natural_sort_key
from thlib.tactic_xml import parse_tactic_xml
from thlib.time_presentation import get_pretty_datetime
from thlib.ui.checkin_out import CheckinOutController


class CoreSimplificationTests(unittest.TestCase):
    def test_color_hash_keeps_existing_identity_colors(self):
        self.assertEqual(color_hash("Hello World"), "#59a667")
        self.assertEqual(color_hash("admin"), "#59a693")
        self.assertEqual(color_hash("shot_010"), "#8359a6")

    def test_natural_sort_orders_frame_and_udim_numbers(self):
        values = ["shot.10.exr", "shot.2.exr", "shot.1.exr"]
        self.assertEqual(
            sorted(values, key=natural_sort_key),
            ["shot.1.exr", "shot.2.exr", "shot.10.exr"],
        )

    def test_python3_text_compression_accepts_text_and_bytes(self):
        value = "frame metadata " * 20
        self.assertEqual(hex_to_html(html_to_hex(value)), value)
        self.assertEqual(
            hex_to_html(html_to_hex(value.encode("utf-8"))), value
        )

    def test_tactic_xml_preserves_attributes_text_and_malformed_fragments(self):
        document = parse_tactic_xml(
            '<config><element name="code" class="a b">A &amp; B</element></config>'
        )
        self.assertEqual(document.element["name"], "code")
        self.assertEqual(document.element.get("class"), ["a", "b"])
        self.assertEqual(document.element.text, "A & B")
        self.assertEqual(
            parse_tactic_xml('<config><element name="x">A & B</config>').element.text,
            "A & B",
        )

    def test_relative_time_is_testable_without_the_vendored_package(self):
        now = datetime.datetime(2026, 9, 4, 12, 0)
        self.assertEqual(
            get_pretty_datetime(now - datetime.timedelta(minutes=3), now=now),
            "3 min ago",
        )

    def test_dcc_only_actions_require_the_selected_thin_client(self):
        target = type("Target", (), {
            "_dcc_bridge": None,
            "tr": lambda _self, value: value,
        })()
        self.assertEqual(
            CheckinOutController.dcc_operation_availability(target, "open"),
            (True, ""),
        )
        self.assertEqual(
            CheckinOutController.dcc_operation_availability(target, "import"),
            (False, "Import requires a selected DCC client"),
        )


if __name__ == "__main__":
    unittest.main()
