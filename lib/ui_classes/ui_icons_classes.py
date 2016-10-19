# module Tree widget item Classes
# file ui_icons_classes.py
# Icons preview Widget

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import lib.ui.misc.ui_icons as ui_icons
# import lib.environment as env
from lib.environment import env_server, env_tactic
import lib.global_functions as gf
import lib.tactic_classes as tc

reload(ui_icons)
from pprint import pprint


class Ui_iconsWidget(QtGui.QWidget, ui_icons.Ui_icons):
    def __init__(self, nested_item, external=False, playblast=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.scene = QtGui.QGraphicsScene(self)

        self.external = external

        self.nested_item = nested_item

        self.playblast = playblast

        # get only icons process, and icons contexts snapshots
        if self.playblast:
            self.versions_icons = self.nested_item.files
        else:
            self.versions_icons = self.nested_item.sobject.process['icon'].contexts['icon'].versions

        self.main_list = []
        self.playblast_list = []
        self.icon_list = []
        self.web_list = []
        self.filter_icons_types()

        self.imagesSlider.setMinimum(1)
        self.spinBox.setMinimum(1)
        self.imagesSlider.setMaximum(len(self.icon_list))
        self.spinBox.setMaximum(len(self.icon_list))

        self.slide_images(len(self.icon_list))

        self.imagesSlider.setValue(len(self.icon_list))
        self.imagesSlider.valueChanged.connect(self.slide_images)

        self.create_menu()

    def create_menu(self):
        self.previewGraphicsView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self.menu_actions = []

        self.open_bigger = QtGui.QAction("Open Bigger", self.previewGraphicsView)
        self.open_bigger.triggered.connect(lambda: self.open_big(self.imagesSlider.value()))

        self.copy_path = QtGui.QAction("Copy Path", self.previewGraphicsView)
        self.copy_path.triggered.connect(lambda: self.copy_pth(self.imagesSlider.value()))

        self.previews_maya = QtGui.QAction('', self.previewGraphicsView)
        self.previews_maya.setSeparator(True)

        self.add_imageplane = QtGui.QAction("Add as Imageplane", self.previewGraphicsView)
        self.add_imageplane.triggered.connect(lambda: self.add_as_image_plane(self.imagesSlider.value()))

        self.previews_sep = QtGui.QAction('', self.previewGraphicsView)
        self.previews_sep.setSeparator(True)

        self.add_new_image = QtGui.QAction("Add new Image", self.previewGraphicsView)
        self.add_new_image.triggered.connect(lambda: self.open_ext(self.imagesSlider.value()))

        self.add_new_playblast = QtGui.QAction("Capture new playblast", self.previewGraphicsView)
        self.add_new_playblast.triggered.connect(lambda: self.open_ext(self.imagesSlider.value()))

        self.open_external = QtGui.QAction("Open External", self.previewGraphicsView)
        self.open_external.triggered.connect(lambda: self.open_ext(self.imagesSlider.value()))

        if self.external:
            self.menu_actions.append(self.open_bigger)
        self.menu_actions.append(self.copy_path)
        self.menu_actions.append(self.previews_maya)
        if not self.playblast:
            self.menu_actions.append(self.add_imageplane)
            self.menu_actions.append(self.previews_sep)
            self.menu_actions.append(self.add_new_image)
        else:
            self.menu_actions.append(self.add_new_playblast)
        self.menu_actions.append(self.open_external)

        self.previewGraphicsView.addActions(self.menu_actions)

    def add_as_image_plane(self, value):
        print('Adding as image plane')
        print(value)
        upload = tc.checkin_playblast()
        pprint(upload)

    def open_ext(self, value):
        # print(self.main_list)
        print(self.slide_images(value))
        gf.open_file_associated(self.slide_images(value))

    def copy_pth(self, value):
        print('Copying path')
        print(value)
        upload = tc.upload_maya_file()
        pprint(upload)

    def open_big(self, value):
        if self.playblast:
            self.external_self_widget = Ui_iconsWidget(self.nested_item, playblast=True)
        else:
            self.external_self_widget = Ui_iconsWidget(self.nested_item)
        self.ext_window = QtGui.QMainWindow(self)
        self.ext_window.setContentsMargins(9, 9, 9, 9)
        item_name = self.nested_item.sobject.info['name']
        if self.playblast:
            self.ext_window.setWindowTitle('Bigger playblast view ' + item_name)
        else:
            self.ext_window.setWindowTitle('Bigger view ' + item_name)
        self.ext_window.setCentralWidget(self.external_self_widget)
        self.ext_window.closeEvent = self.closeEventExt
        self.ext_window.show()
        self.ext_window.resize(700, 500)
        self.external_self_widget.slide_images(value)

    def filter_icons_types(self):

        # only versions needed, because last versions always duplicate versionless
        for snapshot in self.versions_icons.itervalues():
            if self.playblast:
                if snapshot[0]['type'] == 'playblast':
                    self.playblast_list.append(snapshot[0])
                if snapshot[0]['type'] == 'web':
                    self.web_list.append(snapshot[0])
                if snapshot[0]['type'] == 'icon':
                    self.icon_list.append(snapshot[0])
            else:
                for t, f in snapshot.files.iteritems():
                    if t == 'main':
                        self.main_list.append(f[0])
                    if t == 'web':
                        self.web_list.append(f[0])
                    if t == 'icon':
                        self.icon_list.append(f[0])

        # reverse to show from last to first
        self.main_list.reverse()
        self.web_list.reverse()
        self.icon_list.reverse()

    def resizeEvent(self, event):
        self.previewGraphicsView.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def slide_images(self, value):

        #     print('this is snapshot', self.slide_images.__func__)

        # print self.nested_item.type
        #
        # print self.nested_item.sobject.process['icon']
        # print self.nested_item.sobject.process['icon'].contexts['icon']
        # print self.nested_item.sobject.process['icon'].contexts['icon'].versions.values()[0].snapshot

        # print self.versions_icons

        # print value - 1
        # print dir(self.nested_item.sobject)
        # print self.nested_item.sobject.process['icon'].contexts['icon'].versions
        if self.nested_item.type == 'snapshot':
            snapshot_repo = self.nested_item.snapshot.get('repo')
            if snapshot_repo:
                repo = env_tactic.get_base_dir(snapshot_repo)
                if repo:
                    asset_dir = gf.form_path(repo['value'][0])
                else:
                    asset_dir = gf.form_path(env_tactic.get_base_dir('client')['value'][0])
            else:
                asset_dir = gf.form_path(env_tactic.get_base_dir('client')['value'][0])

            # asset_dir = env_server.rep_dirs[self.nested_item.snapshot.get('repo')][0]
            if not self.web_list:
                self.web_list = self.playblast_list
            image_path_icon = u'{0}/{1}/{2}'.format(asset_dir,
                                                    self.web_list[value - 1]['relative_dir'],
                                                    self.web_list[value - 1]['file_name'])

            if self.playblast:
                image_path_big = u'{0}/{1}/{2}'.format(asset_dir,
                                                       self.playblast_list[value - 1]['relative_dir'],
                                                       self.playblast_list[value - 1]['file_name'])
            else:
                image_path_big = u'{0}/{1}/{2}'.format(asset_dir,
                                                       self.main_list[value - 1]['relative_dir'],
                                                       self.main_list[value - 1]['file_name'])

            self.preview_image = QtGui.QImage(0, 0, QtGui.QImage.Format_ARGB32)
            if not self.external:
                self.preview_image.load(image_path_big)
            else:
                self.preview_image.load(image_path_icon)

            pix_map = QtGui.QPixmap.fromImage(
                self.preview_image.scaledToWidth(
                    self.parent().playblastGroupBox.width()-3,
                    QtCore.Qt.SmoothTransformation
                )
            )
            self.scene.addPixmap(pix_map)

            self.previewGraphicsView.setScene(self.scene)

            return image_path_big

    def closeEvent(self, event):
        # print('Save Ui_iconsWidget')
        self.deleteLater()
        event.accept()

    def closeEventExt(self, event):
        # print('Save Ui_iconsWidget_ext_window')
        self.ext_window.deleteLater()
        event.accept()
