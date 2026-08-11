import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt5Compat.GraphicalEffects

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

    WindowSizing { id: sizing }

    // Align adjacent normalized dock rectangles to the same physical pixel.
    // Calculating width from independently rounded fractions can otherwise
    // leave a one-pixel strip at the right or bottom edge while resizing.
    function scaledX() {
        return Math.round(panelX * host.width)
    }
    function scaledY() {
        return Math.round(panelY * host.height)
    }
    function scaledRight() {
        return panelX + panelWidth >= 0.999999
            ? host.width
            : Math.round((panelX + panelWidth) * host.width)
    }
    function scaledBottom() {
        return panelY + panelHeight >= 0.999999
            ? host.height
            : Math.round((panelY + panelHeight) * host.height)
    }
    function scaledWidth() {
        return Math.max(0, scaledRight() - scaledX())
    }
    function scaledHeight() {
        return Math.max(0, scaledBottom() - scaledY())
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
    property bool dockDragging: titleDragMouse.dragging || resultsDragMouse.dragging
    property bool geometryTransitionsReady: false
    property bool hostGeometryChanging: false
    readonly property real chromeInset: dockArea === "floating" ? 6 : 5
    readonly property real minimumPanelWidth: Math.min(
        sizing.dockMinimumWidth(root.kind), root.host.width
    )
    readonly property real minimumPanelHeight: Math.min(
        sizing.dockMinimumHeight(root.kind), root.host.height
    )
    readonly property int titleActionCount:
        (kind === "results" ? 0 : 2)
        + (closable ? 1 : 0)

    function panelIcon(panelKind) {
        return panelKind === "snapshot" ? "movie"
            : panelKind === "tasks" ? "tasks"
            : panelKind === "task_calendar" ? "calendar-month"
            : panelKind === "drop_plate" || panelKind === "commit_queue" ? "publish"
            : panelKind === "notes" ? "comment"
            : panelKind === "advanced_search" ? "search"
            : panelKind === "fast_controls" ? "tune"
            : panelKind === "repo_sync_queue" ? "sync"
            : panelKind === "watch_folders" ? "folder"
            : panelKind === "description" ? "description" : "view_kanban"
    }

    x: dockDragging ? Math.max(0, Math.min(host.width - width, dragStartX + manualDragX)) : localX
    y: dockDragging ? Math.max(0, Math.min(host.height - height, dragStartY + manualDragY)) : localY
    width: dockArea === "floating"
        ? Math.max(minimumPanelWidth, localWidth) : localWidth
    height: dockArea === "floating"
        ? Math.max(minimumPanelHeight, localHeight) : localHeight
    // Keep the item alive for the short exit animation; the model remains the
    // single source of truth for its final visible state.
    opacity: modelVisible ? 1 : 0
    scale: 1
    visible: modelVisible || opacity > 0.01
    z: dockDragging || resizing ? 20000 : stackOrder

    function beginPanelDrag() {
        dragStartX = localX
        dragStartY = localY
        host.beginDockDrag(panelId)
    }

    function updatePanelDrag(surface, pointerX, pointerY, pressHostX, pressHostY) {
        const point = surface.mapToItem(host, pointerX, pointerY)
        manualDragX = point.x - pressHostX
        manualDragY = point.y - pressHostY
        lastPointerX = point.x
        lastPointerY = point.y
        host.updateDockDrag(panelId, point.x, point.y)
    }

    function finishPanelDrag(deltaX, deltaY) {
        localX = Math.max(0, Math.min(host.width - width, dragStartX + deltaX))
        localY = Math.max(0, Math.min(host.height - height, dragStartY + deltaY))
        host.finishDockDrag(panelId, localX, localY, width, height)
    }

    function beginResize(edge, surface, pointerX, pointerY) {
        const point = surface.mapToItem(host, pointerX, pointerY)
        resizeEdge = edge
        resizePressHostX = point.x
        resizePressHostY = point.y
        resizeStartX = localX
        resizeStartY = localY
        resizeStartWidth = width
        resizeStartHeight = height
        resizing = true
        host.beginDockResize()
        dockModel.raise_panel(panelId)
    }

    function updateResize(surface, pointerX, pointerY) {
        if (!resizing)
            return
        const point = surface.mapToItem(host, pointerX, pointerY)
        const dx = point.x - resizePressHostX
        const dy = point.y - resizePressHostY
        const minimumWidth = root.minimumPanelWidth
        const minimumHeight = root.minimumPanelHeight
        let nextX = resizeStartX
        let nextY = resizeStartY
        let nextWidth = resizeStartWidth
        let nextHeight = resizeStartHeight

        if (resizeEdge.indexOf("left") >= 0) {
            const right = resizeStartX + resizeStartWidth
            nextX = Math.max(0, Math.min(right - minimumWidth, resizeStartX + dx))
            nextWidth = right - nextX
        } else if (resizeEdge.indexOf("right") >= 0) {
            nextWidth = Math.max(
                minimumWidth,
                Math.min(host.width - resizeStartX, resizeStartWidth + dx)
            )
        }
        if (resizeEdge.indexOf("top") >= 0) {
            const bottom = resizeStartY + resizeStartHeight
            nextY = Math.max(0, Math.min(bottom - minimumHeight, resizeStartY + dy))
            nextHeight = bottom - nextY
        } else if (resizeEdge.indexOf("bottom") >= 0) {
            nextHeight = Math.max(
                minimumHeight,
                Math.min(host.height - resizeStartY, resizeStartHeight + dy)
            )
        }
        if (dockArea === "floating") {
            localX = nextX
            localY = nextY
            localWidth = nextWidth
            localHeight = nextHeight
        }
        dockModel.preview_resize_panel(
            panelId,
            resizeEdge,
            nextX / Math.max(1, host.width),
            nextY / Math.max(1, host.height),
            nextWidth / Math.max(1, host.width),
            nextHeight / Math.max(1, host.height),
            host.width,
            host.height
        )
    }

    function finishResize() {
        if (!resizing)
            return
        dockModel.resize_panel(
            panelId,
            resizeEdge,
            localX / host.width,
            localY / host.height,
            localWidth / host.width,
            localHeight / host.height,
            host.width,
            host.height
        )
        resizing = false
        resizeEdge = ""
        host.endDockResize()
    }

    Behavior on x { enabled: root.geometryTransitionsReady && root.modelVisible && !root.hostGeometryChanging && !root.host.windowResizeActive && !root.host.dockResizeActive && !root.dockDragging && !root.resizing; NumberAnimation { duration: root.theme.motionMedium; easing.type: Easing.OutCubic } }
    Behavior on y { enabled: root.geometryTransitionsReady && root.modelVisible && !root.hostGeometryChanging && !root.host.windowResizeActive && !root.host.dockResizeActive && !root.dockDragging && !root.resizing; NumberAnimation { duration: root.theme.motionMedium; easing.type: Easing.OutCubic } }
    Behavior on width { enabled: root.geometryTransitionsReady && root.modelVisible && !root.hostGeometryChanging && !root.host.windowResizeActive && !root.host.dockResizeActive && !root.dockDragging && !root.resizing; NumberAnimation { duration: root.theme.motionMedium; easing.type: Easing.OutCubic } }
    Behavior on height { enabled: root.geometryTransitionsReady && root.modelVisible && !root.hostGeometryChanging && !root.host.windowResizeActive && !root.host.dockResizeActive && !root.dockDragging && !root.resizing; NumberAnimation { duration: root.theme.motionMedium; easing.type: Easing.OutCubic } }
    Behavior on opacity {
        enabled: root.stackSize <= 1
        NumberAnimation {
            duration: root.theme.motionFast
            easing.type: Easing.OutCubic
        }
    }

    Timer {
        id: initialGeometryTimer
        interval: 16
        repeat: true
        running: true
        onTriggered: {
            if (root.host.width <= 0 || root.host.height <= 0)
                return
            root.localX = root.scaledX()
            root.localY = root.scaledY()
            root.localWidth = root.scaledWidth()
            root.localHeight = root.scaledHeight()
            repeat = false
            Qt.callLater(function() {
                root.geometryTransitionsReady = true
            })
        }
    }

    Timer {
        id: hostResizeIdleTimer
        interval: 90
        onTriggered: root.hostGeometryChanging = false
    }

    onPanelXChanged: if (!dockDragging) {
        localX = scaledX()
        localWidth = scaledWidth()
    }
    onPanelYChanged: if (!dockDragging) {
        localY = scaledY()
        localHeight = scaledHeight()
    }
    onPanelWidthChanged: localWidth = scaledWidth()
    onPanelHeightChanged: localHeight = scaledHeight()
    onDockDraggingChanged: if (!dockDragging) {
        localX = scaledX()
        localY = scaledY()
        localWidth = scaledWidth()
        localHeight = scaledHeight()
    }
    onVisibleChanged: if (visible) dockModel.raise_panel(panelId)

    Connections {
        target: root.host
        function onWidthChanged() {
            if (!root.dockDragging && !root.resizing) {
                root.hostGeometryChanging = true
                hostResizeIdleTimer.restart()
                root.localX = root.scaledX()
                root.localWidth = root.scaledWidth()
            }
        }
        function onHeightChanged() {
            if (!root.dockDragging && !root.resizing) {
                root.hostGeometryChanging = true
                hostResizeIdleTimer.restart()
                root.localY = root.scaledY()
                root.localHeight = root.scaledHeight()
            }
        }
    }

    Rectangle {
        id: panelSurface
        anchors.fill: parent
        anchors.margins: root.chromeInset
        radius: root.theme.surfaceRadius
        color: root.theme.panel
        border.color: root.dockDragging || root.resizing
            ? root.theme.action : root.theme.outlineVariant
        border.width: 1
        antialiasing: true
        Behavior on border.color {
            ColorAnimation {
                duration: root.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }
    }

    // One masked body owns both the title bar and the panel content.  Content
    // components may paint an opaque rectangular background of their own,
    // but it is clipped to the dock's actual MD3 outline instead of looking
    // like a second rectangular window placed inside a rounded card.
    Item {
        id: panelBody
        z: 100
        anchors.fill: panelSurface
        anchors.margins: panelSurface.border.width
        layer.enabled: true
        layer.smooth: true
        layer.effect: OpacityMask {
            cached: false
            maskSource: Rectangle {
                width: panelBody.width
                height: panelBody.height
                radius: Math.max(0, panelSurface.radius - panelSurface.border.width)
                antialiasing: true
            }
        }
    }

    Rectangle {
        id: titleBar
        parent: panelBody
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        // Ui_checkInOutTabWidget owns the search-type tab bar itself.  The
        // Results owns the Search Type tab bar and must not add a second
        // project-defined title row.
        height: root.kind === "results" && root.stackSize <= 1
            ? 0 : root.theme.dockTitleHeight
        visible: height > 0
        radius: root.theme.surfaceRadius
        color: titleDragMouse.containsMouse
            ? root.theme.surfaceContainerHigh : root.theme.panel
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
            MaterialIcon {
                visible: root.stackSize <= 1
                name: root.panelIcon(root.kind)
                size: 16
                color: root.theme.action
            }
            DockTitleLabel {
                visible: root.stackSize <= 1
                theme: root.theme
                titleText: qsTr(root.title)
                Layout.fillWidth: true
            }
            Item {
                visible: root.stackSize > 1
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
            CompactIconButton {
                visible: root.kind !== "results"
                Layout.preferredWidth: 30
                Layout.preferredHeight: 30
                theme: root.theme
                round: true
                iconName: root.dockArea === "floating"
                    ? "window-restore" : "picture-in-picture"
                iconSize: 14
                iconColor: root.theme.secondaryText
                backgroundColor: root.theme.surfaceContainerHigh
                toolTip: root.dockArea === "floating"
                    ? qsTr("Dock ") + qsTr(root.title)
                    : qsTr("Float ") + qsTr(root.title)
                        + qsTr(" inside workspace")
                onClicked: {
                    if (root.dockArea === "floating")
                        dockModel.dock_panel(root.panelId)
                    else
                        dockModel.float_panel_inside(root.panelId)
                }
            }
            CompactIconButton {
                visible: root.kind !== "results"
                Layout.preferredWidth: 30
                Layout.preferredHeight: 30
                theme: root.theme
                round: true
                iconName: "open-in-new"
                iconSize: 14
                iconColor: root.theme.secondaryText
                backgroundColor: root.theme.surfaceContainerHigh
                toolTip: qsTr("Detach ") + qsTr(root.title)
                onClicked: dockModel.detach_panel(root.panelId)
            }
            CompactIconButton {
                visible: root.closable
                Layout.preferredWidth: 30
                Layout.preferredHeight: 30
                theme: root.theme
                round: true
                iconName: "close"
                iconSize: 14
                iconColor: root.theme.secondaryText
                backgroundColor: root.theme.surfaceContainerHigh
                toolTip: qsTr("Close ") + qsTr(root.title)
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

        Item {
            id: titleDragSurface
            objectName: "dockTitleDrag_" + root.panelId
            visible: root.stackSize <= 1
            anchors.fill: parent
            anchors.rightMargin: root.titleActionCount * 38
            MouseArea {
                id: titleDragMouse
                anchors.fill: parent
                hoverEnabled: true
                preventStealing: true
                cursorShape: dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                property bool dragging: false
                property real pressHostX: 0
                property real pressHostY: 0
                onPressed: mouse => {
                    const point = titleDragSurface.mapToItem(root.host, mouse.x, mouse.y)
                    pressHostX = point.x
                    pressHostY = point.y
                    root.manualDragX = 0
                    root.manualDragY = 0
                }
                onPositionChanged: mouse => {
                    if (!pressed) return
                    const point = titleDragSurface.mapToItem(root.host, mouse.x, mouse.y)
                    if (!dragging && Math.hypot(point.x - pressHostX, point.y - pressHostY) >= 6) {
                        dragging = true
                        root.beginPanelDrag()
                    }
                    if (dragging)
                        root.updatePanelDrag(titleDragSurface, mouse.x, mouse.y, pressHostX, pressHostY)
                }
                onReleased: {
                    if (dragging)
                        root.finishPanelDrag(root.manualDragX, root.manualDragY)
                    else
                        dockModel.raise_panel(root.panelId)
                    dragging = false
                }
                onCanceled: {
                    if (dragging) root.finishPanelDrag(root.manualDragX, root.manualDragY)
                    dragging = false
                }
            }
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
                        property real naturalWidth: Math.min(
                            260, Math.max(112, tabLabel.implicitWidth + 44))
                        width: Math.max(112, Math.min(
                            naturalWidth,
                            stackTabBar.width / Math.max(1, root.stackSize)
                        ))
                        height: stackTabsRow.height
                        z: tabDrag.active ? 10 : 1
                        transform: Translate {
                            x: tabDrag.active ? tabDrag.translation.x : 0
                        }

                        Rectangle {
                            anchors.fill: parent
                            anchors.topMargin: 3
                            anchors.bottomMargin: 3
                            radius: root.theme.itemRadius
                            color: stackTab.record.active
                                ? root.theme.selected
                                : stackTab.hovered
                                    ? root.theme.rowHover : "transparent"
                            Behavior on color {
                                ColorAnimation { duration: root.theme.motionFast }
                            }
                        }
                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 2
                            color: root.theme.action
                            opacity: stackTab.record.active ? 1 : 0
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 4
                            spacing: 6
                            MaterialIcon {
                                name: root.panelIcon(stackTab.record.kind)
                                size: 14
                                color: stackTab.record.active
                                    ? root.theme.action : root.theme.secondaryText
                            }
                            DockTitleLabel {
                                id: tabLabel
                                Layout.fillWidth: true
                                theme: root.theme
                                titleText: stackTab.record.kind === "description"
                                    ? root.descriptionTitle
                                    : stackTab.record.title
                                active: stackTab.record.active
                            }
                        }
                        HoverHandler {
                            id: tabHover
                            cursorShape: Qt.PointingHandCursor
                        }
                        TapHandler {
                            acceptedButtons: Qt.LeftButton
                            onTapped: dockModel.activate_stack_panel(
                                stackTab.record.panelId)
                        }
                        DragHandler {
                            id: tabDrag
                            target: null
                            acceptedButtons: Qt.LeftButton
                            dragThreshold: 8
                            onTranslationChanged: {
                                const center = stackTab.x + stackTab.width / 2
                                    + translation.x
                                let nextIndex = 0
                                for (let itemIndex = 0;
                                        itemIndex < stackTabRepeater.count;
                                        ++itemIndex) {
                                    const item = stackTabRepeater.itemAt(itemIndex)
                                    if (item && center > item.x + item.width / 2)
                                        nextIndex = itemIndex
                                }
                                stackTab.targetIndex = nextIndex
                            }
                            onActiveChanged: {
                                if (active)
                                    return
                                if (Math.abs(translation.y)
                                        > titleBar.height) {
                                    dockModel.float_panel_inside(
                                        stackTab.record.panelId)
                                } else if (stackTab.targetIndex !== index) {
                                    dockModel.reorder_stack_panel(
                                        stackTab.record.panelId,
                                        stackTab.targetIndex)
                                }
                                stackTab.targetIndex = index
                            }
                        }
                    }
                }
            }
        }
    }

    Item {
        id: resultsDragSurface
        parent: panelBody
        objectName: "dockTitleDrag_" + root.panelId
        visible: root.kind === "results"
        anchors.left: parent.left
        anchors.top: parent.top
        width: 34
        height: 48
        z: 50
        Rectangle {
            id: gripBackground
            anchors.centerIn: parent
            width: 24
            height: 32
            radius: root.theme.surfaceRadius
            color: resultsDragMouse.pressed ? root.theme.selected
                : resultsDragMouse.containsMouse ? root.theme.rowHover : "transparent"
            Behavior on color {
                ColorAnimation { duration: root.theme.motionFast }
            }
            MaterialRipple {
                id: gripRipple
                color: root.theme.rippleStrong
                shapeRadius: gripBackground.radius
            }
        }
        Column {
            anchors.centerIn: parent
            spacing: 3
            Repeater {
                model: 3
                Row {
                    spacing: 4
                    Rectangle { width: 3; height: 3; radius: 1.5; color: root.theme.secondaryText; antialiasing: true }
                    Rectangle { width: 3; height: 3; radius: 1.5; color: root.theme.secondaryText; antialiasing: true }
                }
            }
        }
        MouseArea {
            id: resultsDragMouse
            anchors.fill: parent
            hoverEnabled: true
            preventStealing: true
            cursorShape: dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor
            property bool dragging: false
            property real pressHostX: 0
            property real pressHostY: 0
            onPressed: mouse => {
                gripRipple.burst(mouse.x - gripBackground.x, mouse.y - gripBackground.y)
                const point = resultsDragSurface.mapToItem(root.host, mouse.x, mouse.y)
                pressHostX = point.x
                pressHostY = point.y
                root.manualDragX = 0
                root.manualDragY = 0
            }
            onPositionChanged: mouse => {
                if (!pressed) return
                const point = resultsDragSurface.mapToItem(root.host, mouse.x, mouse.y)
                if (!dragging && Math.hypot(point.x - pressHostX, point.y - pressHostY) >= 6) {
                    dragging = true
                    root.beginPanelDrag()
                }
                if (dragging)
                    root.updatePanelDrag(resultsDragSurface, mouse.x, mouse.y, pressHostX, pressHostY)
            }
            onReleased: {
                if (dragging)
                    root.finishPanelDrag(root.manualDragX, root.manualDragY)
                else
                    dockModel.raise_panel(root.panelId)
                dragging = false
            }
            onCanceled: {
                if (dragging) root.finishPanelDrag(root.manualDragX, root.manualDragY)
                dragging = false
            }
        }
    }
    Loader {
        id: panelContentLoader
        parent: panelBody
        anchors.top: titleBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        active: root.panelOpen
        sourceComponent: root.contentComponent
    }
    // Tiled panels resize only at shared dividers. Internal floating panels
    // own their rectangle, so every outer edge is interactive.
    DockResizeEdge {
        panel: root; edge: "left"; z: 90
        visible: root.dockArea === "floating" || root.canResizeLeft
            || (root.resizing && root.resizeEdge === "left")
        enabled: visible
        width: 6
        anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
        anchors.topMargin: 8; anchors.bottomMargin: 8
    }
    DockResizeEdge {
        panel: root; edge: "right"; z: 90
        visible: root.dockArea === "floating" || root.canResizeRight
            || (root.resizing && root.resizeEdge === "right")
        enabled: visible
        width: 6
        anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
        anchors.topMargin: 8; anchors.bottomMargin: 8
    }
    DockResizeEdge {
        panel: root; edge: "top"; z: 90
        visible: root.dockArea === "floating" || root.canResizeTop
            || (root.resizing && root.resizeEdge === "top")
        enabled: visible
        height: 6
        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
        anchors.leftMargin: 8; anchors.rightMargin: 8
    }
    DockResizeEdge {
        panel: root; edge: "bottom"; z: 90
        visible: root.dockArea === "floating" || root.canResizeBottom
            || (root.resizing && root.resizeEdge === "bottom")
        enabled: visible
        height: 6
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
        anchors.leftMargin: 8; anchors.rightMargin: 8
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
