import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    required property var theme
    color: theme.workspace

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: Math.min(230, Math.max(170, root.width * 0.28))
            Layout.fillHeight: true
            color: root.theme.surfaceContainerLow

            ListView {
                anchors.fill: parent
                anchors.margins: 7
                spacing: 4
                clip: true
                model: workReportModel
                delegate: Rectangle {
                    required property string key
                    required property string title
                    required property string description
                    required property string icon
                    required property string permission
                    required property bool selected
                    readonly property bool allowed:
                        permission === "user"
                        || permission === "supervisor"
                            && workHoursController.canManage
                        || permission === "finance"
                            && workHoursController.canViewCosts
                    width: ListView.view.width
                    height: 54
                    radius: root.theme.itemRadius
                    color: selected
                        ? root.theme.primaryContainer
                        : reportMouse.containsMouse
                            ? root.theme.rowHover : "transparent"
                    opacity: allowed ? 1 : 0.45

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8
                        MaterialIcon {
                            name: icon
                            size: 18
                            color: selected
                                ? root.theme.action : root.theme.secondaryText
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1
                            Label {
                                Layout.fillWidth: true
                                text: title
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: description
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.micro
                                elide: Text.ElideRight
                            }
                        }
                    }
                    MouseArea {
                        id: reportMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: parent.allowed
                        cursorShape: enabled
                            ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onClicked: workHoursController.select_report(key)
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: root.theme.workspace

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 9
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 34
                    Label {
                        Layout.fillWidth: true
                        text: String(workHoursController.selectedReport || "")
                            .replace(/_/g, " ").toUpperCase()
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.bodyLarge
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: workHoursController.weekStart + " — "
                            + workHoursController.weekEnd
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.caption
                    }
                    RefreshIconButton {
                        theme: root.theme
                        toolTip: qsTr("Refresh report")
                        onClicked: workHoursController.refresh_report()
                    }
                }

                Label {
                    visible: workHoursController.reportMessage.length > 0
                    Layout.fillWidth: true
                    text: workHoursController.reportMessage
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Typography.label
                    wrapMode: Text.WordWrap
                }

                SmoothListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 6
                    clip: true
                    model: workReportValueModel
                    delegate: Rectangle {
                        required property string label
                        required property string valueLabel
                        required property real share
                        width: ListView.view.width
                        height: 52
                        radius: root.theme.itemRadius
                        color: root.theme.surfaceContainerLow

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 10
                            Label {
                                Layout.preferredWidth: Math.min(
                                    180, parent.width * 0.34
                                )
                                text: label
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                                elide: Text.ElideRight
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 6
                                radius: 3
                                color: root.theme.surfaceContainerHighest
                                Rectangle {
                                    width: parent.width * Math.max(
                                        0, Math.min(1, share)
                                    )
                                    height: parent.height
                                    radius: parent.radius
                                    color: root.theme.action
                                }
                            }
                            Label {
                                Layout.preferredWidth: 70
                                text: valueLabel
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.body
                                font.weight: Font.DemiBold
                                horizontalAlignment: Text.AlignRight
                            }
                        }
                    }
                }
            }
        }
    }

    Component.onCompleted: workHoursController.refresh_report()
}
