import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

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
    readonly property real chromeInset: dockArea === "floating" ? 6 : 5
    readonly property real minimumPanelWidth: Math.min(sizing.dockMinimumWidth(root.kind), root.host.width)
    readonly property real minimumPanelHeight: Math.min(sizing.dockMinimumHeight(root.kind), root.host.height)
    readonly property int titleActionCount: (kind === "results" ? 0 : 3) + (closable ? 1 : 0)
    readonly property bool headerlessSinglePanel: stackSize <= 1 && (kind === "results" || kind === "commit_queue")

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
        host.finishDockDrag(panelId, localX, localY, width, height);
    }

    function beginResize(edge, surface, pointerX, pointerY) {
        const point = surface.mapToItem(host, pointerX, pointerY);
        resizeEdge = edge;
        resizePressHostX = point.x;
        resizePressHostY = point.y;
        resizeStartX = localX;
        resizeStartY = localY;
        resizeStartWidth = width;
        resizeStartHeight = height;
        resizing = true;
        host.beginDockResize();
        dockModel.raise_panel(panelId);
    }

    function updateResize(surface, pointerX, pointerY) {
        if (!resizing)
            return;
        const point = surface.mapToItem(host, pointerX, pointerY);
        const dx = point.x - resizePressHostX;
        const dy = point.y - resizePressHostY;
        const minimumWidth = root.minimumPanelWidth;
        const minimumHeight = root.minimumPanelHeight;
        let nextX = resizeStartX;
        let nextY = resizeStartY;
        let nextWidth = resizeStartWidth;
        let nextHeight = resizeStartHeight;

        if (resizeEdge.indexOf("left") >= 0) {
            const right = resizeStartX + resizeStartWidth;
            nextX = Math.max(0, Math.min(right - minimumWidth, resizeStartX + dx));
            nextWidth = right - nextX;
        } else if (resizeEdge.indexOf("right") >= 0) {
            nextWidth = Math.max(minimumWidth, Math.min(host.width - resizeStartX, resizeStartWidth + dx));
        }
        if (resizeEdge.indexOf("top") >= 0) {
            const bottom = resizeStartY + resizeStartHeight;
            nextY = Math.max(0, Math.min(bottom - minimumHeight, resizeStartY + dy));
            nextHeight = bottom - nextY;
        } else if (resizeEdge.indexOf("bottom") >= 0) {
            nextHeight = Math.max(minimumHeight, Math.min(host.height - resizeStartY, resizeStartHeight + dy));
        }
        if (dockArea === "floating") {
            localX = nextX;
            localY = nextY;
            localWidth = nextWidth;
            localHeight = nextHeight;
        }
        dockModel.preview_resize_panel(panelId, resizeEdge, nextX / Math.max(1, host.width), nextY / Math.max(1, host.height), nextWidth / Math.max(1, host.width), nextHeight / Math.max(1, host.height), host.width, host.height);
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
        border.color: root.dockDragging || root.resizing ? root.theme.action : root.theme.outlineVariant
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
        height: root.headerlessSinglePanel ? 0 : root.theme.dockTitleHeight
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

        RowLayout {
            id: titleLayout
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 6
            spacing: 8
            z: 10
            Controls.MaterialIcon {
                visible: root.stackSize <= 1
                name: root.panelIcon(root.kind)
                size: 16
                color: root.theme.action
            }
            DockTitleLabel {
                visible: root.stackSize <= 1
                theme: root.theme
                titleText: root.localizedPanelTitle(root.kind, root.title)
                Layout.fillWidth: true
            }
            Item {
                visible: root.stackSize > 1
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
            Controls.DockDragGrip {
                id: dockMoveHandle
                visible: root.kind !== "results"
                Layout.preferredWidth: 30
                Layout.preferredHeight: 34
                theme: root.theme
                toolTip: qsTr("Drag to move or dock")
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
                onDragCanceled: root.finishPanelDrag(root.manualDragX, root.manualDragY)
                onContextRequested: (pointerX, pointerY) => dockHandleMenu.openAt(dockMoveHandle, pointerX, pointerY)
            }
            Controls.CompactIconButton {
                visible: root.kind !== "results"
                Layout.preferredWidth: 30
                Layout.preferredHeight: 30
                theme: root.theme
                round: true
                iconName: "help"
                iconSize: 14
                iconColor: root.theme.secondaryText
                backgroundColor: root.theme.surfaceContainerHigh
                toolTip: qsTr("Help for this dock")
                onClicked: root.openDockHelp()
            }
            Controls.CompactIconButton {
                visible: root.kind !== "results"
                Layout.preferredWidth: 30
                Layout.preferredHeight: 30
                theme: root.theme
                round: true
                iconName: "open-in-new"
                iconSize: 14
                iconColor: root.theme.secondaryText
                backgroundColor: root.theme.surfaceContainerHigh
                toolTip: qsTr("Detach ") + root.localizedPanelTitle(root.kind, root.title)
                onClicked: dockModel.detach_panel(root.panelId)
            }
            Controls.CompactIconButton {
                visible: root.closable
                Layout.preferredWidth: 30
                Layout.preferredHeight: 30
                theme: root.theme
                round: true
                iconName: "close"
                iconSize: 14
                iconColor: root.theme.secondaryText
                backgroundColor: root.theme.surfaceContainerHigh
                toolTip: qsTr("Close ") + root.localizedPanelTitle(root.kind, root.title)
                onClicked: dockModel.close_panel(root.panelId)
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
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 6
        anchors.rightMargin: root.titleActionCount * 38 + 6
        height: root.stackSize > 1 ? parent.height : 0
        visible: height > 0
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
                theme: root.theme
                flickableTarget: stackTabsFlick
            }

            Row {
                id: stackTabsRow
                height: parent.height
                spacing: 2

                Repeater {
                    id: stackTabRepeater
                    model: root.stackPanels
                    delegate: Item {
                        id: stackTab
                        property var record: modelData
                        property int targetIndex: index
                        property bool hovered: tabHover.hovered
                        property real naturalWidth: Math.min(260, Math.max(112, tabLabel.implicitWidth + 44))
                        width: Math.max(112, Math.min(naturalWidth, stackTabBar.width / Math.max(1, root.stackSize)))
                        height: stackTabsRow.height
                        z: tabDrag.active ? 10 : 1
                        transform: Translate {
                            x: tabDrag.active ? tabDrag.translation.x : 0
                        }

                        Rectangle {
                            anchors.fill: parent
                            color: root.theme.action
                            opacity: tabDrag.active ? 0.14 : stackTab.record.active ? 0.10 : stackTab.hovered ? 0.07 : 0
                        }
                        Rectangle {
                            anchors.bottom: parent.bottom
                            anchors.horizontalCenter: parent.horizontalCenter
                            width: stackTab.record.active ? Math.max(48, parent.width - 20) : 0
                            height: 3
                            radius: 1.5
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
                            target: null
                            acceptedButtons: Qt.LeftButton
                            dragThreshold: 8
                            onTranslationChanged: {
                                const center = stackTab.x + stackTab.width / 2 + translation.x;
                                let nextIndex = 0;
                                for (let itemIndex = 0; itemIndex < stackTabRepeater.count; ++itemIndex) {
                                    const item = stackTabRepeater.itemAt(itemIndex);
                                    if (item && center > item.x + item.width / 2)
                                        nextIndex = itemIndex;
                                }
                                stackTab.targetIndex = nextIndex;
                            }
                            onActiveChanged: {
                                if (active)
                                    return;
                                if (Math.abs(translation.y) > titleBar.height) {
                                    dockModel.float_panel_inside(stackTab.record.panelId);
                                } else if (stackTab.targetIndex !== index) {
                                    dockModel.reorder_stack_panel(stackTab.record.panelId, stackTab.targetIndex);
                                }
                                stackTab.targetIndex = index;
                            }
                        }
                    }
                }
            }
        }
    }

    Controls.DockDragGrip {
        id: resultsDragHandle
        parent: panelBody
        objectName: "dockTitleDrag_" + root.panelId
        visible: root.kind === "results" && root.stackSize <= 1
        anchors.left: parent.left
        anchors.top: parent.top
        width: 34
        height: 48
        z: 50
        theme: root.theme
        toolTip: qsTr("Drag to move or dock")
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
        onDragCanceled: root.finishPanelDrag(root.manualDragX, root.manualDragY)
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
        z: 90
        visible: root.dockArea === "floating" || root.canResizeLeft || (root.resizing && root.resizeEdge === "left")
        enabled: visible
        width: 6
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin: 8
        anchors.bottomMargin: 8
    }
    DockResizeEdge {
        panel: root
        edge: "right"
        z: 90
        visible: root.dockArea === "floating" || root.canResizeRight || (root.resizing && root.resizeEdge === "right")
        enabled: visible
        width: 6
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.topMargin: 8
        anchors.bottomMargin: 8
    }
    DockResizeEdge {
        panel: root
        edge: "top"
        z: 90
        visible: root.dockArea === "floating" || root.canResizeTop || (root.resizing && root.resizeEdge === "top")
        enabled: visible
        height: 6
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 8
        anchors.rightMargin: 8
    }
    DockResizeEdge {
        panel: root
        edge: "bottom"
        z: 90
        visible: root.dockArea === "floating" || root.canResizeBottom || (root.resizing && root.resizeEdge === "bottom")
        enabled: visible
        height: 6
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 8
        anchors.rightMargin: 8
    }
    DockResizeEdge {
        panel: root
        edge: "bottom_right"
        z: 92
        visible: root.dockArea === "floating"
        enabled: visible
        width: 14
        height: 14
        anchors.right: parent.right
        anchors.bottom: parent.bottom
    }
}
