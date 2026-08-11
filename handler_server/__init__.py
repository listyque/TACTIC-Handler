"""Local command bridge for standalone TACTIC-Handler and thin DCC clients."""

from .client import ThinClient
from .registry import CommandRegistry
from .server import HandlerServer

__all__ = ["CommandRegistry", "HandlerServer", "ThinClient"]
