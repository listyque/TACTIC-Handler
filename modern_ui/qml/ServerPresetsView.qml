import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls"

Item {
    id: root
    required property var theme

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10
        Label {
            text: qsTr("Connection presets")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 16
            font.weight: Font.DemiBold
        }
        Label {
            Layout.fillWidth: true
            text: qsTr("Presets store names only. Credentials remain in the existing authentication storage.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Typography.body
            wrapMode: Text.WordWrap
        }
        RowLayout {
            Layout.fillWidth: true
            Md3TextField {
                id: presetName
                theme: root.theme
                Layout.fillWidth: true
                placeholderText: qsTr("Preset name")
                onAccepted: if (serverPresetsController.add(text)) text = ""
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Add")
                icon.name: "add"
                onClicked: if (serverPresetsController.add(presetName.text))
                    presetName.text = ""
            }
        }
        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: serverPresetsModel
            clip: true
            spacing: 5
            delegate: Rectangle {
                required property int index
                required property string name
                required property bool isProtected
                width: list.width
                height: 48
                radius: 13
                color: root.theme.surfaceContainerLow
                border.width: 1
                border.color: root.theme.outlineVariant
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 9
                    MaterialIcon {
                        name: isProtected ? "lock" : "dns"
                        size: 16
                        color: isProtected ? root.theme.secondaryText : root.theme.action
                    }
                    Label {
                        Layout.fillWidth: true
                        text: name
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.bodyLarge
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "delete"
                        enabled: !isProtected
                        onClicked: serverPresetsController.remove(index)
                    }
                }
            }
            ScrollBar.vertical: Md3ScrollBar { theme: root.theme; flickableTarget: list }
        }
        Label {
            Layout.fillWidth: true
            visible: serverPresetsController.error.length > 0
            text: serverPresetsController.error
            color: root.theme.red
            font.pointSize: Typography.label
        }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: {
                    serverPresetsController.cancel()
                    windowModel.close_window("server_presets")
                }
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Save")
                icon.name: "save"
                highlighted: true
                onClicked: {
                    if (serverPresetsController.save())
                    {
                        configurationController.begin_session()
                        windowModel.close_window("server_presets")
                    }
                }
            }
        }
    }
}
