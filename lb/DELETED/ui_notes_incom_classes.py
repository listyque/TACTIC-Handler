# file ui_notes_incom_classes.py

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import lib.ui.ui_notes_incom as ui_incom

reload(ui_incom)


class Ui_incomWidget(QtGui.QWidget, ui_incom.Ui_incom):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

    # textBrowser->setHtml(noteContent.text);
    # textBrowser->setWordWrapMode(QTextOption::WrapAtWordBoundaryOrAnywhere);
    #
    # int textHeight;
    # textBrowser->document()->setTextWidth(width());
    # if (textBrowser->toPlainText().isEmpty())
    #     textHeight = 0;
    # else
    #     textHeight = textBrowser->document()->size().height() + 5;
    # textBrowser->setFixedHeight(textHeight);