import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    property string payload: "{}"

    Rectangle { anchors.fill: parent; color: root.theme.workspace }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Rectangle {
                Layout.preferredWidth: 44
                Layout.preferredHeight: 44
                radius: 14
                color: root.theme.secondaryContainer
                Controls.MaterialIcon {
                    anchors.centerIn: parent
                    name: "hub"
                    size: 22
                    color: root.theme.action
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: qsTr("TACTIC Handler Server")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                Label {
                    text: qsTr("Local DCC command router  ·  ")
                        + handlerServerController.endpoint
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
            }
            Label {
                text: handlerServerController.state.toUpperCase()
                color: handlerServerController.state === "running"
                    ? root.theme.green : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "help"
                toolTip: qsTr("DCC clients help")
                onClicked: windowModel.open_help("dcc_clients")
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Start")
                icon.name: "play_arrow"
                highlighted: true
                enabled: handlerServerController.state === "stopped"
                onClicked: handlerServerController.start_server()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Stop")
                icon.name: "stop"
                destructive: true
                enabled: handlerServerController.state !== "stopped"
                onClicked: stopDialog.open()
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            Rectangle {
                SplitView.preferredWidth: 250
                SplitView.minimumWidth: 190
                color: root.theme.panelDeep
                radius: 14
                border.width: 1
                border.color: root.theme.outlineVariant
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("CONNECTED CLIENTS")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: handlerServerController.demoRunning
                                ? "stop" : "deployed_code"
                            toolTip: handlerServerController.demoRunning
                                ? qsTr("Stop simulated Maya client")
                                : qsTr("Start simulated Maya client")
                            enabled: handlerServerController.state === "running"
                            onClicked: handlerServerController.demoRunning
                                ? handlerServerController.stop_demo()
                                : handlerServerController.start_demo()
                        }
                    }
                    ListView {
                        id: clientList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: handlerClientModel
                        clip: true
                        spacing: 4
                        ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
                        delegate: Item {
                            id: clientRow
                            required property int index
                            required property string clientId
                            required property string applicationType
                            required property int processId
                            required property string capabilityText
                            required property bool selected
                            width: clientList.width
                            height: clientContent.implicitHeight + 18
                            Controls.ItemSurface {
                                anchors.fill: parent
                                theme: root.theme
                                selected: clientRow.selected
                                hovered: clientMouse.containsMouse
                                pressed: clientMouse.pressed
                                railVisible: clientRow.selected
                            }
                            ColumnLayout {
                                id: clientContent
                                anchors.fill: parent
                                anchors.margins: 9
                                spacing: 2
                                RowLayout {
                                    Layout.fillWidth: true
                                    Controls.MaterialIcon {
                                        name: clientRow.applicationType === "maya"
                                            ? "view_in_ar" : "description"
                                        size: 17
                                        color: root.theme.action
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: clientRow.clientId
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.body
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    ColumnLayout {
                                        spacing: 0
                                        Label {
                                            visible: clientRow.selected
                                            Layout.alignment: Qt.AlignRight
                                            text: qsTr("ACTIVE")
                                            color: root.theme.action
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.micro
                                            font.weight: Font.DemiBold
                                        }
                                        Label {
                                            Layout.alignment: Qt.AlignRight
                                            text: qsTr("PID ") + clientRow.processId
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.caption
                                        }
                                    }
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: clientRow.capabilityText
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                            MouseArea {
                                id: clientMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: handlerServerController.select_client(
                                    clientRow.index
                                )
                            }
                        }
                        Label {
                            anchors.centerIn: parent
                            visible: clientList.count === 0
                            text: qsTr("No DCC clients connected")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                        }
                    }
                    Controls.Button {
                        Layout.fillWidth: true
                        theme: root.theme
                        text: qsTr("Disconnect selected")
                        icon.name: "link_off"
                        destructive: true
                        enabled: handlerServerController.selectedClient.length > 0
                        onClicked: handlerServerController.disconnect_selected()
                    }
                }
            }

            Item {
                SplitView.fillWidth: true
                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    spacing: 8
                    Label {
                        text: qsTr("COMMAND")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Controls.ComboBox {
                            id: actionChoice
                            Layout.fillWidth: true
                            theme: root.theme
                            model: handlerCapabilityModel
                            textRole: "name"
                            enabled: count > 0
                        }
                        Label {
                            text: qsTr("Timeout (seconds)")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                        }
                        Controls.SpinBox {
                            id: timeoutInput
                            Layout.preferredWidth: 110
                            theme: root.theme
                            from: 1
                            to: 300
                            value: 30
                        }
                        Controls.Button {
                            theme: root.theme
                            text: qsTr("Send")
                            icon.name: "send"
                            highlighted: true
                            enabled: handlerServerController.state === "running"
                                && actionChoice.currentText.length > 0
                            onClicked: handlerServerController.send_command(
                                actionChoice.currentText,
                                payloadEditor.text,
                                timeoutInput.value
                            )
                        }
                    }
                    Controls.TextArea {
                        id: payloadEditor
                        Layout.fillWidth: true
                        Layout.preferredHeight: 105
                        theme: root.theme
                        text: root.payload
                        placeholderText: qsTr("JSON payload")
                        font.family: "Consolas"
                        onTextChanged: root.payload = text
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("RESULTS")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "delete_sweep"
                            toolTip: qsTr("Clear results")
                            onClicked: handlerServerController.clear_results()
                        }
                    }
                    ListView {
                        id: resultList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: handlerResultModel
                        clip: true
                        spacing: 4
                        onCountChanged: if (count > 0) positionViewAtEnd()
                        ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
                        delegate: Item {
                            id: resultRow
                            required property string timestamp
                            required property string target
                            required property string action
                            required property string status
                            required property string summary
                            required property string detail
                            width: resultList.width
                            height: resultContent.implicitHeight + 18
                            Controls.ItemSurface {
                                anchors.fill: parent
                                theme: root.theme
                                accent: resultRow.status === "error"
                                    ? root.theme.red
                                    : resultRow.status === "completed"
                                        ? root.theme.green : root.theme.action
                                railVisible: resultRow.status === "error"
                                    || resultRow.status === "completed"
                            }
                            ColumnLayout {
                                id: resultContent
                                anchors.fill: parent
                                anchors.margins: 9
                                spacing: 3
                                RowLayout {
                                    Layout.fillWidth: true
                                    Label {
                                        text: resultRow.timestamp
                                        color: root.theme.secondaryText
                                        font.family: "Consolas"
                                        font.pointSize: Controls.Typography.caption
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: resultRow.target + "  ·  " + resultRow.action
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.body
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        text: resultRow.status.toUpperCase()
                                        color: resultRow.status === "error"
                                            ? root.theme.red
                                            : resultRow.status === "completed"
                                                ? root.theme.green
                                                : root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                    }
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: resultRow.summary
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    wrapMode: Text.WordWrap
                                }
                                Label {
                                    visible: resultRow.detail.length > 0
                                    Layout.fillWidth: true
                                    text: resultRow.detail
                                    color: root.theme.primaryText
                                    font.family: "Consolas"
                                    font.pointSize: Controls.Typography.caption
                                    wrapMode: Text.WrapAnywhere
                                }
                            }
                        }
                    }
                    Label {
                        visible: handlerServerController.error.length > 0
                        Layout.fillWidth: true
                        text: handlerServerController.error
                        color: root.theme.red
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
    }

    Controls.Dialog {
        id: stopDialog
        theme: root.theme
        anchors.centerIn: parent
        width: 410
        title: qsTr("Stop Handler Server?")
        modal: false
        dim: false
        contentItem: Label {
            width: 362
            text: qsTr("Connected DCC clients and pending requests will be disconnected.")
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Stop")
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
        onAccepted: handlerServerController.stop_server()
    }
}
