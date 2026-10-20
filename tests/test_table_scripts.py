"""Actual Qt JS execution stays in a worker and cannot replay writes for confirmation."""
import concurrent.futures
import json
from pathlib import Path
import threading
import unittest

from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from thlib.ui.table.scripts import RUNTIME, TableScriptRunner


class Server:
    def __init__(self):
        self.project = 'cg'
        self.calls = []
        self.entered = threading.Event()
        self.release = threading.Event()

    def set_project(self, project):
        self.project = project

    def query(self, search_type, **options):
        self.calls.append(('query', search_type, options, self.project))
        return [{'code':'ASSET01'}]

    def execute_cmd(self, class_name, args=None, values=None, **options):
        self.calls.append(('execute_cmd', class_name, args, values, options))
        return {'info':True}

    def get_by_search_key(self, key):
        self.entered.set()
        if not self.release.wait(3):
            raise TimeoutError('Test barrier was not released')
        self.calls.append(('get_by_search_key', key))
        return {'code':'admin','display_name':'Admin'}


class TableScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def runner(self, server=None, progress=lambda title, detail:None):
        return TableScriptRunner(server or Server(),dict(searchKey='cg/assets?code=ASSET01',
            searchKeys=['cg/assets?code=ASSET01'],searchType='cg/assets',project='cg',
            record={'code':'ASSET01'},column='action',view='table'),progress)

    def run_worker(self, runner, source, confirmation=None):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(runner.run,source,confirmation).result(timeout=5)

    def test_original_client_api_and_resources_are_independent_identical_copies(self):
        stream = Path('D:/code/TACTIC_VUE/tactic_stream/src')
        if not stream.exists():
            self.skipTest('Counterpart checkout is unavailable')
        self.assertEqual((RUNTIME/'client_api.js').read_bytes(),(stream/'pyasm/common/js/client_api.js').read_bytes())
        self.assertEqual((RUNTIME/'table_action_runtime.js').read_bytes(),(stream/'tactic_stream/compatibility/table_action_runtime.js').read_bytes())
        server = Server()
        result = self.run_worker(self.runner(server),"return TacticServerStub.get().query('cg/assets',{limit:2});")
        self.assertEqual(result['output'],[{'code':'ASSET01'}])
        self.assertEqual(server.calls,[('query','cg/assets',{'limit':2},'cg')])

    def test_confirmation_before_api_never_replays_a_mutation(self):
        server = Server()
        runner = self.runner(server)
        source = "if(confirm('Continue?')) TacticServerStub.get().execute_cmd('ExampleCmd',{code:'A'});"
        first = self.run_worker(runner,source)
        self.assertEqual(first,dict(confirmation='Continue?',commands=[],calls=0))
        self.assertEqual(server.calls,[])
        self.run_worker(runner,source,dict(message='Continue?',accepted=False))
        self.assertEqual(server.calls,[])
        result = self.run_worker(runner,source,dict(message='Continue?',accepted=True))
        self.assertEqual(result['calls'],1)
        self.assertEqual(server.calls,[('execute_cmd','ExampleCmd',{'code':'A'}, {}, {})])
        with self.assertRaisesRegex(ValueError,'Confirm before making server calls'):
            self.run_worker(self.runner(),"TacticServerStub.get().query('cg/assets'); confirm('Too late');")

    def test_blocked_api_does_not_block_qt_event_loop_and_cancel_prevents_next_write(self):
        server = Server()
        runner = self.runner(server)
        ticks = []
        timer = QTimer()
        timer.setInterval(5)
        timer.timeout.connect(lambda:ticks.append(1))
        timer.start()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(runner.run,"var s=TacticServerStub.get(); s.get_by_search_key(bvr.search_key); s.execute_cmd('MustNotRun');")
            try:
                self.assertTrue(server.entered.wait(2))
                QTest.qWait(50)
                self.assertGreaterEqual(len(ticks),3)
                runner.cancel()
            finally:
                server.release.set()
                timer.stop()
            with self.assertRaises(InterruptedError):
                future.result(timeout=3)
        self.assertFalse(any(call[0]=='execute_cmd' for call in server.calls))

    def test_cpu_loop_is_interruptible_without_a_browser_engine(self):
        entered = threading.Event()
        runner = self.runner(progress=lambda title,detail:entered.set())
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(runner.run,"spt.api.app_busy_show('Loop'); while(true) {}")
            try:
                self.assertTrue(entered.wait(2))
            finally:
                runner.cancel()
            with self.assertRaises(InterruptedError):
                future.result(timeout=3)


if __name__ == '__main__':
    unittest.main()
