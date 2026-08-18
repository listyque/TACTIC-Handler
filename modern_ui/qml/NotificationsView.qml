import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme

    Rectangle { anchors.fill: parent; color: root.theme.workspace }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: qsTr("ACTIVITY & NOTIFICATIONS")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.body
                font.weight: Font.DemiBold
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Clear history")
                icon.name: "delete_sweep"
                enabled: notificationHistoryModel.count() > 0
                onClicked: notificationController.clear_history()
            }
        }

        Label {
            Layout.fillWidth: true
            text: qsTr("Client events and background operations from this session.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Typography.body
            wrapMode: Text.WordWrap
        }

        Flow {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: notificationController.historyGroups
                delegate: Md3Button {
                    required property var modelData
                    theme: root.theme
                    text: modelData.title
                    highlighted: notificationController.historyGroup
                        === modelData.key
                    onClicked: notificationController.set_history_group(
                        modelData.key
                    )
                }
            }
        }

        ListView {
            id: history
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: notificationGroupedHistoryModel
            ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

            delegate: Item {
                id: row
                required property string kind
                required property string group
                required property string message
                required property string detail
                required property string timestamp
                width: history.width
                height: content.implicitHeight + 22

                ItemSurface {
                    anchors.fill: parent
                    theme: root.theme
                    accent: row.kind === "error" ? root.theme.red
                        : row.kind === "warning" ? root.theme.yellow
                        : row.kind === "complete" ? root.theme.green
                        : root.theme.action
                    railVisible: true
                }
                RowLayout {
                    id: content
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    MaterialIcon {
                        name: row.kind === "error" ? "priority_high"
                            : row.kind === "warning" ? "warning"
                            : row.kind === "complete" ? "check_circle"
                            : row.kind === "progress" ? "sync" : "info"
                        size: 19
                        color: row.kind === "error" ? root.theme.red
                            : row.kind === "warning" ? root.theme.yellow
                            : row.kind === "complete" ? root.theme.green
                            : root.theme.action
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 3
                        Label {
                            Layout.fillWidth: true
                            text: row.message
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.bodyLarge
                            wrapMode: Text.WordWrap
                        }
                        Label {
                            Layout.fillWidth: true
                            text: row.group === "repository"
                                ? qsTr("Repository sync")
                                : row.group === "checkin"
                                    ? qsTr("Check-in operations")
                                    : row.group === "server"
                                        ? qsTr("Server transactions")
                                        : qsTr("Client")
                            color: root.theme.action
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.caption
                            font.weight: Font.DemiBold
                        }
                        Label {
                            visible: row.detail.length > 0
                            Layout.fillWidth: true
                            text: row.detail
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.label
                            wrapMode: Text.WordWrap
                        }
                    }
                    Label {
                        text: row.timestamp.replace("T", " ").slice(0, 19)
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.label
                    }
                }
            }

            Label {
                anchors.centerIn: parent
                visible: history.count === 0
                text: qsTr("No events in this group")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Typography.bodyLarge
            }
        }
    }
}
