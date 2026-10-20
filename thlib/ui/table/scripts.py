"""Qt JS process isolation keeps even pure JS loops away from Python's UI GIL."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

RUNTIME = Path(__file__).resolve().parents[1] / 'qml/features/table/runtime'
MAX_MESSAGE = 16 * 1024 * 1024


class TableScriptRunner:
    def __init__(self, server, context, progress=lambda title, detail: None):
        self.server, self.context, self.progress = server, dict(context), progress
        self.cancelled = threading.Event()
        self._lock = threading.Lock()
        self._process = None

    def cancel(self):
        self.cancelled.set()
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                self._process.kill()

    def _call(self, message):
        method = message['method']
        if not isinstance(method, str) or method.startswith('_') or method in ('get_ticket', 'get_ticket_data'):
            raise ValueError('Authentication methods are unavailable in table actions')
        args, kwargs = message['args'], message['kwargs']
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            raise ValueError('Invalid table script API arguments')
        function = getattr(self.server, method, None)
        if not callable(function):
            raise ValueError('Unsupported TACTIC API method: ' + method)
        self.server.set_project(message['project'])
        return function(*args, **kwargs)

    def run(self, source, confirmation=None):
        if self.cancelled.is_set():
            raise InterruptedError('Table action cancelled')
        command = [sys.executable, '--table-script-worker'] if getattr(sys, 'frozen', False) else [
            sys.executable, '-B', str(Path(__file__).with_name('script_worker.py'))]
        with tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors,
                text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            with self._lock:
                self._process = process
                if self.cancelled.is_set():
                    process.kill()
            timer = threading.Timer(120, self.cancel)
            timer.daemon = True
            timer.start()
            try:
                process.stdin.write(json.dumps(dict(source=source, context=dict(self.context, confirmation=confirmation)), ensure_ascii=False)+'\n')
                process.stdin.flush()
                while not self.cancelled.is_set():
                    line = process.stdout.readline(MAX_MESSAGE)
                    if not line or not line.endswith('\n'):
                        if self.cancelled.is_set():
                            break
                        errors.seek(0)
                        raise ValueError('Table JS worker stopped: ' + errors.read(4096).decode('utf-8', errors='replace'))
                    message = json.loads(line)
                    if message['type'] == 'result':
                        return message['result']
                    if message['type'] == 'error':
                        raise ValueError(message['error'])
                    if message['type'] == 'progress':
                        self.progress(message['title'], message['detail'])
                        continue
                    if message['type'] != 'call':
                        raise ValueError('Invalid table JS worker message')
                    if self.cancelled.is_set():
                        break
                    try:
                        reply = dict(ok=True, value=self._call(message))
                    except Exception as error:
                        reply = dict(ok=False, error=str(error))
                    if self.cancelled.is_set():
                        break
                    process.stdin.write(json.dumps(reply, default=str)+'\n')
                    process.stdin.flush()
                raise InterruptedError('Table action cancelled. Some operations may already have completed.')
            except (OSError, BrokenPipeError):
                if self.cancelled.is_set():
                    raise InterruptedError('Table action cancelled. Some operations may already have completed.') from None
                raise
            finally:
                timer.cancel()
                timer.join()
                with self._lock:
                    if process.poll() is None:
                        process.kill()
                    self._process = None
                process.wait(timeout=5)
                process.stdin.close()
                process.stdout.close()
