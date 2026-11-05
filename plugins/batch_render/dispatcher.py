"""Batch plugin launch facade; rendering and HTTP remain separate owners."""
from .domain import BATCH_DISPATCHER_CONFIG
from .controller import BatchDispatcherController
from .window import show, _dispose_window, _RUNTIME_WINDOWS
