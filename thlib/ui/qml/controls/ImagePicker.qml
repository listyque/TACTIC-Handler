import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

GridLayout {
    id: root

    required property var theme
    required property url previewUrl
    required property string stagedPath
    property string objectNamePrefix: "imagePicker"
    property string statusText: ""
    property string description: ""
    property string fallbackText: ""
    property string dialogTitle: qsTr("Choose preview image")
    property color accent: theme.action
    property real previewSize: 112
    readonly property bool compact: width < previewSize + 290
    signal selectionRequested(url image)

    columns: compact ? 1 : 2
    columnSpacing: 16
    rowSpacing: 12

    Controls.ItemPreview {
        objectName: root.objectNamePrefix + "Preview"
        Layout.preferredWidth: root.previewSize
        Layout.preferredHeight: root.previewSize
        theme: root.theme
        previewSize: root.previewSize
        decodeAtItemSize: true
        cornerRadius: root.theme.itemRadius
        outlined: true
        effectsEnabled: false
        accent: root.accent
        source: root.previewUrl
        fallbackText: root.fallbackText
    }
    ColumnLayout {
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        Label {
            Layout.fillWidth: true
            text: root.statusText
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WordWrap
        }
        Label {
            Layout.fillWidth: true
            visible: root.description.length > 0
            text: root.description
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }
        Controls.Button {
            objectName: root.objectNamePrefix + "ChoosePreview"
            theme: root.theme
            text: qsTr("Choose image")
            icon.name: "add-photo-alternate"
            onClicked: dialog.open()
        }
        Controls.Button {
            objectName: root.objectNamePrefix + "CancelPreview"
            visible: root.stagedPath.length > 0
            theme: root.theme
            text: qsTr("Undo image selection")
            icon.name: "undo"
            onClicked: root.selectionRequested("")
        }
    }
    Controls.ImageFileDialog {
        id: dialog
        objectName: root.objectNamePrefix + "PreviewDialog"
        title: root.dialogTitle
        onImageSelected: (row, image) => root.selectionRequested(image)
    }
}
