# file ui_item_snapshot.py
# Snapshots Item for TreeWidget

import PySide.QtGui as QtGui
import lib.ui.ui_item_snapshot as ui_item
import global_functions as gf

reload(ui_item)


class Ui_snapshotItemWidget(QtGui.QWidget, ui_item.Ui_snapshotItem):
    def __init__(self, snapshot, sobject, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'snapshot'
        self.tree_item = None
        self.item_info = {}
        self.sobject = sobject
        self.snapshot = None
        self.files = {}

        if snapshot:
            self.snapshot = snapshot.values()[0].snapshot
            self.files = snapshot.values()[0].files
        hidden = ['icon', 'web', 'playblast']

        if self.snapshot:
            self.commentLabel.setText(gf.to_plain_text(self.snapshot['description'], 80))
            self.dateLabel.setText(self.snapshot['timestamp'])
            self.authorLabel.setText(self.snapshot['login'] + ':')
            for key, fl in self.files.iteritems():
                if key not in hidden:
                    self.fileNameLabel.setText(fl[0]['file_name'])
                    self.sizeLabel.setText(gf.sizes(fl[0]['st_size']))
        else:
            self.fileNameLabel.setText('Versionless not found')
            self.commentLabel.setText('Check this snapshot, and update versionless')
            self.dateLabel.deleteLater()
            self.sizeLabel.deleteLater()
            self.authorLabel.deleteLater()

        if snapshot:
            self.item_info = self.snapshot

    def get_skey(self, skey=False):
        """skey://sthpw/snapshot?code=SNAPSHOT00000028"""
        if self.snapshot:
            if skey:
                return 'sthpw/snapshot?code={0}'.format(self.snapshot['code'])
            else:
                return 'skey://sthpw/snapshot?code={0}'.format(self.snapshot['code'])
        else:
            return 'No skey for this item!'

    def get_description(self):
        if self.snapshot:
            return self.snapshot['description']
        else:
            return 'No Description for this item!'

    def update_description(self, new_description):
        self.snapshot['description'] = new_description
        self.commentLabel.setText(new_description)