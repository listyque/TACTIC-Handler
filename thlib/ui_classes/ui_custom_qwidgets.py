# -*- coding: utf-8 -*-
# Customize Default Qt Widgets

# Copyright (c) 2019, Krivospitskiy Alexey, <listy@live.ru>, https://github.com/listyque/TACTIC-Handler
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0


__all__ = ['Ui_extendedTabBarWidget', 'Ui_extendedTreeWidget', 'SquareLabel', 'MenuWithLayout', 'Ui_collapsableWidget',
           'Ui_horizontalCollapsableWidget', 'Ui_namingEditorWidget', 'Ui_serverPresetsEditorWidget',
           'Ui_previewsEditorDialog', 'Ui_screenShotMakerDialog', 'Ui_debugLogWidget', 'SuggestedLineEdit',
           'StyledComboBox', 'Ui_replyWidget', 'Ui_messagesWidget']


import os
import datetime
import codecs
import thlib.side.six as six
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.global_functions as gf
import thlib.tactic_classes as tc
from thlib.environment import env_inst, env_server, env_mode, dl, cfg_controls
import thlib.ui.misc.ui_debuglog as ui_debuglog
import thlib.ui.misc.ui_messages as ui_messages
import thlib.ui_classes.ui_richedit_classes


class FadeWidget(QtGui.QLabel):

    def __init__(self, *args):

        super(self.__class__, self).__init__(*args)

        self.__painter = Qt4Gui.QPainter()

        self.ppval = 0.0

        self.__fade = 0.0
        self.__fade_color = Qt4Gui.QColor(QtCore.Qt.black)

    def paintEvent(self, event):

        super(self.__class__, self).paintEvent(event)

        self.__fade_color.setAlphaF(self.__fade)

        self.__painter.begin(self)
        self.__painter.setRenderHint(Qt4Gui.QPainter.Antialiasing, False)
        self.__painter.setRenderHint(Qt4Gui.QPainter.HighQualityAntialiasing, False)
        self.__painter.fillRect(self.rect(), self.__fade_color)
        self.__painter.end()

    def setFade(self, fade):
        self.__fade = fade

        if self.__fade > 0.0:
            self.repaint()

    def readPP(self):
        return self.ppval

    def setPP(self, val):
        self.ppval = val

        self.setFade(self.ppval)

    Fade = QtCore.Property(float, readPP, setPP, notify=setFade)


class Ui_projectIconWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui_raw()

        self.project = None

        self.create_ui()

    def create_ui_raw(self):
        self.setObjectName('Ui_projectIconWidget')
        self.setMaximumSize(60, 48)
        self.setMinimumSize(60, 48)
        self.setContentsMargins(0, 0, 0, 0)

        self.horizontal_layout = QtGui.QHBoxLayout(self)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.horizontal_layout.setSpacing(0)

        self.previewLabel = QtGui.QLabel(self)
        self.previewLabel.setMinimumSize(QtCore.QSize(60, 48))
        self.previewLabel.setMaximumSize(QtCore.QSize(60, 48))
        self.previewLabel.setStyleSheet('QLabel {background: transparent; border: 0px; border-radius: 0px;padding: 0px 0px;}')
        self.previewLabel.setTextFormat(QtCore.Qt.RichText)
        self.previewLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.previewLabel.setSizePolicy(sizePolicy)

        self.horizontal_layout.addWidget(self.previewLabel)

    def create_ui(self):

        self.fill_info()
        self.setCursor(Qt4Gui.QCursor(QtCore.Qt.PointingHandCursor))

    def set_project(self, project):

        self.project = project

    def get_snapshot(self, process='publish'):

        snapshot_process = self.project.process.get(process)
        if snapshot_process:
            context = list(snapshot_process.contexts.values())[0]
            if context.versionless:
                return list(context.versionless.values())[0]
            else:
                return list(context.versions.values())[0]

    def fill_info(self):
        if self.project:

            if self.project.process:

                if gf.get_value_from_config(cfg_controls.get_checkin(), 'getPreviewsThroughHttpCheckbox') == 1:
                    self.set_web_preview()
                else:
                    self.set_preview()
            else:
                self.previewLabel.setText(u'<span style=" font-size:9pt; font-weight:600; color:{0};">{1}</span>'.format(
                        'rgb(128,128,128)', gf.gen_acronym(self.project.get_title())))
        else:
            self.previewLabel.setText(u'<span style=" font-size:9pt; font-weight:600; color:{0};">{1}</span>'.format(
                'rgb(128,128,128)', ''))

    def set_preview(self):

        snapshots = self.get_snapshot('icon')
        if not snapshots:
            snapshots = self.get_snapshot('publish')

        if snapshots:
            preview_files_objects = snapshots.get_files_objects(group_by='type').get('icon')
            if preview_files_objects:
                icon_previw = preview_files_objects[0].get_icon_preview()
                if icon_previw:
                    pixmap = self.get_preview_pixmap(icon_previw.get_full_abs_path())
                    if pixmap:
                        self.previewLabel.setPixmap(pixmap)

    def set_web_preview(self):

        snapshots = self.get_snapshot('icon')
        if not snapshots:
            snapshots = self.get_snapshot('publish')

        if snapshots:
            preview_files_objects = snapshots.get_files_objects(group_by='type').get('icon')
            if preview_files_objects:
                icon_previw = preview_files_objects[0].get_icon_preview()
                if icon_previw:
                    if icon_previw.is_exists():
                        if icon_previw.get_file_size() == icon_previw.get_file_size(True):
                            self.set_preview()
                        else:
                            self.download_and_set_preview_file(icon_previw)
                    else:
                        self.download_and_set_preview_file(icon_previw)

    def download_and_set_preview_file(self, file_object):
        if not file_object.is_downloaded():
            if file_object.get_unique_id() not in list(env_inst.ui_repo_sync_queue.queue_dict.keys()):
                repo_sync_item = env_inst.ui_repo_sync_queue.schedule_file_object(file_object)
                repo_sync_item.downloaded.connect(self.set_preview_pixmap)
                repo_sync_item.download()

    def set_preview_pixmap(self, file_object):
        pixmap = self.get_preview_pixmap(file_object.get_full_abs_path())
        if pixmap:
            self.previewLabel.setPixmap(pixmap)

    def get_preview_pixmap(self, image_path):
        pixmap = Qt4Gui.QPixmap(image_path)
        if not pixmap.isNull():

            pix_width = 48
            pix_height = 48

            pixmap = pixmap.scaledToHeight(pix_width, QtCore.Qt.SmoothTransformation)

            painter = Qt4Gui.QPainter()
            pixmap_mask = Qt4Gui.QPixmap(pix_width, pix_height)
            pixmap_mask.fill(QtCore.Qt.transparent)
            painter.begin(pixmap_mask)
            painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
            painter.setBrush(Qt4Gui.QBrush(Qt4Gui.QColor(0, 0, 0, 255)))
            painter.drawRoundedRect(QtCore.QRect(4, 4, pix_width-8, pix_height-8), 4, 4)
            painter.end()

            rounded_pixmap = Qt4Gui.QPixmap(pixmap.size())
            rounded_pixmap.fill(QtCore.Qt.transparent)
            painter.begin(rounded_pixmap)
            painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
            painter.drawPixmap(QtCore.QRect((pixmap.width() - pix_width) / 2, 0, pix_width, pix_width), pixmap_mask)
            painter.setCompositionMode(Qt4Gui.QPainter.CompositionMode_SourceIn)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            return rounded_pixmap


class Ui_userIconWidget(QtGui.QWidget):
    def __init__(self, login=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui_raw()

        self.login = None
        self.set_login(login)

        self.create_ui()

    def create_ui_raw(self):
        self.setObjectName('Ui_userIconWidget')
        self.setMaximumSize(60, 36)
        self.setMinimumSize(60, 36)
        self.setContentsMargins(0, 0, 0, 0)

        self.horizontal_layout = QtGui.QHBoxLayout(self)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.horizontal_layout.setSpacing(0)

        self.previewLabel = QtGui.QLabel(self)
        self.previewLabel.setMinimumSize(QtCore.QSize(32, 32))
        self.previewLabel.setMaximumSize(QtCore.QSize(32, 32))
        self.previewLabel.setStyleSheet('QLabel {background: rgba(175, 175, 175, 64); border: 0px; border-radius: 16px;padding: 0px 0px;}')
        self.previewLabel.setPixmap(gf.get_icon('account', icons_set='mdi').pixmap(20, 20))
        self.previewLabel.setTextFormat(QtCore.Qt.RichText)
        self.previewLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.previewLabel.setSizePolicy(sizePolicy)

        self.horizontal_layout.addWidget(self.previewLabel)

    def set_login(self, login):
        self.login = login

        if self.login:
            self.fill_info()

    def create_ui(self):
        self.setCursor(Qt4Gui.QCursor(QtCore.Qt.PointingHandCursor))

    def fill_info(self):

        self.previewLabel.setText(u'<span style=" font-size:9pt; font-weight:600; color:{0};">{1}</span>'.format(
            'rgb(240, 240, 240)', gf.gen_acronym(self.login.get_display_name())))

        self.previewLabel.setStyleSheet(
            'QLabel {{background: {0}; border: 0px; border-radius: 16px;padding: 0px 0px;}}'.format(gf.gen_color(self.login.get_value('login'))))


class Ui_sideBarWidget(QtGui.QWidget):
    clicked = QtCore.Signal()
    hidden = QtCore.Signal()

    def __init__(self, underlayer_widget=None,  parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.underlayer_widget = underlayer_widget

        self.overlay_layout_widget = None

        self.create_ui()

    def overlay_clicked_emit(self):

        self.clicked.emit()

    def overlay_hidden_emit(self):

        self.hidden.emit()

    def create_ui(self):

        self.create_main_layout()
        self.create_dimming_widget()
        self.create_overlay_layout()

    def create_main_layout(self):

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.setSizePolicy(sizePolicy)

        self.main_layout = QtGui.QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)

    def create_dimming_widget(self):
        self.dimmer_widget_dark = QtGui.QLabel()
        self.dimmer_widget = FadeWidget()

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.dimmer_widget.setSizePolicy(sizePolicy)

        self.dimmer_widget_dark.setSizePolicy(sizePolicy)
        self.dimmer_widget_dark.setStyleSheet("QLabel {background-color: rgb(0, 0, 0);}")
        effect = QtGui.QGraphicsOpacityEffect(self.dimmer_widget_dark)
        self.dimmer_widget_dark.setGraphicsEffect(effect)
        effect.setOpacity(0.5)
        self.dimmer_widget_dark.setHidden(True)

        self.dimmer_anm_close = QtCore.QPropertyAnimation(self.dimmer_widget, b'Fade', self.dimmer_widget)
        self.dimmer_anm_close.setDuration(100)
        self.dimmer_anm_close.setStartValue(0.5)
        self.dimmer_anm_close.setEndValue(0.0)
        self.dimmer_anm_close.setEasingCurve(QtCore.QEasingCurve.InSine)
        self.dimmer_anm_open = QtCore.QPropertyAnimation(self.dimmer_widget, b'Fade', self.dimmer_widget)
        self.dimmer_anm_open.setDuration(100)
        self.dimmer_anm_open.setStartValue(0.0)
        self.dimmer_anm_open.setEndValue(0.5)
        self.dimmer_anm_open.setEasingCurve(QtCore.QEasingCurve.OutSine)

        self.dimmer_anm_close.valueChanged.connect(self.hide_overlay_at_animation_end)

        self.main_layout.addWidget(self.dimmer_widget)
        self.main_layout.addWidget(self.dimmer_widget_dark)

    def add_sidebar_widget(self, sidebar_widget):
        self.sidebar = sidebar_widget
        self.sidebar_proxy = QtGui.QLabel()

        self.sidebar_proxy.setParent(self.dimmer_widget)
        self.sidebar.setParent(self.dimmer_widget)

        self.animation_close = QtCore.QPropertyAnimation(self.sidebar_proxy, b'pos', self)
        self.animation_open = QtCore.QPropertyAnimation(self.sidebar_proxy, b'pos', self)

        self.animation_close.setDuration(100)

        self.animation_close.setStartValue(QtCore.QPoint(0, 0))
        self.animation_close.setEndValue(QtCore.QPoint(-250, 0))
        self.animation_close.setEasingCurve(QtCore.QEasingCurve.InExpo)
        self.animation_open.setDuration(200)
        self.animation_open.setStartValue(QtCore.QPoint(-250, 0))
        self.animation_open.setEndValue(QtCore.QPoint(0, 0))
        self.animation_open.setEasingCurve(QtCore.QEasingCurve.OutExpo)

        self.animation_close.valueChanged.connect(self.hide_overlay_at_animation_end)
        self.animation_open.valueChanged.connect(self.enable_updates_at_animation_end)

        # effect = QtGui.QGraphicsDropShadowEffect(self)
        # effect.setOffset(4, 0)
        # effect.setColor(Qt4Gui.QColor(0, 0, 0, 255))
        # effect.setBlurRadius(64)
        # self.sidebar_proxy.setGraphicsEffect(effect)

        self.overlay_layout.addWidget(self.sidebar_proxy)
        self.overlay_layout.addWidget(self.sidebar)

    def create_overlay_layout(self):

        self.overlay_layout_widget = QtGui.QToolButton(self)
        self.overlay_layout_widget.clicked.connect(self.overlay_clicked_emit)
        self.overlay_layout_widget.setStyleSheet("QToolButton { border: 0px; background-color: rgba(0, 0, 0, 0);}")
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.overlay_layout_widget.setSizePolicy(sizePolicy)

        self.overlay_layout = QtGui.QVBoxLayout(self.overlay_layout_widget)
        self.overlay_layout.setSpacing(0)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)

        self.overlay_layout_widget.setLayout(self.overlay_layout)
        self.overlay_layout_widget.setHidden(True)

    def show_overlay(self):
        self.overlay_layout_widget.show()
        self.overlay_layout_widget.raise_()

        self.sidebar.hide()
        self.sidebar_proxy.setPixmap(Qt4Gui.QPixmap.grabWidget(self.sidebar, 0, 0, 250, self.height()))
        self.sidebar.setUpdatesEnabled(False)
        self.sidebar_proxy.show()

        self.dimmer_widget.setPixmap(Qt4Gui.QPixmap.grabWidget(self.underlayer_widget))
        self.underlayer_widget.setUpdatesEnabled(False)
        self.dimmer_widget.show()

        self.dimmer_anm_open.start()
        self.animation_open.start()

    def hide_overlay(self):
        self.dimmer_widget_dark.hide()

        self.underlayer_widget.setUpdatesEnabled(True)
        self.dimmer_widget.setPixmap(Qt4Gui.QPixmap.grabWidget(self.underlayer_widget))
        self.underlayer_widget.setUpdatesEnabled(False)
        self.dimmer_widget.show()

        self.sidebar.setUpdatesEnabled(True)
        self.sidebar.hide()
        self.sidebar_proxy.setPixmap(Qt4Gui.QPixmap.grabWidget(self.sidebar, 0, 0, 250, self.height()))
        self.sidebar_proxy.show()
        self.sidebar.setUpdatesEnabled(False)

        self.dimmer_anm_close.start()
        self.animation_close.start()

    def enable_updates_at_animation_end(self, val):
        if val == QtCore.QPoint(0, 0):
            self.underlayer_widget.setUpdatesEnabled(True)
            self.dimmer_widget.hide()

            self.sidebar.setUpdatesEnabled(True)
            self.sidebar.show()
            self.sidebar_proxy.hide()

            # effect = QtGui.QGraphicsDropShadowEffect(self)
            # effect.setOffset(4, 0)
            # effect.setColor(Qt4Gui.QColor(0, 0, 0, 128))
            # effect.setBlurRadius(16)
            # self.sidebar.setGraphicsEffect(effect)

            self.dimmer_widget.hide()
            self.dimmer_widget_dark.show()

    def hide_overlay_at_animation_end(self, val):
        if val == QtCore.QPoint(-250, 0):
            self.overlay_layout_widget.lower()
            self.overlay_layout_widget.hide()

            self.dimmer_widget.hide()
            self.underlayer_widget.setUpdatesEnabled(True)

            self.sidebar_proxy.hide()
            self.sidebar.setUpdatesEnabled(True)

            self.overlay_hidden_emit()

    def open_sidebar(self):
        self.show_overlay()

    def close_sidebar(self):
        self.hide_overlay()

    def resizeEvent(self, event):
        if self.overlay_layout_widget:
            self.overlay_layout_widget.resize(self.size())
        event.accept()


class Ui_extendedTabBarWidget(QtGui.QTabWidget):
    middle_mouse_pressed = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.corner_offset = 0

    def customize_ui(self, padding=0):
        self.setStyleSheet("""
QTabWidget::pane {
    border: 0px;
    top: 6px;
}
QTabWidget::tab-bar {
    alignment: left;
    left: 0px;
    top: 4px;
}
#%(obj_name)s > QTabBar::tab {
    background: rgb(80, 80, 80);

    border: 0px;
    border-top-right-radius: 3px;
    border-top-left-radius: 3px;
    border-bottom-right-radius: 3px;
    border-bottom-left-radius: 3px;
    padding-left: 0px;
    padding-right: 0px;
    padding-top: 0px;
    padding-bottom: 6px;
    margin-left: 0px;
    margin-right: 3px;

}
#%(obj_name)s > QTabBar::tab:selected{
    background: rgb(120, 120, 120);
}
#%(obj_name)s > QTabBar::tab:hover {
    background: rgb(140, 140, 140);
}""" % {'obj_name': self.objectName(), 'padding': padding})

    def add_left_corner_widget(self, widget):
        self.setCornerWidget(widget, QtCore.Qt.TopLeftCorner)

    def add_tab(self, widget, label=''):
        if isinstance(label, six.string_types):
            self.addTab(widget, label)
        else:
            idx = self.addTab(widget, '')
            self.tabBar().setTabButton(idx, QtGui.QTabBar.RightSide, label)

    def set_corner_offset(self, offset_int):
        self.corner_offset = offset_int

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:
            pos = event.pos()
            # This offset is because hamburger button on the left
            tab_pos = self.tabBar().tabAt(QtCore.QPoint(pos.x() - self.corner_offset, pos.y()))
            if tab_pos != -1:
                self.middle_mouse_pressed.emit(tab_pos)

        event.accept()


class Ui_extendedLeftTabBarWidget(QtGui.QTabWidget):
    middle_mouse_pressed = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.corner_offset = 0

        self.setAutoFillBackground(True)
        self.setTabPosition(QtGui.QTabWidget.West)

    def customize_ui(self, padding=0):
        self.setStyleSheet("""

#%(obj_name)s::left-corner {
    width: 60px;
    height: 32px;
}

#%(obj_name)s::pane {
    border: 0px;
    top: 0px;
    background-color: rgb(64, 64, 64);
}
#%(obj_name)s::tab-bar {
    alignment: left;
    left: 0px;
    top: 0px;
}
#%(obj_name)s > QTabBar::tab {
    background: rgb(64, 64, 64);

    border: 0px transparent;
    border-top-right-radius: 0px;
    border-top-left-radius: 0px;
    border-bottom-right-radius: 0px;
    border-bottom-left-radius: 0px;
    
    padding-left: 0px;
    padding-right: 0px;
    padding-top: 4px;
    padding-bottom: 0px;
    
    margin-left: 0px;
    margin-right: 0px;
    margin-top: 0px;
    margin-bottom: 0px;
}
#%(obj_name)s > QTabBar::tab:selected{
    background: rgb(57, 68, 81);
}
#%(obj_name)s > QTabBar::tab:hover {
    background: rgb(64, 69, 74);
}
#%(obj_name)s > QTabBar::tab:!selected {
    margin-top: 0px;
}""" % {'obj_name': self.objectName(), 'padding': padding})

    def add_left_corner_widget(self, widget):
        self.setCornerWidget(widget, QtCore.Qt.TopLeftCorner)

    def add_tab(self, widget, label=''):
        if isinstance(label, six.string_types):
            self.addTab(widget, label)
        else:
            idx = self.addTab(widget, '')
            self.tabBar().setTabButton(idx, QtGui.QTabBar.RightSide, label)

    def set_corner_offset(self, offset_int):
        self.corner_offset = offset_int

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:
            pos = event.pos()
            # This offset is because hamburger button on the left
            tab_pos = self.tabBar().tabAt(QtCore.QPoint(pos.x() - self.corner_offset, pos.y()))
            if tab_pos != -1:
                self.middle_mouse_pressed.emit(tab_pos)

        event.accept()

    def paintEvent(self, event):
        super(self.__class__, self).paintEvent(event)
        painter = Qt4Gui.QPainter()
        painter.begin(self)
        rect = self.rect()
        painter.fillRect(rect.x(), rect.y(), self.tabBar().minimumSizeHint().width(), rect.height(), Qt4Gui.QColor(64, 64, 64))


class Ui_tabLabel(QtGui.QFrame):
    def __init__(self, label_title='', stype=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.label_title = label_title
        self.stype = stype

        self.create_ui()

        self.customize_ui()

    def create_ui(self):
        self.setContentsMargins(0, -2, 0, 0)
        lay = QtGui.QVBoxLayout()
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lay)

        self.tab_label = QtGui.QLabel()
        lay.addWidget(self.tab_label)
        self.tab_label.setText(self.label_title)

        font = Qt4Gui.QFont()
        font.setPointSize(10)
        font.setWeight(65)
        font.setBold(False)
        self.tab_label.setFont(font)
        self.tab_label.setTextFormat(QtCore.Qt.RichText)
        self.tab_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.tab_label.setMargin(6)
        self.tab_label.setContentsMargins(0, 0, 0, 0)

    def customize_ui(self):
        tab_color = None
        if self.stype:
            tab_color = self.stype.info['color']
        if tab_color:

            tab_color_rgb = gf.hex_to_rgb(tab_color, alpha=128)
            self.tab_label.setStyleSheet('QLabel {border: 0px;}')

            self.setStyleSheet('QFrame {background-color: transparent;' +
                              'border-bottom: 2px solid {0};'.format(tab_color_rgb) + '}')

    def setText(self, text):
        self.tab_label.setText(text)


class Ui_extendedTreeWidget(QtGui.QTreeWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.customize_ui()

    def customize_ui(self):
        self.setStyleSheet(gf.get_qtreeview_style())

        self.scroll_animation = QtCore.QPropertyAnimation(self.verticalScrollBar(), b'value', self)
        self.scroll_animation.setDuration(400)
        self.scroll_animation.setStartValue(0)
        self.scroll_animation.setEndValue(0)
        self.scroll_animation.setEasingCurve(QtCore.QEasingCurve.OutExpo)

    def wheelEvent(self, event):
        if event.orientation() == QtCore.Qt.Vertical:
            event.ignore()
            value = self.verticalScrollBar().value()
            self.scroll_animation.setStartValue(value)
            delta_value = self.verticalScrollBar().value() - event.delta()*2
            self.scroll_animation.setEndValue(delta_value)

            if self.scroll_animation.state() == QtCore.QAbstractAnimation.State.Stopped:
                self.scroll_animation.start()


class SquareLabel(QtGui.QLabel):
    clicked = QtCore.Signal()

    def __init__(self, menu, action, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.menu = menu
        self.action = action

    def mousePressEvent(self, event):
        self.clicked.emit()
        event.accept()

    def enterEvent(self, event):
        self.setAutoFillBackground(False)
        self.menu.setActiveAction(self.action)

    def leaveEvent(self, event):
        self.setAutoFillBackground(True)


class MenuWithLayout(QtGui.QMenu):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        # self.set_styling()
        self.icon_pixmap = None
        self.edit_label = None

        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 1, 1, 1)
        self.layout.setColumnStretch(0, 1)

        self.setLayout(self.layout)

    def set_custom_icon(self, icon_pixmap):
        self.icon_pixmap = icon_pixmap

    # def set_styling(self):
    #
    #     self.setStyleSheet("QMenu::separator { height: 2px;}")

    def addAction(self, action, edit_label=False):

        w = QtGui.QWidget()
        l = QtGui.QGridLayout(w)

        self.edit_label = SquareLabel(menu=self, action=action)
        self.edit_label.setAlignment(QtCore.Qt.AlignCenter)
        if self.icon_pixmap:
            self.edit_label.setPixmap(self.icon_pixmap)
        else:
            self.edit_label.setPixmap(gf.get_icon('square-edit-outline', icons_set='mdi').pixmap(18, 18))
        w.setMinimumSize(22, 13)

        self.edit_label.setAutoFillBackground(True)

        self.edit_label.setBackgroundRole(Qt4Gui.QPalette.Background)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        l.setSpacing(0)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(self.edit_label)

        self.layout.addWidget(w, len(self.actions()), 1, 1, 1)

        spacerItem = QtGui.QSpacerItem(self.sizeHint().width()-5, 2, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        self.layout.addItem(spacerItem, len(self.actions()), 0, 1, 1)

        self.layout.setRowStretch(len(self.actions()), 1)

        super(MenuWithLayout, self).addAction(action)

        w.setFixedHeight(self.actionGeometry(action).height())

        if edit_label:
            return self.edit_label
        else:
            self.edit_label.setHidden(True)
            return action

    def addSeparator(self):
        spacerItem = QtGui.QSpacerItem(0, 2, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.layout.addItem(spacerItem, len(self.actions()), 0, 1, 2)

        return super(MenuWithLayout, self).addSeparator()


class Ui_collapsableWidget(QtGui.QWidget):
    collapsed = QtCore.Signal(object)

    def __init__(self, text=None, state=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.collapse_state = False
        self.__collapsedTex = ''
        self.__text = ''

        self.create_ui()

        self.setText(text)
        self.setCollapsed(state)

        self.controls_actions()

        self.custom_style_sheet()

    def create_ui(self):

        self.setObjectName('collapsable_widget')
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.collapseToolButton = QtGui.QToolButton(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.collapseToolButton.sizePolicy().hasHeightForWidth())
        self.collapseToolButton.setSizePolicy(sizePolicy)
        self.collapseToolButton.setMinimumSize(QtCore.QSize(0, 25))
        self.collapseToolButton.setCheckable(True)
        self.collapseToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.collapseToolButton.setAutoRaise(True)
        self.collapseToolButton.setObjectName("collapseToolButton")
        self.verticalLayout.addWidget(self.collapseToolButton)
        self.widget = QtGui.QWidget(self)
        self.widget.setObjectName("widget")
        self.verticalLayout.addWidget(self.widget)
        self.verticalLayout.setStretch(1, 1)

        self.collapsed_layout = None

        self.overlay_layout = QtGui.QHBoxLayout(self.collapseToolButton)
        self.overlay_layout.setContentsMargins(150, 0, 4, 0)
        spacer = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        self.overlay_layout.addItem(spacer)

        self.collapseToolButton.setMaximumHeight(25)
        self.collapseToolButton.setMinimumHeight(25)

    def add_overlay_widget(self, widget):
        self.overlay_layout.addWidget(widget)

    def add_widget(self, widget, *args):
        if not self.collapsed_layout:
            self.setLayout(QtGui.QGridLayout())
        else:
            self.collapsed_layout.addWidget(widget, *args)

    def custom_style_sheet(self):
        self.collapseToolButton.setStyleSheet(
            'QToolButton {'
            'margin-left: 1px;'
            'margin-right: 1px;'
            'background: rgba(96, 96, 96, 32);'
            'border: 0px; border-radius: 3px; padding: 0px 0px;'
            'border-left: 1px solid rgb(128, 128, 128); border-right: 1px solid rgb(128, 128, 128);}'
            'QToolButton:pressed {'
            'background: rgba(128, 128, 128, 32)}'
        )

    def controls_actions(self):
        self.collapseToolButton.toggled.connect(self.__toggleCollapseState)

    def is_collapsed(self):
        return self.collapse_state

    def setText(self, text):
        self.__text = text
        self.collapseToolButton.setText(self.__text)

    def setCollapsedText(self, text):
        self.__collapsedTex = text
        self.collapseToolButton.setText(self.__collapsedTex)

    def setLayout(self, layout=None):
        self.collapsed_layout = layout

        self.collapsed_layout.setContentsMargins(0, 0, 0, 0)
        self.collapsed_layout.setSpacing(0)

        self.widget.setLayout(self.collapsed_layout)

    def setCollapsed(self, state):
        if state:
            self.collapse_state = True
            self.collapseToolButton.setIcon(gf.get_icon('angle-right'))
            self.widget.setHidden(True)
            self.collapseToolButton.setChecked(False)
            if self.__collapsedTex:
                self.setCollapsedText(self.__collapsedTex)
        else:
            self.collapse_state = False
            self.collapseToolButton.setIcon(gf.get_icon('angle-down'))
            self.widget.setHidden(False)
            self.collapseToolButton.setChecked(True)
            self.setText(self.__text)

    def setCollapseState(self, state):
        if state:
            self.collapseToolButton.toggle()

    def __toggleCollapseState(self):
        if self.collapse_state:
            self.setCollapsed(False)
            self.collapsed.emit(False)
        else:
            self.setCollapsed(True)
            self.collapsed.emit(True)

    def isCollapsed(self):
        if self.collapse_state:
            return True
        else:
            return False


class Ui_horizontalCollapsableWidget(QtGui.QWidget):
    def __init__(self, text=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui()
        self.customize_ui()

        self.collapse_state = False
        self.__direction = 'left'
        self.__collapsedTex = ''
        self.__text = ''

        self.setText(text)
        self.__controlsActions()

    def create_ui(self):
        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.widget = QtGui.QWidget(self)
        self.widget.setObjectName("widget")
        self.horizontalLayout.addWidget(self.widget)
        self.collapseToolButton = QtGui.QToolButton(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.collapseToolButton.sizePolicy().hasHeightForWidth())
        self.collapseToolButton.setSizePolicy(sizePolicy)
        self.collapseToolButton.setMaximumWidth(10)
        self.collapseToolButton.setMinimumWidth(10)
        self.collapseToolButton.setAutoRaise(True)
        self.collapseToolButton.setObjectName("collapseToolButton")
        self.horizontalLayout.addWidget(self.collapseToolButton)
        self.horizontalLayout.setStretch(1, 1)

        self.setMinimumSize(10, 30)

        self.setCursor(Qt4Gui.QCursor(QtCore.Qt.PointingHandCursor))

    def customize_ui(self):

        self.collapseToolButton.setStyleSheet("""
                QToolButton {
                    border: 0px;
                    border-radius: 5px;
                    background: transparent;
                    margin: 0px;
                }
                QToolButton::menu-indicator {
                background: transparent;
                }
                QToolButton:pressed {
                    background-color: rgb(107, 107, 107);
                }
                /*
                QToolButton:hover {
                    background-color: rgb(107, 107, 107);
                }
                */
                """)

        effect = QtGui.QGraphicsDropShadowEffect(self)
        effect.setOffset(0, 0)
        effect.setColor(Qt4Gui.QColor(0, 0, 0, 64))
        effect.setBlurRadius(16)
        self.collapseToolButton.setGraphicsEffect(effect)

    def __controlsActions(self):
        self.collapseToolButton.clicked.connect(self.__toggleCollapseState)

    def set_direction(self, direction):
        self.__direction = direction

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
            if self.__direction == 'left':
                self.collapseToolButton.setIcon(gf.get_icon('angle-left'))
            else:
                self.collapseToolButton.setIcon(gf.get_icon('angle-right'))
            self.widget.setHidden(True)
            if self.__collapsedTex:
                self.setCollapsedText(self.__collapsedTex)
        else:
            self.collapse_state = False
            if self.__direction == 'left':
                self.collapseToolButton.setIcon(gf.get_icon('angle-right'))
            else:
                self.collapseToolButton.setIcon(gf.get_icon('angle-left'))
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


class Ui_serverPresetsEditorWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui()

    def create_ui(self):
        self.setWindowTitle('Editing Server Presets')
        self.resize(550, 450)
        self.setSizeGripEnabled(True)

        self.creat_layout()
        self.create_edit()
        self.create_presets_tree_widget()
        self.create_buttons()

        self.fill_presets_tree()

        self.controls_actions()

    def controls_actions(self):

        self.add_new_button.clicked.connect(self.add_new_preset)
        self.remove_button.clicked.connect(self.delete_selected_preset)
        self.save_button.clicked.connect(self.save_and_close)
        self.close_button.clicked.connect(self.close)

    def creat_layout(self):

        self.main_layout = QtGui.QGridLayout()
        self.main_layout.setContentsMargins(9, 9, 9, 9)
        self.main_layout.setColumnStretch(0, 1)
        self.setLayout(self.main_layout)

    def create_presets_tree_widget(self):

        self.presets_tree_widget = QtGui.QTreeWidget()
        self.presets_tree_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.presets_tree_widget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.presets_tree_widget.setRootIsDecorated(False)
        self.presets_tree_widget.setHeaderHidden(True)
        self.presets_tree_widget.setObjectName('presets_tree_widget')
        self.presets_tree_widget.setStyleSheet(gf.get_qtreeview_style())

        self.main_layout.addWidget(self.presets_tree_widget, 1, 0, 2, 1)

    def save_and_close(self):
        env_server.save_server_presets_defaults()

        env_inst.ui_conf.serverPageWidget.readSettings()

        self.close()

    def fill_presets_tree(self):

        presets = env_server.get_server_presets()
        if presets:
            for preset in presets['presets_list']:
                root_item = QtGui.QTreeWidgetItem()
                root_item.setText(0, preset)
                self.presets_tree_widget.addTopLevelItem(root_item)

    def create_edit(self):

        self.line_edit = QtGui.QLineEdit()

        self.main_layout.addWidget(self.line_edit, 0, 0, 1, 1)

    def create_buttons(self):

        self.add_new_button = QtGui.QPushButton('Add')
        self.add_new_button.setMinimumWidth(90)
        self.remove_button = QtGui.QPushButton('Remove')
        self.remove_button.setMinimumWidth(90)
        self.save_button = QtGui.QPushButton('Save and Close')
        self.save_button.setMinimumWidth(90)
        self.close_button = QtGui.QPushButton('Cancel')
        self.close_button.setMinimumWidth(90)

        self.main_layout.addWidget(self.add_new_button, 0, 1, 1, 1)
        self.main_layout.addWidget(self.remove_button, 1, 1, 1, 1)
        self.main_layout.addWidget(self.save_button, 3, 0, 1, 1)
        self.main_layout.addWidget(self.close_button, 3, 1, 1, 1)

        spacer = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.main_layout.addItem(spacer, 2, 1, 1, 1)

    def add_new_preset(self):

        new_preset_name = self.line_edit.text()

        exclude_list = ['environment_config']
        presets = env_server.get_server_presets()
        exclude_list.extend(presets['presets_list'])

        if new_preset_name and new_preset_name not in exclude_list:
            self.line_edit.setText('')
            root_item = QtGui.QTreeWidgetItem()
            root_item.setText(0, new_preset_name)

            env_server.add_server_preset(new_preset_name)

            self.presets_tree_widget.addTopLevelItem(root_item)
        elif new_preset_name in exclude_list:
            message_box = QtGui.QMessageBox(
                QtGui.QMessageBox.Information,
                'Already exists',
                '<p>Server Preset named <b>{0}</b> already in Presets List.</p><p>Choose another Name.</p>'.format(new_preset_name),
                QtGui.QMessageBox.StandardButton,
                self,
            )
            message_box.exec_()

    def delete_selected_preset(self):
        for item in self.presets_tree_widget.selectedItems():
            preset_name = item.text(0)
            if preset_name != 'default':
                idx = self.presets_tree_widget.indexFromItem(item).row()
                self.presets_tree_widget.takeTopLevelItem(idx)
                env_server.remove_server_preset(preset_name)

    def closeEvent(self, event):
        event.accept()

        # resetting changes to server presets
        env_server.server_presets = None
        env_server.get_server_presets_defaults()
        env_server.get_server_presets()


class Ui_previewsEditorDialog(QtGui.QDialog):
    def __init__(self, files_objects, screenshots, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.files_objects = files_objects
        self.screenshots = screenshots

        self.create_ui()

    def create_ui(self):

        self.setWindowTitle('Preview Images list')

        self.resize(500, 400)
        self.setMinimumSize(QtCore.QSize(500, 400))

        self.create_widgets()

        self.contorls_actions()

        self.fill_items_tree_widget(self.files_objects)
        self.fill_screenshot_items_tree_widget(self.screenshots)

    def contorls_actions(self):

        pass

    def fill_items_tree_widget(self, items=None):
        if items:
            for file_object in items.get('file'):
                gf.add_preview_item(self.items_tree_widget, file_object=file_object)

    def fill_screenshot_items_tree_widget(self, items=None):
        if items:
            for screenshot in items:
                gf.add_preview_item(self.items_tree_widget, screenshot=screenshot)

    def create_widgets(self):

        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)

        self.items_tree_widget = QtGui.QTreeWidget()
        self.items_tree_widget.setAlternatingRowColors(True)
        self.items_tree_widget.setHeaderHidden(True)
        # self.treeWidget_vls.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.items_tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.items_tree_widget.setRootIsDecorated(False)
        self.items_tree_widget.setStyleSheet(gf.get_qtreeview_style())

        self.main_layout.addWidget(self.items_tree_widget)


class Ui_screenShotMakerDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.__dragging = True
        self.__drawn = False
        self.__resizing = False
        self.__offset_pos = None

        self.create_ui()

    def create_ui(self):

        self.setWindowTitle('Making Screenshot')

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        # if do not work on linux, try "apt install xcompmgr" and run it, or compiz
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.setGeometry(Qt4Gui.QCursor.pos().x()-12, Qt4Gui.QCursor.pos().y()-12, 24, 24)

        self.label_lay = QtGui.QVBoxLayout()
        self.setLayout(self.label_lay)
        self.screenshot_pixmap = None

        self.label_lay.setContentsMargins(0, 0, 0, 0)
        self.label_lay.setSpacing(0)

        self.bg_wd = QtGui.QLabel()
        self.bg_wd.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.bg_wd.setPixmap(gf.get_icon('crosshairs', color=Qt4Gui.QColor(255, 255, 255)).pixmap(24, 24))
        self.bg_wd.setStyleSheet(
            'QLabel {padding: 0px;border: 0px dashed rgb(255,255,255); background-color: rgba(0,0,0,1);}')
        self.label_lay.addWidget(self.bg_wd)

        self.bg_wd.setMouseTracking(True)

        self.button_lay = QtGui.QHBoxLayout(self.bg_wd)
        self.button_lay.setContentsMargins(0, 0, 0, 0)
        self.button_lay.setSpacing(0)

        self.move_under_mouse_timer = QtCore.QTimer()
        self.move_under_mouse_timer.setInterval(50)
        self.move_under_mouse_timer.timeout.connect(self.move_under_mouse)
        self.move_under_mouse_timer.start()

        self.create_take_screenshot_button()

        self.setIcon()
        self.setMouseTracking(True)

        self.controls_actions()

    def controls_actions(self):
        self.take_screenshot_button.clicked.connect(self.take_screenshot)

    def create_take_screenshot_button(self):
        self.take_screenshot_button = QtGui.QToolButton()
        self.take_screenshot_button.setText('Take Screenshot')
        self.button_lay.addWidget(self.take_screenshot_button)
        self.take_screenshot_button.setHidden(True)

    def setIcon(self):
        icon = Qt4Gui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

    def move_under_mouse(self):
        self.move(Qt4Gui.QCursor.pos().x() - 12, Qt4Gui.QCursor.pos().y() - 12)

    def take_screenshot(self):
        self.hide()
        width = self.geometry().width()
        height = self.geometry().height()
        top = self.geometry().top()
        left = self.geometry().left()
        self.screenshot_pixmap = Qt4Gui.QPixmap.grabWindow(
            QtGui.QApplication.desktop().winId(),
            left,
            top,
            width,
            height
        )

    def dragging(self, pos):
        result_pos = pos + self.__offset_pos
        self.move(result_pos)

    def resizing(self, pos):
        result_pos = pos - self.__offset_pos
        self.resize(result_pos.toTuple()[0], result_pos.toTuple()[1])

    def mouseMoveEvent(self, event):

        if self.underMouse() and not self.__resizing:
            if self.__dragging and self.__offset_pos:
                self.dragging(Qt4Gui.QCursor.pos())
        if self.__resizing and self.__offset_pos:
            self.resizing(Qt4Gui.QCursor.pos())
        elif self.__dragging and not self.__drawn:
            self.move(Qt4Gui.QCursor.pos().x() - 12, Qt4Gui.QCursor.pos().y() - 12)

        event.accept()

    def mouseReleaseEvent(self, event):
        self.__resizing = False
        self.__dragging = False
        self.setMinimumSize(128, 128)
        self.setSizeGripEnabled(True)
        self.take_screenshot_button.setHidden(False)
        event.accept()

    def mousePressEvent(self, event):
        widget_pos = self.pos()
        offset_pos = widget_pos - Qt4Gui.QCursor.pos()
        self.__offset_pos = offset_pos

        if self.__drawn:
            self.__resizing = False
            self.__dragging = True
        else:
            self.move(Qt4Gui.QCursor.pos())
            self.resize(24, 24)
            self.__offset_pos = Qt4Gui.QCursor.pos()
            self.__resizing = True
            self.__dragging = False
            self.__drawn = True
            self.bg_wd.setStyleSheet('QLabel {padding: 0px;border: 2px dashed rgb(255,255,255); background-color: rgba(0,0,0,25);}')
            self.bg_wd.setPixmap(None)
            self.move_under_mouse_timer.stop()

        event.accept()


class Ui_debugLogWidget(QtGui.QDialog, ui_debuglog.Ui_DebugLog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.create_ui()

    def create_ui(self):
        self.setWindowFlags(QtCore.Qt.Window)
        self.setSizeGripEnabled(True)

        self.controls_actions()
        # self.debugLogTextEdit.setWordWrapMode(Qt4Gui.QTextOption.NoWrap)

    def controls_actions(self):

        self.debugLogTextEdit.textChanged.connect(self.fill_modules_tree)

    def fill_modules_tree(self):
        if self.isVisible():
            scrollbar = self.debugLogTextEdit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            # self.treeWidget.clear()
            if not self.check_if_items_exists(self.treeWidget, 'FULL LOG'):
                self.full_log_item = QtGui.QTreeWidgetItem()
                self.full_log_item.setText(0, ' -- FULL LOG -- ')
                self.full_log_item.setData(0, 12, 'FULL LOG')
                self.treeWidget.addTopLevelItem(self.full_log_item)

            for debuglog_dict in [dl.info_dict, dl.warning_dict, dl.log_dict]:
                self.add_items_by_debuglog_dict(debuglog_dict)

    def add_items_by_debuglog_dict(self, debuglog_dict):
        for key, val in debuglog_dict.items():
            module_item = QtGui.QTreeWidgetItem()
            # module_item.setText(0, '{1} ({0})'.format(len(val), key))
            module_item.setText(0, '{1} ({0})'.format(len(val), key))
            module_item.setData(0, 12, key)
            module_item.setData(0, QtCore.Qt.UserRole, val)
            exist_item = self.check_if_items_exists(self.treeWidget, key)
            if not exist_item:
                self.treeWidget.addTopLevelItem(module_item)
            else:
                # exist_val = exist_item.data(0, QtCore.Qt.UserRole)
                # extended_val = exist_val + val
                # exist_item.setText(0, '{1} ({0})'.format(len(extended_val), key))
                exist_item.setText(0,  '{1} ({0})'.format(len(val), key))
                exist_item.setData(0, 12, exist_item.data(0, 12))
                exist_item.setData(0, QtCore.Qt.UserRole, val)
                module_item = exist_item

            unique_ids = set()
            for i in val:
                if i[1]['unique_id']:
                    unique_ids.add(i[1]['unique_id'])
            if unique_ids:
                for unique_id in unique_ids:
                    subgroup_list = unique_id.split('/')
                    subgroup_list.reverse()
                    self.recursive_add_items(module_item, subgroup_list)

    @staticmethod
    def check_if_items_exists(root_item, item_text):
        if type(root_item) == QtGui.QTreeWidget:
            for i in range(root_item.topLevelItemCount()):
                top_item = root_item.topLevelItem(i)
                if item_text == top_item.data(0, 12):
                    return top_item
        else:
            for i in range(root_item.childCount()):
                top_item = root_item.child(i)
                if item_text == top_item.data(0, 12):
                    return top_item

    def recursive_add_items(self, root_item, subgroup_list):
        item_text = subgroup_list.pop()
        group_item = QtGui.QTreeWidgetItem()
        if self.check_if_items_exists(root_item, item_text):
            group_item = self.check_if_items_exists(root_item, item_text)
        else:
            root_item.addChild(group_item)
            val = root_item.data(0, QtCore.Qt.UserRole)
            if val:
                group_item.setText(0, '{0} ({1})'.format(item_text, len(val)))
            else:
                group_item.setText(0, item_text)
            group_item.setData(0, 12, item_text)
            group_item.setData(0, QtCore.Qt.UserRole, val)

        if subgroup_list:
            return self.recursive_add_items(group_item, subgroup_list)

    def add_debuglog(self, debuglog_dict, message_type, write_log=False):
        if write_log:
            log_text = self.format_debuglog(debuglog_dict[1], message_type, False)
            log_path = u'{0}/log'.format(env_mode.get_current_path())
            date_str = datetime.date.strftime(dl.session_start, '%d_%m_%Y_%H_%M_%S')
            if os.path.isdir(log_path):
                with codecs.open(u'{0}/{1}_session_{2}.log'.format(log_path, env_mode.get_mode(), date_str), 'a', 'utf-8') as log_file:
                    log_file.write(log_text + u'\n')
                log_file.close()
            else:
                os.makedirs(log_path)
                with codecs.open(u'{0}/{1}_session_{2}.log'.format(log_path, env_mode.get_mode(), date_str), 'a', 'utf-8') as log_file:
                    log_file.write(log_text + u'\n')
                log_file.close()

            self.debugLogTextEdit.append(log_text)
        else:
            self.debugLogTextEdit.append(self.format_debuglog(debuglog_dict[1], message_type))

    def format_debuglog(self, debuglog_dict, message_type, html=True):

        trace_str = u'[{6}] \n    Message: {2}\n       {0} {1} {4} / {5}(): {3:04d}\n'.format(
            datetime.date.strftime(debuglog_dict['datetime'], '[%d.%m.%Y - %H:%M:%S.%f]'),
            message_type,
            debuglog_dict['message_text'],
            int(debuglog_dict['line_number']),
            debuglog_dict['module_path'],
            debuglog_dict['function_name'],
            debuglog_dict['unique_id'],)

        if html:
            if message_type == '[ INF ]':
                color = '009933'
            elif message_type == '[ WRN ]':
                color = 'ffcc00'
            elif message_type == '[ ERR ]':
                color = 'ff1a1a'
            elif message_type == '[ CRL ]':
                color = '3385ff'
            elif message_type == '[ EXC ]':
                color = 'ff8080'
            else:
                color = 'a5a5a5'
            return u'<span style="color:#{0};">{1}</span>'.format(color, trace_str)
        else:
            return trace_str

    def showEvent(self, event):
        event.accept()
        self.fill_modules_tree()


class Underlayer(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.pane_color = Qt4Gui.QColor(100, 100, 100, 255)
        self.line_color = Qt4Gui.QColor(80, 80, 80, 255)

    def paintEvent(self, event):

        wdg_size = self.size()
        painter = Qt4Gui.QPainter()
        painter.begin(self)

        painter.setRenderHint(Qt4Gui.QPainter.Antialiasing, True)
        painter.setPen(Qt4Gui.QColor(0, 0, 0, 0))
        painter.setBrush(self.pane_color)
        width = wdg_size.width()-10
        height = wdg_size.height()-10

        rect_width = int(wdg_size.width() / 2 - width / 2)
        rect_height = int(wdg_size.height() / 2 - height / 2)
        painter.drawRoundedRect(rect_width+1, rect_height-42, width-7, height+40, 6, 6)

        pen = Qt4Gui.QPen()
        pen.setStyle(QtCore.Qt.SolidLine)
        pen.setWidth(1)
        pen.setColor(self.line_color)
        painter.setPen(pen)
        painter.drawLine(30, 2, width-20, 2)

        painter.end()


class CustomTreeView(QtGui.QTreeView):
    item_mouse_clicked = QtCore.Signal(object)

    def __init__(self, line_edit_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.line_edit_widget = line_edit_widget
        self.shown_once = False

        self.create_ui()

        self.customize_ui()

        self.controls_actions()

    def controls_actions(self):
        self.pressed.connect(self.item_clicked)

    def item_clicked(self, item):
        self.item_mouse_clicked.emit(item)

    def create_ui(self):
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setFocus(QtCore.Qt.PopupFocusReason)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)
        self.setWordWrap(True)
        self.setAllColumnsShowFocus(True)
        self.setTabKeyNavigation(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        self.underlayer = Underlayer(self)

        effect = QtGui.QGraphicsDropShadowEffect(self)
        effect.setOffset(0, 0)
        effect.setColor(Qt4Gui.QColor(0, 0, 0, 64))
        effect.setBlurRadius(16)
        self.underlayer.setGraphicsEffect(effect)

        self.underlayer.lower()

    def customize_ui(self):
        style = """
        QAbstractItemView {
            font-size: 9pt;
            selection-background-color:	rgb(28, 32, 30);
            selection-color: rgb(245,245,245);
            alternate-background-color: rgba(52,52,52,32);
            background: rgb(52,52,52);
            border: 0px;
        }
        QAbstractItemView::item:hover {
            background-color: rgb(38, 42, 40);
            border: 0px;
        }
        QTreeView::item {
            padding: 1px;
            border: 0px;
        }
        QTreeView::item:selected {
            padding: 1px;
            background: rgb(48, 52, 50);
            border: 0px;
        }
        QTreeView {
            border: 0px;
            padding: 2px 12px 12px 8px;
        }
        QScrollBar:vertical {
            border: 0px ;
            background: transparent;
            width:8px;
            margin: 0px 0px 0px 0px;
            }
        QScrollBar::handle:vertical {
            background: rgba(0,0,0,64);
            min-height: 0px;
            border-radius: 4px;
            }
        QScrollBar::add-line:vertical {
            background: rgba(0,0,0,64);
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
            }
        QScrollBar::sub-line:vertical {
            background: rgba(0,0,0,64);
            height: 0 px;
            subcontrol-position: top;
            subcontrol-origin: margin;
            }
        """
        self.setStyleSheet(style)

    def move_to_start_position(self):
        parent_pos = self.line_edit_widget.mapTo(self.parent(), QtCore.QPoint(0, 0))
        self.move(parent_pos.x(), parent_pos.y()+32)

    def resize_to_start_position(self):
        parent_size = self.line_edit_widget.size()
        self.resize(parent_size.width() + 5, parent_size.height() + 12)

    def resize_to_new_position(self):
        parent_size = self.line_edit_widget.size()
        current_size = self.size()
        self.resize(parent_size.width() + 5, current_size.height())

    def showEvent(self, event):

        super(CustomTreeView, self).showEvent(event)

        if not self.shown_once:
            self.move_to_start_position()
            self.resize_to_start_position()
            self.shown_once = True

    def fit_columns(self):

        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)
        self.resizeColumnToContents(2)

        middle_column_width = self.width() - self.columnWidth(0) - self.columnWidth(2) - 80

        self.setColumnWidth(1, middle_column_width + 40)

    def resizeEvent(self, event):

        path = Qt4Gui.QPainterPath()
        size = self.size()

        path.addRect(QtCore.QRectF(0, 0, size.width()-4, size.height()-4))
        mask = Qt4Gui.QRegion(path.toFillPolygon().toPolygon())

        self.setMask(mask)
        self.underlayer.resize(self.size())

        self.fit_columns()

        event.accept()


class SuggestedLineEdit(QtGui.QLineEdit):

    item_highlighted = QtCore.Signal(object)
    item_selected = QtCore.Signal(object)
    item_clicked = QtCore.Signal(object)

    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.popup_fillColor = Qt4Gui.QColor(103, 103, 103, 255)
        self.popup_penColor = Qt4Gui.QColor(128, 128, 128, 255)

        self.stype = stype
        self.project = project
        self.return_pressed = False
        self.single_click_select_all = True
        self.autofill_selected_items = False
        self.display_limit = 50
        self.popup_limit = 20
        self.suggest_column = 'name'
        self.search_filters = None
        self.default_filter = None

        self.create_ui()

        self.controls_actions()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:

            self.clear_items_list()

        elif event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            item = None

            model_index = self.custom_tree_view.currentIndex()
            if model_index:
                if model_index.row() != -1:
                    item = self.custom_tree_view.model().itemFromIndex(model_index)
                    if item:
                        self.item_selected.emit(item.data(QtCore.Qt.UserRole))

            self.clear_items_list()

            if not item:
                super(SuggestedLineEdit, self).keyPressEvent(event)

        elif event.key() == QtCore.Qt.Key_Down:

            selection = self.custom_tree_view.selectionModel()
            current_index = self.custom_tree_view.currentIndex()
            if current_index.row() == -1:
                model_index = self.custom_tree_view.model().indexFromItem(self.custom_tree_view.model().item(0))
            else:
                model_index = self.custom_tree_view.indexBelow(current_index)

            item = self.custom_tree_view.model().itemFromIndex(model_index)
            if item:
                self.item_highlighted.emit(item.data(QtCore.Qt.UserRole))

            selection.setCurrentIndex(model_index, QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.ClearAndSelect)

        elif event.key() == QtCore.Qt.Key_Up:

            selection = self.custom_tree_view.selectionModel()
            current_index = self.custom_tree_view.currentIndex()
            if current_index.row() == -1:
                rows = self.custom_tree_view.model().rowCount()
                model_index = self.custom_tree_view.model().indexFromItem(self.custom_tree_view.model().item(rows-1))
            else:
                model_index = self.custom_tree_view.indexAbove(current_index)

            item = self.custom_tree_view.model().itemFromIndex(model_index)
            if item:
                self.item_highlighted.emit(item.data(QtCore.Qt.UserRole))

            selection.setCurrentIndex(model_index, QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.ClearAndSelect)

        else:
            super(SuggestedLineEdit, self).keyPressEvent(event)

    def update_items_list(self, string_list, dicts_list):

        if isinstance(self.custom_tree_view.model(), Qt4Gui.QStandardItemModel):
            self.custom_tree_view.model().clear()
            standart_item_model = self.custom_tree_view.model()
        else:
            standart_item_model = Qt4Gui.QStandardItemModel(0, 2)
            self.custom_tree_view.setModel(standart_item_model)

        total_height = 0
        size_hint_of_row = 0
        count_of_rows = 0

        for row, s in enumerate(string_list):
            name = s.split('|')
            if count_of_rows < self.popup_limit:
                total_height += size_hint_of_row
            count_of_rows += 1

            for column in range(3):

                if len(name) > column:
                    item = Qt4Gui.QStandardItem(name[column])
                    if column == 0:
                        item.setIcon(gf.get_icon('magnify', icons_set='mdi', scale_factor=1.1))
                    standart_item_model.setItem(row, column, item)
                    size_hint_of_row = self.custom_tree_view.sizeHintForRow(0)

                    # Adding data dict
                    item.setData(dicts_list[row], QtCore.Qt.UserRole)

        doing_popup = True

        s = self.custom_tree_view.size()
        if standart_item_model.rowCount() < 1:
            self.customize_ui(False)
            self.custom_tree_view.hide()
            doing_popup = False
        elif standart_item_model.rowCount() == 1:
            self.custom_tree_view.show()
            self.custom_tree_view.resize(s.width(), size_hint_of_row * 2)
        else:
            self.custom_tree_view.show()
            self.custom_tree_view.resize(s.width(), total_height + size_hint_of_row * 2)

        if doing_popup:
            self.customize_ui(True)

            self.custom_tree_view.show()
            self.custom_tree_view.raise_()
            self.custom_tree_view.move_to_start_position()

            self.custom_tree_view.fit_columns()

    def clear_items_list(self):
        self.custom_tree_view.hide()
        self.customize_ui(False)

    def create_ui(self):
        # be careful when choosing parent
        self.custom_tree_view = CustomTreeView(line_edit_widget=self, parent=self.parent())
        self.custom_tree_view.setHidden(True)

        # self.customize_ui()

        # limiting available search characters
        self.validator = Qt4Gui.QRegExpValidator(QtCore.QRegExp('\w+'), self)
        self.setFrame(False)

        self.create_magnify_icon()

        self.setMinimumHeight(44)

    def create_magnify_icon(self):

        self.magnify_tool_button = QtGui.QToolButton(self)
        self.magnify_tool_button.move(16, int(self.height() / 2)-2)
        self.magnify_tool_button.setAutoRaise(True)

        self.magnify_tool_button.setStyleSheet(
            'QToolButton {'
            'margin-left: 0px;'
            'margin-right: 0px;'
            'background: transparent;'
            'border: 0px; padding: 0px 0px;}'
            'QToolButton:pressed {'
            'background: rgba(128, 128, 128, 32)}')

        self.magnify_tool_button.setIcon(gf.get_icon('magnify', icons_set='mdi', scale_factor=1.3))

    def controls_actions(self):
        self.item_selected.connect(self.do_item_selected)
        self.item_clicked.connect(self.do_item_clicked)
        self.textEdited.connect(self.search_suggestions)
        self.custom_tree_view.item_mouse_clicked.connect(self.item_mouse_clicked)

    def do_item_selected(self, item_dict):
        if self.autofill_selected_items:
            if self.custom_tree_view.isVisible():
                self.setText(item_dict.get(self.suggest_column))

    def do_item_clicked(self, item_dict):
        if self.autofill_selected_items:
            self.setText(item_dict.get(self.suggest_column))

    def item_mouse_clicked(self, model_index):

        item = self.custom_tree_view.model().itemFromIndex(model_index)
        self.item_clicked.emit(item.data(QtCore.Qt.UserRole))

        self.clear_items_list()

    def mousePressEvent(self, event):
        if self.custom_tree_view.isVisible():
            self.clear_items_list()
        else:
            self.search_suggestions(self.text())

        super(SuggestedLineEdit, self).mousePressEvent(event)

    def focusOutEvent(self, event):
        self.clear_items_list()
        super(SuggestedLineEdit, self).focusOutEvent(event)

    def customize_ui(self, suggested_popup=False):
        self.setContentsMargins(6, 6, 6, 6)
        customize_dict = {'bottom_radius': int(self.height() / 4)-6, 'top_radius': int(self.height() / 4)-6}

        if suggested_popup:
            customize_dict['bottom_radius'] = 0

        self.setStyleSheet("""
        QLineEdit {{
            font-size:11pt;
            border: 0px;
            border-top-left-radius: {top_radius}px;
            border-top-right-radius: {top_radius}px;
            border-bottom-right-radius: {bottom_radius}px;
            border-bottom-left-radius: {bottom_radius}px;
            show-decoration-selected: 1;
            background: rgb(100, 100, 100);
            selection-background-color: darkgray;
            padding-right: 4px;
            padding-left: 32px;
        }}
        QLineEdit:hover{{
            color: white;
        }}
        """.format(**customize_dict))

        effect = QtGui.QGraphicsDropShadowEffect(self)
        effect.setOffset(0, 0)
        effect.setColor(Qt4Gui.QColor(0, 0, 0, 64))
        effect.setBlurRadius(16)
        self.setGraphicsEffect(effect)

    def set_autofill_selected_items(self, do_autofill=True):
        self.autofill_selected_items = do_autofill

    def set_return_pressed(self):
        self.return_pressed = True

    def set_suggest_column(self, column_name):
        self.suggest_column = column_name

    def get_suggest_column(self):
        return self.suggest_column

    def set_default_filter(self, default_filter):
        self.default_filter = default_filter

    def get_default_filter(self):
        return self.default_filter

    def set_search_filters(self, search_filters):
        self.search_filters = search_filters

    def get_search_filters(self):
        return self.search_filters

    @gf.catch_error
    def search_suggestions(self, key=None):

        state = self.validator.validate(key, 0)[0].name

        if self.text() == '' or state == 'Invalid':
            self.clear_items_list()

        if self.suggest_column in ['_expression']:
            state = 'Invalid'

        if key and not state == 'Invalid':
            code = self.stype.info.get('code')
            stype_columns = self.stype.get_columns_info()
            project = self.project.info.get('code')

            additional_columns = ['keywords', 'code', 'description']
            columns = [self.suggest_column]
            if self.suggest_column not in stype_columns:
                self.suggest_column = 'title'
                if self.suggest_column not in stype_columns:
                    self.suggest_column = 'code'

            for add_column in additional_columns:
                # adding only available columns
                if stype_columns.get(add_column):
                    if add_column not in columns:
                        columns.append(add_column)

            from thlib.ui_classes.ui_search_classes import get_suggestion_filter
            self.set_search_filters(get_suggestion_filter(
                self.suggest_column,
                key,
                possible_columns=columns,
                default_filter=self.get_default_filter()
            ))

            def assets_query_new_agent():
                return (tc.server_query(
                    filters=self.get_search_filters(),
                    stype=code,
                    columns=columns,
                    project=project,
                    limit=self.display_limit,
                    offset=0,
                ), key)

            worker = env_inst.server_pool.add_task(assets_query_new_agent)
            worker.result.connect(self.search_suggestions_end)
            worker.error.connect(gf.error_handle)
            worker.start()

    def search_suggestions_end(self, result=None):

        if result[0]:
            key = result[1]
            result = result[0]

            suggestions_list = []
            suggestions_dicts_list = []

            for item in result:
                item_text = item.get(self.suggest_column)
                item_dict = {}

                if item_text:

                    item_dict[self.suggest_column] = six.ensure_text(item_text)

                    if item.get('keywords'):
                        item_dict['keywords'] = six.ensure_text(item.get('keywords'))

                        keywords_list = item_dict['keywords'].replace(',', ' ').replace('  ', ' ').split(' ')
                        kwd = ''
                        for k in keywords_list:
                            if k.find(key) != -1:
                                kwd = k
                        keyword = kwd
                    else:
                        keyword = ''

                    if item.get('description'):
                        item_dict['description'] = six.ensure_text(item.get('description'))

                        description = item_dict['description'].replace('\n', ' ')
                    else:
                        description = ''

                    if keyword and description:
                        result_item_text = u'{}|- {}|#{}'.format(item_text, description, keyword)
                    elif keyword:
                        result_item_text = u'{}||#{}'.format(item_text, keyword)
                    elif description:
                        result_item_text = u'{}|- {}'.format(item_text, description)
                    else:
                        result_item_text = item_text

                    if result_item_text not in suggestions_list:
                        suggestions_list.append(result_item_text)
                        suggestions_dicts_list.append(item_dict)

            self.update_items_list(suggestions_list, suggestions_dicts_list)
        else:
            self.clear_items_list()

    def setText(self, event, block_event=False):
        if block_event:
            self.setText(event)
        else:
            super(SuggestedLineEdit, self).setText(event)

    def resizeEvent(self, event):
        self.custom_tree_view.resize_to_new_position()

        event.accept()

    def showEvent(self, event):

        self.customize_ui()

        event.accept()


class Ui_coloredComboBox(QtGui.QComboBox):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setEditable(True)

        self.customize()

        self.controls_actions()

    def controls_actions(self):
        self.currentIndexChanged.connect(self.index_changed)

    def add_item(self, item_text, item_color=None, hex_color=None, item_data=None):
        if hex_color:
            c = gf.hex_to_rgb(hex_color, tuple=True)
            item_color = Qt4Gui.QColor(c[0], c[1], c[2], 128)

        if not item_color:
            self.addItem(item_text)
        else:
            model = self.model()
            item = Qt4Gui.QStandardItem(u'{0}'.format(item_text))
            item.setBackground(item_color)
            item.setData(item_color, 1)
            item.setData(item_text, 2)
            if item_data:
                item.setData(item_data, 3)
            model.appendRow(item)

    def index_changed(self):
        item_color = self.itemData(self.currentIndex(), 1)
        if item_color:
            c = item_color.toTuple()
            rgba_color = 'rgba({0}, {1}, {2}, {3})'.format(c[0], c[1], c[2], 192)
            self.setStyleSheet('QComboBox {background: ' + rgba_color + ';}')
            self.customize(rgba_color)
        else:
            self.setStyleSheet('')

    def customize(self, rgba_color=None):
        if not rgba_color:
            rgba_color = 'rgba(255, 255, 255, 48)'
        line_edit = self.lineEdit()
        line_edit.setStyleSheet("""
            QLineEdit {
                border: 0px;
                border-radius: 2px;
                show-decoration-selected: 1;
                padding: 0px 0px;
            """ + """background: {};""".format(rgba_color) +
                                """ background-position: bottom left;
                                    background-repeat: fixed;
                                    selection-background-color: darkgray;
                                    padding-left: 0px;
                                }
                                """)


class StyledToolButton(QtGui.QToolButton):
    def __init__(self, size='normal', shadow_enabled=True, square_type=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.shadow_enabled = shadow_enabled
        self.square_type = square_type
        self.size = size
        self.setAutoRaise(True)

        self.create_ui()

    def create_ui(self):

        if self.size == 'tiny':
            if self.shadow_enabled:
                self.setFixedSize(30, 30)
            else:
                self.setFixedSize(22, 22)
        elif self.size == 'small':
            if self.shadow_enabled:
                self.setFixedSize(38, 38)
            else:
                self.setFixedSize(34, 34)
        elif self.size == 'normal':
            if self.shadow_enabled:
                self.setFixedSize(42, 42)
            else:
                self.setFixedSize(38, 38)

        self.customize_ui()
        self.setCursor(Qt4Gui.QCursor(QtCore.Qt.PointingHandCursor))

    def customize_ui(self):

        if self.shadow_enabled:
            if self.square_type:
                customize_dict = {'radius': int(self.height() / 8)}
            else:
                customize_dict = {'radius': int(self.height() / 2) - 4}

            customize_dict['margin'] = 4
            effect = QtGui.QGraphicsDropShadowEffect(self)
            effect.setOffset(0, 0)
            effect.setColor(Qt4Gui.QColor(0, 0, 0, 64))
            effect.setBlurRadius(16)
            self.setGraphicsEffect(effect)
        else:
            if self.square_type:
                customize_dict = {'radius': int(self.height() / 4)}
            else:
                customize_dict = {'radius': int(self.height() / 2)}

            customize_dict['margin'] = 0

        self.setStyleSheet("""
        QToolButton {{
            border: 0px;
            border-radius: {radius}px;
            background: transparent;
            margin: {margin}px;
        }}
        QToolButton::menu-indicator {{
            background: transparent;
        }}
        QToolButton:pressed {{
            background-color: rgb(107, 107, 107);
        }}
        /*
        QToolButton:hover {{
            background-color: rgb(107, 107, 107);
        }}
        */
        """.format(**customize_dict))


class StyledChooserToolButton(QtGui.QToolButton):
    def __init__(self, small=False, shadow_enabled=True, square_type=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.shadow_enabled = shadow_enabled
        self.square_type = square_type
        self.small = small

        effect = QtGui.QGraphicsDropShadowEffect(self)
        effect.setOffset(0, 0)
        effect.setColor(Qt4Gui.QColor(0, 0, 0, 64))
        effect.setBlurRadius(16)
        self.setGraphicsEffect(effect)

        # self.setPopupMode(QtGui.QToolButton.InstantPopup)

        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.setIcon(gf.get_icon('chevron-down', icons_set='mdi', scale_factor=1.2))

        self.create_ui()

    def create_ui(self):

        if self.small:
            self.setMaximumHeight(32)
        else:
            self.setMaximumHeight(38)

        # self.create_menu()

        self.customize_ui()
        self.setCursor(Qt4Gui.QCursor(QtCore.Qt.PointingHandCursor))

    # def create_menu(self):
    #
    #     self.menu = QtGui.QMenu()
    #     self.menu.setLayoutDirection(QtCore.Qt.LeftToRight)
    #
    #     self.setMenu(self.menu)
    #
    # def get_menu(self):
    #     return self.menu

    def customize_ui(self):

        if self.square_type:
            customize_dict = {'radius': int(self.height() / 8), 'margin': 4}
        else:
            customize_dict = {'radius': int(self.height() / 2)-4, 'margin': 4}

        self.setStyleSheet("""
        QToolButton {{
            font-size:11pt;
            color: rgb(192,192,192);
            border: 0px;
            border-radius: {radius}px;
            background: transparent;
            margin: {margin}px;
        }}
        QToolButton::menu-indicator {{
        background: transparent;
        }}
        QToolButton:pressed {{
            /*background-color: rgb(44, 44, 44);*/
        }}
        QToolButton:hover {{
            /*background-color: rgb(107, 107, 107);*/
        }}
        """.format(**customize_dict))

        if self.shadow_enabled:
            effect = QtGui.QGraphicsDropShadowEffect(self)
            effect.setOffset(0, 0)
            effect.setColor(Qt4Gui.QColor(0, 0, 0, 64))
            effect.setBlurRadius(16)
            self.setGraphicsEffect(effect)


class StyledComboBox(QtGui.QComboBox):
    def __init__(self, flat_style=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.flat_style = flat_style

        self.create_ui()

    def create_ui(self):

        self.customize_ui()

        self.controls_actions()

    def controls_actions(self):
        pass

    def customize_ui(self):

        self.setMaximumHeight(32)

        effect = QtGui.QGraphicsDropShadowEffect(self)
        effect.setOffset(0, 0)
        effect.setColor(Qt4Gui.QColor(0, 0, 0, 64))
        effect.setBlurRadius(16)
        self.setGraphicsEffect(effect)

        self.setStyleSheet("""
        QComboBox {
            border: 0px;
            border-radius: 4px;
            padding-right: 4px;
            padding-left: 16px;
            /* min-width: 6em; */
            font-size:11pt;
        }
        
        QComboBox:editable {
            background: transparent;
        }
        
        QComboBox:!editable, QComboBox::drop-down:editable {
             /*background: rgb(100,100,100);*/
             background: transparent;
        }
        
        QComboBox:!editable:on, QComboBox::drop-down:editable:on {
            /*background: rgb(120,120,120);*/
            background: transparent;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 10px;
        
            border-left-width: 0px;
            border-left-color: darkgray;
            border-left-style: solid;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
        }
        
        QComboBox QAbstractItemView {
            border: 0px;
            selection-background-color: rgb(120, 120, 120);
        }
        QScrollBar:vertical {
            border: 0px ;
            background: rgb(64, 64, 64);
            width:8px;
            margin: 0px 0px 0px 0px;
            }
        QScrollBar::handle:vertical {
            background: rgb(100,100,100);
            min-height: 0px;
            border-radius: 4px;
            }
        QScrollBar::add-line:vertical {
            background: rgba(0,0,0,64);
            height: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
            }
        QScrollBar::sub-line:vertical {
            background: rgba(0,0,0,64);
            height: 0 px;
            subcontrol-position: top;
            subcontrol-origin: margin;
            }
        """)


class Ui_replyWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui()

    def create_ui(self):

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.editorLayout = QtGui.QVBoxLayout()
        self.editorLayout.setSpacing(0)
        self.verticalLayout.addLayout(self.editorLayout)
        self.descriptionTextEdit = QtGui.QTextEdit()
        self.verticalLayout.addWidget(self.descriptionTextEdit)
        self.verticalLayout.setStretch(1, 1)
        self.setLayout(self.verticalLayout)

        self.reply_button = QtGui.QPushButton('Reply')

        self.verticalLayout.addWidget(self.reply_button)

        self.create_rich_edit()

    def controls_actions(self):
        pass

    def create_rich_edit(self):
        self.ui_richedit = ui_richedit_classes.Ui_richeditWidget(self.descriptionTextEdit, parent=self.descriptionTextEdit)
        self.editorLayout.addWidget(self.ui_richedit)


class Ui_messagesWidget(QtGui.QDialog, ui_messages.Ui_messages):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        env_inst.ui_messages = self

        self.setupUi(self)

        self.created = False

    def create_ui(self):

        self.setSizeGripEnabled(True)
        self.setWindowTitle('Messages')

        self.usersTreeWidget.setRootIsDecorated(False)

        self.fill_users_tree()
        self.create_chat_tabs()

        self.controls_actions()
        self.created = True

    def controls_actions(self):

        self.usersTreeWidget.itemSelectionChanged.connect(self.select_current_tree_widget_item)

    def fill_users_tree(self):

        # logins = env_inst.logins

        # print logins
        # print env_inst.get_all_login_groups()
        self.usersTreeWidget.clear()

        for login_group in env_inst.get_all_login_groups():
            top_item = QtGui.QTreeWidgetItem()
            top_item.setText(0, login_group.get_pretty_name())
            top_item.setData(0, QtCore.Qt.UserRole, login_group)
            self.usersTreeWidget.addTopLevelItem(top_item)
            group_logins = login_group.get_logins()
            if group_logins:
                for login in group_logins:
                    login_item = QtGui.QTreeWidgetItem()
                    login_item.setText(0, login.get_display_name())
                    login_item.setData(0, QtCore.Qt.UserRole, login)
                    top_item.addChild(login_item)

                top_item.setExpanded(True)

    def select_current_tree_widget_item(self):
        selected_items = self.usersTreeWidget.selectedItems()
        if selected_items:
            # print selected_items[0]
            # print selected_items[0].data(0, QtCore.Qt.UserRole)
            item_data = selected_items[0].data(0, QtCore.Qt.UserRole)
            if item_data.get_object_type() == 'login':
                # print item_data.get_subscriptions()
                print(item_data)
                import random
                key = random.randrange(0, 255)
                tc.server_start().subscribe(key, category='chat')

    def create_chat_tabs(self):

        current_login = env_inst.get_current_login_object()

        self.chat_tab_widget = Ui_extendedTabBarWidget(self)
        self.chat_tab_widget.setMovable(True)
        self.chat_tab_widget.setTabsClosable(True)
        self.chat_tab_widget.setObjectName('chat_tab_widget')
        self.chat_tab_widget.customize_ui()

        for chat in current_login.get_subscriptions_by_category('chat'):
            if chat.get_login() == current_login.get_code():

                partner_login_name = chat.get_message_code()
                for ms_code in current_login.get_subscriptions_by_category('chat'):
                    if ms_code.info['message_code'] == chat.info['message_code'] and ms_code.get_login() != chat.get_login():
                        partner_login_obj = env_inst.get_all_logins(ms_code.get_login())
                        partner_login = ms_code.get_login()
                        if partner_login_obj:
                            partner_login_name = partner_login_obj.get_display_name()
                        else:
                            partner_login_name = ms_code.get_login()

                chat_tab = self.create_chat_tab(chat, partner_login)

                self.chat_tab_widget.addTab(chat_tab, partner_login_name)

        self.tabsVerticalLayout.addWidget(self.chat_tab_widget)

    def create_chat_tab(self, chat_subscription, partner_login):
        tab_layout = QtGui.QVBoxLayout()
        tab_widget = QtGui.QWidget()
        tab_widget.setLayout(tab_layout)

        text_edit = QtGui.QTextEdit()

        reply_widget = Ui_replyWidget(self)

        tab_layout.addWidget(text_edit)
        tab_layout.addWidget(reply_widget)

        # temporary!!!
        reply_widget.reply_button.clicked.connect(lambda: self.post_reply(
            text_edit,
            chat_subscription,
            partner_login,
            reply_widget.descriptionTextEdit.toPlainText(),
        ))

        self.fill_chat_messages(text_edit, chat_subscription, partner_login)

        return tab_widget

    def fill_chat_messages(self, chat_widget, chat_subscription, partner_login):

        for message in chat_subscription.get_messages():
            print(message.get_status())
            if message.get_status() == 'in_progress':
                message_logs = message.get_message_log(True)
                last_cleared_date = gf.parce_timestamp(chat_subscription.get_last_cleared())
                for message_log in reversed(message_logs):
                    if last_cleared_date:
                        message_date = gf.parce_timestamp(message_log.get_timestamp())
                        if last_cleared_date < message_date:
                            chat_widget.append('New Message: ')
                    chat_widget.append(u'   {0}: {1}'.format(message_log.get_login(), message_log.get_message()))

    def post_reply(self, chat_widget, chat_subscription, partner_login, reply_text):

        key = chat_subscription.get_message_code()
        message = reply_text
        category = 'chat'

        tc.server_start().log_message(key, message, category=category, status='in_progress')

        chat_widget.clear()

        # current_login.get_subscriptions_and_messages(True)

        self.fill_chat_messages(chat_widget, chat_subscription, partner_login)

        print(reply_text)

    def showEvent(self, event):
        if not self.created:
            self.create_ui()

        event.accept()


class Ui_elideLabel(QtGui.QLabel):

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.highlighted_part = None
        self.highlighted_part_color = None

        self.setFont(self.font())

        self.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Preferred)
        self.setWordWrap(False)
        # self.setContentsMargins(8, -10, 0, 0)

    def set_font_size(self, size_int):
        self.font().setPointSize(size_int)

    def set_highlighted_part(self, text, color):

        self.highlighted_part = text
        self.highlighted_part_color = color

    def paintEvent(self, event):
        painter = QtGui.QStylePainter(self)
        metrics = Qt4Gui.QFontMetrics(self.font())
        if self.highlighted_part:
            doc = Qt4Gui.QTextDocument(self)
            doc.setUndoRedoEnabled(False)
            elided = metrics.elidedText(self.text(), QtCore.Qt.ElideRight, self.width())

            until_context = elided.find(self.highlighted_part)
            if until_context != -1:
                first_part = elided[:until_context]
                second_part = elided[len(first_part) + len(self.highlighted_part):]

                elided = u'{0}<font color="{1}">{2}</font>{3}'.format(first_part, self.highlighted_part_color, self.highlighted_part, second_part)

            doc.setHtml(elided)
            # doc.setDocumentMargin(2)
            doc.setDefaultFont(self.font())
            doc.setTextWidth(self.width())
            doc.setUseDesignMetrics(True)
            text_options = Qt4Gui.QTextOption()
            text_options.setWrapMode(Qt4Gui.QTextOption.NoWrap)
            doc.setDefaultTextOption(text_options)

            painter.setRenderHints(Qt4Gui.QPainter.Antialiasing | Qt4Gui.QPainter.HighQualityAntialiasing | Qt4Gui.QPainter.SmoothPixmapTransform | Qt4Gui.QPainter.TextAntialiasing, True)
            doc.drawContents(painter, self.contentsRect())
            painter.end()
        else:
            elided = metrics.elidedText(self.text(), QtCore.Qt.ElideRight, self.width())
            painter.drawText(self.contentsRect(), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, elided)
