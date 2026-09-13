import QtQuick
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property string kind
    required property var cell
    signal clicked()

    readonly property var presentation: ({
        "sobject_detail": ["search", qsTr("Open details")],
        "checkin": ["upload", qsTr("Check-in")],
        "explorer": ["folder-open", qsTr("Open folder")],
        "file_list": ["inventory-2", qsTr("Open files")],
        "metadata": ["description", qsTr("Open metadata")],
        "delete": ["delete", qsTr("Delete sObject")]
    })[kind] || ["info", ""]

    Controls.CompactIconButton {
        objectName: root.kind === "checkin" ? "tableCellCheckin"
            : root.kind === "sobject_detail" ? "tableCellSObjectDetail"
            : "tableCellAction_" + root.kind
        anchors.centerIn: parent
        theme: root.theme
        round: true
        iconName: root.presentation[0]
        iconColor: root.kind === "delete"
            ? root.theme.error : root.theme.action
        enabled: root.cell.available !== false
        toolTip: root.presentation[1]
        onClicked: root.clicked()
    }
}
