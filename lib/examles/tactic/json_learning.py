import json
json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
print json.dumps(u'\u1234')