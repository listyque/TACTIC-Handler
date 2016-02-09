# file ui_assets_browser_classes.py
# Assets Browser

import PySide.QtGui as QtGui

import lib.ui.ui_assets_browser as ui_assets_browser

reload(ui_assets_browser)


class Ui_assetsBrowserWidget(QtGui.QWidget, ui_assets_browser.Ui_assetsBrowser):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
