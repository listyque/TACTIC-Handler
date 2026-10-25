"""Project-bound authoring API; execution remains in native Handler hooks/shelves."""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess


class Automation:
    def __init__(self, api, project_code):
        self._api = api
        self._project = project_code
        self._server = api._core.server_start(project=project_code)

    def _call(self, action, **values):
        self._api._check()
        result = self._server.execute_cmd('tactic.ui.panel.handler_automation_cmd.HandlerAutomationCmd',
            dict(action=action, project_code=self._project, **deepcopy(values)))
        if not isinstance(result, dict) or result.get('status') != 'OK':
            raise RuntimeError('Handler automation command failed')
        info = result.get('info')
        return json.loads(info) if isinstance(info, str) else deepcopy(info)

    def read(self):
        return self._call('read')

    def preview(self, document):
        return self._call('preview', document=document)

    def save_hooks(self, rules, expected_revision, operation_id):
        return self._call('save_hooks', rules=rules, expected_revision=expected_revision, operation_id=operation_id)

    def save_draft(self, document, expected_revision, operation_id):
        return self._call('save_draft', document=document, expected_revision=expected_revision, operation_id=operation_id)

    def draft(self, draft_id):
        return self._call('draft', draft_id=draft_id)

    def activate(self, draft_id, draft_revision, expected_revision, operation_id):
        return self._call('activate', draft_id=draft_id, draft_revision=draft_revision,
                          expected_revision=expected_revision, operation_id=operation_id)

    def operation(self, operation_id):
        return self._call('operation', operation_id=operation_id)


def run_checkin_program(argv, payload, *, timeout=60, per_file=False):
    """Explicit native program invocation, not a sandbox or an exactly-once side effect."""
    if (not isinstance(argv, (list, tuple)) or not argv or
            any(not isinstance(value, str) or '\x00' in value for value in argv)):
        raise ValueError('Provide an executable and arguments as a string list')
    if not Path(argv[0]).is_absolute() or not Path(argv[0]).is_file():
        raise ValueError('Choose an existing absolute executable path')
    if os.name == 'nt' and Path(argv[0]).suffix.lower() in ('.bat', '.cmd'):
        raise ValueError('Choose a program executable rather than a shell batch file')
    if type(per_file) is not bool:
        raise ValueError('per_file must be boolean')
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 300:
        raise ValueError('Timeout must be between 0 and 300 seconds')
    files = [str(item['path']) for item in payload.get('files', []) if item.get('path')]
    uses_file = any('{file}' in value for value in argv)
    if uses_file and (not files or not per_file and len(files) != 1):
        raise ValueError('Use per_file=True for several inputs; a file token requires actual input files')
    values = {name: str(payload.get(name) or '') for name in ('project_code', 'search_key', 'process', 'context', 'operation_id', 'result_search_key')}
    results = []
    for path in files if uses_file and per_file else [files[0] if files else '']:
        arguments = []
        for value in argv:
            replacements = dict(values, file=path)
            arguments.append(re.sub(r'\{(file|project_code|search_key|process|context|operation_id|result_search_key)\}',
                                    lambda match: replacements[match[1]], value))
        # This is normal user-authorized execution. Arguments are never parsed by a shell.
        # shortcut: programs own descendant cleanup; add a process-tree runner before accepting untrusted programs.
        try:
            result = subprocess.run(arguments, capture_output=True, text=True, errors='replace', timeout=timeout,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except subprocess.TimeoutExpired as error:
            for output in (error.stdout, error.stderr):
                if output:
                    print(output.decode(errors='replace') if isinstance(output, bytes) else output, end='')
            raise
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='')
        if result.returncode:
            raise RuntimeError(f'Check-in program exited with code {result.returncode}')
        results.append(dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
    return results
