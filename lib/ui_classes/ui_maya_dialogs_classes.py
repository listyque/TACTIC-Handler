# module Maya dialogs classes
# file ui_maya_dialogs_classes.py
# All maya related dialogs

import PySide.QtGui as QtGui
import lib.ui.maya.ui_maya_import as ui_import
import lib.ui.maya.ui_maya_open as ui_open
import lib.ui.maya.ui_maya_reference as ui_reference

reload(ui_import)
reload(ui_open)
reload(ui_reference)


# Importing options Dialog
class Ui_importOptionsWidget(QtGui.QDialog, ui_import.Ui_importOptions):
    def __init__(self, file_path, nested_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.setWindowTitle('Importing: {0}'.format(file_path.split('/')[-1]))


# Referencing options Dialog
class Ui_referenceOptionsWidget(QtGui.QDialog, ui_reference.Ui_referenceOptions):
    def __init__(self, file_path, nested_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.setWindowTitle('Referencing: {0}'.format(file_path.split('/')[-1]))


# Opening options Dialog
class Ui_openOptionsWidget(QtGui.QDialog, ui_open.Ui_openOptions):
    def __init__(self, file_path, nested_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.setWindowTitle('Opening: {0}'.format(file_path.split('/')[-1]))
