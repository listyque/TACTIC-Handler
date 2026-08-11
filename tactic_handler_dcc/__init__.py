"""Thin, name-compatible access to the TACTIC-Handler API."""

from .environment import configure, env_inst, gf, mf, tc
from .session import TacticSession

__all__ = ["TacticSession", "configure", "env_inst", "gf", "mf", "tc"]
