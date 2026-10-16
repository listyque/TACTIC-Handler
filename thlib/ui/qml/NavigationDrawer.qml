pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/shell/navigation.ui.mjs" as Navigation

Item {
    id: root
    objectName: "navigationDrawer"
    required property var model
    required property var theme
    property string selectedKey: "overview"
    property bool opened: false
    property bool sidebarEditingAvailable: false
    property bool pointerEntered: false
    property Item opener: null
    readonly property var scene: Navigation.describe({
        width: width,
        height: height,
        editable: sidebarEditingAvailable
    }, text => qsTranslate("NavigationDrawer", text))
    readonly property var positions: {
        const result = {};
        for (const item of scene.nodes)
            result[item.id] = item;
        return result;
    }
    readonly property var chrome: ({
            width: scene.width,
            height: scene.height,
            nodes: scene.nodes.filter(item => item.kind !== "View")
        })
    readonly property real drawerWidth: scene.width
    signal selected(string key, string title, string command)
    signal editSidebarRequested

    anchors.fill: parent
    z: 100
    visible: opened || panel.x > -panel.width
    focus: visible

    function open() {
        if (opened)
            return;
        opener = root.Window.window.activeFocusItem;
        pointerEntered = false;
        opened = true;
        forceActiveFocus();
    }
    function close(restoreFocus = true) {
        if (!opened)
            return;
        opened = false;
        if (restoreFocus && opener && opener.visible)
            opener.forceActiveFocus();
    }

    function focusRow(row) {
        list.currentIndex = row;
        list.positionViewAtIndex(row, ListView.Contain);
        list.forceLayout();
        const item = list.itemAtIndex(row) as NavigationEntry;
        if (item)
            item.focusRow();
    }

    function navigateKey(key) {
        const rows = root.model.navigation_rows();
        const active = root.activeFocus ? "" : String(list.currentIndex);
        const result = Navigation.move(rows, active, key);
        if (!result)
            return false;
        const row = Number(result.id);
        if (result.type === "expand" || result.type === "collapse")
            root.model.toggle_section(row);
        else
            root.focusRow(row);
        return true;
    }

    function handleKey(event) {
        const keys = {
            [Qt.Key_Down]: "ArrowDown",
            [Qt.Key_Up]: "ArrowUp",
            [Qt.Key_Left]: "ArrowLeft",
            [Qt.Key_Right]: "ArrowRight",
            [Qt.Key_Home]: "Home",
            [Qt.Key_End]: "End"
        };
        if (!keys[event.key])
            return;
        root.navigateKey(keys[event.key]);
        event.accepted = true;
    }
    Keys.onEscapePressed: close()
    Keys.onPressed: event => root.handleKey(event)

    Rectangle {
        id: scrim
        anchors.fill: parent
        color: root.theme.blackMix
        opacity: root.opened ? 0.32 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: root.opened ? theme.motionExtended : theme.motionSlow
                easing.type: root.opened ? Easing.OutCubic : Easing.InCubic
            }
        }
        MouseArea {
            id: scrimMouse
            anchors.fill: parent
            enabled: root.opened
            hoverEnabled: true
            cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
            preventStealing: true
            onPositionChanged: mouse => {
                if (Navigation.shouldClose(root.pointerEntered, "mouse", mouse.x, root.drawerWidth))
                    root.close();
            }
            onWheel: wheel => wheel.accepted = true
            onClicked: root.close()
        }
    }

    Rectangle {
        id: panel
        width: root.drawerWidth
        height: root.height
        x: root.opened ? 0 : -width
        radius: 0
        color: root.theme.panelRaised
        clip: true
        Behavior on x {
            NumberAnimation {
                duration: root.opened ? theme.motionExtended : theme.motionSlow
                easing.type: root.opened ? Easing.OutCubic : Easing.InCubic
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true
            onWheel: wheel => wheel.accepted = true
        }

        HoverHandler {
            onHoveredChanged: if (hovered)
                root.pointerEntered = true
        }
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            scene: root.chrome
            interactive: false
        }
        Controls.CompactIconButton {
            id: editSidebarButton
            objectName: "editSidebarButton"
            visible: root.sidebarEditingAvailable
            x: root.positions.navigationEdit.x
            y: root.positions.navigationEdit.y
            width: root.positions.navigationEdit.width
            height: root.positions.navigationEdit.height
            theme: root.theme
            iconName: "edit"
            round: true
            toolTip: qsTr("Edit project sidebar")
            onClicked: {
                root.close(false);
                root.editSidebarRequested();
            }
        }
        Controls.CompactIconButton {
            objectName: "navigationCloseButton"
            x: root.positions.navigationClose.x
            y: root.positions.navigationClose.y
            width: root.positions.navigationClose.width
            height: root.positions.navigationClose.height
            theme: root.theme
            iconName: "close"
            round: true
            toolTip: qsTr("Close navigation")
            onClicked: root.close()
        }

        Controls.SmoothListView {
            id: list
            theme: root.theme
            objectName: "navigationList"
            x: root.positions.navigationContent.x
            y: root.positions.navigationContent.y
            width: root.positions.navigationContent.width
            height: root.positions.navigationContent.height
            clip: true
            spacing: 0
            rightMargin: navigationScrollBar.reservedExtent
            boundsBehavior: Flickable.StopAtBounds
            model: root.model

            delegate: NavigationEntry {}

            ScrollBar.vertical: Controls.ScrollBar {
                id: navigationScrollBar
                theme: root.theme
                flickableTarget: list
            }
        }
    }

    component NavigationEntry: FocusScope {
        id: entry
        required property int index
        required property string entryKey
        required property string title
        required property string glyph
        required property string command
        required property int badge
        required property bool available
        required property string entryType
        required property int entryDepth
        required property string accent
        required property bool expanded
        required property bool entryVisible

        width: Math.max(0, list.width - list.rightMargin)
        height: !entryVisible ? 0 : sidebarRow.implicitHeight
        visible: entryVisible
        function focusRow() {
            sidebarRow.forceActiveFocus();
        }
        SidebarTreeRow {
            id: sidebarRow
            focus: true
            anchors.fill: parent
            theme: root.theme
            rowType: entry.entryType
            title: entry.title
            glyph: entry.glyph
            depth: entry.entryDepth
            accent: entry.accent
            expanded: entry.expanded
            selected: entry.entryType === "link" && entry.entryKey === root.selectedKey
            badge: entry.badge
            dimmed: !entry.available
            interactive: entry.available && entry.entryType !== "separator"
            Keys.onPressed: event => root.handleKey(event)
            Accessible.description: entry.available ? "" : unavailableHint.text
            onActiveFocusChanged: if (activeFocus)
                list.currentIndex = entry.index
            onActivated: {
                if (entry.entryType === "section") {
                    root.model.toggle_section(entry.index);
                } else {
                    root.selected(entry.entryKey, entry.title, entry.command);
                    root.close();
                }
            }
        }
        HoverHandler {
            id: unavailableHover
            enabled: !entry.available && entry.entryType === "link"
        }
        Controls.ToolTip {
            id: unavailableHint
            objectName: "sidebarUnavailableHint"
            theme: root.theme
            visible: unavailableHover.hovered
            text: qsTr("This sidebar item has no Search Type. Configure it in Sidebar Editor.")
        }
    }

    Rectangle {
        x: panel.x + panel.width
        width: 14
        height: root.height
        visible: panel.x + panel.width > 0
        opacity: root.opened ? 1 : 0
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop {
                position: 0
                color: root.theme.popupShadow
            }
            GradientStop {
                position: 1
                color: "transparent"
            }
        }
        Behavior on opacity {
            NumberAnimation {
                duration: theme.motionMedium
            }
        }
    }
}
