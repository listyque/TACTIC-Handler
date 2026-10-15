"""Plain cell text with conversion determined by the physical column type."""
import json
import math
import re


def cell_text(value: object) -> str:
    return '' if value is None else value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def cell_kind(column_type: str) -> str:
    column_type = (column_type or '').strip().lower()
    if re.search(r'\b(tinyint|smallint|bigint|int(?:eger|[248])?|serial|bigserial|smallserial)\b', column_type):
        return 'integer'
    if column_type.startswith('bool'):
        return 'boolean'
    if column_type.startswith(('numeric', 'decimal')):
        return 'decimal'
    if column_type.startswith(('real', 'float', 'double')):
        return 'float'
    if re.match(r'^jsonb?\b', column_type):
        return 'json'
    return 'text'


def finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError('Invalid number')
    return value


def cell_value(text: str, column_type: str, mode: str = 'value') -> object:
    if mode == 'null':
        return None
    if mode != 'value':
        raise ValueError('Invalid cell mode')
    kind = cell_kind(column_type)
    trimmed = text.strip()
    if kind == 'text':
        return text
    if kind == 'integer':
        if not re.fullmatch(r'[+-]?\d+', trimmed, flags=re.ASCII):
            raise ValueError('Invalid integer')
        value = int(trimmed)
        return str(value) if abs(value) > 9007199254740991 else value
    if kind == 'boolean':
        if trimmed.lower() in ('true', '1'):
            return True
        if trimmed.lower() in ('false', '0'):
            return False
        raise ValueError('Invalid boolean')
    if kind == 'json':
        json.loads(text, parse_float=finite_float, parse_constant=finite_float)
        return text
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', trimmed, flags=re.ASCII):
        raise ValueError('Invalid number')
    return trimmed if kind == 'decimal' else finite_float(trimmed)
