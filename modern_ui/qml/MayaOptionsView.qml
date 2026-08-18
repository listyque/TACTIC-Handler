import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls"

Item {
    id: root
    required property var theme
    required property string operationMode

    onVisibleChanged: if (visible)
        mayaOptionsController.activate(operationMode)

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12
        RowLayout {
            Layout.fillWidth: true
            Rectangle {
                Layout.preferredWidth: 44
                Layout.preferredHeight: 44
                radius: 14
                color: root.theme.secondaryContainer
                MaterialIcon {
                    anchors.centerIn: parent
                    name: root.operationMode === "open" ? "folder_open"
                        : root.operationMode === "import" ? "input"
                        : "link"
                    size: 22
                    color: root.theme.action
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: qsTr(mayaOptionsController.title)
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    text: mayaOptionsController.fileTitle
                        || qsTr("No snapshot file selected")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.body
                    elide: Text.ElideMiddle
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: root.operationMode === "open" ? 92 : 108
            radius: 16
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 7
                RowLayout {
                    visible: root.operationMode !== "open"
                    Layout.fillWidth: true
                    Label {
                        Layout.fillWidth: true
                        text: root.operationMode === "import"
                            ? qsTr("Import count") : qsTr("Reference count")
                        color: root.theme.primaryText
                        font.pointSize: Typography.body
                    }
                    Md3SpinBox {
                        theme: root.theme
                        from: 1
                        to: 100
                        value: mayaOptionsController.count
                        enabled: mayaOptionsController.available
                        onValueModified: mayaOptionsController.set_count(value)
                    }
                }
                Md3CheckBox {
                    theme: root.theme
                    visible: root.operationMode === "open"
                    text: qsTr("Remember setup working directory preference")
                    checked: mayaOptionsController.setupWorkdir
                    enabled: mayaOptionsController.available
                    onToggled: mayaOptionsController.set_setup_workdir(checked)
                }
                Label {
                    Layout.fillWidth: true
                    text: root.operationMode === "open"
                        ? qsTr("Maya will use its existing save-changes confirmation before opening.")
                        : root.operationMode === "import"
                            ? qsTr("Each copy is imported through the current Maya integration.")
                            : qsTr("Each copy is referenced through the current Maya integration.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                    wrapMode: Text.WordWrap
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: unavailableText.implicitHeight + 24
            visible: mayaOptionsController.unavailableReason.length > 0
            radius: 14
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant
            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                MaterialIcon {
                    name: "info"
                    size: 17
                    color: root.theme.secondaryText
                }
                Label {
                    id: unavailableText
                    Layout.fillWidth: true
                    text: mayaOptionsController.unavailableReason
                    color: root.theme.secondaryText
                    font.pointSize: Typography.label
                    wrapMode: Text.WordWrap
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: mayaOptionsController.error.length > 0
            text: mayaOptionsController.error
            color: root.theme.red
            font.pointSize: Typography.label
            wrapMode: Text.WordWrap
        }
        Item { Layout.fillHeight: true }
        RowLayout {
            Layout.fillWidth: true
            Md3Button {
                theme: root.theme
                visible: checkinOutController.checkoutBusy
                text: qsTr("Cancel operation")
                icon.name: "stop"
                destructive: true
                onClicked: mayaOptionsController.cancel()
            }
            Item { Layout.fillWidth: true }
            Md3Button {
                theme: root.theme
                text: qsTr(mayaOptionsController.title)
                icon.name: root.operationMode === "open" ? "folder_open"
                    : root.operationMode === "import" ? "input" : "link"
                highlighted: true
                enabled: mayaOptionsController.available
                onClicked: confirmation.open()
            }
        }
    }

    Md3Dialog {
        id: confirmation
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: 400
        title: mayaOptionsController.title + "?"
        contentItem: Label {
            width: 352
            text: (mayaOptionsController.fileTitle || qsTr("Selected file"))
                + (root.operationMode === "open" ? ""
                    : qsTr("\nCount: ") + mayaOptionsController.count)
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Confirm")
                highlighted: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onAccepted: mayaOptionsController.confirm()
    }
}
