import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property var hostWindow: root.Window.window

    function localizedErrorType(errorType) {
        const labels = {
            "ticket_error": qsTr("Authentication error"),
            "connection_timeout": qsTr("Connection timeout"),
            "connection_refused": qsTr("Connection refused"),
            "login_pass_error": qsTr("Authentication error"),
            "sql_connection_error": qsTr("Database connection error"),
            "database_query_error": qsTr("Database query error"),
            "protocol_error": qsTr("Protocol error"),
            "server_error": qsTr("Server error"),
            "no_project_error": qsTr("Project error"),
            "attribute_error": qsTr("Attribute error"),
            "type_error": qsTr("Type error"),
            "value_error": qsTr("Value error"),
            "key_error": qsTr("Missing data"),
            "index_error": qsTr("Index error"),
            "file_not_found_error": qsTr("File not found"),
            "permission_error": qsTr("Permission error"),
            "import_error": qsTr("Import error"),
            "runtime_error": qsTr("Runtime error"),
            "assertion_error": qsTr("Assertion error"),
            "os_error": qsTr("Operating system error"),
            "qml_error": qsTr("Interface error")
        }
        return labels[String(errorType || "")]
            || String(debugLog.error_title || debugLog.error_kind || "")
            || qsTr("Application error")
    }

    function localizedErrorMessage(errorType, fallback) {
        const messages = {
            "connection_timeout": qsTr("The TACTIC server is unreachable or did not respond in time. Check the server address, network connection, VPN or proxy, and make sure the server is running. Then try again."),
            "connection_refused": qsTr("A connection to the TACTIC server could not be established. Check the server address, network connection, VPN or proxy, and make sure the server is running. Then try again.")
        }
        return messages[String(errorType || "")] || String(fallback || "")
    }

    component DialogAction: Controls.Button {
        theme: root.theme
        property bool primaryAction: false
        highlighted: primaryAction
    }
    Item {
        anchors.fill: parent


        Rectangle {
            id: dialogSurface
            anchors.fill: parent
            color: root.theme.panel
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

                            Controls.MaterialIcon {
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
                                text: root.hostWindow
                                    ? root.hostWindow.title : debugLog.error_title
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
                                    text: root.localizedErrorType(
                                        debugLog.error_type).toUpperCase()
                                    color: root.theme.red
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    font.weight: Font.Bold
                                }
                            }
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
                                objectName: "errorMessage"
                                anchors.fill: parent
                                anchors.margins: 14
                                text: root.localizedErrorMessage(
                                    debugLog.error_type,
                                    debugLog.error_message)
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.bodyLarge
                                lineHeight: 1.18
                                wrapMode: Text.Wrap
                            }
                        }

                        ColumnLayout {
                            id: commandSection
                            visible: debugLog.error_command.length > 0
                            Layout.fillWidth: true
                            spacing: 7

                            Label {
                                text: qsTr("REQUEST")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
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

                                Controls.TextArea {
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
                                    font.pointSize: Controls.Typography.label
                                    background: Item {}
                                }
                            }
                        }

                        RowLayout {
                            id: stacktraceActions
                            visible: debugLog.error_stacktrace.length > 0
                            Layout.fillWidth: true
                            spacing: 9

                            DialogAction {
                                id: showStacktrace
                                Layout.preferredHeight: 36
                                text: checked
                                    ? qsTr("Hide stacktrace")
                                    : qsTr("Show stacktrace")
                                checkable: true
                                checked: false
                                flat: true
                            }

                            Item { Layout.fillWidth: true }

                            DialogAction {
                                Layout.preferredHeight: 36
                                text: qsTr("Copy stacktrace")
                                objectName: "copyErrorStacktrace"
                                onClicked: debugLog.copy_error_stacktrace()
                            }
                        }

                        Rectangle {
                            visible:
                                stacktraceActions.visible
                                && showStacktrace.checked
                            Layout.fillWidth: true
                            Layout.minimumHeight: 220
                            Layout.preferredHeight: Math.max(
                                220,
                                bodyFlickable.height
                                    - messageLabel.implicitHeight - 28
                                    - (commandSection.visible
                                        ? commandSection.implicitHeight : 0)
                                    - stacktraceActions.implicitHeight
                                    - errorBody.spacing * 3 - 40
                            )
                            radius: 12
                            color: root.theme.workspace
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            ScrollView {
                                anchors.fill: parent
                                anchors.margins: 7
                                clip: true
                                ScrollBar.vertical: Controls.ScrollBar {
                                    theme: root.theme
                                }
                                ScrollBar.horizontal: Controls.ScrollBar {
                                    theme: root.theme
                                }

                                Controls.TextArea {
                                    theme: root.theme
                                    readOnly: true
                                    selectByMouse: true
                                    wrapMode: TextEdit.NoWrap
                                    text: debugLog.error_stacktrace
                                    color: root.theme.secondaryText
                                    font.family: "Consolas"
                                    font.pointSize: Controls.Typography.label
                                    background: Item {}
                                }
                            }
                        }
                    }

                    ScrollBar.vertical: Controls.ScrollBar {
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
                            objectName: "openErrorDebugLog"
                            onClicked: {
                                debugLog.dismiss_error()
                                debugLog.show()
                            }
                        }

                        DialogAction {
                            text: qsTr("Help")
                            onClicked: {
                                debugLog.dismiss_error()
                                windowModel.open_help("errors")
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
                                ? qsTr("Sign In") : qsTr("Configuration")
                            onClicked: debugLog.primary_error_action()
                        }

                        DialogAction {
                            text: qsTr("Dismiss")
                            objectName: "dismissError"
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

    Connections {
        target: debugLog

        function onError_changed() {
            if (debugLog.error_visible)
                showStacktrace.checked = false
        }
    }
}
