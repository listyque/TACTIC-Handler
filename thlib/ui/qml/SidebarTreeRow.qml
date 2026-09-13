import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property string rowType: "link"
    property string title: ""
    property string glyph: "link"
    property int depth: 0
    property string accent: ""
    property bool expanded: false
    property bool selected: false
    property int badge: 0
    property bool dimmed: false
    property bool interactive: true

    readonly property bool isSection: rowType === "section"
    readonly property bool isSeparator: rowType === "separator"
    readonly property color itemAccent:
        accent.length > 0 ? accent : theme.action

    signal activated()

    implicitHeight: isSeparator ? 16 : isSection ? 48 : 56
    opacity: dimmed ? 0.5 : 1
    activeFocusOnTab: interactive
    Accessible.role: Accessible.Button
    Accessible.name: title
    Accessible.selected: selected
    Accessible.ignored: isSeparator && !interactive
    Keys.onSpacePressed: if (interactive) activated()
    Keys.onReturnPressed: if (interactive) activated()
    Keys.onEnterPressed: if (interactive) activated()

    Rectangle {
        visible: root.isSeparator
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        height: 1
        color: root.theme.separator
    }

    Item {
        id: indicator
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        anchors.topMargin: 4
        anchors.bottomMargin: 4

        Rectangle {
            objectName: "sidebarRowSurface"
            anchors.fill: parent
            radius: root.theme.itemRadius
            color: root.selected ? root.theme.contentSelection : "transparent"
            border.width: root.activeFocus ? 1 : 0
            border.color: root.theme.action
        }
        Rectangle {
            anchors.fill: parent
            radius: root.theme.itemRadius
            color: root.selected
                ? root.theme.action : root.theme.primaryText
            opacity: rowActivation.pressed ? 0.12
                : rowHover.hovered ? 0.08 : 0
            Behavior on opacity {
                NumberAnimation {
                    duration: rowActivation.pressed
                        ? theme.clickMotionFast
                        : rowHover.hovered
                            ? theme.hoverMotionFast : theme.hoverMotionMedium
                    easing.type: Easing.OutCubic
                }
            }
        }
        Controls.MaterialRipple {
            id: rowRipple
            theme: root.theme
            shapeRadius: root.theme.itemRadius
            color: root.selected
                ? Qt.rgba(
                    root.theme.action.r,
                    root.theme.action.g,
                    root.theme.action.b,
                    0.28
                )
                : root.theme.rippleStrong
        }
    }

    RowLayout {
        visible: !root.isSeparator
        anchors.fill: indicator
        anchors.leftMargin: 16 + root.depth * 16
        anchors.rightMargin: 16
        spacing: 12

        Item {
            Layout.preferredWidth: 32
            Layout.preferredHeight: 32

            Controls.MaterialIcon {
                anchors.centerIn: parent
                visible: root.isSection
                name: root.expanded
                    ? "keyboard_arrow_down" : "chevron_right"
                size: 17
                color: root.theme.secondaryText
            }
            Controls.ItemPreview {
                anchors.centerIn: parent
                visible: !root.isSection
                theme: root.theme
                previewSize: 32
                round: true
                accent: root.itemAccent
                fallbackIcon: root.glyph
                selected: root.selected
            }
        }

        Label {
            objectName: "sidebarRowTitle"
            Layout.fillWidth: true
            text: root.title
            color: root.selected
                ? root.theme.contentSelectionText : root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pixelSize: root.isSection ? 12 : 14
            font.weight: root.isSection
                ? Font.DemiBold : root.selected
                    ? Font.Medium : Font.Normal
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }

        Rectangle {
            visible: root.badge > 0
            Layout.preferredWidth: Math.max(24, badgeLabel.implicitWidth + 12)
            Layout.preferredHeight: 24
            radius: 12
            color: root.selected
                ? root.theme.action : root.theme.rowHover

            Label {
                id: badgeLabel
                anchors.centerIn: parent
                text: root.badge > 99 ? "99+" : root.badge
                color: root.selected
                    ? root.theme.selectedText : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
        }
    }

    HoverHandler {
        id: rowHover
        parent: indicator
        enabled: root.interactive
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
    Controls.ActivationHandler {
        id: rowActivation
        parent: indicator
        enabled: root.interactive
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onPressedChanged: {
            if (pressed)
                rowRipple.burst(point.position.x, point.position.y)
        }
        onActivated: {
            root.forceActiveFocus(Qt.MouseFocusReason)
            root.activated()
        }
    }
}
