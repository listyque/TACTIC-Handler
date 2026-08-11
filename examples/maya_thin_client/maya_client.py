from __future__ import annotations

from handler_server.client import ThinClient
from handler_server.maya_adapter import MayaAdapter
from tactic_handler_dcc import environment as dcc_environment


_client = None


def start(host=None, port=None, token=None, client_id=""):
    global _client
    if _client:
        return _client
    adapter = MayaAdapter()
    if host is None and port is None and token is None:
        _client = ThinClient.local(
            "maya", registry=adapter.registry(), client_id=client_id,
            dispatch=adapter.dispatch,
        )
    else:
        if host is None or port is None or token is None:
            raise ValueError(
                "Manual connection requires host, port, and token"
            )
        _client = ThinClient(
            host, port, token, "maya", registry=adapter.registry(),
            client_id=client_id, dispatch=adapter.dispatch,
        )
    _client.start()
    if not _client.wait_connected(10.0):
        _client.stop()
        _client = None
        raise ConnectionError(
            "TACTIC Handler Server was not discovered. Start the modern "
            "TACTIC-Handler application and try again."
        )
    dcc_environment.configure(_client)
    return _client


def stop():
    global _client
    if _client:
        _client.stop()
        _client = None
