from .environment import tc


def __getattr__(name):
    return getattr(tc(), name)
