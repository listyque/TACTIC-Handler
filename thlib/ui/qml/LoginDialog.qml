import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Qt5Compat.GraphicalEffects
import "controls" as Controls

Window {
    id: root

    required property var ownerWindow
    required property var theme
    property bool blocksMainWindow: false

    transientParent: ownerWindow
    modality: blocksMainWindow ? Qt.ApplicationModal : Qt.NonModal
    flags: Qt.Dialog | Qt.FramelessWindowHint
    color: "transparent"
    visible: appController.authentication_dialog_visible
    width: 440
    height: 376
    minimumWidth: 400
    minimumHeight: 350
    title: qsTr("Sign in to TACTIC")
    x: ownerWindow
        ? ownerWindow.x + (ownerWindow.width - width) / 2 : 100
    y: ownerWindow
        ? ownerWindow.y + (ownerWindow.height - height) / 2 : 100

    onVisibleChanged: Qt.callLater(function() {
        if (!root.visible) {
            passwordField.clear()
        } else {
            loginField.text = appController.login_name
            root.requestActivate()
            if (loginField.text.length > 0)
                passwordField.forceActiveFocus()
            else
                loginField.forceActiveFocus()
        }
    })
    onClosing: function(close) {
        close.accepted = false
        appController.cancel_authentication()
    }

    Shortcut {
        sequences: [StandardKey.Cancel]
        enabled: root.visible && !appController.authentication_busy
        onActivated: appController.cancel_authentication()
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
            radius: 28
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant
            clip: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 86

                    Rectangle {
                        anchors.fill: parent
                        radius: dialogSurface.radius
                        color: root.theme.panelRaised
                    }
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: dialogSurface.radius
                        color: root.theme.panelRaised
                    }

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
                                name: "key"
                                size: 23
                                color: root.theme.action
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 3

                            Label {
                                text: qsTr("Sign in to TACTIC")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 17
                                font.weight: Font.DemiBold
                            }
                            Label {
                                Layout.fillWidth: true
                                text: appController.server_url
                                    || qsTr("Configure a server before signing in")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                elide: Text.ElideMiddle
                            }
                        }

                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "close"
                            iconSize: 19
                            round: true
                            toolTip: qsTr("Cancel")
                            enabled: !appController.authentication_busy
                            onClicked: appController.cancel_authentication()
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.theme.outlineVariant
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.leftMargin: 24
                    Layout.rightMargin: 24
                    Layout.topMargin: 20
                    Layout.bottomMargin: 20
                    spacing: 12

                    Label {
                        objectName: "loginAuthenticationMessage"
                        Layout.fillWidth: true
                        visible: appController.authentication_error.length > 0
                        text: qsTr(appController.authentication_error)
                        color: root.theme.error
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        wrapMode: Text.WordWrap
                    }

                    Controls.TextField {
                        id: loginField
                        Layout.fillWidth: true
                        Layout.preferredHeight: 44
                        theme: root.theme
                        placeholderText: qsTr("Login")
                        enabled: !appController.authentication_busy
                    }

                    Controls.TextField {
                        id: passwordField
                        Layout.fillWidth: true
                        Layout.preferredHeight: 44
                        theme: root.theme
                        placeholderText: qsTr("Password")
                        echoMode: TextInput.Password
                        enabled: !appController.authentication_busy
                        onAccepted: generateButton.clicked()
                    }

                    Item { Layout.fillHeight: true }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Controls.BusyIndicator {
                            uiTheme: root.theme
                            visible: appController.authentication_busy
                            running: visible
                            Layout.preferredWidth: 24
                            Layout.preferredHeight: 24
                        }
                        Item { Layout.fillWidth: true }
                        Controls.Button {
                            theme: root.theme
                            text: qsTr("Cancel")
                            flat: true
                            enabled: !appController.authentication_busy
                            onClicked: appController.cancel_authentication()
                        }
                        Controls.Button {
                            id: generateButton
                            theme: root.theme
                            text: appController.authentication_busy
                                ? qsTr("Generating…") : qsTr("Generate ticket")
                            icon.name: "key"
                            highlighted: true
                            enabled: !appController.authentication_busy
                                && loginField.text.trim().length > 0
                                && passwordField.text.length > 0
                            onClicked: appController.authenticate(
                                loginField.text, passwordField.text
                            )
                        }
                    }
                }
            }
        }
    }
}
