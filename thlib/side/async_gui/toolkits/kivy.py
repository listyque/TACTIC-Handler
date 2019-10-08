#!/usr/bin/env python
# -*- coding: utf-8 -*-
from kivy.base import EventLoop

from ..engine import Engine


class KivyEngine(Engine):
    """ Kivy support
    """
    def update_gui(self):
        if EventLoop.window and hasattr(EventLoop.window, '_mainloop'):
            EventLoop.window._mainloop()
        else:
            EventLoop.idle()
