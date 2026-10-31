"""Administrator-only physical table editor; intentionally bypasses SObject hooks."""


def raw_database_request(action: str, project_code: str = '', identity: str = '',
                         document: dict = None, expected_revision: str = '',
                         item_offset: int = 0, confirmation: str = '') -> dict:
    # Keep this procedure self-contained: Handler sends its source to native TACTIC.
    import csv
    import datetime
    import decimal
    import hashlib
    import io
    import json
    import math
    import re
    from pyasm.biz import Project
    from pyasm.common import Environment, SecurityException
    from pyasm.search import Search, Sql, DbContainer, DbResource

    if not Environment.get_security().is_admin():
        raise SecurityException('Raw database editing requires administrator access.')
    if action not in ('list', 'load', 'save', 'drop', 'export'):
        raise ValueError('Unknown raw database operation.')
    if type(item_offset) is not int or not 0 <= item_offset <= 100000000:
        raise ValueError('Invalid page offset.')

    def quote_name(name):
        if not isinstance(name, str) or not name or '\x00' in name:
            raise ValueError('Invalid database identifier.')
        return '"' + name.replace('"', '""') + '"'

    def encode(value):
        if isinstance(value, (bytes, bytearray, memoryview)):
            return {'binary': bytes(value).hex()}
        if isinstance(value, (datetime.date, datetime.time, decimal.Decimal)):
            return str(value)
        if isinstance(value, int) and not isinstance(value, bool) and abs(value) > 9007199254740991:
            return str(value)
        if isinstance(value, float) and not math.isfinite(value):
            return str(value)
        if isinstance(value, dict):
            return {key: encode(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [encode(item) for item in value]
        return value if value is None or isinstance(value, (str, int, float, bool)) else str(value)

    def digest(value):
        return hashlib.sha256(json.dumps(encode(value), sort_keys=True, ensure_ascii=False,
                                        default=str).encode('utf-8')).hexdigest()

    def secret_name(name):
        return bool(re.search(r'password|passwd|ticket|token|secret|credential|api_key|private_key', name, re.I))

    def redact(value):
        if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
            try:
                parsed = json.loads(value)
            except (ValueError, RecursionError):
                return value
            masked = redact(parsed)
            return json.dumps(masked, ensure_ascii=False) if masked != parsed else value
        if isinstance(value, dict):
            return {name: '[redacted]' if secret_name(name) else redact(item) for name, item in value.items()}
        if isinstance(value, list):
            return [redact(item) for item in value]
        return value

    resources = {'sthpw': DbResource.get_default('sthpw')}
    for project in Search('sthpw/project').get_sobjects():
        resources[project.get_code()] = project.get_project_db_resource()

    def catalog():
        result, seen = [], set()
        for code, resource in resources.items():
            if str(resource) in seen:
                continue
            seen.add(str(resource))
            sql = DbContainer.get(resource)
            for table in table_names(sql, resource):
                result.append(dict(identity=json.dumps([code, table]),
                                   label=resource.get_database() + ' / ' + table))
        return result

    def table_names(sql, resource):
        if sql.get_vendor() == 'Sqlite':
            return [row[0] for row in sql.do_query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        if sql.get_vendor() == 'PostgreSQL':
            schema = Sql.quote(resource.get_schema() or 'public')
            return [row[0] for row in sql.do_query('SELECT tablename FROM pg_tables WHERE schemaname=' + schema + ' ORDER BY tablename')]
        raise ValueError('Raw editor supports SQLite and PostgreSQL.')

    if action == 'list':
        return dict(catalog=catalog(), metadata={}, canWrite=True)
    try:
        code, table = json.loads(identity)
        resource = resources[code]
    except (ValueError, TypeError, KeyError):
        raise ValueError('Choose an available database table.') from None
    sql = DbContainer.get(resource)
    vendor = sql.get_vendor()
    if vendor not in ('Sqlite', 'PostgreSQL'):
        raise ValueError('Raw editor supports SQLite and PostgreSQL.')

    def literal(value):
        if value is None:
            return 'NULL'
        if isinstance(value, bool) and vendor == 'Sqlite':
            value = int(value)
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, allow_nan=False)
        if not isinstance(value, (str, int, float, bool)) or (isinstance(value, float) and not math.isfinite(value)):
            raise ValueError('Unsupported cell value.')
        if vendor == 'PostgreSQL' and isinstance(value, str):
            return Sql.quote(value.replace('\\', '\\\\'), has_outside_quotes=False, escape=True)
        return Sql.quote(value)

    if table not in table_names(sql, resource):
        raise ValueError('The selected table no longer exists.')
    target = quote_name(table)
    if vendor == 'PostgreSQL':
        schema = resource.get_schema() or 'public'
        target = quote_name(schema) + '.' + target
        info = sql.do_query('SELECT column_name, data_type, column_default, is_generated '
                            'FROM information_schema.columns WHERE table_schema=' + literal(schema)
                            + ' AND table_name=' + literal(table) + ' ORDER BY ordinal_position')
        primary = [row[0] for row in sql.do_query(
            'SELECT a.attname FROM pg_index i JOIN pg_class c ON c.oid=i.indrelid '
            'JOIN pg_namespace n ON n.oid=c.relnamespace '
            'JOIN LATERAL unnest(i.indkey) WITH ORDINALITY k(attnum, ord) ON true '
            'JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=k.attnum '
            'WHERE i.indisprimary AND n.nspname=' + literal(schema)
            + ' AND c.relname=' + literal(table) + ' ORDER BY k.ord')]
        physical_key = 'ctid'
        columns = [dict(name=row[0], type=row[1], default=row[2], generated=row[3] != 'NEVER') for row in info]
    else:
        info = sql.do_query('PRAGMA table_xinfo(' + target + ')')
        primary = [row[1] for row in sorted(info, key=lambda row: row[5]) if row[5]]
        if any(row[5] and not row[3] and not (len(primary) == 1 and row[2].upper() == 'INTEGER') for row in info):
            primary = []  # SQLite permits NULL and duplicates in nullable non-integer PRIMARY KEYs.
        columns = [dict(name=row[1], type=row[2], default=row[4], generated=bool(row[6])) for row in info]
        physical_key = next((name for name in ('rowid', '_rowid_', 'oid')
                             if name not in {column['name'] for column in columns}), None)
    if not columns:
        raise ValueError('No readable columns in this table.')
    for column in columns:
        column['secret'] = secret_name(column['name'])
        column['readonly'] = column['secret'] or column['generated'] or column['type'].lower() in ('blob', 'bytea')
    if any(column['secret'] or column['type'].lower() in ('blob', 'bytea') for column in columns if column['name'] in primary):
        primary = []  # Never serialize a secret or binary primary key as the row locator.
    names = [column['name'] for column in columns]
    revision = digest([identity, columns, primary])
    selection = ', '.join(quote_name(name) for name in names)
    if not primary:
        if not physical_key:
            raise ValueError('This table has no usable row identity.')
        selection += ', ' + physical_key + ('::text' if vendor == 'PostgreSQL' else '')
    order = ', '.join(quote_name(name) for name in primary) if primary else physical_key

    def display(values):
        return {column['name']: '[redacted]' if column['secret'] else redact(encode(values[index]))
                for index, column in enumerate(columns)}

    def read_rows(where='', suffix=''):
        return sql.do_query('SELECT ' + selection + ' FROM ' + target + where + suffix)

    if action in ('save', 'drop'):
        if expected_revision != revision:
            raise ValueError('Table structure changed. Reload before saving.')
        # One table lock protects revision checks and the complete batch together.
        if vendor == 'PostgreSQL':
            sql.do_update('LOCK TABLE ' + target + ' IN ACCESS EXCLUSIVE MODE')
        else:
            impl = sql.get_database_impl()
            if hasattr(impl, 'lock_collection_table'):
                impl.lock_collection_table(sql, table)
            else:
                sql.do_update('UPDATE ' + target + ' SET ' + quote_name(names[0]) + ' = ' + quote_name(names[0]) + ' WHERE 1=0')
        if action == 'drop':
            if confirmation != resource.get_database() + ' / ' + table:
                raise ValueError('Type the database / table name to confirm DROP TABLE.')
            sql.do_update('DROP TABLE ' + target)
            Sql.clear_table_cache()
            return dict(catalog=catalog(), identity='', revision='', document={}, metadata={}, canWrite=True)
        if not isinstance(document, dict) or set(document) != {'rows', 'offset'}:
            raise ValueError('Invalid table draft.')
        rows = document['rows']
        if not isinstance(rows, list) or len(rows) > 200:
            raise ValueError('Save at most 200 rows at a time.')
        item_offset = document['offset']
        if type(item_offset) is not int or not 0 <= item_offset <= 100000000:
            raise ValueError('Invalid page offset.')
        seen = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('values'), dict) or set(row['values']) - set(names):
                raise ValueError('Invalid row values.')
            values = row['values']
            if any(redact(encode(value)) != encode(value) for value in values.values()):
                raise ValueError('Generated, binary and secret columns are read-only.')
            key = row.get('key')
            if key is None:
                if row.get('deleted'):
                    continue
                if any(column['readonly'] and column['name'] in values for column in columns):
                    raise ValueError('Generated, binary and secret columns are read-only.')
                if values:
                    sql.do_update('INSERT INTO ' + target + ' (' + ', '.join(quote_name(name) for name in values)
                                  + ') VALUES (' + ', '.join(literal(value) for value in values.values()) + ')')
                else:
                    sql.do_update('INSERT INTO ' + target + ' DEFAULT VALUES')
                continue
            if not isinstance(key, list) or len(key) != (len(primary) or 1):
                raise ValueError('Invalid row identity.')
            marker = digest(key)
            if marker in seen:
                raise ValueError('Duplicate row identity.')
            seen.add(marker)
            where = ' WHERE ' + (' AND '.join(quote_name(name) + ' = ' + literal(value)
                      for name, value in zip(primary, key)) if primary else physical_key + ' = ' + literal(key[0]))
            current = read_rows(where)
            if len(current) != 1 or row.get('revision') != digest(current[0]):
                raise ValueError('A row changed or was deleted. Reload before saving.')
            if row.get('deleted'):
                sql.do_update('DELETE FROM ' + target + where)
                continue
            original = display(current[0])
            changed = {name: value for name, value in values.items() if value != original[name]}
            if any(column['name'] in changed and (column['readonly'] or original[column['name']] != encode(current[0][index]))
                   for index, column in enumerate(columns)):
                raise ValueError('Generated, binary and secret columns are read-only.')
            if changed:
                sql.do_update('UPDATE ' + target + ' SET ' + ', '.join(quote_name(name) + ' = ' + literal(value)
                              for name, value in changed.items()) + where)
        Sql.clear_table_cache()

    total = sql.get_int('SELECT count(*) FROM ' + target)
    metadata = dict(columns=columns, total=total, offset=item_offset, pageSize=50,
                    label=resource.get_database() + ' / ' + table)
    if action == 'export':
        # shortcut: CSV is bounded at 50000 rows; use a streaming download for larger dumps.
        if total > 50000:
            raise ValueError('CSV export supports up to 50000 rows. Use a database dump for larger tables.')
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(names)
        for record in read_rows(suffix=' ORDER BY ' + order + ' LIMIT 50001'):
            values = display(record)
            writer.writerow([json.dumps(values[name], ensure_ascii=False) if isinstance(values[name], (dict, list))
                             else values[name] for name in names])
        metadata['csv'] = output.getvalue()
    records = []
    for row in read_rows(suffix=' ORDER BY ' + order + ' LIMIT 50 OFFSET ' + str(item_offset)):
        key = [encode(row[names.index(name)]) for name in primary] if primary else [encode(row[-1])]
        values = display(row)
        readonly = [column['name'] for index, column in enumerate(columns)
                    if column['readonly'] or values[column['name']] != encode(row[index])]
        records.append(dict(key=key, revision=digest(row), values=values, readonly=readonly))
    return dict(identity=identity, revision=revision, document=dict(rows=records, offset=item_offset),
                metadata=metadata, canWrite=True)

