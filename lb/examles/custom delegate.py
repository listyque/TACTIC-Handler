from PySide import QtGui, QtCore


class MyCustomDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        super(MyCustomDelegate, self).__init__(parent)
        self.mult = 1

    def createEditor(self, parent, option, index):
        editor = QtGui.QSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(100)

        return editor

    def setEditorData(self, spinBox, index):
        value = index.model().data(index, QtCore.Qt.EditRole)

        spinBox.setValue(value)

    def setModelData(self, spinBox, model, index):
        spinBox.interpretText()
        value = spinBox.value()

        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def sizeHint(self, option, index):
        # print "resize"
        # print(str(option.rect.width())+"  "+str(option.rect.height()))
        myFont = QtGui.QFont("Tahoma")
        myFont.setPixelSize(11)
        myFontMetrics = QtGui.QFontMetrics(myFont)
        mySize = myFontMetrics.boundingRect(0, 0, 260, 0,
                                            (QtCore.Qt.TextWordWrap | QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft),
                                            index.data(QtCore.Qt.DisplayRole))
        # print(index.data(QtCore.Qt.DisplayRole).toString())
        # print(str(mySize))
        return QtCore.QSize(mySize.width(), mySize.height() + 40)

        # mySize = myFontMetrics.boundingRect(option.rect,QtCore.Qt.TextExpandTabs|QtCore.Qt.TextWordWrap,index.data(QtCore.Qt.DisplayRole).toString(),10)
        # mySize = myFontMetrics.size(QtCore.Qt.TextExpandTabs, index.data(QtCore.Qt.DisplayRole).toString())
        # print(str(mySize.width())+"  "+str(mySize.height()+50))
        # return QtCore.QSize(mySize.width(),mySize.height()+50)
        # return index.data(QtCore.Qt.UserRole+5).toSize()*self.mult

    def paint(self, painter, option, index):
        # print painter.font().pixelSize()
        # print "paint"
        # self.sizeHint(option, index)
        # self.emmit.sizeHintChanged(index)
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        newMetr = QtGui.QFontMetrics(painter.font())
        heit = newMetr.height() + 2

        gradient = QtGui.QLinearGradient(option.rect.x() + option.rect.width() / 2, option.rect.y(),
                                         option.rect.x() + option.rect.width() / 2,
                                         option.rect.y() + option.rect.height())
        gradient.setColorAt(0.01, option.palette.base().color())
        gradient.setColorAt(0.02, option.palette.window().color())
        gradient.setColorAt(0.98, option.palette.window().color())
        gradient.setColorAt(0.99, option.palette.base().color())
        brush = QtGui.QBrush(gradient)
        painter.fillRect(option.rect, brush)

        if sys.platform == "win32":
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Multiply)
            gradient2 = QtGui.QLinearGradient(option.rect.x(), option.rect.y(), option.rect.width(),
                                              option.rect.height())
            gradient2.setColorAt(0, QtGui.QColor(255, 255, 255))
            gradient2.setColorAt(1, QtGui.QColor(200, 200, 200))
            brush2 = QtGui.QBrush(gradient2)
            painter.fillRect(option.rect, brush2)

            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Overlay)
            gradient3 = QtGui.QLinearGradient(option.rect.x(), option.rect.y(), option.rect.x() + option.rect.width(),
                                              option.rect.y() + option.rect.height())
            gradient3.setColorAt(1, QtGui.QColor(0, 0, 0, 100))
            gradient3.setColorAt(0, QtGui.QColor(255, 255, 255, 100))
            brush3 = QtGui.QBrush(gradient3)
            painter.fillRect(option.rect.x() + 2, option.rect.y() + 2, option.rect.width() / 2, heit, brush3)

            gradient4 = QtGui.QLinearGradient(option.rect.x(), option.rect.y(), option.rect.x() + option.rect.width(),
                                              option.rect.y() + option.rect.height())
            gradient4.setColorAt(0, QtGui.QColor(0, 0, 0, 100))
            gradient4.setColorAt(1, QtGui.QColor(255, 255, 255, 100))
            brush4 = QtGui.QBrush(gradient4)
            painter.fillRect(option.rect.x() + option.rect.width() / 2, option.rect.y() + option.rect.height() - heit,
                             option.rect.width() / 2, heit, brush4)

        gradient5 = QtGui.QLinearGradient(option.rect.x(), option.rect.y(), option.rect.x() + option.rect.width(),
                                          option.rect.y() + option.rect.height())
        gradient5.setColorAt(1, QtGui.QColor(100, 100, 100, 155))
        gradient5.setColorAt(0, QtGui.QColor(255, 255, 255, 155))
        brush5 = QtGui.QBrush(gradient5)
        painter.fillRect(option.rect.x() + 2, option.rect.y() + heit, option.rect.width(), 1, brush5)

        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)

        # text = index.model().data(index,QtCore.Qt.DisplayRole).toString()
        # painter.drawText( option.rect.x()+5,option.rect.y()+2,option.rect.width(),option.rect.height(),QtCore.Qt.AlignTop|QtCore.Qt.AlignLeft,text)

        textNickname = index.data(QtCore.Qt.UserRole + 3)
        one_widthNickName = painter.fontMetrics().width(textNickname)
        painter.drawText(option.rect.x() + 4, option.rect.y() + 2, option.rect.width(), option.rect.height(), (
        QtCore.Qt.TextWrapAnywhere | QtCore.Qt.TextWordWrap | QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft), textNickname)

        textFVersion = index.data(QtCore.Qt.UserRole + 6)
        if textFVersion != "":
            textFVersion = " Final: " + textFVersion
            painter.save()
            myFont = painter.font()
            myFont.setBold(True)
            painter.setFont(myFont)
            penFV = QtGui.QPen(QtGui.QColor(40, 200, 10))
            painter.setPen(penFV)
            # painter.setBrush(brushFV)
            painter.drawText(option.rect.x() + 4 + one_widthNickName, option.rect.y() + 2, option.rect.width(),
                             option.rect.height(), (
                             QtCore.Qt.TextWrapAnywhere | QtCore.Qt.TextWordWrap | QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft),
                             textFVersion)
            painter.restore();

        textSize = index.data(QtCore.Qt.UserRole + 5)
        one_widthSize = painter.fontMetrics().width(textSize)
        painter.drawText(option.rect.x() + option.rect.width() - one_widthSize - 2,
                         option.rect.y() + option.rect.height() - heit, option.rect.width(), option.rect.height(), (
                         QtCore.Qt.TextWrapAnywhere | QtCore.Qt.TextWordWrap | QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft),
                         textSize)

        textDateTyme = index.data(QtCore.Qt.UserRole + 2)
        one_width = painter.fontMetrics().width(textDateTyme)
        painter.drawText(option.rect.x() + option.rect.width() - one_width - 2, option.rect.y() + 2,
                         option.rect.width(), option.rect.height(), (
                         QtCore.Qt.TextWrapAnywhere | QtCore.Qt.TextWordWrap | QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft),
                         textDateTyme)

        textPath = index.data(QtCore.Qt.UserRole + 4)
        textPathElide = painter.fontMetrics().elidedText(textPath, QtCore.Qt.ElideLeft, option.rect.width() - 5)
        one_width = painter.fontMetrics().width(textPathElide)
        painter.drawText(option.rect.x() + option.rect.width() - one_width - 6 - one_widthSize,
                         option.rect.y() + option.rect.height() - heit, option.rect.width(), option.rect.height(), (
                         QtCore.Qt.TextWrapAnywhere | QtCore.Qt.TextWordWrap | QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft),
                         textPathElide)

        text = index.data(QtCore.Qt.DisplayRole)
        # newText = painter.fontMetrics().elidedText(text, QtCore.Qt.ElideRight, option.rect.width())
        painter.drawText(option.rect.x() + 5, option.rect.y() + heit + 5, option.rect.width(),
                         option.rect.height() - heit,
                         (QtCore.Qt.TextWordWrap | QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft), text)

        if option.state & QtGui.QStyle.State_Selected:
            colr = QtGui.QBrush(option.palette.highlight())
            ccc = QtGui.QColor(colr.color())
            ccc.setAlphaF(.2)
            colr.setColor(ccc)
            painter.fillRect(option.rect, colr)
        painter.restore();


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    tree = QtGui.QTreeView()
    model = QtGui.QStandardItemModel()
    tree.setModel(model)
    delegate = MyCustomDelegate()
    tree.setItemDelegate(delegate)
    root = model.invisibleRootItem()
    item = QtGui.QStandardItem("text")
    root.appendRow(item)
    item = QtGui.QStandardItem("text")
    root.appendRow(item)
    item = QtGui.QStandardItem("text")
    root.appendRow(item)
    tree.show()
    sys.exit(app.exec_())
