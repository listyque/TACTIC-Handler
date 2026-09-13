import QtQuick
import QtQuick.Dialogs

FileDialog {
    id: root

    property int targetRow: -1
    property bool allowMultiple: false
    signal imageSelected(int row, url image)
    signal imagesSelected(int row, var images)

    title: allowMultiple
        ? qsTr("Choose preview images") : qsTr("Choose preview image")
    fileMode: allowMultiple ? FileDialog.OpenFiles : FileDialog.OpenFile
    nameFilters: [qsTr("Images") + " (*.png *.jpg *.jpeg *.webp *.tif *.tiff *.bmp)"]

    function openForRow(row) {
        targetRow = row
        open()
    }

    onAccepted: {
        const row = targetRow
        targetRow = -1
        const images = allowMultiple ? selectedFiles : [selectedFile]
        imagesSelected(row, images)
        if (!allowMultiple && images.length)
            imageSelected(row, images[0])
    }
    onRejected: targetRow = -1
}
