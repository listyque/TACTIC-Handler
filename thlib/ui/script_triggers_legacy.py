"""Handler hooks through the original TACTIC SDK, without Stream commands."""

import hashlib
import json


def read_hooks(server) -> dict:
    records = server.query(
        'config/trigger', [('trigger_type', 'handler_script_hook')],
        show_retired=True,
    ) or []
    if isinstance(records, dict):
        records = [records]
    owned = [{key: row.get(key) for key in (
        'code', 'title', 'description', 'event', 'script_path',
        'trigger_type', 'data', 's_status', 'timestamp',
    )} for row in records]
    owned.sort(key=lambda row: str(row.get('code') or ''))
    revision = hashlib.sha256(json.dumps(
        owned, sort_keys=True, ensure_ascii=False, default=str,
        separators=(',', ':'),
    ).encode('utf-8')).hexdigest()
    return dict(records=records, revision=revision)


def save_hooks(server, project: str, rules: list[dict], expected_revision: str) -> dict:
    if len(rules) > 256:
        raise ValueError('Expected at most 256 Handler trigger rules')
    login_ticket = server.get_login_ticket()
    server.start('Save Handler script triggers')
    try:
        current = read_hooks(server)
        if current['revision'] != expected_revision:
            raise RuntimeError('Script triggers changed on the server. Reload before saving.')
        existing = {row['code'] for row in current['records']}
        codes = [rule['code'] for rule in rules if rule.get('code')]
        if len(set(codes)) != len(codes) or set(codes) - existing:
            raise ValueError('Trigger identity is missing or duplicated')
        for order, rule in enumerate(rules):
            data = dict(
                title=rule['title'].strip(), description=rule['description'].strip(),
                event='handler|' + '|'.join((rule['phase'], *rule['action'].split('.'))),
                script_path=rule['script'].strip().strip('/'),
                trigger_type='handler_script_hook',
                data=json.dumps(dict(
                    version=1, action=rule['action'], phase=rule['phase'],
                    search_type=rule['searchType'],
                    search_keys=list(dict.fromkeys(
                        key.strip() for key in rule['searchKeysText'].replace(',', '\n').splitlines()
                        if key.strip()
                    )),
                    process=rule['process'], context=rule['context'], order=order,
                ), ensure_ascii=False, separators=(',', ':')),
                s_status='' if rule['enabled'] else 'retired',
            )
            if rule.get('code'):
                key = server.build_search_key('config/trigger', rule['code'], project_code=project)
                server.update(key, data, triggers=True)
            else:
                server.insert('config/trigger', data, triggers=True)
        for code in existing - set(codes):
            key = server.build_search_key('config/trigger', code, project_code=project)
            server.delete_sobject(key)
        server.finish()
    except Exception:
        server.abort()
        raise
    finally:
        # The original SDK clears its active ticket after abort().
        server.set_login_ticket(login_ticket)
    return read_hooks(server)
