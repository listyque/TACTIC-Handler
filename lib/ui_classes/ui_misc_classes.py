# import PySide.QtGui as QtGui
# import PySide.QtCore as QtCore
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore

import lib.global_functions as gf
import lib.ui.misc.ui_collapsable as ui_collapsable
import lib.ui.misc.ui_horizontal_collapsable as ui_horizontal_collapsable
import lib.ui.misc.ui_debuglog as ui_debuglog


class Ui_collapsableWidget(QtGui.QWidget, ui_collapsable.Ui_collapsableWidget):
    def __init__(self, text=None, state=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.collapse_state = False
        self.__collapsedTex = ''
        self.__text = ''

        self.setText(text)
        self.setCollapsed(state)
        self.__controlsActions()

    def __controlsActions(self):
        self.collapseToolButton.toggled.connect(self.__toggleCollapseState)

    def setText(self, text):
        self.__text = text
        self.collapseToolButton.setText(self.__text)

    def setCollapsedText(self, text):
        self.__collapsedTex = text
        self.collapseToolButton.setText(self.__collapsedTex)

    def setLayout(self, layout):
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.widget.setLayout(layout)

    def setCollapsed(self, state):

        if state:
            self.collapse_state = True
            self.collapseToolButton.setArrowType(QtCore.Qt.RightArrow)
            self.widget.setHidden(True)
            self.collapseToolButton.setChecked(False)
            if self.__collapsedTex:
                self.setCollapsedText(self.__collapsedTex)
        else:
            self.collapse_state = False
            self.collapseToolButton.setArrowType(QtCore.Qt.DownArrow)
            self.widget.setHidden(False)
            self.collapseToolButton.setChecked(True)
            self.setText(self.__text)

    def __toggleCollapseState(self):
        if self.collapse_state:
            self.setCollapsed(False)
        else:
            self.setCollapsed(True)


class Ui_horizontalCollapsableWidget(QtGui.QWidget, ui_horizontal_collapsable.Ui_horizontalCollapsableWidget):
    def __init__(self, text=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.collapse_state = False
        self.__collapsedTex = ''
        self.__text = ''

        self.setText(text)
        self.__controlsActions()

    def __controlsActions(self):
        self.collapseToolButton.clicked.connect(self.__toggleCollapseState)

    def setText(self, text):
        self.__text = text
        self.collapseToolButton.setText(self.__text)

    def setCollapsedText(self, text):
        self.__collapsedTex = text
        self.collapseToolButton.setText(self.__collapsedTex)

    def setLayout(self, layout):

        self.widget.setLayout(layout)

    def setCollapsed(self, state):

        if state:
            self.collapse_state = True
            self.collapseToolButton.setIcon(gf.get_icon('angle-left'))
            self.widget.setHidden(True)
            if self.__collapsedTex:
                self.setCollapsedText(self.__collapsedTex)
        else:
            self.collapse_state = False
            self.collapseToolButton.setIcon(gf.get_icon('angle-right'))
            self.widget.setHidden(False)
            self.setText(self.__text)

    def isCollapsed(self):
        if self.collapse_state:
            return True
        else:
            return False

    def __toggleCollapseState(self):

        if self.collapse_state:
            self.setCollapsed(False)
        else:
            self.setCollapsed(True)


class Ui_namingEditorWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        print('Now you can edit your names :)')


class Ui_screenShotMakerDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.setWindowTitle('Making Screenshot')

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # self.setWindowOpacity(0.5)

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # self.setSizeGripEnabled(True)

        mouse_pos = Qt4Gui.QCursor.pos()
        self.setGeometry(mouse_pos.x()-16, mouse_pos.y()-16, 32, 32)

        # self.resize(150, 150)
        # self.move()

        self.label_lay = QtGui.QVBoxLayout()
        self.setLayout(self.label_lay)
        self.screenshot_pixmap = None

        self.label_lay.setContentsMargins(0, 0, 0, 0)
        self.label_lay.setSpacing(0)

        self.bg_wd = QtGui.QLabel()
        self.bg_wd.setStyleSheet('QLabel {padding: 0px;border: 2px dashed grey; background-color: rgba(0,0,0,25);}')
        self.label_lay.addWidget(self.bg_wd)
        self.bg_wd.setMouseTracking(True)

        self.button_lay = QtGui.QHBoxLayout(self.bg_wd)
        self.button_lay.setContentsMargins(0, 0, 0, 0)
        self.button_lay.setSpacing(0)

        self.pb = QtGui.QToolButton()
        self.pb.setText('Take Screenshot')
        self.pb.setAutoRaise(True)
        # self.button_lay.addWidget(self.pb)

        self.pb.clicked.connect(self.ru)

        self.__dragging = False
        self.__resizing = False
        self.__offset_pos = None

        self.single_click_timer = QtCore.QTimer()
        self.single_click_timer.setInterval(1000)
        self.single_click_timer.timeout.connect(self.ts)

        self.create_ui()

    def create_ui(self):

        self.setIcon()
        self.setMouseTracking(True)
        self.installEventFilter(self)

    def setIcon(self):
        icon = Qt4Gui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

    def ts(self):
        self.single_click_timer.stop()
        width = self.geometry().width()
        height = self.geometry().height()
        top = self.geometry().top()
        left = self.geometry().left()
        self.screenshot_pixmap = Qt4Gui.QPixmap.grabWindow(QtGui.QApplication.desktop().winId(), left, top, width, height)
        self.close()

    def ru(self):
        self.hide()
        self.single_click_timer.start()

    def dragging(self, pos):
        result_pos = pos + self.__offset_pos
        self.move(result_pos)

    def resizing(self, pos):
        result_pos = pos - self.__offset_pos
        self.resize(result_pos.toTuple()[0], result_pos.toTuple()[1])

    def mouseMoveEvent(self, event):
        # print event.globalPos()
        global_pos = event.globalPos()
        self.move(global_pos.x()-16, global_pos.y()-16)

        # if self.underMouse() and not self.__resizing:
        #     if self.__dragging and self.__offset_pos:
        #         self.dragging(event.globalPos())
        # else:
        #     if self.__resizing and self.__offset_pos:
        #         self.resizing(event.globalPos())

        event.accept()

    # def mouseReleaseEvent(self, event):
    #     self.__dragging = False
    #     self.__resizing = False
    #     event.accept()
    #
    # def mousePressEvent(self, event):
    #     widget_pos = self.pos()
    #     offset_pos = widget_pos - event.globalPos()
    #     self.__offset_pos = offset_pos
    #
    #     if self.underMouse():
    #         self.__dragging = True
    #     else:
    #         self.move(event.globalPos())
    #         self.resize(0, 0)
    #         self.__offset_pos = event.globalPos()
    #         self.__resizing = True
    #
    #     event.accept()


class Ui_debugLogWidget(QtGui.QDialog, ui_debuglog.Ui_DebugLog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.create_ui()

    def create_ui(self):

        self.debugLogTextEdit.setText('')

    def add_info(self, info_text):

        self.debugLogTextEdit.insertHtml(info_text)

    def add_warning(self, warning_text):

        self.debugLogTextEdit.insertHtml(warning_text)
