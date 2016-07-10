# file ui_richedit_classes.py
# Rich editor panel

import PySide.QtGui as QtGui

import lib.ui.ui_richedit as ui_richedit

reload(ui_richedit)


class Ui_richeditWidget(QtGui.QWidget, ui_richedit.Ui_richedit):
    def __init__(self, text_edit, lightweight=True, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.text_edit = text_edit

        self.controls_actions()

        self.set_lightweight(lightweight)

        self.text_edit.selectionChanged.connect(self.set_triggers)

    def set_triggers(self):
        if self.text_edit.textCursor().charFormat().fontItalic():
            self.italicButton.setChecked(True)
        else:
            self.italicButton.setChecked(False)

    def set_lightweight(self, lw):
        if lw:
            self.linkButton.hide()
            self.folderButton.hide()
            self.copyButton.hide()
            self.cutButton.hide()
            self.pictureButton.hide()
            self.bulletsListButton.hide()
            self.numbersListButton.hide()
            self.downTextButton.hide()
            self.upTextButton.hide()
            self.capsButton.hide()
            self.smallCapsButton.hide()
            self.fontcolorButton.hide()
            self.fontButton.hide()
            self.linkButton.hide()
            self.pictureButton.hide()
            self.folderButton.hide()
            self.cutButton.hide()
            self.copyButton.hide()
            self.pasteButton.hide()

    def controls_actions(self):
        self.italicButton.clicked.connect(self.toggle_italic)

    def toggle_italic(self):
        # print(self.text_edit.textCursor().selectedText())
        if self.text_edit.textCursor().charFormat().fontItalic():
            self.text_edit.setFontItalic(False)
        else:
            self.text_edit.setFontItalic(True)
