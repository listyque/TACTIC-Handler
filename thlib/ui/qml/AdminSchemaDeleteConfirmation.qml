import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id: root

    required property var controller
    readonly property var details: controller.metadata

    objectName: "adminDeleteSearchTypeConfirmation"
    title: qsTr("Delete Search Type from project?")
    modal: true
    focus: true
    width: Math.min(540, parent.width - 24)
    height: Math.min(implicitHeight, parent.height - 24)
    anchors.centerIn: parent
    closePolicy: controller.deleting ? Popup.NoAutoClose : Popup.CloseOnEscape
    standardButtons: Dialog.NoButton
    onOpened: cancelButton.forceActiveFocus()
    onClosed: controller.cancel()

    Connections {
        target: root.controller
        function onCommitted() { root.close() }
    }
    contentItem: Flickable {
        id: viewport
        objectName: "adminDeleteSearchTypeViewport"
        implicitHeight: content.implicitHeight
        contentWidth: width
        contentHeight: content.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ColumnLayout {
            id: content
            width: Math.max(0, viewport.width - scrollBar.reservedExtent - 4)
            spacing: 12
            Label {
                Layout.fillWidth: true
                text: root.controller.deleting ? qsTr("Deleting Search Type…")
                    : root.controller.busy ? qsTr("Checking the table and its dependencies…") : root.controller.error
                visible: text.length > 0
                color: root.controller.error ? root.theme.error : root.theme.secondaryText
                wrapMode: Text.Wrap
            }
            Label {
                objectName: "adminDeleteSearchTypeSummary"
                Layout.fillWidth: true
                visible: !!root.details.table
                text: (root.details.title || "") + "\n" + root.controller.identity + "\n\n"
                    + qsTr("Project: %1 · Table: %2").arg(root.details.project || "").arg(root.details.table || "")
                    + "\n" + qsTr("Search Objects (including retired): %1").arg(root.details.objects || 0)
                    + "\n" + qsTr("Pipelines: %1").arg((root.details.pipelines || []).join(", ") || "—")
                textFormat: Text.PlainText
                color: root.theme.primaryText
                wrapMode: Text.Wrap
            }
            Label {
                objectName: "adminDeleteSearchTypeBlocks"
                Layout.fillWidth: true
                visible: !!root.details.table && !root.controller.canWrite
                text: qsTr("Deletion is blocked. Remove Search Objects and dependencies first, or only remove the node from the canvas.")
                    + "\n" + (root.details.aliases || []).concat(root.details.usedPipelines || [], root.details.otherSchemas || [])
                        .concat((root.details.references || []).map(row => row.type + ": " + row.count)).join("\n")
                textFormat: Text.PlainText
                color: root.theme.error
                wrapMode: Text.Wrap
            }
            Label {
                Layout.fillWidth: true
                visible: root.controller.canWrite
                text: qsTr("This deletes the empty table, empty pipelines and the node with its connections in this project. This editor cannot undo the deletion. Check scripts, naming rules and saved searches that refer to this type.")
                    + (root.details.sharedRegistration ? "\n\n" + qsTr("The shared Search Type registration is kept for other projects, as in TACTIC.") : "")
                color: root.theme.primaryText
                wrapMode: Text.Wrap
            }
            Label {
                Layout.fillWidth: true
                visible: root.controller.canWrite
                text: qsTr("Enter %1 to confirm").arg(root.controller.identity)
                textFormat: Text.PlainText
                color: root.theme.secondaryText
                wrapMode: Text.Wrap
            }
            Controls.TextField {
                objectName: "adminDeleteSearchTypeName"
                Layout.fillWidth: true
                theme: root.theme
                visible: root.controller.canWrite
                enabled: !root.controller.busy
                Accessible.name: qsTr("Search Type identifier")
                text: root.controller.document.confirmation || ""
                onTextEdited: root.controller.set_field("confirmation", text)
            }
        }
        ScrollBar.vertical: Controls.ScrollBar { id: scrollBar; theme: root.theme; flickableTarget: viewport }
    }
    footer: Controls.DialogActions {
        theme: root.theme
        Controls.Button {
            id: cancelButton
            objectName: "adminCancelDeleteSearchType"
            theme: root.theme
            text: qsTr("Cancel")
            enabled: !root.controller.deleting
            onClicked: root.reject()
        }
        Controls.Button {
            objectName: "adminConfirmDeleteSearchType"
            theme: root.theme
            text: qsTr("Delete from project")
            icon.name: "delete"
            destructive: true
            enabled: root.controller.canWrite && !root.controller.busy
                && root.controller.identity.length > 0
                && root.controller.document.confirmation === root.controller.identity
            onClicked: root.controller.save()
        }
    }
}
