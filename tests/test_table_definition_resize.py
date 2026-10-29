"""Native reference for materializing a schema column on its first resize."""
import unittest
from xml.etree import ElementTree

from thlib.ui.columns_editor import ColumnsEditorController
from tests.test_columns_table_view import _Application, _SType


class TableDefinitionResize(unittest.TestCase):
    def test_name_width_materializes_when_missing_from_source_xml(self):
        for source in (
            '<config><table/></config>',
            '<config><!--keep--><table><element name="code" title="Code">'
            '<display widget="text"><option>keep</option></display>'
            '</element></table></config>',
        ):
            with self.subTest(source=source):
                controller = ColumnsEditorController(_Application(_SType()))
                controller._view = 'table'
                controller._definition_root = controller._catalog_xml_root(source)
                controller._source_elements = {
                    node.get('name'): [node]
                    for node in controller._definition_root.findall('table/element')
                }
                controller.model.replace([
                    dict(name=name, label=name.title(), displayVisible=True,
                         displayWidth=160, hideOrder=0)
                    for name in ('code', 'name')
                ])
                controller.set_width(1, 208)
                saved = controller._serialize(controller.model._records)
                table = ElementTree.fromstring(saved).find('table')
                self.assertEqual([node.get('name') for node in table], ['code', 'name'])
                self.assertEqual(table.find("element[@name='name']").get('width'), '208')
                if '<!--keep-->' in source:
                    self.assertIn('<!--keep-->', saved)
                    self.assertEqual(table.find("element[@name='code']/display/option").text, 'keep')


if __name__ == '__main__':
    unittest.main()
