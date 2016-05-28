import tactic_classes as tc
from pprint import pprint
# print(tc.server_start().get_column_names('sthpw/note'))
#
# print(tc.server_start().add_column_to_search_type('sthpw/note', 'note_html2', 'string'))

# pprint(tc.server_start().get_related_types('sthpw/notification'))

pprint(tc.server_start().get_protocol())

# pprint(tc.server_start().set_protocol('local'))

pprint(tc.server_start().test_error())
