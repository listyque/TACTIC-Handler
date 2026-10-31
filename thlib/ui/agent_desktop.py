"""Authenticated desktop companion for explicit local executor controls."""
from copy import deepcopy
import json
from pathlib import Path
import socket
from uuid import uuid4

from PySide6.QtCore import QObject, QTimer

from thlib.local_agent import LocalAgents

COMMAND = 'tactic.ui.panel.agent_executor_cmd.AgentExecutorCmd'


class AgentDesktopController(QObject):
    def __init__(self, application, pool):
        super().__init__(application)
        self.application, self.pool = application, pool
        self.session = None
        self.available = None
        self.generation = 0
        self.worker = None
        self.device, self.acks = '', []
        self.agents = None
        self.timer = QTimer(self)
        self.timer.setInterval(4000)
        self.timer.timeout.connect(self.poll)
        application.authentication_changed.connect(self.sync)
        application.signing_out.connect(self.close)
        self.sync()

    def sync(self):
        from thlib.environment import env_server, env_mode
        ticket = env_server.get_ticket()
        if self.application.authentication_required or not self.application.can_administer or not ticket:
            self.close()
            return
        session = (env_server.get_server(), env_server.get_user(), ticket)
        if session != self.session:
            self.close()
            self.session = session
            self.device = str(uuid4())
            self.agents = LocalAgents(Path(env_mode.get_current_path()) / 'cache/agent_python')
            from thlib import tactic_classes as tc
            self.server = tc.server_start(project='admin')
        if self.available is False:
            return
        self.timer.start()
        self.poll()

    def close(self):
        self.timer.stop()
        self.generation += 1
        if self.agents:
            self.agents.close()
        self.session, self.device, self.acks, self.worker = None, '', [], None
        self.available = None

    def poll(self):
        if not self.session or self.worker or self.available is False:
            return
        if self.pool.is_stopped:
            self.pool.start()
        values = dict(action='desktop_poll', project_code='admin', device=self.device, label=socket.gethostname(),
                      reports=self.agents.reports(), acks=list(self.acks))
        self.worker = self.pool.add_task(self.load, self.server, values, self.generation, self.available)
        self.worker.result.connect(self.done)
        self.worker.start()

    @staticmethod
    def load(server, values, generation, available=None):
        try:
            if available is None:
                available = server.class_exists(COMMAND)
            if not available:
                return dict(generation=generation, available=False)
            result = server.execute_cmd(COMMAND, values)
            if result.get('status') != 'OK':
                raise RuntimeError(result.get('description') or 'Desktop companion unavailable')
            info = json.loads(result['info']) if isinstance(result['info'], str) else result['info']
            return dict(generation=generation, available=True, info=info, acks=values['acks'])
        except Exception:
            # An offline server does not authorize stopping/replaying local user work.
            return dict(generation=generation, available=available)

    def done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        if result['generation'] != self.generation:
            return
        self.worker = None
        self.available = result.get('available')
        if self.available is False:
            self.timer.stop()
            return
        if 'info' not in result or not self.session:
            return
        self.acks = [code for code in self.acks if code not in result['acks']]
        url, _, ticket = self.session
        if '://' not in url:
            url = 'http://' + url
        for command in result['info']['commands']:
            operation = command['operation']
            if operation in self.acks:
                continue
            if command['action'] == 'start':
                self.agents.start(command['project'], operation, url, ticket)
            elif command['action'] == 'stop':
                self.agents.stop(command['project'], operation)
            else:
                continue
            self.acks.append(operation)

    def decorate(self, executor):
        result = deepcopy(executor)
        result['preferred'] = self.device
        return result

    def stop_local(self, project, values):
        if self.agents and values.get('target') == self.device and values.get('action') == 'stop':
            self.agents.stop(project)
