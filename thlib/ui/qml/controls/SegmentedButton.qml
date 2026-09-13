import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "." as Controls

Item {
    id: root

    required property var theme
    property var model: []
    property string currentValue: ""
    property real segmentWidth: 84
    property real minimumSegmentWidth: 62
    property real contentPadding: 3
    property bool iconOnly: false
    property string segmentObjectNamePrefix: "segmentedButtonSegment_"
    signal activated(string value)

    readonly property int segmentCount: model && model.length
        ? model.length : 0

    implicitWidth: Math.max(
        minimumSegmentWidth * segmentCount + contentPadding * 2,
        segmentWidth * segmentCount + contentPadding * 2
    )
    implicitHeight: theme.controlHeight

    Rectangle {
        anchors.fill: parent
        radius: Math.min(height / 2, root.theme.itemRadius)
        color: root.theme.surfaceContainerHigh
        border.width: 1
        border.color: root.theme.outlineVariant
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: root.contentPadding
        spacing: 0

        Repeater {
            model: root.model

            delegate: Basic.Button {
                id: segment

                required property var modelData
                objectName: root.segmentObjectNamePrefix + modelData.value
                readonly property bool selected:
                    String(modelData.value || "") === root.currentValue

                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: root.minimumSegmentWidth
                Layout.preferredWidth: root.segmentWidth
                enabled: modelData.enabled !== false
                padding: 0
                focusPolicy: Qt.TabFocus
                Accessible.name: qsTr(String(modelData.label || ""))
                Basic.ToolTip.visible: root.iconOnly && hovered
                Basic.ToolTip.text: Accessible.name

                contentItem: Item {
                    clip: true

                    Row {
                        id: segmentContent
                        anchors.centerIn: parent
                        spacing: 6

                        Controls.MaterialIcon {
                            id: segmentIcon
                            visible: String(segment.modelData.icon || "").length > 0
                            name: String(segment.modelData.icon || "")
                            size: 15
                            color: !segment.enabled
                                ? root.theme.disabledText
                                : segment.selected
                                    ? root.theme.selectedText
                                    : root.theme.secondaryText
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Basic.Label {
                            visible: !root.iconOnly
                            text: segment.modelData.translate === false
                                ? String(segment.modelData.label || "")
                                : qsTr(String(segment.modelData.label || ""))
                            width: Math.min(
                                implicitWidth,
                                Math.max(
                                    0,
                                    segment.width
                                        - (segmentIcon.visible
                                            ? segmentIcon.width
                                                + parent.spacing
                                            : 0)
                                        - 16
                                )
                            )
                            elide: Text.ElideRight
                            maximumLineCount: 1
                            color: !segment.enabled
                                ? root.theme.disabledText
                                : segment.selected
                                    ? root.theme.selectedText
                                    : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.body
                            font.weight: segment.selected
                                ? Font.DemiBold : Font.Medium
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                background: Rectangle {
                    radius: Math.max(3, root.theme.itemRadius - 2)
                    color: !segment.enabled
                        ? "transparent"
                        : segment.down
                            ? root.theme.surfaceContainerHighest
                            : segment.selected
                                ? root.theme.selected
                                : segment.hovered
                                    ? root.theme.rowHover : "transparent"

                }

                HoverHandler {
                    cursorShape: Qt.PointingHandCursor
                }

                onClicked: {
                    if (!selected || modelData.reselectable === true)
                        root.activated(String(modelData.value || ""))
                }
            }
        }
    }
}
