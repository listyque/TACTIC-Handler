import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    required property string windowId

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 10

        MaterialIcon {
            name: "priority_high"
            size: 28
            color: root.theme.yellow
            Layout.alignment: Qt.AlignHCenter
        }
        Label {
            text: root.windowId === "duplicate_sobject"
                ? qsTr("Duplicate selected sObject?")
                : qsTr("Delete selected sObject?")
            color: root.theme.primaryText
            font.pixelSize: 12
            Layout.alignment: Qt.AlignHCenter
        }
        Label {
            text: root.windowId === "delete_sobject"
                ? (appController.selected_result_count > 1
                    ? appController.selected_result_count
                        + qsTr(" selected items will be removed from TACTIC. ")
                        + qsTr("This cannot be undone.")
                    : qsTr("The item will be removed from TACTIC. ")
                        + qsTr("This cannot be undone."))
                : qsTr("A new server item will be created from the ")
                    + qsTr("selected object.")
            color: root.theme.secondaryText
            font.pointSize: Typography.label
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            Layout.fillWidth: true
        }
        Item { Layout.fillHeight: true }
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Md3Button {
                theme: root.theme
                text: root.windowId === "duplicate_sobject"
                    ? qsTr("Duplicate") : qsTr("Delete")
                destructive: root.windowId !== "duplicate_sobject"
                onClicked: appController.confirm_item_action(root.windowId)
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: windowModel.close_window(root.windowId)
            }
        }
    }
}
