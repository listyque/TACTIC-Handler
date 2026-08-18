import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Qt5Compat.GraphicalEffects

Window {
    id: root

    required property var ownerWindow
    required property var theme
    property bool blocksMainWindow: false

    component DialogAction: Md3Button {
        theme: root.theme
        property bool primaryAction: false
        highlighted: primaryAction
    }

    transientParent: ownerWindow
    modality: blocksMainWindow ? Qt.ApplicationModal : Qt.NonModal
    flags: Qt.Dialog | Qt.FramelessWindowHint
    color: "transparent"
    visible: debugLog.error_visible
    width: 640
    height: 450
    minimumWidth: 480
    minimumHeight: 330
    title: debugLog.error_title
    x: ownerWindow
        ? ownerWindow.x + (ownerWindow.width - width) / 2 : 100
    y: ownerWindow
        ? ownerWindow.y + (ownerWindow.height - height) / 2 : 100

    onVisibleChanged: {
        if (visible) {
            showStacktrace.checked = false
            requestActivate()
        }
    }
    onClosing: function(close) {
        close.accepted = false
        debugLog.dismiss_error()
    }

    Item {
        anchors.fill: parent

        DropShadow {
            anchors.fill: dialogSurface
            source: dialogSurface
            horizontalOffset: 0
            verticalOffset: 9
            radius: 20
            samples: 41
            color: root.theme.dialogShadow
            transparentBorder: true
        }

        Rectangle {
            id: dialogSurface
            anchors.fill: parent
            anchors.margins: 18
            radius: 30
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant
            clip: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 86
                    color: root.theme.panelRaised

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 20
                        anchors.rightMargin: 14
                        spacing: 14

                        Rectangle {
                            Layout.preferredWidth: 46
                            Layout.preferredHeight: 46
                            radius: 16
                            color: root.theme.surfaceContainerHighest

                            MaterialIcon {
                                anchors.centerIn: parent
                                name: "error"
                                size: 24
                                forceSolid: true
                                color: root.theme.red
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4

                            Label {
                                Layout.fillWidth: true
                                text: debugLog.error_title
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 17
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }

                            Rectangle {
                                Layout.preferredWidth:
                                    errorTypeLabel.implicitWidth + 18
                                Layout.preferredHeight: 24
                                radius: 12
                                color: root.theme.surfaceContainerHighest

                                Label {
                                    id: errorTypeLabel
                                    anchors.centerIn: parent
                                    text: debugLog.error_type
                                        .replace(/_/g, " ").toUpperCase()
                                    color: root.theme.red
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.caption
                                    font.weight: Font.Bold
                                }
                            }
                        }

                        CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            iconSize: 19
                            round: true
                            toolTip: qsTr("Dismiss")
                            onClicked: debugLog.dismiss_error()
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.theme.outlineVariant
                }

                Flickable {
                    id: bodyFlickable
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: width
                    contentHeight: errorBody.implicitHeight + 36
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    ColumnLayout {
                        id: errorBody
                        width: bodyFlickable.width - 48
                        x: 24
                        y: 20
                        spacing: 14

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight:
                                messageLabel.implicitHeight + 28
                            radius: 16
                            color: root.theme.surfaceContainerLow
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            Label {
                                id: messageLabel
                                anchors.fill: parent
                                anchors.margins: 14
                                text: debugLog.error_message
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.bodyLarge
                                lineHeight: 1.18
                                wrapMode: Text.Wrap
                            }
                        }

                        ColumnLayout {
                            visible: debugLog.error_command.length > 0
                            Layout.fillWidth: true
                            spacing: 7

                            Label {
                                text: qsTr("REQUEST")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                                font.weight: Font.DemiBold
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight:
                                    Math.min(110, commandText.implicitHeight + 22)
                                radius: 12
                                color: root.theme.workspace
                                border.width: 1
                                border.color: root.theme.outlineVariant

                                Md3TextArea {
                                    theme: root.theme
                                    id: commandText
                                    anchors.fill: parent
                                    anchors.margins: 7
                                    readOnly: true
                                    selectByMouse: true
                                    wrapMode: TextEdit.WrapAnywhere
                                    text: debugLog.error_command
                                    color: root.theme.action
                                    font.family: "Consolas"
                                    font.pointSize: Typography.label
                                    background: Item {}
                                }
                            }
                        }

                        DialogAction {
                            id: showStacktrace
                            visible: debugLog.error_stacktrace.length > 0
                            Layout.preferredHeight: 36
                            text: checked
                                ? qsTr("Hide stacktrace")
                                : qsTr("Show stacktrace")
                            checkable: true
                            checked: false
                            flat: true
                        }

                        Rectangle {
                            visible:
                                showStacktrace.visible && showStacktrace.checked
                            Layout.fillWidth: true
                            Layout.preferredHeight: 190
                            radius: 12
                            color: root.theme.workspace
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            ScrollView {
                                anchors.fill: parent
                                anchors.margins: 7
                                clip: true
                                ScrollBar.vertical: Md3ScrollBar {
                                    theme: root.theme
                                }
                                ScrollBar.horizontal: Md3ScrollBar {
                                    theme: root.theme
                                }

                                Md3TextArea {
                                    theme: root.theme
                                    readOnly: true
                                    selectByMouse: true
                                    wrapMode: TextEdit.NoWrap
                                    text: debugLog.error_stacktrace
                                    color: root.theme.secondaryText
                                    font.family: "Consolas"
                                    font.pointSize: Typography.label
                                    background: Item {}
                                }
                            }
                        }
                    }

                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: bodyFlickable
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 76
                    color: root.theme.panelRaised

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        height: 1
                        color: root.theme.outlineVariant
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 18
                        anchors.rightMargin: 18
                        spacing: 9

                        DialogAction {
                            text: qsTr("Open Debug Log")
                            onClicked: {
                                debugLog.dismiss_error()
                                debugLog.show()
                            }
                        }

                        Item { Layout.fillWidth: true }

                        DialogAction {
                            visible:
                                debugLog.error_type === "ticket_error"
                                || debugLog.error_type === "login_pass_error"
                                || debugLog.error_type
                                    === "connection_refused"
                                || debugLog.error_type
                                    === "connection_timeout"
                                || debugLog.error_type
                                    === "sql_connection_error"
                                || debugLog.error_type === "protocol_error"
                                || debugLog.error_type === "no_project_error"
                            text:
                                debugLog.error_type === "ticket_error"
                                || debugLog.error_type === "login_pass_error"
                                ? "Sign In" : "Configuration"
                            onClicked: debugLog.primary_error_action()
                        }

                        DialogAction {
                            text: qsTr("Dismiss")
                            onClicked: debugLog.dismiss_error()
                        }

                        DialogAction {
                            visible: debugLog.can_retry
                            text: qsTr("Retry")
                            primaryAction: true
                            onClicked: debugLog.retry_error()
                        }
                    }
                }
            }
        }
    }
}
