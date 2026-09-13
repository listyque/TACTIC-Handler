import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root
    required property var theme
    property var entries: []
    property bool compact: false
    property string title: qsTr("On this page")
    signal headingRequested(var heading)

    implicitWidth: 220
    implicitHeight: root.compact
        ? Math.min(210, 42 + root.entries.length * 30)
        : 260
    radius: root.theme.surfaceRadius
    color: root.theme.surfaceContainerLow
    border.width: 1
    border.color: root.theme.outlineVariant

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Controls.MaterialIcon {
                name: "list-ul"
                size: 15
                color: root.theme.action
            }
            Label {
                objectName: "knowledgeTableOfContentsTitle"
                Layout.fillWidth: true
                text: root.title
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
            }
        }

        Controls.SmoothListView {
            id: outlineList
            objectName: "knowledgeTableOfContents"
            Layout.fillWidth: true
            Layout.fillHeight: true
            theme: root.theme
            model: root.entries
            clip: true
            spacing: 1
            rightMargin: 10

            Controls.ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: outlineList
            }

            delegate: Controls.PopupAction {
                id: headingAction
                required property var modelData
                required property int index
                objectName: "knowledgeTocEntry-" + index
                width: outlineList.width - outlineList.rightMargin
                height: 29
                leftPadding: 7 + Math.max(0, modelData.level - 1) * 11
                rightPadding: 6
                text: String(modelData.title || "")
                background: Rectangle {
                    radius: root.theme.itemRadius
                    color: headingAction.down
                        ? root.theme.selected
                        : headingAction.hovered
                            ? root.theme.rowHover : "transparent"
                }
                contentItem: RowLayout {
                    spacing: 6
                    Controls.MaterialIcon {
                        visible: String(
                            headingAction.modelData.kind || ""
                        ).length > 0
                        name: headingAction.modelData.kind === "section"
                            ? "folder" : "file"
                        size: 14
                        color: headingAction.modelData.kind === "section"
                            ? root.theme.tertiary : root.theme.action
                    }
                    Label {
                        Layout.fillWidth: true
                        text: headingAction.text
                        color: headingAction.enabled
                            ? root.theme.secondaryText
                            : root.theme.disabledText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Number(
                            headingAction.modelData.level
                        ) === 1 ? Font.DemiBold : Font.Normal
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                }
                onClicked: root.headingRequested(modelData)
            }
        }
    }
}
