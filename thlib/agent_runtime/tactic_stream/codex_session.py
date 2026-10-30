"""Small stdio client for the installed Codex app-server protocol."""
import json
import queue
import subprocess
import threading
import time
import os
import signal


def stop_process(process):
    if process.poll() is not None:
        return
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=15)
    else:
        os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=15)


class CodexSession:
    def __init__(self, command, environment, cwd):
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding='utf-8', errors='replace', env=environment,
            cwd=cwd, start_new_session=os.name != 'nt', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        self.incoming = queue.Queue()
        self.notifications = []
        self.serial = 0
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        try:
            self.call('initialize', dict(clientInfo=dict(name='tactic_admin', version='1.0'), capabilities=dict(experimentalApi=False)))
            self.send(dict(method='initialized'))
        except BaseException:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.process.stdout:
                try:
                    self.incoming.put(json.loads(line))
                except ValueError:
                    self.incoming.put(dict(error=dict(message='Codex returned invalid protocol data')))
        finally:
            self.incoming.put(None)

    def send(self, message):
        self.process.stdin.write(json.dumps(message, ensure_ascii=False) + '\n')
        self.process.stdin.flush()

    def receive(self, timeout=1):
        try:
            message = self.incoming.get(timeout=timeout)
        except queue.Empty:
            return {}
        if message is None:
            raise RuntimeError('Codex connection closed')
        if 'method' in message and 'id' in message:
            self.send(dict(id=message['id'], error=dict(code=-32601, message='Interactive external tool approvals are unavailable in this host')))
            raise RuntimeError('Codex requested an unsupported interactive operation')
        return message

    def call(self, method, params, timeout=60):
        self.serial += 1
        code = self.serial
        self.send(dict(id=code, method=method, params=params))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            message = self.receive()
            if message.get('id') == code:
                if 'error' in message:
                    raise RuntimeError(str(message['error'].get('message', 'Codex operation failed')))
                return message['result']
            if message:
                self.notifications.append(message)
        raise RuntimeError('Codex protocol response timed out')

    def close(self):
        stop_process(self.process)
        self.process.stdin.close()
        self.process.stdout.close()
        self.reader.join(timeout=2)
