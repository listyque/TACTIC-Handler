"""Own local host processes. No server checkout, shell command or stored ticket."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

RUNTIME = Path(__file__).resolve().parent / 'agent_runtime'
BUSY = ('preparing', 'starting', 'connected', 'stopping')


class LocalAgents:
    def __init__(self, cache):
        self.cache = Path(cache)
        self.runs = {}
        self.lock = threading.Lock()

    def reports(self):
        with self.lock:
            return {project: dict(run['report']) for project, run in self.runs.items()}

    def start(self, project, operation, url, ticket):
        with self.lock:
            previous = self.runs.get(project)
            if previous and previous['report']['state'] in BUSY:
                previous['report']['operation'] = operation
                return
            run = dict(report=dict(operation=operation, state='preparing', error=''), stop=threading.Event())
            self.runs[project] = run
            run['thread'] = threading.Thread(target=self.run, args=(project, run, url, ticket))
            run['thread'].start()

    def stop(self, project, operation=None):
        with self.lock:
            run = self.runs.get(project)
            if not run:
                if operation:
                    self.runs[project] = dict(report=dict(operation=operation, state='stopped', error=''))
                return
            if operation:
                run['report']['operation'] = operation
            if run['report']['state'] in BUSY:
                run['report']['state'] = 'stopping'
                run['stop'].set()

    def close(self):
        for project in list(self.runs):
            self.stop(project)

    def update(self, run, state, error=''):
        with self.lock:
            if run['stop'].is_set() and state in ('preparing', 'starting', 'connected'):
                return
            run['report'].update(state=state, error=error[:2000])

    @staticmethod
    def kill(process):
        if process.poll() is not None:
            return
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=15)
        else:
            import signal
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=15)

    def prepare(self, stop):
        from PySide6.QtCore import QLockFile
        self.cache.parent.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(self.cache) + '.lock')
        while not lock.tryLock(100):
            if stop.is_set():
                return None
        try:
            python = self.cache / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
            ready = self.cache / 'agent-requirements.txt'
            requirements = (RUNTIME / 'requirements.txt').read_bytes()
            commands = []
            if not python.is_file() or not ready.is_file():
                commands.append([sys.executable, '-m', 'venv', str(self.cache)])
            if commands or ready.read_bytes() != requirements:
                commands.append([str(python), '-m', 'pip', 'install', '--disable-pip-version-check',
                                 '-r', str(RUNTIME / 'requirements.txt')])
            for command in commands:
                if stop.is_set():
                    return None
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding='utf-8', errors='replace', **self.flags())
                try:
                    deadline = time.monotonic() + 300
                    while True:
                        try:
                            output = process.communicate(timeout=.2)[0]
                            break
                        except subprocess.TimeoutExpired:
                            if stop.is_set() or time.monotonic() >= deadline:
                                self.kill(process)
                                if stop.is_set():
                                    return None
                                raise RuntimeError('Local agent dependency installation timed out. Check the network and retry.')
                    if process.returncode:
                        raise RuntimeError('Could not prepare the local agent environment: ' + output[-2000:])
                finally:
                    self.kill(process)
            if not stop.is_set():
                ready.write_bytes(requirements)
                return python
        finally:
            lock.unlock()

    @staticmethod
    def flags():
        return dict(start_new_session=os.name != 'nt', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

    def run(self, project, run, url, ticket):
        process = None
        try:
            python = self.prepare(run['stop'])
            if not python or run['stop'].is_set():
                self.update(run, 'stopped')
                return
            self.update(run, 'starting')
            environment = dict(os.environ, TACTIC_AGENT_TICKET=ticket, PYTHONPATH=str(RUNTIME), PYTHONUTF8='1')
            environment.pop('TACTIC_AGENT_PASSWORD', None)
            command = [str(python), '-B', '-X', 'utf8', '-m', 'tactic_stream.agent_worker',
                       '--server', url, '--project', project, '--stream-root', str(RUNTIME),
                       '--handler-root', str(Path(__file__).resolve().parents[1]), '--allow-changes']
            process = subprocess.Popen(command, env=environment, cwd=RUNTIME, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', **self.flags())

            def stopping():
                while process.poll() is None:
                    if run['stop'].wait(.2):
                        try:
                            process.stdin.write('stop\n')
                            process.stdin.flush()
                            process.wait(timeout=10)
                        except (OSError, subprocess.TimeoutExpired):
                            self.kill(process)
                        return

            watcher = threading.Thread(target=stopping, daemon=True)
            watcher.start()
            last = ''
            for line in process.stdout:
                last = (last + line)[-2000:].replace(ticket, '[REDACTED]')
                if line.startswith('TACTIC_EXECUTOR:'):
                    value = json.loads(line.removeprefix('TACTIC_EXECUTOR:'))
                    self.update(run, value['state'], value['error'].replace(ticket, '[REDACTED]'))
            process.wait()
            watcher.join(timeout=1)
            if run['stop'].is_set():
                self.update(run, 'stopped')
            elif run['report']['state'] != 'failed':
                self.update(run, 'failed', last or 'The local agent stopped unexpectedly. Reconnect it to try again.')
        except Exception as error:
            self.update(run, 'stopped' if run['stop'].is_set() else 'failed', str(error).replace(ticket, '[REDACTED]'))
        finally:
            if process:
                self.kill(process)
                process.stdin.close()
                process.stdout.close()
