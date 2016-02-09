# -*- coding: utf-8 -*-
#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
import inspect


class LineEditor(QtGui.QLineEdit):


    def __init__(self, name = None, parent = None, slot = None):
        QtGui.QLineEdit.__init__(self, parent)
        self.textChanged.connect(slot)
        self.name = name

    @staticmethod
    def paintForDelegate(delegate, painter, option, index):
        QtGui.QItemDelegate.paint(delegate, painter, option, index)

    def get(self):
        return str(self.text())

    def set(self, val):
        self.setText(QtCore.QString.fromUtf8(val))

class ColorEditor(QtGui.QComboBox):


    def _populateList(self):
        for name in QtGui.QColor.colorNames():
            self.addItem(name)
            index = self.findText(name)
            self.setItemData(index, QtGui.QColor(name), QtCore.Qt.DecorationRole)

    def __init__(self, name = None, parent = None, slot = None):
        QtGui.QComboBox.__init__(self, parent)
        self._populateList()
        self.currentIndexChanged.connect(slot)
        self.name = QtCore.QString.fromUtf8(name)

    @staticmethod
    def paintForDelegate(delegate, painter, option, index):
        QtGui.QItemDelegate.paint(delegate, painter, option, index)

    def get(self):
        qColor = QtGui.QColor(self.itemData(self.currentIndex(), QtCore.Qt.DecorationRole))        
        color = ((qColor.blue() | (qColor.green() << 8)) | (qColor.red() << 16))
        return color

    def set(self, val):
        blue = (val & 255)
        green = ((val & 65280) >> 8)
        red = ((val & 16711680) >> 16)
        color = QtGui.QColor(red, green, blue)
        index = self.findData(color, QtCore.Qt.DecorationRole)
        self.setCurrentIndex(index) 

class PropertyEditorDelegate(QtGui.QItemDelegate):


    def __init__(self, object, propName, parent = None):
        QtGui.QItemDelegate.__init__(self, parent)
        self._object = object
        self._propName = propName

    def paint(self, painter, option, index):
        self._object.paintForDelegate(self._propName, self, painter, option, index)

    def createEditor(self, parent, option, index):
        return self._object.createEditor(self._propName)

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        editor.set(value)

    def setModelData(self, editor, model, index):
        if index.column() == 0:
            model.setData(index, editor.name, QtCore.Qt.EditRole)
        else:
            model.setData(index, editor.get(), QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class PropertyEditor(QtGui.QWidget):

    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self._object = None
        self._delegates = []
        self._mainLayout = QtGui.QVBoxLayout()
        self._mainLayout.setContentsMargins(2, 2, 2, 2)
        self._mainLayout.setSpacing(2)
        self.setLayout(self._mainLayout)
        self._contents = QtGui.QTreeWidget()
        self._contents.setColumnCount(2)
        self._contents.currentItemChanged.connect(self.printCurrent)
        self._mainLayout.addWidget(self._contents)

    def printCurrent(self, curr, prev):
        print self._contents.currentIndex().row()
        print self._contents.currentIndex().column()
        print self._contents.itemDelegate(self._contents.currentIndex())._propName
        print self._contents.itemDelegate(self._contents.currentIndex())

    def object(self):
        return self._object

    def setObject(self, value):       
        self._object = value

        def isProperty(p):
            return isinstance(p, property)

        for (name, value) in inspect.getmembers(type(self._object), isProperty):
            if self._object.isEditable(name):
                item = QtGui.QTreeWidgetItem()
                item.setData(0, QtCore.Qt.EditRole, QtCore.QString.fromUtf8(self._object.getPropertyName(name)))
                item.setData(1, QtCore.Qt.EditRole, self._object.get(name))
                self._contents.addTopLevelItem(item)

                self._delegates.append(PropertyEditorDelegate(self._object, name, self._contents))
                index = self._contents.indexOfTopLevelItem(item)    
                self._contents.setItemDelegateForRow(index, self._delegates[index])

class WorkZone(object):


    def __init__(self):

        self._name = ''
        self.currentEditor = None
        self.red = 100
        self.green = 100
        self.blue = 100
        self._width = 1

    def _getColor(self):
        color = ((self.blue | (self.green << 8)) | (self.red << 16))
        return color

    def _setColor(self, color):
        self.blue = (color & 255)
        self.green = ((color & 65280) >> 8)
        self.red = ((color & 16711680) >> 16)

    color = property(_getColor, _setColor)

    def currentColorChanged(self, index):
        if self.currentEditor is not None:
            self.color = self.currentEditor.get()
        print self.color

    def currentNameChanged(self, newName):
        if self.currentEditor is not None:
            self.name = self.currentEditor.get()
        print self.name

    def createEditor(self, prop):
        if prop == 'color':
            self.currentEditor = ColorEditor('Color', None, self.currentColorChanged)
            self.currentEditor.set(self.color) 
            return self.currentEditor
        elif prop == 'name':
            self.currentEditor = LineEditor('Name', None, self.currentNameChanged) 
            self.currentEditor.set(self.name)
            return self.currentEditor
        else:
            return None

    def releaseEditor(self):
        self.currentEditor = None

    def isEditable(self, prop):
        if prop == 'color':
            return True
        elif prop == 'name':
            return True
        else:
            return False

    def set(self, prop, val):
        if prop == 'color':
            self.color = val
        elif prop == 'name':
            self.name = val

    def get(self, prop):
        if prop == 'color':
            return self.color
        elif prop == 'name':
            return self.name

    def getPropertyName(self, prop):
        if prop == 'color':
            return 'Color'
        elif prop == 'name':
            return 'Name'

    def paintForDelegate(self, prop, delegate, painter, option, index):
        if prop == 'color':
            ColorEditor.paintForDelegate(delegate, painter, option, index)
        elif prop == 'name':
            LineEditor.paintForDelegate(delegate, painter, option, index)

    def _setWidth(self, Width):
        self._width = Width

    def _getWidth(self):
        return self._width

    width = property(_getWidth, _setWidth)

    def _getName(self):
        return self._name

    def _setName(self, val):
        self._name = val

    name = property(_getName, _setName)



if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    zone = WorkZone()
    zone.color = 0
    zone.width = 1
    propertyEditor = PropertyEditor()
    propertyEditor.setObject(zone)


    propertyEditor.show()
    sys.exit(app.exec_())