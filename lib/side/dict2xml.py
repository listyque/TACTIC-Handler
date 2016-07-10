"""
	Simple xml serializer to lxml Elemets.

	@author Reimund Trost 2013
	@author Joelmir Ribacki 2015

"""

from lxml import etree

def dict2xml(d, root_node=None):
	root = 'objects' if None == root_node else root_node
	obj_xml = etree.Element(root)
	root_singular = root[:-1] if 's' == root[-1] and None == root_node else root
	children_obj  = []
	if isinstance(d, dict):
		for key, value in dict.items(d):
			if isinstance(value, dict) or isinstance(value, list):
				_obj_xml = dict2xml(value, key)
				if isinstance(_obj_xml, list):
					for elem in _obj_xml:
						obj_xml.append(elem)	
				else:
					obj_xml.append(_obj_xml)
			else:
				obj_xml.attrib[str(key)] = str(value)
	else:
		for value in d:
			children_obj.append(dict2xml(value, root_singular))

		obj_xml = children_obj		
	return obj_xml


'''
	Exemple:
'''

mydict = {
	'name': 'The Andersson\'s',
	'size': 4,
	'children': {
		'total-age': 62,
		'child': [
			{ 'name': 'Tom', 'sex': 'male', },
			{
				'name': 'Betty',
				'sex': 'female',
				'grandchildren': {
					'grandchild': [
						{ 'name': 'herbert', 'sex': 'male', },
						{ 'name': 'lisa', 'sex': 'female', }
					]
				},
			}
		]
	},
}

obj_xml = dict2xml(mydict, 'family')
print etree.tostring(obj_xml, encoding='utf-8',xml_declaration=True, pretty_print=True)

'''
<?xml version='1.0' encoding='utf-8'?>
<family name="The Andersson's" size="4">
  <children total-age="62">
    <child name="Tom" sex="male"/>
    <child name="Betty" sex="female">
      <grandchildren>
        <grandchild name="herbert" sex="male"/>
        <grandchild name="lisa" sex="female"/>
      </grandchildren>
    </child>
  </children>
</family>

'''