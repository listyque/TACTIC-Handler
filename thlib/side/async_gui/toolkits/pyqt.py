#!/usr/bin/env python
# -*- coding: utf-8 -*-
from thlib.side.Qt import QtCore

from ._qt import QtEngine


class PyQtEngine(QtEngine):
    """ PyQt4 support
    """
    QtCore = QtCore