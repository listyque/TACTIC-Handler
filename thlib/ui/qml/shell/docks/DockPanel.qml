pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Window
import "../.."
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../../tactic_frame/controls/tabs/tab_layout.mjs" as TabLayout
import "../../tactic_frame/shell/dock_chrome.ui.mjs" as DockChrome
import "../../tactic_frame/shell/dock.placement.mjs" as Placement
import "../../tactic_frame/shell/dock.layout.mjs" as DockLayout
import "../../tactic_frame/shell/dock.keys.mjs" as DockKeys

Item {
    id: root
    objectName: "dockPanel_" + panelId
    required property var host
    required property var theme
    required property string panelId
    required property string title
    required property string kind
    required property real panelX
    required property real panelY
    required property real panelWidth
    required property real panelHeight
    required property bool modelVisible
    required property bool panelOpen
    required property bool stackActive
    required property bool closable
    required property int stackOrder
    required property string dockArea
    required property bool canResizeLeft
    required property bool canResizeRight
    required property bool canResizeTop
    required property bool canResizeBottom
    required property var stackPanels
    required property int stackSize
    required property Component contentComponent
    property string descriptionTitle: "Description"
    property bool retainContent: false
    property bool tabDragging: false
    property int tabDragEpoch: 0

    function cancelTabDrag() {
        tabDragEpoch++;
        tabDragging = false;
    }
    Shortcut {
        sequence: "Escape"
        enabled: root.tabDragging
        context: Qt.WindowShortcut
        onActivated: root.cancelTabDrag()
    }

    component StackTab: Item {
        id: stackTab
        required property var modelData
        required property int index
        objectName: "dockTab_" + root.panelId + "_" + record.panelId
        activeFocusOnTab: record.active
        Accessible.role: Accessible.PageTab
        Accessible.name: tabLabel.titleText
        Accessible.selected: record.active
        Keys.onPressed: event => root.tabKey(record.panelId, event)
        property var record: modelData
        property int targetIndex: index
        property bool hovered: tabHover.hovered
        width: TabLayout.dockTabWidth(tabLabel.implicitWidth, stackTabBar.width, root.stackSize)
        height: stackTabsRow.height
        z: (tabDrag.active && tabDrag.epoch === root.tabDragEpoch) ? 10 : 1
        transform: Translate {
            x: (tabDrag.active && tabDrag.epoch === root.tabDragEpoch) ? tabDrag.translation.x : 0
        }

        Rectangle {
            anchors.fill: parent
            color: root.theme.action
            opacity: (tabDrag.active && tabDrag.epoch === root.tabDragEpoch) ? TabLayout.dockTab.draggingOpacity : stackTab.record.active ? TabLayout.dockTab.selectedOpacity : stackTab.hovered ? TabLayout.dockTab.hoveredOpacity : 0
        }
        Rectangle {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            width: stackTab.record.active ? Math.max(TabLayout.dockTab.indicatorMinimum, parent.width - TabLayout.dockTab.indicatorInset * 2) : 0
            height: TabLayout.dockTab.indicatorThickness
            radius: height / 2
            color: root.theme.action
            opacity: stackTab.record.active ? 1 : 0
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 4
            spacing: 6
            Controls.MaterialIcon {
                name: root.panelIcon(stackTab.record.kind)
                size: 14
                color: stackTab.record.active ? root.theme.action : root.theme.secondaryText
            }
            DockTitleLabel {
                id: tabLabel
                Layout.fillWidth: true
                theme: root.theme
                titleText: root.localizedPanelTitle(stackTab.record.kind, stackTab.record.kind === "description" ? root.descriptionTitle : stackTab.record.title)
                active: stackTab.record.active
            }
        }
        HoverHandler {
            id: tabHover
            cursorShape: Qt.PointingHandCursor
        }
        Controls.ActivationHandler {
            onActivated: dockModel.activate_stack_panel(stackTab.record.panelId)
        }
        DragHandler {
            id: tabDrag
            property int epoch: -1
            target: null
            acceptedButtons: Qt.LeftButton
            dragThreshold: TabLayout.dockTab.dragThreshold
            onTranslationChanged: {
                const centers = [];
                for (let itemIndex = 0; itemIndex < stackTabRepeater.count; ++itemIndex) {
                    const item = stackTabRepeater.itemAt(itemIndex);
                    centers.push(item.x + item.width / 2);
                }
                stackTab.targetIndex = DockLayout.tabTarget(centers, index, translation.x);
            }
            onActiveChanged: {
                root.tabDragging = active;
                if (active)
                    epoch = root.tabDragEpoch;
            }
            onGrabChanged: (transition, point) => {
                if (transition !== PointerDevice.UngrabExclusive || epoch !== root.tabDragEpoch)
                    return;
                const identity = stackTab.record.panelId;
                const destination = stackTab.targetIndex;
                const position = index;
                stackTab.targetIndex = position;
                if (Math.abs(translation.y) > titleBar.height) {
                    dockModel.float_panel_inside(identity);
                } else if (destination !== position) {
                    dockModel.reorder_stack_panel(identity, destination);
                }
            }
        }
    }

    function focusTab(identity) {
        if (!root.visible || !root.stackActive)
            return false;
        for (let index = 0; index < stackTabRepeater.count; index++) {
            const item = stackTabRepeater.itemAt(index) as StackTab;
            if (!item.visible || item.record.panelId !== identity)
                continue;
            item.forceActiveFocus(Qt.TabFocusReason);
            stackTabsFlick.contentX = Math.max(0, Math.min(item.x, stackTabsFlick.contentWidth - stackTabsFlick.width));
            return true;
        }
        if (root.panelId !== identity)
            return false;
        root.forceActiveFocus(Qt.TabFocusReason);
        return true;
    }
    function closeDock(identity) {
        const records = root.stackPanels.map(record => ({
                    id: record.panelId,
                    closable: record.closable
                }));
        const next = DockKeys.neighbor(records, identity);
        let focus = root.Window.window ? root.Window.window.activeFocusItem : null;
        while (focus && focus !== root)
            focus = focus.parent;
        const restore = focus === root;
        const owner = root.host;
        dockModel.close_panel(identity);
        if (next)
            dockModel.activate_stack_panel(next);
        if (restore)
            Qt.callLater(() => owner.focusDockTab(next));
    }
    function tabKey(identity, event) {
        const names = {};
        names[Qt.Key_Left] = "ArrowLeft";
        names[Qt.Key_Right] = "ArrowRight";
        names[Qt.Key_Home] = "Home";
        names[Qt.Key_End] = "End";
        names[Qt.Key_Delete] = "Delete";
        names[Qt.Key_Return] = "Enter";
        names[Qt.Key_Enter] = "Enter";
        names[Qt.Key_Space] = " ";
        const records = root.stackPanels.map(record => ({
                    id: record.panelId,
                    closable: record.closable
                }));
        const command = DockKeys.action(records, identity, names[event.key] || "", !!(event.modifiers & Qt.ControlModifier) && !!(event.modifiers & Qt.ShiftModifier));
        if (!command)
            return;
        event.accepted = true;
        if (command.type === "close") {
            root.closeDock(identity);
            return;
        }
        const owner = root.host;
        if (command.type === "reorder")
            dockModel.reorder_stack_panel(identity, command.target);
        else
            dockModel.activate_stack_panel(command.id);
        Qt.callLater(() => owner.focusDockTab(command.id));
    }

    function syncPanelContent() {
        if (root.panelOpen) {
            root.retainContent = true;
        }
    }

    onPanelOpenChanged: syncPanelContent()
    Component.onCompleted: {
        syncPanelContent();
        initializeGeometry();
    }

    WindowSizing {
        id: sizing
    }

    // Align adjacent normalized dock rectangles to the same physical pixel.
    // Calculating width from independently rounded fractions can otherwise
    // leave a one-pixel strip at the right or bottom edge while resizing.
    function scaledX() {
        return host ? Math.round(panelX * host.width) : 0;
    }
    function scaledY() {
        return host ? Math.round(panelY * host.height) : 0;
    }
    function scaledRight() {
        if (!host)
            return 0;
        return panelX + panelWidth >= 0.999999 ? host.width : Math.round((panelX + panelWidth) * host.width);
    }
    function scaledBottom() {
        if (!host)
            return 0;
        return panelY + panelHeight >= 0.999999 ? host.height : Math.round((panelY + panelHeight) * host.height);
    }
    function scaledWidth() {
        return host ? Math.max(0, scaledRight() - scaledX()) : 0;
    }
    function scaledHeight() {
        return host ? Math.max(0, scaledBottom() - scaledY()) : 0;
    }

    property real localX: scaledX()
    property real localY: scaledY()
    property real localWidth: scaledWidth()
    property real localHeight: scaledHeight()
    property real dragStartX: 0
    property real dragStartY: 0
    property real resizeStartWidth: 0
    property real resizeStartHeight: 0
    property real resizeStartX: 0
    property real resizeStartY: 0
    property real resizePressHostX: 0
    property real resizePressHostY: 0
    property string resizeEdge: ""
    property bool resizing: false
    property real lastPointerX: 0
    property real lastPointerY: 0
    property real manualDragX: 0
    property real manualDragY: 0
    property real handlePressHostX: 0
    property real handlePressHostY: 0
    property bool dockDragging: resultsDragHandle.dragActive || dockMoveHandle.dragActive
    property bool geometryTransitionsReady: false
    property bool resultsDragHandleVisible: true
    readonly property real chromeInset: dockArea === "floating" ? DockChrome.dimensions.floatingSurfaceInset : DockChrome.dimensions.surfaceInset
    readonly property var chrome: DockChrome.describe({
        width: panelBody.width,
        kind: root.kind,
        stackSize: root.stackSize,
        closable: root.closable,
        floating: root.dockArea === "floating",
        leadingStackInset: resultsDragHandle.visible ? resultsDragHandle.width + 6 : 6,
        capabilities: {
            separateWindow: true,
            queueOwnChrome: true
        }
    })
    readonly property var chromeControls: DockChrome.positions(chrome)
    readonly property real minimumPanelWidth: Math.min(sizing.dockMinimumWidth(root.kind), root.host.width)
    readonly property real minimumPanelHeight: Math.min(sizing.dockMinimumHeight(root.kind), root.host.height)
    readonly property bool resizeHighlighted: {
        if (!host || typeof host.dockSharesActiveResize !== "function")
            return resizing;
        return host.dockSharesActiveResize(panelId, localX, localY, localWidth, localHeight);
    }

    function panelIcon(panelKind) {
        return panelKind === "snapshot" ? "movie" : panelKind === "tasks" ? "tasks" : panelKind === "task_calendar" ? "calendar-month" : panelKind === "drop_plate" || panelKind === "commit_queue" ? "publish" : panelKind === "notes" ? "comment" : panelKind === "knowledge" ? "book-open" : panelKind === "advanced_search" ? "search" : panelKind === "repo_sync_queue" ? "repository-sync" : panelKind === "watch_folders" ? "folder" : panelKind === "description" ? "description" : "view_kanban";
    }

    function localizedPanelTitle(panelKind, fallbackTitle) {
        if (panelKind === "results")
            return qsTr("Search");
        if (panelKind === "snapshot")
            return qsTr("Snapshots");
        if (panelKind === "tasks")
            return qsTr("Tasks");
        if (panelKind === "task_calendar")
            return qsTr("Task Calendar");
        if (panelKind === "timesheet")
            return qsTr("Timesheet");
        if (panelKind === "work_reports")
            return qsTr("Work Reports");
        if (panelKind === "cost_reports")
            return qsTr("Cost Reports");
        if (panelKind === "notes")
            return qsTr("Task Inspector");
        if (panelKind === "knowledge")
            return qsTr("Knowledge Base");
        if (panelKind === "drop_plate")
            return qsTr("Drop Plate");
        if (panelKind === "advanced_search")
            return qsTr("Advanced Search");
        if (panelKind === "watch_folders")
            return qsTr("Watch Folders");
        if (panelKind === "db_table")
            return qsTr("Database Editor");
        if (panelKind === "description") {
            const value = String(fallbackTitle || "");
            const prefix = "Description";
            return qsTr("Description") + (value.indexOf(prefix) === 0 ? value.slice(prefix.length) : "");
        }
        // Unknown titles can be project- or extension-defined data and must
        // remain unchanged rather than being passed to the app translator.
        return String(fallbackTitle || "");
    }

    function openDockHelp() {
        windowModel.open_help("dock." + root.kind);
    }

    x: dockDragging ? Math.max(0, Math.min(host.width - width, dragStartX + manualDragX)) : localX
    y: dockDragging ? Math.max(0, Math.min(host.height - height, dragStartY + manualDragY)) : localY
    width: dockArea === "floating" ? Math.max(minimumPanelWidth, localWidth) : localWidth
    height: dockArea === "floating" ? Math.max(minimumPanelHeight, localHeight) : localHeight
    // Keep the item alive for the short exit animation; the model remains the
    // single source of truth for its final visible state.
    opacity: modelVisible ? 1 : 0
    scale: 1
    visible: modelVisible || opacity > 0.01
    z: dockDragging || resizing ? 20000 : stackOrder

    function beginPanelDrag() {
        dragStartX = localX;
        dragStartY = localY;
        host.beginDockDrag(panelId);
    }

    function updatePanelDrag(surface, pointerX, pointerY, pressHostX, pressHostY) {
        const point = surface.mapToItem(host, pointerX, pointerY);
        manualDragX = point.x - pressHostX;
        manualDragY = point.y - pressHostY;
        lastPointerX = point.x;
        lastPointerY = point.y;
        host.updateDockDrag(panelId, point.x, point.y);
    }

    function finishPanelDrag(deltaX, deltaY) {
        localX = Math.max(0, Math.min(host.width - width, dragStartX + deltaX));
        localY = Math.max(0, Math.min(host.height - height, dragStartY + deltaY));
        host.finishDockDrag(panelId, localX, localY, width, height, dockArea === "floating");
    }

    function beginResize(edge, surface, pointerX, pointerY) {
        const point = surface.mapToItem(host, pointerX, pointerY);
        const vertical = edge === "left" || edge === "right";
        const boundary = vertical ? localX + (edge === "right" ? localWidth : 0) : localY + (edge === "bottom" ? localHeight : 0);
        dockModel.begin_resize(panelId);
        resizeEdge = edge;
        resizePressHostX = point.x;
        resizePressHostY = point.y;
        resizeStartX = localX;
        resizeStartY = localY;
        resizeStartWidth = width;
        resizeStartHeight = height;
        resizing = true;
        host.beginDockResize(panelId, vertical ? "vertical" : "horizontal", boundary, vertical ? localY : localX, vertical ? localY + localHeight : localX + localWidth, dockArea !== "floating");
        dockModel.raise_panel(panelId);
    }

    function updateResize(surface, pointerX, pointerY) {
        if (!resizing)
            return;
        const point = surface.mapToItem(host, pointerX, pointerY);
        const dx = point.x - resizePressHostX;
        const dy = point.y - resizePressHostY;
        const geometry = DockLayout.floatingResize([resizeStartX, resizeStartY, resizeStartWidth, resizeStartHeight], resizeEdge, dx, dy, root.kind, host.width, host.height);
        const nextX = geometry[0], nextY = geometry[1], nextWidth = geometry[2], nextHeight = geometry[3];
        if (dockArea === "floating") {
            localX = nextX;
            localY = nextY;
            localWidth = nextWidth;
            localHeight = nextHeight;
        }
        if (typeof host.updateDockResizeBoundary === "function") {
            const vertical = resizeEdge.indexOf("left") >= 0 || resizeEdge.indexOf("right") >= 0;
            host.updateDockResizeBoundary(vertical ? nextX + (resizeEdge === "right" ? nextWidth : 0) : nextY + (resizeEdge === "bottom" ? nextHeight : 0), vertical ? nextY : nextX, vertical ? nextY + nextHeight : nextX + nextWidth);
        }
        dockModel.preview_resize_panel(panelId, resizeEdge, nextX / Math.max(1, host.width), nextY / Math.max(1, host.height), nextWidth / Math.max(1, host.width), nextHeight / Math.max(1, host.height), host.width, host.height);
    }

    function cancelResize() {
        if (!resizing)
            return;
        dockModel.cancel_resize(panelId);
        resizing = false;
        resizeEdge = "";
        localX = scaledX();
        localY = scaledY();
        localWidth = scaledWidth();
        localHeight = scaledHeight();
        host.endDockResize();
    }
    function cancelGesture() {
        resultsDragHandle.cancel();
        dockMoveHandle.cancel();
        titleDrag.cancel();
        cancelResize();
        cancelTabDrag();
    }
    function finishResize() {
        if (!resizing)
            return;
        dockModel.resize_panel(panelId, resizeEdge, localX / host.width, localY / host.height, localWidth / host.width, localHeight / host.height, host.width, host.height);
        resizing = false;
        resizeEdge = "";
        host.endDockResize();
    }

    function initializeGeometry() {
        if (root.geometryTransitionsReady || root.host.width <= 0 || root.host.height <= 0)
            return;
        root.localX = root.scaledX();
        root.localY = root.scaledY();
        root.localWidth = root.scaledWidth();
        root.localHeight = root.scaledHeight();
        root.geometryTransitionsReady = true;
    }

    onPanelXChanged: if (!dockDragging) {
        localX = scaledX();
        localWidth = scaledWidth();
    }
    onPanelYChanged: if (!dockDragging) {
        localY = scaledY();
        localHeight = scaledHeight();
    }
    onPanelWidthChanged: localWidth = scaledWidth()
    onPanelHeightChanged: localHeight = scaledHeight()
    onDockDraggingChanged: if (!dockDragging) {
        localX = scaledX();
        localY = scaledY();
        localWidth = scaledWidth();
        localHeight = scaledHeight();
    }
    TapHandler {
        target: null
        enabled: root.dockArea === "floating"
        acceptedButtons: Qt.AllButtons
        gesturePolicy: TapHandler.DragThreshold
        onPressedChanged: {
            if (pressed && root.dockArea === "floating")
                dockModel.raise_panel(root.panelId);
        }
    }

    Connections {
        target: root.host
        function onWidthChanged() {
            root.initializeGeometry();
            if (!root.dockDragging && !root.resizing) {
                root.localX = root.scaledX();
                root.localWidth = root.scaledWidth();
            }
        }
        function onHeightChanged() {
            root.initializeGeometry();
            if (!root.dockDragging && !root.resizing) {
                root.localY = root.scaledY();
                root.localHeight = root.scaledHeight();
            }
        }
    }

    Rectangle {
        id: panelSurface
        anchors.fill: parent
        anchors.margins: root.chromeInset
        radius: root.theme.surfaceRadius
        color: root.theme.panel
        border.color: root.dockDragging || root.resizeHighlighted ? root.theme.action : root.theme.outlineVariant
        border.width: 1
        antialiasing: true
        Behavior on border.color {
            ColorAnimation {
                duration: root.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }
    }

    // One direct-rendered body owns both the title bar and panel content.
    // Rectangular clipping prevents child content from escaping the dock
    // without rasterizing and resampling every glyph at fractional DPI.
    Item {
        id: panelBody
        z: 100
        anchors.fill: panelSurface
        anchors.margins: panelSurface.border.width
        // Keep text and icons in the direct scene-graph path.  Applying an
        // OpacityMask here turns the complete dock into an offscreen texture;
        // at fractional Windows scale factors (notably 125%) that texture is
        // resampled and native DirectWrite glyphs become visibly soft.
        clip: true
    }

    Rectangle {
        id: titleBar
        parent: panelBody
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        // Results and Commit Queue own their top-level chrome and must not
        // add a second title row.  Keeping the title bar for a stack preserves
        // access to its tabs when an older saved layout already contains one.
        height: root.chrome.height
        visible: height > 0
        radius: root.theme.surfaceRadius
        color: root.dockDragging ? root.theme.surfaceContainerHigh : root.theme.panel
        antialiasing: true
        Behavior on color {
            ColorAnimation {
                duration: root.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: Math.min(12, parent.height)
            color: parent.color
        }

        DockTitleDrag {
            id: titleDrag
            anchors.fill: parent
            panel: root
        }
        Item {
            id: titleLayout
            anchors.fill: parent
            z: 10
            Controls.MaterialIcon {
                readonly property var frameGeometry: root.chromeControls.dockIcon
                property string frameId: "dockIcon"
                x: frameGeometry.x
                y: frameGeometry.y
                width: frameGeometry.width
                height: frameGeometry.height
                visible: frameGeometry.visible !== false
                name: root.panelIcon(root.kind)
                size: 16
                color: root.theme.action
            }

            DockTitleLabel {
                readonly property var frameGeometry: root.chromeControls.dockTitle
                property string frameId: "dockTitle"
                x: frameGeometry.x
                y: frameGeometry.y
                width: frameGeometry.width
                height: frameGeometry.height
                visible: frameGeometry.visible !== false
                theme: root.theme
                titleText: root.localizedPanelTitle(root.kind, root.title)
            }

            Controls.DockDragGrip {
                id: dockMoveHandle
                readonly property var frameGeometry: root.chromeControls.dockGrip
                property string frameId: "dockGrip"
                x: frameGeometry.x
                y: frameGeometry.y
                width: frameGeometry.width
                height: frameGeometry.height
                visible: frameGeometry.visible !== false
                objectName: "dockStackDrag_" + root.panelId
                theme: root.theme
                toolTip: qsTr("Drag to move or dock")
                dragThreshold: Placement.dragThreshold
                onPressed: dockModel.raise_panel(root.panelId)
                onClicked: dockModel.raise_panel(root.panelId)
                onDragStarted: (pressX, pressY) => {
                    const point = dockMoveHandle.mapToItem(root.host, pressX, pressY);
                    root.handlePressHostX = point.x;
                    root.handlePressHostY = point.y;
                    root.manualDragX = 0;
                    root.manualDragY = 0;
                    root.beginPanelDrag();
                }
                onDragMoved: (pointerX, pointerY) => root.updatePanelDrag(dockMoveHandle, pointerX, pointerY, root.handlePressHostX, root.handlePressHostY)
                onDragFinished: root.finishPanelDrag(root.manualDragX, root.manualDragY)
                onDragCanceled: root.host.cancelDockDrag(root.panelId)
                onContextRequested: (pointerX, pointerY) => dockHandleMenu.openAt(dockMoveHandle, pointerX, pointerY)
            }

            Controls.CompactIconButton {
                readonly property var frameGeometry: root.chromeControls.dockHelp
                property string frameId: "dockHelp"
                x: frameGeometry.x
                y: frameGeometry.y
                width: frameGeometry.width
                height: frameGeometry.height
                visible: frameGeometry.visible !== false
                theme: root.theme
                round: frameGeometry.round
                iconName: "help"
                iconSize: DockChrome.dimensions.actionIcon
                iconColor: root.theme.secondaryText
                backgroundColor: root.theme.surfaceContainerHigh
                toolTip: qsTr("Help for this dock")
                onClicked: root.openDockHelp()
            }

            Controls.CompactIconButton {
                readonly property var frameGeometry: root.chromeControls.dockDetach
                property string frameId: "dockDetach"
                x: frameGeometry.x
                y: frameGeometry.y
                width: frameGeometry.width
                height: frameGeometry.height
                visible: frameGeometry.visible !== false
                theme: root.theme
                round: frameGeometry.round
                iconName: "open-in-new"
                iconSize: DockChrome.dimensions.actionIcon
                iconColor: root.theme.secondaryText
                backgroundColor: root.theme.surfaceContainerHigh
                toolTip: qsTr("Detach ") + root.localizedPanelTitle(root.kind, root.title)
                onClicked: dockModel.detach_panel(root.panelId)
            }

            Controls.CompactIconButton {
                readonly property var frameGeometry: root.chromeControls.dockClose
                property string frameId: "dockClose"
                x: frameGeometry.x
                y: frameGeometry.y
                width: frameGeometry.width
                height: frameGeometry.height
                visible: frameGeometry.visible !== false
                theme: root.theme
                round: frameGeometry.round
                iconName: "close"
                iconSize: DockChrome.dimensions.actionIcon
                iconColor: root.theme.secondaryText
                backgroundColor: root.theme.surfaceContainerHigh
                toolTip: qsTr("Close ") + root.localizedPanelTitle(root.kind, root.title)
                onClicked: root.closeDock(root.panelId)
            }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            color: root.theme.outlineVariant
        }
    }
    Rectangle {
        id: stackTabBar
        parent: titleBar
        x: root.chromeControls.dockTabs.x
        y: root.chromeControls.dockTabs.y
        width: root.chromeControls.dockTabs.width
        height: root.chromeControls.dockTabs.height
        visible: root.chromeControls.dockTabs.visible && height > 0
        color: "transparent"
        clip: true
        z: 20

        Flickable {
            id: stackTabsFlick
            anchors.fill: parent
            contentWidth: stackTabsRow.width
            contentHeight: height
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.HorizontalFlick
            clip: true
            ScrollBar.horizontal: Controls.ScrollBar {
                id: stackTabsScrollBar
                theme: root.theme
                flickableTarget: stackTabsFlick
            }

            Row {
                id: stackTabsRow
                height: TabLayout.dockTabHeight(stackTabsFlick.height, stackTabsFlick.contentWidth > stackTabsFlick.width + 0.5)
                spacing: TabLayout.dockTab.spacing

                Repeater {
                    id: stackTabRepeater
                    model: root.stackPanels
                    delegate: StackTab {}
                }
            }
        }
    }

    Controls.DockDragGrip {
        id: resultsDragHandle
        parent: panelBody
        objectName: "dockTitleDrag_" + root.panelId
        visible: root.kind === "results" && root.resultsDragHandleVisible
        anchors.left: parent.left
        anchors.top: parent.top
        width: 34
        height: 48
        z: 50
        theme: root.theme
        toolTip: qsTr("Drag to move or dock")
        dragThreshold: Placement.dragThreshold
        property real pressHostX: 0
        property real pressHostY: 0
        onPressed: dockModel.raise_panel(root.panelId)
        onClicked: dockModel.raise_panel(root.panelId)
        onDragStarted: (pressX, pressY) => {
            const point = resultsDragHandle.mapToItem(root.host, pressX, pressY);
            pressHostX = point.x;
            pressHostY = point.y;
            root.manualDragX = 0;
            root.manualDragY = 0;
            root.beginPanelDrag();
        }
        onDragMoved: (pointerX, pointerY) => root.updatePanelDrag(resultsDragHandle, pointerX, pointerY, pressHostX, pressHostY)
        onDragFinished: root.finishPanelDrag(root.manualDragX, root.manualDragY)
        onDragCanceled: root.host.cancelDockDrag(root.panelId)
        onContextRequested: (pointerX, pointerY) => dockHandleMenu.openAt(resultsDragHandle, pointerX, pointerY)
    }
    ActionMenu {
        id: dockHandleMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: [
            {
                "title": qsTr("Help for this dock"),
                "icon": "help",
                "command": "help"
            },
            {
                "separator": true
            },
            {
                "title": qsTr("Dock to workspace"),
                "icon": "window-restore",
                "command": "dock",
                "visible": root.dockArea === "floating"
            },
            {
                "title": qsTr("Open in separate window"),
                "icon": "open-in-new",
                "command": "detach",
                "visible": root.kind !== "results"
            },
            {
                "title": qsTr("Close dock"),
                "icon": "close",
                "command": "close",
                "visible": root.closable
            }
        ]
        onTriggered: command => {
            if (command === "help")
                root.openDockHelp();
            else if (command === "dock")
                dockModel.dock_panel(root.panelId);
            else if (command === "detach")
                dockModel.detach_panel(root.panelId);
            else if (command === "close")
                dockModel.close_panel(root.panelId);
        }
    }
    Loader {
        id: panelContentLoader
        objectName: "dockPanelContentLoader_" + root.panelId
        parent: panelBody
        x: 0
        y: titleBar.height
        width: parent.width
        height: Math.max(0, parent.height - titleBar.height)
        active: root.panelOpen || root.retainContent
        asynchronous: true
        visible: root.panelOpen
        sourceComponent: root.contentComponent
    }
    Binding {
        target: panelContentLoader.item
        property: "dockResizeActive"
        value: Boolean(root.host && root.host.dockResizeActive)
        when: root.kind === "knowledge" && panelContentLoader.status === Loader.Ready
    }
    Controls.BusyIndicator {
        parent: panelBody
        anchors.centerIn: panelContentLoader
        running: root.panelOpen && panelContentLoader.status === Loader.Loading
        visible: running
        uiTheme: root.theme
        z: 60
    }
    // Tiled panels resize only at shared dividers. Internal floating panels
    // own their rectangle, so every outer edge is interactive.
    DockResizeEdge {
        panel: root
        edge: "left"
        z: panelBody.z + 10
        visible: root.dockArea === "floating" || root.canResizeLeft || (root.resizing && root.resizeEdge === "left")
        enabled: visible
        width: root.dockArea === "floating" ? 10 : 9
        x: -width / 2
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin: 8
        anchors.bottomMargin: 8
    }
    DockResizeEdge {
        panel: root
        edge: "right"
        z: panelBody.z + 10
        visible: root.dockArea === "floating" || root.canResizeRight || (root.resizing && root.resizeEdge === "right")
        enabled: visible
        width: root.dockArea === "floating" ? 10 : 9
        x: parent.width - width / 2
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin: 8
        anchors.bottomMargin: 8
    }
    DockResizeEdge {
        panel: root
        edge: "top"
        z: panelBody.z + 10
        visible: root.dockArea === "floating" || root.canResizeTop || (root.resizing && root.resizeEdge === "top")
        enabled: visible
        height: root.dockArea === "floating" ? 10 : 9
        anchors.left: parent.left
        anchors.right: parent.right
        y: -height / 2
        anchors.leftMargin: 8
        anchors.rightMargin: 8
    }
    DockResizeEdge {
        panel: root
        edge: "bottom"
        z: panelBody.z + 10
        visible: root.dockArea === "floating" || root.canResizeBottom || (root.resizing && root.resizeEdge === "bottom")
        enabled: visible
        height: root.dockArea === "floating" ? 10 : 9
        anchors.left: parent.left
        anchors.right: parent.right
        y: parent.height - height / 2
        anchors.leftMargin: 8
        anchors.rightMargin: 8
    }
    Repeater {
        model: ["top_left", "top_right", "bottom_left", "bottom_right"]
        delegate: DockResizeEdge {
            required property string modelData
            panel: root
            edge: modelData
            z: panelBody.z + 12
            visible: root.dockArea === "floating"
            enabled: visible
            width: 14
            height: 14
            x: edge.indexOf("right") >= 0 ? root.width - width : 0
            y: edge.indexOf("bottom") >= 0 ? root.height - height : 0
        }
    }
}
