pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "tactic_frame" as Frame
import "tactic_frame/controls/tabs/section.ui.mjs" as Section
import Qt5Compat.GraphicalEffects
import "controls" as Controls
import "tactic_frame/controls/tabs/tab_layout.mjs" as TabLayout
import "tactic_frame/controls/tabs/workspace.ui.mjs" as Workspace

Item {
    id: root
    required property var theme
    required property var model
    signal selected(string key)
    signal closed(string key)
    signal reordered(int sourceRow, int targetRow)

    property bool hoverLatched: false
    property int revealedIndex: -1
    property int focusedIndex: -1
    readonly property bool expanded: hoverLatched || rail.dragSourceIndex >= 0
    readonly property real reservedWidth: Workspace.dimensions.railWidth

    function openSectionMenu(item, x, y) {
        sectionMenu.replaceActions(Section.actions(item.index, rail.count, item.title));
        sectionMenu.sectionKey = item.entryKey;
        sectionMenu.openAt(item, x, y, false);
    }
    Shortcut {
        sequence: "Shift+F10"
        enabled: root.focusedIndex >= 0
        onActivated: {
            const item = rail.itemAtIndex(root.focusedIndex) as SectionTabDelegate;
            if (item)
                root.openSectionMenu(item, 20, item.height / 2);
        }
    }
    function cancelDrag() {
        for (let index = 0; index < rail.count; index++) {
            const item = rail.itemAtIndex(index) as SectionTabDelegate;
            if (item)
                item.cancelSectionDrag();
        }
    }
    Shortcut {
        sequence: "Escape"
        enabled: rail.dragSourceIndex >= 0
        onActivated: root.cancelDrag()
    }
    Connections {
        target: root.model
        function onModelAboutToBeReset() {
            root.cancelDrag();
        }
        function onRowsAboutToBeRemoved() {
            root.cancelDrag();
        }
    }
    Connections {
        target: root.Window.window
        function onActiveChanged() {
            if (!root.Window.window.active)
                root.cancelDrag();
        }
    }
    function updateHoverState() {
        const active = root.focusedIndex >= 0 || panelHover.hovered || rail.hoveredIndex >= 0 || rail.dragSourceIndex >= 0;
        if (active) {
            collapseTimer.stop();
            hoverLatched = true;
        } else if (hoverLatched) {
            collapseTimer.restart();
        }
    }

    Timer {
        id: collapseTimer
        interval: Workspace.dimensions.revealDelay
        repeat: false
        onTriggered: {
            if (root.focusedIndex >= 0 || panelHover.hovered || rail.hoveredIndex >= 0 || rail.dragSourceIndex >= 0)
                return;
            root.hoverLatched = false;
            root.revealedIndex = -1;
        }
    }

    ActionMenu {
        id: sectionMenu
        objectName: "sectionTabActionsMenu"
        property string sectionKey: ""
        theme: root.theme
        frameComposition: true
        preferredWidth: Section.metrics.menuWidth
        onTriggered: command => {
            const rows = root.model.keyboard_rows();
            const index = rows.findIndex(row => row.id === sectionKey);
            if (index < 0)
                return;
            if (command === "close")
                root.closed(sectionKey);
            else {
                const target = index + (command === "up" ? -1 : 1);
                if (target >= 0 && target < rows.length)
                    root.reordered(index, target);
            }
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

        Frame.FrameView {
            id: panelBackground
            objectName: "sectionTabPanelBackground"
            anchors.bottomMargin: Section.metrics.panelBottom
            width: root.reservedWidth
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            theme: root.theme
            interactive: false
            scene: Section.panel(height + Section.metrics.panelBottom, root.theme.surfaceRadius)

            HoverHandler {
                id: panelHover
                cursorShape: Qt.PointingHandCursor
                onHoveredChanged: root.updateHoverState()
            }
            WheelHandler {
                target: null
                blocking: true
                enabled: rail.contentHeight > rail.height
                onWheel: function (event) {
                    const delta = event.pixelDelta.y !== 0 ? event.pixelDelta.y : event.angleDelta.y / 2;
                    const minimumY = rail.originY;
                    const maximumY = Math.max(minimumY, minimumY + rail.contentHeight - rail.height);
                    rail.contentY = Math.max(minimumY, Math.min(maximumY, rail.contentY - delta));
                    event.accepted = true;
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
            anchors.topMargin: Section.metrics.top
            anchors.bottomMargin: Section.metrics.bottom
            spacing: Workspace.dimensions.rowSpacing
            clip: false
            model: root.model

            delegate: SectionTabDelegate {}

            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: rail
            }
        }
    }
    component SectionTabDelegate: Controls.WorkspaceTabInput {
        id: tab
        objectName: "sectionTabDelegate"
        identity: entryKey
        label: title
        selected: current
        vertical: true
        recordsProvider: () => root.model.keyboard_rows()
        onActiveFocusChanged: {
            if (activeFocus) {
                root.focusedIndex = index;
                root.revealedIndex = index;
            } else if (root.focusedIndex === index)
                root.focusedIndex = -1;
            root.updateHoverState();
        }
        Keys.onSpacePressed: root.selected(entryKey)
        Keys.onReturnPressed: root.selected(entryKey)
        onCommand: action => {
            const owner = root, view = rail, id = action.id || tab.entryKey;
            if (action.type === "close")
                owner.closed(id);
            else if (action.type === "reorder")
                owner.reordered(action.source, action.target);
            Qt.callLater(() => {
                const rows = owner.model.keyboard_rows();
                let target = rows.findIndex(row => row.id === id);
                if (target < 0)
                    target = Math.max(0, rows.findIndex(row => row.current));
                view.positionViewAtIndex(target, ListView.Contain);
                view.forceLayout();
                const item = view.itemAtIndex(target);
                if (item)
                    item.forceActiveFocus();
            });
        }
        required property int index
        required property string entryKey
        required property string title
        readonly property color resolvedAccent: accent || root.theme.action
        required property string accent
        required property bool current
        required property string glyph
        property bool dragAborted: false
        function cancelSectionDrag() {
            if (!tabDrag.active)
                return;
            dragAborted = true;
        }
        property int dragTargetIndex: index
        property bool hovered: tabHover.hovered || tabMouse.containsMouse || closeButton.pointerHovered || closeButton.activeFocus
        property bool revealed: index === root.revealedIndex && (root.hoverLatched || hovered || tabDrag.active)
        property real expandedWidth: Section.expandedWidth(titleMetrics.advanceWidth)
        onHoveredChanged: {
            if (hovered) {
                rail.hoveredIndex = index;
                root.revealedIndex = index;
            } else if (rail.hoveredIndex === index) {
                rail.hoveredIndex = -1;
            }
            root.updateHoverState();
        }
        HoverHandler {
            id: tabHover
            cursorShape: Qt.PointingHandCursor
        }

        property real displacedY: TabLayout.displacedTabOffset(index, rail.dragSourceIndex, rail.dragTargetIndex, height + rail.spacing)

        width: revealed ? expandedWidth : root.reservedWidth
        height: Workspace.dimensions.rowHeight
        z: tabDrag.active ? 10 : revealed ? 5 : 1
        Behavior on width {
            NumberAnimation {
                duration: root.theme.motionMedium
                easing.type: Easing.OutCubic
            }
        }
        transform: Translate {
            y: tabDrag.active ? tabDrag.translation.y : tab.displacedY
            Behavior on y {
                enabled: !tabDrag.active
                NumberAnimation {
                    duration: root.theme.motionMedium
                    easing.type: Easing.OutCubic
                }
            }
        }

        TextMetrics {
            id: titleMetrics
            text: tab.title
            font: Qt.font({
                family: root.theme.fontFamily,
                pixelSize: 13,
                weight: tab.current ? Font.Bold : Font.DemiBold
            })
        }
        readonly property var composition: Section.row(width, {
            title: tab.title,
            icon: tab.glyph,
            current: tab.current,
            accent: String(tab.resolvedAccent)
        }, {
            revealed: tab.revealed,
            pressed: tabMouse.pressed || tabDrag.active
        }, root.theme.framePalette)
        Frame.FrameView {
            id: tabVisual
            anchors.fill: parent
            theme: root.theme
            interactive: false
            scene: ({
                    width: tab.width,
                    height: tab.height,
                    nodes: tab.composition.nodes.filter(node => node.kind !== "View")
                })
        }
        Loader {
            x: tab.composition.nodes[0].x
            y: tab.composition.nodes[0].y
            width: tab.composition.nodes[0].width
            height: tab.composition.nodes[0].height
            z: -1
            active: tab.revealed
            sourceComponent: DropShadow {
                anchors.fill: parent
                source: tabVisual.wrapperAt(0) ? tabVisual.wrapperAt(0).control : null
                horizontalOffset: 2
                verticalOffset: 6
                radius: 12
                samples: 25
                color: root.theme.popupShadow
                transparentBorder: true
            }
        }

        DragHandler {
            id: tabDrag
            objectName: "sectionTabDragHandler"
            target: null
            cursorShape: Qt.PointingHandCursor
            enabled: root.expanded && !closeButton.pointerHovered && !tab.dragAborted
            dragThreshold: Section.metrics.dragThreshold
            acceptedButtons: Qt.LeftButton
            xAxis.enabled: false
            onTranslationChanged: {
                if (!active)
                    return;
                const center = tab.y + tab.height / 2 + translation.y;
                const target = Section.targetAt(Array.from({
                    length: rail.count
                }, (_, i) => ({
                            top: i * (tab.height + rail.spacing),
                            bottom: i * (tab.height + rail.spacing) + tab.height
                        })), center);
                tab.dragTargetIndex = target;
                rail.dragTargetIndex = target;
            }
            onActiveChanged: {
                if (active) {
                    tab.dragTargetIndex = tab.index;
                    root.revealedIndex = tab.index;
                    rail.dragSourceIndex = tab.index;
                    rail.dragTargetIndex = tab.index;
                } else {
                    const sourceRow = rail.dragSourceIndex;
                    const targetRow = rail.dragTargetIndex;
                    rail.dragSourceIndex = -1;
                    rail.dragTargetIndex = -1;
                    if (!tab.dragAborted && sourceRow >= 0 && targetRow >= 0 && sourceRow !== targetRow)
                        root.reordered(sourceRow, targetRow);
                    root.updateHoverState();
                }
            }
        }

        MouseArea {
            id: tabMouse
            anchors.fill: parent
            anchors.rightMargin: closeButton.visible ? Section.metrics.closeAllowance : 0
            enabled: !tabDrag.active
            hoverEnabled: true
            pressAndHoldInterval: Section.metrics.holdDelay
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
            cursorShape: Qt.PointingHandCursor
            onPressed: {
                tab.dragAborted = false;
                tab.forceActiveFocus(Qt.MouseFocusReason);
            }
            onPressAndHold: mouse => {
                root.openSectionMenu(tab, mouse.x, mouse.y);
            }
            onClicked: function (mouse) {
                tab.forceActiveFocus(Qt.MouseFocusReason);
                if (mouse.button === Qt.RightButton) {
                    root.openSectionMenu(tab, mouse.x, mouse.y);
                } else if (mouse.button === Qt.MiddleButton)
                    root.closed(tab.entryKey);
                else
                    root.selected(tab.entryKey);
            }
        }

        Controls.CompactIconButton {
            id: closeButton
            objectName: "sectionTabCloseButton"
            x: tab.composition.nodes[5].x
            y: tab.composition.nodes[5].y
            width: tab.composition.nodes[5].width
            height: tab.composition.nodes[5].height
            z: 3
            visible: tab.composition.nodes[5].visible
            theme: root.theme
            iconName: "close"
            iconSize: Section.metrics.closeIconSize
            toolTip: qsTr("Close tab")
            onClicked: root.closed(tab.entryKey)
        }
    }
}
