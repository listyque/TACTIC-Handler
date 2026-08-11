import QtQuick
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    property var model: []
    property string currentValue: ""
    property real segmentWidth: 84
    property real minimumSegmentWidth: 62
    property real contentPadding: 3
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
                readonly property bool selected:
                    String(modelData.value || "") === root.currentValue

                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: root.minimumSegmentWidth
                Layout.preferredWidth: root.segmentWidth
                enabled: modelData.enabled !== false
                padding: 0
                focusPolicy: Qt.TabFocus

                contentItem: Item {
                    Row {
                        id: segmentContent
                        anchors.centerIn: parent
                        spacing: 6

                        MaterialIcon {
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
                            text: segment.modelData.translate === false
                                ? String(segment.modelData.label || "")
                                : qsTr(String(segment.modelData.label || ""))
                            color: !segment.enabled
                                ? root.theme.disabledText
                                : segment.selected
                                    ? root.theme.selectedText
                                    : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 10
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
                    cursorShape: segment.enabled
                        ? Qt.PointingHandCursor : Qt.ArrowCursor
                }

                onClicked: {
                    if (!selected || modelData.reselectable === true)
                        root.activated(String(modelData.value || ""))
                }
            }
        }
    }
}
