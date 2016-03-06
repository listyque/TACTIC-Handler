# file ui_drop_plate_classes.py

import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import lib.ui.ui_drop_plate as ui_drop_plate
import pyseq

reload(ui_drop_plate)


# seqs = pyseq.get_sequences('//renderserver/Project/UrfinJuse/scenes/ep29/ep29sc27/compose/sequence/tif/v1')
# print(seqs)


def split_files_and_dirs(filename):
    dirs_list = []
    files_list = []
    for single in filename:
        if os.path.isdir(single):
            dirs_list.append(single)
        else:
            files_list.append(extract_filename(single))

    return dirs_list, files_list


def sequences_from_files(files_list):
    print(files_list)


def sequences_from_dirs(files_list):
    print(files_list)


def file_format(ext):
    ext_only = ext.split('.')[-1]
    formats = {
        'ma': 'mayaAscii',
        'mb': 'mayaBinary',
        'hip': 'Houdini',
        '3b': '3D-Coat',
        'max': '3DSMax scene',
        'scn': 'Softimage XSI',
        'mud': 'Mudbox',
        'abc': 'Alembic',
        'obj': 'OBJ',
        '3ds': '3DSMax model',
        'nk': 'Nuke',
        'fbx': 'FBX',
        'dae': 'COLLADA',
        'rs': 'Redshift Proxy',
        'vdb': 'Open VDB',
        'jpg': 'JPEG Image',
        'jpeg': 'JPEG Image',
        'psd': 'Photoshop PSD',
        'tif': 'TIFF Image',
        'tiff': 'TIFF Image',
        'png': 'PNG Image',
        'tga': 'TARGA Image',
        'exr': 'EXR Image',
        'hdr': 'HDR Image',
        'dpx': 'DPX Image',
        'mov': 'MOV Animation',
        'avi': 'AVI Animation',
    }
    if ext_only in formats.iterkeys():
        return formats[ext_only]
    else:
        return ext


def extract_extension(filename):
    ext = unicode(os.path.basename(filename)).split('.', 1)
    if not os.path.isdir(filename):
        if len(ext) > 1:
            return file_format(ext[1])
    elif os.path.isdir(filename):
        return 'Folder'


def extract_filename(filename):
    name = unicode(os.path.basename(filename)).split('.', 1)
    if len(name) > 1:
        return name[0] + '.' + name[1]
    else:
        return name[0]


def extract_dirname(filename):
    dir = unicode(os.path.realpath(filename)).split('.', 1)
    if len(dir) == 1 and not os.path.isdir(filename):
        return dir[0]
    else:
        return os.path.dirname(filename)


class Ui_dropPlateWidget(QtGui.QGroupBox, ui_drop_plate.Ui_dropPlateGroupBox):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.setAcceptDrops(True)

    def append_items_to_tree(self, items):

        file_dir_tuple = split_files_and_dirs(items)
        print(file_dir_tuple)

        for item in items:
            tree_item = QtGui.QTreeWidgetItem()
            tree_item.setText(0, extract_filename(item))
            tree_item.setText(1, extract_extension(item))
            tree_item.setText(2, extract_dirname(item))
            self.dropTreeWidget.addTopLevelItem(tree_item)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(unicode(url.toLocalFile()))
            self.append_items_to_tree(links)
        else:
            event.ignore()
