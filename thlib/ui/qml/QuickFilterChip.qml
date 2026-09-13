import QtQuick
import QtQuick.Controls
import "controls" as Controls

Controls.PopupAction {
    id: root

    required property var theme
    property string iconName: ""
    property color accent: theme.action
    property bool showAccentMarker: false
    property bool subtle: false
    property real cornerRadius: height / 2
    property real emphasis: 0
    property real maximumChipWidth: 10000
    readonly property real desiredContentWidth:
        chipLabel.implicitWidth
        + (iconName.length > 0 ? 16 : 0)
        + (showAccentMarker ? 13 : 0)

    implicitWidth: Math.min(
        maximumChipWidth, desiredContentWidth + 24
    )
    implicitHeight: 32 + Math.round(Math.max(0, emphasis) * 12)
    hoverEnabled: true
    checkable: false
    padding: 0
    Accessible.name: text

    background: Rectangle {
        id: chipSurface
        radius: root.cornerRadius
        antialiasing: true
        color: root.checked
            ? root.subtle
                ? Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.16)
                : root.accent
            : "transparent"
        border.width: 1
        border.color: root.checked ? root.accent : root.theme.outline

        Behavior on color {
            ColorAnimation { duration: theme.clickMotionFast }
        }
        Behavior on border.color {
            ColorAnimation { duration: theme.clickMotionFast }
        }

        Controls.MaterialRipple {
            id: chipRipple
            theme: root.theme
            color: root.theme.rippleStrong
            shapeRadius: chipSurface.radius
        }
    }

    contentItem: Item {
        Row {
            id: chipContent

            anchors.centerIn: parent
            width: Math.min(
                root.desiredContentWidth,
                Math.max(0, parent.width - 20)
            )
            spacing: root.iconName.length > 0
                || root.showAccentMarker ? 5 : 0

            Rectangle {
                id: accentMarker
                objectName: "quickFilterAccentMarker"
                anchors.verticalCenter: parent.verticalCenter
                visible: root.showAccentMarker
                width: 8
                height: 8
                radius: 4
                antialiasing: true
                color: root.accent
            }

            Controls.MaterialIcon {
                anchors.verticalCenter: parent.verticalCenter
                visible: root.iconName.length > 0
                name: root.iconName
                size: 11 + Math.round(Math.max(0, root.emphasis) * 4)
                color: root.checked && root.subtle
                    ? root.accent
                    : root.checked
                        ? root.theme.selectedText
                        : root.theme.secondaryText
            }
            Label {
                id: chipLabel
                anchors.verticalCenter: parent.verticalCenter
                width: Math.min(
                    implicitWidth,
                    Math.max(0, chipContent.width
                        - (root.iconName.length > 0 ? 16 : 0)
                        - (root.showAccentMarker ? 13 : 0))
                )
                text: root.text
                color: root.checked
                    ? root.subtle
                        ? root.theme.primaryText
                        : root.theme.selectedText
                    : root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                    + Math.round(Math.max(0, root.emphasis) * 8)
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
        }
    }

    onPressedChanged: {
        if (pressed)
            chipRipple.burst(width / 2, height / 2)
    }

}
