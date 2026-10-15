"""JSON representations of the SDK's XML-RPC binary and datetime values."""
import base64
from datetime import date, datetime
from xmlrpc.client import Binary, DateTime

CODEC = 'tactic-sdk-v1'
TYPE = '__tactic_rpc_type__'


def encode(value):
    if isinstance(value, (bytes, bytearray, Binary)):
        data = value.data if isinstance(value, Binary) else value
        return {TYPE: 'binary', 'value': base64.b64encode(data).decode('ascii')}
    if isinstance(value, (datetime, date, DateTime)):
        timestamp = value.value if isinstance(value, DateTime) else value.strftime('%Y%m%dT%H:%M:%S')
        return {TYPE: 'datetime', 'value': timestamp}
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError('RPC dictionary keys must be strings')
        if TYPE in value:
            return {TYPE: 'dict', 'items': [[key, encode(item)] for key, item in value.items()]}
        return {key: encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError('Unsupported RPC value: ' + type(value).__name__)


def decode(value, use_builtin_types=False):
    if isinstance(value, list):
        return [decode(item, use_builtin_types) for item in value]
    if not isinstance(value, dict):
        return value
    if TYPE not in value:
        return {key: decode(item, use_builtin_types) for key, item in value.items()}
    kind = value[TYPE]
    if kind == 'dict' and set(value) == {TYPE, 'items'}:
        items = value['items']
        if (not isinstance(items, list) or any(
                not isinstance(item, list) or len(item) != 2 or not isinstance(item[0], str)
                for item in items)):
            raise ValueError('Invalid RPC dictionary')
        if len({item[0] for item in items}) != len(items):
            raise ValueError('Duplicate RPC dictionary key')
        return {key: decode(item, use_builtin_types) for key, item in items}
    if set(value) != {TYPE, 'value'} or not isinstance(value['value'], str):
        raise ValueError('Invalid typed RPC value')
    if kind == 'binary':
        data = base64.b64decode(value['value'], validate=True)
        return data if use_builtin_types else Binary(data)
    if kind == 'datetime':
        timestamp = datetime.strptime(value['value'], '%Y%m%dT%H:%M:%S')
        return timestamp if use_builtin_types else DateTime(value['value'])
    raise ValueError('Unknown typed RPC value')
