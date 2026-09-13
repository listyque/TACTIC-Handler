pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                Layout.preferredWidth: 44
                Layout.preferredHeight: 44
                radius: 14
                color: root.theme.secondaryContainer

                Controls.MaterialIcon {
                    anchors.centerIn: parent
                    name: String(dccOptionsController.schema.icon || "deployed_code")
                    size: 22
                    color: root.theme.action
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Label {
                    text: qsTr(dccOptionsController.title)
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }

                Label {
                    Layout.fillWidth: true
                    text: dccOptionsController.targetTitle
                        || dccOptionsController.applicationTitle
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    elide: Text.ElideMiddle
                }
            }
        }

        ScrollView {
            id: optionsScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth
            contentHeight: optionsCard.implicitHeight
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: optionsScroll
            }

            Rectangle {
                id: optionsCard
                width: Math.max(0, optionsScroll.availableWidth - 8)
                implicitHeight: optionsColumn.implicitHeight + 24
                radius: 16
                color: root.theme.surfaceContainerLow
                border.width: 1
                border.color: root.theme.outlineVariant

                ColumnLayout {
                    id: optionsColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.margins: 12

                    Repeater {
                        objectName: "dccActionOptions"
                        model: dccOptionsController.schema.options || []

                        DccSettingField {
                            id: optionDelegate
                            required property var modelData
                            Layout.fillWidth: true
                            theme: root.theme
                            field: optionDelegate.modelData
                            value: dccOptionsController.values[
                                optionDelegate.modelData.key
                            ]
                            onValueEdited: value => dccOptionsController.set_value(
                                optionDelegate.modelData.key, value
                            )
                        }
                    }
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: dccOptionsController.error.length > 0
            text: dccOptionsController.error
            color: root.theme.red
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }

            Controls.Button {
                theme: root.theme
                text: qsTr("Run")
                icon.name: String(
                    dccOptionsController.schema.icon || "play-arrow"
                )
                highlighted: true
                enabled: dccOptionsController.available
                onClicked: dccOptionsController.confirm()
            }
        }
    }
}
