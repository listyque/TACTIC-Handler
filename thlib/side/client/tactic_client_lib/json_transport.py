"""TACTIC Stream JSON RPC behind the existing SDK method interface."""
import json
from functools import partial
from urllib.error import HTTPError
from urllib.request import Request
from xmlrpc.client import Fault

from .rpc_json import CODEC, decode, encode


def _reject_constant(value):
    raise ValueError('Invalid JSON constant: ' + value)


class JsonServerProxy:
    def __init__(self, server_url, transport=None):
        from thlib.proxy import UrllibTransport

        self.url = server_url.rstrip('/') + '/admin/rpc'
        self.transport = transport if transport is not None else UrllibTransport()

    def __getattr__(self, method):
        if method.startswith('_'):
            raise AttributeError(method)
        return partial(self._request, method)

    def _request(self, method, *args, **kwargs):
        payload = {'method': method, 'args': encode(args), 'kwargs': encode(kwargs), 'codec': CODEC}
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        request = Request(self.url, body, {'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            with self.transport.open(request) as response:
                data = response.read()
        except HTTPError as error:
            with error:
                data = error.read()
            if error.code in (502, 503, 504):
                raise
            try:
                failure = json.loads(data, parse_constant=_reject_constant)
            except (ValueError, UnicodeError):
                failure = {}
            message = failure.get('error') if isinstance(failure, dict) else None
            if error.code == 404 or not isinstance(message, str):
                message = 'JSON RPC is unavailable. Select XML-RPC for Legacy TACTIC or update TACTIC Stream.'
            raise Fault(error.code, message) from error
        try:
            result = json.loads(data, parse_constant=_reject_constant)
            if not isinstance(result, dict) or result.get('codec') != CODEC or 'result' not in result:
                raise ValueError('Missing SDK response envelope')
            return decode(result['result'])
        except (ValueError, UnicodeError, TypeError) as error:
            raise Fault(502, 'Invalid JSON RPC response. Select XML-RPC for Legacy TACTIC or update TACTIC Stream.') from error
