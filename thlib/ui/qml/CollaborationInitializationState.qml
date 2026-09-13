import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    property bool canInitialize: false
    property bool busy: false
    property string error: ""
    property string featureTitle: ""
    property string featureMessage: ""
    property string featureIcon: "database"
    property string projectCode: ""

    signal initializeRequested()

    color: root.theme.workspace

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        hoverEnabled: true
        onWheel: wheel => wheel.accepted = true
    }

    Controls.EmptyState {
        anchors.fill: parent
        visible: !root.busy
        theme: root.theme
        iconName: root.featureIcon
        title: root.featureTitle
        message: root.error.length > 0
            ? root.error
            : root.canInitialize
                ? root.featureMessage
                : qsTr("A TACTIC administrator must initialize these features once.")

        Controls.Button {
            id: initializeButton
            objectName: "collaborationInitializeButton"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 16
            visible: root.canInitialize
            theme: root.theme
            text: qsTr("Initialize Messages and Knowledge Base")
            icon.name: "add-circle"
            highlighted: true
            onClicked: confirmation.open()
        }
    }

    Controls.BusyIndicator {
        anchors.centerIn: parent
        visible: root.busy
        running: visible
        uiTheme: root.theme
    }

    Controls.Dialog {
        id: confirmation
        objectName: "collaborationInitializationConfirmation"
        anchors.centerIn: parent
        width: Math.min(620, Math.max(300, root.width - 32))
        height: Math.min(560, Math.max(300, root.height - 24))
        theme: root.theme
        modal: true
        title: qsTr("Initialize server features?")
        standardButtons: Dialog.NoButton
        focus: true
        onOpened: {
            detailsViewport.contentY = 0
            cancelButton.forceActiveFocus()
        }
        onAccepted: root.initializeRequested()

        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                id: cancelButton
                objectName: "collaborationInitializationCancel"
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: confirmation.reject()
            }
            Controls.Button {
                objectName: "collaborationInitializationConfirm"
                theme: root.theme
                text: qsTr("Initialize")
                icon.name: "add-circle"
                highlighted: true
                onClicked: confirmation.accept()
            }
        }

        contentItem: Flickable {
            id: detailsViewport
            objectName: "collaborationInitializationDetails"
            contentHeight: detailsColumn.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            clip: true

            ColumnLayout {
                id: detailsColumn
                width: Math.max(
                    0, detailsViewport.width
                        - detailsScrollBar.reservedExtent - 4)
                spacing: 12

                Label {
                    Layout.fillWidth: true
                    text: qsTr("This one-time initialization changes the TACTIC server schema for both features:")
                    textFormat: Text.PlainText
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.Wrap
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: messagesDetails.implicitHeight + 24
                    radius: root.theme.itemRadius
                    color: root.theme.surfaceContainer
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    ColumnLayout {
                        id: messagesDetails
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 5
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Messages")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                        }
                        Label {
                            objectName: "collaborationMessagesChange"
                            Layout.fillWidth: true
                            text: qsTr("Adds the text column metadata to sthpw/message and sthpw/message_log. It stores conversation summaries, replies, reactions, pins, forwarding and delivery state.")
                            textFormat: Text.PlainText
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            wrapMode: Text.Wrap
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: knowledgeDetails.implicitHeight + 24
                    radius: root.theme.itemRadius
                    color: root.theme.surfaceContainer
                    border.width: 1
                    border.color: root.theme.outlineVariant

                    ColumnLayout {
                        id: knowledgeDetails
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 5
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Knowledge Base · %1").arg(
                                root.projectCode || qsTr("current project"))
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                        }
                        Label {
                            objectName: "collaborationKnowledgeChange"
                            Layout.fillWidth: true
                            text: qsTr("Creates PROJECT/th_knowledge_article when it is missing, then adds kind, parent_code, content, content_text, sort_order, updated_by and linked_skeys.")
                            textFormat: Text.PlainText
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            wrapMode: Text.Wrap
                        }
                    }
                }

                Label {
                    objectName: "collaborationPreservationNotice"
                    Layout.fillWidth: true
                    text: qsTr("Existing columns and data are kept. Nothing is deleted. The schema changes affect every TACTIC Handler user on this server and project.")
                    textFormat: Text.PlainText
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    wrapMode: Text.Wrap
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                id: detailsScrollBar
                objectName: "collaborationInitializationScrollBar"
                theme: root.theme
                flickableTarget: detailsViewport
            }
        }
    }
}
