#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ..engine import Engine


class WxEngine(Engine):
    """ WxPython support
    """
    def update_gui(self):
        self.main_app.Yield()
