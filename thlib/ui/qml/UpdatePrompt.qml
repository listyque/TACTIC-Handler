import QtQuick
import QtQuick.Controls
import "controls" as Controls

Item {
    id: root
    required property var theme
    required property var controller
    required property var windows

    Connections {
        target: root.controller
        function onUpdateAvailable(version) {
            prompt.releaseVersion = version
            prompt.open()
        }
    }

    Controls.Dialog {
        id: prompt
        objectName: "availableUpdateDialog"
        theme: root.theme
        property string releaseVersion: ""
        modal: true
        anchors.centerIn: parent
        width: Math.min(420, root.width - 24)
        title: qsTr("Update available")
        contentItem: Label {
            width: Math.max(0, prompt.width - 40)
            text: qsTr("Version %1 is available. Install it now?")
                .arg(prompt.releaseVersion)
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Later")
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
            Controls.Button {
                objectName: "installUpdateButton"
                theme: root.theme
                text: qsTr("Install update")
                highlighted: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
        }
        onAccepted: {
            root.controller.install_selected()
            root.windows.show_window("update")
        }
    }
}
