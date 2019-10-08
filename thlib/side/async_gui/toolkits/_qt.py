#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ..engine import Engine


class QtEngine(Engine):
    QtCore = None

    def update_gui(self):
        if self.main_app is None:
            self.main_app = self.QtCore.QCoreApplication.instance()
        self.main_app.processEvents(
            self.QtCore.QEventLoop.AllEvents,
            int(self.pool_timeout * 1000)
        )

