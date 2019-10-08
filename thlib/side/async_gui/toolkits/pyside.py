#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PySide import QtCore

from ._qt import QtEngine


class PySideEngine(QtEngine):
    """ PySide support
    """
    QtCore = QtCore