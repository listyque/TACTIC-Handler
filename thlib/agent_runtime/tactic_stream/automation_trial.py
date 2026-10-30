"""External host-owned OCI trials; this module never imports TS core or Handler."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TrialFile(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: Annotated[str, Field(pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,95}$')]
    content: Annotated[str, Field(max_length=65536)] = 'Owned test data'


class TrialAction(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Literal['click', 'expect', 'point', 'text', 'backspace']
    target: Annotated[str, Field(max_length=256)] = ''
    contains: Annotated[str, Field(max_length=1024)] = ''
    x: Annotated[int, Field(ge=0, le=2000)] = 0
    y: Annotated[int, Field(ge=0, le=2000)] = 0
    text: Annotated[str, Field(max_length=256)] = ''


class TrialArtifact(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: Annotated[str, Field(pattern=r'^[a-zA-Z0-9][a-zA-Z0-9_./-]{0,95}$')]
    contains: Annotated[str, Field(max_length=8192)] = ''

    @model_validator(mode='after')
    def relative_path(self):
        if '..' in self.name.split('/'):
            raise ValueError('Artifacts must stay inside /work')
        return self


class TrialCase(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    expect: Literal['allow', 'reject', 'modal']
    files: Annotated[list[TrialFile], Field(min_length=1, max_length=8)] = Field(
        default_factory=lambda: [TrialFile(name='input.bin')])
    process: Annotated[str, Field(max_length=128)] = 'publish'
    context: Annotated[str, Field(max_length=128)] = 'publish'
    artifacts: Annotated[list[TrialArtifact], Field(max_length=8)] = Field(default_factory=list)
    actions: Annotated[list[TrialAction], Field(max_length=16)] = Field(default_factory=list)

    @model_validator(mode='after')
    def unique_files(self):
        if len({item.name for item in self.files}) != len(self.files):
            raise ValueError('Trial filenames must be distinct')
        return self


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@contextmanager
def trial_slot(directory):
    with (directory/'.runner.lock').open('a+b') as stream:
        if stream.seek(0, 2) == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ValueError('Trial runner is busy or its OS lock is unavailable; retry the same UUID later') from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def verify_container(value, image):
    config, host = value['Config'], value['HostConfig']
    proxies = {'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}
    allowed = proxies | {'PATH', 'DEBIAN_FRONTEND', 'PYTHONUNBUFFERED', 'PYTHONDONTWRITEBYTECODE',
                         'TACTIC_DATA_DIR', 'HOME', 'QT_QPA_PLATFORM', 'QT_QUICK_BACKEND',
                         'QSG_RENDER_LOOP', 'QT_QUICK_CONTROLS_STYLE', 'LANG', 'LC_ALL'}
    for item in config.get('Env') or []:
        key, _, content = item.partition('=')
        if key not in allowed or key in proxies and content:
            raise RuntimeError('Unexpected trial environment; refusing to expose host configuration')
    if (value['Image'] != image or config['User'] != '10001:10001' or
            host['NetworkMode'] != 'none' or not host['ReadonlyRootfs'] or host['Privileged'] or
            host.get('CapAdd') or host.get('CapDrop') != ['ALL'] or value.get('Mounts') or
            host.get('Binds') or host.get('Devices') or host.get('PortBindings') or
            host.get('PidMode') not in ('', 'private') or host.get('UTSMode') not in ('', 'private') or host.get('IpcMode') != 'private' or
            host.get('CgroupnsMode') != 'private' or host['PidsLimit'] != 128 or
            host['Memory'] != 768*1024*1024 or host['MemorySwap'] != host['Memory'] or
            host['NanoCpus'] != 1000000000 or
            set(host.get('SecurityOpt') or []) != {'no-new-privileges=true', 'seccomp=builtin'} or
            set(host.get('Tmpfs') or {}) != {'/work', '/tmp'} or
            host.get('LogConfig', {}).get('Type') != 'none'):
        raise RuntimeError('Container OS policy does not match the required trial boundary')
    for target, limit in (('/work', '256m'), ('/tmp', '64m')):
        options = set(host['Tmpfs'][target].split(','))
        if not {'rw', 'nosuid', 'nodev', 'size='+limit, 'mode=1777'} <= options:
            raise RuntimeError('Unexpected writable filesystem policy')
    return dict(image=image, network='none', mounts=[], root_read_only=True, uid=10001,
                memory_mb=768, cpu=1, pids=128, no_new_privileges=True, seccomp='builtin')


def attached_trial(name, payload):
    process = subprocess.Popen(['docker', 'start', '--attach', '--interactive', name],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def read(stream, limit):
        chunks, total = [], 0
        while chunk := stream.read(16384):
            total += len(chunk)
            if total > limit:
                process.kill()
                raise ValueError('Isolated output exceeds its size limit')
            chunks.append(chunk)
        return b''.join(chunks)
    def write():
        try:
            process.stdin.write(payload)
        finally:
            process.stdin.close()
    with process.stdout, process.stderr, ThreadPoolExecutor(max_workers=3) as pool:
        output = pool.submit(read, process.stdout, 2*1024*1024)
        errors = pool.submit(read, process.stderr, 16384)
        writer = pool.submit(write)
        try:
            process.wait(timeout=90)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(10)
        writer.result(5)
        return process.returncode, output.result(5), errors.result(5).decode(errors='replace')


class AutomationTrials:
    def __init__(self, image, directory, scope):
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', image):
            raise ValueError('Trial image must be a host-selected immutable local sha256 ID')
        self.image = image
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.scope = digest(scope)

    def read(self, trial_id):
        identity = str(UUID(trial_id))
        if trial_id != identity:
            raise ValueError('Use a canonical trial UUID')
        path = self.directory/(identity+'.json')
        if not path.is_file():
            return dict(trial_id=identity, status='not_found')
        if path.stat().st_size > 4*1024*1024:
            raise ValueError('Trial receipt exceeds its size limit')
        record = json.loads(path.read_text(encoding='utf-8'))
        if record['scope'] != self.scope:
            raise ValueError('Trial is unavailable for this host session/project')
        return record

    def _save(self, path, value):
        descriptor, name = tempfile.mkstemp(dir=self.directory, prefix='.trial-')
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                json.dump(value, stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)

    def run(self, trial_id, draft, case, project):
        with trial_slot(self.directory):
            return self._run(trial_id, draft, case, project)

    def _run(self, trial_id, draft, case, project):
        case = TrialCase.model_validate(case).model_dump()
        document = draft['document']
        if (document['kind'] == 'shelf') != (case['expect'] == 'modal'):
            raise ValueError('Choose a modal UI case for a shelf or allow/reject for a hook')
        if document['kind'] == 'hook' and document['phase'] == 'after' and case['expect'] != 'allow':
            raise ValueError('After hooks run after a successful check-in; use allow')
        for field in ('process', 'context'):
            if document[field] and document[field] != case[field]:
                raise ValueError('Trial context must match the hook binding: ' + field)
        # Dependency freshness belongs to activation, not to replaying the caller's original trial request.
        fingerprint = digest([self.image, draft['draft_id'], draft['revision'], document, case, project])
        previous = self.read(trial_id)
        if previous['status'] != 'not_found':
            if previous['fingerprint'] != fingerprint:
                raise ValueError('Trial ID was used with different inputs')
            return previous
        path = self.directory/(trial_id+'.json')
        record = dict(trial_id=trial_id, scope=self.scope, fingerprint=fingerprint, status='started',
                      image=self.image, draft_id=draft['draft_id'], draft_revision=draft['revision'],
                      document_hash=digest(document), dependency_revision=draft['dependency_revision'], case=case)
        # The OS slot serializes writers; atomic publication keeps concurrent status reads complete.
        self._save(path, record)
        name = 'tactic-automation-trial-' + trial_id
        created = False
        try:
            image = self._docker('image', 'inspect', self.image)[0]
            if image['Os'] != 'linux' or image['Config'].get('Labels', {}).get('tactic.automation-trial') != '1':
                raise ValueError('Choose a built and trusted TACTIC trial image')
            command = ['docker', 'create', '--pull=never', '--name', name, '--label', 'tactic.automation-trial=owned',
                '-i', '--read-only', '--network', 'none', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges=true', '--security-opt', 'seccomp=builtin',
                '--user', '10001:10001', '--pids-limit', '128', '--memory', '768m', '--memory-swap', '768m',
                '--cpus', '1', '--ipc', 'private', '--cgroupns', 'private', '--log-driver', 'none',
                '--tmpfs', '/work:rw,nosuid,nodev,size=256m,mode=1777',
                '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m,mode=1777']
            # Docker client proxy defaults can contain credentials; never forward them to tested code.
            for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'):
                command += ['--env', key+'=']
            subprocess.run(command + [self.image],
                check=True, capture_output=True, timeout=15)
            created = True
            record['isolation'] = verify_container(self._docker('inspect', name)[0], self.image)
            request = dict(document=document, project=project, trial_id=trial_id, case=case)
            payload = json.dumps(request, ensure_ascii=False).encode()
            if len(payload) > 2*1024*1024:
                raise ValueError('Trial input exceeds its size limit')
            returncode, raw, diagnostics = attached_trial(name, payload)
            state = self._docker('inspect', name)[0]['State']
            result = json.loads(raw)
            record.update(result=result, status='passed' if returncode == 0 and not state['OOMKilled']
                          and state['ExitCode'] == 0 and result.get('status') == 'passed' else 'failed',
                          exit_code=state['ExitCode'], diagnostics=diagnostics)
        except Exception as error:
            record.update(status='failed', error=str(error))
        finally:
            if created:
                try:
                    self._remove(name)
                except Exception as error:
                    record.update(status='failed', cleanup_error=str(error), owned_container=name)
            self._save(path, record)
        return record

    @staticmethod
    def _docker(*args):
        result = subprocess.run(['docker', *args], check=True, capture_output=True, timeout=15)
        return json.loads(result.stdout)

    @staticmethod
    def _remove(name):
        subprocess.run(['docker', 'rm', '--force', name], check=True, capture_output=True, timeout=15)

    def require_passed(self, trial_ids, draft, expected_revision):
        if not isinstance(trial_ids, list) or not 1 <= len(trial_ids) <= 4 or len(set(trial_ids)) != len(trial_ids):
            raise ValueError('Provide one to four distinct trial UUIDs')
        records = [self.read(identity) for identity in trial_ids]
        for record in records:
            if (record['status'] != 'passed' or record['image'] != self.image or
                    record['draft_id'] != draft['draft_id'] or record['draft_revision'] != draft['revision'] or
                    record['document_hash'] != digest(draft['document']) or
                    record['dependency_revision'] != expected_revision or draft['dependency_revision'] != expected_revision):
                raise ValueError('A successful isolated trial of this exact draft and dependencies is required')
        document = draft['document']
        required = {'modal'} if document['kind'] == 'shelf' else {'allow', 'reject'} if document['phase'] == 'before' else {'allow'}
        if not required <= {record['case']['expect'] for record in records}:
            raise ValueError('Before activation requires allow AND reject cases; After requires allow; shelf requires modal')
        return records
