import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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
    opacity: dimmed ? 0.38 : 1

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
        visible: !root.isSeparator
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        anchors.topMargin: 4
        anchors.bottomMargin: 4

        Rectangle {
            anchors.fill: parent
            radius: height / 2
            color: root.selected ? root.theme.selected : "transparent"
        }
        Rectangle {
            anchors.fill: parent
            radius: height / 2
            color: root.selected
                ? root.theme.action : root.theme.primaryText
            opacity: rowMouse.pressed ? 0.12
                : rowMouse.containsMouse ? 0.08 : 0
            Behavior on opacity {
                NumberAnimation {
                    duration: rowMouse.containsMouse ? 100 : 140
                    easing.type: Easing.OutCubic
                }
            }
        }
        MaterialRipple {
            id: rowRipple
            shapeRadius: indicator.height / 2
            color: root.selected
                ? Qt.rgba(
                    root.theme.action.r,
                    root.theme.action.g,
                    root.theme.action.b,
                    0.28
                )
                : root.theme.dark ? "#52ffffff" : "#38000000"
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

            MaterialIcon {
                anchors.centerIn: parent
                visible: root.isSection
                name: root.expanded
                    ? "keyboard_arrow_down" : "chevron_right"
                size: 17
                color: root.theme.secondaryText
            }
            ItemPreview {
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
            Layout.fillWidth: true
            text: root.title
            color: root.selected
                ? root.theme.action : root.theme.primaryText
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
                font.pointSize: Typography.body
                font.weight: Font.DemiBold
            }
        }
    }

    MouseArea {
        id: rowMouse
        anchors.fill: indicator
        hoverEnabled: true
        enabled: root.interactive && !root.isSeparator
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onPressed: mouse => rowRipple.burst(mouse.x, mouse.y)
        onClicked: root.activated()
    }
}
