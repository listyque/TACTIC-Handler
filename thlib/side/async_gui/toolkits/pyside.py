#!/usr/bin/env python
# -*- coding: utf-8 -*-
from thlib.side.Qt import QtCore

from ._qt import QtEngine


class PySideEngine(QtEngine):
    """ PySide support
    """
    QtCore = QtCore