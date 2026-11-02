"""Optional runner denials stored in native TACTIC group access rules."""


def query_runner_access(project_code: str) -> str:
    """Execute in the authenticated server context; no client group claims."""
    import json
    from xml.etree import ElementTree
    from pyasm.biz import Project
    from pyasm.common import Environment

    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select the script project first')
    security = Environment.get_security()
    denied = set()
    if not security.is_admin():
        for group in security.get_groups():
            bound = group.get_value('project_code', no_exception=True) or ''
            if bound and bound != project_code:
                continue
            xml = group.get_value('access_rules', no_exception=True) or '<rules/>'
            if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():
                raise ValueError('Document types and XML entities are not supported')
            for rule in ElementTree.fromstring(xml).findall('rule'):
                if (rule.get('group') or rule.get('category')) != 'script_runner':
                    continue
                if (bound or rule.get('project') or '*') not in ('*', project_code):
                    continue
                if rule.get('access') in ('deny', 'false') and rule.get('key'):
                    denied.add(rule.get('key'))
    return json.dumps({'project': project_code, 'denied': sorted(denied)})
