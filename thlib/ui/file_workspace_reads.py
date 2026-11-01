"""One cancellable read request and one pending view request, independent of writes."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import threading
import traceback

from PySide6.QtCore import Slot, Qt
from .file_workspace_interaction import VIEW_FIELDS

READ_ACTIONS={'stream_editor','changelist_details','select_tree_files','catalog_page','activate_tab','select_directory','choose_stream','toggle_depot','more_depot','toggle_workspace_tree',
              'more_workspace_tree','toggle_change','more_change','select_change','history','history_preview','preview','files',
              'next_files','previous_files','next_changes','next_tasks','next_conflicts','transfer_status',
              'task_files','next_task_files','compare','shelf_targets','shelf_targets_more'}
READ_FIELDS=tuple(key for key in VIEW_FIELDS if key not in ('selected','selection_ids','selection_scope','selection_records',
                    'selection_query','focus_id','anchor_id','columns','sort_column','sort_desc','name_filter','status_filter','scroll'))+(
    'files_selection','files_stream','files_prefix','files_source','tree_selection','depot_tree','depot_heads','depot_expanded',
    'workspace_tree','workspace_tree_root','workspace_expanded','conflicts','conflicts_after','resolved_conflicts',
    'administrator','catalog_capabilities','storage_info','stream_editor','change_details','history_preview','preview','comparison','tasks','tasks_after','task_files','task_files_after','task_info','shelves','shelves_after')


class FileWorkspaceReads:
    def _init_reads(self):
        self._read_generation=0
        self._read_worker=None
        self._read_worker_generation=-1
        self._read_pending=None
        self._read_cancel=threading.Event()

    def _start_read(self,action,values):
        if not self.application.is_stream_server:
            return
        self._read_generation+=1
        self._read_cancel.set()
        self._read_pending=(action,dict(values))
        if self._read_worker is None:
            self._run_read()

    def _run_read(self):
        from thlib.environment import env_inst,env_server,env_mode
        from thlib.proxy import UrllibTransport
        from thlib.side.client.tactic_client_lib.file_transfer import FileTransferClient
        if not self.application.is_stream_server or not self._read_pending or not self.enabled:
            return
        action,values=self._read_pending
        self._read_pending=None
        generation=self._read_generation
        state=deepcopy({key:value for key,value in self._data.items() if key!='tab_states'})
        cancelled=threading.Event()
        self._read_cancel=cancelled
        server=str(env_server.get_server()).rstrip('/')
        if not server.startswith(('http://','https://')):
            server='http://'+server
        ticket=str(env_server.get_ticket())
        project=self._project_code
        from .file_workspace_recovery import cache_directory
        cache=cache_directory(env_mode.current_path,server,env_server.get_user(),project,state['workspace'],state['root'])
        def execute():
            try:
                if not self.application.is_stream_server:
                    raise InterruptedError('The Stream file workspace session changed')
                client=FileTransferClient(server,ticket,project,opener_factory=UrllibTransport)
                native=client.rpc
                def call(rpc_action,**kwargs):
                    if cancelled.is_set() or not self.application.is_stream_server:
                        raise InterruptedError('View request replaced')
                    return native(rpc_action,**kwargs)
                client.rpc=call
                result=self._execute(client,state,cache,action,values,cancelled)
                if not cancelled.is_set():
                    return result
                else:
                    return None
            except Exception as error:
                return {'read_error':error,'stacktrace':traceback.format_exc()}
        worker=env_inst.server_pool.add_task(execute)
        if worker is None:
            self._log('WARNING',self.tr('File worker pool is unavailable'))
            return
        self._read_worker=worker
        self._read_worker_generation=generation
        worker.add_result_data(generation)
        worker.result.connect(self._read_result,Qt.ConnectionType.QueuedConnection)
        worker.start()

    @Slot(object)
    def _read_result(self,envelope):
        result,generation=envelope
        if generation != self._read_worker_generation:
            return
        self._read_worker=None
        if generation==self._read_generation and result:
            if 'read_error' in result:
                error=result['read_error']
                if not isinstance(error,InterruptedError):
                    self._log('WARNING',self.tr('Could not load this view. Open Debug Log for details.'))
                    debug=getattr(self.application,'debug_log',None)
                    if debug:
                        debug.log('ERROR',str(error),group='server/file_workspace',source='File view',stacktrace=result['stacktrace'])
            else:
                notice=result.pop('operation_notice',None)
                if notice:self._log(notice['level'],self.tr(notice['message']))
                self._data.update({key:result[key] for key in READ_FIELDS if key in result})
                self.stateChanged.emit()
        if self._read_pending:
            self._run_read()

    def _stop_reads(self,dispose=False):
        self._read_generation+=1
        self._read_pending=None
        self._read_cancel.set()
        if dispose and self._read_worker:
            self._read_worker.result.disconnect(self._read_result)
            self._read_worker.cancel()
            self._read_worker=None
