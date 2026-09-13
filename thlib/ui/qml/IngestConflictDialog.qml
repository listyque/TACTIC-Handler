import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller

    function syncDialog() {
        if (controller.conflictPending && !conflictDialog.opened)
            conflictDialog.open()
        else if (!controller.conflictPending && conflictDialog.opened)
            conflictDialog.close()
    }

    Controls.Dialog {
        id: conflictDialog

        objectName: "ingestConflictDialog"
        readonly property bool compactLayout: width < 480

        theme: root.theme
        parent: root
        title: qsTr("Resolve matching names")
        modal: true
        focus: true
        anchors.centerIn: parent
        width: Math.min(620, Math.max(320, parent.width - 24))
        closePolicy: Popup.CloseOnEscape
        standardButtons: Dialog.NoButton

        contentItem: ColumnLayout {
            spacing: 10

            Label {
                Layout.fillWidth: true
                text: qsTr("%1 file(s) match existing child items or repeat a name in this batch. What should ingest do?")
                    .arg(root.controller.conflictCount)
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.WordWrap
            }
            Label {
                Layout.fillWidth: true
                visible: root.controller.conflictNames.length > 0
                text: qsTr("Conflicts: %1").arg(
                    root.controller.conflictNames.slice(0, 5).join(", "))
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                visible: !root.controller.canUpdateConflicts
                text: qsTr("Update is unavailable because at least one name does not identify exactly one existing item.")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                wrapMode: Text.WordWrap
            }
        }

        footer: Item {
            implicitHeight: actionGrid.implicitHeight + 24

            GridLayout {
                id: actionGrid

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                columns: conflictDialog.compactLayout ? 1 : 2
                columnSpacing: 8
                rowSpacing: 8

                Controls.Button {
                    objectName: "cancelIngestConflictButton"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: root.controller.resolve_ingest_conflict("cancel")
                }
                Controls.Button {
                    objectName: "duplicateIngestConflictButton"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("Create duplicates")
                    icon.name: "content-copy"
                    onClicked: root.controller.resolve_ingest_conflict("duplicates")
                }
                Controls.Button {
                    objectName: "skipIngestConflictButton"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("Skip existing")
                    icon.name: "cancel"
                    highlighted: !root.controller.canUpdateConflicts
                    onClicked: root.controller.resolve_ingest_conflict("skip")
                }
                Controls.Button {
                    objectName: "updateIngestConflictButton"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("Update existing")
                    icon.name: "update"
                    highlighted: root.controller.canUpdateConflicts
                    enabled: root.controller.canUpdateConflicts
                    onClicked: root.controller.resolve_ingest_conflict("update")
                }
            }
        }

        onClosed: {
            if (root.controller.conflictPending)
                root.controller.resolve_ingest_conflict("cancel")
        }
    }

    Connections {
        target: root.controller
        function onStateChanged() { root.syncDialog() }
    }

    Component.onCompleted: Qt.callLater(root.syncDialog)
}
