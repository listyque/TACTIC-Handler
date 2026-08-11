from .environment import gf


def __getattr__(name):
    return getattr(gf(), name)
