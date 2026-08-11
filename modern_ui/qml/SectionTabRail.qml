import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects

Item {
    id: root
    required property var theme
    required property var model
    signal selected(string key)
    signal closed(string key)
    signal reordered(int sourceRow, int targetRow)

    readonly property bool expanded: panelHover.hovered
        || rail.hoveredIndex >= 0 || rail.dragSourceIndex >= 0

    width: 10
    z: 30
    clip: false

    Rectangle {
        id: panel
        width: 52
        height: root.height
        x: root.expanded ? 0 : -(width - root.width)
        color: root.theme.toolBar
        border.width: root.expanded ? 1 : 0
        border.color: root.theme.separator
        radius: root.expanded ? 0 : 4

        Behavior on x {
            NumberAnimation {
                duration: 190
                easing.type: Easing.OutCubic
            }
        }
        Behavior on border.width { NumberAnimation { duration: 120 } }

        HoverHandler {
            id: panelHover
            cursorShape: root.expanded ? Qt.ArrowCursor : Qt.PointingHandCursor
        }

        ListView {
            id: rail
            property int dragSourceIndex: -1
            property int dragTargetIndex: -1
            property int hoveredIndex: -1
            anchors.fill: parent
            anchors.topMargin: 7
            anchors.bottomMargin: 7
            spacing: 3
            clip: false
            model: root.model

            delegate: Item {
                id: tab
                required property int index
                required property string entryKey
                required property string title
                required property string acronym
                required property string accent
                required property bool current
                property int dragTargetIndex: index
                property bool hovered: tabMouse.containsMouse
                property real expandedWidth: Math.max(
                    168, titleLabel.implicitWidth + 66)
                onHoveredChanged: {
                    if (hovered)
                        rail.hoveredIndex = index
                    else if (rail.hoveredIndex === index)
                        rail.hoveredIndex = -1
                }
                property real displacedY: {
                    if (rail.dragSourceIndex < 0 || rail.dragTargetIndex < 0)
                        return 0
                    if (rail.dragSourceIndex < rail.dragTargetIndex
                            && index > rail.dragSourceIndex
                            && index <= rail.dragTargetIndex)
                        return -height - rail.spacing
                    if (rail.dragSourceIndex > rail.dragTargetIndex
                            && index >= rail.dragTargetIndex
                            && index < rail.dragSourceIndex)
                        return height + rail.spacing
                    return 0
                }

                width: hovered ? expandedWidth : rail.width
                height: 42
                z: tabDrag.active ? 10 : 1
                transform: Translate {
                    y: tabDrag.active ? tabDrag.translation.y : tab.displacedY
                    Behavior on y {
                        enabled: !tabDrag.active
                        NumberAnimation {
                            duration: 150
                            easing.type: Easing.OutCubic
                        }
                    }
                }
                Behavior on width {
                    NumberAnimation {
                        duration: 210
                        easing.type: Easing.OutCubic
                    }
                }

                DropShadow {
                    anchors.fill: tabSurface
                    source: tabSurface
                    visible: opacity > 0
                    horizontalOffset: 2
                    verticalOffset: 6
                    radius: 12
                    samples: 25
                    color: root.theme.dark ? "#48000000" : "#30000000"
                    transparentBorder: true
                    opacity: tab.hovered ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: 160 } }
                }

                Rectangle {
                    id: tabSurface
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 4
                    anchors.rightMargin: tab.hovered ? 0 : 4
                    height: 38
                    anchors.verticalCenter: parent.verticalCenter
                    radius: 9
                    color: tabMouse.containsMouse
                        ? root.theme.panelRaised
                        : tab.current ? root.theme.selected : "transparent"
                    border.width: tab.current ? 1 : 0
                    border.color: tab.accent || root.theme.action

                    Behavior on color { ColorAnimation { duration: 110 } }
                    Behavior on anchors.rightMargin {
                        NumberAnimation {
                            duration: 210
                            easing.type: Easing.OutCubic
                        }
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.leftMargin: 5
                        anchors.verticalCenter: parent.verticalCenter
                        width: 0
                        height: 26
                        radius: 3
                        color: tab.accent || root.theme.action
                    }

                    Rectangle {
                        id: badge
                        anchors.left: parent.left
                        anchors.leftMargin: 7
                        anchors.verticalCenter: parent.verticalCenter
                        width: 30
                        height: 30
                        radius: 15
                        color: Qt.darker(
                            tab.accent || root.theme.action,
                            tab.current ? 1.35 : 1.65
                        )
                        border.width: 1
                        border.color: tab.accent || root.theme.action
                        Label {
                            anchors.centerIn: parent
                            text: tab.acronym
                            color: "#f2f2f2"
                            font.family: root.theme.fontFamily
                            font.pixelSize: 8
                            font.weight: Font.DemiBold
                        }
                    }

                    Label {
                        id: titleLabel
                        anchors.left: parent.left
                        anchors.leftMargin: 51
                        anchors.right: parent.right
                        anchors.rightMargin: 8
                        anchors.verticalCenter: parent.verticalCenter
                        text: tab.title
                        color: tab.current
                            ? root.theme.selectedText : root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 11
                        font.weight: tab.current ? Font.Bold : Font.DemiBold
                        elide: Text.ElideRight
                        opacity: tab.hovered && tab.width > 96 ? 1 : 0
                        Behavior on opacity {
                            NumberAnimation { duration: 120 }
                        }
                    }
                }

                Rectangle {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    width: root.expanded ? 0 : 5
                    height: 30
                    radius: 3
                    color: tab.accent || root.theme.action
                    opacity: tab.current ? 1 : 0.68
                    Behavior on width { NumberAnimation { duration: 100 } }
                }

                DragHandler {
                    id: tabDrag
                    target: null
                    enabled: root.expanded
                    acceptedButtons: Qt.LeftButton
                    xAxis.enabled: false
                    onTranslationChanged: {
                        if (!active)
                            return
                        const center = tab.y + tab.height / 2 + translation.y
                        let target = rail.indexAt(rail.width / 2, center)
                        if (target < 0)
                            target = center < 0 ? 0 : rail.count - 1
                        tab.dragTargetIndex = target
                        rail.dragTargetIndex = target
                    }
                    onActiveChanged: {
                        if (active) {
                            tab.dragTargetIndex = tab.index
                            rail.dragSourceIndex = tab.index
                            rail.dragTargetIndex = tab.index
                        } else {
                            const sourceRow = rail.dragSourceIndex
                            const targetRow = rail.dragTargetIndex
                            rail.dragSourceIndex = -1
                            rail.dragTargetIndex = -1
                            if (sourceRow >= 0 && targetRow >= 0
                                    && sourceRow !== targetRow)
                                root.reordered(sourceRow, targetRow)
                        }
                    }
                }

                MouseArea {
                    id: tabMouse
                    anchors.fill: parent
                    enabled: root.expanded && !tabDrag.active
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                    cursorShape: Qt.PointingHandCursor
                    onClicked: function(mouse) {
                        if (mouse.button === Qt.MiddleButton)
                            root.closed(tab.entryKey)
                        else
                            root.selected(tab.entryKey)
                    }
                }
            }

            ScrollBar.vertical: Md3ScrollBar {
                theme: root.theme
                flickableTarget: rail
                visible: root.expanded && rail.contentHeight > rail.height
            }
        }
    }
}
