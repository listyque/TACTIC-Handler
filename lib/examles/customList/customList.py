# -*- coding: utf-8 -*-
###########################################################
##
##  Copyright(C) 2014 Digital Frontier Inc.
##
##    [免責事項]
##        本ツール、コードを使用したことによって
##        引き起こるいかなる損害も当方は一切責任を負いかねます。
##        自己責任でご使用ください。
##       
##        Terms of Use
##        The following script is provided for your conveniece and is used at your
##        own discretion and risk. Digital Frontier is not responsible for any
##        damage to your computer system or loss of data that results from the
##        access, download and use of the content on this site.
##
###########################################################

import os
import sys
from PySide import QtCore, QtGui

# スクリプトのフォルダ
CURRENT_PATH = os.path.dirname(__file__)

# オリジナルのRole
DESCRIPTION_ROLE = QtCore.Qt.UserRole
STATUS_ROLE = QtCore.Qt.UserRole + 1
THUMB_ROLE = QtCore.Qt.UserRole + 2

# Modelに入るデータ
SAMPLE_DATA = [
    {"name": "Ben", "description": "Support", "status": "OK", "color": [217, 204, 0], "thumbnail": "ben.png"},
    {
        "name": "Chris", "description": "Modeling", "status": "NOT OK", "color": [127, 197, 195],
        "thumbnail": "chris.png"
        },
    {"name": "Daniel", "description": "Manager", "status": "OK", "color": [217, 204, 166], "thumbnail": "daniel.png"},
    {
        "name": "Natalie", "description": "Sales", "status": "NOT OK", "color": [237, 111, 112],
        "thumbnail": "natalie.png"
        },
    {"name": "Mike", "description": "Animation", "status": "NOT OK", "color": [127, 197, 195], "thumbnail": "mike.png"}
]


class CustomListModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None, data=None):

        super(CustomListModel, self).__init__(parent)
        self.__items = data

    def rowCount(self, parent=QtCore.QModelIndex()):

        return len(self.__items)

    def data(self, index, role=QtCore.Qt.DisplayRole):

        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self.__items):
            return None

        if role == QtCore.Qt.DisplayRole:
            return self.__items[index.row()]["name"]

        elif role == DESCRIPTION_ROLE:
            return self.__items[index.row()]["description"]

        elif role == STATUS_ROLE:
            return self.__items[index.row()]["status"]

        elif role == THUMB_ROLE:
            return self.__items[index.row()]["thumbnail"]

        elif role == QtCore.Qt.BackgroundRole:
            color = self.__items[index.row()]["color"]
            return QtGui.QColor(color[0], color[1], color[2])

        else:
            return None

    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled


class CustomListDelegate(QtGui.QStyledItemDelegate):
    # Listの各アイテムの大きさ
    ITEM_SIZE_HINT = [300, 70]

    # 各アイテム内の表示に使う定数
    MARGIN = 20
    THUMB_AREA_WIDTH = 70
    THUMB_WIDTH = 60
    STATUS_AREA_WIDTH = 24

    # Painterが使うブラシやペンの定義
    BG_DEFAULT = QtGui.QBrush(QtGui.QColor(247, 248, 242))
    BG_SELECTED = QtGui.QBrush(QtGui.QColor(255, 255, 204))
    BORDER_DEFAULT = QtGui.QPen(QtGui.QColor(255, 255, 255), 0.5, QtCore.Qt.SolidLine)
    TEXT_BLACK_PEN = QtGui.QPen(QtGui.QColor(106, 107, 109), 0.5, QtCore.Qt.SolidLine)
    SHADOW_PEN = QtGui.QPen(QtGui.QColor(220, 220, 220, 100), 1, QtCore.Qt.SolidLine)
    FONT_H1 = QtGui.QFont("Corbel", 12, QtGui.QFont.Normal, True)
    FONT_H2 = QtGui.QFont("Corbel", 11, QtGui.QFont.Normal, True)

    def __init__(self, parent=None):

        super(CustomListDelegate, self).__init__(parent)

    # 背景描画メソッド　paintメソッド内で呼ばれている
    def drawBackground(self, painter, rect, selected, color):

        if selected:
            baseColor = self.BG_SELECTED

        else:
            baseColor = self.BG_DEFAULT

        painter.setPen(self.BORDER_DEFAULT)
        painter.setBrush(baseColor)
        painter.drawRoundedRect(rect, 1, 1)

        painter.setPen(self.SHADOW_PEN)
        painter.drawLine(rect.bottomLeft().x(), rect.bottomLeft().y() + 2, rect.bottomRight().x(),
                         rect.bottomRight().y() + 2)

        r = QtCore.QRect(rect.left(),
                         rect.top(),
                         self.THUMB_AREA_WIDTH,
                         rect.height())

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(color))
        painter.drawRoundedRect(r, 1, 1)

    # サムネイル描画メソッド　paintメソッド内で呼ばれている
    def drawThumbnail(self, painter, rect, thumbnail):

        r = QtCore.QRect(rect.left() + (self.THUMB_AREA_WIDTH - self.THUMB_WIDTH) / 2,
                         rect.top() + (self.THUMB_AREA_WIDTH - self.THUMB_WIDTH) / 2,
                         self.THUMB_WIDTH,
                         self.THUMB_WIDTH)
        thumbImage = QtGui.QPixmap(os.path.join(CURRENT_PATH, "images", thumbnail)).scaled(self.THUMB_WIDTH,
                                                                                           self.THUMB_WIDTH)
        painter.drawPixmap(r, thumbImage)

    # 名前テキスト描画メソッド　paintメソッド内で呼ばれている
    def drawName(self, painter, rect, name):

        painter.setFont(self.FONT_H1)
        painter.setPen(self.TEXT_BLACK_PEN)
        r = QtCore.QRect(rect.left() + self.THUMB_AREA_WIDTH + self.MARGIN,
                         rect.top(),
                         rect.width() - self.THUMB_AREA_WIDTH - self.STATUS_AREA_WIDTH - self.MARGIN * 3,
                         rect.height() / 2)
        painter.drawText(r, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, "Name : " + name)
        painter.setPen(self.TEXT_BLACK_PEN)
        painter.drawLine(r.bottomLeft(), r.bottomRight())

    # ディスクリプションテキスト描画メソッド　paintメソッド内で呼ばれている
    def drawDescription(self, painter, rect, description):

        painter.setFont(self.FONT_H2)
        painter.setPen(self.TEXT_BLACK_PEN)
        r = QtCore.QRect(rect.left() + self.THUMB_AREA_WIDTH + self.MARGIN,
                         rect.top() + rect.height() / 2,
                         rect.width() - self.THUMB_AREA_WIDTH - self.STATUS_AREA_WIDTH - self.MARGIN * 3,
                         rect.height() / 2)
        painter.drawText(r, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, description)

    # ステータス画像描画メソッド　paintメソッド内で呼ばれている
    def drawStatus(self, painter, rect, status):
        painter.setFont(self.FONT_H2)
        painter.setPen(self.TEXT_BLACK_PEN)
        r = QtCore.QRect(rect.right() - self.STATUS_AREA_WIDTH - self.MARGIN,
                         rect.center().y() - self.STATUS_AREA_WIDTH / 2,
                         self.STATUS_AREA_WIDTH,
                         self.STATUS_AREA_WIDTH)
        statusIcon = "notok.png"

        if status == "OK":
            statusIcon = "ok.png"

        statusImage = QtGui.QPixmap(os.path.join(CURRENT_PATH, "images", statusIcon))
        painter.drawPixmap(r, statusImage)

    # 描画メインメソッド
    def paint(self, painter, option, index):

        selected = False

        if option.state & QtGui.QStyle.State_Selected:
            selected = True

        name = index.data(QtCore.Qt.DisplayRole)
        description = index.data(DESCRIPTION_ROLE)
        status = index.data(STATUS_ROLE)
        color = index.data(QtCore.Qt.BackgroundRole)
        thumbnail = index.data(THUMB_ROLE)

        self.drawBackground(painter, option.rect, selected, color)
        self.drawThumbnail(painter, option.rect, thumbnail)
        self.drawName(painter, option.rect, name)
        self.drawDescription(painter, option.rect, description)
        self.drawStatus(painter, option.rect, status)

    # 各アイテムの大きさ
    def sizeHint(self, option, index):

        return QtCore.QSize(self.ITEM_SIZE_HINT[0], self.ITEM_SIZE_HINT[1])


# ----------------------------------------------------------------------------
## メインUI
class GUI(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(GUI, self).__init__(parent)
        self.setWindowTitle('Main Window')
        self.resize(350, 600)
        self.setMaximumSize(525, 700)
        self.initUI()

    def initUI(self):
        # リストの設定
        myListView = QtGui.QListView(self)
        myListView.setSpacing(10)
        myListView.setAutoFillBackground(False)
        url = os.path.join(CURRENT_PATH, "images", "bg.png").replace("\\", "/")
        myListView.setStyleSheet("background: url(" + url + ") center center;")
        myListView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        # modelを作る
        myListModel = CustomListModel(data=SAMPLE_DATA)

        # delegateを作る
        myListDelegate = CustomListDelegate()

        # modelとdelegateをリストにセット
        myListView.setItemDelegate(myListDelegate)
        myListView.setModel(myListModel)

        self.setCentralWidget(myListView)


def main():
    app = QtGui.QApplication(sys.argv)
    ui = GUI()
    ui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
