import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import "controls" as Controls

ApplicationWindow {
    id: window
    readonly property var backend: typeof thinClientController !== "undefined"
        ? thinClientController : null
    width: 620
    height: 680
    minimumWidth: 480
    minimumHeight: 520
    visible: true
    title: qsTr("Maya Thin Client · ") + (backend ? backend.clientId : "")
    color: theme.workspace

    Theme {
        id: theme
        dark: true
    }
    Material.theme: Material.Dark
    Material.accent: theme.action

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 82
            radius: 18
            color: theme.panelRaised
            border.width: 1
            border.color: theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 12
                Rectangle {
                    Layout.preferredWidth: 48
                    Layout.preferredHeight: 48
                    radius: 15
                    color: theme.secondaryContainer
                    Controls.MaterialIcon {
                        anchors.centerIn: parent
                        name: "deployed_code"
                        size: 24
                        color: theme.action
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        text: qsTr("Maya thin client")
                        color: theme.primaryText
                        font.family: theme.fontFamily
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: qsTr("Simulated DCC environment · ")
                            + (window.backend ? window.backend.endpoint : "Offline")
                        color: theme.secondaryText
                        font.family: theme.fontFamily
                        font.pointSize: Controls.Typography.body
                    }
                }
                Rectangle {
                    Layout.preferredWidth: statusRow.implicitWidth + 20
                    Layout.preferredHeight: 32
                    radius: 16
                    color: theme.secondaryContainer
                    Row {
                        id: statusRow
                        anchors.centerIn: parent
                        spacing: 7
                        Rectangle {
                            anchors.verticalCenter: parent.verticalCenter
                            width: 8
                            height: 8
                            radius: 4
                            color: window.backend && window.backend.connected
                                ? theme.green : theme.red
                        }
                        Label {
                            anchors.verticalCenter: parent.verticalCenter
                            text: window.backend && window.backend.connected
                                ? "CONNECTED" : "OFFLINE"
                            color: theme.secondaryText
                            font.family: theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.DemiBold
                        }
                    }
                }
            }
        }

        Controls.Button {
            Layout.alignment: Qt.AlignRight
            theme: theme
            text: qsTr("Show TACTIC Handler")
            icon.name: "open_in_new"
            highlighted: true
            enabled: window.backend && window.backend.connected
            onClicked: {
                if (window.backend)
                    window.backend.show_handler_window()
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Label {
                text: qsTr("CURRENT SCENE")
                color: theme.secondaryText
                font.family: theme.fontFamily
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
            }
            Label {
                Layout.fillWidth: true
                text: window.backend ? window.backend.currentScene : ""
                color: theme.primaryText
                font.family: theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                elide: Text.ElideMiddle
            }
        }

        Label {
            text: qsTr("REGISTERED ACTIONS")
            color: theme.secondaryText
            font.family: theme.fontFamily
            font.pointSize: Controls.Typography.label
            font.weight: Font.DemiBold
        }

        GridLayout {
            Layout.fillWidth: true
            columns: width >= 560 ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10
            Repeater {
                model: window.backend ? window.backend.scripts : []
                delegate: Rectangle {
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: 86
                    radius: 16
                    color: actionMouse.containsMouse
                        ? theme.rowHover : theme.panel
                    border.width: 1
                    border.color: theme.outlineVariant
                    Behavior on color { ColorAnimation { duration: theme.hoverMotionFast } }

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 10
                        Controls.MaterialIcon {
                            name: modelData.icon
                            size: 22
                            color: theme.action
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label {
                                Layout.fillWidth: true
                                text: modelData.title
                                color: theme.primaryText
                                font.family: theme.fontFamily
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: modelData.description
                                color: theme.secondaryText
                                font.family: theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                    MouseArea {
                        id: actionMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        enabled: window.backend && window.backend.connected
                        onClicked: {
                            if (window.backend)
                                window.backend.run_action(modelData.action)
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: qsTr("RESULT")
                color: theme.secondaryText
                font.family: theme.fontFamily
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
            }
            Controls.Button {
                theme: theme
                text: qsTr("Reconnect")
                icon.name: "sync"
                visible: !window.backend || !window.backend.connected
                onClicked: {
                    if (window.backend)
                        window.backend.reconnect()
                }
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 120
            radius: 16
            color: theme.panelDeep
            border.width: 1
            border.color: theme.outlineVariant
            ScrollView {
                id: resultScrollView
                anchors.fill: parent
                anchors.margins: 10
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: theme
                    flickableTarget: resultScrollView
                }
                Controls.TextArea {
                    theme: theme
                    readOnly: true
                    text: window.backend ? window.backend.resultText : ""
                    color: theme.primaryText
                    font.family: "Consolas"
                    font.pointSize: Controls.Typography.body
                    wrapMode: TextEdit.WrapAnywhere
                    background: null
                    selectByMouse: true
                }
            }
        }
    }
}
