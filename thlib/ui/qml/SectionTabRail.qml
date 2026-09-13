import QtQuick
import QtQuick.Controls
import Qt5Compat.GraphicalEffects
import "controls" as Controls

Item {
    id: root
    required property var theme
    required property var model
    signal selected(string key)
    signal closed(string key)
    signal reordered(int sourceRow, int targetRow)

    property bool hoverLatched: false
    property int revealedIndex: -1
    readonly property bool expanded: hoverLatched || rail.dragSourceIndex >= 0
    readonly property real reservedWidth: 48

    function updateHoverState() {
        const active = panelHover.hovered
            || rail.hoveredIndex >= 0 || rail.dragSourceIndex >= 0
        if (active) {
            collapseTimer.stop()
            hoverLatched = true
        } else if (hoverLatched) {
            collapseTimer.restart()
        }
    }

    Timer {
        id: collapseTimer
        interval: 350
        repeat: false
        onTriggered: {
            if (panelHover.hovered || rail.hoveredIndex >= 0
                    || rail.dragSourceIndex >= 0)
                return
            root.hoverLatched = false
            root.revealedIndex = -1
        }
    }

    width: 320
    z: 30
    clip: false

    Item {
        id: panel
        objectName: "sectionTabPanel"
        width: root.width
        height: root.height

        Rectangle {
            id: panelBackground
            objectName: "sectionTabPanelBackground"
            x: 0
            width: root.reservedWidth
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 5
            color: root.theme.toolBar
            border.width: 0
            radius: 0
            bottomRightRadius: root.theme.surfaceRadius
            antialiasing: true

            HoverHandler {
                id: panelHover
                cursorShape: Qt.PointingHandCursor
                onHoveredChanged: root.updateHoverState()
            }
            WheelHandler {
                target: null
                blocking: true
                enabled: rail.contentHeight > rail.height
                onWheel: function(event) {
                    const delta = event.pixelDelta.y !== 0
                        ? event.pixelDelta.y : event.angleDelta.y / 2
                    const minimumY = rail.originY
                    const maximumY = Math.max(
                        minimumY,
                        minimumY + rail.contentHeight - rail.height
                    )
                    rail.contentY = Math.max(
                        minimumY,
                        Math.min(maximumY, rail.contentY - delta)
                    )
                    event.accepted = true
                }
            }
        }
        ListView {
            id: rail
            objectName: "sectionTabList"
            property int dragSourceIndex: -1
            property int dragTargetIndex: -1
            property int hoveredIndex: -1
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            width: root.width
            interactive: false
            anchors.topMargin: 7
            anchors.bottomMargin: 7
            spacing: 3
            clip: false
            model: root.model

            delegate: Item {
                id: tab
                objectName: "sectionTabDelegate"
                required property int index
                required property string entryKey
                required property string title
                required property string accent
                required property bool current
                required property string glyph
                property int dragTargetIndex: index
                property bool hovered: tabHover.hovered
                    || tabMouse.containsMouse || closeButton.pointerHovered
                property bool revealed: index === root.revealedIndex
                    && (root.hoverLatched || hovered || tabDrag.active)
                property real expandedWidth: Math.min(
                    320, Math.max(260, titleLabel.implicitWidth + 112))
                onHoveredChanged: {
                    if (hovered) {
                        rail.hoveredIndex = index
                        root.revealedIndex = index
                    } else if (rail.hoveredIndex === index) {
                        rail.hoveredIndex = -1
                    }
                    root.updateHoverState()
                }
                HoverHandler {
                    id: tabHover
                    cursorShape: Qt.PointingHandCursor
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

                width: revealed ? expandedWidth : root.reservedWidth
                height: 42
                z: tabDrag.active ? 10 : revealed ? 5 : 1
                Behavior on width {
                    NumberAnimation {
                        duration: theme.motionMedium
                        easing.type: Easing.OutCubic
                    }
                }
                transform: Translate {
                    y: tabDrag.active ? tabDrag.translation.y : tab.displacedY
                    Behavior on y {
                        enabled: !tabDrag.active
                        NumberAnimation {
                            duration: theme.motionMedium
                            easing.type: Easing.OutCubic
                        }
                    }
                }

                Loader {
                    anchors.fill: tabSurface
                    active: tab.revealed
                    sourceComponent: DropShadow {
                        anchors.fill: parent
                        source: tabSurface
                        horizontalOffset: 2
                        verticalOffset: 6
                        radius: 12
                        samples: 25
                        color: root.theme.popupShadow
                        transparentBorder: true
                    }
                }

                Controls.ItemSurface {
                    id: tabSurface
                    objectName: "sectionTabSurface"
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 4
                    anchors.rightMargin: tab.revealed ? 0 : 4
                    height: 38
                    anchors.verticalCenter: parent.verticalCenter
                    theme: root.theme
                    selected: tab.current
                    hovered: tab.revealed
                    pressed: tabMouse.pressed || tabDrag.active
                    accent: tab.accent || root.theme.action
                    railVisible: tab.current
                    railX: width - railWidth
                    railWidth: 3
                    normalColor: root.theme.toolBar
                    selectedColor: root.theme.contentSelection
                    cornerRadius: 9
                    separatorVisible: false
                    animateStateChanges: false
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
                    Controls.MaterialIcon {
                        objectName: "sectionTabIcon"
                        anchors.centerIn: parent
                        name: tab.glyph
                        size: 16
                        color: root.theme.readableText(badge.color)
                    }
                }

                Label {
                    id: titleLabel
                    anchors.left: parent.left
                    anchors.leftMargin: 51
                    anchors.right: closeButton.left
                    anchors.rightMargin: 7
                    anchors.verticalCenter: parent.verticalCenter
                    text: tab.title
                    color: tab.current
                        ? root.theme.selectedText : root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: tab.current ? Font.Bold : Font.DemiBold
                    elide: Text.ElideRight
                    opacity: tab.revealed && tab.width > 96 ? 1 : 0
                    Behavior on opacity {
                        NumberAnimation { duration: theme.hoverMotionFast }
                    }
                }

                DragHandler {
                    id: tabDrag
                    objectName: "sectionTabDragHandler"
                    target: null
                    cursorShape: Qt.PointingHandCursor
                    enabled: root.expanded && !closeButton.pointerHovered
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
                            root.revealedIndex = tab.index
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
                            root.updateHoverState()
                        }
                    }
                }

                MouseArea {
                    id: tabMouse
                    anchors.fill: parent
                    anchors.rightMargin: tab.revealed ? 40 : 0
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

                Controls.CompactIconButton {
                    id: closeButton
                    objectName: "sectionTabCloseButton"
                    anchors.right: parent.right
                    anchors.rightMargin: 7
                    anchors.verticalCenter: parent.verticalCenter
                    width: 32
                    height: 32
                    z: 3
                    visible: tab.revealed && tab.width > 120
                    theme: root.theme
                    iconName: "close"
                    iconSize: 14
                    toolTip: qsTr("Close tab")
                    onClicked: root.closed(tab.entryKey)
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: rail
            }
        }
    }
}
