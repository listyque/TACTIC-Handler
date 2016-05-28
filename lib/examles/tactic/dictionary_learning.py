my_dict = {
    'key1': 'value1',
    'key2': 'value2',
    'key3': 'value3'
}
for item in my_dict:
    print item

for key, value in my_dict.items():
    print key, value

for key, value in my_dict.iteritems():
    print key, value

for key in my_dict.iterkeys():
    print key

for value in my_dict.itervalues():
    print value

key_value_pairs = [
    ('key1', 'value1'),
    ('key1', 'value2'),
    ('key1', 'value3'),
    ('key2', 'value1'),
    ('key2', 'value2'),
    ('key2', 'value3'),
]
dict_ = {}

for key, value in key_value_pairs:
    dict_.setdefault(key, []).append(value)

print dict_

dct = [{
           'code': u'exam/chars', 'description': u'Characters', 'database': u'exam',
           'class_name': u'pyasm.search.SObject', 'type': u'maya', 'title': u'Characters', 'namespace': u'exam',
           'message_event': None, 'id': 84, 'search_type': u'exam/chars', 'color': None, 'table_name': u'chars',
           '__search_key__': u'sthpw/search_object?code=exam/chars', 'metadata_parser': None, 'id_column': None,
           'default_layout': u'check-in', 'schema': u'public'
           }, {
           'code': u'exam/props', 'description': u'All tipes of props', 'database': u'exam',
           'class_name': u'pyasm.search.SObject', 'type': u'maya', 'title': u'Props', 'namespace': u'exam',
           'message_event': u'change', 'id': 83, 'search_type': u'exam/props', 'color': None, 'table_name': u'props',
           '__search_key__': u'sthpw/search_object?code=exam/props', 'metadata_parser': None, 'id_column': None,
           'default_layout': u'check-in', 'schema': u'public'
           }, {
           'code': u'exam/scenes', 'description': u'Scenes', 'database': u'exam', 'class_name': u'pyasm.search.SObject',
           'type': u'maya', 'title': u'Scenes', 'namespace': u'exam', 'message_event': None, 'id': 86,
           'search_type': u'exam/scenes', 'color': None, 'table_name': u'scenes',
           '__search_key__': u'sthpw/search_object?code=exam/scenes', 'metadata_parser': None, 'id_column': None,
           'default_layout': u'check-in', 'schema': u'public'
           }, {
           'code': u'exam/sets', 'description': u'Scene sets', 'database': u'exam',
           'class_name': u'pyasm.search.SObject', 'type': u'maya', 'title': u'Sets', 'namespace': u'exam',
           'message_event': None, 'id': 85, 'search_type': u'exam/sets', 'color': None, 'table_name': u'sets',
           '__search_key__': u'sthpw/search_object?code=exam/sets', 'metadata_parser': None, 'id_column': None,
           'default_layout': u'check-in', 'schema': u'public'
           }, {
           'code': u'exam/shaders', 'description': u'3d shaders', 'database': u'exam',
           'class_name': u'pyasm.search.SObject', 'type': u'maya', 'title': u'Shaders', 'namespace': u'exam',
           'message_event': None, 'id': 96, 'search_type': u'exam/shaders', 'color': None, 'table_name': u'shaders',
           '__search_key__': u'sthpw/search_object?code=exam/shaders', 'metadata_parser': None, 'id_column': None,
           'default_layout': u'tile', 'schema': u'public'
           }]
