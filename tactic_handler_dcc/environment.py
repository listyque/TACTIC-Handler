from __future__ import annotations

from .session import configure_session, current_session


def configure(client, target="@modern_ui", timeout=60.0):
    return configure_session(client, target, timeout)


def tc():
    return current_session().module("tactic_classes")


def gf():
    return current_session().module("global_functions")


def mf():
    from .maya_functions import MayaFunctions
    return MayaFunctions.instance()


class EnvironmentInstance:
    def __getattr__(self, name):
        return getattr(current_session().environment, name)


env_inst = EnvironmentInstance()
